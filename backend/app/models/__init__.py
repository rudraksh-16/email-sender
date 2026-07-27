"""SQLAlchemy ORM models.

Importing this package triggers every submodule so Alembic autogenerate and
Base.metadata see the full model graph.
"""

from __future__ import annotations

from app.models.attachment import Attachment, email_log_attachments
from app.models.base import Base, TimestampMixin, uuid_str
from app.models.campaign import Campaign, CampaignStatus, EmailLog, EmailLogStatus
from app.models.contact import Contact, ContactGroup, contact_group_members
from app.models.smtp_account import SmtpAccount
from app.models.template import Template

__all__ = [
    "Attachment",
    "Base",
    "Campaign",
    "CampaignStatus",
    "Contact",
    "ContactGroup",
    "EmailLog",
    "EmailLogStatus",
    "SmtpAccount",
    "Template",
    "TimestampMixin",
    "contact_group_members",
    "email_log_attachments",
    "uuid_str",
]
