"""Thin wrapper around email-validator."""

from __future__ import annotations

from email_validator import EmailNotValidError, validate_email

from app.utils.errors import ValidationError


def normalise_email(address: str) -> str:
    try:
        info = validate_email(address, check_deliverability=False)
    except EmailNotValidError as exc:
        raise ValidationError(f"Invalid email: {address}") from exc
    return info.normalized
