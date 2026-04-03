"""Parameterized MCP tools facade.

This module re-exports all tool implementations from the params/ module.
Tool registration (@mcp.tool) is done in the params/ submodules to avoid
"Component already exists" errors when server.py loads the modules.

All implementation has been moved to src/tracertm/mcp/tools/params/
"""

from tracertm.mcp.tools.params import (
    agent_manage,
    backup_manage,
    benchmark_manage,
    chaos_manage,
    config_manage,
    database_manage,
    design_manage,
    export_manage,
    file_watch_manage,
    graph_analyze,
    import_manage,
    ingestion_manage,
    item_manage,
    link_manage,
    progress_manage,
    project_manage,
    quality_analyze,
    saved_queries_manage,
    specification_manage,
    sync_manage,
    test_manage,
    trace_analyze,
    tui_manage,
)

__all__ = [
    "agent_manage",
    "backup_manage",
    "benchmark_manage",
    "chaos_manage",
    "config_manage",
    "database_manage",
    "design_manage",
    "export_manage",
    "file_watch_manage",
    "graph_analyze",
    "import_manage",
    "ingestion_manage",
    "item_manage",
    "link_manage",
    "progress_manage",
    "project_manage",
    "quality_analyze",
    "saved_queries_manage",
    "specification_manage",
    "sync_manage",
    "test_manage",
    "trace_analyze",
    "tui_manage",
]
