"""Fernet encryption for SMTP credentials.

Key lives under ``user_data_dir/key`` (0o600). Auto-generated on first use.
Plaintext is never logged.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from cryptography.fernet import Fernet

from app.config import get_settings


def _load_or_create_key(path: Path) -> bytes:
    if path.exists():
        return path.read_bytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    key = Fernet.generate_key()
    path.write_bytes(key)
    path.chmod(0o600)
    return key


@lru_cache(maxsize=1)
def get_fernet() -> Fernet:
    settings = get_settings()
    key = _load_or_create_key(settings.key_file)
    return Fernet(key)


def encrypt(plaintext: str) -> bytes:
    if not plaintext:
        return b""
    return get_fernet().encrypt(plaintext.encode("utf-8"))


def decrypt(ciphertext: bytes | None) -> str:
    if not ciphertext:
        return ""
    return get_fernet().decrypt(ciphertext).decode("utf-8")
