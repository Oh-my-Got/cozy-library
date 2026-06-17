"""Resolve resource and runtime data paths.

Supports source execution, PyInstaller bundles, and legacy data migration.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys


def resource_path(relative_path: str | Path) -> Path:
    """Resolve resource paths in source mode and packaged PyInstaller builds."""
    path = Path(relative_path)
    if path.is_absolute():
        return path

    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base_path / path


def get_runtime_data_dir() -> Path:
    """Return the writable runtime data directory for the current platform."""
    if os.name == "nt":
        appdata_root = os.environ.get("APPDATA")
        if appdata_root:
            return Path(appdata_root) / "CozyLibrary"
        return Path.home() / "AppData" / "Roaming" / "CozyLibrary"

    return Path(__file__).resolve().parent.parent / "data"


def get_legacy_runtime_data_dirs() -> list[Path]:
    """Return older runtime data directories used by previous app names."""
    legacy_dirs: list[Path] = []
    if os.name == "nt":
        appdata_root = os.environ.get("APPDATA")
        if appdata_root:
            legacy_dirs.append(Path(appdata_root) / "BookshelfHabitTracker")
        else:
            legacy_dirs.append(Path.home() / "AppData" / "Roaming" / "BookshelfHabitTracker")
    return legacy_dirs


def get_runtime_data_path() -> Path:
    """Return the writable JSON data file path for the current platform."""
    return get_runtime_data_dir() / "habit_data.json"


def get_runtime_database_path() -> Path:
    """Return the writable SQLite database path for v2 storage."""
    return get_runtime_data_dir() / "cozy_library.db"


def migrate_legacy_runtime_data() -> None:
    """Move legacy runtime data into the current app data directory when needed."""
    target_dir = get_runtime_data_dir()
    if target_dir.exists():
        return

    for legacy_dir in get_legacy_runtime_data_dirs():
        if legacy_dir.exists():
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(legacy_dir), str(target_dir))
            return


def get_downloads_dir() -> Path:
    """Return a user-friendly Downloads directory for export defaults."""
    downloads_dir = Path.home() / "Downloads"
    if downloads_dir.exists():
        return downloads_dir
    return Path.home()
