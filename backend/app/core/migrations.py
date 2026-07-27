"""Run Alembic migrations programmatically on app startup."""

from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.config import get_settings
from app.paths import resource_dir

logger = logging.getLogger(__name__)


def _alembic_config() -> Config:
    settings = get_settings()
    cfg = Config()
    script_location = resource_dir() / "backend" / "alembic"
    cfg.set_main_option("script_location", str(script_location))
    cfg.set_main_option("sqlalchemy.url", settings.sync_database_url)
    return cfg


def upgrade_to_head() -> None:
    cfg = _alembic_config()
    # Ensure the DB file's parent exists before sqlite tries to open it.
    settings = get_settings()
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    logger.info("Running alembic upgrade head against %s", settings.db_path)
    command.upgrade(cfg, "head")
