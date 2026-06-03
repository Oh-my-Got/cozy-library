"""Draw concrete bookshelf canvas elements.

Contains background, book, and day-number drawable classes.
"""

from __future__ import annotations

from pathlib import Path
import tkinter as tk

from .background_utils import render_background_view
from .drawable import VisualElement
from .exceptions import AssetLoadError
from .path_utils import resource_path

try:
    from PIL import Image, ImageTk
except ImportError:  # pragma: no cover - depends on local environment
    Image = None
    ImageTk = None


class ShelfBackground(VisualElement):
    """Draw the bookshelf image or a fallback shelf panel."""

    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        width: int = 490,
        height: int = 650,
        image_path: Path | str | None = None,
    ) -> None:
        super().__init__(x=x, y=y, image_path=image_path)
        self._width = width
        self._height = height

    def draw(self, canvas: tk.Canvas) -> None:
        try:
            if self.photo_image is None:
                self.load_image()
            canvas.create_image(self.x, self.y, image=self.photo_image, anchor="nw")
        except AssetLoadError:
            x2 = self.x + self._width
            y2 = self.y + self._height
            canvas.create_rectangle(
                self.x,
                self.y,
                x2,
                y2,
                fill="#e5d3b3",
                outline="#8a6844",
                width=2,
            )
            self._draw_shelf_lines(canvas)

    def _draw_shelf_lines(self, canvas: tk.Canvas) -> None:
        shelf_count = 5
        gap = self._height // shelf_count
        for index in range(1, shelf_count):
            y = self.y + index * gap
            canvas.create_line(
                self.x + 12,
                y,
                self.x + self._width - 12,
                y,
                fill="#8a6844",
                width=3,
            )


class WindowBackground(VisualElement):
    """Draw the month background or a fallback fill."""

    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        width: int = 780,
        height: int = 1080,
        image_offset: tuple[int, int] = (0, 0),
        image_path: Path | str | None = None,
    ) -> None:
        super().__init__(x=x, y=y, image_path=image_path)
        self._width = width
        self._height = height
        self._image_offset = image_offset

    def draw(self, canvas: tk.Canvas) -> None:
        try:
            if self.photo_image is None:
                self._load_viewport_image()
            canvas.create_image(self.x, self.y, image=self.photo_image, anchor="nw")
        except AssetLoadError:
            canvas.create_rectangle(
                self.x,
                self.y,
                self.x + self._width,
                self.y + self._height,
                fill="#efe6d5",
                outline="",
            )

    def _load_viewport_image(self) -> None:
        if self.image_path is None:
            raise AssetLoadError("No image path was provided.")
        if Image is None or ImageTk is None:
            raise AssetLoadError("Pillow is not available for image loading.")

        try:
            offset_x, offset_y = self._image_offset
            image = render_background_view(
                self.image_path,
                self._width,
                self._height,
                offset_x,
                offset_y,
            )
            self._photo_image = ImageTk.PhotoImage(image)
        except (OSError, FileNotFoundError, RuntimeError) as error:
            raise AssetLoadError(f"Could not load asset: {self.image_path}") from error


class BookSprite(VisualElement):
    """Draw a completed-day book image or fallback rectangle."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int = 34,
        height: int = 56,
        image_path: Path | str | None = None,
    ) -> None:
        super().__init__(x=x, y=y, image_path=image_path)
        self._width = width
        self._height = height

    def draw(self, canvas: tk.Canvas) -> None:
        try:
            if self.photo_image is None:
                self.load_image()
            canvas.create_image(self.x, self.y, image=self.photo_image, anchor="nw")
        except AssetLoadError:
            x2 = self.x + self._width
            y2 = self.y + self._height
            canvas.create_rectangle(
                self.x,
                self.y,
                x2,
                y2,
                fill="#5e81ac",
                outline="#2e3440",
                width=2,
            )
            canvas.create_line(
                self.x + 8,
                self.y + 4,
                self.x + 8,
                y2 - 4,
                fill="#d8dee9",
                width=2,
            )


class DayNumberOverlay(VisualElement):
    """Draw a day number overlay on the shelf cell."""

    def __init__(
        self,
        x: int,
        y: int,
        day_number: int,
        is_future: bool = False,
    ) -> None:
        super().__init__(x=x, y=y)
        self._day_number = day_number
        self._is_future = is_future

    def draw(self, canvas: tk.Canvas) -> None:
        fill_color = "#b0b0b0" if not self._is_future else "#d0d0d0"
        canvas.create_text(
            self.x,
            self.y,
            text=str(self._day_number),
            fill=fill_color,
            font=("Arial", 12),
            anchor="nw",
        )
