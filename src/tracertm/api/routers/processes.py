"""Process management API endpoints for TraceRTM.

Provides:
- Process CRUD operations
- Process versioning
- Process activation/deprecation
- Process execution tracking
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from tracertm.api.config.rate_limiting import enforce_rate_limit
from tracertm.api.deps import auth_guard, get_db
from tracertm.repositories.process_repository import ProcessRepository
from tracertm.schemas.process import (
    ProcessActivation,
    ProcessCreate,
    ProcessDeprecation,
    ProcessExecutionComplete,
    ProcessExecutionCreate,
    ProcessUpdate,
    ProcessVersionCreate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/processes", tags=["processes"])


def ensure_project_access(project_id: str | None, claims: dict[str, Any] | None) -> None:
    """Check if user has access to project."""
    from tracertm.api.main import ensure_project_access as _epa

    _epa(project_id, claims)


def ensure_write_permission(claims: dict[str, Any] | None, action: str) -> None:
    """Check if user has write permission."""
    from tracertm.api.main import ensure_write_permission as _ewp

    _ewp(claims, action)


@router.get("")
async def list_processes(
    request: Request,
    project_id: str,
    status: str | None = None,
    category: str | None = None,
    owner: str | None = None,
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """List processes in a project with optional filters."""
    if not (request and request.headers.get("X-Bulk-Operation") == "true"):
        enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)

    repo = ProcessRepository(db)
    processes = await repo.list_all(
        project_id=project_id,
        status=status,
        category=category,
        owner=owner,
        active_only=active_only,
        limit=limit,
        offset=skip,
    )

    return {
        "total": len(processes),
        "processes": [
            {
                "id": str(p.id),
                "process_number": p.process_number,
                "project_id": str(p.project_id),
                "name": p.name,
                "status": p.status,
                "category": p.category,
                "owner": p.owner,
                "version_number": p.version_number,
                "is_active_version": p.is_active_version,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in processes
        ],
    }


@router.get("/{process_id}")
async def get_process(
    request: Request,
    process_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Get a specific process by ID."""
    enforce_rate_limit(request, claims)

    repo = ProcessRepository(db)
    process = await repo.get_by_id(process_id)

    if not process:
        raise HTTPException(status_code=404, detail="Process not found")

    return {
        "id": str(process.id),
        "process_number": process.process_number,
        "project_id": str(process.project_id),
        "name": process.name,
        "description": process.description,
        "purpose": process.purpose,
        "status": process.status,
        "category": process.category,
        "tags": process.tags,
        "version_number": process.version_number,
        "is_active_version": process.is_active_version,
        "parent_version_id": process.parent_version_id,
        "version_notes": process.version_notes,
        "stages": process.stages,
        "swimlanes": process.swimlanes,
        "inputs": process.inputs,
        "outputs": process.outputs,
        "triggers": process.triggers,
        "exit_criteria": process.exit_criteria,
        "bpmn_xml": process.bpmn_xml,
        "bpmn_diagram_url": process.bpmn_diagram_url,
        "owner": process.owner,
        "responsible_team": process.responsible_team,
        "expected_duration_hours": process.expected_duration_hours,
        "sla_hours": process.sla_hours,
        "activated_at": process.activated_at.isoformat() if process.activated_at else None,
        "activated_by": process.activated_by,
        "deprecated_at": process.deprecated_at.isoformat() if process.deprecated_at else None,
        "deprecated_by": process.deprecated_by,
        "deprecation_reason": process.deprecation_reason,
        "related_process_ids": process.related_process_ids,
        "metadata": process.process_metadata,
        "version": process.version,
        "created_at": process.created_at.isoformat() if process.created_at else None,
        "updated_at": process.updated_at.isoformat() if process.updated_at else None,
    }


@router.post("")
async def create_process(
    request: Request,
    project_id: str,
    process_data: ProcessCreate,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Create a new process."""
    enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)
    ensure_write_permission(claims, "create")

    repo = ProcessRepository(db)

    stages = [s.model_dump() for s in process_data.stages] if process_data.stages else None
    swimlanes = [s.model_dump() for s in process_data.swimlanes] if process_data.swimlanes else None
    inputs = [i.model_dump() for i in process_data.inputs] if process_data.inputs else None
    outputs = [o.model_dump() for o in process_data.outputs] if process_data.outputs else None
    triggers = [t.model_dump() for t in process_data.triggers] if process_data.triggers else None

    process = await repo.create(
        project_id=project_id,
        name=process_data.name,
        description=process_data.description,
        purpose=process_data.purpose,
        category=process_data.category.value if process_data.category else None,
        tags=process_data.tags,
        stages=stages,
        swimlanes=swimlanes,
        inputs=inputs,
        outputs=outputs,
        triggers=triggers,
        exit_criteria=process_data.exit_criteria,
        bpmn_xml=process_data.bpmn_xml,
        owner=process_data.owner,
        responsible_team=process_data.responsible_team,
        expected_duration_hours=process_data.expected_duration_hours,
        sla_hours=process_data.sla_hours,
        related_process_ids=process_data.related_process_ids,
        metadata=process_data.metadata,
        _created_by=str(claims.get("sub", "system")),
    )
    await db.commit()

    return {"id": str(process.id), "process_number": process.process_number}


@router.put("/{process_id}")
async def update_process(
    request: Request,
    process_id: str,
    process_data: ProcessUpdate,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Update a process."""
    enforce_rate_limit(request, claims)
    ensure_write_permission(claims, "update")

    repo = ProcessRepository(db)
    process = await repo.get_by_id(process_id)
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")

    updates = process_data.model_dump(exclude_unset=True)

    if "category" in updates and updates["category"] is not None:
        updates["category"] = updates["category"].value

    for key in ["stages", "swimlanes", "inputs", "outputs", "triggers"]:
        if key in updates and updates[key] is not None:
            updates[key] = [item.model_dump() if hasattr(item, "model_dump") else item for item in updates[key]]

    if "metadata" in updates:
        updates["process_metadata"] = updates.pop("metadata")

    process = await repo.update(
        process_id=process_id,
        expected_version=process.version,
        **updates,
    )
    await db.commit()

    return {"id": str(process.id), "version": process.version}


@router.post("/{process_id}/versions")
async def create_process_version(
    request: Request,
    process_id: str,
    version_data: ProcessVersionCreate,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Create a new version of a process."""
    enforce_rate_limit(request, claims)
    ensure_write_permission(claims, "create")

    repo = ProcessRepository(db)
    try:
        new_process = await repo.create_version(
            process_id=process_id,
            version_notes=version_data.version_notes,
            _created_by=str(claims.get("sub", "system")),
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "id": str(new_process.id),
        "process_number": new_process.process_number,
        "version_number": new_process.version_number,
        "parent_version_id": new_process.parent_version_id,
    }


@router.put("/{process_id}/activate")
async def activate_process(
    request: Request,
    process_id: str,
    activation_data: ProcessActivation,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Activate a process version."""
    enforce_rate_limit(request, claims)
    ensure_write_permission(claims, "update")

    repo = ProcessRepository(db)
    try:
        process = await repo.activate_version(
            process_id=process_id,
            activated_by=activation_data.activated_by or claims.get("sub", "system"),
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "id": str(process.id),
        "status": process.status,
        "is_active_version": process.is_active_version,
    }


@router.put("/{process_id}/deprecate")
async def deprecate_process(
    request: Request,
    process_id: str,
    deprecation_data: ProcessDeprecation,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Deprecate a process."""
    enforce_rate_limit(request, claims)
    ensure_write_permission(claims, "update")

    repo = ProcessRepository(db)
    try:
        process = await repo.deprecate(
            process_id=process_id,
            deprecation_reason=deprecation_data.deprecation_reason,
            deprecated_by=deprecation_data.deprecated_by or claims.get("sub", "system"),
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"id": str(process.id), "status": process.status}


@router.delete("/{process_id}")
async def delete_process(
    request: Request,
    process_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Delete a process (soft delete)."""
    enforce_rate_limit(request, claims)
    ensure_write_permission(claims, "delete")

    repo = ProcessRepository(db)
    success = await repo.delete(process_id, soft=True)
    await db.commit()

    if not success:
        raise HTTPException(status_code=404, detail="Process not found")

    return {"deleted": True, "id": process_id}


@router.get("/{project_id}/stats")
async def get_process_stats(
    request: Request,
    project_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Get process statistics for a project."""
    enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)

    repo = ProcessRepository(db)
    by_status = await repo.count_by_status(project_id)
    by_category = await repo.count_by_category(project_id)

    return {
        "project_id": project_id,
        "by_status": by_status,
        "by_category": by_category,
        "total": sum(by_status.values()),
    }


@router.post("/{process_id}/executions")
async def create_process_execution(
    request: Request,
    process_id: str,
    execution_data: ProcessExecutionCreate,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Start a new execution of a process."""
    enforce_rate_limit(request, claims)
    ensure_write_permission(claims, "create")

    repo = ProcessRepository(db)
    try:
        execution = await repo.create_execution(
            process_id=process_id,
            initiated_by=claims.get("sub", "system"),
            trigger_item_id=execution_data.trigger_item_id,
            context_data=execution_data.context_data,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"id": str(execution.id), "execution_number": execution.execution_number}


@router.get("/{process_id}/executions")
async def list_process_executions(
    request: Request,
    process_id: str,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """List executions for a process."""
    enforce_rate_limit(request, claims)

    repo = ProcessRepository(db)
    executions = await repo.list_executions(
        process_id=process_id,
        status=status,
        limit=limit,
        offset=skip,
    )

    return {
        "total": len(executions),
        "executions": [
            {
                "id": str(e.id),
                "process_id": str(e.process_id),
                "execution_number": e.execution_number,
                "status": e.status,
                "current_stage_id": e.current_stage_id,
                "started_at": e.started_at.isoformat() if e.started_at else None,
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "initiated_by": e.initiated_by,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in executions
        ],
    }


@router.get("/executions/{execution_id}")
async def get_execution_by_id_endpoint(
    request: Request,
    execution_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Get a specific process execution."""
    enforce_rate_limit(request, claims)

    repo = ProcessRepository(db)
    execution = await repo.get_execution_by_id(execution_id)

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return {
        "id": str(execution.id),
        "process_id": str(execution.process_id),
        "execution_number": execution.execution_number,
        "status": execution.status,
        "current_stage_id": execution.current_stage_id,
        "completed_stages": execution.completed_stages,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "initiated_by": execution.initiated_by,
        "completed_by": execution.completed_by,
        "trigger_item_id": execution.trigger_item_id,
        "context_data": execution.context_data,
        "result_summary": execution.result_summary,
        "output_item_ids": execution.output_item_ids,
        "created_at": execution.created_at.isoformat() if execution.created_at else None,
        "updated_at": execution.updated_at.isoformat() if execution.updated_at else None,
    }


@router.post("/executions/{execution_id}/start")
async def start_execution_endpoint(
    request: Request,
    execution_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Start a pending execution."""
    enforce_rate_limit(request, claims)
    ensure_write_permission(claims, "update")

    repo = ProcessRepository(db)
    try:
        execution = await repo.start_execution(execution_id)
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"id": str(execution.id), "status": execution.status}


@router.post("/executions/{execution_id}/advance")
async def advance_execution(
    request: Request,
    execution_id: str,
    stage_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Advance execution to next stage."""
    enforce_rate_limit(request, claims)
    ensure_write_permission(claims, "update")

    repo = ProcessRepository(db)
    try:
        execution = await repo.advance_execution(execution_id, stage_id)
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "id": str(execution.id),
        "current_stage_id": execution.current_stage_id,
        "completed_stages": execution.completed_stages,
    }


@router.post("/executions/{execution_id}/complete")
async def complete_execution_endpoint(
    request: Request,
    execution_id: str,
    completion_data: ProcessExecutionComplete,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Complete a process execution."""
    enforce_rate_limit(request, claims)
    ensure_write_permission(claims, "update")

    repo = ProcessRepository(db)
    try:
        execution = await repo.complete_execution(
            execution_id=execution_id,
            completed_by=completion_data.completed_by or claims.get("sub", "system"),
            result_summary=completion_data.result_summary,
            output_item_ids=completion_data.output_item_ids,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"id": str(execution.id), "status": execution.status}
