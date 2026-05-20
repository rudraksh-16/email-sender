"""Domain exception types + FastAPI exception handler registration.

Routers / services raise `AppError` subclasses; the registered handler maps
them to a stable JSON envelope: ``{"error": {"code": ..., "message": ...}}``.
Adding a new error type means adding a subclass — no per-route try/except.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request


class AppError(Exception):
    """Base for all application errors."""

    status_code: int = 500
    code: str = "app_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"


class SmtpSendError(AppError):
    status_code = 502
    code = "smtp_send_error"


class RateLimitedError(AppError):
    status_code = 429
    code = "rate_limited"


async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)
