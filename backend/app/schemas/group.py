from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedDTO
from app.schemas.contact import ContactRead


class ContactGroupBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class ContactGroupCreate(ContactGroupBase):
    pass


class ContactGroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ContactGroupRead(ContactGroupBase, TimestampedDTO):
    id: str
    contact_count: int = 0


class ContactGroupDetail(ContactGroupRead):
    contacts: list[ContactRead] = Field(default_factory=list)
