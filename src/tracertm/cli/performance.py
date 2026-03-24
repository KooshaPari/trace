"""Performance utilities for TraceRTM CLI."""
from __future__ import annotations
from typing import Any


class CommandCache:
    """Stub cache for CLI command results."""

    def get(self, key: str) -> Any:
        return None

    def set(self, key: str, value: Any) -> None:
        pass

    def clear(self) -> None:
        pass


class LazyLoader:
    """Stub lazy loader for CLI modules."""

    def load(self, module: str) -> Any:
        return None


class PerformanceMonitor:
    """Stub performance monitor."""

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def report(self) -> dict[str, Any]:
        return {}


def get_loader() -> None:
    """Return the global lazy loader instance."""
    return None
