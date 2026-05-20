from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedDTO


class TemplateBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    subject: str = Field(min_length=1, max_length=255)
    body_html: str
    body_text: str | None = None
    default_smtp_account_id: str | None = None


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: str | None = None
    subject: str | None = None
    body_html: str | None = None
    body_text: str | None = None
    default_smtp_account_id: str | None = None


class TemplateRead(TemplateBase, TimestampedDTO):
    id: str


class TemplatePreviewRequest(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)


class TemplatePreviewResult(BaseModel):
    subject: str
    body_html: str
    body_text: str
