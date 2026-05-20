from __future__ import annotations

from sqlalchemy import Column, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_str

contact_group_members = Table(
    "contact_group_members",
    Base.metadata,
    Column(
        "contact_id", String(36), ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "group_id",
        String(36),
        ForeignKey("contact_groups.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Contact(Base, TimestampMixin):
    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    first_name: Mapped[str | None] = mapped_column(String(120))
    last_name: Mapped[str | None] = mapped_column(String(120))
    extra_json: Mapped[str | None] = mapped_column(Text)  # JSON-encoded merge fields

    groups: Mapped[list["ContactGroup"]] = relationship(
        secondary=contact_group_members, back_populates="contacts"
    )


class ContactGroup(Base, TimestampMixin):
    __tablename__ = "contact_groups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    contacts: Mapped[list[Contact]] = relationship(
        secondary=contact_group_members, back_populates="groups"
    )
