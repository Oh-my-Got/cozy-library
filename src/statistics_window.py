"""Render the detailed statistics window.

Displays monthly progress, summary values, and yearly progress charts.
"""

from __future__ import annotations

from calendar import month_abbr
from pathlib import Path
import tkinter as tk
from tkinter import font as tkfont

from .date_service import DateService
from .models import HabitData
from .path_utils import resource_path
from .ui_rendering import choose_ui_font_family, render_text_image
from .ui_constants import (
    HEADER_TEXT_COLOR,
    STATS_AXIS_COLOR,
    STATS_BAR_CANVAS_HEIGHT,
    STATS_BAR_CANVAS_WIDTH,
    STATS_BAR_CANVAS_X,
    STATS_BAR_CANVAS_Y,
    STATS_COMPLETED_COLOR,
    STATS_HEADER_CANVAS_HEIGHT,
    STATS_HEADER_CANVAS_WIDTH,
    STATS_HEADER_CANVAS_X,
    STATS_HEADER_CANVAS_Y,
    STATS_HEADER_FONT_SIZE,
    STATS_HEADER_TEXT,
    STATS_PIE_CANVAS_SIZE,
    STATS_PIE_CANVAS_X,
    STATS_PIE_CANVAS_Y,
    STATS_PANEL_BACKGROUND,
    STATS_PANEL_BORDER,
    STATS_REMAINING_COLOR,
    STATS_SECTION_TITLE_FONT_SIZE,
    STATS_SUBTLE_TEXT_COLOR,
    STATS_TEXT_COLOR,
    STATS_TEXT_LINE_GAP,
    STATS_TEXT_WIDTH,
    STATS_TEXT_X,
    STATS_TEXT_Y,
    STATS_WINDOW_BACKGROUND,
    STATS_WINDOW_HEIGHT,
    STATS_WINDOW_MIN_HEIGHT,
    STATS_WINDOW_MIN_WIDTH,
    STATS_WINDOW_WIDTH,
    UI_FONT_FAMILY,
    fit_window_to_screen,
)


class StatisticsWindow:
    """Show detailed habit statistics in a separate window."""

    def __init__(
        self,
        parent: tk.Tk,
        habit_data: HabitData,
        date_service: DateService,
        window_background_path: Path | str,
        assets_root: Path | str | None = None,
    ) -> None:
        self.parent = parent
        self.habit_data = habit_data
        self.date_service = date_service
        self.window_background_path = Path(window_background_path)
        self._assets_root = Path(assets_root) if assets_root is not None else resource_path("assets")
        self._header_font_path = self._assets_root / "poxast.regular.ttf"
        self._ui_font_family = UI_FONT_FAMILY
        self.window_width, self.window_height = fit_window_to_screen(
            parent.winfo_screenwidth(),
            parent.winfo_screenheight(),
            aspect_width=STATS_WINDOW_WIDTH,
            aspect_height=STATS_WINDOW_HEIGHT,
            min_width=600,
            min_height=690,
        )
        self._scale_x = self.window_width / STATS_WINDOW_WIDTH
        self._scale_y = self.window_height / STATS_WINDOW_HEIGHT

        self.window = tk.Toplevel(parent)
        self.window.title("Detailed Statistics")
        self.window.geometry(f"{self.window_width}x{self.window_height}")
        self.window.minsize(self.window_width, self.window_height)
        self.window.resizable(False, False)
        self.window.configure(bg=STATS_WINDOW_BACKGROUND)
        self.window.transient(parent)
        self.window.focus_set()
        self._configure_ui_font_family()
        self._recalculate_geometry()

        self._header_photo = None
        self._pie_title_photo = None
        self._summary_title_photo = None
        self._bar_title_photo = None

        self.header_canvas = tk.Canvas(
            self.window,
            width=self.header_canvas_width,
            height=self.header_canvas_height,
            bg=STATS_WINDOW_BACKGROUND,
            bd=0,
            highlightthickness=0,
        )
        self.header_canvas.place(
            x=self.header_canvas_x,
            y=self.header_canvas_y,
            width=self.header_canvas_width,
            height=self.header_canvas_height,
        )

        self.pie_canvas = tk.Canvas(
            self.window,
            width=self.pie_canvas_size,
            height=self.pie_canvas_size,
            bg=STATS_PANEL_BACKGROUND,
            bd=0,
            highlightthickness=0,
        )
        self.pie_canvas.place(x=self.pie_canvas_x, y=self.pie_canvas_y)

        self.summary_canvas = tk.Canvas(
            self.window,
            width=self.summary_width,
            height=self.pie_canvas_size,
            bg=STATS_PANEL_BACKGROUND,
            bd=0,
            highlightthickness=0,
        )
        self.summary_canvas.place(x=self.summary_x, y=self.summary_y)

        self.bar_canvas = tk.Canvas(
            self.window,
            width=self.bar_canvas_width,
            height=self.bar_canvas_height,
            bg=STATS_PANEL_BACKGROUND,
            bd=0,
            highlightthickness=0,
        )
        self.bar_canvas.place(x=self.bar_canvas_x, y=self.bar_canvas_y)

        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.refresh()

    def close(self) -> None:
        self.window.destroy()

    def is_open(self) -> bool:
        return bool(self.window.winfo_exists())

    def lift(self) -> None:
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()

    def refresh(
        self,
        habit_data: HabitData | None = None,
        window_background_path: Path | str | None = None,
    ) -> None:
        """Refresh all statistics panels from current habit data."""
        if habit_data is not None:
            self.habit_data = habit_data
        if window_background_path is not None:
            self.window_background_path = Path(window_background_path)

        self._refresh_header()
        self._draw_pie_chart()
        self._draw_summary_text()
        self._draw_year_bar_chart()

    def _recalculate_geometry(self) -> None:
        self.header_canvas_x = self._sx(STATS_HEADER_CANVAS_X)
        self.header_canvas_y = self._sy(STATS_HEADER_CANVAS_Y)
        self.header_canvas_width = self._sx(STATS_HEADER_CANVAS_WIDTH)
        self.header_canvas_height = self._sy(STATS_HEADER_CANVAS_HEIGHT)
        self.pie_canvas_x = self._sx(STATS_PIE_CANVAS_X)
        self.pie_canvas_y = self._sy(STATS_PIE_CANVAS_Y)
        self.pie_canvas_size = self._sx(STATS_PIE_CANVAS_SIZE)
        self.summary_x = self._sx(STATS_TEXT_X)
        self.summary_y = self._sy(STATS_TEXT_Y)
        self.summary_width = self._sx(STATS_TEXT_WIDTH)
        self.bar_canvas_x = self._sx(STATS_BAR_CANVAS_X)
        self.bar_canvas_y = self._sy(STATS_BAR_CANVAS_Y)
        self.bar_canvas_width = self._sx(STATS_BAR_CANVAS_WIDTH)
        self.bar_canvas_height = self._sy(STATS_BAR_CANVAS_HEIGHT)
        self.text_line_gap = self._sy(STATS_TEXT_LINE_GAP)

    def _sx(self, value: int) -> int:
        return max(1, round(value * self._scale_x))

    def _sy(self, value: int) -> int:
        return max(1, round(value * self._scale_y))

    def _font_size(self, value: int) -> int:
        return max(8, round(value * min(self._scale_x, self._scale_y)))

    def _configure_ui_font_family(self) -> None:
        self._ui_font_family = choose_ui_font_family(self.window)

    def _refresh_header(self) -> None:
        self.header_canvas.delete("all")
        self.header_canvas.create_rectangle(
            0,
            0,
            self.header_canvas_width,
            self.header_canvas_height,
            fill=STATS_WINDOW_BACKGROUND,
            outline="",
        )

        self._draw_title_with_fallback(
            self.header_canvas,
            photo_attr="_header_photo",
            text=STATS_HEADER_TEXT,
            font_size=STATS_HEADER_FONT_SIZE,
            image_width=self.header_canvas_width,
            image_height=self.header_canvas_height,
            image_x=self.header_canvas_width // 2,
            image_y=self.header_canvas_height // 2,
            fallback_text=STATS_HEADER_TEXT,
            fallback_x=self.header_canvas_width // 2,
            fallback_y=self.header_canvas_height // 2,
            fallback_font=(self._ui_font_family, self._font_size(16), "bold"),
            fallback_fill=HEADER_TEXT_COLOR,
        )

    def _draw_pie_chart(self) -> None:
        """Draw current-month progress as a pie chart."""
        self.pie_canvas.delete("all")

        today = self.date_service.today()
        completed_days = self.habit_data.get_month_completed(today.year, today.month)
        editable_days = self.habit_data.get_month_editable_days(today.year, today.month, today)

        self._draw_panel_background(self.pie_canvas, self.pie_canvas_size, self.pie_canvas_size)

        pie_title_text = today.strftime("%B").upper()
        self._draw_title_with_fallback(
            self.pie_canvas,
            photo_attr="_pie_title_photo",
            text=pie_title_text,
            font_size=STATS_SECTION_TITLE_FONT_SIZE,
            image_width=self.pie_canvas_size - self._sx(40),
            image_height=self._sy(34),
            image_x=self.pie_canvas_size // 2,
            image_y=self._sy(24),
            fallback_text=today.strftime("%B"),
            fallback_x=self.pie_canvas_size // 2,
            fallback_y=self._sy(24),
            fallback_font=(self._ui_font_family, self._font_size(14), "bold"),
            fallback_fill=STATS_TEXT_COLOR,
        )

        if editable_days <= 0:
            self.pie_canvas.create_text(
                self.pie_canvas_size // 2,
                self.pie_canvas_size // 2,
                text="No editable days yet",
                font=(self._ui_font_family, self._font_size(12)),
                fill=STATS_SUBTLE_TEXT_COLOR,
            )
            return

        padding = self._sx(46)
        x1 = padding
        y1 = self._sy(52)
        x2 = self.pie_canvas_size - padding
        y2 = self.pie_canvas_size - padding
        completed_extent = (completed_days / editable_days) * 360.0

        if completed_days <= 0:
            self.pie_canvas.create_oval(
                x1,
                y1,
                x2,
                y2,
                fill=STATS_REMAINING_COLOR,
                outline="",
            )
        elif completed_days >= editable_days:
            self.pie_canvas.create_oval(
                x1,
                y1,
                x2,
                y2,
                fill=STATS_COMPLETED_COLOR,
                outline="",
            )
        else:
            self.pie_canvas.create_arc(
                x1,
                y1,
                x2,
                y2,
                start=90,
                extent=-completed_extent,
                fill=STATS_COMPLETED_COLOR,
                outline="",
            )
            self.pie_canvas.create_arc(
                x1,
                y1,
                x2,
                y2,
                start=90 - completed_extent,
                extent=-(360.0 - completed_extent),
                fill=STATS_REMAINING_COLOR,
                outline="",
            )
        center_x = self.pie_canvas_size // 2
        center_y = (y1 + y2) // 2
        percentage = (completed_days / editable_days) * 100.0
        self.pie_canvas.create_text(
            center_x,
            center_y - self._sy(8),
            text=f"{percentage:.0f}%",
            font=(self._ui_font_family, self._font_size(20), "bold"),
            fill=STATS_TEXT_COLOR,
        )
        self.pie_canvas.create_text(
            center_x,
            center_y + self._sy(16),
            text=f"{completed_days}/{editable_days} days",
            font=(self._ui_font_family, self._font_size(11)),
            fill=STATS_SUBTLE_TEXT_COLOR,
        )

        legend_y = self.pie_canvas_size - self._sy(32)
        self.pie_canvas.create_rectangle(self._sx(64), legend_y - self._sy(8), self._sx(78), legend_y + self._sy(6), fill=STATS_COMPLETED_COLOR, outline="")
        self.pie_canvas.create_text(self._sx(86), legend_y, text="Completed", anchor="w", font=(self._ui_font_family, self._font_size(10)), fill=STATS_TEXT_COLOR)
        self.pie_canvas.create_rectangle(self._sx(172), legend_y - self._sy(8), self._sx(186), legend_y + self._sy(6), fill=STATS_REMAINING_COLOR, outline="")
        self.pie_canvas.create_text(self._sx(194), legend_y, text="Remaining", anchor="w", font=(self._ui_font_family, self._font_size(10)), fill=STATS_TEXT_COLOR)

    def _draw_summary_text(self) -> None:
        """Draw text summary for current and total progress."""
        self.summary_canvas.delete("all")
        self._draw_panel_background(self.summary_canvas, self.summary_width, self.pie_canvas_size)

        today = self.date_service.today()
        current_month_completed = self.habit_data.get_month_completed(today.year, today.month)
        current_month_editable = self.habit_data.get_month_editable_days(today.year, today.month, today)
        current_month_percentage = self.habit_data.get_month_completion_percentage(today.year, today.month, today)
        total_completed = self.habit_data.get_total_completed()
        tracked_days = self.habit_data.get_tracked_days_count()

        summary_lines = [
            ("Current month:", f"{today.strftime('%B %Y')}"),
            ("Completed this month:", f"{current_month_completed}"),
            ("Remaining this month:", f"{max(0, current_month_editable - current_month_completed)}"),
            ("Month progress:", f"{current_month_percentage:.1f}%"),
            ("Total completed:", f"{total_completed}"),
            ("Tracked day records:", f"{tracked_days}"),
            ("Created at:", self.habit_data.created_at.replace("T", " ")),
            ("Last opened:", self.habit_data.last_opened_at.replace("T", " ")),
        ]

        self._draw_title_with_fallback(
            self.summary_canvas,
            photo_attr="_summary_title_photo",
            text="SUMMARY",
            font_size=STATS_SECTION_TITLE_FONT_SIZE,
            image_width=self.summary_width - self._sx(40),
            image_height=self._sy(34),
            image_x=self.summary_width // 2,
            image_y=self._sy(24),
            fallback_text="Summary",
            fallback_x=self.summary_width // 2,
            fallback_y=self._sy(24),
            fallback_font=(self._ui_font_family, self._font_size(16), "bold"),
            fallback_fill=STATS_TEXT_COLOR,
        )

        start_y = self._sy(56)
        label_font = tkfont.Font(family=self._ui_font_family, size=self._font_size(11), weight="bold")
        value_font = tkfont.Font(family=self._ui_font_family, size=self._font_size(12))
        for index, (label_text, value_text) in enumerate(summary_lines):
            y = start_y + index * self.text_line_gap
            self.summary_canvas.create_text(
                self._sx(18),
                y,
                text=label_text,
                anchor="nw",
                font=label_font,
                fill=STATS_TEXT_COLOR,
            )
            label_width = label_font.measure(label_text)
            self.summary_canvas.create_text(
                self._sx(18) + label_width + self._sx(6),
                y,
                text=value_text,
                anchor="nw",
                font=value_font,
                fill=STATS_TEXT_COLOR,
            )

    def _draw_year_bar_chart(self) -> None:
        """Draw completed-day counts for each month of the current year."""
        self.bar_canvas.delete("all")
        self._draw_panel_background(self.bar_canvas, self.bar_canvas_width, self.bar_canvas_height)

        today = self.date_service.today()
        year = today.year
        month_counts = self.habit_data.get_year_month_counts(year)
        max_height_value = max(month_counts.values(), default=0)
        top_value = max(max_height_value, 1)

        self._draw_title_with_fallback(
            self.bar_canvas,
            photo_attr="_bar_title_photo",
            text="THIS YEAR PROGRESS",
            font_size=STATS_SECTION_TITLE_FONT_SIZE,
            image_width=self.bar_canvas_width - self._sx(40),
            image_height=self._sy(34),
            image_x=self.bar_canvas_width // 2,
            image_y=self._sy(24),
            fallback_text="This Year Progress",
            fallback_x=self.bar_canvas_width // 2,
            fallback_y=self._sy(24),
            fallback_font=(self._ui_font_family, self._font_size(16), "bold"),
            fallback_fill=STATS_TEXT_COLOR,
        )

        left_margin = self._sx(56)
        right_margin = self._sx(18)
        top_margin = self._sy(56)
        bottom_margin = self._sy(52)
        chart_height = self.bar_canvas_height - top_margin - bottom_margin
        chart_width = self.bar_canvas_width - left_margin - right_margin
        base_y = self.bar_canvas_height - bottom_margin

        self.bar_canvas.create_line(left_margin, top_margin, left_margin, base_y, fill=STATS_AXIS_COLOR, width=2)
        self.bar_canvas.create_line(left_margin, base_y, self.bar_canvas_width - right_margin, base_y, fill=STATS_AXIS_COLOR, width=2)

        for step in range(5):
            ratio = step / 4
            y = base_y - (chart_height * ratio)
            value = int(round(top_value * ratio))
            self.bar_canvas.create_line(left_margin - self._sx(6), y, left_margin, y, fill=STATS_AXIS_COLOR)
            self.bar_canvas.create_text(left_margin - self._sx(12), y, text=str(value), anchor="e", font=(self._ui_font_family, self._font_size(9)), fill=STATS_SUBTLE_TEXT_COLOR)

        column_width = chart_width / 12
        bar_width = max(self._sx(18), column_width * 0.55)
        for month_index in range(1, 13):
            value = month_counts[month_index]
            ratio = value / top_value if top_value else 0.0
            bar_height = chart_height * ratio
            center_x = left_margin + ((month_index - 0.5) * column_width)
            x1 = center_x - (bar_width / 2)
            x2 = center_x + (bar_width / 2)
            y1 = base_y - bar_height
            self.bar_canvas.create_rectangle(x1, y1, x2, base_y, fill=STATS_COMPLETED_COLOR, outline="")
            self.bar_canvas.create_text(center_x, base_y + self._sy(16), text=month_abbr[month_index].upper(), font=(self._ui_font_family, self._font_size(9)), fill=STATS_TEXT_COLOR)
            self.bar_canvas.create_text(center_x, y1 - self._sy(10), text=str(value), font=(self._ui_font_family, self._font_size(9)), fill=STATS_SUBTLE_TEXT_COLOR)

    def _draw_panel_background(self, canvas: tk.Canvas, width: int, height: int) -> None:
        canvas.create_rectangle(
            0,
            0,
            width,
            height,
            fill=STATS_PANEL_BACKGROUND,
            outline=STATS_PANEL_BORDER,
            width=2,
        )

    def _draw_title_with_fallback(
        self,
        canvas: tk.Canvas,
        *,
        photo_attr: str,
        text: str,
        font_size: int,
        image_width: int,
        image_height: int,
        image_x: int,
        image_y: int,
        fallback_text: str,
        fallback_x: int,
        fallback_y: int,
        fallback_font: tuple,
        fallback_fill: str,
    ) -> None:
        title_photo = self._render_text_image(text, font_size, image_width, image_height)
        if title_photo is not None:
            setattr(self, photo_attr, title_photo)
            canvas.create_image(image_x, image_y, image=getattr(self, photo_attr))
        else:
            setattr(self, photo_attr, None)
            canvas.create_text(
                fallback_x,
                fallback_y,
                text=fallback_text,
                font=fallback_font,
                fill=fallback_fill,
            )

    def _render_text_image(self, text: str, font_size: int, width: int, height: int):
        return render_text_image(
            text,
            self._header_font_path,
            font_size,
            width,
            height,
            fill=HEADER_TEXT_COLOR,
            align="center",
        )
