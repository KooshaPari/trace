"""Flakiness analysis endpoints.

Provides test flakiness detection using Meta's probabilistic model.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from tracertm.api.deps import auth_guard, get_db
from tracertm.schemas.spec_analytics import (
    AnalyzeFlakinessRequest,
    FlakinessAnalysisResponse,
)
from tracertm.services import spec_analytics_service

router = APIRouter(prefix="/analytics", tags=["Item Spec Analytics - Flakiness"])


@router.post(
    "/tests/{spec_id}/analyze/flakiness",
    response_model=FlakinessAnalysisResponse,
)
async def analyze_flakiness(
    _project_id: Annotated[str, Path(description="Project ID")],
    spec_id: Annotated[str, Path(description="Test spec ID")],
    request: Annotated[AnalyzeFlakinessRequest | None, Body()] = None,
    _claims: dict[str, object] = Depends(auth_guard),
    _db: AsyncSession = Depends(get_db),
) -> FlakinessAnalysisResponse:
    """Analyze test flakiness using Meta's probablistic flakiness detection model."""
    try:
        run_history: list[dict[str, object]] = []
        window_size = 30
        if request:
            if hasattr(request, "run_history"):
                run_history = list(request.run_history or [])
            if hasattr(request, "window_size"):
                window_size = int(request.window_size or 30)

        run_history_list: list[dict[str, object]] = run_history
        window_size_int: int = window_size
        analysis = spec_analytics_service.analyze_test_flakiness(
            run_history=run_history_list,
            window_size=window_size_int,
        )

        return FlakinessAnalysisResponse(
            spec_id=spec_id,
            probability=analysis.flakiness_score,
            entropy=analysis.entropy_score,
            pattern=None,
            pattern_confidence=analysis.confidence,
            quarantine_recommended=analysis.quarantine_recommended,
            recent_runs=0,
            flaky_runs=0,
            pass_rate=1.0 - (analysis.failure_rate_24h or 0.0),
            analyzed_at=datetime.now(UTC),
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
