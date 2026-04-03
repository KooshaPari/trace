"""Test run management API endpoints for TraceRTM.

Provides:
- Test run CRUD operations
- Test run execution lifecycle (start, complete, cancel)
- Test result submission
- Test run activities and statistics
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from tracertm.api.config.rate_limiting import enforce_rate_limit
from tracertm.api.deps import auth_guard, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/test-runs", tags=["test-runs"])


def ensure_project_access(project_id: str | None, claims: dict[str, Any] | None) -> None:
    """Check if user has access to project."""
    from tracertm.api.main import ensure_project_access as _epa

    _epa(project_id, claims)


@router.get("")
async def list_test_runs(
    request: Request,
    project_id: str,
    status: str | None = None,
    run_type: str | None = None,
    suite_id: str | None = None,
    environment: str | None = None,
    initiated_by: str | None = None,
    skip: int = 0,
    limit: int = 50,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """List test runs for a project with filtering."""
    enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)

    from tracertm.repositories.test_run_repository import TestRunRepository

    repo = TestRunRepository(db)
    runs, total = await repo.list_by_project(
        project_id=project_id,
        status=status,
        run_type=run_type,
        suite_id=suite_id,
        environment=environment,
        initiated_by=initiated_by,
        skip=skip,
        limit=limit,
    )

    return {
        "test_runs": [
            {
                "id": r.id,
                "run_number": r.run_number,
                "project_id": r.project_id,
                "suite_id": r.suite_id,
                "name": r.name,
                "description": r.description,
                "status": r.status.value if hasattr(r.status, "value") else r.status,
                "run_type": r.run_type.value if hasattr(r.run_type, "value") else r.run_type,
                "environment": r.environment,
                "build_number": r.build_number,
                "build_url": r.build_url,
                "branch": r.branch,
                "commit_sha": r.commit_sha,
                "scheduled_at": r.scheduled_at.isoformat() if r.scheduled_at else None,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "duration_seconds": r.duration_seconds,
                "initiated_by": r.initiated_by,
                "executed_by": r.executed_by,
                "total_tests": r.total_tests,
                "passed_count": r.passed_count,
                "failed_count": r.failed_count,
                "skipped_count": r.skipped_count,
                "blocked_count": r.blocked_count,
                "error_count": r.error_count,
                "pass_rate": r.pass_rate,
                "tags": r.tags,
                "external_run_id": r.external_run_id,
                "metadata": r.run_metadata,
                "version": r.version,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat(),
            }
            for r in runs
        ],
        "total": total,
    }


@router.get("/{run_id}")
async def get_test_run(
    request: Request,
    run_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Get a test run by ID."""
    enforce_rate_limit(request, claims)

    from tracertm.repositories.test_run_repository import TestRunRepository

    repo = TestRunRepository(db)
    run = await repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    ensure_project_access(run.project_id, claims)

    return {
        "id": run.id,
        "run_number": run.run_number,
        "project_id": run.project_id,
        "suite_id": run.suite_id,
        "name": run.name,
        "description": run.description,
        "status": run.status.value if hasattr(run.status, "value") else run.status,
        "run_type": run.run_type.value if hasattr(run.run_type, "value") else run.run_type,
        "environment": run.environment,
        "build_number": run.build_number,
        "build_url": run.build_url,
        "branch": run.branch,
        "commit_sha": run.commit_sha,
        "scheduled_at": run.scheduled_at.isoformat() if run.scheduled_at else None,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "duration_seconds": run.duration_seconds,
        "initiated_by": run.initiated_by,
        "executed_by": run.executed_by,
        "total_tests": run.total_tests,
        "passed_count": run.passed_count,
        "failed_count": run.failed_count,
        "skipped_count": run.skipped_count,
        "blocked_count": run.blocked_count,
        "error_count": run.error_count,
        "pass_rate": run.pass_rate,
        "notes": run.notes,
        "failure_summary": run.failure_summary,
        "tags": run.tags,
        "external_run_id": run.external_run_id,
        "webhook_id": run.webhook_id,
        "metadata": run.run_metadata,
        "version": run.version,
        "created_at": run.created_at.isoformat(),
        "updated_at": run.updated_at.isoformat(),
    }


@router.post("")
async def create_test_run(
    request: Request,
    project_id: str,
    run_data: dict[str, Any],
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Create a new test run."""
    enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)

    from tracertm.repositories.test_run_repository import TestRunRepository

    repo = TestRunRepository(db)
    run = await repo.create(
        project_id=project_id,
        name=run_data["name"],
        description=run_data.get("description"),
        suite_id=run_data.get("suite_id"),
        run_type=run_data.get("run_type", "manual"),
        environment=run_data.get("environment"),
        build_number=run_data.get("build_number"),
        build_url=run_data.get("build_url"),
        branch=run_data.get("branch"),
        commit_sha=run_data.get("commit_sha"),
        scheduled_at=run_data.get("scheduled_at"),
        initiated_by=claims.get("sub"),
        tags=run_data.get("tags"),
        external_run_id=run_data.get("external_run_id"),
        webhook_id=run_data.get("webhook_id"),
        metadata=run_data.get("metadata"),
    )
    await db.commit()

    return {"id": run.id, "run_number": run.run_number}


@router.put("/{run_id}")
async def update_test_run(
    request: Request,
    run_id: str,
    run_data: dict[str, Any],
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Update a test run."""
    enforce_rate_limit(request, claims)

    from tracertm.repositories.test_run_repository import TestRunRepository

    repo = TestRunRepository(db)
    run = await repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    ensure_project_access(run.project_id, claims)

    updates = {k: v for k, v in run_data.items() if v is not None}
    if "metadata" in updates:
        updates["run_metadata"] = updates.pop("metadata")

    updated = await repo.update(run_id, updated_by=claims.get("sub"), **updates)
    await db.commit()

    if updated is None:
        raise HTTPException(status_code=404, detail="Test run not found after update")
    return {"id": updated.id, "version": updated.version}


@router.post("/{run_id}/start")
async def start_test_run(
    request: Request,
    run_id: str,
    start_data: dict[str, Any] | None = None,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Start a test run."""
    enforce_rate_limit(request, claims)

    from tracertm.repositories.test_run_repository import TestRunRepository

    repo = TestRunRepository(db)
    run = await repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    ensure_project_access(run.project_id, claims)

    start_data = start_data or {}
    updated = await repo.start(
        run_id=run_id,
        executed_by=start_data.get("executed_by") or claims.get("sub"),
    )
    await db.commit()

    if updated is None:
        raise HTTPException(status_code=404, detail="Test run not found after start")
    return {
        "id": updated.id,
        "status": updated.status.value if hasattr(updated.status, "value") else updated.status,
        "started_at": updated.started_at.isoformat() if updated.started_at else None,
    }


@router.post("/{run_id}/complete")
async def complete_test_run(
    request: Request,
    run_id: str,
    complete_data: dict[str, Any] | None = None,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Complete a test run."""
    enforce_rate_limit(request, claims)

    from tracertm.repositories.test_run_repository import TestRunRepository

    repo = TestRunRepository(db)
    run = await repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    ensure_project_access(run.project_id, claims)

    complete_data = complete_data or {}
    updated = await repo.complete(
        run_id=run_id,
        status=complete_data.get("status"),
        notes=complete_data.get("notes"),
        failure_summary=complete_data.get("failure_summary"),
        completed_by=claims.get("sub"),
    )
    await db.commit()

    if updated is None:
        raise HTTPException(status_code=404, detail="Test run not found after complete")
    return {
        "id": updated.id,
        "status": updated.status.value if hasattr(updated.status, "value") else updated.status,
        "completed_at": updated.completed_at.isoformat() if updated.completed_at else None,
        "pass_rate": updated.pass_rate,
    }


@router.post("/{run_id}/cancel")
async def cancel_test_run(
    request: Request,
    run_id: str,
    cancel_data: dict[str, Any] | None = None,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Cancel a test run."""
    enforce_rate_limit(request, claims)

    from tracertm.repositories.test_run_repository import TestRunRepository

    repo = TestRunRepository(db)
    run = await repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    ensure_project_access(run.project_id, claims)

    cancel_data = cancel_data or {}
    updated = await repo.cancel(
        run_id=run_id,
        reason=cancel_data.get("reason"),
        cancelled_by=claims.get("sub"),
    )
    await db.commit()

    if updated is None:
        raise HTTPException(status_code=404, detail="Test run not found after cancel")
    return {
        "id": updated.id,
        "status": updated.status.value if hasattr(updated.status, "value") else updated.status,
    }


@router.post("/{run_id}/results")
async def submit_test_result(
    request: Request,
    run_id: str,
    result_data: dict[str, Any],
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Submit a single test result."""
    enforce_rate_limit(request, claims)

    from tracertm.repositories.test_run_repository import TestRunRepository

    repo = TestRunRepository(db)
    run = await repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    ensure_project_access(run.project_id, claims)

    result = await repo.add_result(
        run_id=run_id,
        test_case_id=result_data["test_case_id"],
        status=result_data["status"],
        started_at=result_data.get("started_at"),
        completed_at=result_data.get("completed_at"),
        duration_seconds=result_data.get("duration_seconds"),
        executed_by=result_data.get("executed_by") or claims.get("sub"),
        actual_result=result_data.get("actual_result"),
        failure_reason=result_data.get("failure_reason"),
        error_message=result_data.get("error_message"),
        stack_trace=result_data.get("stack_trace"),
        screenshots=result_data.get("screenshots"),
        logs_url=result_data.get("logs_url"),
        attachments=result_data.get("attachments"),
        step_results=result_data.get("step_results"),
        linked_defect_ids=result_data.get("linked_defect_ids"),
        created_defect_id=result_data.get("created_defect_id"),
        retry_count=result_data.get("retry_count", 0),
        is_flaky=result_data.get("is_flaky", False),
        notes=result_data.get("notes"),
        metadata=result_data.get("metadata"),
    )
    await db.commit()

    return {"id": result.id, "run_id": run_id, "test_case_id": result_data["test_case_id"]}


@router.post("/{run_id}/bulk-results")
async def submit_bulk_test_results(
    request: Request,
    run_id: str,
    bulk_data: dict[str, Any],
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Submit multiple test results at once."""
    enforce_rate_limit(request, claims)

    from tracertm.repositories.test_run_repository import TestRunRepository

    repo = TestRunRepository(db)
    run = await repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    ensure_project_access(run.project_id, claims)

    results = await repo.add_bulk_results(run_id, bulk_data.get("results", []))
    await db.commit()

    return {
        "run_id": run_id,
        "submitted_count": len(results),
        "result_ids": [r.id for r in results],
    }


@router.get("/{run_id}/results")
async def get_test_run_results(
    request: Request,
    run_id: str,
    status: str | None = None,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Get all results for a test run."""
    enforce_rate_limit(request, claims)

    from tracertm.repositories.test_run_repository import TestRunRepository

    repo = TestRunRepository(db)
    run = await repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    ensure_project_access(run.project_id, claims)

    results = await repo.get_results(run_id, status)

    return {
        "run_id": run_id,
        "results": [
            {
                "id": r.id,
                "run_id": r.run_id,
                "test_case_id": r.test_case_id,
                "status": r.status.value if hasattr(r.status, "value") else r.status,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "duration_seconds": r.duration_seconds,
                "executed_by": r.executed_by,
                "actual_result": r.actual_result,
                "failure_reason": r.failure_reason,
                "error_message": r.error_message,
                "screenshots": r.screenshots,
                "logs_url": r.logs_url,
                "step_results": r.step_results,
                "linked_defect_ids": r.linked_defect_ids,
                "retry_count": r.retry_count,
                "is_flaky": r.is_flaky,
                "notes": r.notes,
                "metadata": r.run_metadata,
                "created_at": r.created_at.isoformat(),
            }
            for r in results
        ],
        "total": len(results),
    }


@router.get("/{run_id}/activities")
async def get_test_run_activities(
    request: Request,
    run_id: str,
    limit: int = 50,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Get activity log for a test run."""
    enforce_rate_limit(request, claims)

    from tracertm.repositories.test_run_repository import TestRunRepository

    repo = TestRunRepository(db)
    run = await repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    ensure_project_access(run.project_id, claims)

    activities = await repo.get_activities(run_id, limit)

    return {
        "run_id": run_id,
        "activities": [
            {
                "id": a.id,
                "run_id": a.run_id,
                "activity_type": a.activity_type,
                "from_value": a.from_value,
                "to_value": a.to_value,
                "description": a.description,
                "performed_by": a.performed_by,
                "metadata": a.run_metadata,
                "created_at": a.created_at.isoformat(),
            }
            for a in activities
        ],
    }


@router.delete("/{run_id}")
async def delete_test_run(
    request: Request,
    run_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Delete a test run."""
    enforce_rate_limit(request, claims)

    from tracertm.repositories.test_run_repository import TestRunRepository

    repo = TestRunRepository(db)
    run = await repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    ensure_project_access(run.project_id, claims)

    await repo.delete(run_id)
    await db.commit()

    return {"deleted": True, "id": run_id}


@router.get("/stats")
async def get_test_run_stats(
    request: Request,
    project_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Get test run statistics for a project."""
    enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)

    from tracertm.repositories.test_run_repository import TestRunRepository

    repo = TestRunRepository(db)
    stats = await repo.get_stats(project_id)

    stats["recent_runs"] = [
        {
            "id": r.id,
            "run_number": r.run_number,
            "name": r.name,
            "status": r.status.value if hasattr(r.status, "value") else r.status,
            "pass_rate": r.pass_rate,
            "created_at": r.created_at.isoformat(),
        }
        for r in stats.get("recent_runs", [])
    ]

    return stats
