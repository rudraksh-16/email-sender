from __future__ import annotations

import sys
import threading

from app.config import get_settings


def main() -> None:
    settings = get_settings()
    if settings.HEADLESS:
        # Headless: just run uvicorn on a fixed port for smoke testing / curl.
        import socket

        from app.server import run_server

        port_env = 8765
        # Probe if port is taken; fall back to ephemeral.
        try:
            with socket.socket() as s:
                s.bind(("127.0.0.1", port_env))
            port = port_env
        except OSError:
            with socket.socket() as s:
                s.bind(("127.0.0.1", 0))
                port = s.getsockname()[1]

        ready = threading.Event()
        print(f"[email-app] headless on http://127.0.0.1:{port}", flush=True)
        # Run in foreground (block) — no webview.
        run_server(port, ready)
        return

    from app.desktop import launch

    launch()


if __name__ == "__main__":
    sys.exit(main())
