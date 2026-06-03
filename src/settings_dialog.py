"""Build and manage the Cozy Library settings dialog.

Contains reminder-time editing, hotkey capture, startup preference, and save flow.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import tkinter as tk
from tkinter import messagebox, ttk

from .models import (
    DEFAULT_HOTKEYS,
    DEFAULT_NOTIFICATION_PLACEHOLDER,
    MAX_NOTIFICATION_TIMES,
    NotificationSettings,
    HabitData,
)
from .notification_service import NotificationService
from .storage import StorageManager
from .exceptions import StorageError
from .ui_constants import (
    HEADER_TEXT_COLOR,
    SETTINGS_HEADER_FONT_SIZE,
    SETTINGS_HEADER_HEIGHT,
    SETTINGS_HEADER_WIDTH,
    SETTINGS_HEADER_X,
    SETTINGS_HEADER_Y,
    SETTINGS_HOTKEY_PANEL_HEIGHT,
    SETTINGS_HOTKEY_PANEL_Y,
    SETTINGS_NOTIFICATION_PANEL_HEIGHT,
    SETTINGS_NOTIFICATION_PANEL_Y,
    SETTINGS_PANEL_BACKGROUND,
    SETTINGS_PANEL_BORDER,
    SETTINGS_PANEL_WIDTH,
    SETTINGS_PANEL_X,
    SETTINGS_WINDOW_BACKGROUND,
    SETTINGS_WINDOW_HEIGHT,
    SETTINGS_WINDOW_MIN_HEIGHT,
    SETTINGS_WINDOW_MIN_WIDTH,
    SETTINGS_WINDOW_WIDTH,
)


@dataclass(slots=True)
class _SettingsDraft:
    notifications_enabled: bool
    reminder_times: list[str]
    message_template: str
    startup_enabled: bool
    hotkeys: dict[str, str]


class NotificationSettingsEditor:
    """Manage reminder time rows and validation state."""

    def __init__(
        self,
        *,
        parent: tk.Frame,
        enabled_var: tk.BooleanVar,
        ui_font_family: str,
        initial_times: list[str],
        on_layout_changed: Callable[[], None],
    ) -> None:
        self._enabled_var = enabled_var
        self._ui_font_family = ui_font_family
        self._on_layout_changed = on_layout_changed

        self._time_vars: list[tk.StringVar] = []
        self._time_entries: list[tk.Entry] = []
        self._time_row_frames: list[tk.Frame] = []
        self._time_remove_buttons: list[ttk.Button] = []

        self._left_column_x = 18
        self._times_container_width = 320
        self._row_height = 30
        self._row_gap = 8
        self._base_times_y = 154

        self._times_container = tk.Frame(parent, bg=SETTINGS_PANEL_BACKGROUND, bd=0, highlightthickness=0)
        self._times_container.place(x=self._left_column_x, y=self._base_times_y, width=self._times_container_width, height=90)

        self._add_time_button = ttk.Button(parent, text="Add More", command=self._add_time_row)
        self._add_time_hint = tk.Label(
            parent,
            text="Up to 5 reminders.",
            font=(self._ui_font_family, 9),
            bg=SETTINGS_PANEL_BACKGROUND,
            fg="#5f5546",
            justify="left",
        )

        for initial_value in initial_times:
            self._create_time_row(initial_value)

        self.normalize_rows(mark_errors=True)
        self.refresh_layout()

    def get_reminder_times(self) -> list[str]:
        normalized_values = self.normalize_rows(mark_errors=True)
        return [
            value
            for value in normalized_values
            if value != DEFAULT_NOTIFICATION_PLACEHOLDER
        ]

    def get_bottom_y(self) -> int:
        return self._add_button_y + 28

    def refresh_layout(self) -> None:
        for index, row_frame in enumerate(self._time_row_frames):
            row_frame.place(
                x=0,
                y=index * (self._row_height + self._row_gap),
                width=self._times_container_width,
                height=self._row_height,
            )

        rows_height = max(
            self._row_height,
            len(self._time_row_frames) * self._row_height + max(0, len(self._time_row_frames) - 1) * self._row_gap,
        )
        self._times_container.place_configure(height=rows_height)
        self._add_button_y = self._base_times_y + rows_height + 10
        self._add_time_button.place(x=self._left_column_x, y=self._add_button_y, width=112)
        self._add_time_hint.place(x=self._left_column_x + 124, y=self._add_button_y + 4)
        self._update_controls_state()

    def normalize_rows(self, mark_errors: bool = True) -> list[str]:
        normalized_values: list[str] = []
        active_time_indices: dict[str, list[int]] = {}
        invalid_indices: set[int] = set()

        for index, variable in enumerate(self._time_vars):
            raw_value = variable.get().strip() or DEFAULT_NOTIFICATION_PLACEHOLDER
            try:
                normalized = NotificationSettings.normalize_time(raw_value)
            except ValueError:
                variable.set(DEFAULT_NOTIFICATION_PLACEHOLDER)
                normalized = DEFAULT_NOTIFICATION_PLACEHOLDER
                invalid_indices.add(index)

            normalized_values.append(normalized)
            if normalized != DEFAULT_NOTIFICATION_PLACEHOLDER:
                active_time_indices.setdefault(normalized, []).append(index)

        duplicate_indices = {
            index
            for indexes in active_time_indices.values()
            if len(indexes) > 1
            for index in indexes
        }

        if mark_errors:
            for index, entry in enumerate(self._time_entries):
                self._set_time_entry_state(entry, is_error=index in invalid_indices or index in duplicate_indices)

        return normalized_values

    def _set_time_entry_state(self, entry: tk.Entry, *, is_error: bool) -> None:
        if is_error:
            entry.configure(
                highlightbackground="#b54b4b",
                highlightcolor="#b54b4b",
                highlightthickness=2,
                bd=1,
                relief="solid",
            )
        else:
            entry.configure(
                highlightbackground=SETTINGS_PANEL_BORDER,
                highlightcolor=SETTINGS_PANEL_BORDER,
                highlightthickness=1,
                bd=1,
                relief="solid",
            )

    def _update_controls_state(self) -> None:
        notifications_enabled = bool(self._enabled_var.get())
        entry_state = tk.NORMAL if notifications_enabled else tk.DISABLED
        button_state = tk.NORMAL if notifications_enabled else tk.DISABLED

        for entry in self._time_entries:
            entry.configure(state=entry_state)

        for remove_button in self._time_remove_buttons:
            remove_button.configure(state=button_state)

        can_add_more = notifications_enabled and len(self._time_vars) < MAX_NOTIFICATION_TIMES
        self._add_time_button.configure(state=tk.NORMAL if can_add_more else tk.DISABLED)

    def _create_time_row(self, initial_value: str) -> None:
        row_frame = tk.Frame(self._times_container, bg=SETTINGS_PANEL_BACKGROUND, bd=0, highlightthickness=0)
        time_var = tk.StringVar(value=initial_value)

        entry = tk.Entry(
            row_frame,
            textvariable=time_var,
            font=(self._ui_font_family, 10),
            bg="#f6f0e4",
            fg=HEADER_TEXT_COLOR,
            insertbackground=HEADER_TEXT_COLOR,
            relief="solid",
            bd=1,
        )
        self._set_time_entry_state(entry, is_error=False)
        entry.place(x=0, y=0, width=144, height=28)
        entry.bind("<FocusOut>", lambda _event, current_entry=entry, current_var=time_var: self._validate_row_on_focus_out(current_entry, current_var))

        remove_button = ttk.Button(row_frame, text="Remove")
        remove_button.configure(command=lambda current_frame=row_frame, current_var=time_var, current_entry=entry: self._remove_row(current_frame, current_var, current_entry))
        remove_button.place(x=160, y=0, width=94, height=28)

        row_frame.place(x=0, y=0, width=self._times_container_width, height=self._row_height)
        self._time_row_frames.append(row_frame)
        self._time_vars.append(time_var)
        self._time_entries.append(entry)
        self._time_remove_buttons.append(remove_button)

    def _validate_row_on_focus_out(self, current_entry: tk.Entry, current_var: tk.StringVar) -> None:
        raw_value = current_var.get().strip() or DEFAULT_NOTIFICATION_PLACEHOLDER
        try:
            normalized = NotificationSettings.normalize_time(raw_value)
            current_var.set(normalized)
        except ValueError:
            current_var.set(DEFAULT_NOTIFICATION_PLACEHOLDER)
            self._set_time_entry_state(current_entry, is_error=True)
        self.normalize_rows(mark_errors=True)

    def _remove_row(self, current_frame: tk.Frame, current_var: tk.StringVar, current_entry: tk.Entry) -> None:
        if len(self._time_vars) == 1:
            current_var.set(DEFAULT_NOTIFICATION_PLACEHOLDER)
            self._set_time_entry_state(current_entry, is_error=False)
            self.normalize_rows(mark_errors=True)
            return

        index = self._time_row_frames.index(current_frame)
        self._time_row_frames.pop(index)
        self._time_vars.pop(index)
        self._time_entries.pop(index)
        self._time_remove_buttons.pop(index)
        current_frame.destroy()
        self.normalize_rows(mark_errors=True)
        self.refresh_layout()
        self._on_layout_changed()

    def _add_time_row(self) -> None:
        if len(self._time_vars) >= MAX_NOTIFICATION_TIMES:
            return
        self._create_time_row(DEFAULT_NOTIFICATION_PLACEHOLDER)
        self.normalize_rows(mark_errors=True)
        self.refresh_layout()
        self._on_layout_changed()


class HotkeySettingsEditor:
    """Manage keyboard navigation settings and key capture."""

    def __init__(
        self,
        *,
        parent: tk.Frame,
        ui_font_family: str,
        hotkey_values: dict[str, str],
        normalize_keysym: Callable[[str], str],
    ) -> None:
        self.parent = parent
        self._ui_font_family = ui_font_family
        self._normalize_keysym = normalize_keysym
        self._hotkey_vars = {
            action_name: tk.StringVar(value=value)
            for action_name, value in hotkey_values.items()
        }
        self._capture_labels = {
            "previous_month": "Previous month",
            "next_month": "Next month",
            "previous_year": "Previous year",
            "next_year": "Next year",
            "current_month": "Current month",
        }
        self._hotkey_buttons: dict[str, tk.Button] = {}
        self._active_capture_action: str | None = None
        self._build_ui()

    def get_hotkeys(self) -> dict[str, str]:
        return {
            action_name: variable.get()
            for action_name, variable in self._hotkey_vars.items()
        }

    def handle_keypress(self, event: tk.Event) -> str | None:
        """Capture one replacement hotkey or cancel capture with Escape."""
        selected_action = self._active_capture_action
        if selected_action is None:
            return None

        if event.keysym == "Escape":
            self._hotkey_buttons[selected_action].configure(text=self._hotkey_vars[selected_action].get())
            self._active_capture_action = None
            self._refresh_hotkey_button_styles()
            return "break"
        if event.keysym in {"Tab", "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"}:
            return "break"

        normalized = self._normalize_keysym(event.keysym)
        self._hotkey_vars[selected_action].set(normalized)
        self._hotkey_buttons[selected_action].configure(text=normalized)
        self._active_capture_action = None
        self._refresh_hotkey_button_styles()
        return "break"

    def _build_ui(self) -> None:
        tk.Label(
            self.parent,
            text="Reassign the keys used to browse months and years.",
            font=(self._ui_font_family, 10),
            bg=SETTINGS_PANEL_BACKGROUND,
            fg="#5f5546",
        ).place(x=18, y=48)
        tk.Label(
            self.parent,
            text="Click a key box, then press the new key. Escape cancels the capture.",
            font=(self._ui_font_family, 10),
            bg=SETTINGS_PANEL_BACKGROUND,
            fg="#5f5546",
            wraplength=430,
            justify="left",
        ).place(x=18, y=72)

        start_y = 116
        for index, (action_name, description) in enumerate(self._capture_labels.items()):
            y = start_y + (index * 26)
            tk.Label(
                self.parent,
                text=f"{description}:",
                font=(self._ui_font_family, 11, "bold"),
                bg=SETTINGS_PANEL_BACKGROUND,
                fg=HEADER_TEXT_COLOR,
            ).place(x=18, y=y)

            hotkey_button = tk.Button(
                self.parent,
                text=self._hotkey_vars[action_name].get(),
                command=lambda selected_action=action_name: self._begin_hotkey_capture(selected_action),
                width=18,
                font=(self._ui_font_family, 10),
                bg="#f6f0e4",
                fg=HEADER_TEXT_COLOR,
                activebackground="#f6f0e4",
                activeforeground=HEADER_TEXT_COLOR,
                relief="solid",
                bd=1,
                highlightthickness=1,
                highlightbackground=SETTINGS_PANEL_BORDER,
                highlightcolor=SETTINGS_PANEL_BORDER,
            )
            hotkey_button.place(x=182, y=y - 3)
            self._hotkey_buttons[action_name] = hotkey_button

        reset_hotkeys_button = ttk.Button(
            self.parent,
            text="Reset to Defaults",
            command=self._reset_hotkeys_to_defaults,
        )
        reset_hotkeys_button.place(x=484, y=252, width=168)
        self._refresh_hotkey_button_styles()

    def _refresh_hotkey_button_styles(self) -> None:
        for button_action, button in self._hotkey_buttons.items():
            if self._active_capture_action == button_action:
                button.configure(
                    highlightbackground="#6f9f66",
                    highlightcolor="#6f9f66",
                    highlightthickness=2,
                    bd=1,
                    relief="solid",
                )
            else:
                button.configure(
                    highlightbackground=SETTINGS_PANEL_BORDER,
                    highlightcolor=SETTINGS_PANEL_BORDER,
                    highlightthickness=1,
                    bd=1,
                    relief="solid",
                )

    def _begin_hotkey_capture(self, selected_action: str) -> None:
        self._active_capture_action = selected_action
        for button_action, button in self._hotkey_buttons.items():
            if button_action == selected_action:
                button.configure(text="Press a key...")
            else:
                button.configure(text=self._hotkey_vars[button_action].get())
        self._refresh_hotkey_button_styles()
        self.parent.winfo_toplevel().focus_force()

    def _reset_hotkeys_to_defaults(self) -> None:
        self._active_capture_action = None
        for action_name, default_key in DEFAULT_HOTKEYS.items():
            self._hotkey_vars[action_name].set(default_key)
            self._hotkey_buttons[action_name].configure(text=default_key)
        self._refresh_hotkey_button_styles()


class SettingsDialog:
    """Manage the settings window and dialog-local interactions."""

    def __init__(
        self,
        *,
        parent: tk.Tk,
        habit_data: HabitData,
        notification_service: NotificationService,
        storage_manager: StorageManager,
        ui_font_family: str,
        render_text_image: Callable[..., object | None],
        handle_container_click_focus_out: Callable[[tk.Misc, tk.Event], None],
        apply_hotkey_bindings: Callable[[], None],
        apply_startup_preference: Callable[[], None],
        confirm_and_uninstall: Callable[[tk.Misc | None], None],
        on_close: Callable[[], None],
    ) -> None:
        self.parent = parent
        self.habit_data = habit_data
        self.notification_service = notification_service
        self.storage_manager = storage_manager
        self._ui_font_family = ui_font_family
        self._render_text_image = render_text_image
        self._handle_container_click_focus_out = handle_container_click_focus_out
        self._apply_hotkey_bindings = apply_hotkey_bindings
        self._apply_startup_preference = apply_startup_preference
        self._confirm_and_uninstall = confirm_and_uninstall
        self._on_close = on_close

        self.window = tk.Toplevel(self.parent)
        self.window.title("Settings")
        self.window.geometry(f"{SETTINGS_WINDOW_WIDTH}x{SETTINGS_WINDOW_HEIGHT}")
        self.window.minsize(SETTINGS_WINDOW_MIN_WIDTH, SETTINGS_WINDOW_MIN_HEIGHT)
        self.window.resizable(False, False)
        self.window.configure(bg=SETTINGS_WINDOW_BACKGROUND)
        self.window.transient(self.parent)
        self.window.bind(
            "<Button-1>",
            lambda event: self._handle_container_click_focus_out(self.window, event),
            add="+",
        )

        self._enabled_var = tk.BooleanVar(value=self.habit_data.notifications.enabled)
        self._startup_enabled_var = tk.BooleanVar(value=self.habit_data.startup_enabled)
        self._initial_times = self.habit_data.notifications.times or [DEFAULT_NOTIFICATION_PLACEHOLDER]

        self._save_button: ttk.Button | None = None
        self._cancel_button: ttk.Button | None = None
        self._uninstall_button: ttk.Button | None = None
        self._message_label: tk.Label | None = None
        self._message_hint: tk.Label | None = None
        self._message_box_frame: tk.Frame | None = None
        self._message_text: tk.Text | None = None
        self._notification_editor: NotificationSettingsEditor | None = None
        self._hotkey_editor: HotkeySettingsEditor | None = None

        self._build_ui()
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.show()

    def is_open(self) -> bool:
        return bool(self.window.winfo_exists())

    def show(self) -> None:
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()

    def close(self) -> None:
        if self.window.winfo_exists():
            self.window.unbind("<KeyPress>")
            self.window.destroy()
        self._on_close()

    def _build_ui(self) -> None:
        """Build settings sections and action buttons."""
        header_canvas = tk.Canvas(
            self.window,
            width=SETTINGS_HEADER_WIDTH,
            height=SETTINGS_HEADER_HEIGHT,
            bg=SETTINGS_WINDOW_BACKGROUND,
            bd=0,
            highlightthickness=0,
        )
        header_canvas.place(
            x=SETTINGS_HEADER_X,
            y=SETTINGS_HEADER_Y,
            width=SETTINGS_HEADER_WIDTH,
            height=SETTINGS_HEADER_HEIGHT,
        )

        header_photo = self._render_text_image(
            "SETTINGS",
            SETTINGS_HEADER_FONT_SIZE,
            SETTINGS_HEADER_WIDTH,
            SETTINGS_HEADER_HEIGHT,
        )
        if header_photo is not None:
            header_canvas._header_photo = header_photo  # type: ignore[attr-defined]
            header_canvas.create_image(
                SETTINGS_HEADER_WIDTH // 2,
                SETTINGS_HEADER_HEIGHT // 2,
                image=header_photo,
            )
        else:
            header_canvas.create_text(
                SETTINGS_HEADER_WIDTH // 2,
                SETTINGS_HEADER_HEIGHT // 2,
                text="Settings",
                font=(self._ui_font_family, 16, "bold"),
                fill=HEADER_TEXT_COLOR,
            )

        notification_panel = tk.Frame(
            self.window,
            bg=SETTINGS_PANEL_BACKGROUND,
            highlightbackground=SETTINGS_PANEL_BORDER,
            highlightthickness=2,
            bd=0,
        )
        notification_panel.place(
            x=SETTINGS_PANEL_X,
            y=SETTINGS_NOTIFICATION_PANEL_Y,
            width=SETTINGS_PANEL_WIDTH,
            height=SETTINGS_NOTIFICATION_PANEL_HEIGHT,
        )
        self._notification_panel = notification_panel

        hotkey_panel = tk.Frame(
            self.window,
            bg=SETTINGS_PANEL_BACKGROUND,
            highlightbackground=SETTINGS_PANEL_BORDER,
            highlightthickness=2,
            bd=0,
        )
        hotkey_panel.place(
            x=SETTINGS_PANEL_X,
            y=SETTINGS_HOTKEY_PANEL_Y,
            width=SETTINGS_PANEL_WIDTH,
            height=SETTINGS_HOTKEY_PANEL_HEIGHT,
        )
        self._hotkey_panel = hotkey_panel

        self._build_notification_panel()
        self._build_hotkey_panel()

        self._save_button = ttk.Button(self.window, text="Save", command=self._save_settings)
        self._cancel_button = ttk.Button(self.window, text="Cancel", command=self.close)
        self._uninstall_button = ttk.Button(
            self.window,
            text="Uninstall App",
            command=lambda: self._confirm_and_uninstall(self.window),
        )
        self._refresh_notification_panel_layout()

        self.window.bind("<KeyPress>", self._capture_hotkey)

    def _build_notification_panel(self) -> None:
        notification_title_canvas = tk.Canvas(
            self._notification_panel,
            width=260,
            height=28,
            bg=SETTINGS_PANEL_BACKGROUND,
            bd=0,
            highlightthickness=0,
        )
        notification_title_canvas.place(x=18, y=14)
        notification_title_photo = self._render_text_image("NOTIFICATIONS", 18, 260, 28, align="left")
        if notification_title_photo is not None:
            notification_title_canvas._title_photo = notification_title_photo  # type: ignore[attr-defined]
            notification_title_canvas.create_image(0, 0, image=notification_title_photo, anchor="nw")
        else:
            notification_title_canvas.create_text(
                0,
                0,
                text="Notifications",
                font=(self._ui_font_family, 15, "bold"),
                fill=HEADER_TEXT_COLOR,
                anchor="nw",
            )

        tk.Label(
            self._notification_panel,
            text="Desktop reminders for your current habit.",
            font=(self._ui_font_family, 10),
            bg=SETTINGS_PANEL_BACKGROUND,
            fg="#5f5546",
        ).place(x=18, y=48)

        enabled_check = tk.Checkbutton(
            self._notification_panel,
            text="Enable desktop reminders",
            variable=self._enabled_var,
            command=self._handle_notifications_enabled_toggle,
            bg=SETTINGS_PANEL_BACKGROUND,
            fg=HEADER_TEXT_COLOR,
            activebackground=SETTINGS_PANEL_BACKGROUND,
            selectcolor=SETTINGS_PANEL_BACKGROUND,
            font=(self._ui_font_family, 11),
        )
        enabled_check.place(x=18, y=80)

        startup_check = tk.Checkbutton(
            self._notification_panel,
            text="Run at Windows startup",
            variable=self._startup_enabled_var,
            bg=SETTINGS_PANEL_BACKGROUND,
            fg=HEADER_TEXT_COLOR,
            activebackground=SETTINGS_PANEL_BACKGROUND,
            selectcolor=SETTINGS_PANEL_BACKGROUND,
            font=(self._ui_font_family, 11),
        )
        startup_check.place(x=332, y=80)

        tk.Label(
            self._notification_panel,
            text="Reminder times (HH:MM)",
            font=(self._ui_font_family, 11, "bold"),
            bg=SETTINGS_PANEL_BACKGROUND,
            fg=HEADER_TEXT_COLOR,
        ).place(x=18, y=126)

        self._notification_editor = NotificationSettingsEditor(
            parent=self._notification_panel,
            enabled_var=self._enabled_var,
            ui_font_family=self._ui_font_family,
            initial_times=self._initial_times,
            on_layout_changed=self._refresh_notification_panel_layout,
        )

        self._message_label = tk.Label(
            self._notification_panel,
            text="Notification message",
            font=(self._ui_font_family, 11, "bold"),
            bg=SETTINGS_PANEL_BACKGROUND,
            fg=HEADER_TEXT_COLOR,
        )

        self._message_hint = tk.Label(
            self._notification_panel,
            text="Use {habit} to insert the current habit text.",
            font=(self._ui_font_family, 9),
            bg=SETTINGS_PANEL_BACKGROUND,
            fg="#5f5546",
            justify="left",
        )

        self._message_box_frame = tk.Frame(
            self._notification_panel,
            bg="#f6f0e4",
            highlightbackground=SETTINGS_PANEL_BORDER,
            highlightthickness=1,
            bd=0,
        )

        self._message_text = tk.Text(
            self._message_box_frame,
            width=30,
            height=4,
            wrap="word",
            font=(self._ui_font_family, 10),
            bg="#f6f0e4",
            fg=HEADER_TEXT_COLOR,
            insertbackground=HEADER_TEXT_COLOR,
            relief="flat",
            bd=0,
        )
        message_scrollbar = tk.Scrollbar(self._message_box_frame, orient="vertical", command=self._message_text.yview)
        self._message_text.configure(yscrollcommand=message_scrollbar.set)
        self._message_text.place(x=8, y=8, relwidth=1.0, width=-24, relheight=1.0, height=-16)
        message_scrollbar.place(relx=1.0, x=-14, y=8, width=10, relheight=1.0, height=-16)
        self._message_text.insert("1.0", self.habit_data.notifications.message_template)
        self._refresh_notification_panel_layout()

    def _build_hotkey_panel(self) -> None:
        hotkey_title_canvas = tk.Canvas(
            self._hotkey_panel,
            width=340,
            height=28,
            bg=SETTINGS_PANEL_BACKGROUND,
            bd=0,
            highlightthickness=0,
        )
        hotkey_title_canvas.place(x=16, y=14)
        hotkey_title_photo = self._render_text_image("KEYBOARD NAVIGATION", 18, 340, 28, align="left")
        if hotkey_title_photo is not None:
            hotkey_title_canvas._title_photo = hotkey_title_photo  # type: ignore[attr-defined]
            hotkey_title_canvas.create_image(0, 0, image=hotkey_title_photo, anchor="nw")
        else:
            hotkey_title_canvas.create_text(
                0,
                0,
                text="Keyboard Navigation",
                font=(self._ui_font_family, 15, "bold"),
                fill=HEADER_TEXT_COLOR,
                anchor="nw",
            )

        self._hotkey_editor = HotkeySettingsEditor(
            parent=self._hotkey_panel,
            ui_font_family=self._ui_font_family,
            hotkey_values={
                "previous_month": self.habit_data.hotkeys.previous_month,
                "next_month": self.habit_data.hotkeys.next_month,
                "previous_year": self.habit_data.hotkeys.previous_year,
                "next_year": self.habit_data.hotkeys.next_year,
                "current_month": self.habit_data.hotkeys.current_month,
            },
            normalize_keysym=self.habit_data.hotkeys.normalize_keysym,
        )

    def _refresh_notification_panel_layout(self) -> None:
        if self._notification_editor is None:
            return

        right_column_x = 374
        right_column_width = SETTINGS_PANEL_WIDTH - right_column_x - 18
        message_label_y = 126
        message_hint_y = message_label_y + 24
        message_box_y = message_hint_y + 22
        message_box_height = max(106, self._notification_editor.get_bottom_y() - message_box_y)

        if self._message_label is not None:
            self._message_label.place_configure(x=right_column_x, y=message_label_y)
        if self._message_hint is not None:
            self._message_hint.configure(wraplength=right_column_width)
            self._message_hint.place_configure(x=right_column_x, y=message_hint_y)
        if self._message_box_frame is not None:
            self._message_box_frame.place(x=right_column_x, y=message_box_y, width=right_column_width, height=message_box_height)

        left_column_bottom = self._notification_editor.get_bottom_y()
        right_column_bottom = message_box_y + message_box_height
        notification_panel_height = max(left_column_bottom, right_column_bottom) + 18
        self._notification_panel.place_configure(height=notification_panel_height)

        hotkey_y = SETTINGS_NOTIFICATION_PANEL_Y + notification_panel_height + 18
        self._hotkey_panel.place_configure(y=hotkey_y)

        button_row_y = hotkey_y + SETTINGS_HOTKEY_PANEL_HEIGHT + 20
        if self._uninstall_button is not None:
            self._uninstall_button.place(x=24, y=button_row_y, width=138)
        if self._save_button is not None:
            self._save_button.place(x=SETTINGS_WINDOW_WIDTH - 120, y=button_row_y, width=90)
        if self._cancel_button is not None:
            self._cancel_button.place(x=SETTINGS_WINDOW_WIDTH - 220, y=button_row_y, width=90)

        dialog_height = button_row_y + 58
        self.window.geometry(f"{SETTINGS_WINDOW_WIDTH}x{dialog_height}")
        self.window.minsize(SETTINGS_WINDOW_MIN_WIDTH, dialog_height)

    def _capture_hotkey(self, event: tk.Event) -> str | None:
        if self._hotkey_editor is None:
            return None
        return self._hotkey_editor.handle_keypress(event)

    def _handle_notifications_enabled_toggle(self) -> None:
        if self._notification_editor is not None:
            self._notification_editor.refresh_layout()
        self._refresh_notification_panel_layout()

    def _build_settings_draft(self) -> _SettingsDraft:
        """Collect settings values before validation and saving."""
        active_times = self._notification_editor.get_reminder_times() if self._notification_editor is not None else []
        message_template = self._message_text.get("1.0", tk.END).strip() if self._message_text is not None else ""
        hotkey_values = self._hotkey_editor.get_hotkeys() if self._hotkey_editor is not None else {}
        return _SettingsDraft(
            notifications_enabled=bool(self._enabled_var.get()),
            reminder_times=active_times,
            message_template=message_template,
            startup_enabled=bool(self._startup_enabled_var.get()),
            hotkeys=hotkey_values,
        )

    def _apply_settings_draft(self, target: HabitData, draft: _SettingsDraft) -> None:
        target.notifications.set_times(draft.reminder_times)
        target.notifications.set_message_template(draft.message_template)
        target.startup_enabled = draft.startup_enabled
        if draft.notifications_enabled:
            target.notifications.enable()
        else:
            target.notifications.disable()
        for action_name, value in draft.hotkeys.items():
            target.hotkeys.update_binding(action_name, value)

    def _save_settings(self) -> None:
        """Validate, save, and apply settings using a draft copy first."""
        try:
            draft = self._build_settings_draft()
            draft_habit_data = self.habit_data.copy()
            self._apply_settings_draft(draft_habit_data, draft)
            self.storage_manager.save(draft_habit_data)
            self._apply_settings_draft(self.habit_data, draft)
            self._apply_hotkey_bindings()
            self._apply_startup_preference()

            if draft.notifications_enabled and not self.notification_service.is_available:
                messagebox.showinfo(
                    "Plyer Not Available",
                    "Plyer is not installed, so notifications will be skipped until it is available.",
                    parent=self.window,
                )

            self.close()
        except ValueError as error:
            messagebox.showerror("Invalid Time", str(error), parent=self.window)
        except StorageError as error:
            messagebox.showerror("Save Failed", str(error), parent=self.window)
