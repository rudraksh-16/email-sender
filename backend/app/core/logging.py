"""Process-wide logging configuration.

Called once from the FastAPI lifespan; idempotent so repeated calls (e.g. in
tests) don't stack handlers.
"""
from __future__ import annotations

import logging
import logging.config

_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)-7s %(name)s :: %(message)s",
                    "datefmt": "%H:%M:%S",
                },
            },
            "handlers": {
                "stderr": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
            },
            "root": {"level": level, "handlers": ["stderr"]},
            "loggers": {
                "uvicorn.error": {"level": level},
                "uvicorn.access": {"level": "WARNING"},
            },
        }
    )
    _CONFIGURED = True
