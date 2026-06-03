"""Manage Windows startup shortcuts.

Creates and removes Startup-folder shortcuts for packaged Cozy Library builds.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


class StartupService:
    """Create or remove the packaged app startup shortcut."""

    SHORTCUT_NAME = "Cozy Library.lnk"
    LEGACY_SHORTCUT_NAMES = ("Bookshelf Habit Tracker.lnk",)

    def __init__(self, *, icon_path: Path | None = None) -> None:
        self._icon_path = Path(icon_path) if icon_path is not None else None

    @property
    def is_supported(self) -> bool:
        return os.name == "nt" and bool(getattr(sys, "frozen", False))

    @property
    def startup_folder(self) -> Path:
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise RuntimeError("APPDATA is not available.")
        return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

    @property
    def shortcut_path(self) -> Path:
        return self.startup_folder / self.SHORTCUT_NAME

    @property
    def legacy_shortcut_paths(self) -> list[Path]:
        return [self.startup_folder / shortcut_name for shortcut_name in self.LEGACY_SHORTCUT_NAMES]

    def is_startup_enabled(self) -> bool:
        return self.shortcut_path.exists()

    def enable_startup(self) -> None:
        """Create a Windows Startup shortcut for the packaged executable."""
        if not self.is_supported:
            raise RuntimeError("Startup shortcuts are only supported for packaged Windows builds.")

        target_path = Path(sys.executable).resolve()
        self.startup_folder.mkdir(parents=True, exist_ok=True)
        for legacy_shortcut_path in self.legacy_shortcut_paths:
            if legacy_shortcut_path.exists():
                legacy_shortcut_path.unlink()

        icon_location = ""
        if self._icon_path is not None and self._icon_path.exists():
            icon_location = str(self._icon_path.resolve())

        command = (
            "$shell = New-Object -ComObject WScript.Shell; "
            f"$shortcut = $shell.CreateShortcut('{self.shortcut_path}'); "
            f"$shortcut.TargetPath = '{target_path}'; "
            "$shortcut.Arguments = '--start-hidden'; "
            f"$shortcut.WorkingDirectory = '{target_path.parent}'; "
        )
        if icon_location:
            command += f"$shortcut.IconLocation = '{icon_location}'; "
        command += "$shortcut.Save();"

        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            check=True,
            capture_output=True,
            text=True,
        )

    def disable_startup(self) -> None:
        if self.shortcut_path.exists():
            self.shortcut_path.unlink()
        for legacy_shortcut_path in self.legacy_shortcut_paths:
            if legacy_shortcut_path.exists():
                legacy_shortcut_path.unlink()
