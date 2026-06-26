from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.paths import user_data_path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="EMAIL_APP_",
        env_file=".env",
        extra="ignore",
    )

    DEV_MODE: bool = False
    HEADLESS: bool = False
    BIND_HOST: str = "127.0.0.1"
    DEV_FRONTEND_URL: str = "http://localhost:5173"

    # Storage
    DATABASE_URL: str | None = None  # async URL; defaults to user-data sqlite
    KEY_FILE: Path | None = None  # Fernet key path; defaults to user-data
    ATTACHMENT_DIR: Path | None = None

    # Limits
    MAX_ATTACHMENT_MB: int = 25
    CSV_ROW_CAP: int = 50_000

    # Pre-flight verification
    VERIFY_CHECK_MX: bool = True  # DNS MX lookup per domain; disable for offline/tests

    # Allowed attachment MIME types (declared by client; extension-checked too).
    ALLOWED_ATTACHMENT_MIMES: tuple[str, ...] = (
        "application/pdf",
        "application/zip",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/webp",
        "text/plain",
        "text/csv",
    )

    @property
    def data_dir(self) -> Path:
        return user_data_path()

    @property
    def db_path(self) -> Path:
        return self.data_dir / "app.db"

    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"sqlite+aiosqlite:///{self.db_path}"

    @property
    def sync_database_url(self) -> str:
        # Alembic uses sync drivers.
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace("+aiosqlite", "")
        return f"sqlite:///{self.db_path}"

    @property
    def key_file(self) -> Path:
        return self.KEY_FILE or (self.data_dir / "key")

    @property
    def attachment_dir(self) -> Path:
        return self.ATTACHMENT_DIR or (self.data_dir / "attachments")


@lru_cache
def get_settings() -> Settings:
    return Settings()
