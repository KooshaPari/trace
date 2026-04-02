"""Problem management API endpoints for TraceRTM.

Provides:
- Problem CRUD operations
- Problem status transitions
- RCA, workaround, permanent fix tracking
- Problem activities
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from tracertm.api.config.rate_limiting import enforce_rate_limit
from tracertm.api.deps import auth_guard, get_db
from tracertm.repositories.problem_repository import ProblemRepository
from tracertm.schemas.problem import (
    PermanentFixUpdate,
    ProblemClosure,
    ProblemCreate,
    ProblemStatusTransition,
    ProblemUpdate,
    RCARequest,
    WorkaroundUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/problems", tags=["problems"])


def ensure_project_access(project_id: str | None, claims: dict[str, Any] | None) -> None:
    """Check if user has access to project."""
    from tracertm.api.main import ensure_project_access as _epa

    _epa(project_id, claims)


def ensure_write_permission(claims: dict[str, Any] | None, action: str) -> None:
    """Check if user has write permission."""
    from tracertm.api.main import ensure_write_permission as _ewp

    _ewp(claims, action)


@router.get("")
async def list_problems(
    request: Request,
    project_id: str,
    status: str | None = None,
    priority: str | None = None,
    impact_level: str | None = None,
    category: str | None = None,
    assigned_to: str | None = None,
    skip: int = 0,
    limit: int = 100,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """List problems in a project with optional filters."""
    if not (request and request.headers.get("X-Bulk-Operation") == "true"):
        enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)

    repo = ProblemRepository(db)
    problems = await repo.list_all(
        project_id=project_id,
        status=status,
        priority=priority,
        impact_level=impact_level,
        category=category,
        assigned_to=assigned_to,
        limit=limit,
        offset=skip,
    )

    return {
        "total": len(problems),
        "problems": [
            {
                "id": str(p.id),
                "problem_number": p.problem_number,
                "project_id": str(p.project_id),
                "title": p.title,
                "status": p.status,
                "priority": p.priority,
                "impact_level": p.impact_level,
                "category": p.category,
                "assigned_to": p.assigned_to,
                "assigned_team": p.assigned_team,
                "root_cause_identified": p.root_cause_identified,
                "workaround_available": p.workaround_available,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in problems
        ],
    }


@router.get("/{problem_id}")
async def get_problem(
    request: Request,
    problem_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Get a specific problem by ID."""
    enforce_rate_limit(request, claims)

    repo = ProblemRepository(db)
    problem = await repo.get_by_id(problem_id)

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    return {
        "id": str(problem.id),
        "problem_number": problem.problem_number,
        "project_id": str(problem.project_id),
        "title": problem.title,
        "description": problem.description,
        "status": problem.status,
        "resolution_type": problem.resolution_type,
        "category": problem.category,
        "sub_category": problem.sub_category,
        "tags": problem.tags,
        "impact_level": problem.impact_level,
        "urgency": problem.urgency,
        "priority": problem.priority,
        "affected_systems": problem.affected_systems,
        "affected_users_estimated": problem.affected_users_estimated,
        "business_impact_description": problem.business_impact_description,
        "rca_performed": problem.rca_performed,
        "rca_method": problem.rca_method,
        "rca_notes": problem.rca_notes,
        "rca_data": problem.rca_data,
        "root_cause_identified": problem.root_cause_identified,
        "root_cause_description": problem.root_cause_description,
        "root_cause_category": problem.root_cause_category,
        "root_cause_confidence": problem.root_cause_confidence,
        "rca_completed_at": problem.rca_completed_at.isoformat() if problem.rca_completed_at else None,
        "rca_completed_by": problem.rca_completed_by,
        "workaround_available": problem.workaround_available,
        "workaround_description": problem.workaround_description,
        "workaround_effectiveness": problem.workaround_effectiveness,
        "permanent_fix_available": problem.permanent_fix_available,
        "permanent_fix_description": problem.permanent_fix_description,
        "permanent_fix_implemented_at": problem.permanent_fix_implemented_at.isoformat()
        if problem.permanent_fix_implemented_at
        else None,
        "permanent_fix_change_id": problem.permanent_fix_change_id,
        "known_error_id": problem.known_error_id,
        "knowledge_article_id": problem.knowledge_article_id,
        "assigned_to": problem.assigned_to,
        "assigned_team": problem.assigned_team,
        "owner": problem.owner,
        "closed_by": problem.closed_by,
        "closed_at": problem.closed_at.isoformat() if problem.closed_at else None,
        "closure_notes": problem.closure_notes,
        "target_resolution_date": problem.target_resolution_date.isoformat()
        if problem.target_resolution_date
        else None,
        "metadata": problem.problem_metadata,
        "version": problem.version,
        "created_at": problem.created_at.isoformat() if problem.created_at else None,
        "updated_at": problem.updated_at.isoformat() if problem.updated_at else None,
    }


@router.post("")
async def create_problem(
    request: Request,
    project_id: str,
    problem_data: ProblemCreate,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Create a new problem."""
    enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)
    ensure_write_permission(claims, "create")

    repo = ProblemRepository(db)
    problem = await repo.create(
        project_id=project_id,
        title=problem_data.title,
        description=problem_data.description,
        category=problem_data.category,
        sub_category=problem_data.sub_category,
        tags=problem_data.tags,
        impact_level=problem_data.impact_level.value,
        urgency=problem_data.urgency.value,
        priority=problem_data.priority.value,
        affected_systems=problem_data.affected_systems,
        affected_users_estimated=problem_data.affected_users_estimated,
        business_impact_description=problem_data.business_impact_description,
        assigned_to=problem_data.assigned_to,
        assigned_team=problem_data.assigned_team,
        owner=problem_data.owner,
        target_resolution_date=problem_data.target_resolution_date,
        metadata=problem_data.metadata,
        created_by=claims.get("sub", "system"),
    )
    await db.commit()

    return {"id": str(problem.id), "problem_number": problem.problem_number}


@router.put("/{problem_id}")
async def update_problem(
    request: Request,
    problem_id: str,
    problem_data: ProblemUpdate,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Update a problem."""
    enforce_rate_limit(request, claims)
    ensure_write_permission(claims, "update")

    repo = ProblemRepository(db)
    problem = await repo.get_by_id(problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    updates = problem_data.model_dump(exclude_unset=True)
    for key in ["impact_level", "urgency", "priority"]:
        if key in updates and updates[key] is not None:
            updates[key] = updates[key].value

    if "metadata" in updates:
        updates["problem_metadata"] = updates.pop("metadata")

    problem = await repo.update(
        problem_id=problem_id,
        expected_version=problem.version,
        performed_by=claims.get("sub", "system"),
        **updates,
    )
    await db.commit()

    return {"id": str(problem.id), "version": problem.version}


@router.post("/{problem_id}/status")
async def transition_problem_status(
    request: Request,
    problem_id: str,
    transition: ProblemStatusTransition,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Transition problem to a new status."""
    enforce_rate_limit(request, claims)
    ensure_write_permission(claims, "update")

    repo = ProblemRepository(db)
    try:
        problem = await repo.transition_status(
            problem_id=problem_id,
            to_status=transition.to_status.value,
            reason=transition.reason,
            performed_by=transition.performed_by or claims.get("sub", "system"),
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"id": str(problem.id), "status": problem.status, "version": problem.version}


@router.post("/{problem_id}/rca")
async def record_problem_rca(
    request: Request,
    problem_id: str,
    rca_data: RCARequest,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Record Root Cause Analysis for a problem."""
    enforce_rate_limit(request, claims)
    ensure_write_permission(claims, "update")

    repo = ProblemRepository(db)
    problem = await repo.record_rca(
        problem_id=problem_id,
        rca_method=rca_data.rca_method.value,
        rca_notes=rca_data.rca_notes,
        rca_data=rca_data.rca_data,
        root_cause_identified=rca_data.root_cause_identified,
        root_cause_description=rca_data.root_cause_description,
        root_cause_category=rca_data.root_cause_category.value if rca_data.root_cause_category else None,
        root_cause_confidence=rca_data.root_cause_confidence,
        performed_by=rca_data.performed_by or claims.get("sub", "system"),
    )
    await db.commit()

    return {
        "id": str(problem.id),
        "rca_performed": problem.rca_performed,
        "root_cause_identified": problem.root_cause_identified,
    }


@router.put("/{problem_id}/workaround")
async def update_problem_workaround(
    request: Request,
    problem_id: str,
    workaround_data: WorkaroundUpdate,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Update workaround information for a problem."""
    enforce_rate_limit(request, claims)
    ensure_write_permission(claims, "update")

    repo = ProblemRepository(db)
    problem = await repo.update_workaround(
        problem_id=problem_id,
        workaround_available=workaround_data.workaround_available,
        workaround_description=workaround_data.workaround_description,
        workaround_effectiveness=workaround_data.workaround_effectiveness,
        performed_by=claims.get("sub", "system"),
    )
    await db.commit()

    return {"id": str(problem.id), "workaround_available": problem.workaround_available}


@router.put("/{problem_id}/permanent-fix")
async def update_problem_permanent_fix(
    request: Request,
    problem_id: str,
    fix_data: PermanentFixUpdate,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Update permanent fix information for a problem."""
    enforce_rate_limit(request, claims)
    ensure_write_permission(claims, "update")

    repo = ProblemRepository(db)
    problem = await repo.update_permanent_fix(
        problem_id=problem_id,
        permanent_fix_available=fix_data.permanent_fix_available,
        permanent_fix_description=fix_data.permanent_fix_description,
        permanent_fix_change_id=fix_data.permanent_fix_change_id,
        performed_by=claims.get("sub", "system"),
    )
    await db.commit()

    return {"id": str(problem.id), "permanent_fix_available": problem.permanent_fix_available}


@router.post("/{problem_id}/close")
async def close_problem(
    request: Request,
    problem_id: str,
    closure_data: ProblemClosure,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Close a problem."""
    enforce_rate_limit(request, claims)
    ensure_write_permission(claims, "update")

    repo = ProblemRepository(db)
    problem = await repo.close(
        problem_id=problem_id,
        resolution_type=closure_data.resolution_type.value,
        closure_notes=closure_data.closure_notes,
        closed_by=closure_data.closed_by or claims.get("sub", "system"),
    )
    await db.commit()

    return {"id": str(problem.id), "status": problem.status, "resolution_type": problem.resolution_type}


@router.get("/{problem_id}/activities")
async def get_problem_activities(
    request: Request,
    problem_id: str,
    limit: int = 50,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Get activity log for a problem."""
    enforce_rate_limit(request, claims)

    repo = ProblemRepository(db)
    activities = await repo.get_activities(problem_id, limit=limit)

    return {
        "problem_id": problem_id,
        "activities": [
            {
                "id": str(a.id),
                "problem_id": str(a.problem_id),
                "activity_type": a.activity_type,
                "from_value": a.from_value,
                "to_value": a.to_value,
                "description": a.description,
                "performed_by": a.performed_by,
                "metadata": a.activity_metadata,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in activities
        ],
    }


@router.delete("/{problem_id}")
async def delete_problem(
    request: Request,
    problem_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Delete a problem (soft delete)."""
    enforce_rate_limit(request, claims)
    ensure_write_permission(claims, "delete")

    repo = ProblemRepository(db)
    success = await repo.delete(problem_id, soft=True)
    await db.commit()

    if not success:
        raise HTTPException(status_code=404, detail="Problem not found")

    return {"deleted": True, "id": problem_id}


@router.get("/stats")
async def get_problem_stats(
    request: Request,
    project_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Get problem statistics for a project."""
    enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)

    repo = ProblemRepository(db)
    by_status = await repo.count_by_status(project_id)
    by_priority = await repo.count_by_priority(project_id)

    return {
        "project_id": project_id,
        "by_status": by_status,
        "by_priority": by_priority,
        "total": sum(by_status.values()),
    }
