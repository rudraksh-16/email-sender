"""Jinja2 sandboxed renderer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from jinja2 import StrictUndefined
from jinja2.sandbox import SandboxedEnvironment

from app.utils.errors import ValidationError

_env = SandboxedEnvironment(undefined=StrictUndefined, autoescape=False)


def render(template_str: str, data: Mapping[str, Any]) -> str:
    try:
        return _env.from_string(template_str).render(**data)
    except Exception as exc:  # noqa: BLE001 — surface any render error as a 422
        raise ValidationError(f"Template render error: {exc}") from exc
