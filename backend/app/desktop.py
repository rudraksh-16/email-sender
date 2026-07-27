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


class SaveApi:
    """JS bridge for saving files from the SPA.

    WKWebView ignores the HTML ``<a download>`` attribute, so a browser-style
    download just navigates the window away and unmounts the app. Instead the
    frontend calls this over ``window.pywebview.api`` to get a native Save
    dialog and write the file itself — the page never navigates.
    """

    def __init__(self) -> None:
        self.window: webview.Window | None = None

    def save_csv(self, filename: str, content: str) -> bool:
        if self.window is None:
            return False
        result = self.window.create_file_dialog(
            webview.FileDialog.SAVE, save_filename=filename
        )
        if not result:
            return False  # user cancelled
        path = result[0] if isinstance(result, (list, tuple)) else result
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        return True


def launch() -> None:
    settings = get_settings()
    port = _pick_free_port()
    ready = threading.Event()
    t = threading.Thread(target=run_server, args=(port, ready), daemon=True)
    t.start()
    if not ready.wait(timeout=10):
        raise RuntimeError("Backend failed to start within 10s")

    url = settings.DEV_FRONTEND_URL if settings.DEV_MODE else f"http://127.0.0.1:{port}/"

    api = SaveApi()
    api.window = webview.create_window(
        title="Email App",
        url=url,
        width=1280,
        height=860,
        min_size=(960, 640),
        confirm_close=True,
        text_select=True,
        js_api=api,
    )
    # In dev mode the SPA reads the backend port via a meta tag from /api/__config;
    # expose it through query string for the dev server too.
    webview.start()
