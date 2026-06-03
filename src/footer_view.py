"""Render the main window footer.

Contains footer background handling and total/month progress text items.
"""

from __future__ import annotations

from pathlib import Path
import tkinter as tk

from .background_utils import render_background_view

try:
    from PIL import ImageTk
except ImportError:  # pragma: no cover - depends on local environment
    ImageTk = None


class FooterView:
    """Manage footer canvas background and text updates."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        ui_font_family: str,
        font_size_fn,
        text_color: str,
        background_fallback: str,
    ) -> None:
        self._ui_font_family = ui_font_family
        self._font_size = font_size_fn
        self._text_color = text_color
        self._background_fallback = background_fallback
        self.canvas = tk.Canvas(
            parent,
            bg=background_fallback,
            bd=0,
            highlightthickness=0,
        )
        self._footer_background_photo = None
        self._footer_background_rect_id: int | None = None
        self._footer_background_image_id: int | None = None
        self._footer_total_title_id: int | None = None
        self._footer_total_value_id: int | None = None
        self._footer_month_title_id: int | None = None
        self._footer_month_value_id: int | None = None
        self._width = 0
        self._height = 0

    def place(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        *,
        total_center_x: int,
        month_center_x: int,
        title_y: int,
        value_y: int,
    ) -> None:
        self._width = width
        self._height = height
        self.canvas.place(x=x, y=y, width=width, height=height)

        footer_title_font = (self._ui_font_family, self._font_size(14), "bold")
        footer_value_font = (self._ui_font_family, self._font_size(30), "bold")

        if self._footer_background_rect_id is None:
            self._footer_background_rect_id = self.canvas.create_rectangle(
                0,
                0,
                width,
                height,
                fill=self._background_fallback,
                outline="",
            )
        else:
            self.canvas.coords(self._footer_background_rect_id, 0, 0, width, height)

        if self._footer_background_image_id is None:
            self._footer_background_image_id = self.canvas.create_image(
                0,
                0,
                anchor="nw",
                image="",
            )
        else:
            self.canvas.coords(self._footer_background_image_id, 0, 0)

        if self._footer_total_title_id is None:
            self._footer_total_title_id = self.canvas.create_text(
                total_center_x,
                title_y,
                text="",
                font=footer_title_font,
                fill=self._text_color,
                anchor="n",
                justify="center",
            )
        else:
            self.canvas.coords(self._footer_total_title_id, total_center_x, title_y)

        if self._footer_total_value_id is None:
            self._footer_total_value_id = self.canvas.create_text(
                total_center_x,
                value_y,
                text="",
                font=footer_value_font,
                fill=self._text_color,
                anchor="n",
                justify="center",
            )
        else:
            self.canvas.coords(self._footer_total_value_id, total_center_x, value_y)

        if self._footer_month_title_id is None:
            self._footer_month_title_id = self.canvas.create_text(
                month_center_x,
                title_y,
                text="",
                font=footer_title_font,
                fill=self._text_color,
                anchor="n",
                justify="center",
            )
        else:
            self.canvas.coords(self._footer_month_title_id, month_center_x, title_y)

        if self._footer_month_value_id is None:
            self._footer_month_value_id = self.canvas.create_text(
                month_center_x,
                value_y,
                text="",
                font=footer_value_font,
                fill=self._text_color,
                anchor="n",
                justify="center",
            )
        else:
            self.canvas.coords(self._footer_month_value_id, month_center_x, value_y)

    def refresh_background(
        self,
        background_path: Path,
        offset_x: int,
        offset_y: int,
        fallback_color: str,
    ) -> None:
        """Render the footer background from the active month image."""
        if ImageTk is None or not background_path.exists():
            self.clear_background()
            return

        try:
            footer_background = render_background_view(
                background_path,
                self._width,
                self._height,
                offset_x,
                offset_y,
            )
            self._footer_background_photo = ImageTk.PhotoImage(footer_background)
            self.canvas.itemconfigure(self._footer_background_image_id, image=self._footer_background_photo)
            self.canvas.tag_lower(self._footer_background_image_id)
            self.canvas.tag_lower(self._footer_background_rect_id)
        except (OSError, FileNotFoundError, RuntimeError):
            self.clear_background(fallback_color)

    def clear_background(self, fallback_color: str | None = None) -> None:
        if fallback_color is None:
            fallback_color = self._background_fallback
        self._footer_background_photo = None
        self.canvas.itemconfigure(self._footer_background_image_id, image="")
        self.canvas.itemconfigure(self._footer_background_rect_id, fill=fallback_color)

    def update_texts(
        self,
        *,
        total_title: str,
        total_value: str,
        month_title: str,
        month_value: str,
    ) -> None:
        self.canvas.itemconfigure(self._footer_total_title_id, text=total_title)
        self.canvas.itemconfigure(self._footer_total_value_id, text=total_value)
        self.canvas.itemconfigure(self._footer_month_title_id, text=month_title)
        self.canvas.itemconfigure(self._footer_month_value_id, text=month_value)
