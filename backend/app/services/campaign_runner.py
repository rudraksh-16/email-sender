"""Bulk-send orchestrator.

Spawned by FastAPI BackgroundTasks per campaign. Pulls queued EmailLog rows,
renders + sanitises + sends each, updates status, respects the rate limiter.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.db import get_session_factory
from app.models import (
    Attachment,
    Campaign,
    CampaignStatus,
    EmailLog,
    EmailLogStatus,
    SmtpAccount,
)
from app.services import attachment_store, html_sanitizer, mail_merge, smtp_sender, text_fallback
from app.services.rate_limiter import default_limiter
from app.services.smtp_sender import Attachment as SmtpAttachment, SendRequest
from app.utils.errors import SmtpSendError

logger = logging.getLogger(__name__)


async def _load_attachments(campaign_id: str) -> list[SmtpAttachment]:
    Session = get_session_factory()
    async with Session() as session:
        rows = (
            (await session.execute(select(Attachment).where(Attachment.campaign_id == campaign_id)))
            .scalars()
            .all()
        )
        return [
            SmtpAttachment(
                filename=row.filename,
                content=attachment_store.read_bytes(row.stored_name),
                mime_type=row.mime_type,
            )
            for row in rows
        ]


async def _process_row(
    session,
    campaign: Campaign,
    account: SmtpAccount,
    log: EmailLog,
    attachments: list[SmtpAttachment],
) -> bool:
    """Render + send one EmailLog. Returns True on success."""
    log.status = EmailLogStatus.sending
    log.attempts += 1
    await session.commit()

    try:
        await default_limiter().acquire(
            account.id,
            per_minute=account.max_per_minute,
            per_hour=account.max_per_hour,
        )

        merge = json.loads(log.merge_data) if log.merge_data else {}
        subject = mail_merge.render(campaign.subject, merge)
        body_raw = mail_merge.render(campaign.body_html, merge)
        body_html = html_sanitizer.sanitize(body_raw)
        body_text = text_fallback.to_text(body_html)

        await smtp_sender.send(
            account,
            SendRequest(
                to=log.to_email,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                attachments=attachments,
            ),
        )

        log.status = EmailLogStatus.sent
        log.subject_rendered = subject
        log.body_html_rendered = body_html
        log.sent_at = datetime.now(timezone.utc)
        log.error_message = None
        return True
    except SmtpSendError as exc:
        log.status = EmailLogStatus.failed
        log.error_message = exc.message
        return False
    except Exception as exc:  # noqa: BLE001
        log.status = EmailLogStatus.failed
        log.error_message = f"{type(exc).__name__}: {exc}"
        return False
    finally:
        await session.commit()


async def run_campaign(campaign_id: str) -> None:
    Session = get_session_factory()
    logger.info("Starting campaign %s", campaign_id)
    attachments = await _load_attachments(campaign_id)

    async with Session() as session:
        campaign = await session.get(Campaign, campaign_id)
        if campaign is None:
            logger.warning("Campaign %s not found", campaign_id)
            return
        if campaign.status not in (CampaignStatus.queued, CampaignStatus.running):
            logger.info("Campaign %s not runnable (status=%s)", campaign_id, campaign.status)
            return
        account = await session.get(SmtpAccount, campaign.smtp_account_id)
        if account is None:
            campaign.status = CampaignStatus.failed
            await session.commit()
            return

        campaign.status = CampaignStatus.running
        campaign.started_at = datetime.now(timezone.utc)
        await session.commit()

        while True:
            # Re-check status (cancel support).
            refreshed = await session.get(Campaign, campaign_id)
            if refreshed and refreshed.status == CampaignStatus.cancelled:
                logger.info("Campaign %s cancelled", campaign_id)
                return

            log = (
                await session.execute(
                    select(EmailLog)
                    .where(
                        EmailLog.campaign_id == campaign_id,
                        EmailLog.status.in_([EmailLogStatus.queued, EmailLogStatus.retrying]),
                    )
                    .limit(1)
                )
            ).scalar_one_or_none()

            if log is None:
                break

            ok = await _process_row(session, campaign, account, log, attachments)
            if ok:
                campaign.sent_count += 1
            else:
                campaign.failed_count += 1
            await session.commit()
            # Tiny yield to keep responsiveness under heavy loops.
            await asyncio.sleep(0)

        campaign.status = (
            CampaignStatus.done if campaign.failed_count == 0 else CampaignStatus.failed
        )
        campaign.finished_at = datetime.now(timezone.utc)
        await session.commit()
        logger.info(
            "Campaign %s finished sent=%s failed=%s",
            campaign_id,
            campaign.sent_count,
            campaign.failed_count,
        )


async def retry_log(log_id: str) -> bool:
    Session = get_session_factory()
    async with Session() as session:
        log = await session.get(EmailLog, log_id)
        if log is None:
            return False
        if log.campaign_id is None:
            return False
        campaign = await session.get(Campaign, log.campaign_id)
        if campaign is None:
            return False
        account = await session.get(SmtpAccount, campaign.smtp_account_id)
        if account is None:
            return False
        attachments = await _load_attachments(campaign.id)
        was_failed = log.status == EmailLogStatus.failed
        log.status = EmailLogStatus.retrying
        await session.commit()
        ok = await _process_row(session, campaign, account, log, attachments)
        # Reconcile campaign counters.
        if was_failed and ok:
            campaign.failed_count = max(0, campaign.failed_count - 1)
            campaign.sent_count += 1
            if campaign.status == CampaignStatus.failed and campaign.failed_count == 0:
                campaign.status = CampaignStatus.done
            await session.commit()
        return ok
