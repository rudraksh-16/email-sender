"""Contacts CRUD + CSV import.

Planned endpoints:
    GET    /            list (paginated, searchable)
    POST   /            create
    GET    /{id}        read
    PATCH  /{id}        update
    DELETE /{id}        delete
    POST   /import      streamed CSV upload (row cap 50_000)
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()
