"""Flakiness analytics module."""

from __future__ import annotations

import math
import statistics
from collections import Counter
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

FLAKINESS_VARIANCE_MIN_SAMPLES = 2
FLAKINESS_QUARANTINE_FAILURES = 3
FLAKINESS_QUARANTINE_SCORE = 0.15
FLAKINESS_QUARANTINE_RATE = 0.1
FLAKINESS_ENTROPY_MIN_LENGTH = 2
FLAKINESS_TRANSITION_MIN_LENGTH = 2
FLAKINESS_DURATION_MIN_SAMPLES = 5
FLAKINESS_DURATION_CV_THRESHOLD = 0.5
FLAKINESS_RACE_MIN_LENGTH = 5
FLAKINESS_STABLE_PASS_THRESHOLD = 15
FLAKINESS_STABLE_FAILURE_RATE = 0.1
FLAKINESS_BROKEN_FAILURE_THRESHOLD = 8
FLAKINESS_VARIANCE_THRESHOLD = 0.5
FLAKINESS_CLUSTER_MIN_FAILURES = 2
FLAKINESS_SEVERITY_STABLE_MAX = 0.01
FLAKINESS_SEVERITY_LOW_MAX = 0.05
FLAKINESS_SEVERITY_MEDIUM_MAX = 0.15
FLAKINESS_SEVERITY_HIGH_MAX = 0.30


class FlakinessSeverity(StrEnum):
    """Flakiness severity levels (Meta model)."""

    STABLE = "stable"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FlakinessPattern(StrEnum):
    """Detected flakiness patterns."""

    ORDER_DEPENDENT = "order_dependent"
    TIME_DEPENDENT = "time_dependent"
    RESOURCE_DEPENDENT = "resource_dependent"
    ENVIRONMENT_DEPENDENT = "environment_dependent"
    DATA_DEPENDENT = "data_dependent"
    RACE_CONDITION = "race_condition"
    EXTERNAL_DEPENDENCY = "external_dependency"
    MEMORY_PRESSURE = "memory_pressure"
    NETWORK_INSTABILITY = "network_instability"
    ASYNC_TIMING = "async_timing"


class FlakinessAnalysis(BaseModel):
    """Complete flakiness analysis result."""

    flakiness_score: float = Field(ge=0, le=1)
    severity: FlakinessSeverity
    detected_patterns: list[FlakinessPattern] = Field(default_factory=list)
    failure_rate_24h: float | None = None
    failure_rate_7d: float | None = None
    failure_rate_30d: float | None = None
    entropy_score: float
    transition_count: int
    consecutive_failures_max: int
    consecutive_passes_max: int
    quarantine_recommended: bool
    suggested_fix_category: str | None = None
    confidence: float = Field(ge=0, le=1)
    run_time_variance: float | None = None
    failure_clustering_score: float | None = None


class FlakinessDetector:
    """Meta-style probabilistic flakiness detector."""

    def analyze(self, run_history: list[dict[str, Any]], window_size: int = 30) -> FlakinessAnalysis:
        """Analyze test flakiness from execution history."""
        if not run_history:
            return FlakinessAnalysis(
                flakiness_score=0.0,
                severity=FlakinessSeverity.STABLE,
                entropy_score=0.0,
                transition_count=0,
                consecutive_failures_max=0,
                consecutive_passes_max=0,
                quarantine_recommended=False,
                confidence=0.0,
            )

        recent = run_history[-window_size:]
        statuses = [r.get("status", "unknown") for r in recent]
        timestamps = [r.get("timestamp") for r in recent]
        durations = [r.get("duration_ms", 0) for r in recent if r.get("duration_ms")]

        total = len(statuses)
        failures = sum(1 for s in statuses if s in {"failed", "error", "flaky"})
        failure_rate = failures / total if total > 0 else 0

        entropy = self._calculate_entropy(statuses)
        transition_count = self._count_transitions(statuses)

        max_failures = self._max_consecutive(statuses, {"failed", "error", "flaky"})
        max_passes = self._max_consecutive(statuses, {"passed"})

        duration_variance = None
        if durations and len(durations) > FLAKINESS_VARIANCE_MIN_SAMPLES:
            mean_duration = statistics.mean(durations)
            if mean_duration > 0:
                std_duration = statistics.stdev(durations)
                duration_variance = std_duration / mean_duration

        patterns = self._detect_patterns(recent, durations, timestamps)

        flakiness_score = self._calculate_flakiness_score(
            failure_rate, entropy, max_failures, max_passes, duration_variance
        )

        severity = self._score_to_severity(flakiness_score)

        clustering_score = self._calculate_failure_clustering([
            (r.get("timestamp"), r.get("status") or "") for r in recent
        ])

        quarantine_recommended = (
            severity in {FlakinessSeverity.HIGH, FlakinessSeverity.CRITICAL}
            or max_failures >= FLAKINESS_QUARANTINE_FAILURES
            or (flakiness_score > FLAKINESS_QUARANTINE_SCORE and failure_rate > FLAKINESS_QUARANTINE_RATE)
        )

        suggested_fix = self._suggest_fix(patterns)
        confidence = min(1.0, total / 30)

        return FlakinessAnalysis(
            flakiness_score=round(flakiness_score, 4),
            severity=severity,
            detected_patterns=patterns,
            failure_rate_7d=round(failure_rate, 4),
            failure_rate_30d=round(failure_rate, 4),
            entropy_score=round(entropy, 4),
            transition_count=transition_count,
            consecutive_failures_max=max_failures,
            consecutive_passes_max=max_passes,
            quarantine_recommended=quarantine_recommended,
            suggested_fix_category=suggested_fix,
            confidence=round(confidence, 2),
            run_time_variance=round(duration_variance, 4) if duration_variance else None,
            failure_clustering_score=round(clustering_score, 4) if clustering_score else None,
        )

    def _calculate_entropy(self, statuses: list[str]) -> float:
        """Calculate Shannon entropy of status sequence."""
        if len(statuses) < FLAKINESS_ENTROPY_MIN_LENGTH:
            return 0.0
        counter = Counter(statuses)
        total = len(statuses)
        entropy = 0.0
        for count in counter.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        max_entropy = math.log2(len(counter)) if len(counter) > 1 else 1
        return entropy / max_entropy if max_entropy > 0 else 0.0

    def _count_transitions(self, statuses: list[str]) -> int:
        """Count state transitions in sequence."""
        if len(statuses) < FLAKINESS_TRANSITION_MIN_LENGTH:
            return 0
        return sum(1 for i in range(1, len(statuses)) if statuses[i] != statuses[i - 1])

    def _max_consecutive(self, statuses: list[str], target: set[str]) -> int:
        """Find maximum consecutive occurrences of target statuses."""
        max_count = 0
        current = 0
        for status in statuses:
            if status in target:
                current += 1
                max_count = max(max_count, current)
            else:
                current = 0
        return max_count

    def _detect_patterns(
        self,
        runs: list[dict[str, Any]],
        durations: list[float],
        _timestamps: list[object],
    ) -> list[FlakinessPattern]:
        """Detect specific flakiness patterns."""
        patterns = []
        if durations and len(durations) > FLAKINESS_DURATION_MIN_SAMPLES:
            mean_d = statistics.mean(durations)
            if mean_d > 0:
                cv = statistics.stdev(durations) / mean_d
                if cv > FLAKINESS_DURATION_CV_THRESHOLD:
                    patterns.append(FlakinessPattern.RESOURCE_DEPENDENT)

        statuses_raw = [r.get("status") for r in runs]
        statuses: list[str] = [s for s in statuses_raw if isinstance(s, str)]
        if len(statuses) > FLAKINESS_RACE_MIN_LENGTH:
            transitions = self._count_transitions(statuses)
            if transitions > len(statuses) * 0.6:
                patterns.append(FlakinessPattern.RACE_CONDITION)

        return patterns

    def _calculate_flakiness_score(
        self,
        failure_rate: float,
        entropy: float,
        max_failures: int,
        max_passes: int,
        duration_variance: float | None,
    ) -> float:
        """Calculate composite flakiness score."""
        base_score = failure_rate
        entropy_factor = 1 + (entropy * 0.5)

        if max_passes > FLAKINESS_STABLE_PASS_THRESHOLD and failure_rate < FLAKINESS_STABLE_FAILURE_RATE:
            consistency_factor = 0.4
        elif max_failures > FLAKINESS_BROKEN_FAILURE_THRESHOLD:
            consistency_factor = 0.3
        else:
            consistency_factor = 1.0

        variance_factor = 1.0
        if duration_variance and duration_variance > FLAKINESS_VARIANCE_THRESHOLD:
            variance_factor = 1.2

        score = base_score * entropy_factor * consistency_factor * variance_factor
        return min(1.0, max(0.0, score))

    def _calculate_failure_clustering(self, runs: list[tuple[Any, str]]) -> float | None:
        """Calculate temporal clustering of failures."""
        failures = [i for i, (_, status) in enumerate(runs) if status in {"failed", "error", "flaky"}]
        if len(failures) < FLAKINESS_CLUSTER_MIN_FAILURES:
            return None

        gaps = [failures[i + 1] - failures[i] for i in range(len(failures) - 1)]
        if not gaps:
            return None

        mean_gap = statistics.mean(gaps)
        if mean_gap > 0:
            std_gap = statistics.stdev(gaps) if len(gaps) > 1 else 0
            return 1.0 - min(1.0, std_gap / mean_gap)

        return None

    def _score_to_severity(self, score: float) -> FlakinessSeverity:
        """Map score to severity level."""
        if score < FLAKINESS_SEVERITY_STABLE_MAX:
            return FlakinessSeverity.STABLE
        if score < FLAKINESS_SEVERITY_LOW_MAX:
            return FlakinessSeverity.LOW
        if score < FLAKINESS_SEVERITY_MEDIUM_MAX:
            return FlakinessSeverity.MEDIUM
        if score < FLAKINESS_SEVERITY_HIGH_MAX:
            return FlakinessSeverity.HIGH
        return FlakinessSeverity.CRITICAL

    def _suggest_fix(self, patterns: list[FlakinessPattern]) -> str | None:
        """Suggest fix based on detected patterns."""
        suggestions = {
            FlakinessPattern.RACE_CONDITION: "Add synchronization barriers or increase wait timeouts",
            FlakinessPattern.RESOURCE_DEPENDENT: "Reduce resource contention, add retry logic, or isolate test",
            FlakinessPattern.TIME_DEPENDENT: "Mock time-dependent behavior or use fixed test timestamps",
            FlakinessPattern.EXTERNAL_DEPENDENCY: "Mock external services or add circuit breakers",
            FlakinessPattern.ORDER_DEPENDENT: "Ensure test isolation with proper setup/teardown",
            FlakinessPattern.ASYNC_TIMING: "Use proper async waits instead of fixed delays",
            FlakinessPattern.NETWORK_INSTABILITY: "Add network retry logic or mock network calls",
        }
        for pattern in patterns:
            if pattern in suggestions:
                return suggestions[pattern]
        return None


__all__ = [
    "FlakinessAnalysis",
    "FlakinessDetector",
    "FlakinessPattern",
    "FlakinessSeverity",
]
