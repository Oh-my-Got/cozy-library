"""Manage the habit description panel.

Contains the display canvas, edit text box, scrollbar, and local mode switching.
"""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk

from .background_utils import render_background_view

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
except ImportError:  # pragma: no cover - depends on local environment
    Image = None
    ImageDraw = None
    ImageFont = None
    ImageTk = None


class DescriptionPanel:
    """Control description display mode and edit mode."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        ui_font_family: str,
        font_size_fn,
        sx_fn,
        sy_fn,
        edit_background_color: str,
        edit_text_color: str,
        display_text_color: str,
        display_background_fallback: str,
        on_focus_out,
    ) -> None:
        self.parent = parent
        self._ui_font_family = ui_font_family
        self._font_size = font_size_fn
        self._sx = sx_fn
        self._sy = sy_fn
        self._edit_background_color = edit_background_color
        self._edit_text_color = edit_text_color
        self._display_text_color = display_text_color
        self._display_background_fallback = display_background_fallback
        self._description_edit_mode = False
        self._description_background_photo = None
        self._description_display_photo = None
        self._width = 0
        self._height = 0

        # Display and edit widgets share one container and are swapped by mode.
        self.description_container = tk.Frame(
            parent,
            bg=display_background_fallback,
            bd=0,
            highlightthickness=0,
        )

        self.description_display = tk.Canvas(
            self.description_container,
            bg=display_background_fallback,
            bd=0,
            highlightthickness=0,
            cursor="xterm",
        )
        self.description_display.bind("<Button-1>", self._handle_display_click)

        self.description_edit_frame = tk.Frame(
            self.description_container,
            bg=edit_background_color,
            bd=0,
            highlightthickness=0,
        )
        self.description_entry = tk.Text(
            self.description_edit_frame,
            font=(self._ui_font_family, self._font_size(14)),
            bg=edit_background_color,
            fg=edit_text_color,
            insertbackground=edit_text_color,
            wrap="word",
            bd=0,
            relief="flat",
            highlightthickness=0,
            padx=self._sx(10),
            pady=self._sy(8),
        )
        self.description_scrollbar = ttk.Scrollbar(
            self.description_edit_frame,
            orient="vertical",
            command=self.description_entry.yview,
        )
        self.description_entry.configure(yscrollcommand=self.description_scrollbar.set)
        self.description_entry.bind("<FocusOut>", on_focus_out)

    def place(self, x: int, y: int, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self.description_container.place(x=x, y=y, width=width, height=height)
        self.description_entry.place(x=0, y=0, width=width - self._sx(14), height=height)
        self.description_scrollbar.place(
            x=width - self._sx(14),
            y=0,
            width=self._sx(14),
            height=height,
        )
        if self._description_edit_mode:
            self.description_edit_frame.place(x=0, y=0, width=width, height=height)
        else:
            self.description_display.place(x=0, y=0, width=width, height=height)

    def set_text(self, text: str) -> None:
        self.description_entry.delete("1.0", tk.END)
        self.description_entry.insert("1.0", text)

    def get_text(self) -> str:
        return self.description_entry.get("1.0", "end-1c").strip()

    def show_display_mode(self) -> None:
        self._description_edit_mode = False
        self.description_edit_frame.place_forget()
        self.description_display.place(x=0, y=0, width=self._width, height=self._height)
        self.parent.focus_set()

    def show_edit_mode(self) -> None:
        if self._description_edit_mode:
            return
        self._description_edit_mode = True
        self.description_display.place_forget()
        self.description_edit_frame.place(x=0, y=0, width=self._width, height=self._height)
        self.description_entry.focus_set()
        self.description_entry.mark_set("insert", "end-1c")

    def is_edit_mode(self) -> bool:
        return self._description_edit_mode

    def contains_widget(self, widget: tk.Misc | None) -> bool:
        current = widget
        while current is not None:
            if current is self.description_edit_frame:
                return True
            current = getattr(current, "master", None)
        return False

    def refresh_display(
        self,
        *,
        text: str,
        background_path: Path | str,
        offset_x: int,
        offset_y: int,
    ) -> None:
        """Render the read-only description view."""
        self.description_display.delete("all")
        self._description_background_photo = None
        self._description_display_photo = None

        # Tkinter widgets do not share transparent background, so a matching
        # cropped background section is rendered behind the description text.
        try:
            background_view = render_background_view(
                background_path,
                self._width,
                self._height,
                offset_x,
                offset_y,
            )
            if ImageTk is not None:
                self._description_background_photo = ImageTk.PhotoImage(background_view)
                self.description_display.create_image(0, 0, image=self._description_background_photo, anchor="nw")
        except (OSError, FileNotFoundError, RuntimeError):
            self.description_display.create_rectangle(
                0,
                0,
                self._width,
                self._height,
                fill=self._display_background_fallback,
                outline="",
            )

        text = text.strip()
        if not text:
            return

        image = self._render_description_text_image(text)
        if image is not None:
            self._description_display_photo = image
            self.description_display.create_image(0, 0, image=self._description_display_photo, anchor="nw")
            return

        self.description_display.create_text(
            self._width // 2,
            self._height // 2,
            text=text,
            anchor="center",
            width=max(1, self._width - self._sx(20)),
            font=(self._ui_font_family, self._font_size(12), "bold"),
            fill=self._display_text_color,
            justify="center",
        )

    def _handle_display_click(self, event: tk.Event | None = None) -> None:
        self.show_edit_mode()

    def _render_description_text_image(self, text: str):
        """Render description text with Pillow when the required font is available."""
        if (
            not text
            or Image is None
            or ImageDraw is None
            or ImageFont is None
            or ImageTk is None
        ):
            return None

        font = None
        font_candidates = [
            "C:/Windows/Fonts/CascadiaMono.ttf",
            "C:/Windows/Fonts/CascadiaCode.ttf",
            "C:/Windows/Fonts/consola.ttf",
        ]
        for font_path in font_candidates:
            try:
                font = ImageFont.truetype(font_path, self._font_size(14))
                break
            except OSError:
                continue
        if font is None:
            return None

        padding_x = self._sx(10)
        padding_y = self._sy(8)
        max_text_width = max(1, self._width - (padding_x * 2))

        draw_probe = ImageDraw.Draw(Image.new("RGBA", (1, 1), (0, 0, 0, 0)))
        wrapped_lines = self._wrap_text_for_width(text, draw_probe, font, max_text_width)
        line_height = max(1, font.size + self._sy(4))
        total_height = len(wrapped_lines) * line_height

        image = Image.new("RGBA", (self._width, self._height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        y = max(padding_y, (self._height - total_height) // 2)
        for line in wrapped_lines:
            if y + line_height > self._height:
                break
            left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
            line_width = right - left
            text_x = max(padding_x, (self._width - line_width) // 2 - left)
            draw.text((text_x, y), line, font=font, fill=self._display_text_color)
            draw.text((text_x + 1, y), line, font=font, fill=self._display_text_color)
            y += line_height

        return ImageTk.PhotoImage(image)

    def _wrap_text_for_width(self, text: str, draw, font, max_width: int) -> list[str]:
        """Wrap text to fit the rendered description image."""
        lines: list[str] = []
        for paragraph in text.splitlines() or [""]:
            words = paragraph.split()
            if not words:
                lines.append("")
                continue

            current_line = words[0]
            for word in words[1:]:
                candidate = f"{current_line} {word}"
                left, top, right, bottom = draw.textbbox((0, 0), candidate, font=font)
                if right - left <= max_width:
                    current_line = candidate
                else:
                    lines.append(current_line)
                    current_line = word
            lines.append(current_line)
        return lines
