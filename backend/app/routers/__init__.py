"""HTTP routers aggregated into a single APIRouter, mounted under /api.

Each resource has its own module so feature work touches one file. The
aggregator below wires them with stable URL prefixes + tags; adding a new
resource means a new module + one line here.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.routers import (
    attachments,
    campaigns,
    contacts,
    groups,
    health,
    send,
    smtp_accounts,
    system,
    templates,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(system.router, tags=["system"])
api_router.include_router(smtp_accounts.router, prefix="/smtp-accounts", tags=["smtp"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(groups.router, prefix="/groups", tags=["groups"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(send.router, prefix="/send", tags=["send"])
api_router.include_router(attachments.router, prefix="/attachments", tags=["attachments"])
