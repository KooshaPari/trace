"""System tools (benchmark, chaos) MCP tools."""

from __future__ import annotations

import asyncio
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

from tracertm.config.manager import ConfigManager
from tracertm.services.benchmark_service import BenchmarkService
from tracertm.services.chaos_mode_service import ChaosModeService

from .common import _get_async_session, _wrap


@mcp.tool(description="Unified benchmark operations")
async def benchmark_manage(
    action: str,
    payload: dict[str, object] | None = None,
    ctx: object | None = None,
) -> dict[str, object]:
    """Unified benchmark management tool.

    Actions:
    - views: Benchmark all views
    - refresh: Benchmark refresh performance
    - report: Get performance report
    """
    payload = payload or {}
    action = action.lower()
    session = await _get_async_session()
    engine = getattr(session, "_tracertm_engine", None)
    try:
        service = BenchmarkService(session)
        if action == "views":
            results = await service.benchmark_all_views()
            data = [
                {
                    "view_name": r.view_name,
                    "query_time_ms": r.query_time_ms,
                    "target_ms": r.target_ms,
                    "meets_target": r.meets_target,
                    "row_count": r.row_count,
                    "size_bytes": r.size_bytes,
                }
                for r in results
            ]
            return _wrap({"views": data}, ctx, action)
        if action == "refresh":
            incremental = await service.benchmark_refresh_incremental()
            full = await service.benchmark_refresh_full()
            return _wrap(
                {
                    "incremental": {
                        "duration_ms": incremental.duration_ms,
                        "metadata": incremental.metadata,
                    },
                    "full": {
                        "duration_ms": full.duration_ms,
                        "metadata": full.metadata,
                    },
                },
                ctx,
                action,
            )
        if action == "report":
            report = await service.get_performance_report()
            return _wrap(report, ctx, action)
    finally:
        await session.close()
        if engine is not None:
            await engine.dispose()

    msg = f"Unknown benchmark action: {action}"
    raise ToolError(msg)


@mcp.tool(description="Unified chaos operations")
async def chaos_manage(
    action: str,
    payload: dict[str, object] | None = None,
    ctx: object | None = None,
) -> dict[str, object]:
    """Unified chaos management tool.

    Actions:
    - explode: Explode file into items
    - crash: Track scope crash
    - zombies: Detect zombie items
    - snapshot: Create snapshot
    - enable: Enable chaos mode
    - disable: Disable chaos mode
    """
    payload = payload or {}
    action = action.lower()
    project_id_obj = payload.get("project_id")
    project_id = (
        str(project_id_obj)
        if project_id_obj
        else str(ConfigManager().get("current_project_id"))
        if ConfigManager().get("current_project_id")
        else None
    )
    if action in {"explode", "crash", "zombies", "snapshot"} and not project_id:
        msg = "project_id is required."
        raise ToolError(msg)

    session = await _get_async_session()
    engine = getattr(session, "_tracertm_engine", None)
    try:
        service = ChaosModeService(session)
        pid: str = project_id if isinstance(project_id, str) else str(project_id or "")

        if action == "explode":
            file_path = payload.get("path")
            view = payload.get("view", "FEATURE")
            if not file_path:
                msg = "path is required for explode."
                raise ToolError(msg)
            from pathlib import Path as Path_

            def _read_file() -> str:
                return Path_(file_path).read_text(encoding="utf-8")

            content = await asyncio.to_thread(_read_file)
            items_created = await service.explode_file(content, pid, view)
            await session.commit()
            return _wrap({"items_created": items_created}, ctx, action)

        if action == "crash":
            reason = payload.get("reason")
            if not reason:
                msg = "reason is required for crash."
                raise ToolError(msg)
            item_ids = payload.get("item_ids") or []
            result = await service.track_scope_crash(pid, str(reason), item_ids)
            await session.commit()
            return _wrap(result, ctx, action)

        if action == "zombies":
            days_inactive = int(payload.get("days_inactive", 30))
            cleanup = bool(payload.get("cleanup", False))
            result = await service.detect_zombies(pid, days_inactive)
            if cleanup:
                deleted = await service.cleanup_zombies(pid, days_inactive)
                result["deleted"] = deleted
                await session.commit()
            return _wrap(result, ctx, action)

        if action == "snapshot":
            name = payload.get("name")
            description = payload.get("description")
            if not name:
                msg = "name is required for snapshot."
                raise ToolError(msg)
            result = await service.create_snapshot(pid, str(name), description)
            await session.commit()
            return _wrap(result, ctx, action)

        if action == "enable":
            return _wrap({"enabled": True}, ctx, action)
        if action == "disable":
            return _wrap({"enabled": False}, ctx, action)
    finally:
        await session.close()
        if engine is not None:
            await engine.dispose()

    msg = f"Unknown chaos action: {action}"
    raise ToolError(msg)


__all__ = ["benchmark_manage", "chaos_manage"]
