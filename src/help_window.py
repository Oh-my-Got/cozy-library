"""Display a short user guide for Cozy Library.

Provides a Help page overlay for the main workflow and settings.
"""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk

from .ui_constants import HEADER_TEXT_COLOR
from .ui_rendering import render_text_image


class HelpPage:
    """Show the Help page as an overlay on the main window."""

    HELP_SECTIONS = [
        (
            "Tracking progress",
            "Use Mark Today or Unmark Today to change today's completion state.\n"
            "You can also click a visible past or current day on the shelf.\n"
            "Future days cannot be marked.",
        ),
        (
            "Editing habit text",
            "Type your habit in the description area, then click outside the editor to save it.",
        ),
        (
            "Statistics",
            "Open Statistics to see monthly progress based on passed days,\n"
            "total completed days, and yearly progress.",
        ),
        (
            "Reminders",
            "Open Settings to enable desktop reminders, add reminder times,\n"
            "and edit the notification message.\n"
            "Reminder times use 24-hour format.",
        ),
        (
            "Hotkeys",
            "Keyboard shortcuts can be changed in Settings.\n"
            "Default keys browse months and years,\n"
            "and Home returns to the current month.",
        ),
        (
            "Import, export, and reset",
            "Use the File menu to import validated JSON,\n"
            "export current data, or reset saved data after confirmation.",
        ),
        (
            "Tray behavior",
            "When the system tray is available, closing the main window hides Cozy Library to the tray.\n"
            "Use the tray menu to reopen or exit the app.",
        ),
        (
            "Local data",
            "Cozy Library stores runtime data in a local SQLite database.\n"
            "JSON files are used for import, export, and migration.",
        ),
    ]

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
            padx=42,
            pady=28,
        )
        container.pack(fill="both", expand=True)

        content = tk.Frame(container, bg="#efe6d5")
        content.pack(fill="both", expand=True, pady=(0, 14))

        for title, body in self.HELP_SECTIONS:
            self._pack_heading(content, title, font_size=14, width=390, height=22, pady=(0, 2))
            tk.Label(
                content,
                text=body,
                font=(self._ui_font_family, 9),
                bg="#efe6d5",
                fg="#2b2118",
                wraplength=620,
                justify="left",
            ).pack(anchor="w", pady=(0, 8))

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
