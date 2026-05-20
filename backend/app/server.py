from __future__ import annotations

import asyncio
import threading

import uvicorn


def run_server(port: int, ready: threading.Event) -> None:
    # Import lazily so the FastAPI app constructs inside the server thread's loop context.
    from app.main import app

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        loop="asyncio",
        access_log=False,
    )
    server = uvicorn.Server(config)

    async def serve() -> None:
        task = asyncio.create_task(server.serve())
        while not server.started:
            await asyncio.sleep(0.05)
        ready.set()
        await task

    asyncio.run(serve())
