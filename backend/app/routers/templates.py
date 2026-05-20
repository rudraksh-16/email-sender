"""Email templates CRUD + preview render.

Planned endpoints:
    GET/POST/PATCH/DELETE /[/{id}]
    POST /{id}/preview      render subject + body against sample merge data

Bodies are stored as raw HTML; rendering goes through
``app.services.mail_merge`` (Jinja sandbox) then ``html_sanitizer`` (bleach).
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()
