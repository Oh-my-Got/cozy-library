"""Store Cozy Library data in a local SQLite database.

Implements StorageBackend and manages schema creation, loading, saving, and reset.
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3

from .date_service import DateService
from .exceptions import StorageError
from .models import DEFAULT_HOTKEYS, DEFAULT_NOTIFICATION_MESSAGE, HabitData
from .storage_backend import StorageBackend


class SQLiteStorageBackend(StorageBackend):
    """SQLite implementation of the storage backend interface."""

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
        """Load habit data from SQLite, creating default data when empty."""
        self._ensure_schema()
        try:
            with closing(sqlite3.connect(self.database_path)) as connection:
                with connection:
                    data = self._read_habit_data(connection)
        except (sqlite3.Error, ValueError) as error:
            raise StorageError(f"Could not load SQLite database '{self.database_path}'.") from error

        if data is None:
            habit_data = self._create_default_data()
            self.save(habit_data)
            return habit_data
        return data

    def save(self, habit_data: HabitData) -> None:
        """Save the complete habit state to SQLite."""
        self._ensure_schema()
        try:
            with closing(sqlite3.connect(self.database_path)) as connection:
                with connection:
                    self._write_habit_data(connection, habit_data)
        except (sqlite3.Error, ValueError) as error:
            raise StorageError(f"Could not save SQLite database '{self.database_path}'.") from error

    def reset_data(self) -> HabitData:
        """Replace SQLite data with a default habit state."""
        habit_data = self._create_default_data()
        self.save(habit_data)
        return habit_data

    def _ensure_schema(self) -> None:
        """Create all v2 SQLite tables inside one transaction."""
        try:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(self.database_path)) as connection:
                with connection:
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

    def _read_habit_data(self, connection: sqlite3.Connection) -> HabitData | None:
        habit_row = connection.execute(
            """
            SELECT habit_description, created_at, last_opened_at, startup_enabled
            FROM habit
            WHERE id = 1
            """
        ).fetchone()
        if habit_row is None:
            return None

        notification_row = connection.execute(
            """
            SELECT enabled, message_template
            FROM notification_settings
            WHERE id = 1
            """
        ).fetchone()
        notification_enabled = False
        message_template = DEFAULT_NOTIFICATION_MESSAGE
        if notification_row is not None:
            notification_enabled = bool(notification_row[0])
            message_template = notification_row[1]

        notification_times = [
            row[0]
            for row in connection.execute(
                "SELECT time_value FROM notification_times ORDER BY rowid"
            ).fetchall()
        ]
        completion_days = {
            row[0]: bool(row[1])
            for row in connection.execute(
                "SELECT date_key, completed FROM completion_days"
            ).fetchall()
        }
        hotkeys = {
            row[0]: row[1]
            for row in connection.execute(
                "SELECT action, keysym FROM hotkey_settings"
            ).fetchall()
        }
        for action, default_key in DEFAULT_HOTKEYS.items():
            hotkeys.setdefault(action, default_key)

        return HabitData.from_dict(
            {
                "version": 1,
                "habit_description": habit_row[0],
                "created_at": habit_row[1],
                "last_opened_at": habit_row[2],
                "startup_enabled": bool(habit_row[3]),
                "notifications": {
                    "enabled": notification_enabled,
                    "times": notification_times,
                    "message_template": message_template,
                },
                "hotkeys": hotkeys,
                "completion_days": completion_days,
            }
        )

    def _write_habit_data(self, connection: sqlite3.Connection, habit_data: HabitData) -> None:
        data = habit_data.to_dict()
        notifications = data["notifications"]
        hotkeys = data["hotkeys"]
        completion_days = data["completion_days"]

        connection.execute("DELETE FROM completion_days")
        connection.execute("DELETE FROM notification_times")
        connection.execute("DELETE FROM hotkey_settings")
        connection.execute("DELETE FROM notification_settings")
        connection.execute("DELETE FROM habit")

        connection.execute(
            """
            INSERT INTO habit (
                id,
                habit_description,
                created_at,
                last_opened_at,
                startup_enabled
            )
            VALUES (1, ?, ?, ?, ?)
            """,
            (
                data["habit_description"],
                data["created_at"],
                data["last_opened_at"],
                int(data["startup_enabled"]),
            ),
        )
        connection.execute(
            """
            INSERT INTO notification_settings (id, enabled, message_template)
            VALUES (1, ?, ?)
            """,
            (
                int(notifications["enabled"]),
                notifications["message_template"],
            ),
        )
        connection.executemany(
            """
            INSERT INTO notification_times (time_value)
            VALUES (?)
            """,
            [(time_value,) for time_value in notifications["times"]],
        )
        connection.executemany(
            """
            INSERT INTO hotkey_settings (action, keysym)
            VALUES (?, ?)
            """,
            sorted(hotkeys.items()),
        )
        connection.executemany(
            """
            INSERT INTO completion_days (date_key, completed)
            VALUES (?, ?)
            """,
            [
                (date_key, int(completed))
                for date_key, completed in sorted(completion_days.items())
            ],
        )

    def _create_default_data(self) -> HabitData:
        timestamp = self._date_service.now().isoformat(timespec="seconds")
        return HabitData(
            _habit_description="",
            _completion_days={},
            _created_at=timestamp,
            _last_opened_at=timestamp,
        )
