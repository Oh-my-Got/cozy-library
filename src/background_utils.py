"""Render cropped background sections for Cozy Library views.

Supports the main window, header, footer, and description panel backgrounds.
"""

from __future__ import annotations

from pathlib import Path

from .path_utils import resource_path

try:
    from PIL import Image
except ImportError:  # pragma: no cover - depends on local environment
    Image = None


def render_background_view(
    image_path: Path | str,
    viewport_width: int,
    viewport_height: int,
    offset_x: int,
    offset_y: int,
):
    """Render a viewport-sized crop from a background image."""
    if Image is None:
        raise RuntimeError("Pillow is not available for background rendering.")

    resolved_path = resource_path(image_path)
    if not resolved_path.exists():
        raise FileNotFoundError(resolved_path)

    image = Image.open(resolved_path).convert("RGBA")

    if image.width < viewport_width or image.height < viewport_height:
        scale = max(viewport_width / image.width, viewport_height / image.height)
        image = image.resize((int(image.width * scale), int(image.height * scale)))

    viewport = Image.new("RGBA", (viewport_width, viewport_height))
    viewport.paste(image, (offset_x, offset_y))
    return viewport
