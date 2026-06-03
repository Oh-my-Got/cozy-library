"""Manage the Cozy Library system tray icon.

Starts, stops, and handles tray menu callbacks when pystray is available.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

try:
    import pystray
except ImportError:  # pragma: no cover - depends on local environment
    pystray = None

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover - depends on local environment
    Image = None
    ImageDraw = None


class TrayService:
    """Manage tray icon lifecycle and menu callbacks."""

    def __init__(
        self,
        *,
        icon_path: Path,
        on_open: Callable[[], None],
        on_exit: Callable[[], None],
        tooltip: str = "Cozy Library",
    ) -> None:
        self._icon_path = Path(icon_path)
        self._on_open = on_open
        self._on_exit = on_exit
        self._tooltip = tooltip
        self._icon = None
        self._is_running = False
        self._last_error: str | None = None

    @property
    def is_available(self) -> bool:
        return pystray is not None and Image is not None

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def start(self) -> bool:
        """Start the tray icon in detached mode when the backend is available."""
        if self._is_running:
            return False

        if not self.is_available:
            missing_parts: list[str] = []
            if pystray is None:
                missing_parts.append("pystray")
            if Image is None:
                missing_parts.append("Pillow.Image")
            if ImageDraw is None:
                missing_parts.append("Pillow.ImageDraw")

            if not missing_parts:
                missing_parts.append("unknown tray dependency")
            self._last_error = f"Tray dependencies unavailable: {', '.join(missing_parts)}."
            return False

        image = self._load_icon_image()
        if image is None:
            self._last_error = "No tray icon image could be loaded."
            return False

        try:
            menu = pystray.Menu(
                pystray.MenuItem("Open Cozy Library", self._handle_open, default=True),
                pystray.MenuItem("Exit", self._handle_exit),
            )
            self._icon = pystray.Icon("cozy_library", image, self._tooltip, menu)
            self._icon.run_detached()
            self._is_running = True
            self._last_error = None
            return True
        except Exception as error:  # pragma: no cover - backend/platform dependent
            self._icon = None
            self._is_running = False
            self._last_error = f"Tray start failed: {error!r}"
            return False

    def stop(self) -> None:
        """Stop and dispose of the tray icon."""
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass
        self._icon = None
        self._is_running = False

    def _handle_open(self, icon, item) -> None:  # pragma: no cover - callback owned by pystray
        self._on_open()

    def _handle_exit(self, icon, item) -> None:  # pragma: no cover - callback owned by pystray
        self._on_exit()

    def _load_icon_image(self):
        """Load the tray icon image or build a fallback icon."""
        if Image is None:
            self._last_error = "Pillow Image module is unavailable."
            return None

        if self._icon_path.exists():
            try:
                with Image.open(self._icon_path) as image:
                    return image.copy()
            except OSError:
                pass

        return self._build_fallback_icon()

    def _build_fallback_icon(self):
        """Create a simple tray icon when the bundled image is unavailable."""
        if Image is None or ImageDraw is None:
            self._last_error = "Pillow drawing support is unavailable."
            return None

        image = Image.new("RGBA", (64, 64), "#efe6d5")
        draw = ImageDraw.Draw(image)
        draw.rectangle((10, 12, 54, 52), fill="#7a4d27", outline="#44210d", width=3)
        draw.rectangle((16, 22, 48, 28), fill="#c68b53", outline="#44210d", width=2)
        draw.rectangle((16, 36, 48, 42), fill="#c68b53", outline="#44210d", width=2)
        draw.rectangle((22, 18, 30, 46), fill="#6f8fbf", outline="#2d4667", width=2)
        draw.rectangle((32, 20, 40, 44), fill="#81a65e", outline="#3c5630", width=2)
        return image
