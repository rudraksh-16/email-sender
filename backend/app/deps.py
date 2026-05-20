"""FastAPI dependency providers."""
from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings as _get_settings
from app.db import get_db as _get_db


def get_settings() -> Settings:
    return _get_settings()


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in _get_db():
        yield session
