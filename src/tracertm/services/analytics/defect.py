"""Defect analytics module (IBM ODC classification)."""

from __future__ import annotations

from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, Field


class ODCDefectType(StrEnum):
    """IBM Orthogonal Defect Classification - Defect Types."""

    FUNCTION = "function"
    INTERFACE = "interface"
    CHECKING = "checking"
    ASSIGNMENT = "assignment"
    TIMING = "timing"
    BUILD = "build"
    DOCUMENTATION = "documentation"
    ALGORITHM = "algorithm"


class ODCTrigger(StrEnum):
    """IBM ODC - What triggered the defect discovery."""

    REVIEW = "review"
    WALKTHROUGH = "walkthrough"
    UNIT_TEST = "unit_test"
    FUNCTION_TEST = "function_test"
    SYSTEM_TEST = "system_test"
    REGRESSION_TEST = "regression_test"
    CUSTOMER_FOUND = "customer_found"
    STATIC_ANALYSIS = "static_analysis"


class ODCImpact(StrEnum):
    """IBM ODC - Customer impact category."""

    INSTALLABILITY = "installability"
    SERVICEABILITY = "serviceability"
    STANDARDS = "standards"
    INTEGRITY = "integrity"
    SECURITY = "security"
    PERFORMANCE = "performance"
    REQUIREMENTS = "requirements"
    USABILITY = "usability"
    ACCESSIBILITY = "accessibility"
    CAPABILITY = "capability"
    RELIABILITY = "reliability"
    MIGRATION = "migration"


class ODCClassification(BaseModel):
    """Complete IBM ODC classification for a defect."""

    defect_type: ODCDefectType
    trigger: ODCTrigger
    impact: ODCImpact
    qualifier: str | None = None
    age: str | None = None
    source: str | None = None
    confidence: float = Field(ge=0, le=1, default=1.0)


class CVSSScore(BaseModel):
    """CVSS v3.1 security vulnerability scoring."""

    base_score: float = Field(ge=0, le=10)
    temporal_score: float | None = Field(None, ge=0, le=10)
    environmental_score: float | None = Field(None, ge=0, le=10)
    severity: str
    vector_string: str
    attack_vector: str
    attack_complexity: str
    privileges_required: str
    user_interaction: str
    scope: str
    confidentiality_impact: str
    integrity_impact: str
    availability_impact: str


class ODCClassifier:
    """IBM Orthogonal Defect Classification system."""

    TYPE_KEYWORDS: ClassVar[dict[ODCDefectType, list[str]]] = {
        ODCDefectType.FUNCTION: ["missing", "function", "feature", "capability", "not implemented"],
        ODCDefectType.INTERFACE: ["interface", "api", "contract", "protocol", "integration"],
        ODCDefectType.CHECKING: ["validation", "check", "verify", "null", "empty", "bounds"],
        ODCDefectType.ASSIGNMENT: ["variable", "assignment", "initialization", "value", "wrong"],
        ODCDefectType.TIMING: ["race", "deadlock", "timeout", "async", "concurrent", "thread"],
        ODCDefectType.BUILD: ["build", "compile", "link", "package", "dependency", "merge"],
        ODCDefectType.DOCUMENTATION: ["documentation", "comment", "readme", "spec"],
        ODCDefectType.ALGORITHM: ["algorithm", "logic", "calculation", "formula", "incorrect"],
    }

    IMPACT_KEYWORDS: ClassVar[dict[ODCImpact, list[str]]] = {
        ODCImpact.SECURITY: ["security", "vulnerability", "auth", "permission", "injection", "xss"],
        ODCImpact.PERFORMANCE: ["performance", "slow", "memory", "cpu", "latency", "throughput"],
        ODCImpact.RELIABILITY: ["crash", "hang", "freeze", "restart", "failure", "exception"],
        ODCImpact.USABILITY: ["usability", "ux", "user experience", "confusing", "unclear"],
        ODCImpact.ACCESSIBILITY: ["accessibility", "a11y", "screen reader", "keyboard", "wcag"],
        ODCImpact.CAPABILITY: ["feature", "capability", "function", "missing"],
        ODCImpact.INTEGRITY: ["data", "corruption", "integrity", "consistency", "loss"],
    }

    TRIGGER_KEYWORDS: ClassVar[list[tuple[str, ODCTrigger]]] = [
        ("code review", ODCTrigger.REVIEW),
        ("review", ODCTrigger.REVIEW),
        ("unit test", ODCTrigger.UNIT_TEST),
        ("regression", ODCTrigger.REGRESSION_TEST),
        ("customer", ODCTrigger.CUSTOMER_FOUND),
        ("production", ODCTrigger.CUSTOMER_FOUND),
        ("static", ODCTrigger.STATIC_ANALYSIS),
        ("lint", ODCTrigger.STATIC_ANALYSIS),
        ("system test", ODCTrigger.SYSTEM_TEST),
    ]

    def classify(
        self,
        defect_description: str,
        trigger_context: str | None = None,
        impact_description: str | None = None,
    ) -> ODCClassification:
        """Classify a defect using ODC taxonomy."""
        desc_lower = defect_description.lower()
        defect_type = self._classify_type(desc_lower)
        trigger = self._classify_trigger(trigger_context)
        impact = self._classify_impact(impact_description or desc_lower)
        qualifier = self._determine_qualifier(desc_lower)
        return ODCClassification(
            defect_type=defect_type,
            trigger=trigger,
            impact=impact,
            qualifier=qualifier,
            confidence=0.75,
        )

    def _classify_type(self, description: str) -> ODCDefectType:
        """Classify defect type from description."""
        scores = {}
        for dtype, keywords in self.TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in description)
            scores[dtype] = score
        if max(scores.values()) > 0:
            return max(scores, key=lambda k: scores[k])
        return ODCDefectType.FUNCTION

    def _classify_trigger(self, context: str | None) -> ODCTrigger:
        """Classify how defect was discovered."""
        trigger = ODCTrigger.FUNCTION_TEST
        if not context:
            return trigger
        context_lower = context.lower()
        for keyword, trigger_value in self.TRIGGER_KEYWORDS:
            if keyword in context_lower:
                trigger = trigger_value
                break
        return trigger

    def _classify_impact(self, description: str) -> ODCImpact:
        """Classify customer impact."""
        desc_lower = description.lower()
        scores = {}
        for impact, keywords in self.IMPACT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in desc_lower)
            scores[impact] = score
        if max(scores.values()) > 0:
            return max(scores, key=lambda k: scores[k])
        return ODCImpact.CAPABILITY

    def _determine_qualifier(self, description: str) -> str:
        """Determine if defect is missing, incorrect, or extraneous."""
        if any(kw in description for kw in ["missing", "not implemented", "need", "should have"]):
            return "missing"
        if any(kw in description for kw in ["extra", "unnecessary", "should not", "extraneous"]):
            return "extraneous"
        return "incorrect"


__all__ = [
    "CVSSScore",
    "ODCClassification",
    "ODCClassifier",
    "ODCDefectType",
    "ODCImpact",
    "ODCTrigger",
]
