from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class SingleSendRequest(BaseModel):
    smtp_account_id: str
    to: EmailStr
    subject: str
    body_html: str
    reply_to: EmailStr | None = None
    attachment_ids: list[str] = Field(default_factory=list)


class SingleSendResult(BaseModel):
    accepted: bool
    message_id: str | None = None
    info: str | None = None
