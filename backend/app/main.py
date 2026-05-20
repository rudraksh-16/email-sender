"""FastAPI application factory and static-frontend mount.

This module wires together the layers — config, logging, routers, exception
handlers, static SPA — into a single FastAPI instance. Process lifecycle
(uvicorn, pywebview) lives in `server.py` / `desktop.py` / `__main__.py`.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings, get_settings
from app.core.logging import configure_logging
from app.paths import ensure_user_dirs, resource_dir
from app.routers import api_router
from app.utils.errors import register_exception_handlers


_PLACEHOLDER_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Email App</title>
    <style>
      body { font-family: -apple-system, system-ui, sans-serif; padding: 2rem; color: #222; }
      code { background: #f3f3f3; padding: 0.1rem 0.35rem; border-radius: 4px; }
      a { color: #2962ff; }
    </style>
  </head>
  <body>
    <h1>Email App</h1>
    <p>Backend running. Frontend not built yet.</p>
    <p>Health: <a href="/api/health">/api/health</a></p>
  </body>
</html>
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    ensure_user_dirs()
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Email App", version="0.1.0", lifespan=lifespan)
    app.include_router(api_router, prefix="/api")
    register_exception_handlers(app)
    _mount_frontend(app)
    return app


def _mount_frontend(app: FastAPI) -> None:
    dist = resource_dir() / "frontend" / "dist"
    if dist.exists() and (dist / "index.html").exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
        return

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def _placeholder() -> str:
        return _PLACEHOLDER_HTML


app = create_app()
