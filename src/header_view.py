"""Render the main window header.

Contains header background handling and month/date text drawing.
"""

from __future__ import annotations

from pathlib import Path
import tkinter as tk

from .background_utils import render_background_view
from .ui_constants import HEADER_TEXT_COLOR
from .ui_rendering import render_text_image

try:
    from PIL import ImageTk
except ImportError:  # pragma: no cover - depends on local environment
    ImageTk = None


class HeaderView:
    """Manage header canvas background and text updates."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        ui_font_family: str,
        font_size_fn,
        header_font_path: Path,
        canvas_background_fallback: str,
    ) -> None:
        self._ui_font_family = ui_font_family
        self._font_size = font_size_fn
        self._header_font_path = header_font_path
        self.canvas = tk.Canvas(
            parent,
            bg=canvas_background_fallback,
            bd=0,
            highlightthickness=0,
        )
        self._header_background_photo = None
        self._month_header_photo = None
        self._date_header_photo = None
        self._month_header_image_id: int | None = None
        self._date_header_image_id: int | None = None
        self._width = 0
        self._height = 0

    def place(self, x: int, y: int, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self.canvas.place(x=x, y=y, width=width, height=height)

    def refresh_background(
        self,
        background_path: Path,
        offset_x: int,
        offset_y: int,
        fallback_color: str,
    ) -> None:
        """Render the header background from the active month image."""
        if ImageTk is None:
            return

        self.canvas.delete("all")
        try:
            header_background = render_background_view(
                background_path,
                self._width,
                self._height,
                offset_x,
                offset_y,
            )
            self._header_background_photo = ImageTk.PhotoImage(header_background)
            self.canvas.create_image(0, 0, image=self._header_background_photo, anchor="nw")
        except (OSError, FileNotFoundError, RuntimeError):
            self._header_background_photo = None
            self.canvas.create_rectangle(
                0,
                0,
                self._width,
                self._height,
                fill=fallback_color,
                outline="",
            )
        self._month_header_image_id = None
        self._date_header_image_id = None

    def update_texts(
        self,
        *,
        month_text: str,
        date_text: str,
        month_center_y: int,
        date_center_y: int,
        label_width: int,
        label_height: int,
        month_font_size: int,
        date_font_size: int,
    ) -> None:
        """Update month and date labels with image or canvas text fallback."""
        month_photo = render_text_image(
            month_text,
            self._header_font_path,
            month_font_size,
            label_width,
            label_height,
            fill=HEADER_TEXT_COLOR,
            align="center",
        )
        date_photo = render_text_image(
            date_text,
            self._header_font_path,
            date_font_size,
            label_width,
            label_height,
            fill=HEADER_TEXT_COLOR,
            align="center",
        )

        if month_photo is not None:
            self._month_header_photo = month_photo
            if self._month_header_image_id is None:
                self._month_header_image_id = self.canvas.create_image(
                    label_width // 2,
                    month_center_y,
                    image=self._month_header_photo,
                )
            else:
                self.canvas.itemconfigure(self._month_header_image_id, image=self._month_header_photo)
        else:
            self._month_header_photo = None
            self._draw_text_fallback(
                "_month_header_image_id",
                month_text,
                (self._ui_font_family, self._font_size(15), "bold"),
                month_center_y,
                label_width,
            )

        if date_photo is not None:
            self._date_header_photo = date_photo
            if self._date_header_image_id is None:
                self._date_header_image_id = self.canvas.create_image(
                    label_width // 2,
                    date_center_y,
                    image=self._date_header_photo,
                )
            else:
                self.canvas.itemconfigure(self._date_header_image_id, image=self._date_header_photo)
        else:
            self._date_header_photo = None
            self._draw_text_fallback(
                "_date_header_image_id",
                date_text,
                (self._ui_font_family, self._font_size(11)),
                date_center_y,
                label_width,
            )

    def _draw_text_fallback(
        self,
        item_id_attr: str,
        text: str,
        font: tuple[str, int] | tuple[str, int, str],
        center_y: int,
        label_width: int,
    ) -> None:
        current_id = getattr(self, item_id_attr)
        if current_id is None:
            current_id = self.canvas.create_text(
                label_width // 2,
                center_y,
                text=text,
                font=font,
                fill=HEADER_TEXT_COLOR,
            )
            setattr(self, item_id_attr, current_id)
        else:
            self.canvas.itemconfigure(current_id, image="", text=text, font=font, fill=HEADER_TEXT_COLOR)
