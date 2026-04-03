"""Analysis endpoints for TraceRTM API.

Provides:
- Traceability gaps analysis
- Traceability matrix generation
- Impact analysis (forward and reverse)
- Cycle detection
- Shortest path finding
- Project health metrics
"""

from typing import TYPE_CHECKING, Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request

from tracertm.api.config.rate_limiting import enforce_rate_limit
from tracertm.api.deps import auth_guard, get_cache_service, get_db
from tracertm.services import (
    impact_analysis_service,
    performance_service,
    shortest_path_service,
    traceability_matrix_service,
    traceability_service,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from tracertm.services.cache_service import CacheService

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


async def _maybe_await(result: object) -> object:
    """Await result if awaitable, otherwise return as-is."""
    import inspect

    if inspect.isawaitable(result):
        return await result
    return result


def ensure_project_access(project_id: str | None, claims: dict[str, Any] | None) -> None:
    """Check project access; system admins bypass."""
    from tracertm.api.main import ensure_project_access as _epa

    _epa(project_id, claims)


@router.get("/gaps")
async def get_traceability_gaps(
    request: Request,
    project_id: str,
    from_view: str,
    to_view: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)],
    db: Annotated["AsyncSession", Depends(get_db)],
) -> dict[str, Any]:
    """Find coverage gaps between two views."""
    enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)

    service = traceability_service.TraceabilityService(db)
    gaps_result = await _maybe_await(
        service.find_gaps(project_id=project_id, source_view=from_view, target_view=to_view)
    )
    gaps = cast("list[Any]", gaps_result)

    return {
        "project_id": project_id,
        "from_view": from_view.upper(),
        "to_view": to_view.upper(),
        "gap_count": len(gaps),
        "gaps": [
            {
                "id": item.id,
                "external_id": getattr(item, "external_id", None),
                "title": getattr(item, "title", None),
                "status": getattr(item, "status", None),
            }
            for item in gaps
        ],
    }


@router.get("/trace-matrix")
async def get_traceability_matrix(
    request: Request,
    project_id: str,
    source_view: str | None = None,
    target_view: str | None = None,
    claims: dict[str, Any] = Depends(auth_guard),
    db: "AsyncSession" = Depends(get_db),
) -> dict[str, Any]:
    """Generate traceability matrix."""
    enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)

    service = traceability_matrix_service.TraceabilityMatrixService(db)
    matrix = await _maybe_await(
        service.generate_matrix(
            project_id=project_id,
            source_view=source_view,
            target_view=target_view,
        ),
    )
    return {
        "project_id": project_id,
        "source_view": source_view,
        "target_view": target_view,
        "matrix": matrix.to_dict() if hasattr(matrix, "to_dict") else matrix,
    }


@router.get("/reverse-impact/{item_id}")
async def get_reverse_impact(
    request: Request,
    item_id: str,
    project_id: str,
    max_depth: int = 5,
    claims: dict[str, Any] = Depends(auth_guard),
    db: "AsyncSession" = Depends(get_db),
) -> dict[str, Any]:
    """Analyze upstream dependencies of an item."""
    enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)

    service = impact_analysis_service.ImpactAnalysisService(db)
    result = await _maybe_await(service.analyze_reverse_impact(item_id=item_id, max_depth=max_depth))

    return {
        "root_item_id": item_id,
        "max_depth": max_depth,
        "dependencies": result.to_dict() if hasattr(result, "to_dict") else result,
    }


@router.get("/health/{project_id}")
async def get_project_health(
    request: Request,
    project_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)],
    db: Annotated["AsyncSession", Depends(get_db)],
) -> dict[str, Any]:
    """Get high-level health metrics for a project."""
    enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)

    service = performance_service.PerformanceService(db)
    stats_result = await _maybe_await(service.get_project_statistics(project_id))
    stats = cast("dict[str, Any]", stats_result)
    return {
        "project_id": project_id,
        "item_count": stats.get("item_count"),
        "link_count": stats.get("link_count"),
        "density": stats.get("density"),
        "complexity": stats.get("complexity"),
        "views": stats.get("views"),
        "statuses": stats.get("statuses"),
    }


@router.get("/impact/{item_id}")
async def get_impact_analysis(
    request: Request,
    item_id: str,
    project_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)],
    db: Annotated["AsyncSession", Depends(get_db)],
) -> dict[str, Any]:
    """Get impact analysis for an item."""
    enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)

    service = impact_analysis_service.ImpactAnalysisService(db)
    try:
        result_obj = await _maybe_await(service.analyze_impact(item_id))
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    result = cast("Any", result_obj)

    return {
        "root_item_id": result.root_item_id,
        "total_affected": result.total_affected,
        "max_depth": result.max_depth_reached,
        "affected_items": result.affected_items,
    }


@router.get("/cycles/{project_id}")
async def detect_cycles(
    request: Request,
    project_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)],
    db: Annotated["AsyncSession", Depends(get_db)],
) -> dict[str, Any]:
    """Detect circular dependencies in project items."""
    enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)

    from tracertm.services.cycle_detection_service import CycleDetectionService

    service = CycleDetectionService(db)
    cycles_result = await _maybe_await(service.detect_cycles(project_id))
    cycles = cast("list[Any]", cycles_result)

    return {
        "project_id": project_id,
        "cycle_count": len(cycles),
        "cycles": [
            {
                "item_id": c.item_id,
                "title": getattr(c, "title", None),
                "path": getattr(c, "path", []),
            }
            for c in cycles
        ],
    }


@router.get("/shortest-path")
async def find_shortest_path(
    request: Request,
    project_id: str,
    source_id: str,
    target_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)],
    db: Annotated["AsyncSession", Depends(get_db)],
    cache: Annotated["CacheService", Depends(get_cache_service)],
) -> dict[str, Any]:
    """Find shortest path between two items with Redis caching for 10x performance."""
    enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)

    service = shortest_path_service.ShortestPathService(db, cache)
    result_obj = await _maybe_await(service.find_shortest_path(project_id, source_id, target_id))
    result = cast("Any", result_obj)

    return {
        "exists": result.exists,
        "distance": result.distance,
        "path": result.path,
        "link_types": result.link_types,
    }
