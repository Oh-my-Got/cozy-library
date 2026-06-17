"""Coordinate runtime storage for Cozy Library.

Uses SQLite for app data and keeps JSON validation for migration and import/export.
"""

from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path
import re
import shutil
from typing import overload

from .date_service import DateService
from .exceptions import ImportValidationError, StorageError, ValidationError
from .models import (
    DEFAULT_NOTIFICATION_MESSAGE,
    DEFAULT_NOTIFICATION_PLACEHOLDER,
    MAX_NOTIFICATION_TIMES,
    NotificationSettings,
    HabitData,
)
from .path_utils import get_runtime_database_path
from .storage_backend import StorageBackend
from .sqlite_storage_backend import SQLiteStorageBackend


TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


class StorageManager:
    """Manage runtime SQLite storage and JSON import/export compatibility."""

    def __init__(
        self,
        file_path: Path | str,
        date_service: DateService | None = None,
        database_path: Path | str | None = None,
    ) -> None:
        self.file_path = Path(file_path)
        self._date_service = date_service or DateService()
        self.database_path = Path(database_path) if database_path is not None else get_runtime_database_path()
        self._sqlite_backend: StorageBackend = SQLiteStorageBackend(self.database_path, date_service=self._date_service)
        self.last_warning: str | None = None
        self.created_default_on_load = False

    def load(self) -> HabitData:
        """Load the current habit data, creating or recovering it when needed."""
        self.last_warning = None
        self.created_default_on_load = False

        if self._sqlite_backend.exists():
            try:
                habit_data = self._sqlite_backend.load()
                habit_data.last_opened_at = self._current_timestamp()
                self.save(habit_data)
                return habit_data
            except StorageError as error:
                return self._recover_from_corrupted_database(error)

        if self.file_path.exists():
            habit_data = self._load_legacy_json_file()
            habit_data.last_opened_at = self._current_timestamp()
            self._sqlite_backend.save(habit_data)
            self.last_warning = "Legacy JSON data was migrated to SQLite. The JSON file was kept as a backup."
            return habit_data

        habit_data = self._create_default_data()
        self._sqlite_backend.save(habit_data)
        self.created_default_on_load = True
        return habit_data

    def _load_legacy_json_file(self) -> HabitData:
        """Load and validate the legacy runtime JSON file for migration."""
        try:
            return self._read_valid_json_file(self.file_path)
        except (OSError, json.JSONDecodeError, ValidationError, ValueError) as error:
            return self._recover_from_corrupted_json_file(error)

    def _read_valid_json_file(self, source_path: Path) -> HabitData:
        """Read a JSON file and validate it as persisted habit data."""
        with source_path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
        self.validate_json(raw_data)
        return HabitData.from_dict(raw_data)

    def save(self, habit_data: HabitData) -> None:
        """Save the current habit data to SQLite runtime storage."""
        self._sqlite_backend.save(habit_data)

    def validate_json(self, data: dict) -> None:
        """Validate raw JSON data against the saved-state schema."""
        if not isinstance(data, dict):
            raise ValidationError("Root JSON value must be an object.")

        self._validate_root_fields(data)
        self._validate_notifications(data["notifications"])
        self._validate_hotkeys(data.get("hotkeys"))
        self._validate_completion_days(data["completion_days"])

    @overload
    def import_file(self, source_path: str) -> HabitData:
        ...

    @overload
    def import_file(self, source_path: Path) -> HabitData:
        ...

    def import_file(self, source_path: Path | str) -> HabitData:
        """Load and validate habit data from another file without changing current state."""
        source = Path(source_path)
        try:
            return self._read_valid_json_file(source)
        except (OSError, json.JSONDecodeError, ValidationError, ValueError) as error:
            raise ImportValidationError(f"Import failed for '{source}'.") from error

    @overload
    def export_file(self, destination_path: Path | str, habit_data: HabitData) -> None:
        ...

    @overload
    def export_file(self, habit_data: HabitData, destination_path: Path | str) -> None:
        ...

    def export_file(self, destination_path: Path | str | HabitData, habit_data: HabitData | Path | str) -> None:
        """Export the current habit data to a user-selected JSON file."""
        if isinstance(destination_path, HabitData):
            destination = Path(habit_data)
            export_data = destination_path
        else:
            destination = Path(destination_path)
            export_data = habit_data

        if not isinstance(export_data, HabitData):
            raise StorageError("Could not export habit data because the provided data is invalid.")

        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("w", encoding="utf-8") as file:
                json.dump(export_data.to_dict(), file, indent=2, ensure_ascii=False)
        except OSError as error:
            raise StorageError(f"Could not export habit data to '{destination}'.") from error

    def reset_data(self) -> HabitData:
        """Replace SQLite runtime data with a fresh default state."""
        return self._sqlite_backend.reset_data()

    def _create_default_data(self) -> HabitData:
        timestamp = self._current_timestamp()
        return HabitData(
            _habit_description="",
            _completion_days={},
            _created_at=timestamp,
            _last_opened_at=timestamp,
        )

    def _recover_from_corrupted_database(self, error: Exception) -> HabitData:
        """Back up invalid SQLite data and recover from JSON or defaults."""
        backup_path = self._backup_corrupted_database()
        try:
            if self.file_path.exists():
                habit_data = self._read_valid_json_file(self.file_path)
                habit_data.last_opened_at = self._current_timestamp()
                self._sqlite_backend.save(habit_data)
                if backup_path is None:
                    self.last_warning = "SQLite data was invalid. The app recovered from the legacy JSON file."
                else:
                    self.last_warning = (
                        f"SQLite data was invalid. The database was backed up to '{backup_path.name}' "
                        "and recovered from the legacy JSON file."
                    )
                return habit_data
        except (StorageError, ImportValidationError, ValidationError, ValueError, OSError, json.JSONDecodeError):
            pass

        habit_data = self._create_default_data()
        try:
            self._sqlite_backend.save(habit_data)
        except StorageError as save_error:
            raise StorageError("SQLite data was invalid and the safe default state could not be saved.") from save_error

        self.created_default_on_load = True
        if backup_path is None:
            self.last_warning = "SQLite data was invalid. A safe default database was created."
        else:
            self.last_warning = (
                f"SQLite data was invalid. The database was backed up to '{backup_path.name}' "
                "and a safe default database was created."
            )
        return habit_data

    def _recover_from_corrupted_json_file(self, error: Exception) -> HabitData:
        """Back up invalid legacy JSON data and continue with SQLite defaults."""
        if self.file_path.exists():
            backup_name = f"{self.file_path.stem}.corrupted{self.file_path.suffix}"
            backup_path = self.file_path.with_name(backup_name)
            try:
                shutil.copy2(self.file_path, backup_path)
            except OSError:
                backup_path = None
        else:
            backup_path = None

        habit_data = self._create_default_data()
        try:
            self._sqlite_backend.save(habit_data)
        except StorageError as save_error:
            raise StorageError("Legacy JSON data was invalid and the safe default state could not be saved.") from save_error

        self.created_default_on_load = True
        if backup_path is None:
            self.last_warning = "Legacy JSON data was invalid. A safe default database was created."
            return habit_data

        self.last_warning = (
            f"Legacy JSON data was invalid. The original file was backed up to '{backup_path.name}' "
            "and a safe default database was created."
        )
        return habit_data

    def _backup_corrupted_database(self) -> Path | None:
        if not self.database_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = self.database_path.with_name(
            f"{self.database_path.stem}.corrupted-{timestamp}{self.database_path.suffix}"
        )
        try:
            shutil.copy2(self.database_path, backup_path)
            self.database_path.unlink()
            return backup_path
        except OSError:
            return None

    def _validate_root_fields(self, data: dict) -> None:
        if "version" not in data or not isinstance(data["version"], int):
            raise ValidationError("Field 'version' must be an integer.")
        if "habit_description" not in data or not isinstance(data["habit_description"], str):
            raise ValidationError("Field 'habit_description' must be a string.")
        if "created_at" not in data or not isinstance(data["created_at"], str):
            raise ValidationError("Field 'created_at' must be an ISO datetime string.")
        if "last_opened_at" not in data or not isinstance(data["last_opened_at"], str):
            raise ValidationError("Field 'last_opened_at' must be an ISO datetime string.")
        if "notifications" not in data or not isinstance(data["notifications"], dict):
            raise ValidationError("Field 'notifications' must be an object.")
        if "completion_days" not in data or not isinstance(data["completion_days"], dict):
            raise ValidationError("Field 'completion_days' must be an object.")
        startup_enabled = data.get("startup_enabled", True)
        if not isinstance(startup_enabled, bool):
            raise ValidationError("Field 'startup_enabled' must be boolean.")

        self._validate_iso_datetime(data["created_at"], field_name="created_at")
        self._validate_iso_datetime(data["last_opened_at"], field_name="last_opened_at")

    def _validate_notifications(self, notifications: dict) -> None:
        if "enabled" not in notifications or not isinstance(notifications["enabled"], bool):
            raise ValidationError("Field 'notifications.enabled' must be boolean.")
        times = notifications.get("times")
        if times is None:
            raise ValidationError("Field 'notifications.times' must be a list.")
        if not isinstance(times, list):
            raise ValidationError("Field 'notifications.times' must be a list.")
        if len(times) > MAX_NOTIFICATION_TIMES:
            raise ValidationError(f"Field 'notifications.times' can contain at most {MAX_NOTIFICATION_TIMES} values.")

        seen_active_times: set[str] = set()
        for time_value in times:
            if not isinstance(time_value, str):
                raise ValidationError("Each value in 'notifications.times' must be a string.")
            if not TIME_PATTERN.fullmatch(time_value):
                raise ValidationError("Each value in 'notifications.times' must match HH:MM 24-hour format.")
            if time_value == DEFAULT_NOTIFICATION_PLACEHOLDER:
                continue
            if time_value in seen_active_times:
                raise ValidationError("Notification times must be unique.")
            seen_active_times.add(time_value)

        message_template = notifications.get("message_template", DEFAULT_NOTIFICATION_MESSAGE)
        if not isinstance(message_template, str) or not message_template.strip():
            raise ValidationError("Field 'notifications.message_template' must be a non-empty string.")

        try:
            NotificationSettings.sanitize_times(times)
        except ValueError as error:
            raise ValidationError(str(error)) from error

    def _validate_hotkeys(self, hotkeys: dict | None) -> None:
        if hotkeys is None:
            return
        if not isinstance(hotkeys, dict):
            raise ValidationError("Field 'hotkeys' must be an object.")

        required_fields = [
            "previous_month",
            "next_month",
            "previous_year",
            "next_year",
            "current_month",
        ]
        seen_values: list[str] = []
        for field_name in required_fields:
            value = hotkeys.get(field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValidationError(f"Field 'hotkeys.{field_name}' must be a non-empty string.")
            normalized = value.strip()
            if normalized in seen_values:
                raise ValidationError("Each hotkey must use a different key.")
            seen_values.append(normalized)

    def _validate_completion_days(self, completion_days: dict) -> None:
        for date_key, completed in completion_days.items():
            if not isinstance(date_key, str):
                raise ValidationError("Every completion day key must be an ISO date string.")
            self._validate_iso_date(date_key, field_name="completion_days key")
            if not isinstance(completed, bool):
                raise ValidationError("Every completion day value must be boolean.")

    def _validate_iso_datetime(self, value: str, field_name: str) -> None:
        try:
            datetime.fromisoformat(value)
        except ValueError as error:
            raise ValidationError(f"Field '{field_name}' must be a valid ISO datetime string.") from error

    def _validate_iso_date(self, value: str, field_name: str) -> None:
        try:
            date.fromisoformat(value)
        except ValueError as error:
            raise ValidationError(f"Field '{field_name}' must be a valid ISO date string.") from error

    def _current_timestamp(self) -> str:
        return self._date_service.now().isoformat(timespec="seconds")
