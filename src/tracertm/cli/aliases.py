"""Command aliases for TraceRTM CLI."""
from __future__ import annotations

ALIASES: dict[str, str] = {}


def get_aliases_for_command(cmd: str) -> list[str]:
    """Return all aliases that resolve to the given command."""
    return [alias for alias, target in ALIASES.items() if target == cmd]


def resolve_alias(alias: str) -> str:
    """Resolve an alias to the canonical command name."""
    return ALIASES.get(alias, alias)
