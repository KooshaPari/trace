"""Query and test management MCP tools."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

try:
    from tracertm.mcp.core import mcp
except ImportError:

    class _StubMCP:
        def tool(self, *_args: object, **_kwargs: object) -> object:
            def decorator(fn: object) -> object:
                return fn

            return decorator

    mcp: Any = _StubMCP()  # type: ignore[no-redef]

from fastmcp.exceptions import ToolError

from .common import _wrap

try:
    from tracertm.cli.commands.saved_queries import load_saved_queries, save_queries
except ImportError:
    load_saved_queries = save_queries = None


@mcp.tool(description="Unified saved query operations")
async def saved_query_manage(
    action: str,
    payload: dict[str, object] | None = None,
    ctx: object | None = None,
) -> dict[str, object]:
    """Unified saved query management tool.

    Actions:
    - list: List all saved queries
    - save: Save a query
    - get: Get a saved query
    - delete: Delete a saved query
    """
    await asyncio.sleep(0)
    payload = payload or {}
    action = action.lower()

    if load_saved_queries is None or save_queries is None:
        msg = "Saved queries are not available in this environment."
        raise ToolError(msg)

    if action == "list":
        return _wrap({"queries": load_saved_queries()}, ctx, action)

    if action == "save":
        name = payload.get("name")
        if not name:
            msg = "name is required."
            raise ToolError(msg)
        queries = load_saved_queries()
        query_def = {
            "filter": payload.get("filter"),
            "view": payload.get("view"),
            "status": payload.get("status"),
            "query": payload.get("query"),
        }
        query_def = {k: v for k, v in query_def.items() if v is not None}
        queries[name] = query_def
        save_queries(queries)
        return _wrap({"saved": name, "query": query_def}, ctx, action)

    if action == "delete":
        name = payload.get("name")
        if not name:
            msg = "name is required."
            raise ToolError(msg)
        queries = load_saved_queries()
        if name in queries:
            del queries[name]
            save_queries(queries)
        return _wrap({"deleted": name}, ctx, action)

    if action == "get":
        name = payload.get("name")
        if not name:
            msg = "name is required."
            raise ToolError(msg)
        queries = load_saved_queries()
        return _wrap({"name": name, "query": queries.get(name)}, ctx, action)

    msg = f"Unknown saved-queries action: {action}"
    raise ToolError(msg)


async def _saved_queries_manage(
    action: str,
    payload: dict[str, object] | None = None,
    ctx: object | None = None,
) -> dict[str, object]:
    return await saved_query_manage(action, payload, ctx)


@mcp.tool(description="Unified test operations")
async def test_manage(
    action: str,
    payload: dict[str, object] | None = None,
    ctx: object | None = None,
) -> dict[str, object]:
    """Unified test management tool.

    Actions:
    - discover: Discover tests in project
    - run: Run tests
    """
    await asyncio.sleep(0)
    payload = payload or {}
    action = action.lower()

    try:
        from tracertm.cli.commands.test.discovery import TestDiscovery
        from tracertm.cli.commands.test.runner import TestRunner
    except ImportError as err:
        msg = "Test module is not available in this environment."
        raise ToolError(msg) from err

    if action == "discover":
        scope = payload.get("scope", "all")
        language = payload.get("language")
        languages = [language] if language else None
        tests = TestDiscovery(Path.cwd()).discover(languages=languages, scope=scope)
        return _wrap(
            {
                "count": len(tests),
                "tests": [
                    {
                        "path": test.path,
                        "language": test.language,
                        "package": test.package,
                    }
                    for test in tests
                ],
            },
            ctx,
            action,
        )

    if action == "run":
        language = payload.get("language", "python")
        scope = payload.get("scope", "all")
        tests = TestDiscovery(Path.cwd()).discover(languages=[language], scope=scope)
        runner = TestRunner()
        results = [runner.run_test(test) for test in tests]
        return _wrap(
            {
                "results": [
                    {
                        "path": result.test_file.path,
                        "language": result.test_file.language,
                        "passed": result.passed,
                        "duration_ms": result.duration_ms,
                        "output": result.output,
                    }
                    for result in results
                ],
            },
            ctx,
            action,
        )

    msg = f"Unknown test action: {action}"
    raise ToolError(msg)


__all__ = ["_saved_queries_manage", "saved_query_manage", "test_manage"]
