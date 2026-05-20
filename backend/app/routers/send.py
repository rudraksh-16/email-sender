"""Single-message send (no campaign tracking)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.models.attachment import Attachment
from app.models.smtp_account import SmtpAccount
from app.schemas.send import SingleSendRequest, SingleSendResult
from app.services import attachment_store, html_sanitizer, smtp_sender, text_fallback
from app.services.smtp_sender import Attachment as SmtpAttachment, SendRequest
from app.utils.errors import NotFoundError, SmtpSendError

router = APIRouter()


@router.post("", response_model=SingleSendResult)
async def send_single(
    payload: SingleSendRequest, db: AsyncSession = Depends(get_db)
) -> SingleSendResult:
    account = await db.get(SmtpAccount, payload.smtp_account_id)
    if account is None:
        raise NotFoundError(f"SMTP account {payload.smtp_account_id} not found")

    attachments: list[SmtpAttachment] = []
    if payload.attachment_ids:
        rows = (
            await db.execute(select(Attachment).where(Attachment.id.in_(payload.attachment_ids)))
        ).scalars().all()
        for row in rows:
            attachments.append(
                SmtpAttachment(
                    filename=row.filename,
                    content=attachment_store.read_bytes(row.stored_name),
                    mime_type=row.mime_type,
                )
            )

    body_html = html_sanitizer.sanitize(payload.body_html)
    body_text = text_fallback.to_text(body_html)

    try:
        result = await smtp_sender.send(
            account,
            SendRequest(
                to=payload.to,
                subject=payload.subject,
                body_html=body_html,
                body_text=body_text,
                attachments=attachments,
                reply_to=payload.reply_to,
            ),
        )
    except SmtpSendError as exc:
        return SingleSendResult(accepted=False, info=exc.message)

    return SingleSendResult(
        accepted=result.accepted,
        message_id=result.message_id,
        info=result.info,
    )
