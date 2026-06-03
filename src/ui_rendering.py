"""Provide shared UI text rendering helpers.

Selects available fonts and renders title text through Tkinter and Pillow.
"""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import font as tkfont

from .ui_constants import HEADER_TEXT_COLOR, UI_FONT_FALLBACK_FAMILY, UI_FONT_FAMILY

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
except ImportError:  # pragma: no cover - depends on local environment
    Image = None
    ImageDraw = None
    ImageFont = None
    ImageTk = None


def choose_ui_font_family(widget: tk.Misc) -> str:
    """Choose the first available preferred UI font family."""
    preferred_families = [UI_FONT_FAMILY, "Cascadia Code", UI_FONT_FALLBACK_FAMILY]
    available_families = set(tkfont.families(widget))
    for family in preferred_families:
        if family in available_families:
            return family
    return UI_FONT_FALLBACK_FAMILY


def render_text_image(
    text: str,
    font_path: Path,
    font_size: int,
    width: int,
    height: int,
    *,
    fill: str = HEADER_TEXT_COLOR,
    align: str = "center",
):
    """Render text into a Tk image, returning None when rendering is unavailable."""
    if (
        not text
        or Image is None
        or ImageDraw is None
        or ImageFont is None
        or ImageTk is None
        or not font_path.exists()
    ):
        return None

    try:
        font = ImageFont.truetype(str(font_path), font_size)
        temp_image = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_image)
        left, top, right, bottom = temp_draw.textbbox((0, 0), text, font=font)
        text_width = max(1, right - left)
        text_height = max(1, bottom - top)

        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        if align == "left":
            text_x = -left
        else:
            text_x = (width - text_width) // 2 - left
        text_y = (height - text_height) // 2 - top
        draw.text((text_x, text_y), text, font=font, fill=fill)
        return ImageTk.PhotoImage(image)
    except OSError:
        return None
