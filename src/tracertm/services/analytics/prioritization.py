"""Prioritization analytics module."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class PriorityFramework(StrEnum):
    """Prioritization frameworks."""

    WSJF = "wsjf"
    RICE = "rice"
    MOSCOW = "moscow"
    KANO = "kano"
    ICE = "ice"
    VALUE_VS_EFFORT = "value_vs_effort"
    COST_OF_DELAY = "cost_of_delay"


class WSJFScore(BaseModel):
    """WSJF (Weighted Shortest Job First) scoring from SAFe."""

    business_value: int = Field(ge=1, le=10)
    time_criticality: int = Field(ge=1, le=10)
    risk_reduction: int = Field(ge=1, le=10)
    opportunity_enablement: int = Field(ge=1, le=10, default=1)
    job_size: int = Field(ge=1, le=21)
    cost_of_delay: float
    wsjf_score: float
    percentile: int | None = None
    rank: int | None = None


class RICEScore(BaseModel):
    """RICE scoring model."""

    reach: int
    impact: float = Field(ge=0.25, le=3)
    confidence: float = Field(ge=0, le=1)
    effort: int
    rice_score: float
    percentile: int | None = None
    rank: int | None = None


class SemanticSimilarity(BaseModel):
    """Semantic similarity between items."""

    source_id: str
    target_id: str
    similarity_score: float = Field(ge=0, le=1)
    similarity_type: str
    embedding_model: str
    matched_phrases: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class PrioritizationCalculator:
    """Multi-framework prioritization calculator."""

    @staticmethod
    def calculate_wsjf(
        business_value: int,
        time_criticality: int,
        risk_reduction: int,
        job_size: int,
        opportunity_enablement: int = 1,
    ) -> WSJFScore:
        """Calculate WSJF score per SAFe framework."""
        business_value = max(1, min(10, business_value))
        time_criticality = max(1, min(10, time_criticality))
        risk_reduction = max(1, min(10, risk_reduction))
        opportunity_enablement = max(1, min(10, opportunity_enablement))
        job_size = max(1, min(21, job_size))

        cost_of_delay = business_value + time_criticality + risk_reduction + opportunity_enablement
        wsjf_score = cost_of_delay / job_size

        return WSJFScore(
            business_value=business_value,
            time_criticality=time_criticality,
            risk_reduction=risk_reduction,
            opportunity_enablement=opportunity_enablement,
            job_size=job_size,
            cost_of_delay=round(cost_of_delay, 2),
            wsjf_score=round(wsjf_score, 2),
        )

    @staticmethod
    def calculate_rice(reach: int, impact: float, confidence: float, effort: int) -> RICEScore:
        """Calculate RICE score."""
        reach = max(1, reach)
        impact = max(0.25, min(3.0, impact))
        confidence = max(0.0, min(1.0, confidence))
        effort = max(1, effort)

        rice_score = (reach * impact * confidence) / effort

        return RICEScore(
            reach=reach,
            impact=impact,
            confidence=confidence,
            effort=effort,
            rice_score=round(rice_score, 2),
        )

    @staticmethod
    def rank_by_wsjf(items: list[WSJFScore]) -> list[WSJFScore]:
        """Rank items by WSJF and assign percentiles."""
        sorted_items = sorted(items, key=lambda x: x.wsjf_score, reverse=True)
        total = len(sorted_items)

        for i, item in enumerate(sorted_items):
            item.percentile = int(((total - i) / total) * 100)
            item.rank = i + 1

        return sorted_items

    @staticmethod
    def rank_by_rice(items: list[RICEScore]) -> list[RICEScore]:
        """Rank items by RICE and assign percentiles."""
        sorted_items = sorted(items, key=lambda x: x.rice_score, reverse=True)
        total = len(sorted_items)

        for i, item in enumerate(sorted_items):
            item.percentile = int(((total - i) / total) * 100)
            item.rank = i + 1

        return sorted_items

    @staticmethod
    def moscow_categorize(
        items: list[dict[str, Any]],
        must_threshold: float = 0.8,
        should_threshold: float = 0.5,
        could_threshold: float = 0.2,
    ) -> dict[str, list[str]]:
        """Categorize items into MoSCoW buckets based on priority score."""
        result: dict[str, list[str]] = {"must": [], "should": [], "could": [], "wont": []}

        for item in items:
            score = item.get("priority_score", 0)
            item_id = item.get("id", "unknown")

            if score >= must_threshold:
                result["must"].append(item_id)
            elif score >= should_threshold:
                result["should"].append(item_id)
            elif score >= could_threshold:
                result["could"].append(item_id)
            else:
                result["wont"].append(item_id)

        return result


__all__ = [
    "PrioritizationCalculator",
    "PriorityFramework",
    "RICEScore",
    "SemanticSimilarity",
    "WSJFScore",
]
