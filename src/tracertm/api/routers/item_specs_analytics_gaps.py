"""Coverage gap and suspect link analysis endpoints.

Provides test coverage gap detection and suspect traceability link analysis.
"""

from datetime import UTC, datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from tracertm.api.deps import auth_guard, get_db
from tracertm.schemas.spec_analytics import (
    AnalyzeCoverageGapsRequest,
    AnalyzeSuspectLinksRequest,
    CoverageGap,
    CoverageGapAnalysisResponse,
    SuspectLinkAnalysisResponse,
)
from tracertm.services import spec_analytics_service

router = APIRouter(prefix="/analytics", tags=["Item Spec Analytics - Coverage & Links"])


@router.post(
    "/analyze/coverage-gaps",
    response_model=CoverageGapAnalysisResponse,
)
async def analyze_coverage_gaps(
    project_id: Annotated[str, Path(description="Project ID")],
    request: AnalyzeCoverageGapsRequest | None = None,
    _claims: dict[str, object] = Depends(auth_guard),
    _db: AsyncSession = Depends(get_db),
) -> CoverageGapAnalysisResponse:
    """Analyze test coverage gaps for requirements."""
    try:
        requirements: list[dict[str, object]] = []
        tests: list[dict[str, object]] = []
        trace_links: list[dict[str, object]] = []
        safety_level: object = None

        if request:
            if hasattr(request, "requirements"):
                requirements = list(request.requirements or [])
            if hasattr(request, "tests"):
                tests = list(request.tests or [])
            if hasattr(request, "trace_links"):
                trace_links = list(request.trace_links or [])
            if hasattr(request, "safety_level"):
                safety_level = request.safety_level

        from tracertm.services.spec_analytics_service import SafetyLevel as ServiceSafetyLevel

        safety: ServiceSafetyLevel | None = (
            safety_level if isinstance(safety_level, (ServiceSafetyLevel, type(None))) else None
        )
        gaps = spec_analytics_service.analyze_coverage_gaps(
            requirements=requirements,
            tests=tests,
            trace_links=trace_links,
            safety_level=safety,
        )

        gap_list = [
            CoverageGap(
                requirement_id=gap.item_id,
                requirement_title=gap.item_id,
                gap_type=gap.gap_type,
                severity=gap.severity,
                recommendation=gap.suggestion,
            )
            for gap in gaps
        ]

        return CoverageGapAnalysisResponse(
            project_id=project_id,
            gaps=gap_list,
            total_gaps=len(gap_list),
            coverage_percentage=0.0,
            critical_gaps=len([g for g in gap_list if g.severity == "critical"]),
            high_gaps=len([g for g in gap_list if g.severity == "high"]),
            analyzed_at=datetime.now(UTC),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/analyze/suspect-links",
    response_model=SuspectLinkAnalysisResponse,
)
async def analyze_suspect_links(
    project_id: Annotated[str, Path(description="Project ID")],
    request: AnalyzeSuspectLinksRequest | None = None,
    _claims: dict[str, object] = Depends(auth_guard),
    _db: AsyncSession = Depends(get_db),
) -> SuspectLinkAnalysisResponse:
    """Detect suspect traceability links that may be broken or invalid."""
    try:
        links: list[dict[str, object]] = []
        item_versions: dict[str, object] = {}
        recent_changes: list[dict[str, object]] = []

        if request:
            if hasattr(request, "links"):
                links = request.links or []
            if hasattr(request, "item_versions"):
                item_versions = request.item_versions or {}
            if hasattr(request, "recent_changes"):
                recent_changes = request.recent_changes or []

        links_typed = links
        versions_typed = cast("dict[str, int]", item_versions)
        changes_typed = recent_changes
        detected_suspect_links = spec_analytics_service.detect_suspect_links(
            links=links_typed,
            item_versions=versions_typed,
            recent_changes=changes_typed,
        )

        return SuspectLinkAnalysisResponse(
            project_id=project_id,
            suspect_links=detected_suspect_links or [],
            total_links=len(links),
            analyzed_at=datetime.now(UTC),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
