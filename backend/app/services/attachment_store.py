"""On-disk attachment storage under user_data_dir/attachments."""
from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

from app.config import get_settings
from app.utils.errors import ValidationError


def _ensure_dir() -> Path:
    d = get_settings().attachment_dir
    d.mkdir(parents=True, exist_ok=True)
    return d


def _check_size_and_mime(size_bytes: int, mime_type: str) -> None:
    settings = get_settings()
    max_bytes = settings.MAX_ATTACHMENT_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise ValidationError(
            f"Attachment too large ({size_bytes} bytes > {max_bytes})"
        )
    if mime_type not in settings.ALLOWED_ATTACHMENT_MIMES:
        raise ValidationError(f"Disallowed MIME type: {mime_type}")


def store_bytes(data: bytes, *, filename: str, mime_type: str) -> tuple[str, int]:
    """Persist `data` under a UUID name. Return (stored_name, size_bytes)."""
    size = len(data)
    _check_size_and_mime(size, mime_type)
    stored_dir = _ensure_dir()
    stored_name = uuid.uuid4().hex + Path(filename).suffix.lower()
    dest = stored_dir / stored_name
    with dest.open("wb") as fh:
        fh.write(data)
    os.chmod(dest, 0o600)
    return stored_name, size


def open_blob(stored_name: str):
    path = _ensure_dir() / stored_name
    if not path.exists():
        raise ValidationError(f"Attachment missing on disk: {stored_name}")
    return path.open("rb")


def read_bytes(stored_name: str) -> bytes:
    path = _ensure_dir() / stored_name
    if not path.exists():
        raise ValidationError(f"Attachment missing on disk: {stored_name}")
    return path.read_bytes()


def delete(stored_name: str) -> None:
    path = _ensure_dir() / stored_name
    path.unlink(missing_ok=True)


def wipe_all() -> None:
    """Test helper — nuke the attachment dir."""
    d = get_settings().attachment_dir
    if d.exists():
        shutil.rmtree(d)
