from __future__ import annotations

import socket
import threading

import webview

from app.config import get_settings
from app.server import run_server


def _pick_free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def launch() -> None:
    settings = get_settings()
    port = _pick_free_port()
    ready = threading.Event()
    t = threading.Thread(target=run_server, args=(port, ready), daemon=True)
    t.start()
    if not ready.wait(timeout=10):
        raise RuntimeError("Backend failed to start within 10s")

    url = settings.DEV_FRONTEND_URL if settings.DEV_MODE else f"http://127.0.0.1:{port}/"

    webview.create_window(
        title="Email App",
        url=url,
        width=1280,
        height=860,
        min_size=(960, 640),
        confirm_close=True,
    )
    # In dev mode the SPA reads the backend port via a meta tag from /api/__config;
    # expose it through query string for the dev server too.
    webview.start()
