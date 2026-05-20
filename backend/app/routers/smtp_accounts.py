"""SMTP account CRUD + connection test.

Planned endpoints:
    GET    /                list accounts
    POST   /                create
    GET    /{id}            read
    PATCH  /{id}            update
    DELETE /{id}            delete
    POST   /{id}/test       connection check

Passwords are Fernet-encrypted in the DB via ``app.services.crypto``; no
response ever returns the plaintext.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()
