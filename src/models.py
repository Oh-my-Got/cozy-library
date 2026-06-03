"""Define Cozy Library domain models.

Contains habit state, notification settings, hotkey settings, and JSON mapping.
"""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime
import re


TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
DEFAULT_NOTIFICATION_MESSAGE = "Today's habit: {habit}"
DEFAULT_NOTIFICATION_PLACEHOLDER = "00:00"
MAX_NOTIFICATION_TIMES = 5
DEFAULT_HOTKEYS = {
    "previous_month": "Left",
    "next_month": "Right",
    "previous_year": "Up",
    "next_year": "Down",
    "current_month": "Home",
}


def _parse_iso_date(date_str: str) -> date:
    """Parse an ISO date string."""
    return date.fromisoformat(date_str)


def _format_iso_date(date_obj: date) -> str:
    """Format a date as an ISO string."""
    return date_obj.isoformat()


@dataclass(slots=True)
class NotificationSettings:
    """Store and validate reminder preferences."""

    _enabled: bool = False
    _times: list[str] | None = None
    _message_template: str = DEFAULT_NOTIFICATION_MESSAGE

    def __post_init__(self) -> None:
        if self._times is None:
            self._times = []

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    @staticmethod
    def is_placeholder_time(time_str: str) -> bool:
        return time_str == DEFAULT_NOTIFICATION_PLACEHOLDER

    @staticmethod
    def normalize_time(time_str: str) -> str:
        if not isinstance(time_str, str):
            raise ValueError("Notification time must be a string.")
        normalized = time_str.strip().replace(".", ":")
        loose_match = re.fullmatch(r"(\d{1,2}):(\d{2})", normalized)
        if loose_match:
            hour = int(loose_match.group(1))
            minute = int(loose_match.group(2))
            normalized = f"{hour:02d}:{minute:02d}"

        if not TIME_PATTERN.fullmatch(normalized):
            raise ValueError("Notification time must match HH:MM 24-hour format.")
        return normalized

    @classmethod
    def sanitize_times(cls, times: list[str]) -> list[str]:
        if not isinstance(times, list):
            raise ValueError("Notification times must be a list.")

        sanitized: list[str] = []
        seen: set[str] = set()
        for raw_time in times:
            normalized = cls.normalize_time(raw_time)
            if cls.is_placeholder_time(normalized):
                continue
            if normalized in seen:
                raise ValueError("Notification times must be unique.")
            seen.add(normalized)
            sanitized.append(normalized)

        if len(sanitized) > MAX_NOTIFICATION_TIMES:
            raise ValueError(f"You can set up to {MAX_NOTIFICATION_TIMES} notification times.")

        return sanitized

    def set_time(self, time_str: str) -> None:
        normalized = self.normalize_time(time_str)
        if self.is_placeholder_time(normalized):
            self._times = []
            return
        self._times = [normalized]

    def set_times(self, times: list[str]) -> None:
        self._times = self.sanitize_times(times)

    def add_time(self, time_str: str) -> None:
        normalized = self.normalize_time(time_str)
        if self.is_placeholder_time(normalized):
            return
        self.set_times([*self._times, normalized])

    def remove_time(self, time_str: str) -> None:
        normalized = self.normalize_time(time_str)
        self._times = [value for value in self._times if value != normalized]

    def should_send_now(self, current_datetime: datetime) -> bool:
        """Check whether a reminder is due at the current time."""
        if not self._enabled:
            return False

        current_time = current_datetime.strftime("%H:%M")
        return current_time in self._times

    def set_message_template(self, template: str) -> None:
        if not isinstance(template, str) or not template.strip():
            raise ValueError("Notification message must be a non-empty string.")
        self._message_template = template.strip()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def times(self) -> list[str]:
        return list(self._times)

    @property
    def time(self) -> str:
        if self._times:
            return self._times[0]
        return DEFAULT_NOTIFICATION_PLACEHOLDER

    @property
    def message_template(self) -> str:
        return self._message_template

    def to_dict(self) -> dict:
        return {
            "enabled": self._enabled,
            "times": self._times,
            "message_template": self._message_template,
        }

    @classmethod
    def from_dict(cls, data: dict) -> NotificationSettings:
        if not isinstance(data, dict):
            raise ValueError("Notification settings must be a dictionary.")

        enabled = data.get("enabled", False)
        times = data.get("times")
        message_template = data.get("message_template", DEFAULT_NOTIFICATION_MESSAGE)

        if not isinstance(enabled, bool):
            raise ValueError("Notification enabled flag must be boolean.")
        if not isinstance(message_template, str):
            raise ValueError("Notification message must be a string.")
        if times is None:
            legacy_time = data.get("time", DEFAULT_NOTIFICATION_PLACEHOLDER)
            if not isinstance(legacy_time, str):
                raise ValueError("Notification time must be a string.")
            times = [] if cls.is_placeholder_time(legacy_time.strip()) else [legacy_time]

        settings = cls(
            _enabled=enabled,
            _times=times,
            _message_template=message_template,
        )
        settings.set_times(settings._times)
        settings.set_message_template(settings._message_template)

        return settings


@dataclass(slots=True)
class HotkeySettings:
    """Store and validate keyboard navigation shortcuts."""

    _previous_month: str = DEFAULT_HOTKEYS["previous_month"]
    _next_month: str = DEFAULT_HOTKEYS["next_month"]
    _previous_year: str = DEFAULT_HOTKEYS["previous_year"]
    _next_year: str = DEFAULT_HOTKEYS["next_year"]
    _current_month: str = DEFAULT_HOTKEYS["current_month"]

    @staticmethod
    def normalize_keysym(keysym: str) -> str:
        if not isinstance(keysym, str):
            raise ValueError("Hotkey must be a string.")
        normalized = keysym.strip().strip("<>").strip()
        if not normalized:
            raise ValueError("Hotkey cannot be empty.")

        alias_map = {
            "left": "Left",
            "right": "Right",
            "up": "Up",
            "down": "Down",
            "home": "Home",
            "return": "Return",
            "enter": "Return",
            "space": "space",
            "pageup": "Prior",
            "pagedown": "Next",
        }
        lowered = normalized.lower()
        if lowered in alias_map:
            return alias_map[lowered]
        if len(normalized) == 1:
            return normalized.lower()
        return normalized[0].upper() + normalized[1:]

    def update_binding(self, action: str, keysym: str) -> None:
        normalized = self.normalize_keysym(keysym)
        field_map = {
            "previous_month": "_previous_month",
            "next_month": "_next_month",
            "previous_year": "_previous_year",
            "next_year": "_next_year",
            "current_month": "_current_month",
        }
        if action not in field_map:
            raise ValueError(f"Unknown hotkey action '{action}'.")
        setattr(self, field_map[action], normalized)
        self.validate_unique()

    def validate_unique(self) -> None:
        values = [
            self._previous_month,
            self._next_month,
            self._previous_year,
            self._next_year,
            self._current_month,
        ]
        if len(set(values)) != len(values):
            raise ValueError("Each hotkey must use a different key.")

    @property
    def previous_month(self) -> str:
        return self._previous_month

    @property
    def next_month(self) -> str:
        return self._next_month

    @property
    def previous_year(self) -> str:
        return self._previous_year

    @property
    def next_year(self) -> str:
        return self._next_year

    @property
    def current_month(self) -> str:
        return self._current_month

    def to_dict(self) -> dict[str, str]:
        return {
            "previous_month": self._previous_month,
            "next_month": self._next_month,
            "previous_year": self._previous_year,
            "next_year": self._next_year,
            "current_month": self._current_month,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> HotkeySettings:
        if data is None:
            return cls()
        if not isinstance(data, dict):
            raise ValueError("Hotkey settings must be a dictionary.")

        settings = cls(
            _previous_month=cls.normalize_keysym(data.get("previous_month", DEFAULT_HOTKEYS["previous_month"])),
            _next_month=cls.normalize_keysym(data.get("next_month", DEFAULT_HOTKEYS["next_month"])),
            _previous_year=cls.normalize_keysym(data.get("previous_year", DEFAULT_HOTKEYS["previous_year"])),
            _next_year=cls.normalize_keysym(data.get("next_year", DEFAULT_HOTKEYS["next_year"])),
            _current_month=cls.normalize_keysym(data.get("current_month", DEFAULT_HOTKEYS["current_month"])),
        )
        settings.validate_unique()
        return settings


@dataclass(slots=True)
class HabitData:
    """Store the full state for one tracked habit."""

    _habit_description: str = ""
    _completion_days: dict[str, bool] | None = None
    _created_at: str | None = None
    _last_opened_at: str | None = None
    _notifications: NotificationSettings | None = None
    _hotkeys: HotkeySettings | None = None
    _startup_enabled: bool = True

    def __post_init__(self) -> None:
        now_iso = datetime.now().isoformat(timespec="seconds")
        if self._completion_days is None:
            self._completion_days = {}
        if self._created_at is None:
            self._created_at = now_iso
        if self._last_opened_at is None:
            self._last_opened_at = now_iso
        if self._notifications is None:
            self._notifications = NotificationSettings()
        if self._hotkeys is None:
            self._hotkeys = HotkeySettings()

    @property
    def description(self) -> str:
        return self._habit_description

    @description.setter
    def description(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("Habit description must be a string.")
        self._habit_description = value

    @property
    def completion_days(self) -> dict[str, bool]:
        return dict(self._completion_days)

    @property
    def created_at(self) -> str:
        return self._created_at

    @property
    def last_opened_at(self) -> str:
        return self._last_opened_at

    @last_opened_at.setter
    def last_opened_at(self, value: str) -> None:
        datetime.fromisoformat(value)
        self._last_opened_at = value

    @property
    def notifications(self) -> NotificationSettings:
        return self._notifications

    @property
    def hotkeys(self) -> HotkeySettings:
        return self._hotkeys

    @property
    def startup_enabled(self) -> bool:
        return self._startup_enabled

    @startup_enabled.setter
    def startup_enabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError("Startup enabled flag must be boolean.")
        self._startup_enabled = value

    def mark_day(self, day: date) -> None:
        self._completion_days[_format_iso_date(day)] = True

    def unmark_day(self, day: date) -> None:
        self._completion_days[_format_iso_date(day)] = False

    def toggle_day(self, day: date) -> None:
        day_key = _format_iso_date(day)
        current_value = self._completion_days.get(day_key, False)
        self._completion_days[day_key] = not current_value

    def is_completed(self, day: date) -> bool:
        return self._completion_days.get(_format_iso_date(day), False)

    def get_total_completed(self) -> int:
        return sum(1 for completed in self._completion_days.values() if completed)

    def get_month_completed(self, year: int, month: int) -> int:
        total = 0
        for date_str, completed in self._completion_days.items():
            if not completed:
                continue
            parsed_day = _parse_iso_date(date_str)
            if parsed_day.year == year and parsed_day.month == month:
                total += 1
        return total

    def get_month_completion_percentage(self, year: int, month: int, today: date) -> float:
        considered_days = self.get_month_editable_days(year, month, today)

        if considered_days == 0:
            return 0.0

        month_completed = self.get_month_completed(year, month)
        return (month_completed / considered_days) * 100.0

    def get_month_editable_days(self, year: int, month: int, today: date) -> int:
        if year > today.year or (year == today.year and month > today.month):
            return 0
        if year == today.year and month == today.month:
            return today.day
        return monthrange(year, month)[1]

    def get_year_month_counts(self, year: int) -> dict[int, int]:
        month_counts = {month: 0 for month in range(1, 13)}
        for date_str, completed in self._completion_days.items():
            if not completed:
                continue
            parsed_day = _parse_iso_date(date_str)
            if parsed_day.year == year:
                month_counts[parsed_day.month] += 1
        return month_counts

    def get_tracked_days_count(self) -> int:
        return len(self._completion_days)

    def copy(self) -> HabitData:
        """Return a new HabitData instance with the same persisted state."""
        return HabitData.from_dict(self.to_dict())

    def to_dict(self) -> dict:
        return {
            "version": 1,
            "habit_description": self._habit_description,
            "created_at": self._created_at,
            "last_opened_at": self._last_opened_at,
            "notifications": self._notifications.to_dict(),
            "hotkeys": self._hotkeys.to_dict(),
            "startup_enabled": self._startup_enabled,
            "completion_days": dict(self._completion_days),
        }

    @classmethod
    def from_dict(cls, data: dict) -> HabitData:
        if not isinstance(data, dict):
            raise ValueError("Habit data must be a dictionary.")

        description = data.get("habit_description", "")
        created_at = data.get("created_at", datetime.now().isoformat(timespec="seconds"))
        last_opened_at = data.get("last_opened_at", created_at)
        completion_days = data.get("completion_days", {})
        notifications_data = data.get("notifications", {})
        hotkeys_data = data.get("hotkeys")
        startup_enabled = data.get("startup_enabled", True)

        if not isinstance(description, str):
            raise ValueError("Habit description must be a string.")
        if not isinstance(created_at, str) or not isinstance(last_opened_at, str):
            raise ValueError("Created and last opened timestamps must be ISO strings.")
        if not isinstance(completion_days, dict):
            raise ValueError("Completion days must be a dictionary.")
        if not isinstance(startup_enabled, bool):
            raise ValueError("Startup enabled flag must be boolean.")

        datetime.fromisoformat(created_at)
        datetime.fromisoformat(last_opened_at)

        validated_completion_days: dict[str, bool] = {}
        for date_str, completed in completion_days.items():
            if not isinstance(date_str, str):
                raise ValueError("Completion day keys must be ISO date strings.")
            _parse_iso_date(date_str)
            if not isinstance(completed, bool):
                raise ValueError("Completion day values must be boolean.")
            validated_completion_days[date_str] = completed

        habit = cls(
            _habit_description=description,
            _completion_days=validated_completion_days,
            _created_at=created_at,
            _last_opened_at=last_opened_at,
            _notifications=NotificationSettings.from_dict(notifications_data),
            _hotkeys=HotkeySettings.from_dict(hotkeys_data),
            _startup_enabled=startup_enabled,
        )
        return habit
