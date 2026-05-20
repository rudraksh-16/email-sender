"""Contact groups CRUD + membership management.

Planned endpoints:
    GET/POST/PATCH/DELETE /[/{id}]
    POST   /{id}/members/{contact_id}    add member
    DELETE /{id}/members/{contact_id}    remove member
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()
