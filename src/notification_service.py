"""Send desktop reminders for Cozy Library.

Checks reminder settings and uses available Plyer notification backends.
"""

from __future__ import annotations

from .date_service import DateService
from .models import HabitData

try:
    from plyer import notification as plyer_notification
except ImportError:  # pragma: no cover - depends on local environment
    plyer_notification = None

try:
    from plyer.platforms.win.notification import instance as plyer_windows_notification_instance
except ImportError:  # pragma: no cover - depends on local environment
    plyer_windows_notification_instance = None


class NotificationService:
    """Check reminder rules and send desktop notifications when possible."""

    def __init__(self, date_service: DateService | None = None) -> None:
        self._date_service = date_service or DateService()
        self._last_status_message = ""
        self._last_sent_slot: str | None = None
        self._last_attempt_slot: str | None = None

    @property
    def last_status_message(self) -> str:
        return self._last_status_message

    @property
    def is_available(self) -> bool:
        return plyer_notification is not None or plyer_windows_notification_instance is not None

    def check_and_send(self, habit_data: HabitData) -> bool:
        """Send a reminder if enabled and one of the configured times matches the current minute."""
        current_datetime = self._date_service.now()
        settings = habit_data.notifications
        current_slot = current_datetime.strftime("%Y-%m-%d %H:%M")

        if not settings.enabled:
            self._last_status_message = "Notifications are disabled."
            return False

        if not settings.should_send_now(current_datetime):
            self._last_status_message = "No notification is due right now."
            return False

        if self._last_attempt_slot == current_slot:
            self._last_status_message = "Notification already attempted for this minute."
            return False

        self._last_attempt_slot = current_slot

        title = "Cozy Library"
        description = habit_data.description.strip() or "Remember to complete your habit today."
        message_template = habit_data.notifications.message_template
        try:
            message = message_template.format(habit=description)
        except Exception:
            message = message_template

        sent = self.send_notification(title, message)
        if sent:
            self._last_sent_slot = current_slot
            self._last_status_message = "Notification sent."
            return True

        if plyer_notification is None and plyer_windows_notification_instance is None:
            self._last_status_message = "Notification backend is unavailable. Notification was skipped."
            return False

        self._last_status_message = "Notification could not be sent."
        return False

    def send_notification(self, title: str, message: str) -> bool:
        """Try to send a desktop notification, returning success or failure."""
        try:
            if plyer_notification is not None:
                plyer_notification.notify(
                    title=title,
                    message=message,
                    app_name="Cozy Library",
                    timeout=10,
                )
                return True

            if plyer_windows_notification_instance is not None:
                backend = plyer_windows_notification_instance()
                backend.notify(
                    title=title,
                    message=message,
                    app_name="Cozy Library",
                    timeout=10,
                )
                return True

            return False
        except Exception:
            return False
