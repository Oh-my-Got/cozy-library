"""Define project-specific exceptions.

Supports storage, validation, import, and asset-loading error handling.
"""


class StorageError(Exception):
    """Raised when persistent storage cannot be loaded or saved."""


class ValidationError(Exception):
    """Raised when JSON data does not match the required structure."""


class ImportValidationError(ValidationError):
    """Raised when imported JSON data fails validation."""


class AssetLoadError(Exception):
    """Raised when an image asset cannot be loaded."""
