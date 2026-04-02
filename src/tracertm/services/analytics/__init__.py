"""Specification analytics module.

Provides comprehensive analytics for specification objects including:
- EARS pattern analysis
- ISO 29148 quality scoring
- Cryptographic version chains
- Merkle proof generation
- Flakiness detection
- ODC defect classification
- Prioritization (WSJF/RICE)
- Impact analysis
- Suspect link detection
- Coverage gap analysis
"""

from tracertm.services.analytics.coverage import (
    CoverageGap,
    CoverageGapAnalyzer,
    CoverageType,
    SafetyLevel,
)
from tracertm.services.analytics.defect import (
    CVSSScore,
    ODCClassification,
    ODCClassifier,
    ODCDefectType,
    ODCImpact,
    ODCTrigger,
)
from tracertm.services.analytics.ears_quality import (
    EARSAnalysisResult,
    EARSComponents,
    EARSPatternAnalyzer,
    EARSPatternType,
    QualityDimension,
    QualityIssue,
    QualityScore,
    RequirementQualityAnalyzer,
    TestOracleType,
    VerificationMethod,
)
from tracertm.services.analytics.flakiness import (
    FlakinessAnalysis,
    FlakinessDetector,
    FlakinessPattern,
    FlakinessSeverity,
)
from tracertm.services.analytics.impact import (
    ImpactAnalysisResult,
    ImpactAnalyzer,
    SuspectLink,
    SuspectLinkDetector,
    SuspectLinkReason,
)
from tracertm.services.analytics.prioritization import (
    PrioritizationCalculator,
    PriorityFramework,
    RICEScore,
    SemanticSimilarity,
    WSJFScore,
)
from tracertm.services.analytics.version import (
    ContentAddress,
    MerkleProof,
    MerkleTree,
    VersionBlock,
    VersionChain,
)

__all__ = [
    # Coverage
    "CoverageGap",
    "CoverageGapAnalyzer",
    "CoverageType",
    "SafetyLevel",
    # EARS Quality
    "EARSAnalysisResult",
    "EARSComponents",
    "EARSPatternAnalyzer",
    "EARSPatternType",
    "QualityDimension",
    "QualityIssue",
    "QualityScore",
    "RequirementQualityAnalyzer",
    "TestOracleType",
    "VerificationMethod",
    # Version
    "ContentAddress",
    "MerkleProof",
    "MerkleTree",
    "VersionBlock",
    "VersionChain",
    # Defect
    "CVSSScore",
    "ODCClassification",
    "ODCClassifier",
    "ODCDefectType",
    "ODCImpact",
    "ODCTrigger",
    # Flakiness
    "FlakinessAnalysis",
    "FlakinessDetector",
    "FlakinessPattern",
    "FlakinessSeverity",
    # Impact
    "ImpactAnalysisResult",
    "ImpactAnalyzer",
    "SuspectLink",
    "SuspectLinkDetector",
    "SuspectLinkReason",
    # Prioritization
    "PrioritizationCalculator",
    "PriorityFramework",
    "RICEScore",
    "SemanticSimilarity",
    "WSJFScore",
]
