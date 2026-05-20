"""Pydantic v2 DTOs — the wire contract.

Request/Response models per resource. ORM models live in ``app.models``;
routers must never return models directly — convert via ``model_validate`` so
internal fields (password_encrypted, etc.) don't leak.
"""
