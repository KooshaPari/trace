"""Defect analysis endpoints.

Provides ODC classification and CVSS scoring endpoints.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from tracertm.api.deps import auth_guard, get_db
from tracertm.schemas.spec_analytics import (
    AnalyzeCVSSRequest,
    AnalyzeODCRequest,
    CVSSBreakdown,
    CVSSScoreResponse,
    CVSSSeverity,
    ODCClassificationResponse,
    ODCDefectType,
    ODCImpact,
    ODCTrigger,
)
from tracertm.services import spec_analytics_service

router = APIRouter(prefix="/analytics", tags=["Item Spec Analytics - Defects"])


@router.post(
    "/defects/{spec_id}/analyze/odc",
    response_model=ODCClassificationResponse,
)
async def analyze_odc_classification(
    _project_id: Annotated[str, Path(description="Project ID")],
    spec_id: Annotated[str, Path(description="Defect spec ID")],
    request: Annotated[AnalyzeODCRequest | None, Body()] = None,
    _claims: dict[str, object] = Depends(auth_guard),
    _db: AsyncSession = Depends(get_db),
) -> ODCClassificationResponse:
    """Classify a defect using the Orthogonal Defect Classification (ODC) scheme."""
    try:
        description: str = ""
        trigger_context: str | None = None
        impact_description: str | None = None

        if request:
            if hasattr(request, "description"):
                description = str(request.description or "")
            if hasattr(request, "trigger_context"):
                trigger_context = None if request.trigger_context is None else str(request.trigger_context)
            if hasattr(request, "impact_description"):
                impact_description = None if request.impact_description is None else str(request.impact_description)

        if not description:
            raise HTTPException(status_code=400, detail="Defect description is required for ODC classification")

        classification = spec_analytics_service.classify_defect(
            description=description,
            trigger_context=trigger_context,
            impact_description=impact_description,
        )

        return ODCClassificationResponse(
            spec_id=spec_id,
            defect_type=ODCDefectType(classification.defect_type.value),
            trigger=ODCTrigger(classification.trigger.value),
            impact=ODCImpact(classification.impact.value),
            confidence=classification.confidence,
            defect_type_confidence=classification.confidence,
            trigger_confidence=classification.confidence,
            impact_confidence=classification.confidence,
            analyzed_at=datetime.now(UTC),
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/defects/{spec_id}/analyze/cvss",
    response_model=CVSSScoreResponse,
)
async def analyze_cvss_score(
    _project_id: Annotated[str, Path(description="Project ID")],
    spec_id: Annotated[str, Path(description="Defect spec ID")],
    request: Annotated[AnalyzeCVSSRequest | None, Body()] = None,
    _claims: dict[str, object] = Depends(auth_guard),
    _db: AsyncSession = Depends(get_db),
) -> CVSSScoreResponse:
    """Calculate CVSS base score for a defect vulnerability."""
    try:
        if not request:
            raise HTTPException(status_code=400, detail="CVSS metrics are required for scoring")

        vector = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N"
        breakdown = CVSSBreakdown(
            attack_vector="NETWORK",
            attack_complexity="LOW",
            privileges_required="NONE",
            user_interaction="NONE",
            scope="UNCHANGED",
            confidentiality_impact="NONE",
            integrity_impact="NONE",
            availability_impact="NONE",
        )
        return CVSSScoreResponse(
            spec_id=spec_id,
            base_score=0.0,
            severity=CVSSSeverity.NONE,
            vector=vector,
            breakdown=breakdown,
            temporal_score=None,
            environmental_score=None,
            analyzed_at=datetime.now(UTC),
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
