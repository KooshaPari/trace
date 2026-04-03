"""Workflow management API endpoints for TraceRTM.

Provides:
- Workflow triggering via Temporal
- Graph operations (snapshot, validate, export, diff)
- Integration sync workflows
- Workflow schedules management
- Temporal summary
"""

from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from tracertm.api.deps import auth_guard, get_db
from tracertm.services.temporal_service import TemporalService

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])


class WorkflowTriggerPayload(BaseModel):
    """Request payload for triggering a workflow by name."""

    workflow_name: str
    input: dict[str, Any] | None = None


def ensure_write_permission(claims: dict[str, Any] | None, action: str) -> None:
    """Check if user has write permission."""
    from tracertm.api.main import ensure_write_permission as _ewp

    _ewp(claims, action=action)


@router.post("/trigger")
async def trigger_workflow_endpoint(
    payload: WorkflowTriggerPayload,
    claims: Annotated[dict[str, Any], Depends(auth_guard)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Trigger a Temporal workflow by name."""
    ensure_write_permission(claims, action="trigger_workflow")
    service = TemporalService()
    workflow_map = {
        "graph.snapshot": "GraphSnapshotWorkflow",
        "graph.validate": "GraphValidationWorkflow",
        "graph.export": "GraphExportWorkflow",
        "graph.diff": "GraphDiffWorkflow",
        "integrations.sync": "IntegrationSyncWorkflow",
        "integrations.retry": "IntegrationRetryWorkflow",
    }
    workflow_name = workflow_map.get(payload.workflow_name, payload.workflow_name)
    result = await service.start_workflow(workflow_name, **(payload.input or {}))

    try:
        from tracertm.repositories.workflow_run_repository import WorkflowRunRepository

        repo = WorkflowRunRepository(db)
        input_dict = payload.input or {}
        user_id_obj = claims.get("sub") if claims else None
        user_id = cast("str | None", user_id_obj) if user_id_obj else None
        await repo.create_run(
            workflow_name=payload.workflow_name,
            payload=payload.input or {},
            project_id=cast("str | None", input_dict.get("project_id")),
            graph_id=cast("str | None", input_dict.get("graph_id")),
            external_run_id=result.get("workflow_id") or result.get("run_id"),
            created_by_user_id=user_id,
        )
        await db.commit()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to record workflow run: {exc}") from exc
    return {"status": "queued", "result": result}


@router.post("/graph-snapshot")
async def trigger_graph_snapshot(
    project_id: str,
    graph_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Trigger graph snapshot workflow in Temporal."""
    ensure_write_permission(claims, action="graph_snapshot")
    service = TemporalService()
    result = await service.start_workflow(
        "GraphSnapshotWorkflow",
        project_id=project_id,
        graph_id=graph_id,
    )
    try:
        from tracertm.repositories.workflow_run_repository import WorkflowRunRepository

        repo = WorkflowRunRepository(db)
        await repo.create_run(
            workflow_name="graph.snapshot",
            payload={"project_id": project_id, "graph_id": graph_id},
            project_id=project_id,
            graph_id=graph_id,
            external_run_id=result.get("workflow_id") or result.get("run_id"),
            created_by_user_id=cast("str | None", claims.get("sub")) if claims else None,
        )
        await db.commit()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to record workflow run: {exc}") from exc
    return {"status": "queued", "result": result}


@router.post("/graph-validate")
async def trigger_graph_validation(
    project_id: str,
    graph_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Trigger graph validation workflow in Temporal."""
    ensure_write_permission(claims, action="graph_validate")
    service = TemporalService()
    result = await service.start_workflow(
        "GraphValidationWorkflow",
        project_id=project_id,
        graph_id=graph_id,
    )
    try:
        from tracertm.repositories.workflow_run_repository import WorkflowRunRepository

        repo = WorkflowRunRepository(db)
        await repo.create_run(
            workflow_name="graph.validate",
            payload={"project_id": project_id, "graph_id": graph_id},
            project_id=project_id,
            graph_id=graph_id,
            external_run_id=result.get("workflow_id") or result.get("run_id"),
            created_by_user_id=cast("str | None", claims.get("sub")) if claims else None,
        )
        await db.commit()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to record workflow run: {exc}") from exc
    return {"status": "queued", "result": result}


@router.post("/graph-export")
async def trigger_graph_export(
    project_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Trigger graph export workflow in Temporal."""
    ensure_write_permission(claims, action="graph_export")
    service = TemporalService()
    result = await service.start_workflow(
        "GraphExportWorkflow",
        project_id=project_id,
    )
    try:
        from tracertm.repositories.workflow_run_repository import WorkflowRunRepository

        repo = WorkflowRunRepository(db)
        await repo.create_run(
            workflow_name="graph.export",
            payload={"project_id": project_id},
            project_id=project_id,
            external_run_id=result.get("workflow_id") or result.get("run_id"),
            created_by_user_id=cast("str | None", claims.get("sub")) if claims else None,
        )
        await db.commit()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to record workflow run: {exc}") from exc
    return {"status": "queued", "result": result}


@router.post("/graph-diff")
async def trigger_graph_diff(
    project_id: str,
    graph_id: str,
    from_version: int,
    to_version: int,
    claims: Annotated[dict[str, Any], Depends(auth_guard)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Trigger graph diff workflow in Temporal."""
    ensure_write_permission(claims, action="graph_diff")
    service = TemporalService()
    result = await service.start_workflow(
        "GraphDiffWorkflow",
        project_id=project_id,
        graph_id=graph_id,
        from_version=from_version,
        to_version=to_version,
    )
    try:
        from tracertm.repositories.workflow_run_repository import WorkflowRunRepository

        repo = WorkflowRunRepository(db)
        await repo.create_run(
            workflow_name="graph.diff",
            payload={
                "project_id": project_id,
                "graph_id": graph_id,
                "from_version": from_version,
                "to_version": to_version,
            },
            project_id=project_id,
            graph_id=graph_id,
            external_run_id=result.get("workflow_id") or result.get("run_id"),
            created_by_user_id=cast("str | None", claims.get("sub")) if claims else None,
        )
        await db.commit()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to record workflow run: {exc}") from exc
    return {"status": "queued", "result": result}


@router.post("/integrations-sync")
async def trigger_integrations_sync(
    limit: int = 50,
    claims: dict[str, Any] = Depends(auth_guard),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Trigger integration sync workflow in Temporal."""
    ensure_write_permission(claims, action="integrations_sync")
    service = TemporalService()
    result = await service.start_workflow(
        "IntegrationSyncWorkflow",
        limit=limit,
    )
    try:
        from tracertm.repositories.workflow_run_repository import WorkflowRunRepository

        repo = WorkflowRunRepository(db)
        await repo.create_run(
            workflow_name="integrations.sync",
            payload={"limit": limit},
            external_run_id=result.get("workflow_id") or result.get("run_id"),
            created_by_user_id=cast("str | None", claims.get("sub")) if claims else None,
        )
        await db.commit()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to record workflow run: {exc}") from exc
    return {"status": "queued", "result": result}


@router.post("/integrations-retry")
async def trigger_integrations_retry(
    credential_id: str,
    claims: dict[str, Any] = Depends(auth_guard),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retry failed integration sync for a specific credential."""
    ensure_write_permission(claims, action="integrations_retry")
    service = TemporalService()
    result = await service.start_workflow(
        "IntegrationRetryWorkflow",
        credential_id=credential_id,
    )
    try:
        from tracertm.repositories.workflow_run_repository import WorkflowRunRepository

        repo = WorkflowRunRepository(db)
        await repo.create_run(
            workflow_name="integrations.retry",
            payload={"credential_id": credential_id},
            external_run_id=result.get("workflow_id") or result.get("run_id"),
            created_by_user_id=cast("str | None", claims.get("sub")) if claims else None,
        )
        await db.commit()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to record workflow run: {exc}") from exc
    return {"status": "queued", "result": result}
