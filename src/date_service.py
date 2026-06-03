"""Provide date and time helpers for Cozy Library.

Supports month navigation, progress calculations, and notification checks.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime


class DateService:
    """Provide current date/time values and date formatting helpers."""

    def today(self) -> date:
        return date.today()

    def now(self) -> datetime:
        return datetime.now()

    def is_future_date(self, date_obj: date) -> bool:
        return date_obj > self.today()

    def get_days_in_month(self, year: int, month: int) -> int:
        return monthrange(year, month)[1]

    def get_current_year_month(self) -> tuple[int, int]:
        today = self.today()
        return today.year, today.month

    def parse_iso_date(self, date_str: str) -> date:
        return date.fromisoformat(date_str)

    def format_iso_date(self, date_obj: date) -> str:
        return date_obj.isoformat()
