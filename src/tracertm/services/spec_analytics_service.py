"""Enhanced Specification Analytics Service V2.

A comprehensive, deeply-integrated analytics engine for specification objects
inspired by smart contract/blockchain/NFT entity patterns.

This service provides:
1. EARS Pattern Analysis with formal validation
2. ISO 29148 Quality Scoring (8 dimensions)
3. Cryptographic Version Chain (blockchain-style audit)
4. Merkle Proof Generation for baseline verification
5. Content Addressing (IPFS-style CIDs)
6. Flakiness Detection (Meta probabilistic model)
7. Orthogonal Defect Classification (IBM ODC)
8. CVSS Security Scoring
9. WSJF/RICE/MoSCoW Prioritization
10. Semantic Similarity Detection
11. Graph-based Impact Analysis
12. Suspect Link Detection
13. Formal Constraint Verification (Z3-style)
14. Coverage Gap Analysis
15. Test Oracle Pattern Detection

Functional Requirements: FR-QUAL-010
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from tracertm.services.analytics import (
    ContentAddress,
    CoverageGap,
    CoverageGapAnalyzer,
    EARSPatternAnalyzer,
    FlakinessAnalysis,
    FlakinessDetector,
    ImpactAnalysisResult,
    ImpactAnalyzer,
    MerkleProof,
    MerkleTree,
    ODCClassification,
    ODCClassifier,
    PrioritizationCalculator,
    RequirementQualityAnalyzer,
    RICEScore,
    SafetyLevel,
    SuspectLink,
    SuspectLinkDetector,
    VersionBlock,
    VersionChain,
    WSJFScore,
)


class SpecAnalyticsServiceFacade:
    """Comprehensive specification analytics service facade.

    Provides unified access to all analytics capabilities via submodules.
    """

    def __init__(self) -> None:
        """Initialize."""
        self.ears_analyzer = EARSPatternAnalyzer()
        self.quality_analyzer = RequirementQualityAnalyzer()
        self.flakiness_detector = FlakinessDetector()
        self.odc_classifier = ODCClassifier()
        self.impact_analyzer = ImpactAnalyzer()
        self.suspect_link_detector = SuspectLinkDetector()
        self.coverage_gap_analyzer = CoverageGapAnalyzer()

    def analyze_requirement(
        self,
        requirement_text: str,
        related_requirements: list[str] | None = None,
        linked_tests: list[str] | None = None,
        linked_items: dict[str, list[str]] | None = None,
    ) -> dict[str, Any]:
        """Comprehensive requirement analysis."""
        ears_result = self.ears_analyzer.analyze(requirement_text)
        quality_result = self.quality_analyzer.analyze(
            requirement_text,
            related_requirements,
            linked_tests,
            linked_items,
        )

        return {
            "ears_analysis": ears_result.model_dump(),
            "quality_analysis": quality_result.model_dump(),
            "overall_health": {
                "is_well_formed": ears_result.is_valid,
                "pattern_type": ears_result.pattern_type.value,
                "quality_grade": quality_result.grade,
                "quality_score": quality_result.overall_score,
                "total_issues": len(ears_result.validation_issues) + len(quality_result.issues),
                "needs_attention": (not ears_result.is_valid or quality_result.grade in {"D", "F"}),
                "improvement_priorities": quality_result.improvement_priority,
            },
            "formal_structure": ears_result.formal_structure,
            "ambiguous_terms": ears_result.ambiguous_terms,
        }

    def batch_analyze_requirements(self, requirements: list[dict[str, str]]) -> list[dict[str, Any]]:
        """Analyze multiple requirements at once."""
        return [{"id": req.get("id", ""), **self.analyze_requirement(req.get("text", ""))} for req in requirements]

    def create_genesis_block(
        self,
        content: dict[str, Any],
        author_id: str,
        change_summary: str = "Initial creation",
    ) -> VersionBlock:
        """Create first block in version chain."""
        return VersionChain.create_genesis_block(content, author_id, change_summary)

    def add_version_block(
        self,
        previous_block: VersionBlock,
        content: dict[str, Any],
        author_id: str,
        change_type: str,
        change_summary: str,
    ) -> VersionBlock:
        """Add new block to version chain."""
        return VersionChain.add_block(previous_block, content, author_id, change_type, change_summary)

    def verify_version_chain(self, blocks: list[VersionBlock]) -> tuple[bool, list[str]]:
        """Verify integrity of version chain."""
        return VersionChain.verify_chain(blocks)

    def create_merkle_tree(self, items: list[tuple[str, str]]) -> MerkleTree:
        """Create Merkle tree from items for baseline verification."""
        return MerkleTree(items)

    def get_merkle_proof(self, tree: MerkleTree, item_id: str) -> MerkleProof | None:
        """Get inclusion proof for an item."""
        return tree.get_proof(item_id)

    def verify_merkle_proof(self, proof: MerkleProof) -> bool:
        """Verify Merkle inclusion proof."""
        return MerkleTree.verify_proof(proof)

    def analyze_test_flakiness(self, run_history: list[dict[str, Any]], window_size: int = 30) -> FlakinessAnalysis:
        """Analyze test flakiness from execution history."""
        return self.flakiness_detector.analyze(run_history, window_size)

    def batch_analyze_flakiness(self, tests: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Analyze flakiness for multiple tests."""
        results = []
        for test in tests:
            analysis = self.flakiness_detector.analyze(test.get("run_history", []))
            results.append({"test_id": test.get("id", ""), "flakiness_analysis": analysis.model_dump()})
        return results

    def classify_defect(
        self,
        description: str,
        trigger_context: str | None = None,
        impact_description: str | None = None,
    ) -> ODCClassification:
        """Classify defect using IBM ODC taxonomy."""
        return self.odc_classifier.classify(description, trigger_context, impact_description)

    def calculate_wsjf(
        self,
        business_value: int,
        time_criticality: int,
        risk_reduction: int,
        job_size: int,
        opportunity_enablement: int = 1,
    ) -> WSJFScore:
        """Calculate WSJF prioritization score."""
        return PrioritizationCalculator.calculate_wsjf(
            business_value,
            time_criticality,
            risk_reduction,
            job_size,
            opportunity_enablement,
        )

    def calculate_rice(self, reach: int, impact: float, confidence: float, effort: int) -> RICEScore:
        """Calculate RICE prioritization score."""
        return PrioritizationCalculator.calculate_rice(reach, impact, confidence, effort)

    def rank_items_wsjf(self, items: list[WSJFScore]) -> list[WSJFScore]:
        """Rank items by WSJF score."""
        return PrioritizationCalculator.rank_by_wsjf(items)

    def rank_items_rice(self, items: list[RICEScore]) -> list[RICEScore]:
        """Rank items by RICE score."""
        return PrioritizationCalculator.rank_by_rice(items)

    def analyze_change_impact(
        self,
        source_item_id: str,
        adjacency: dict[str, list[str]],
        item_metadata: dict[str, dict[str, Any]] | None = None,
        max_depth: int = 5,
    ) -> ImpactAnalysisResult:
        """Analyze impact of changing an item."""
        return self.impact_analyzer.analyze_impact(source_item_id, adjacency, item_metadata, max_depth)

    def detect_suspect_links(
        self,
        links: list[dict[str, Any]],
        item_versions: dict[str, int],
        recent_changes: list[dict[str, Any]],
    ) -> list[SuspectLink]:
        """Detect suspect trace links after changes."""
        return self.suspect_link_detector.detect_suspect_links(links, item_versions, recent_changes)

    def analyze_coverage_gaps(
        self,
        requirements: list[dict[str, Any]],
        tests: list[dict[str, Any]],
        trace_links: list[dict[str, Any]],
        safety_level: SafetyLevel | None = None,
    ) -> list[CoverageGap]:
        """Analyze traceability coverage gaps."""
        return self.coverage_gap_analyzer.analyze_gaps(requirements, tests, trace_links, safety_level)

    @staticmethod
    def generate_content_address(content: dict[str, Any], content_type: str = "application/json") -> ContentAddress:
        """Generate IPFS-style content address for specification."""
        content_str = json.dumps(content, sort_keys=True, default=str)
        content_bytes = content_str.encode()
        cid = hashlib.sha256(content_bytes).hexdigest()

        return ContentAddress(
            cid=f"tracertm:{cid}",
            algorithm="sha256",
            size_bytes=len(content_bytes),
            content_type=content_type,
            created_at=datetime.now(UTC),
        )

    @staticmethod
    def verify_content_address(content: dict[str, Any], expected_cid: str) -> bool:
        """Verify content matches its address."""
        content_str = json.dumps(content, sort_keys=True, default=str)
        actual_cid = f"tracertm:{hashlib.sha256(content_str.encode()).hexdigest()}"
        return actual_cid == expected_cid


SpecAnalyticsService = SpecAnalyticsServiceFacade

spec_analytics = SpecAnalyticsServiceFacade()
spec_analytics_service = spec_analytics


def analyze_requirement(text: str, **kwargs: Any) -> dict[str, Any]:
    """Convenience function for requirement analysis."""
    return spec_analytics.analyze_requirement(text, **kwargs)


def analyze_flakiness(run_history: list[dict[str, Any]]) -> FlakinessAnalysis:
    """Convenience function for flakiness analysis."""
    return spec_analytics.analyze_test_flakiness(run_history)


def calculate_wsjf(**kwargs: Any) -> WSJFScore:
    """Convenience function for WSJF calculation."""
    return spec_analytics.calculate_wsjf(**kwargs)


def calculate_rice(**kwargs: Any) -> RICEScore:
    """Convenience function for RICE calculation."""
    return spec_analytics.calculate_rice(**kwargs)
