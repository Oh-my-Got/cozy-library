"""Coordinate the main Cozy Library window.

Builds the main UI, connects services, refreshes views, and handles app actions.
"""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

from .background_utils import render_background_view
from .date_service import DateService
from .description_panel import DescriptionPanel
from .exceptions import ImportValidationError, StorageError
from .footer_view import FooterView
from .header_view import HeaderView
from .layout import LayoutManager
from .models import HabitData
from .notification_service import NotificationService
from .path_utils import get_downloads_dir, resource_path
from .settings_dialog import SettingsDialog
from .shelf_view import ShelfView
from .startup_service import StartupService
from .statistics_window import StatisticsWindow
from .storage import StorageManager
from .tray_service import TrayService
from .ui_rendering import choose_ui_font_family, render_text_image
from .uninstall_service import UninstallService
from .ui_constants import (
    CANVAS_BACKGROUND_FALLBACK,
    CANVAS_BORDER_COLOR,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    CANVAS_X,
    CANVAS_Y,
    DESCRIPTION_DISPLAY_TEXT_COLOR,
    DESCRIPTION_EDIT_BACKGROUND_COLOR,
    DESCRIPTION_EDIT_TEXT_COLOR,
    HEADER_DATE_FONT_SIZE,
    HEADER_CANVAS_HEIGHT,
    HEADER_CANVAS_WIDTH,
    HEADER_CANVAS_X,
    HEADER_CANVAS_Y,
    HEADER_DATE_Y,
    HEADER_LABEL_HEIGHT,
    HEADER_LABEL_WIDTH,
    HEADER_MONTH_FONT_SIZE,
    HEADER_MONTH_Y,
    HEADER_TEXT_COLOR,
    MAIN_WINDOW_RATIO_HEIGHT,
    MAIN_WINDOW_RATIO_WIDTH,
    MIN_RESPONSIVE_WINDOW_HEIGHT,
    MIN_RESPONSIVE_WINDOW_WIDTH,
    NAVIGATION_Y,
    NEXT_BUTTON_WIDTH,
    NEXT_BUTTON_X,
    PREV_BUTTON_WIDTH,
    PREV_BUTTON_X,
    UI_FONT_FAMILY,
    WINDOW_BACKGROUND_FALLBACK,
    WINDOW_BACKGROUND_OFFSET_X,
    WINDOW_BACKGROUND_OFFSET_Y,
    WINDOW_HEIGHT,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_WIDTH,
    fit_window_to_screen,
)

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
except ImportError:  # pragma: no cover - depends on local environment
    Image = None
    ImageDraw = None
    ImageFont = None
    ImageTk = None


class MainWindow:
    """Coordinate the main interface and application services."""

    def __init__(
        self,
        root: tk.Tk,
        habit_data: HabitData,
        storage_manager: StorageManager,
        date_service: DateService,
        layout_manager: LayoutManager,
        notification_service: NotificationService,
        assets_root: Path | str | None = None,
        start_hidden: bool = False,
    ) -> None:
        self.root = root
        self.habit_data = habit_data
        self.storage_manager = storage_manager
        self.date_service = date_service
        self.layout_manager = layout_manager
        self.notification_service = notification_service
        self._assets_root = Path(assets_root) if assets_root is not None else resource_path("assets")
        self._start_hidden_requested = start_hidden
        self.window_width, self.window_height = fit_window_to_screen(
            self.root.winfo_screenwidth(),
            self.root.winfo_screenheight(),
            aspect_width=MAIN_WINDOW_RATIO_WIDTH,
            aspect_height=MAIN_WINDOW_RATIO_HEIGHT,
            min_width=WINDOW_WIDTH,
            min_height=MIN_RESPONSIVE_WINDOW_HEIGHT,
        )
        self._scale_x = self.window_width / WINDOW_WIDTH
        self._scale_y = self.window_height / WINDOW_HEIGHT

        self.shelf_view: ShelfView | None = None
        self.statistics_window: StatisticsWindow | None = None
        self.settings_window: tk.Toplevel | None = None
        self._settings_dialog: SettingsDialog | None = None
        self._notification_job_id: str | None = None
        self._bound_hotkey_sequences: dict[str, list[str]] = {}
        self._is_exiting = False
        self._date_label_var = tk.StringVar()
        self._month_label_var = tk.StringVar()
        self._footer_total_title_var = tk.StringVar()
        self._footer_total_value_var = tk.StringVar()
        self._footer_month_title_var = tk.StringVar()
        self._footer_month_value_var = tk.StringVar()
        self._today_button_var = tk.StringVar()
        self._window_background_photo = None
        self._header_font_path = self._assets_root / "poxast.regular.ttf"
        self._tray_icon_path = self._assets_root / "tray.ico"
        if not self._tray_icon_path.exists():
            self._tray_icon_path = self._assets_root / "app.ico"
        self._ui_font_family = UI_FONT_FAMILY
        self.startup_service = StartupService(icon_path=self._tray_icon_path)
        self.uninstall_service = UninstallService(startup_service=self.startup_service)
        self.tray_service = TrayService(
            icon_path=self._tray_icon_path,
            on_open=lambda: self.root.after(0, self._restore_from_tray),
            on_exit=lambda: self.root.after(0, self._exit_application),
        )
        self._tray_available = self.tray_service.start()
        self.start_hidden_effective = self._start_hidden_requested and self._tray_available
        self._recalculate_geometry()

        self._background_label = tk.Label(
            self.root,
            bd=0,
            highlightthickness=0,
            bg=WINDOW_BACKGROUND_FALLBACK,
            anchor="nw",
        )
        self._background_label.place(x=0, y=0, relwidth=1, relheight=1)
        self._background_label.lower()

        self._build_ui()
        self._bind_shortcuts()
        self.refresh_ui(sync_description_text=True, redraw_shelf=True)
        self.schedule_notification_check()
        self._enable_startup_on_first_profile_if_needed()

        if self.storage_manager.last_warning:
            self.root.after(100, self._show_startup_warning)

        self.root.protocol("WM_DELETE_WINDOW", self._handle_close)

    def _ensure_tray_running(self) -> bool:
        if self.tray_service is None:
            self._tray_available = False
            return False

        if self.tray_service.is_running:
            self._tray_available = True
            return True

        self._tray_available = self.tray_service.start()
        return self._tray_available

    def _recalculate_geometry(self) -> None:
        horizontal_margin = self._sx(16)
        self.header_canvas_width = min(self._sx(HEADER_CANVAS_WIDTH), self.window_width - self._sx(220))
        self.header_canvas_height = self._sy(HEADER_CANVAS_HEIGHT)
        self.header_canvas_x = max(horizontal_margin, (self.window_width - self.header_canvas_width) // 2)
        self.header_canvas_y = self._sy(HEADER_CANVAS_Y)
        self.header_label_width = self.header_canvas_width
        self.header_label_height = self._sy(HEADER_LABEL_HEIGHT)
        self.header_month_y = self._sy(HEADER_MONTH_Y)
        self.header_date_y = self._sy(HEADER_DATE_Y)

        self.description_entry_width = round(self.window_width * (2.25 / 3))
        self.description_entry_x = max(horizontal_margin, (self.window_width - self.description_entry_width) // 2)
        self.description_entry_y = self.header_canvas_y + self.header_canvas_height + self._sy(10)
        self.prev_button_width = self._sx(PREV_BUTTON_WIDTH)
        self.next_button_width = self._sx(NEXT_BUTTON_WIDTH)
        self.prev_button_x = horizontal_margin
        self.next_button_x = self.window_width - horizontal_margin - self.next_button_width
        self.navigation_y = self.header_canvas_y + self._sy(10)

        reserved_bottom = self._sy(118)
        self.canvas_width = min(CANVAS_WIDTH, self.window_width - (horizontal_margin * 2))
        self.canvas_x = max(horizontal_margin, (self.window_width - self.canvas_width) // 2)
        self.canvas_y = self._sy(CANVAS_Y)
        self.description_entry_height = max(self._sy(92), self.canvas_y - self.description_entry_y - self._sy(16))
        available_canvas_height = self.window_height - self.canvas_y - reserved_bottom
        self.canvas_height = min(CANVAS_HEIGHT, max(680, available_canvas_height))

        self.footer_x = horizontal_margin
        self.footer_y = self.canvas_y + self.canvas_height + self._sy(8)
        self.footer_width = self.window_width - (horizontal_margin * 2)
        self.footer_height = self.window_height - self.footer_y - self._sy(12)
        self.footer_column_gap = self._sx(16)
        self.footer_column_width = max(120, (self.footer_width - (self.footer_column_gap * 2)) // 3)

    def _sx(self, value: int) -> int:
        return max(1, round(value * self._scale_x))

    def _sy(self, value: int) -> int:
        return max(1, round(value * self._scale_y))

    def _font_size(self, value: int) -> int:
        return max(8, round(value * min(self._scale_x, self._scale_y)))

    def _build_ui(self) -> None:
        """Build the main window layout and connect user actions."""
        self.root.title("Cozy Library")
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.root.minsize(self.window_width, self.window_height)
        self.root.resizable(False, False)
        self.root.configure(bg=WINDOW_BACKGROUND_FALLBACK)
        self._configure_ui_fonts()
        window_x = max(0, (self.root.winfo_screenwidth() - self.window_width) // 2)
        window_y = max(0, (self.root.winfo_screenheight() - self.window_height) // 2)
        self.root.geometry(f"{self.window_width}x{self.window_height}+{window_x}+{window_y}")

        self._build_menu()

        self.header_view = HeaderView(
            self.root,
            ui_font_family=self._ui_font_family,
            font_size_fn=self._font_size,
            header_font_path=self._header_font_path,
            canvas_background_fallback=CANVAS_BACKGROUND_FALLBACK,
        )
        self.header_view.place(
            self.header_canvas_x,
            self.header_canvas_y,
            self.header_canvas_width,
            self.header_canvas_height,
        )
        self.root.tk.call("raise", self.header_view.canvas._w)

        self.description_panel = DescriptionPanel(
            self.root,
            ui_font_family=self._ui_font_family,
            font_size_fn=self._font_size,
            sx_fn=self._sx,
            sy_fn=self._sy,
            edit_background_color=DESCRIPTION_EDIT_BACKGROUND_COLOR,
            edit_text_color=DESCRIPTION_EDIT_TEXT_COLOR,
            display_text_color=DESCRIPTION_DISPLAY_TEXT_COLOR,
            display_background_fallback=WINDOW_BACKGROUND_FALLBACK,
            on_focus_out=self._handle_description_focus_out,
        )
        self.description_panel.place(
            self.description_entry_x,
            self.description_entry_y,
            self.description_entry_width,
            self.description_entry_height,
        )

        self.previous_button = ttk.Button(
            self.root,
            text="Previous Month",
            command=self.show_previous_month,
        )
        self.previous_button.place(
            x=self.prev_button_x,
            y=self.navigation_y,
            width=self.prev_button_width,
            height=self._sy(32),
        )

        self.next_button = ttk.Button(
            self.root,
            text="Next Month",
            command=self.show_next_month,
        )
        self.next_button.place(
            x=self.next_button_x,
            y=self.navigation_y,
            width=self.next_button_width,
            height=self._sy(32),
        )

        self.canvas = tk.Canvas(
            self.root,
            width=self.canvas_width,
            height=self.canvas_height,
            bg=CANVAS_BACKGROUND_FALLBACK,
            bd=0,
            highlightthickness=0,
            highlightbackground=CANVAS_BORDER_COLOR,
        )
        self.canvas.place(x=self.canvas_x, y=self.canvas_y, width=self.canvas_width, height=self.canvas_height)
        self.layout_manager.configure_viewport(
            self.canvas_x,
            self.canvas_y,
            self.canvas_width,
            self.canvas_height,
        )

        self.shelf_view = ShelfView(
            canvas=self.canvas,
            habit_data=self.habit_data,
            date_service=self.date_service,
            layout_manager=self.layout_manager,
            on_state_changed=self._handle_shelf_state_changed,
            assets_root=self._assets_root,
        )
        self.canvas.bind("<Button-1>", self.shelf_view.handle_click)

        self.footer_view = FooterView(
            self.root,
            ui_font_family=self._ui_font_family,
            font_size_fn=self._font_size,
            text_color=DESCRIPTION_DISPLAY_TEXT_COLOR,
            background_fallback=WINDOW_BACKGROUND_FALLBACK,
        )
        footer_button_width = max(118, self.footer_column_width - self._sx(20))
        footer_left_center_x = self.footer_column_width // 2
        footer_center_center_x = self.footer_column_width + self.footer_column_gap + (self.footer_column_width // 2)
        footer_right_center_x = ((self.footer_column_width + self.footer_column_gap) * 2) + (self.footer_column_width // 2)
        self.footer_view.place(
            self.footer_x,
            self.footer_y,
            self.footer_width,
            self.footer_height,
            total_center_x=footer_left_center_x,
            month_center_x=footer_center_center_x,
            title_y=self._sy(12),
            value_y=self._sy(38),
        )

        self.toggle_today_button = ttk.Button(
            self.root,
            textvariable=self._today_button_var,
            command=self.toggle_today,
        )
        self.toggle_today_button.place(
            x=self.footer_x + footer_right_center_x - 94,
            y=self.footer_y + self._sy(18),
            width=self._sx(189),
            height=self._sy(32),
        )

        self.stats_button = ttk.Button(
            self.root,
            text="See Details",
            command=self.open_statistics_window,
        )
        self.stats_button.place(
            x=self.footer_x + footer_right_center_x - 94,
            y=self.footer_y + self._sy(56),
            width=self._sx(189),
            height=self._sy(32),
        )

        self.root.bind("<Button-1>", self._handle_root_click_focus_out, add="+")

    def _build_menu(self) -> None:
        """Build file, settings, and view menus."""
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Import JSON", command=self.import_json)
        file_menu.add_command(label="Export JSON", command=self.export_json)
        file_menu.add_separator()
        file_menu.add_command(label="Reset all data", command=self.reset_all_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._exit_application)
        menu_bar.add_cascade(label="File", menu=file_menu)

        settings_menu = tk.Menu(menu_bar, tearoff=False)
        settings_menu.add_command(label="Notification settings", command=self.open_settings_dialog)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)

        view_menu = tk.Menu(menu_bar, tearoff=False)
        view_menu.add_command(label="Detailed statistics", command=self.open_statistics_window)
        menu_bar.add_cascade(label="View", menu=view_menu)

        self.root.config(menu=menu_bar)

    def _bind_shortcuts(self) -> None:
        self._apply_hotkey_bindings()

    def refresh_ui(self, sync_description_text: bool = True, redraw_shelf: bool = True) -> None:
        """Refresh visible UI state from the current habit data."""
        self._date_label_var.set(self._format_current_date())

        if sync_description_text:
            current_text = self._get_description_text()
            if current_text != self.habit_data.description:
                self.description_panel.set_text(self.habit_data.description)
            self._refresh_description_display()

        today_completed = self.habit_data.is_completed(self.date_service.today())
        today_button_text = "Unmark Today" if today_completed else "Mark Today"
        self._today_button_var.set(today_button_text)
        self._refresh_header_canvas_background()

        if self.shelf_view is not None:
            self._refresh_window_background(self.shelf_view.active_layout.window_background_path)
            self._refresh_footer_background(self.shelf_view.active_layout.window_background_path)
            self.canvas.configure(
                width=self.shelf_view.active_layout.canvas_width,
                height=self.shelf_view.active_layout.canvas_height,
            )
            self.canvas.place(
                x=self.shelf_view.active_layout.canvas_x,
                y=self.shelf_view.active_layout.canvas_y,
                width=self.shelf_view.active_layout.canvas_width,
                height=self.shelf_view.active_layout.canvas_height,
            )
            self._month_label_var.set(self.shelf_view.get_selected_month_label())
            self._refresh_header_texts()
            month_completed = self.shelf_view.get_selected_month_completed()
            month_percentage = self.shelf_view.get_selected_month_percentage()
            if redraw_shelf:
                self.shelf_view.draw()
        else:
            self._clear_window_background()
            self._clear_footer_background()
            self._refresh_header_texts()
            month_completed = 0
            month_percentage = 0.0

        total_completed = self.habit_data.get_total_completed()
        self._footer_total_title_var.set("Total Completed Days")
        self._footer_total_value_var.set(str(total_completed))
        self._footer_month_title_var.set(self._get_footer_month_name())
        self._footer_month_value_var.set(f"{month_percentage:.0f}%")
        self.footer_view.update_texts(
            total_title=self._footer_total_title_var.get(),
            total_value=self._footer_total_value_var.get(),
            month_title=self._footer_month_title_var.get(),
            month_value=self._footer_month_value_var.get(),
        )
        self._refresh_statistics_window_if_open()

    def save_description(self, event: tk.Event | None = None) -> None:
        """Save edited description text and restore the previous value on failure."""
        previous_description = self.habit_data.description
        self.habit_data.description = self._get_description_text()
        if self._save_current_state():
            self.refresh_ui(sync_description_text=False, redraw_shelf=False)
            self._show_description_display_mode()
            return

        self.habit_data.description = previous_description
        self.refresh_ui(sync_description_text=True, redraw_shelf=False)

    def _handle_description_focus_out(self, event: tk.Event | None = None) -> None:
        self.root.after_idle(self._finalize_description_focus_change)

    def toggle_today(self) -> None:
        """Toggle today's completion state and revert if saving fails."""
        today = self.date_service.today()
        self.habit_data.toggle_day(today)
        if self._save_current_state():
            self.refresh_ui(sync_description_text=False, redraw_shelf=True)
            return

        self.habit_data.toggle_day(today)
        self.refresh_ui(sync_description_text=False, redraw_shelf=True)

    def show_previous_month(self) -> None:
        if self.shelf_view is None:
            return
        self.shelf_view.go_previous_month()
        self.refresh_ui(sync_description_text=False, redraw_shelf=False)

    def show_next_month(self) -> None:
        if self.shelf_view is None:
            return
        self.shelf_view.go_next_month()
        self.refresh_ui(sync_description_text=False, redraw_shelf=False)

    def import_json(self) -> None:
        """Import and validate habit data from a selected JSON file."""
        file_path = filedialog.askopenfilename(
            title="Import habit data",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            imported_data = self.storage_manager.import_file(file_path)
            imported_data.last_opened_at = self.date_service.now().isoformat(timespec="seconds")
            self.storage_manager.save(imported_data)
            self._set_habit_data(imported_data)
            self.refresh_ui(sync_description_text=True, redraw_shelf=True)
            messagebox.showinfo("Import Complete", "Habit data was imported successfully.")
        except ImportValidationError as error:
            messagebox.showerror("Import Failed", str(error))
        except StorageError as error:
            messagebox.showerror("Save Failed", str(error))

    def export_json(self) -> None:
        """Export the current habit data to a selected JSON file."""
        export_name = f"cozy_library_data_{self.date_service.today().isoformat()}.json"
        file_path = filedialog.asksaveasfilename(
            title="Export habit data",
            defaultextension=".json",
            initialdir=str(get_downloads_dir()),
            initialfile=export_name,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            self.storage_manager.export_file(file_path, self.habit_data)
            messagebox.showinfo("Export Complete", "Habit data was exported successfully.")
        except StorageError as error:
            messagebox.showerror("Export Failed", str(error))

    def reset_all_data(self) -> None:
        """Reset all saved habit data after two user confirmations."""
        first_confirm = messagebox.askyesno(
            "Reset All Data",
            "This will remove the current habit description and all completion history. Continue?",
        )
        if not first_confirm:
            return

        second_confirm = messagebox.askyesno(
            "Confirm Reset",
            "Are you absolutely sure you want to reset all data? This cannot be undone.",
        )
        if not second_confirm:
            return

        try:
            new_data = self.storage_manager.reset_data()
            self._set_habit_data(new_data)
            if self.shelf_view is not None:
                current_year, current_month = self.date_service.get_current_year_month()
                self.shelf_view.refresh_month(current_year, current_month)
            self.refresh_ui(sync_description_text=True, redraw_shelf=False)
            messagebox.showinfo("Reset Complete", "All habit data has been reset.")
        except StorageError as error:
            messagebox.showerror("Reset Failed", str(error))

    def open_settings_dialog(self) -> None:
        """Open the settings dialog or focus the existing one."""
        if self._settings_dialog is not None and self._settings_dialog.is_open():
            self._settings_dialog.show()
            self.settings_window = self._settings_dialog.window
            return

        self._settings_dialog = SettingsDialog(
            parent=self.root,
            habit_data=self.habit_data,
            notification_service=self.notification_service,
            storage_manager=self.storage_manager,
            ui_font_family=self._ui_font_family,
            render_text_image=self._render_text_image,
            handle_container_click_focus_out=self._handle_container_click_focus_out,
            apply_hotkey_bindings=self._apply_hotkey_bindings,
            apply_startup_preference=self._apply_startup_preference,
            confirm_and_uninstall=self._confirm_and_uninstall,
            on_close=self._handle_settings_dialog_closed,
        )
        self.settings_window = self._settings_dialog.window

    def _handle_settings_dialog_closed(self) -> None:
        self._settings_dialog = None
        self.settings_window = None

    def schedule_notification_check(self) -> None:
        """Run reminder checks on a repeating timer."""
        sent = self.notification_service.check_and_send(self.habit_data)
        if sent:
            self._save_current_state(show_error=False)

        self._notification_job_id = self.root.after(15_000, self.schedule_notification_check)

    def _set_habit_data(self, habit_data: HabitData) -> None:
        self.habit_data = habit_data
        self._apply_hotkey_bindings()
        if self.shelf_view is not None:
            self.shelf_view.habit_data = habit_data
        if self.statistics_window is not None and self.statistics_window.is_open():
            self.statistics_window.habit_data = habit_data

    def _handle_shelf_state_changed(self) -> bool:
        if self._save_current_state():
            self.refresh_ui(sync_description_text=False, redraw_shelf=False)
            return True
        return False

    def _save_current_state(self, show_error: bool = True) -> bool:
        try:
            self.storage_manager.save(self.habit_data)
            return True
        except StorageError as error:
            if show_error:
                messagebox.showerror("Save Failed", str(error))
            return False

    def _show_startup_warning(self) -> None:
        warning_text = self.storage_manager.last_warning
        if warning_text:
            messagebox.showwarning("Recovered Data File", warning_text)
            self.storage_manager.last_warning = None

    def _get_description_text(self) -> str:
        return self.description_panel.get_text()

    def _show_description_display_mode(self) -> None:
        self._refresh_description_display()
        self.description_panel.show_display_mode()

    def _finalize_description_focus_change(self) -> None:
        """Save or close the description editor after focus has settled."""
        focused_widget = self.root.focus_get()
        if self.description_panel.contains_widget(focused_widget):
            return
        if self._get_description_text() != self.habit_data.description:
            self.save_description()
            return
        self._show_description_display_mode()

    def _refresh_description_display(self) -> None:
        """Render the description display using the active background image."""
        self.description_panel.refresh_display(
            text=self.habit_data.description,
            background_path=self._get_active_background_path(),
            offset_x=WINDOW_BACKGROUND_OFFSET_X - self.description_entry_x,
            offset_y=WINDOW_BACKGROUND_OFFSET_Y - self.description_entry_y,
        )

    def _configure_ui_fonts(self) -> None:
        """Apply the selected UI font family to Tkinter named fonts."""
        self._ui_font_family = choose_ui_font_family(self.root)

        for font_name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            named_font = tkfont.nametofont(font_name)
            named_font.configure(family=self._ui_font_family)

        style = ttk.Style(self.root)
        style.configure("TButton", font=(self._ui_font_family, self._font_size(10)))
        style.configure("TCheckbutton", font=(self._ui_font_family, self._font_size(10)))

    def _handle_root_click_focus_out(self, event: tk.Event) -> None:
        self._handle_container_click_focus_out(self.root, event)

    def _handle_container_click_focus_out(self, container: tk.Misc, event: tk.Event) -> None:
        """Move focus away from text widgets when clicking outside editable controls."""
        focused_widget = container.focus_get()
        clicked_widget = event.widget

        if focused_widget is None:
            return
        if clicked_widget is focused_widget:
            return
        if isinstance(clicked_widget, (ttk.Entry, tk.Entry, tk.Text)):
            return

        container.after_idle(container.focus_set)

    def _enable_startup_on_first_profile_if_needed(self) -> None:
        """Enable startup automatically for a new packaged Windows profile."""
        if not self.storage_manager.created_default_on_load:
            return
        if not self._tray_available:
            return
        if not self.startup_service.is_supported:
            return
        if not self.habit_data.startup_enabled:
            return

        try:
            if not self.startup_service.is_startup_enabled():
                self.startup_service.enable_startup()
        except Exception:
            # Startup enrollment is best-effort and should not block the main app.
            pass

    def _apply_startup_preference(self) -> None:
        """Apply the saved startup preference to Windows startup shortcuts."""
        if not self.startup_service.is_supported:
            return

        try:
            if self.habit_data.startup_enabled:
                if not self.startup_service.is_startup_enabled():
                    self.startup_service.enable_startup()
            else:
                if self.startup_service.is_startup_enabled():
                    self.startup_service.disable_startup()
        except Exception:
            # Startup enrollment is best-effort and should not block the main app.
            pass

    def _format_current_date(self) -> str:
        current_date = self.date_service.today()
        weekday_name = current_date.strftime("%A").lower()
        return f"Today {weekday_name} {current_date.day}"

    def _refresh_header_texts(self) -> None:
        self.header_view.update_texts(
            month_text=self._month_label_var.get(),
            date_text=self._date_label_var.get(),
            month_center_y=(self.header_month_y - self.header_canvas_y) + (self.header_label_height // 2),
            date_center_y=(self.header_date_y - self.header_canvas_y) + (self.header_label_height // 2),
            label_width=self.header_label_width,
            label_height=self.header_label_height,
            month_font_size=self._font_size(HEADER_MONTH_FONT_SIZE),
            date_font_size=self._font_size(HEADER_DATE_FONT_SIZE),
        )

    def _render_text_image(self, text: str, font_size: int, width: int, height: int, *, align: str = "center"):
        return render_text_image(
            text,
            self._header_font_path,
            font_size,
            width,
            height,
            fill=HEADER_TEXT_COLOR,
            align=align,
        )

    def _apply_hotkey_bindings(self) -> None:
        """Bind the current navigation hotkeys to main-window actions."""
        for sequences in self._bound_hotkey_sequences.values():
            for sequence in sequences:
                self.root.unbind(sequence)

        hotkey_map = {
            "previous_month": (self.habit_data.hotkeys.previous_month, self._handle_previous_month_hotkey),
            "next_month": (self.habit_data.hotkeys.next_month, self._handle_next_month_hotkey),
            "previous_year": (self.habit_data.hotkeys.previous_year, self._handle_previous_year_hotkey),
            "next_year": (self.habit_data.hotkeys.next_year, self._handle_next_year_hotkey),
            "current_month": (self.habit_data.hotkeys.current_month, self._handle_current_month_hotkey),
        }

        self._bound_hotkey_sequences = {}
        for action_name, (keysym, handler) in hotkey_map.items():
            sequences = [f"<{keysym}>"]
            if len(keysym) == 1 and keysym.isalpha():
                sequences.append(f"<{keysym.upper()}>")

            for sequence in sequences:
                self.root.bind(sequence, handler)
            self._bound_hotkey_sequences[action_name] = sequences

    def _is_text_input_focused(self) -> bool:
        focused_widget = self.root.focus_get()
        return isinstance(focused_widget, (ttk.Entry, tk.Entry, tk.Text))

    def _handle_previous_month_hotkey(self, event: tk.Event | None = None) -> None:
        if self._is_text_input_focused():
            return
        self.show_previous_month()

    def _handle_next_month_hotkey(self, event: tk.Event | None = None) -> None:
        if self._is_text_input_focused():
            return
        self.show_next_month()

    def _handle_current_month_hotkey(self, event: tk.Event | None = None) -> None:
        if self._is_text_input_focused():
            return
        if self.shelf_view is None:
            return

        current_year, current_month = self.date_service.get_current_year_month()
        self.shelf_view.refresh_month(current_year, current_month)
        self.refresh_ui(sync_description_text=False, redraw_shelf=False)

    def _handle_previous_year_hotkey(self, event: tk.Event | None = None) -> None:
        if self._is_text_input_focused():
            return
        if self.shelf_view is None:
            return

        self.shelf_view.refresh_month(self.shelf_view.current_year - 1, self.shelf_view.current_month)
        self.refresh_ui(sync_description_text=False, redraw_shelf=False)

    def _handle_next_year_hotkey(self, event: tk.Event | None = None) -> None:
        if self._is_text_input_focused():
            return
        if self.shelf_view is None:
            return

        self.shelf_view.refresh_month(self.shelf_view.current_year + 1, self.shelf_view.current_month)
        self.refresh_ui(sync_description_text=False, redraw_shelf=False)

    def _get_footer_month_name(self) -> str:
        month_label = self._month_label_var.get().strip()
        if not month_label:
            return "Month"
        return month_label.split()[0].title()

    def _confirm_and_uninstall(self, parent: tk.Misc | None = None) -> None:
        """Confirm and run uninstall cleanup actions."""
        primary_message = (
            "This will close Cozy Library, remove it from Windows startup, "
            "and delete its saved data from AppData.\n\nContinue?"
        )
        if not messagebox.askyesno("Uninstall Application", primary_message, parent=parent):
            return

        if self.uninstall_service.can_self_delete_executable:
            secondary_message = (
                "The packaged application executable will also be deleted from disk.\n\n"
                "This cannot be undone. Continue?"
            )
        else:
            secondary_message = (
                "Saved data and startup shortcuts will be removed, but source files in this "
                "development folder will stay on disk.\n\nContinue?"
            )

        if not messagebox.askyesno("Confirm Uninstall", secondary_message, parent=parent):
            return

        try:
            self.uninstall_service.remove_startup_shortcut()
            if self.uninstall_service.can_self_delete_executable:
                self.uninstall_service.schedule_packaged_uninstall()
            else:
                self.uninstall_service.clear_runtime_data()
        except Exception as error:
            messagebox.showerror("Uninstall Failed", str(error), parent=parent)
            return

        self._exit_application()

    def _refresh_header_canvas_background(self) -> None:
        if self.shelf_view is None or ImageTk is None:
            return

        self.header_view.refresh_background(
            self.shelf_view.active_layout.window_background_path,
            WINDOW_BACKGROUND_OFFSET_X - self.header_canvas_x,
            WINDOW_BACKGROUND_OFFSET_Y - self.header_canvas_y,
            WINDOW_BACKGROUND_FALLBACK,
        )

    def _refresh_window_background(self, image_path: Path) -> None:
        """Render the main window background from the active month image."""
        if Image is None or ImageTk is None or not image_path.exists():
            self._clear_window_background()
            return

        try:
            image = render_background_view(
                image_path,
                self.window_width,
                self.window_height,
                WINDOW_BACKGROUND_OFFSET_X,
                WINDOW_BACKGROUND_OFFSET_Y,
            )
            self._window_background_photo = ImageTk.PhotoImage(image)
            self._background_label.configure(image=self._window_background_photo, bg=WINDOW_BACKGROUND_FALLBACK)
            self._background_label.place(x=0, y=0, width=self.window_width, height=self.window_height)
        except (OSError, FileNotFoundError, RuntimeError):
            self._clear_window_background()

    def _clear_window_background(self) -> None:
        self._window_background_photo = None
        self._background_label.configure(image="", bg=WINDOW_BACKGROUND_FALLBACK)
        self._background_label.place(x=0, y=0, relwidth=1, relheight=1)

    def _refresh_footer_background(self, image_path: Path) -> None:
        self.footer_view.refresh_background(
            image_path,
            WINDOW_BACKGROUND_OFFSET_X - self.footer_x,
            WINDOW_BACKGROUND_OFFSET_Y - self.footer_y,
            WINDOW_BACKGROUND_FALLBACK,
        )

    def _clear_footer_background(self) -> None:
        self.footer_view.clear_background(WINDOW_BACKGROUND_FALLBACK)

    def _handle_close(self) -> None:
        """Hide to tray when available, otherwise exit the application."""
        if not self._is_exiting and self._ensure_tray_running():
            self._hide_to_tray()
            return
        self._exit_application()

    def _hide_to_tray(self) -> None:
        if not self._ensure_tray_running():
            self._exit_application()
            return
        self.root.withdraw()

    def _restore_from_tray(self) -> None:
        if not self.root.winfo_exists():
            return
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _exit_application(self) -> None:
        """Stop background services and close the application."""
        if self._is_exiting:
            return
        self._is_exiting = True
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.destroy()
        if self.statistics_window is not None and self.statistics_window.is_open():
            self.statistics_window.close()
        if self._notification_job_id is not None:
            try:
                self.root.after_cancel(self._notification_job_id)
            except ValueError:
                pass
        if self.tray_service is not None:
            self.tray_service.stop()
        self.root.destroy()

    def open_statistics_window(self) -> None:
        """Open the statistics window or refresh the existing one."""
        background_path = self._get_active_background_path()
        if self.statistics_window is not None and self.statistics_window.is_open():
            self.statistics_window.refresh(
                habit_data=self.habit_data,
                window_background_path=background_path,
            )
            self.statistics_window.lift()
            return

        self.statistics_window = StatisticsWindow(
            parent=self.root,
            habit_data=self.habit_data,
            date_service=self.date_service,
            window_background_path=background_path,
            assets_root=self._assets_root,
        )

    def _refresh_statistics_window_if_open(self) -> None:
        if self.statistics_window is None or not self.statistics_window.is_open():
            return
        self.statistics_window.refresh(
            habit_data=self.habit_data,
            window_background_path=self._get_active_background_path(),
        )

    def _get_active_background_path(self) -> Path:
        if self.shelf_view is not None:
            return self.shelf_view.active_layout.window_background_path
        return self._assets_root / "backgrounds" / "month_01.png"
