"""Single-message send (no campaign tracking).

Planned endpoint:
    POST /        send one email immediately, return SmtpSendResult

For anything more than one recipient use the campaigns router so progress
and retries are tracked in the DB.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()
