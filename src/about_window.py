"""Display project information for Cozy Library.

Provides an overlay About page with application purpose and technology summary.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class AboutPage:
    """Show the About page as an overlay on the main window."""

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
            padx=48,
            pady=44,
        )
        container.pack(fill="both", expand=True)

        tk.Label(
            container,
            text="Cozy Library",
            font=(self._ui_font_family, 18, "bold"),
            bg="#efe6d5",
            fg="#2b2118",
        ).pack(anchor="w")

        tk.Label(
            container,
            text="A one-habit desktop tracker with a bookshelf-style calendar view.",
            font=(self._ui_font_family, 10),
            bg="#efe6d5",
            fg="#2b2118",
            wraplength=520,
            justify="left",
        ).pack(anchor="w", pady=(12, 0))

        tk.Label(
            container,
            text="Coursework desktop application",
            font=(self._ui_font_family, 10),
            bg="#efe6d5",
            fg="#5f5546",
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        technologies = (
            "Technologies used:\n"
            "- Python\n"
            "- Tkinter GUI\n"
            "- JSON data storage\n"
            "- Desktop notifications\n"
            "- System tray integration"
        )
        tk.Label(
            container,
            text=technologies,
            font=(self._ui_font_family, 10),
            bg="#efe6d5",
            fg="#2b2118",
            justify="left",
        ).pack(anchor="w", pady=(28, 0))

        ttk.Button(container, text="Back", command=self.close).pack(anchor="e", side="bottom")
