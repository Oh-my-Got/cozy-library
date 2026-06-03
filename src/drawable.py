"""Define drawable canvas elements for Cozy Library.

Provides the abstract draw contract and shared image-loading base class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import tkinter as tk

from .exceptions import AssetLoadError
from .path_utils import resource_path

try:
    from PIL import Image, ImageTk
except ImportError:  # pragma: no cover - depends on local environment
    Image = None
    ImageTk = None


class Drawable(ABC):
    """Abstract drawing contract for canvas elements."""

    @abstractmethod
    def draw(self, canvas: tk.Canvas) -> None:
        """Render the object on the provided canvas."""


class VisualElement(Drawable):
    """Base class for drawable objects with optional image assets."""

    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        image_path: Path | str | None = None,
    ) -> None:
        self._x = x
        self._y = y
        self._image_path = Path(image_path) if image_path is not None else None
        self._photo_image = None

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    @property
    def image_path(self) -> Path | None:
        return self._image_path

    @property
    def photo_image(self):
        return self._photo_image

    def load_image(self) -> None:
        """Load the element's image asset if Pillow and the file are available."""
        if self._image_path is None:
            raise AssetLoadError("No image path was provided.")
        if Image is None or ImageTk is None:
            raise AssetLoadError("Pillow is not available for image loading.")
        resolved_path = resource_path(self._image_path)
        if not resolved_path.exists():
            raise AssetLoadError(f"Asset file was not found: {resolved_path}")

        try:
            image = Image.open(resolved_path)
            self._photo_image = ImageTk.PhotoImage(image)
        except OSError as error:
            raise AssetLoadError(f"Could not load asset: {resolved_path}") from error
