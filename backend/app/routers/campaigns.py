"""Bulk-send campaigns: queue jobs, watch progress, retry failed rows."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Form, UploadFile, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.models import Attachment, Campaign, CampaignStatus, EmailLog, EmailLogStatus, SmtpAccount
from app.schemas.campaign import (
    CampaignCreate,
    CampaignDuplicateRequest,
    CampaignEmailMatch,
    CampaignRead,
    EmailLogRead,
)
from app.schemas.common import Page
from app.services import attachment_store, campaign_runner, csv_parser
from app.utils.errors import NotFoundError, ValidationError

router = APIRouter()


def _campaign_to_read(
    row: Campaign,
    *,
    sent_count: int | None = None,
    failed_count: int | None = None,
    status: CampaignStatus | None = None,
) -> CampaignRead:
    return CampaignRead(
        id=row.id,
        name=row.name,
        subject=row.subject,
        body_html=row.body_html,
        smtp_account_id=row.smtp_account_id,
        template_id=row.template_id,
        status=status if status is not None else row.status,
        total=row.total,
        sent_count=sent_count if sent_count is not None else row.sent_count,
        failed_count=failed_count if failed_count is not None else row.failed_count,
        started_at=row.started_at,
        finished_at=row.finished_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _counts_by_campaign(
    db: AsyncSession, campaign_ids: list[str]
) -> dict[str, tuple[int, int]]:
    """Live sent/failed counts derived from EmailLog rows (source of truth)."""
    if not campaign_ids:
        return {}
    rows = (
        await db.execute(
            select(EmailLog.campaign_id, EmailLog.status, func.count())
            .where(EmailLog.campaign_id.in_(campaign_ids))
            .group_by(EmailLog.campaign_id, EmailLog.status)
        )
    ).all()
    counts: dict[str, tuple[int, int]] = {cid: (0, 0) for cid in campaign_ids}
    for cid, log_status, n in rows:
        sent, failed = counts[cid]
        if log_status == EmailLogStatus.sent:
            sent = n
        elif log_status == EmailLogStatus.failed:
            failed = n
        counts[cid] = (sent, failed)
    return counts


def _derive_status(row: Campaign, sent: int, failed: int) -> CampaignStatus:
    """Recompute terminal status from live counts; leave in-flight states alone."""
    if row.status in (CampaignStatus.done, CampaignStatus.failed):
        if sent + failed >= row.total:
            return CampaignStatus.done if failed == 0 else CampaignStatus.failed
    return row.status


def _log_to_read(row: EmailLog) -> EmailLogRead:
    merge = json.loads(row.merge_data) if row.merge_data else None
    return EmailLogRead(
        id=row.id,
        campaign_id=row.campaign_id,
        to_email=row.to_email,
        merge_data=merge,
        subject_rendered=row.subject_rendered,
        body_html_rendered=row.body_html_rendered,
        status=row.status,
        error_message=row.error_message,
        attempts=row.attempts,
        sent_at=row.sent_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _link_attachments(db: AsyncSession, campaign_id: str, ids: list[str]) -> None:
    if not ids:
        return
    await db.execute(
        update(Attachment).where(Attachment.id.in_(ids)).values(campaign_id=campaign_id)
    )


async def _clone_attachments(db: AsyncSession, src_campaign_id: str, dst_campaign_id: str) -> None:
    """Copy each attachment of the source campaign to the new one.

    Blobs are re-stored under a fresh name so the clone is independent — deleting
    either campaign won't pull the file out from under the other.
    """
    rows = (
        (
            await db.execute(
                select(Attachment).where(Attachment.campaign_id == src_campaign_id)
            )
        )
        .scalars()
        .all()
    )
    for a in rows:
        data = attachment_store.read_bytes(a.stored_name)
        stored_name, size = attachment_store.store_bytes(
            data, filename=a.filename, mime_type=a.mime_type
        )
        db.add(
            Attachment(
                filename=a.filename,
                stored_name=stored_name,
                mime_type=a.mime_type,
                size_bytes=size,
                campaign_id=dst_campaign_id,
                template_id=a.template_id,
            )
        )
    if rows:
        await db.commit()


async def _persist_campaign_with_rows(
    db: AsyncSession,
    *,
    name: str,
    subject: str,
    body_html: str,
    smtp_account_id: str,
    template_id: str | None,
    rows: list[dict[str, Any]],
    attachment_ids: list[str],
) -> Campaign:
    account = await db.get(SmtpAccount, smtp_account_id)
    if account is None:
        raise NotFoundError(f"SMTP account {smtp_account_id} not found")
    if not rows:
        raise ValidationError("Campaign needs at least one recipient")

    campaign = Campaign(
        name=name,
        subject=subject,
        body_html=body_html,
        smtp_account_id=smtp_account_id,
        template_id=template_id,
        status=CampaignStatus.queued,
        total=len(rows),
    )
    db.add(campaign)
    await db.flush()  # need campaign.id

    for row in rows:
        email = row.get("email") or row.get("to_email")
        if not email:
            raise ValidationError("Every recipient needs an 'email' field")
        merge = {k: v for k, v in row.items() if k != "email"}
        db.add(
            EmailLog(
                campaign_id=campaign.id,
                to_email=email,
                merge_data=json.dumps(merge) if merge else None,
                status=EmailLogStatus.queued,
            )
        )

    await _link_attachments(db, campaign.id, attachment_ids)
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.get("", response_model=list[CampaignRead])
async def list_campaigns(db: AsyncSession = Depends(get_db)) -> list[CampaignRead]:
    rows = (await db.execute(select(Campaign).order_by(Campaign.created_at.desc()))).scalars().all()
    counts = await _counts_by_campaign(db, [r.id for r in rows])
    result = []
    for r in rows:
        sent, failed = counts.get(r.id, (r.sent_count, r.failed_count))
        result.append(
            _campaign_to_read(
                r,
                sent_count=sent,
                failed_count=failed,
                status=_derive_status(r, sent, failed),
            )
        )
    return result


@router.get("/search-by-email", response_model=list[CampaignEmailMatch])
async def search_by_email(
    email: str,
    db: AsyncSession = Depends(get_db),
) -> list[CampaignEmailMatch]:
    """Find every campaign a given email address was a recipient of.

    Match is case-insensitive and exact. If the same address appears more than
    once in one campaign, only its most recent log is returned for that campaign.
    """
    needle = email.strip().lower()
    if not needle:
        raise ValidationError("email is required")

    rows = (
        (
            await db.execute(
                select(EmailLog, Campaign)
                .join(Campaign, EmailLog.campaign_id == Campaign.id)
                .where(func.lower(EmailLog.to_email) == needle)
                .order_by(EmailLog.created_at.desc())
            )
        )
        .all()
    )

    matches: list[CampaignEmailMatch] = []
    seen: set[str] = set()
    for log, campaign in rows:
        if campaign.id in seen:
            continue
        seen.add(campaign.id)
        matches.append(
            CampaignEmailMatch(
                campaign_id=campaign.id,
                campaign_name=campaign.name,
                subject=campaign.subject,
                campaign_status=campaign.status,
                to_email=log.to_email,
                email_status=log.status,
                error_message=log.error_message,
                sent_at=log.sent_at,
                created_at=log.created_at,
            )
        )
    return matches


@router.post("", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> CampaignRead:
    rows = [{"email": r.email, **r.data} for r in payload.recipients]
    campaign = await _persist_campaign_with_rows(
        db,
        name=payload.name,
        subject=payload.subject,
        body_html=payload.body_html,
        smtp_account_id=payload.smtp_account_id,
        template_id=payload.template_id,
        rows=rows,
        attachment_ids=payload.attachment_ids,
    )
    background.add_task(campaign_runner.run_campaign, campaign.id)
    return _campaign_to_read(campaign)


@router.post("/from-csv", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
async def create_campaign_from_csv(
    background: BackgroundTasks,
    file: UploadFile,
    name: str = Form(...),
    subject: str = Form(...),
    body_html: str = Form(...),
    smtp_account_id: str = Form(...),
    template_id: str | None = Form(default=None),
    attachment_ids: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
) -> CampaignRead:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise ValidationError("Upload a .csv file")
    raw = await file.read()
    rows = csv_parser.parse_bytes(raw)

    ids = [s.strip() for s in attachment_ids.split(",") if s.strip()]
    campaign = await _persist_campaign_with_rows(
        db,
        name=name,
        subject=subject,
        body_html=body_html,
        smtp_account_id=smtp_account_id,
        template_id=template_id,
        rows=rows,
        attachment_ids=ids,
    )
    background.add_task(campaign_runner.run_campaign, campaign.id)
    return _campaign_to_read(campaign)


@router.post(
    "/{campaign_id}/duplicate",
    response_model=CampaignRead,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_campaign(
    campaign_id: str,
    payload: CampaignDuplicateRequest,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> CampaignRead:
    """Clone a campaign (subject/body/recipients/attachments) and queue it fresh.

    The source campaign and its logs are left untouched.
    """
    source = await db.get(Campaign, campaign_id)
    if source is None:
        raise NotFoundError(f"Campaign {campaign_id} not found")

    stmt = select(EmailLog).where(EmailLog.campaign_id == campaign_id)
    if payload.recipients == "sent":
        stmt = stmt.where(EmailLog.status == EmailLogStatus.sent)
    elif payload.recipients == "failed":
        stmt = stmt.where(EmailLog.status == EmailLogStatus.failed)
    logs = (await db.execute(stmt)).scalars().all()

    rows: list[dict[str, Any]] = []
    for log in logs:
        merge = json.loads(log.merge_data) if log.merge_data else {}
        rows.append({"email": log.to_email, **merge})

    new_campaign = await _persist_campaign_with_rows(
        db,
        name=payload.name or f"{source.name} (resend)",
        subject=source.subject,
        body_html=source.body_html,
        smtp_account_id=source.smtp_account_id,
        template_id=source.template_id,
        rows=rows,
        attachment_ids=[],
    )
    await _clone_attachments(db, source.id, new_campaign.id)

    background.add_task(campaign_runner.run_campaign, new_campaign.id)
    return _campaign_to_read(new_campaign)


@router.get("/{campaign_id}", response_model=CampaignRead)
async def read_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)) -> CampaignRead:
    row = await db.get(Campaign, campaign_id)
    if row is None:
        raise NotFoundError(f"Campaign {campaign_id} not found")
    counts = await _counts_by_campaign(db, [campaign_id])
    sent, failed = counts[campaign_id]
    return _campaign_to_read(
        row,
        sent_count=sent,
        failed_count=failed,
        status=_derive_status(row, sent, failed),
    )


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)) -> None:
    """Delete a campaign, its logs, and its attachment blobs.

    Refuses while the campaign is still queued/running — cancel it first so the
    background sender isn't yanked mid-send.
    """
    campaign = await db.get(Campaign, campaign_id)
    if campaign is None:
        raise NotFoundError(f"Campaign {campaign_id} not found")
    if campaign.status in (CampaignStatus.queued, CampaignStatus.running):
        raise ValidationError("Cancel the campaign before deleting it")

    attachments = (
        (await db.execute(select(Attachment).where(Attachment.campaign_id == campaign_id)))
        .scalars()
        .all()
    )
    for a in attachments:
        attachment_store.delete(a.stored_name)

    # email_logs + attachment rows cascade via FK ON DELETE CASCADE.
    await db.delete(campaign)
    await db.commit()


@router.post("/{campaign_id}/cancel", response_model=CampaignRead)
async def cancel_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)) -> CampaignRead:
    row = await db.get(Campaign, campaign_id)
    if row is None:
        raise NotFoundError(f"Campaign {campaign_id} not found")
    if row.status in (CampaignStatus.queued, CampaignStatus.running):
        row.status = CampaignStatus.cancelled
        await db.commit()
        await db.refresh(row)
    return _campaign_to_read(row)


@router.post("/{campaign_id}/retry-failed", response_model=CampaignRead)
async def retry_failed(
    campaign_id: str,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> CampaignRead:
    campaign = await db.get(Campaign, campaign_id)
    if campaign is None:
        raise NotFoundError(f"Campaign {campaign_id} not found")
    if campaign.status in (CampaignStatus.queued, CampaignStatus.running):
        raise ValidationError("Campaign is still running")

    n = await db.scalar(
        select(func.count())
        .select_from(EmailLog)
        .where(
            EmailLog.campaign_id == campaign_id,
            EmailLog.status == EmailLogStatus.failed,
        )
    )
    if not n:
        counts = await _counts_by_campaign(db, [campaign_id])
        sent, failed = counts[campaign_id]
        return _campaign_to_read(
            campaign, sent_count=sent, failed_count=failed, status=_derive_status(campaign, sent, failed)
        )

    await db.execute(
        update(EmailLog)
        .where(
            EmailLog.campaign_id == campaign_id,
            EmailLog.status == EmailLogStatus.failed,
        )
        .values(status=EmailLogStatus.queued, error_message=None)
    )
    campaign.failed_count = max(0, campaign.failed_count - n)
    campaign.status = CampaignStatus.queued
    campaign.finished_at = None
    await db.commit()
    await db.refresh(campaign)

    background.add_task(campaign_runner.run_campaign, campaign_id)

    counts = await _counts_by_campaign(db, [campaign_id])
    sent, failed = counts[campaign_id]
    return _campaign_to_read(
        campaign, sent_count=sent, failed_count=failed, status=campaign.status
    )


@router.get("/{campaign_id}/logs", response_model=Page[EmailLogRead])
async def list_logs(
    campaign_id: str,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> Page[EmailLogRead]:
    campaign = await db.get(Campaign, campaign_id)
    if campaign is None:
        raise NotFoundError(f"Campaign {campaign_id} not found")
    rows = (
        (
            await db.execute(
                select(EmailLog)
                .where(EmailLog.campaign_id == campaign_id)
                .order_by(EmailLog.created_at)
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    total = campaign.total
    return Page(items=[_log_to_read(r) for r in rows], total=total, limit=limit, offset=offset)


@router.post("/logs/{log_id}/retry", response_model=EmailLogRead)
async def retry_log(
    log_id: str,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> EmailLogRead:
    row = await db.get(EmailLog, log_id)
    if row is None:
        raise NotFoundError(f"Log {log_id} not found")
    if row.status != EmailLogStatus.failed:
        raise ValidationError(f"Log {log_id} is not in failed status (current: {row.status})")
    background.add_task(campaign_runner.retry_log, log_id)
    return _log_to_read(row)
