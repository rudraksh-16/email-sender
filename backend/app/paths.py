from __future__ import annotations

import sys
from pathlib import Path

from platformdirs import user_data_dir as _platform_user_data_dir


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def resource_dir() -> Path:
    if is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # repo root = backend/app/paths.py -> parents[2]
    return Path(__file__).resolve().parents[2]


def user_data_path() -> Path:
    return Path(_platform_user_data_dir("EmailApp", "rohit"))


def ensure_user_dirs() -> None:
    root = user_data_path()
    root.mkdir(parents=True, exist_ok=True)
    root.chmod(0o700)
    (root / "attachments").mkdir(exist_ok=True)
    (root / "attachments").chmod(0o700)
