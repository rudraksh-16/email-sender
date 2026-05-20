"""aiosmtplib wrapper: connect, AUTH, send EmailMessage."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from email.message import EmailMessage

import aiosmtplib

from app.models.smtp_account import SmtpAccount
from app.services.crypto import decrypt
from app.utils.errors import SmtpSendError

logger = logging.getLogger(__name__)


@dataclass
class Attachment:
    filename: str
    content: bytes
    mime_type: str


@dataclass
class SendRequest:
    to: str
    subject: str
    body_html: str
    body_text: str | None = None
    attachments: list[Attachment] | None = None
    reply_to: str | None = None


@dataclass
class SendResult:
    accepted: bool
    message_id: str | None
    info: str | None


def build_message(account: SmtpAccount, req: SendRequest) -> EmailMessage:
    msg = EmailMessage()
    sender = account.from_email
    if account.from_name:
        sender = f"{account.from_name} <{account.from_email}>"
    msg["From"] = sender
    msg["To"] = req.to
    msg["Subject"] = req.subject
    if req.reply_to:
        msg["Reply-To"] = req.reply_to

    text_part = req.body_text or ""
    msg.set_content(text_part or " ")
    msg.add_alternative(req.body_html, subtype="html")

    for att in req.attachments or []:
        maintype, _, subtype = att.mime_type.partition("/")
        if not subtype:
            maintype, subtype = "application", "octet-stream"
        msg.get_payload()  # ensure structure
        msg.add_attachment(
            att.content,
            maintype=maintype,
            subtype=subtype,
            filename=att.filename,
        )
    return msg


async def send(account: SmtpAccount, req: SendRequest) -> SendResult:
    msg = build_message(account, req)
    password = decrypt(account.password_encrypted) or None
    try:
        result = await aiosmtplib.send(
            msg,
            hostname=account.host,
            port=account.port,
            username=account.username or None,
            password=password,
            use_tls=account.use_ssl,
            start_tls=account.use_tls and not account.use_ssl,
            timeout=30,
        )
    except (aiosmtplib.SMTPException, OSError) as exc:
        logger.warning("SMTP send failed to %s: %s", req.to, exc)
        raise SmtpSendError(str(exc)) from exc

    info = None
    if isinstance(result, tuple) and len(result) == 2:
        _resp, info = result
    return SendResult(accepted=True, message_id=msg.get("Message-ID"), info=str(info))


async def test_connection(account: SmtpAccount) -> None:
    """Open connection + AUTH + NOOP + QUIT. Raises SmtpSendError on failure."""
    password = decrypt(account.password_encrypted) or None
    client = aiosmtplib.SMTP(
        hostname=account.host,
        port=account.port,
        use_tls=account.use_ssl,
        start_tls=False,
        timeout=15,
    )
    try:
        await client.connect()
        if account.use_tls and not account.use_ssl:
            await client.starttls()
        if account.username and password:
            await client.login(account.username, password)
        await client.noop()
    except (aiosmtplib.SMTPException, OSError) as exc:
        raise SmtpSendError(str(exc)) from exc
    finally:
        try:
            await client.quit()
        except Exception:  # noqa: BLE001
            pass
