"""Attachment upload + retrieval.

Planned endpoints:
    POST   /            multipart upload (size + MIME allowlist enforced)
    GET    /{id}        download
    DELETE /{id}

Storage is on disk under ``user_data_dir/attachments`` with UUID filenames;
see ``app.services.attachment_store``.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()
