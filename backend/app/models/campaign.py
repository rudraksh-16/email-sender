from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid_str


class CampaignStatus(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"
    cancelled = "cancelled"


class EmailLogStatus(str, Enum):
    queued = "queued"
    sending = "sending"
    sent = "sent"
    failed = "failed"
    retrying = "retrying"


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    smtp_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("smtp_accounts.id", ondelete="RESTRICT"), nullable=False
    )
    template_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("templates.id", ondelete="SET NULL")
    )
    status: Mapped[CampaignStatus] = mapped_column(
        SQLEnum(CampaignStatus, native_enum=False, length=20),
        default=CampaignStatus.queued,
        nullable=False,
        index=True,
    )
    total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)


class EmailLog(Base, TimestampMixin):
    __tablename__ = "email_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    campaign_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    to_email: Mapped[str] = mapped_column(String(255), nullable=False)
    merge_data: Mapped[str | None] = mapped_column(Text)  # JSON
    subject_rendered: Mapped[str | None] = mapped_column(String(255))
    body_html_rendered: Mapped[str | None] = mapped_column(Text)
    status: Mapped[EmailLogStatus] = mapped_column(
        SQLEnum(EmailLogStatus, native_enum=False, length=20),
        default=EmailLogStatus.queued,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime)

    __table_args__ = (
        Index("ix_email_logs_campaign_status", "campaign_id", "status"),
        Index("ix_email_logs_status_created_at", "status", "created_at"),
    )
