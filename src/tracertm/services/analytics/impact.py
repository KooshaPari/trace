"""Impact analysis analytics module."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SuspectLinkReason(StrEnum):
    """Reasons for marking a trace link as suspect."""

    UPSTREAM_MODIFIED = "upstream_modified"
    CONTENT_CHANGED = "content_changed"
    STATUS_CHANGED = "status_changed"
    DEPENDENCY_BROKEN = "dependency_broken"
    VERSION_MISMATCH = "version_mismatch"
    COVERAGE_GAP = "coverage_gap"


class ImpactAnalysisResult(BaseModel):
    """Graph-based impact analysis result."""

    source_item_id: str
    direct_impacts: list[str] = Field(default_factory=list)
    transitive_impacts: list[str] = Field(default_factory=list)
    impact_depth: int
    blast_radius: int
    critical_path_items: list[str] = Field(default_factory=list)
    affected_tests: list[str] = Field(default_factory=list)
    affected_documents: list[str] = Field(default_factory=list)
    risk_score: float = Field(ge=0, le=100)
    estimated_effort_hours: float | None = None


class SuspectLink(BaseModel):
    """A suspect traceability link requiring review."""

    link_id: str
    source_id: str
    target_id: str
    reason: SuspectLinkReason
    detected_at: datetime
    source_version_before: int
    source_version_after: int
    change_summary: str
    requires_verification: bool = True
    auto_resolvable: bool = False


class ImpactAnalyzer:
    """Graph-based impact analysis engine."""

    def analyze_impact(
        self,
        source_item_id: str,
        adjacency: dict[str, list[str]],
        item_metadata: dict[str, dict[str, Any]] | None = None,
        max_depth: int = 5,
    ) -> ImpactAnalysisResult:
        """Analyze impact of changes to a source item."""
        (
            direct_impacts,
            transitive_impacts,
            affected_tests,
            affected_docs,
            depth,
        ) = self._collect_impacts(source_item_id, adjacency, item_metadata, max_depth)

        blast_radius = len(direct_impacts) + len(transitive_impacts)
        critical_path = self._find_critical_path(direct_impacts, transitive_impacts, item_metadata)
        risk_score = self._calculate_risk_score(blast_radius, len(critical_path), depth, item_metadata)

        return ImpactAnalysisResult(
            source_item_id=source_item_id,
            direct_impacts=direct_impacts,
            transitive_impacts=transitive_impacts,
            impact_depth=depth,
            blast_radius=blast_radius,
            critical_path_items=critical_path,
            affected_tests=affected_tests,
            affected_documents=affected_docs,
            risk_score=risk_score,
        )

    def _collect_impacts(
        self,
        source_item_id: str,
        adjacency: dict[str, list[str]],
        item_metadata: dict[str, dict[str, Any]] | None,
        max_depth: int,
    ) -> tuple[list[str], list[str], list[str], list[str], int]:
        visited: set[str] = set()
        direct_impacts: list[str] = []
        transitive_impacts: list[str] = []
        affected_tests: list[str] = []
        affected_docs: list[str] = []
        depth = 0
        current_level = [source_item_id]

        while current_level and depth < max_depth:
            next_level = []
            for item_id in current_level:
                if item_id in visited:
                    continue
                visited.add(item_id)
                dependents = adjacency.get(item_id, [])
                next_level.extend(
                    self._process_dependents(
                        dependents=dependents,
                        depth=depth,
                        visited=visited,
                        direct_impacts=direct_impacts,
                        transitive_impacts=transitive_impacts,
                        affected_tests=affected_tests,
                        affected_docs=affected_docs,
                        item_metadata=item_metadata,
                    ),
                )
            current_level = next_level
            depth += 1

        return direct_impacts, transitive_impacts, affected_tests, affected_docs, depth

    def _process_dependents(
        self,
        *,
        dependents: list[str],
        depth: int,
        visited: set[str],
        direct_impacts: list[str],
        transitive_impacts: list[str],
        affected_tests: list[str],
        affected_docs: list[str],
        item_metadata: dict[str, dict[str, Any]] | None,
    ) -> list[str]:
        next_level: list[str] = []
        for dep_id in dependents:
            if dep_id in visited:
                continue
            next_level.append(dep_id)
            self._record_impact(dep_id, depth, direct_impacts, transitive_impacts)
            self._categorize_impact(dep_id, item_metadata, affected_tests, affected_docs)
        return next_level

    def _record_impact(
        self,
        dep_id: str,
        depth: int,
        direct_impacts: list[str],
        transitive_impacts: list[str],
    ) -> None:
        if depth == 0:
            direct_impacts.append(dep_id)
        else:
            transitive_impacts.append(dep_id)

    def _categorize_impact(
        self,
        dep_id: str,
        item_metadata: dict[str, dict[str, Any]] | None,
        affected_tests: list[str],
        affected_docs: list[str],
    ) -> None:
        if not item_metadata:
            return
        meta = item_metadata.get(dep_id, {})
        item_type = meta.get("type", "")
        item_type_lower = item_type.lower()
        if "test" in item_type_lower:
            affected_tests.append(dep_id)
        elif "doc" in item_type_lower:
            affected_docs.append(dep_id)

    def _find_critical_path(
        self,
        direct_impacts: list[str],
        transitive_impacts: list[str],
        item_metadata: dict[str, dict[str, Any]] | None,
    ) -> list[str]:
        if not item_metadata:
            return []
        critical_path: list[str] = []
        for item_id in direct_impacts + transitive_impacts:
            meta = item_metadata.get(item_id, {})
            if meta.get("criticality", "") in {"high", "critical"}:
                critical_path.append(item_id)
        return critical_path

    def _calculate_risk_score(
        self,
        blast_radius: int,
        critical_count: int,
        depth: int,
        _metadata: dict[str, dict[str, Any]] | None,
    ) -> float:
        """Calculate composite risk score."""
        radius_risk = min(40, blast_radius * 2)
        critical_risk = min(30, critical_count * 10)
        depth_risk = min(20, depth * 4)
        base_risk = 10
        return min(100, radius_risk + critical_risk + depth_risk + base_risk)


class SuspectLinkDetector:
    """Detects suspect traceability links after changes."""

    def detect_suspect_links(
        self,
        links: list[dict[str, Any]],
        item_versions: dict[str, int],
        recent_changes: list[dict[str, Any]],
    ) -> list[SuspectLink]:
        """Detect links that may be invalid after recent changes."""
        suspect_links = []
        changed_items = {c["item_id"]: c for c in recent_changes}

        for link in links:
            link_id = link.get("id", "")
            source_id = link.get("source_id", "")
            target_id = link.get("target_id", "")
            link_source_version = link.get("source_version", 0)

            current_version = item_versions.get(source_id, 0)

            if source_id in changed_items:
                change = changed_items[source_id]

                if current_version > link_source_version:
                    suspect_links.append(
                        SuspectLink(
                            link_id=link_id,
                            source_id=source_id,
                            target_id=target_id,
                            reason=SuspectLinkReason.UPSTREAM_MODIFIED,
                            detected_at=datetime.now(UTC),
                            source_version_before=link_source_version,
                            source_version_after=current_version,
                            change_summary=change.get("summary", "Source item modified"),
                            requires_verification=True,
                            auto_resolvable=False,
                        ),
                    )

                elif change.get("change_type") == "status_changed":
                    suspect_links.append(
                        SuspectLink(
                            link_id=link_id,
                            source_id=source_id,
                            target_id=target_id,
                            reason=SuspectLinkReason.STATUS_CHANGED,
                            detected_at=datetime.now(UTC),
                            source_version_before=link_source_version,
                            source_version_after=current_version,
                            change_summary=f"Status changed: {change.get('old_status')} -> {change.get('new_status')}",
                            requires_verification=True,
                            auto_resolvable=change.get("new_status") == "approved",
                        ),
                    )

        return suspect_links


__all__ = [
    "ImpactAnalysisResult",
    "ImpactAnalyzer",
    "SuspectLink",
    "SuspectLinkDetector",
    "SuspectLinkReason",
]
