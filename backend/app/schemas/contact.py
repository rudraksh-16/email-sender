from __future__ import annotations

from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import TimestampedDTO


class ContactBase(BaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    extra: dict[str, Any] | None = None


class ContactRead(ContactBase, TimestampedDTO):
    id: str


class ContactImportResult(BaseModel):
    created: int
    updated: int
    skipped: int
    errors: list[str] = Field(default_factory=list)
