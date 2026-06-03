"""Provide uninstall cleanup helpers.

Removes startup shortcuts, runtime data, and packaged executable files.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

from .path_utils import get_legacy_runtime_data_dirs, get_runtime_data_dir
from .startup_service import StartupService


class UninstallService:
    """Remove startup hooks, runtime data, and packaged executable files."""

    def __init__(self, *, startup_service: StartupService) -> None:
        self._startup_service = startup_service
        self._runtime_data_dir = get_runtime_data_dir()
        self._legacy_runtime_data_dirs = get_legacy_runtime_data_dirs()

    @property
    def can_self_delete_executable(self) -> bool:
        return os.name == "nt" and bool(getattr(sys, "frozen", False))

    def remove_startup_shortcut(self) -> None:
        self._startup_service.disable_startup()

    def clear_runtime_data(self) -> None:
        if self._runtime_data_dir.exists():
            shutil.rmtree(self._runtime_data_dir, ignore_errors=False)
        for legacy_runtime_data_dir in self._legacy_runtime_data_dirs:
            if legacy_runtime_data_dir.exists():
                shutil.rmtree(legacy_runtime_data_dir, ignore_errors=False)

    def schedule_packaged_uninstall(self) -> None:
        """Schedule delayed self-removal for a packaged Windows executable."""
        if not self.can_self_delete_executable:
            raise RuntimeError("Executable self-removal is only supported for packaged Windows builds.")

        executable_path = Path(sys.executable).resolve()
        runtime_dir = self._runtime_data_dir.resolve()
        legacy_cleanup = " ".join(
            f'& rmdir /s /q "{legacy_runtime_dir.resolve()}"'
            for legacy_runtime_dir in self._legacy_runtime_data_dirs
            if legacy_runtime_dir.exists()
        )
        parent_dir = executable_path.parent.resolve()

        command = (
            f'timeout /t 2 /nobreak >nul & '
            f'del /f /q "{executable_path}" & '
            f'rmdir /s /q "{runtime_dir}" & '
            f'{legacy_cleanup} '
            f'rd "{parent_dir}" 2>nul'
        )

        subprocess.Popen(
            ["cmd", "/c", command],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            close_fds=True,
        )
