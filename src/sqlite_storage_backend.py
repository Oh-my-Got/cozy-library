"""Prepare SQLite runtime storage for Cozy Library v2.

Creates the local database schema while keeping current JSON storage unchanged.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3

from .date_service import DateService
from .exceptions import StorageError
from .models import HabitData
from .storage_backend import StorageBackend


class SQLiteStorageBackend(StorageBackend):
    """SQLite storage backend for future runtime persistence."""

    SCHEMA_VERSION = "1"

    def __init__(self, database_path: Path | str, date_service: DateService | None = None) -> None:
        self.database_path = Path(database_path)
        self._date_service = date_service or DateService()

    def exists(self) -> bool:
        """Return whether the SQLite database file exists."""
        return self.database_path.exists()

    def initialize(self) -> None:
        """Create the database file and schema when needed."""
        self._ensure_schema()

    def load(self) -> HabitData:
        """Load habit data from SQLite in a later migration batch."""
        raise NotImplementedError("SQLite load will be implemented in Batch 2.")

    def save(self, habit_data: HabitData) -> None:
        """Save habit data to SQLite in a later migration batch."""
        raise NotImplementedError("SQLite save will be implemented in Batch 2.")

    def reset_data(self) -> HabitData:
        """Reset SQLite data in a later migration batch."""
        raise NotImplementedError("SQLite reset will be implemented in Batch 2.")

    def _ensure_schema(self) -> None:
        """Create all v2 SQLite tables inside one transaction."""
        try:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.database_path) as connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS app_metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS habit (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        habit_description TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_opened_at TEXT NOT NULL,
                        startup_enabled INTEGER NOT NULL CHECK (startup_enabled IN (0, 1))
                    );

                    CREATE TABLE IF NOT EXISTS completion_days (
                        date_key TEXT PRIMARY KEY,
                        completed INTEGER NOT NULL CHECK (completed IN (0, 1))
                    );

                    CREATE TABLE IF NOT EXISTS notification_settings (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        enabled INTEGER NOT NULL CHECK (enabled IN (0, 1)),
                        message_template TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS notification_times (
                        time_value TEXT PRIMARY KEY
                    );

                    CREATE TABLE IF NOT EXISTS hotkey_settings (
                        action TEXT PRIMARY KEY,
                        keysym TEXT NOT NULL
                    );
                    """
                )
                connection.execute(
                    """
                    INSERT OR REPLACE INTO app_metadata (key, value)
                    VALUES ('schema_version', ?)
                    """,
                    (self.SCHEMA_VERSION,),
                )
        except (OSError, sqlite3.Error) as error:
            raise StorageError(f"Could not initialize SQLite database '{self.database_path}'.") from error
