"""Expose public Cozy Library classes and helpers."""

from .date_service import DateService
from .drawable import Drawable, VisualElement
from .exceptions import AssetLoadError, ImportValidationError, StorageError, ValidationError
from .layout import BookSlot, LayoutManager, MonthLayoutConfig
from .main_window import MainWindow
from .models import HabitData, HotkeySettings, NotificationSettings
from .notification_service import NotificationService
from .path_utils import get_downloads_dir, get_runtime_data_dir, get_runtime_data_path, resource_path
from .shelf_view import ShelfView
from .sprites import BookSprite, DayNumberOverlay, ShelfBackground, WindowBackground
from .startup_service import StartupService
from .statistics_window import StatisticsWindow
from .storage import StorageManager
from .tray_service import TrayService
from .uninstall_service import UninstallService

__all__ = [
    "AssetLoadError",
    "BookSlot",
    "BookSprite",
    "DateService",
    "DayNumberOverlay",
    "Drawable",
    "HabitData",
    "HotkeySettings",
    "ImportValidationError",
    "LayoutManager",
    "MainWindow",
    "MonthLayoutConfig",
    "NotificationService",
    "NotificationSettings",
    "get_downloads_dir",
    "get_runtime_data_dir",
    "get_runtime_data_path",
    "resource_path",
    "ShelfView",
    "ShelfBackground",
    "StorageManager",
    "StorageError",
    "StartupService",
    "StatisticsWindow",
    "TrayService",
    "UninstallService",
    "ValidationError",
    "VisualElement",
    "WindowBackground",
]
