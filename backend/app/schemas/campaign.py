from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field

from app.models.campaign import CampaignStatus, EmailLogStatus
from app.schemas.common import TimestampedDTO


class Recipient(BaseModel):
    email: EmailStr
    data: dict[str, Any] = Field(default_factory=dict)


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    subject: str
    body_html: str
    smtp_account_id: str
    template_id: str | None = None
    recipients: list[Recipient] = Field(default_factory=list)
    attachment_ids: list[str] = Field(default_factory=list)


class CampaignRead(TimestampedDTO):
    id: str
    name: str
    subject: str
    body_html: str
    smtp_account_id: str
    template_id: str | None
    status: CampaignStatus
    total: int
    sent_count: int
    failed_count: int
    started_at: datetime | None
    finished_at: datetime | None


class EmailLogRead(TimestampedDTO):
    id: str
    campaign_id: str | None
    to_email: str
    merge_data: dict[str, Any] | None
    subject_rendered: str | None
    body_html_rendered: str | None
    status: EmailLogStatus
    error_message: str | None
    attempts: int
    sent_at: datetime | None


class CampaignDuplicateRequest(BaseModel):
    """Clone an existing campaign into a fresh one and queue it.

    `recipients` scopes which of the source campaign's recipients carry over:
    all of them, only those that sent successfully, or only those that failed.
    """

    name: str | None = Field(default=None, max_length=255)
    recipients: Literal["all", "sent", "failed"] = "all"


class CampaignFromCsvRequest(BaseModel):
    """JSON wrapper used by /from-csv after the CSV is parsed client-side.

    For server-side CSV parsing we use a multipart endpoint instead.
    """

    name: str
    subject: str
    body_html: str
    smtp_account_id: str
    template_id: str | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)
    attachment_ids: list[str] = Field(default_factory=list)
