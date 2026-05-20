"""Runtime config endpoint.

The SPA fetches this at boot to discover the API base URL. In bundled mode
the SPA is served same-origin so apiBase is empty; in Vite dev mode the
desktop bootstrap can inject the random backend port here.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/__config")
async def runtime_config() -> dict[str, str]:
    return {"apiBase": ""}
