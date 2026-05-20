"""Bulk-send campaigns: queue jobs, watch progress, retry failed rows."""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Form, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.models import Attachment, Campaign, CampaignStatus, EmailLog, EmailLogStatus, SmtpAccount
from app.schemas.campaign import CampaignCreate, CampaignRead, EmailLogRead
from app.schemas.common import Page
from app.services import campaign_runner, csv_parser
from app.utils.errors import NotFoundError, ValidationError

router = APIRouter()


def _campaign_to_read(row: Campaign) -> CampaignRead:
    return CampaignRead(
        id=row.id,
        name=row.name,
        subject=row.subject,
        body_html=row.body_html,
        smtp_account_id=row.smtp_account_id,
        template_id=row.template_id,
        status=row.status,
        total=row.total,
        sent_count=row.sent_count,
        failed_count=row.failed_count,
        started_at=row.started_at,
        finished_at=row.finished_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


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
    rows = (
        await db.execute(select(Campaign).order_by(Campaign.created_at.desc()))
    ).scalars().all()
    return [_campaign_to_read(r) for r in rows]


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


@router.get("/{campaign_id}", response_model=CampaignRead)
async def read_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)) -> CampaignRead:
    row = await db.get(Campaign, campaign_id)
    if row is None:
        raise NotFoundError(f"Campaign {campaign_id} not found")
    return _campaign_to_read(row)


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
        await db.execute(
            select(EmailLog)
            .where(EmailLog.campaign_id == campaign_id)
            .order_by(EmailLog.created_at)
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()
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
    background.add_task(campaign_runner.retry_log, log_id)
    return _log_to_read(row)
