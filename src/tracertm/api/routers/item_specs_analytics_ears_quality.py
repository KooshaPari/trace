"""EARS and Quality analysis endpoints.

Provides EARS pattern analysis and ISO 29148 quality scoring endpoints.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from tracertm.api.deps import auth_guard, get_db
from tracertm.schemas.spec_analytics import (
    AnalyzeEARSRequest,
    AnalyzeQualityRequest,
    EARSAnalysisResponse,
    EARSComponent,
    EARSPatternType,
    QualityGrade,
    QualityScoreResponse,
)
from tracertm.services import spec_analytics_service

router = APIRouter(prefix="/analytics", tags=["Item Spec Analytics - EARS & Quality"])


@router.post(
    "/requirements/{spec_id}/analyze/ears",
    response_model=EARSAnalysisResponse,
)
async def analyze_ears_pattern(
    _project_id: Annotated[str, Path(description="Project ID")],
    spec_id: Annotated[str, Path(description="Requirement spec ID")],
    request: Annotated[AnalyzeEARSRequest | None, Body()] = None,
    _claims: dict[str, object] = Depends(auth_guard),
    _db: AsyncSession = Depends(get_db),
) -> EARSAnalysisResponse:
    """Analyze a requirement using the EARS (Enhanced Artifact Requirements Styles) pattern."""
    try:
        requirement_text = ""
        if request and hasattr(request, "content"):
            requirement_text = request.content

        if not requirement_text:
            raise HTTPException(status_code=400, detail="Requirement content is required for EARS analysis")

        result = spec_analytics_service.analyze_requirement(requirement_text)
        ears_analysis = result.get("ears_analysis", {})

        raw_pattern = ears_analysis.get("pattern_type", "complex")
        try:
            pattern_type = EARSPatternType(raw_pattern)
        except ValueError:
            pattern_type = EARSPatternType.COMPLEX

        raw_components = ears_analysis.get("components", {})
        components = {k: EARSComponent(**v) if isinstance(v, dict) else v for k, v in raw_components.items()}

        suggestions: list[str] = []
        for key in ("validation_issues", "improvement_suggestions", "ambiguous_terms"):
            val = ears_analysis.get(key, [])
            if isinstance(val, list):
                suggestions.extend(str(x) for x in val)
            elif val:
                suggestions.append(str(val))

        return EARSAnalysisResponse(
            spec_id=spec_id,
            pattern_type=pattern_type,
            confidence=float(ears_analysis.get("confidence", 0.0)),
            trigger=ears_analysis.get("trigger"),
            precondition=ears_analysis.get("precondition"),
            postcondition=ears_analysis.get("postcondition"),
            system_name=ears_analysis.get("system_name"),
            formal_structure=ears_analysis.get("formal_structure"),
            components=components,
            suggestions=suggestions,
            is_well_formed=bool(ears_analysis.get("is_valid", False)),
            analyzed_at=datetime.now(UTC),
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/requirements/{spec_id}/analyze/quality",
    response_model=QualityScoreResponse,
)
async def analyze_quality_dimensions(
    _project_id: Annotated[str, Path(description="Project ID")],
    spec_id: Annotated[str, Path(description="Requirement spec ID")],
    request: Annotated[AnalyzeQualityRequest | None, Body()] = None,
    _claims: dict[str, object] = Depends(auth_guard),
    _db: AsyncSession = Depends(get_db),
) -> QualityScoreResponse:
    """Analyze requirement quality using ISO 29148 quality dimensions."""
    try:
        requirement_text = ""
        if request and hasattr(request, "content"):
            requirement_text = request.content

        if not requirement_text:
            raise HTTPException(status_code=400, detail="Requirement content is required for quality analysis")

        result = spec_analytics_service.analyze_requirement(requirement_text)
        quality_analysis = result.get("quality_analysis", {})

        raw_grade = quality_analysis.get("grade", "F")
        grade = QualityGrade(raw_grade) if isinstance(raw_grade, str) else QualityGrade.F
        dims = quality_analysis.get("dimension_scores", quality_analysis.get("dimensions", {}))
        return QualityScoreResponse(
            spec_id=spec_id,
            dimensions={k: float(v) for k, v in dims.items()} if isinstance(dims, dict) else {},
            dimension_details=[],
            overall_score=float(quality_analysis.get("overall_score", 0.0)),
            grade=grade,
            issues=[],
            critical_issues_count=int(quality_analysis.get("critical_issues_count", 0)),
            warning_issues_count=int(quality_analysis.get("warning_issues_count", 0)),
            top_improvement_areas=quality_analysis.get(
                "improvement_priority",
                quality_analysis.get("top_improvement_areas", []),
            )
            or [],
            analyzed_at=datetime.now(UTC),
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
