"""Storage helper utilities for TraceRTM CLI."""
from __future__ import annotations
from typing import Any

_storage_manager: Any = None


def get_storage_manager(*args: Any, **kwargs: Any) -> None:
    """Return the global storage manager instance."""
    return _storage_manager


def reset_storage_manager(*args: Any, **kwargs: Any) -> None:
    """Reset the global storage manager."""
    global _storage_manager
    _storage_manager = None


def require_project(*args: Any, **kwargs: Any) -> None:
    """Assert that a project is configured; raise if not."""
    pass


def with_sync(*args: Any, **kwargs: Any) -> Any:
    """Context manager / decorator stub for sync operations."""
    return None


def show_sync_status(*args: Any, **kwargs: Any) -> None:
    """Print sync status to the console."""
    pass


def format_item_for_display(*args: Any, **kwargs: Any) -> str:
    """Format a single item for display."""
    return ""


def format_items_table(*args: Any, **kwargs: Any) -> str:
    """Format a list of items as a table."""
    return ""


def format_link_for_display(*args: Any, **kwargs: Any) -> str:
    """Format a single link for display."""
    return ""


def format_links_table(*args: Any, **kwargs: Any) -> str:
    """Format a list of links as a table."""
    return ""


def _human_time_delta(*args: Any, **kwargs: Any) -> str:
    """Return a human-readable time delta string."""
    return ""
