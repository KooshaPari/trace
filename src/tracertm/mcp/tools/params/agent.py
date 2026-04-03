"""Agent and progress management MCP tools."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

try:
    from tracertm.mcp.core import mcp
except Exception:

    class _StubMCP:
        def tool(self, *_args: object, **_kwargs: object) -> object:
            def decorator(fn: object) -> object:
                return fn

            return decorator

    mcp: Any = _StubMCP()  # type: ignore[no-redef]

from fastmcp.exceptions import ToolError

from tracertm.models.agent import Agent
from tracertm.models.event import Event
from tracertm.models.item import Item
from tracertm.services.progress_service import ProgressService
from tracertm.storage.local_storage import LocalStorageManager

from .common import _parse_since, _wrap

HOURS_IDLE_THRESHOLD = 24


async def _agents_list_impl(
    project_id: str, ctx: object | None
) -> dict[str, object]:
    storage = LocalStorageManager()
    with storage.get_session() as session:
        agents = session.query(Agent).filter(Agent.project_id == project_id).all()
        return _wrap(
            {
                "agents": [
                    {
                        "id": str(agent.id),
                        "name": agent.name,
                        "type": agent.agent_type,
                        "status": agent.status,
                        "last_activity_at": agent.last_activity_at,
                    }
                    for agent in agents
                ],
            },
            ctx,
            "list",
        )


async def _agents_activity_impl(
    project_id: str, payload: dict[str, object], ctx: object | None
) -> dict[str, object]:
    storage = LocalStorageManager()
    with storage.get_session() as session:
        agent_id = payload.get("agent_id")
        since_date = _parse_since(payload.get("since"))
        limit = int(payload.get("limit", 50))

        query = session.query(Event).filter(Event.project_id == project_id)
        if agent_id:
            query = query.filter(Event.agent_id == agent_id)
        if since_date:
            query = query.filter(Event.created_at >= since_date)
        events = query.order_by(Event.created_at.desc()).limit(limit).all()

        return _wrap(
            {
                "events": [
                    {
                        "id": str(event.id),
                        "agent_id": event.agent_id,
                        "event_type": event.event_type,
                        "entity_type": event.entity_type,
                        "entity_id": event.entity_id,
                        "created_at": event.created_at.isoformat() if event.created_at else None,
                        "data": event.data,
                    }
                    for event in events
                ],
            },
            ctx,
            "activity",
        )


async def _agents_metrics_impl(
    project_id: str, payload: dict[str, object], ctx: object | None
) -> dict[str, object]:
    storage = LocalStorageManager()
    with storage.get_session() as session:
        agent_id = payload.get("agent_id")
        since_date = _parse_since(payload.get("since")) or datetime.now(UTC) - timedelta(hours=24)
        query = session.query(Event).filter(
            Event.project_id == project_id,
            Event.created_at >= since_date,
        )
        if agent_id:
            agent_ids = [agent_id]
        else:
            agent_ids = [a.id for a in session.query(Agent).filter(Agent.project_id == project_id).all()]

        metrics_list = []
        for aid in agent_ids:
            agent_events = query.filter(Event.agent_id == aid).all()
            if not agent_events:
                continue
            total_ops = len(agent_events)
            successful_ops = sum(1 for e in agent_events if e.event_type != "conflict_detected")
            conflicts = sum(1 for e in agent_events if e.event_type == "conflict_detected")
            hours_float = (datetime.now(UTC) - since_date).total_seconds() / 3600
            ops_per_hour = total_ops / hours_float if hours_float > 0 else 0
            success_rate = (successful_ops / total_ops * 100) if total_ops else 0
            conflict_rate = (conflicts / total_ops * 100) if total_ops else 0
            agent = session.query(Agent).filter(Agent.id == aid).first()
            metrics_list.append({
                "agent_id": str(aid),
                "agent_name": agent.name if agent else str(aid)[:8],
                "total_operations": total_ops,
                "operations_per_hour": round(ops_per_hour, 2),
                "success_rate": round(success_rate, 2),
                "conflict_rate": round(conflict_rate, 2),
                "conflicts": conflicts,
            })

        return _wrap({"metrics": metrics_list}, ctx, "metrics")


async def _agents_workload_impl(
    project_id: str, payload: dict[str, object], ctx: object | None
) -> dict[str, object]:
    storage = LocalStorageManager()
    with storage.get_session() as session:
        agent_id = payload.get("agent_id")
        if agent_id:
            agent_result = session.query(Agent).filter(Agent.id == agent_id).first()
            agents = [agent_result] if agent_result else []
        else:
            agents = session.query(Agent).filter(Agent.project_id == project_id).all()
        workloads = []
        for agent in agents:
            items = (
                session
                .query(Item)
                .filter(Item.project_id == project_id)
                .filter(Item.owner == str(agent.id))
                .filter(Item.deleted_at.is_(None))
                .all()
            )
            status_counts: dict[str, int] = {}
            for item in items:
                status_counts[item.status] = status_counts.get(item.status, 0) + 1
            workloads.append({
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "todo": status_counts.get("todo", 0),
                "in_progress": status_counts.get("in_progress", 0),
                "blocked": status_counts.get("blocked", 0),
                "total": len(items),
            })
        return _wrap({"workloads": workloads}, ctx, "workload")


async def _agents_health_impl(
    project_id: str, payload: dict[str, object], ctx: object | None
) -> dict[str, object]:
    storage = LocalStorageManager()
    with storage.get_session() as session:
        agent_id = payload.get("agent_id")
        if agent_id:
            agent_result = session.query(Agent).filter(Agent.id == agent_id).first()
            agents = [agent_result] if agent_result else []
        else:
            agents = session.query(Agent).filter(Agent.project_id == project_id).all()
        healths = []
        for agent in agents:
            health = "unknown"
            if agent.last_activity_at:
                try:
                    last_activity = datetime.fromisoformat(agent.last_activity_at)
                    hours_since = (datetime.now(UTC) - last_activity.replace(tzinfo=None)).total_seconds() / 3600
                    if hours_since < 1:
                        health = "healthy"
                    elif hours_since < HOURS_IDLE_THRESHOLD:
                        health = "idle"
                    else:
                        health = "stale"
                except (TypeError, ValueError):
                    health = "unknown"
            else:
                health = "no_activity"
            healths.append({
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "status": agent.status or "active",
                "last_activity_at": agent.last_activity_at,
                "health": health,
            })
        return _wrap({"health": healths}, ctx, "health")


@mcp.tool(description="Unified agent operations")
async def agent_manage(
    action: str,
    payload: dict[str, object] | None = None,
    ctx: object | None = None,
) -> dict[str, object]:
    """Unified agent management tool.

    Actions:
    - list: List all agents in project
    - activity: Get agent activity events
    - metrics: Get agent metrics
    - workload: Get agent workload distribution
    - health: Get agent health status
    """
    await asyncio.sleep(0)
    payload = payload or {}
    action = action.lower()
    config = _get_config()
    project_id_obj = payload.get("project_id")
    if project_id_obj:
        project_id = str(project_id_obj)
    elif config.get("current_project_id"):
        project_id = str(config.get("current_project_id"))
    else:
        project_id = None
    if not project_id:
        msg = "project_id is required."
        raise ToolError(msg)

    if action == "list":
        return await _agents_list_impl(project_id, ctx)
    if action == "activity":
        return await _agents_activity_impl(project_id, payload, ctx)
    if action == "metrics":
        return await _agents_metrics_impl(project_id, payload, ctx)
    if action == "workload":
        return await _agents_workload_impl(project_id, payload, ctx)
    if action == "health":
        return await _agents_health_impl(project_id, payload, ctx)

    msg = f"Unknown agents action: {action}"
    raise ToolError(msg)


@mcp.tool(description="Unified progress operations")
async def progress_manage(
    action: str,
    payload: dict[str, object] | None = None,
    ctx: object | None = None,
) -> dict[str, object]:
    """Unified progress management tool.

    Actions:
    - show: Show progress for item or view
    - blocked: List blocked items
    - stalled: List stalled items
    - velocity: Calculate velocity
    - report: Generate progress report
    """
    await asyncio.sleep(0)
    payload = payload or {}
    action = action.lower()
    config = _get_config()
    project_id_obj = payload.get("project_id")
    if project_id_obj:
        project_id = str(project_id_obj)
    elif config.get("current_project_id"):
        project_id = str(config.get("current_project_id"))
    else:
        project_id = None
    if not project_id:
        msg = "project_id is required."
        raise ToolError(msg)

    storage = LocalStorageManager()
    with storage.get_session() as session:
        service = ProgressService(session)
        if action == "show":
            item_id = payload.get("item_id")
            view = payload.get("view")
            if item_id:
                item = session.query(Item).filter(Item.id.like(f"{item_id}%"), Item.project_id == project_id).first()
                if not item:
                    msg = f"Item not found: {item_id}"
                    raise ToolError(msg)
                completion = service.calculate_completion(str(item.id))
                return _wrap(
                    {
                        "item_id": str(item.id),
                        "title": item.title,
                        "status": item.status,
                        "completion": completion,
                    },
                    ctx,
                    action,
                )
            if view:
                items = (
                    session
                    .query(Item)
                    .filter(
                        Item.project_id == project_id,
                        Item.view == view.upper(),
                        Item.deleted_at.is_(None),
                    )
                    .all()
                )
                avg_completion = (
                    sum(service.calculate_completion(str(item.id)) for item in items) / len(items) if items else 0
                )
                return _wrap(
                    {"view": view, "items": len(items), "average_completion": avg_completion},
                    ctx,
                    action,
                )
            items = session.query(Item).filter(Item.project_id == project_id, Item.deleted_at.is_(None)).all()
            avg_completion = (
                sum(service.calculate_completion(str(item.id)) for item in items) / len(items) if items else 0
            )
            return _wrap({"items": len(items), "average_completion": avg_completion}, ctx, action)

        if action == "blocked":
            limit = int(payload.get("limit", 50))
            blocked = service.get_blocked_items(project_id)
            return _wrap({"blocked": blocked[:limit]}, ctx, action)

        if action == "stalled":
            days = int(payload.get("days", 7))
            limit = int(payload.get("limit", 50))
            stalled = service.get_stalled_items(project_id, days)
            return _wrap({"stalled": stalled[:limit]}, ctx, action)

        if action == "velocity":
            days = int(payload.get("days", 7))
            velocity = service.calculate_velocity(project_id, days)
            return _wrap(velocity, ctx, action)

        if action == "report":
            days = int(payload.get("days", 30))
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=days)
            report = service.generate_progress_report(project_id, start_date, end_date)
            return _wrap(report, ctx, action)

    msg = f"Unknown progress action: {action}"
    raise ToolError(msg)


def _get_config() -> Any:
    from tracertm.config.manager import ConfigManager
    return ConfigManager()


__all__ = ["agent_manage", "progress_manage"]
