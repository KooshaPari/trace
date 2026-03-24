"""Error classes for TraceRTM CLI."""
from __future__ import annotations


class TraceRTMError(Exception):
    """Base error class for TraceRTM."""

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)


class ConfigurationError(TraceRTMError):
    """Raised when configuration is invalid or missing."""


class DatabaseConnectionError(TraceRTMError):
    """Raised when a database connection fails."""


class DiskSpaceError(TraceRTMError):
    """Raised when there is insufficient disk space."""


class NetworkError(TraceRTMError):
    """Raised when a network operation fails."""


class PermissionError(TraceRTMError):
    """Raised when a permission check fails."""


class ProjectNotFoundError(TraceRTMError):
    """Raised when a project cannot be found."""


def format_validation_error(error: Exception) -> str:
    """Format a validation error into a user-friendly string."""
    return str(error)


def handle_error(error: Exception) -> None:
    """Handle an error by printing a user-friendly message."""
    print(f"Error: {error}")
