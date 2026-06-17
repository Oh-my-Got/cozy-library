"""Define the storage backend interface for Cozy Library.

Provides the interface-like contract used by runtime persistence backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import HabitData


class StorageBackend(ABC):
    """Interface-like base class for habit data storage backends."""

    @abstractmethod
    def load(self) -> HabitData:
        """Load habit data from the backend."""

    @abstractmethod
    def save(self, habit_data: HabitData) -> None:
        """Save habit data to the backend."""

    @abstractmethod
    def reset_data(self) -> HabitData:
        """Replace stored data with a default state and return it."""

    @abstractmethod
    def exists(self) -> bool:
        """Return whether the backend storage already exists."""
