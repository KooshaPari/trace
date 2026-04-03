"""UI and design integration MCP tools."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
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


@mcp.tool(description="Unified TUI operations")
async def tui_manage(
    action: str,
    payload: dict[str, object] | None = None,
    ctx: object | None = None,
) -> dict[str, object]:
    """Unified TUI management tool.

    Actions:
    - list: List available TUI apps
    - launch: Launch a TUI app
    """
    await asyncio.sleep(0)
    payload = payload or {}
    action = action.lower()

    if action == "list":
        return _wrap(
            {
                "apps": [
                    {"name": "dashboard", "command": "rtm tui dashboard"},
                    {"name": "browser", "command": "rtm tui browser"},
                    {"name": "graph", "command": "rtm tui graph"},
                ],
            },
            ctx,
            action,
        )

    if action == "launch":
        app_name = payload.get("app", "dashboard")
        watch = bool(payload.get("watch", False))
        project_path = payload.get("path")
        spawn = bool(payload.get("spawn", False))

        cmd = ["rtm", "tui", app_name]
        if watch:
            cmd.append("--watch")
        if project_path:
            cmd.extend(["--path", project_path])

        if not spawn:
            return _wrap({"command": " ".join(cmd), "spawned": False}, ctx, action)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=Path.cwd(),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        return _wrap({"command": " ".join(cmd), "spawned": True, "pid": proc.pid}, ctx, action)

    msg = f"Unknown tui action: {action}"
    raise ToolError(msg)


@mcp.tool(description="Unified design integration operations")
async def design_manage(
    action: str,
    payload: dict[str, object] | None = None,
    ctx: object | None = None,
) -> dict[str, object]:
    """Unified design management tool.

    Actions:
    - init: Initialize design configuration
    - link: Link component to Figma
    - status: Get design sync status
    - list: List components
    - sync: Sync designs with Figma
    - generate: Generate stories
    - export: Export designs to Figma
    """
    await asyncio.sleep(0)
    payload = payload or {}
    action = action.lower()

    try:
        from tracertm.cli.commands import design as design_module
    except ImportError as err:
        msg = "Design module is not available in this environment."
        raise ToolError(msg) from err

    path = payload.get("path")
    trace_dir = design_module._get_trace_dir(path)

    if action == "init":
        figma_key = payload.get("figma_key", "")
        figma_token = payload.get("figma_token", "")
        designs_config = dict[str, Any](design_module.DESIGNS_YAML_TEMPLATE)
        figma_config = designs_config.get("figma")
        if isinstance(figma_config, dict):
            figma_config["file_key"] = figma_key
            figma_config["access_token"] = figma_token
        design_module._save_designs_config(trace_dir, designs_config)

        components_config = dict[str, Any](design_module.COMPONENTS_YAML_TEMPLATE)
        metadata = components_config.get("metadata")
        if isinstance(metadata, dict):
            metadata["created_at"] = datetime.now(UTC).isoformat()
        design_module._save_components_config(trace_dir, components_config)
        return _wrap({"initialized": True}, ctx, action)

    if action == "link":
        component = payload.get("component")
        figma_url = payload.get("figma_url")
        component_path = payload.get("component_path")
        if not component or not figma_url:
            msg = "component and figma_url are required."
            raise ToolError(msg)
        file_key, node_id = design_module._validate_figma_url(figma_url)
        designs_config = design_module._load_designs_config(trace_dir)
        components_config = design_module._load_components_config(trace_dir)
        if "components" not in designs_config:
            designs_config["components"] = {}
        designs_config["components"][component] = {
            "figma_file_key": file_key,
            "figma_node_id": node_id,
            "figma_url": figma_url,
            "linked_at": datetime.now(UTC).isoformat(),
        }
        design_module._save_designs_config(trace_dir, designs_config)

        components_list = components_config.get("components", [])
        existing_idx = None
        for idx, comp in enumerate(components_list):
            if comp.get("name") == component:
                existing_idx = idx
                break
        component_entry = {
            "name": component,
            "path": component_path or f"src/components/{component}",
            "figma_url": figma_url,
            "figma_node_id": node_id,
            "has_story": False,
            "sync_status": "unsynced",
            "last_synced": None,
        }
        if existing_idx is not None:
            components_list[existing_idx] = component_entry
        else:
            components_list.append(component_entry)
        components_config["components"] = components_list
        design_module._save_components_config(trace_dir, components_config)
        return _wrap({"linked": component, "figma_url": figma_url}, ctx, action)

    if action == "status":
        designs_config = design_module._load_designs_config(trace_dir)
        components_config = design_module._load_components_config(trace_dir)
        figma_config = designs_config.get("figma", {})
        components_list = components_config.get("components", [])
        synced_count = sum(1 for c in components_list if c.get("sync_status") == "synced")
        unsynced_count = sum(1 for c in components_list if c.get("sync_status") == "unsynced")
        with_stories = sum(1 for c in components_list if c.get("has_story"))
        return _wrap(
            {
                "figma_file_key": figma_config.get("file_key"),
                "last_sync": designs_config.get("last_sync"),
                "total_components": len(components_list),
                "synced": synced_count,
                "unsynced": unsynced_count,
                "with_stories": with_stories,
            },
            ctx,
            action,
        )

    if action == "list":
        components_config = design_module._load_components_config(trace_dir)
        components_list = components_config.get("components", [])
        filter_status = payload.get("status")
        if filter_status:
            components_list = [c for c in components_list if c.get("sync_status") == filter_status]
        return _wrap({"components": components_list}, ctx, action)

    if action == "sync":
        direction = payload.get("direction", "both")
        dry_run = bool(payload.get("dry_run", False))
        if dry_run:
            return _wrap({"dry_run": True, "direction": direction}, ctx, action)
        designs_config = design_module._load_designs_config(trace_dir)
        components_config = design_module._load_components_config(trace_dir)
        cwd = Path.cwd()
        if direction in {"pull", "both"}:
            proc = await asyncio.create_subprocess_exec("bun", "run", "figma:pull", cwd=cwd)
            await proc.wait()
        if direction in {"push", "both"}:
            proc = await asyncio.create_subprocess_exec("bun", "run", "figma:push", cwd=cwd)
            await proc.wait()
        designs_config["last_sync"] = datetime.now(UTC).isoformat()
        design_module._save_designs_config(trace_dir, designs_config)
        for component in components_config.get("components", []):
            component["sync_status"] = "synced"
            component["last_synced"] = datetime.now(UTC).isoformat()
        design_module._save_components_config(trace_dir, components_config)
        return _wrap({"synced": True, "direction": direction}, ctx, action)

    if action == "generate":
        component = payload.get("component")
        all_components = bool(payload.get("all", False))
        template = payload.get("template", "default")
        if not all_components and not component:
            msg = "Specify component or all=true."
            raise ToolError(msg)
        components_config = design_module._load_components_config(trace_dir)
        components_list = components_config.get("components", [])
        target_components = (
            components_list if all_components else [c for c in components_list if c.get("name") == component]
        )
        generated = []
        cwd = Path.cwd()
        for comp in target_components:
            comp_name = comp.get("name")
            proc = await asyncio.create_subprocess_exec(
                "bun",
                "run",
                "storybook:generate",
                comp_name,
                "--template",
                template,
                cwd=cwd,
            )
            await proc.wait()
            comp["has_story"] = True
            generated.append(comp_name)
        design_module._save_components_config(trace_dir, components_config)
        return _wrap({"generated": generated}, ctx, action)

    if action == "export":
        component = payload.get("component")
        all_components = bool(payload.get("all", False))
        if not all_components and not component:
            msg = "Specify component or all=true."
            raise ToolError(msg)
        designs_config = design_module._load_designs_config(trace_dir)
        components_config = design_module._load_components_config(trace_dir)
        figma_config = designs_config.get("figma", {})
        figma_file_key = figma_config.get("file_key")
        figma_token = figma_config.get("access_token")
        if not figma_file_key or not figma_token:
            msg = "Figma credentials not configured."
            raise ToolError(msg)
        components_list = components_config.get("components", [])
        target_components = (
            components_list if all_components else [c for c in components_list if c.get("name") == component]
        )
        cwd = Path.cwd()
        exported = []
        for comp in target_components:
            if not comp.get("has_story"):
                continue
            proc = await asyncio.create_subprocess_exec(
                "bun",
                "run",
                "figma:export",
                comp.get("name"),
                "--file-key",
                figma_file_key,
                "--token",
                figma_token,
                cwd=cwd,
            )
            await proc.wait()
            exported.append(comp.get("name"))
        return _wrap({"exported": exported}, ctx, action)

    msg = f"Unknown design action: {action}"
    raise ToolError(msg)


__all__ = ["design_manage", "tui_manage"]
