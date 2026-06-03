"""Start Cozy Library.

Creates core services, loads runtime data, and opens the Tkinter main window.
"""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import messagebox

from src import DateService, LayoutManager, MainWindow, NotificationService, StorageError, StorageManager
from src.path_utils import get_runtime_data_path, migrate_legacy_runtime_data, resource_path


def main() -> None:
    """Create services, load data, and launch the application."""
    assets_root = resource_path("assets")
    migrate_legacy_runtime_data()
    data_path = get_runtime_data_path()
    icon_path = resource_path("assets/app.ico")
    start_hidden = "--start-hidden" in sys.argv

    root = tk.Tk()
    root.withdraw()
    try:
        if icon_path.exists():
            root.iconbitmap(default=str(icon_path))
    except tk.TclError:
        pass

    date_service = DateService()
    storage_manager = StorageManager(data_path, date_service=date_service)

    try:
        habit_data = storage_manager.load()
    except StorageError as error:
        messagebox.showerror("Storage Error", str(error), parent=root)
        root.destroy()
        return

    layout_manager = LayoutManager(assets_root=assets_root)
    notification_service = NotificationService(date_service=date_service)

    window = MainWindow(
        root=root,
        habit_data=habit_data,
        storage_manager=storage_manager,
        date_service=date_service,
        layout_manager=layout_manager,
        notification_service=notification_service,
        assets_root=assets_root,
        start_hidden=start_hidden,
    )

    if not window.start_hidden_effective:
        root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()
