"""Display a short user guide for Cozy Library.

Provides a Help page overlay for the main workflow and settings.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class HelpPage:
    """Show the Help page as an overlay on the main window."""

    HELP_SECTIONS = [
        (
            "Tracking habit progress",
            "Use Mark Today or Unmark Today to change today's completion state. You can also click visible past or current days on the bookshelf calendar.",
        ),
        (
            "Editing habit description",
            "Click the description area to edit the habit text. Click outside the text box to save the change and return to display mode.",
        ),
        (
            "Using reminders",
            "Open Settings to enable desktop reminders, add reminder times, and edit the notification message. Reminder times use 24-hour HH:MM format.",
        ),
        (
            "Using hotkeys",
            "Open Settings to change the keyboard navigation keys. The default keys browse months and years, and Home returns to the current month.",
        ),
        (
            "Import, export, and reset data",
            "Use the File menu to import validated JSON, export the current data, or reset all data after confirmation.",
        ),
        (
            "Tray behavior",
            "When the system tray is available, closing the main window hides Cozy Library to the tray. Use the tray menu to reopen or exit the app.",
        ),
    ]

    def __init__(self, parent: tk.Tk, *, ui_font_family: str) -> None:
        self.parent = parent
        self._ui_font_family = ui_font_family
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
            pady=34,
        )
        container.pack(fill="both", expand=True)

        tk.Label(
            container,
            text="Help",
            font=(self._ui_font_family, 16, "bold"),
            bg="#efe6d5",
            fg="#2b2118",
        ).pack(anchor="w")

        content = tk.Frame(container, bg="#efe6d5")
        content.pack(fill="both", expand=True, pady=(20, 20))

        for title, body in self.HELP_SECTIONS:
            tk.Label(
                content,
                text=title,
                font=(self._ui_font_family, 11, "bold"),
                bg="#efe6d5",
                fg="#2b2118",
            ).pack(anchor="w", pady=(0, 4))
            tk.Label(
                content,
                text=body,
                font=(self._ui_font_family, 10),
                bg="#efe6d5",
                fg="#2b2118",
                wraplength=620,
                justify="left",
            ).pack(anchor="w", pady=(0, 14))

        ttk.Button(container, text="Back", command=self.close).pack(anchor="e", side="bottom")
