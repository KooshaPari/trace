"""Impact analysis and prioritization endpoints.

Provides graph-based impact analysis and WSJF/RICE prioritization.
"""

from datetime import UTC, datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from tracertm.api.deps import auth_guard, get_db
from tracertm.api.routers.item_specs_schemas import (
    RISK_THRESHOLD_CRITICAL,
    RISK_THRESHOLD_HIGH,
    RISK_THRESHOLD_MEDIUM,
)
from tracertm.schemas.spec_analytics import (
    AnalyzeImpactRequest,
    CalculatePrioritizationRequest,
    ImpactAnalysisResponse,
    ImpactedItem,
    PrioritizationResponse,
    RICEScore,
    WSJFScore,
)
from tracertm.services import spec_analytics_service

router = APIRouter(prefix="/analytics", tags=["Item Spec Analytics - Impact & Priority"])


@router.post(
    "/{spec_type}/{spec_id}/analyze/impact",
    response_model=ImpactAnalysisResponse,
)
async def analyze_impact(
    _project_id: Annotated[str, Path(description="Project ID")],
    _spec_type: Annotated[
        str, Path(pattern="^(requirements|tests|epics|stories|tasks|defects)$", description="Spec type")
    ],
    spec_id: Annotated[str, Path(description="Spec ID")],
    request: AnalyzeImpactRequest | None = None,
    _claims: dict[str, object] = Depends(auth_guard),
    _db: AsyncSession = Depends(get_db),
) -> ImpactAnalysisResponse:
    """Analyze the impact of changes to a specification item using graph propagation."""
    try:
        adjacency: dict[str, list[str]] = {}
        item_metadata: dict[str, dict[str, object]] | None = None
        max_depth = 5

        if request:
            if hasattr(request, "adjacency"):
                adjacency = cast("dict[str, list[str]]", request.adjacency or {})
            if hasattr(request, "item_metadata"):
                raw = request.item_metadata
                item_metadata = cast("dict[str, dict[str, object]] | None", raw if isinstance(raw, dict) else None)
            if hasattr(request, "max_depth"):
                max_depth = request.max_depth or 5

        result = spec_analytics_service.analyze_change_impact(
            source_item_id=spec_id,
            adjacency=adjacency,
            item_metadata=item_metadata,
            max_depth=max_depth,
        )

        def to_impacted(item_id: str, impact_type: str, distance: int) -> ImpactedItem:
            return ImpactedItem(
                item_id=item_id,
                item_type="",
                item_title="",
                impact_type=impact_type,
                impact_severity="medium",
                distance=distance,
            )

        risk_category = (
            "critical"
            if result.risk_score >= RISK_THRESHOLD_CRITICAL
            else "high"
            if result.risk_score >= RISK_THRESHOLD_HIGH
            else "medium"
            if result.risk_score >= RISK_THRESHOLD_MEDIUM
            else "low"
        )
        return ImpactAnalysisResponse(
            spec_id=result.source_item_id,
            direct_impacts=[to_impacted(x, "direct", 1) for x in result.direct_impacts],
            transitive_impacts=[to_impacted(x, "transitive", result.impact_depth) for x in result.transitive_impacts],
            direct_impact_count=len(result.direct_impacts),
            transitive_impact_count=len(result.transitive_impacts),
            total_affected=result.blast_radius,
            max_propagation_depth=result.impact_depth,
            risk_score=result.risk_score,
            risk_category=risk_category,
            analyzed_at=datetime.now(UTC),
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/{spec_type}/{spec_id}/prioritization",
    response_model=PrioritizationResponse,
)
async def calculate_prioritization(
    _project_id: Annotated[str, Path(description="Project ID")],
    _spec_type: Annotated[str, Path(pattern="^(requirements|epics|stories|tasks)$", description="Spec type")],
    spec_id: Annotated[str, Path(description="Spec ID")],
    request: CalculatePrioritizationRequest | None = None,
    _claims: dict[str, object] = Depends(auth_guard),
    _db: AsyncSession = Depends(get_db),
) -> PrioritizationResponse:
    """Calculate WSJF and RICE prioritization scores for a specification item."""
    try:
        if not request:
            raise HTTPException(status_code=400, detail="Prioritization input values are required")

        wsjf_result: WSJFScore | None = None
        if all(
            getattr(request, a, None) is not None
            for a in ("business_value", "time_criticality", "risk_reduction", "job_size")
        ):
            wsjf_score = spec_analytics_service.calculate_wsjf(
                business_value=request.business_value or 1,
                time_criticality=request.time_criticality or 1,
                risk_reduction=request.risk_reduction or 1,
                job_size=request.job_size or 1,
                opportunity_enablement=1,
            )
            wsjf_result = WSJFScore(
                business_value=wsjf_score.business_value,
                time_criticality=wsjf_score.time_criticality,
                risk_reduction=wsjf_score.risk_reduction,
                job_size=wsjf_score.job_size,
                wsjf_score=wsjf_score.wsjf_score,
            )

        rice_result: RICEScore | None = None
        if all(getattr(request, a, None) is not None for a in ("reach", "impact", "confidence", "effort")):
            rice_score = spec_analytics_service.calculate_rice(
                reach=request.reach or 0,
                impact=request.impact or 1,
                confidence=request.confidence or 0.5,
                effort=request.effort or 1,
            )
            rice_result = RICEScore(
                reach=rice_score.reach,
                impact=int(rice_score.impact),
                confidence=rice_score.confidence,
                effort=rice_score.effort,
                rice_score=rice_score.rice_score,
            )

        return PrioritizationResponse(
            spec_id=spec_id,
            wsjf=wsjf_result,
            rice=rice_result,
            calculated_at=datetime.now(UTC),
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
