"""Render the bookshelf month view.

Draws the active month and processes day-cell clicks.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
import tkinter as tk
from typing import Callable

from .date_service import DateService
from .layout import LayoutManager
from .models import HabitData
from .path_utils import resource_path
from .sprites import BookSprite, ShelfBackground, WindowBackground
from .ui_constants import WINDOW_BACKGROUND_OFFSET_X, WINDOW_BACKGROUND_OFFSET_Y


class ShelfView:
    """Render a bookshelf month view and handle day-cell interaction."""

    def __init__(
        self,
        canvas: tk.Canvas,
        habit_data: HabitData,
        date_service: DateService,
        layout_manager: LayoutManager,
        on_state_changed: Callable[[], bool] | None = None,
        assets_root: Path | str | None = None,
    ) -> None:
        self.canvas = canvas
        self.habit_data = habit_data
        self.date_service = date_service
        self.layout_manager = layout_manager
        self._on_state_changed = on_state_changed

        self._assets_root = Path(assets_root) if assets_root is not None else resource_path("assets")
        self._book_image_path = self._assets_root / "books" / "book_completed.png"
        self._books_root = self._assets_root / "books"
        self._rendered_elements: list[object] = []

        self.current_year, self.current_month = self.date_service.get_current_year_month()
        self.active_layout = self.layout_manager.get_layout_for_month(
            self.date_service.get_days_in_month(self.current_year, self.current_month),
            self.current_month,
        )

    def draw(self) -> None:
        """Redraw the active month scene."""
        self.canvas.delete("all")
        self._rendered_elements = []
        self.draw_window_background()
        self.draw_background()
        self.draw_books()

    def draw_window_background(self) -> None:
        background = WindowBackground(
            x=0,
            y=0,
            width=self.active_layout.canvas_width,
            height=self.active_layout.canvas_height,
            image_offset=(
                WINDOW_BACKGROUND_OFFSET_X - self.active_layout.canvas_x,
                WINDOW_BACKGROUND_OFFSET_Y - self.active_layout.canvas_y,
            ),
            image_path=self.active_layout.window_background_path,
        )
        self._rendered_elements.append(background)
        background.draw(self.canvas)

    def draw_background(self) -> None:
        background = ShelfBackground(
            x=self.active_layout.shelf_x,
            y=self.active_layout.shelf_y,
            width=self.active_layout.shelf_width,
            height=self.active_layout.shelf_height,
            image_path=self.active_layout.shelf_image_path,
        )
        self._rendered_elements.append(background)
        background.draw(self.canvas)

    def draw_books(self) -> None:
        for day in self.active_layout.slots:
            day_date = date(self.current_year, self.current_month, day)
            if not self.habit_data.is_completed(day_date):
                continue

            book_x, book_y = self.active_layout.get_book_position(day)
            book_width, book_height = self.active_layout.get_book_size(day)
            book = BookSprite(
                x=book_x,
                y=book_y,
                width=book_width,
                height=book_height,
                image_path=self._resolve_book_image_path(day),
            )
            self._rendered_elements.append(book)
            book.draw(self.canvas)

    def handle_click(self, event: tk.Event) -> None:
        """Toggle a clicked day when it is editable and save succeeds."""
        selected_day = self._find_day_at_point(event.x, event.y)
        if selected_day is None:
            return

        selected_date = date(self.current_year, self.current_month, selected_day)
        if self.date_service.is_future_date(selected_date):
            return

        self.habit_data.toggle_day(selected_date)
        if self._on_state_changed is not None:
            saved = self._on_state_changed()
            if not saved:
                self.habit_data.toggle_day(selected_date)
                self.draw()
                return
        self.draw()

    def go_previous_month(self) -> None:
        if self.current_month == 1:
            self.refresh_month(self.current_year - 1, 12)
            return
        self.refresh_month(self.current_year, self.current_month - 1)

    def go_next_month(self) -> None:
        if self.current_month == 12:
            self.refresh_month(self.current_year + 1, 1)
            return
        self.refresh_month(self.current_year, self.current_month + 1)

    def refresh_month(self, year: int, month: int) -> None:
        self.current_year = year
        self.current_month = month
        days_count = self.date_service.get_days_in_month(year, month)
        self.active_layout = self.layout_manager.get_layout_for_month(days_count, month)
        self.draw()

    def get_selected_month_label(self) -> str:
        month_name = date(self.current_year, self.current_month, 1).strftime("%B").upper()
        return f"{month_name} {self.current_year}"

    def get_selected_month_completed(self) -> int:
        return self.habit_data.get_month_completed(self.current_year, self.current_month)

    def get_selected_month_percentage(self) -> float:
        return self.habit_data.get_month_completion_percentage(
            self.current_year,
            self.current_month,
            self.date_service.today(),
        )

    def _find_day_at_point(self, x: int, y: int) -> int | None:
        for day in reversed(list(self.active_layout.slots)):
            if self.active_layout.contains_point(day, x, y):
                return day
        return None

    def _resolve_book_image_path(self, day: int) -> Path:
        image_name = self.active_layout.get_book_image_name(day)
        if image_name:
            return self._books_root / image_name

        day_specific_path = self._books_root / f"{day}.png"
        if day_specific_path.exists():
            return day_specific_path

        return self._book_image_path
