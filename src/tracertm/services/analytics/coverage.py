"""Coverage analytics module."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class CoverageType(StrEnum):
    """Coverage measurement types (DO-178C levels)."""

    STATEMENT = "statement"
    BRANCH = "branch"
    CONDITION = "condition"
    MCDC = "mcdc"
    PATH = "path"
    MUTATION = "mutation"


class SafetyLevel(StrEnum):
    """Safety integrity levels (combined from multiple standards)."""

    ASIL_D = "asil_d"
    ASIL_C = "asil_c"
    ASIL_B = "asil_b"
    ASIL_A = "asil_a"
    QM = "qm"
    DAL_A = "dal_a"
    DAL_B = "dal_b"
    DAL_C = "dal_c"
    DAL_D = "dal_d"
    DAL_E = "dal_e"
    CLASS_A = "class_a"
    CLASS_B = "class_b"
    CLASS_C = "class_c"
    NONE = "none"


class CoverageGap(BaseModel):
    """Identified coverage gap in traceability."""

    gap_type: str
    item_id: str
    item_type: str
    severity: str
    expected_coverage_type: CoverageType | None = None
    current_coverage: float
    required_coverage: float
    safety_level: SafetyLevel | None = None
    suggestion: str


class CoverageGapAnalyzer:
    """Analyzes traceability coverage gaps."""

    SAFETY_COVERAGE_REQUIREMENTS: dict[SafetyLevel, dict[CoverageType, int]] = {
        SafetyLevel.DAL_A: {CoverageType.MCDC: 100, CoverageType.BRANCH: 100, CoverageType.STATEMENT: 100},
        SafetyLevel.DAL_B: {CoverageType.BRANCH: 100, CoverageType.STATEMENT: 100},
        SafetyLevel.DAL_C: {CoverageType.STATEMENT: 100},
        SafetyLevel.ASIL_D: {CoverageType.MCDC: 100, CoverageType.BRANCH: 100},
        SafetyLevel.ASIL_C: {CoverageType.BRANCH: 100},
        SafetyLevel.ASIL_B: {CoverageType.STATEMENT: 100},
        SafetyLevel.CLASS_C: {CoverageType.BRANCH: 100, CoverageType.STATEMENT: 100},
    }

    def analyze_gaps(
        self,
        requirements: list[dict[str, Any]],
        tests: list[dict[str, Any]],
        trace_links: list[dict[str, Any]],
        safety_level: SafetyLevel | None = None,
    ) -> list[CoverageGap]:
        """Analyze coverage gaps in traceability matrix."""
        covered_reqs, linked_tests = self._build_trace_sets(trace_links)
        gaps = []
        gaps.extend(self._find_requirement_gaps(requirements, covered_reqs, safety_level))
        gaps.extend(self._find_orphaned_tests(tests, linked_tests))
        gaps.extend(self._find_safety_coverage_gaps(tests, safety_level))
        return gaps

    def _build_trace_sets(self, trace_links: list[dict[str, Any]]) -> tuple[set[str], set[str]]:
        covered_reqs: set[str] = set()
        linked_tests: set[str] = set()
        for link in trace_links:
            if link.get("link_type") != "verifies":
                continue
            target_id = link.get("target_id")
            source_id = link.get("source_id")
            if isinstance(target_id, str):
                covered_reqs.add(target_id)
            if isinstance(source_id, str):
                linked_tests.add(source_id)
        return covered_reqs, linked_tests

    def _find_requirement_gaps(
        self,
        requirements: list[dict[str, Any]],
        covered_reqs: set[str],
        safety_level: SafetyLevel | None,
    ) -> list[CoverageGap]:
        gaps: list[CoverageGap] = []
        for req in requirements:
            req_id = req["id"]
            if req_id in covered_reqs:
                continue
            req_safety = req.get("safety_level") or safety_level
            severity = self._gap_severity(req_safety, req.get("criticality"))
            gaps.append(
                CoverageGap(
                    gap_type="no_tests",
                    item_id=req_id,
                    item_type="requirement",
                    severity=severity,
                    current_coverage=0.0,
                    required_coverage=100.0,
                    safety_level=req_safety,
                    suggestion=f"Add test cases to verify requirement {req_id}",
                ),
            )
        return gaps

    def _find_orphaned_tests(self, tests: list[dict[str, Any]], linked_tests: set[str]) -> list[CoverageGap]:
        gaps: list[CoverageGap] = []
        for test in tests:
            test_id = test["id"]
            if test_id in linked_tests:
                continue
            gaps.append(
                CoverageGap(
                    gap_type="orphaned_test",
                    item_id=test_id,
                    item_type="test",
                    severity="low",
                    current_coverage=0.0,
                    required_coverage=0.0,
                    suggestion=f"Link test {test_id} to its corresponding requirement",
                ),
            )
        return gaps

    def _find_safety_coverage_gaps(
        self,
        tests: list[dict[str, Any]],
        safety_level: SafetyLevel | None,
    ) -> list[CoverageGap]:
        if not safety_level:
            return []
        required_coverage = self.SAFETY_COVERAGE_REQUIREMENTS.get(safety_level)
        if not required_coverage:
            return []
        gaps: list[CoverageGap] = []
        for test in tests:
            test_coverage = test.get("coverage", {})
            for coverage_type, required in required_coverage.items():
                actual = test_coverage.get(coverage_type.value, 0)
                if actual >= required:
                    continue
                gaps.append(
                    CoverageGap(
                        gap_type="insufficient_coverage",
                        item_id=test["id"],
                        item_type="test",
                        severity="critical" if coverage_type == CoverageType.MCDC else "high",
                        expected_coverage_type=coverage_type,
                        current_coverage=actual,
                        required_coverage=required,
                        safety_level=safety_level,
                        suggestion=f"Increase {coverage_type.value} coverage from {actual}% to {required}%",
                    ),
                )
        return gaps

    def _gap_severity(self, safety_level: SafetyLevel | None, criticality: str | None) -> str:
        """Determine gap severity based on safety and criticality."""
        if safety_level in {SafetyLevel.DAL_A, SafetyLevel.DAL_B, SafetyLevel.ASIL_D}:
            return "critical"
        if safety_level in {SafetyLevel.ASIL_C, SafetyLevel.CLASS_C} or criticality == "high":
            return "high"
        if criticality == "medium":
            return "medium"
        return "low"


__all__ = [
    "CoverageGap",
    "CoverageGapAnalyzer",
    "CoverageType",
    "SafetyLevel",
]
