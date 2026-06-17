"""Display project information for Cozy Library.

Provides an overlay About page with application purpose and technology summary.
"""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk

from .ui_constants import HEADER_TEXT_COLOR
from .ui_rendering import render_text_image


class AboutPage:
    """Show the About page as an overlay on the main window."""

    def __init__(self, parent: tk.Tk, *, ui_font_family: str, header_font_path: Path) -> None:
        self.parent = parent
        self._ui_font_family = ui_font_family
        self._header_font_path = header_font_path
        self._heading_images = []
        self._is_open = False

        self.frame = tk.Frame(parent, bg="#efe6d5", bd=0, highlightthickness=0, takefocus=True)
        self._build_ui()

    def is_open(self) -> bool:
        return self._is_open

    def show(self) -> None:
        self.frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.frame.lift()
        self.frame.focus_set()
        self._is_open = True

    def close(self) -> None:
        self.frame.place_forget()
        self.parent.focus_set()
        self._is_open = False

    def _build_ui(self) -> None:
        container = tk.Frame(
            self.frame,
            bg="#efe6d5",
            padx=48,
            pady=44,
        )
        container.pack(fill="both", expand=True)

        self._pack_heading(container, "Cozy Library", font_size=32, width=360, height=44)

        tk.Label(
            container,
            text="A small desktop habit tracker\nwith bookshelf-style monthly progress.",
            font=(self._ui_font_family, 10),
            bg="#efe6d5",
            fg="#2b2118",
            wraplength=560,
            justify="left",
        ).pack(anchor="w", pady=(12, 0))

        self._pack_heading(container, "Purpose", font_size=18, width=240, height=28, pady=(26, 4))

        tk.Label(
            container,
            text=(
                "Cozy Library is designed for tracking one repeated habit\n"
                "without accounts, cloud sync, or a large task system.\n"
                "The goal is simple daily progress visibility."
            ),
            font=(self._ui_font_family, 10),
            bg="#efe6d5",
            fg="#2b2118",
            wraplength=620,
            justify="left",
        ).pack(anchor="w")

        technologies = (
            "- Python\n"
            "- Tkinter GUI\n"
            "- SQLite local runtime storage\n"
            "- JSON import/export\n"
            "- Pillow image rendering\n"
            "- Plyer desktop notifications\n"
            "- Pystray system tray integration\n"
            "- PyInstaller executable build"
        )
        self._pack_heading(container, "Technologies", font_size=18, width=300, height=28, pady=(24, 4))
        tk.Label(
            container,
            text=technologies,
            font=(self._ui_font_family, 10),
            bg="#efe6d5",
            fg="#2b2118",
            justify="left",
        ).pack(anchor="w")

        self._pack_heading(container, "Data storage", font_size=18, width=300, height=28, pady=(24, 4))
        tk.Label(
            container,
            text=(
                "Application data is stored locally in cozy_library.db.\n"
                "JSON files are supported for import, export,\n"
                "and migration from the previous version."
            ),
            font=(self._ui_font_family, 10),
            bg="#efe6d5",
            fg="#2b2118",
            wraplength=620,
            justify="left",
        ).pack(anchor="w")

        self._pack_heading(container, "Source code", font_size=18, width=300, height=28, pady=(24, 4))
        tk.Label(
            container,
            text=(
                "The project source code is submitted together with the report\n"
                "and is also available in the project repository.\n"
                "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧"
            ),
            font=(self._ui_font_family, 10),
            bg="#efe6d5",
            fg="#2b2118",
            wraplength=620,
            justify="left",
        ).pack(anchor="w")

        ttk.Button(container, text="Back", command=self.close).pack(anchor="e", side="bottom")

    def _pack_heading(
        self,
        parent: tk.Misc,
        text: str,
        *,
        font_size: int,
        width: int,
        height: int,
        pady: tuple[int, int] = (0, 0),
    ) -> None:
        heading_image = render_text_image(
            text,
            self._header_font_path,
            font_size,
            width,
            height,
            fill=HEADER_TEXT_COLOR,
            align="left",
        )
        if heading_image is not None:
            self._heading_images.append(heading_image)
            tk.Label(parent, image=heading_image, bg="#efe6d5", bd=0).pack(anchor="w", pady=pady)
            return

        tk.Label(
            parent,
            text=text,
            font=(self._ui_font_family, max(10, font_size // 2), "bold"),
            bg="#efe6d5",
            fg="#2b2118",
        ).pack(anchor="w", pady=pady)
