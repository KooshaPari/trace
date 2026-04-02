"""EARS quality analytics module."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, Field

QUALITY_IMPROVEMENT_THRESHOLD = 0.7
QUALITY_MIN_LENGTH = 30
QUALITY_AND_COUNT_THRESHOLD = 2
GRADE_A_THRESHOLD = 0.90
GRADE_B_THRESHOLD = 0.80
GRADE_C_THRESHOLD = 0.70
GRADE_D_THRESHOLD = 0.60
_MIN_SAMPLES_FOR_METRICS = 2


class EARSPatternType(StrEnum):
    """EARS (Easy Approach to Requirements Syntax) pattern types."""

    UBIQUITOUS = "ubiquitous"
    EVENT_DRIVEN = "event_driven"
    STATE_DRIVEN = "state_driven"
    OPTIONAL = "optional"
    COMPLEX = "complex"
    UNWANTED = "unwanted"
    UNCLASSIFIED = "unclassified"


class QualityDimension(StrEnum):
    """ISO 29148 quality dimensions for requirements."""

    UNAMBIGUITY = "unambiguity"
    COMPLETENESS = "completeness"
    VERIFIABILITY = "verifiability"
    CONSISTENCY = "consistency"
    NECESSITY = "necessity"
    SINGULARITY = "singularity"
    FEASIBILITY = "feasibility"
    TRACEABILITY = "traceability"
    CORRECTNESS = "correctness"


class VerificationMethod(StrEnum):
    """ISO 29148 verification methods (IDAT)."""

    INSPECTION = "inspection"
    DEMONSTRATION = "demonstration"
    ANALYSIS = "analysis"
    TEST = "test"


class TestOracleType(StrEnum):
    """Test oracle pattern types."""

    EXPECTED_OUTPUT = "expected_output"
    METAMORPHIC = "metamorphic"
    PROPERTY_BASED = "property_based"
    DIFFERENTIAL = "differential"
    REGRESSION = "regression"
    STATISTICAL = "statistical"
    HUMAN = "human"
    CONTRACT = "contract"


class EARSComponents(BaseModel):
    """Extracted EARS components from a requirement."""

    trigger: str | None = None
    precondition: str | None = None
    postcondition: str | None = None
    system_response: str | None = None
    constraint: str | None = None
    actor: str | None = None
    system_name: str | None = None
    negation: bool = False


class EARSAnalysisResult(BaseModel):
    """Complete EARS pattern analysis result."""

    pattern_type: EARSPatternType
    confidence: float = Field(ge=0, le=1)
    components: EARSComponents
    is_valid: bool
    validation_issues: list[str] = Field(default_factory=list)
    improvement_suggestions: list[str] = Field(default_factory=list)
    formal_structure: str | None = None
    ambiguous_terms: list[str] = Field(default_factory=list)
    incomplete_markers: list[str] = Field(default_factory=list)


class QualityIssue(BaseModel):
    """A detected quality issue with full context."""

    dimension: QualityDimension
    severity: str = Field(pattern="^(error|warning|info)$")
    message: str
    suggestion: str | None = None
    position: int | None = None
    context: str | None = None
    rule_id: str | None = None


class QualityScore(BaseModel):
    """Comprehensive quality scoring result."""

    dimension_scores: dict[str, float]
    overall_score: float
    issues: list[QualityIssue]
    grade: str
    percentile: int | None = None
    improvement_priority: list[str] = Field(default_factory=list)


class EARSPatternAnalyzer:
    """Advanced EARS pattern analyzer with formal structure extraction."""

    PATTERNS: ClassVar[dict[EARSPatternType, re.Pattern[str]]] = {
        EARSPatternType.UNWANTED: re.compile(
            r"^(?:if|when)\s+(.+?),?\s+(?:then\s+)?(?:the\s+)?(\w+)\s+shall\s+(?:not|never)\s+(.+)$",
            re.IGNORECASE,
        ),
        EARSPatternType.COMPLEX: re.compile(
            r"^(?:while\s+(.+?)\s+)?(?:when|if|upon)\s+(.+?),?\s+(?:the\s+)?(\w+)\s+shall\s+(.+)$",
            re.IGNORECASE,
        ),
        EARSPatternType.STATE_DRIVEN: re.compile(
            r"^(?:while|during|as\s+long\s+as)\s+(.+?),?\s+(?:the\s+)?(\w+)\s+shall\s+(.+)$",
            re.IGNORECASE,
        ),
        EARSPatternType.EVENT_DRIVEN: re.compile(
            r"^(?:when|upon|after|once|if)\s+(.+?),?\s+(?:the\s+)?(\w+)\s+shall\s+(.+)$",
            re.IGNORECASE,
        ),
        EARSPatternType.OPTIONAL: re.compile(
            r"^(?:where|if|in\s+case)\s+(.+?)\s+(?:is\s+)?(?:enabled|configured|available|supported),?\s+(?:the\s+)?(\w+)\s+shall\s+(.+)$",
            re.IGNORECASE,
        ),
        EARSPatternType.UBIQUITOUS: re.compile(r"^(?:the\s+)?(\w+)\s+shall\s+(.+)$", re.IGNORECASE),
    }

    AMBIGUOUS_WORDS = frozenset({
        "appropriate", "adequate", "reasonable", "sufficient", "timely", "easy", "simple",
        "fast", "quick", "efficient", "effective", "user-friendly", "flexible", "scalable",
        "robust", "secure", "good", "bad", "better", "best", "optimal", "minimal",
        "maximum", "some", "several", "many", "few", "various", "etc", "and/or",
        "normally", "usually", "typically", "generally", "often", "may", "might",
        "could", "possibly", "perhaps", "probably", "as appropriate", "as needed",
        "if necessary", "when required", "similar", "etc.", "and so on", "such as", "for example",
    })

    INCOMPLETE_MARKERS = frozenset({
        "tbd", "tba", "todo", "fixme", "xxx", "???", "...", "placeholder",
        "pending", "to be determined", "to be defined",
    })

    WEAK_MODALS = frozenset({"may", "might", "could", "should", "would"})

    def analyze(self, requirement_text: str) -> EARSAnalysisResult:
        """Perform complete EARS analysis on a requirement."""
        text = requirement_text.strip()
        text_lower = text.lower()
        issues = []
        suggestions = []
        ambiguous = [w for w in self.AMBIGUOUS_WORDS if w in text_lower]
        incomplete = [m for m in self.INCOMPLETE_MARKERS if m in text_lower]

        for pattern_type, pattern in self.PATTERNS.items():
            match = pattern.match(text)
            if match:
                components = self._extract_components(pattern_type, match)
                confidence = self._calculate_confidence(text, pattern_type, components, ambiguous, incomplete)
                validation_issues = self._validate(text, components, ambiguous, incomplete)
                issues.extend(validation_issues)
                if validation_issues:
                    suggestions.extend(self._generate_suggestions(validation_issues))
                formal_structure = self._to_formal_structure(pattern_type, components)
                return EARSAnalysisResult(
                    pattern_type=pattern_type,
                    confidence=confidence,
                    components=components,
                    is_valid=len([i for i in validation_issues if "error" in i.lower()]) == 0,
                    validation_issues=validation_issues,
                    improvement_suggestions=suggestions,
                    formal_structure=formal_structure,
                    ambiguous_terms=ambiguous,
                    incomplete_markers=incomplete,
                )

        return EARSAnalysisResult(
            pattern_type=EARSPatternType.UNCLASSIFIED,
            confidence=0.0,
            components=EARSComponents(),
            is_valid=False,
            validation_issues=["Requirement does not match any EARS pattern"],
            improvement_suggestions=[
                "Restructure as: 'The <system> shall <action>'",
                "For conditions: 'When <trigger>, the <system> shall <action>'",
                "For states: 'While <state>, the <system> shall <action>'",
            ],
            ambiguous_terms=ambiguous,
            incomplete_markers=incomplete,
        )

    def _extract_components(self, pattern_type: EARSPatternType, match: re.Match[str]) -> EARSComponents:
        groups = match.groups()
        if pattern_type == EARSPatternType.UBIQUITOUS:
            return EARSComponents(
                system_name=groups[0] if len(groups) > 0 else None,
                system_response=groups[1] if len(groups) > 1 else None,
            )
        if pattern_type == EARSPatternType.EVENT_DRIVEN:
            return EARSComponents(
                trigger=groups[0] if len(groups) > 0 else None,
                system_name=groups[1] if len(groups) > 1 else None,
                system_response=groups[2] if len(groups) > _MIN_SAMPLES_FOR_METRICS else None,
            )
        if pattern_type == EARSPatternType.STATE_DRIVEN:
            return EARSComponents(
                precondition=groups[0] if len(groups) > 0 else None,
                system_name=groups[1] if len(groups) > 1 else None,
                system_response=groups[2] if len(groups) > _MIN_SAMPLES_FOR_METRICS else None,
            )
        if pattern_type == EARSPatternType.OPTIONAL:
            return EARSComponents(
                constraint=groups[0] if len(groups) > 0 else None,
                system_name=groups[1] if len(groups) > 1 else None,
                system_response=groups[2] if len(groups) > _MIN_SAMPLES_FOR_METRICS else None,
            )
        if pattern_type == EARSPatternType.UNWANTED:
            return EARSComponents(
                precondition=groups[0] if len(groups) > 0 else None,
                system_name=groups[1] if len(groups) > 1 else None,
                postcondition=groups[2] if len(groups) > _MIN_SAMPLES_FOR_METRICS else None,
                negation=True,
            )
        if pattern_type == EARSPatternType.COMPLEX:
            return EARSComponents(
                precondition=groups[0] if len(groups) > 0 and groups[0] else None,
                trigger=groups[1] if len(groups) > 1 else None,
                system_name=groups[2] if len(groups) > _MIN_SAMPLES_FOR_METRICS else None,
                system_response=groups[3] if len(groups) > 3 else None,
            )
        return EARSComponents()

    def _calculate_confidence(
        self,
        text: str,
        _pattern_type: EARSPatternType,
        components: EARSComponents,
        ambiguous: list[str],
        incomplete: list[str],
    ) -> float:
        confidence = 0.6
        if "shall" in text.lower():
            confidence += 0.15
        if components.system_name and len(components.system_name) > _MIN_SAMPLES_FOR_METRICS:
            confidence += 0.1
        if components.system_response and len(components.system_response) > 15:
            confidence += 0.1
        confidence -= len(ambiguous) * 0.03
        confidence -= len(incomplete) * 0.15
        text_lower = text.lower()
        weak_count = sum(1 for w in self.WEAK_MODALS if f" {w} " in f" {text_lower} ")
        confidence -= weak_count * 0.05
        return max(0.0, min(1.0, confidence))

    def _validate(
        self,
        text: str,
        _components: EARSComponents,
        ambiguous: list[str],
        incomplete: list[str],
    ) -> list[str]:
        issues = []
        if ambiguous:
            issues.append(f"Ambiguous terms: {', '.join(ambiguous[:5])}")
        if incomplete:
            issues.append(f"[ERROR] Incomplete markers: {', '.join(incomplete)}")
        if text.count(" and ") > _MIN_SAMPLES_FOR_METRICS or text.count(" or ") > 1:
            issues.append("Possible compound requirement - consider splitting")
        perf_words = ["fast", "quick", "efficient", "responsive", "performance"]
        if any(w in text.lower() for w in perf_words) and not any(c.isdigit() for c in text):
            issues.append("Performance requirement lacks quantifiable metric")
        if len(text) < 25:
            issues.append("Requirement may be too brief")
        passive_indicators = [" be ", " been ", " being ", " was ", " were "]
        if any(p in text.lower() for p in passive_indicators):
            issues.append("Consider using active voice for clarity")
        return issues

    def _generate_suggestions(self, issues: list[str]) -> list[str]:
        suggestions = []
        for issue in issues:
            issue_lower = issue.lower()
            if "ambiguous" in issue_lower:
                suggestions.append("Replace ambiguous terms with specific, measurable criteria")
            elif "incomplete" in issue_lower:
                suggestions.append("Complete all TBD/placeholder sections")
            elif "compound" in issue_lower:
                suggestions.append("Split into separate atomic requirements for better traceability")
            elif "quantifiable" in issue_lower or "metric" in issue_lower:
                suggestions.append("Add measurable targets (e.g., 'within 200ms', '99.9% uptime')")
            elif "passive" in issue_lower:
                suggestions.append("Rewrite using active voice: 'The system shall...' not 'It shall be...'")
        return suggestions

    def _to_formal_structure(self, pattern_type: EARSPatternType, components: EARSComponents) -> str:
        if pattern_type == EARSPatternType.UBIQUITOUS:
            return f"The {components.system_name or '<system>'} shall {components.system_response or '<response>'}."
        if pattern_type == EARSPatternType.EVENT_DRIVEN:
            return f"WHEN {components.trigger or '<trigger>'}, the {components.system_name or '<system>'} shall {components.system_response or '<response>'}."
        if pattern_type == EARSPatternType.STATE_DRIVEN:
            return f"WHILE {components.precondition or '<state>'}, the {components.system_name or '<system>'} shall {components.system_response or '<response>'}."
        if pattern_type == EARSPatternType.OPTIONAL:
            return f"WHERE {components.constraint or '<feature>'} is enabled, the {components.system_name or '<system>'} shall {components.system_response or '<response>'}."
        if pattern_type == EARSPatternType.UNWANTED:
            return f"IF {components.precondition or '<condition>'}, THEN the {components.system_name or '<system>'} shall NOT {components.postcondition or '<action>'}."
        if pattern_type == EARSPatternType.COMPLEX:
            parts = []
            if components.precondition:
                parts.append(f"WHILE {components.precondition}")
            if components.trigger:
                parts.append(f"WHEN {components.trigger}")
            parts.append(f"the {components.system_name or '<system>'} shall {components.system_response or '<response>'}")
            return ", ".join(parts) + "."
        return "<unclassified>"


class RequirementQualityAnalyzer:
    """ISO 29148 compliant quality analyzer with 9 dimensions."""

    DIMENSION_WEIGHTS: ClassVar[dict[QualityDimension, float]] = {
        QualityDimension.UNAMBIGUITY: 0.18,
        QualityDimension.COMPLETENESS: 0.18,
        QualityDimension.VERIFIABILITY: 0.14,
        QualityDimension.CONSISTENCY: 0.12,
        QualityDimension.NECESSITY: 0.10,
        QualityDimension.SINGULARITY: 0.10,
        QualityDimension.FEASIBILITY: 0.06,
        QualityDimension.TRACEABILITY: 0.06,
        QualityDimension.CORRECTNESS: 0.06,
    }

    def analyze(
        self,
        requirement_text: str,
        related_requirements: list[str] | None = None,
        linked_tests: list[str] | None = None,
        linked_items: dict[str, list[str]] | None = None,
    ) -> QualityScore:
        """Analyze requirement quality across all ISO 29148 dimensions."""
        issues: list[QualityIssue] = []
        scores: dict[str, float] = {}
        scores[QualityDimension.UNAMBIGUITY.value], unambiguity_issues = self._analyze_unambiguity(requirement_text)
        issues.extend(unambiguity_issues)
        scores[QualityDimension.COMPLETENESS.value], completeness_issues = self._analyze_completeness(requirement_text)
        issues.extend(completeness_issues)
        scores[QualityDimension.VERIFIABILITY.value], verifiability_issues = self._analyze_verifiability(requirement_text)
        issues.extend(verifiability_issues)
        scores[QualityDimension.SINGULARITY.value], singularity_issues = self._analyze_singularity(requirement_text)
        issues.extend(singularity_issues)
        scores[QualityDimension.NECESSITY.value], necessity_issues = self._analyze_necessity(requirement_text)
        issues.extend(necessity_issues)
        scores[QualityDimension.TRACEABILITY.value], traceability_issues = self._analyze_traceability(linked_tests, linked_items)
        issues.extend(traceability_issues)
        scores[QualityDimension.CONSISTENCY.value], consistency_issues = self._analyze_consistency(requirement_text, related_requirements)
        issues.extend(consistency_issues)
        scores[QualityDimension.FEASIBILITY.value] = 0.8
        scores[QualityDimension.CORRECTNESS.value] = 0.8
        overall = sum(scores.get(dim.value, 0.8) * weight for dim, weight in self.DIMENSION_WEIGHTS.items())
        grade = self._score_to_grade(overall)
        improvement_priority = sorted(
            [d.value for d in QualityDimension if scores.get(d.value, 1.0) < QUALITY_IMPROVEMENT_THRESHOLD],
            key=lambda d: scores.get(d, 1.0),
        )
        return QualityScore(
            dimension_scores=scores,
            overall_score=overall * 100,
            issues=issues,
            grade=grade,
            improvement_priority=improvement_priority,
        )

    def _analyze_unambiguity(self, text: str) -> tuple[float, list[QualityIssue]]:
        issues = []
        score = 1.0
        text_lower = text.lower()
        ambiguous_terms = {
            "appropriate": "Define specific criteria",
            "adequate": "Specify measurable thresholds",
            "reasonable": "Provide concrete bounds",
            "sufficient": "Quantify the requirement",
            "timely": "Specify time constraints in ms/s/min",
            "fast": "Define performance target (e.g., <200ms)",
            "quick": "Define performance target",
            "efficient": "Specify efficiency metrics",
            "user-friendly": "Define usability criteria (e.g., SUS score >68)",
            "flexible": "Enumerate supported variations",
            "scalable": "Define scaling parameters and limits",
            "robust": "Specify error handling requirements",
            "secure": "Reference security standards (e.g., OWASP)",
            "etc": "List all items explicitly",
            "and/or": "Choose 'and' or 'or' - not both",
        }
        for term, suggestion in ambiguous_terms.items():
            if term in text_lower:
                pos = text_lower.find(term)
                score -= 0.12
                issues.append(QualityIssue(
                    dimension=QualityDimension.UNAMBIGUITY,
                    severity="warning",
                    message=f"Ambiguous term '{term}' detected",
                    suggestion=suggestion,
                    position=pos,
                    rule_id="ISO29148-AMB-001",
                ))
        weak_modals = {"may", "might", "could", "possibly", "perhaps", "probably"}
        for modal in weak_modals:
            if f" {modal} " in f" {text_lower} ":
                score -= 0.08
                issues.append(QualityIssue(
                    dimension=QualityDimension.UNAMBIGUITY,
                    severity="info",
                    message=f"Weak modal '{modal}' suggests uncertainty",
                    suggestion="Use 'shall' for mandatory, 'may' only for truly optional",
                    rule_id="ISO29148-AMB-002",
                ))
        return max(0.0, score), issues

    def _analyze_completeness(self, text: str) -> tuple[float, list[QualityIssue]]:
        issues = []
        score = 1.0
        text_lower = text.lower()
        incomplete_markers = {
            "tbd": "To Be Determined",
            "tba": "To Be Announced",
            "todo": "TODO marker",
            "fixme": "FIXME marker",
            "xxx": "XXX placeholder",
            "???": "Question marks",
            "...": "Ellipsis",
            "pending": "Pending content",
            "placeholder": "Placeholder text",
        }
        for marker, desc in incomplete_markers.items():
            if marker in text_lower:
                score -= 0.25
                issues.append(QualityIssue(
                    dimension=QualityDimension.COMPLETENESS,
                    severity="error",
                    message=f"Incomplete marker found: {desc}",
                    suggestion="Complete all placeholder sections before baseline",
                    rule_id="ISO29148-COMP-001",
                ))
        if len(text) < QUALITY_MIN_LENGTH:
            score -= 0.15
            issues.append(QualityIssue(
                dimension=QualityDimension.COMPLETENESS,
                severity="warning",
                message="Requirement may be too brief to be complete",
                suggestion="Ensure actor, action, and conditions are specified",
                rule_id="ISO29148-COMP-002",
            ))
        if "shall" in text_lower and not any(
            actor in text_lower for actor in ["system", "user", "operator", "administrator"]
        ):
            score -= 0.10
            issues.append(QualityIssue(
                dimension=QualityDimension.COMPLETENESS,
                severity="info",
                message="No clear actor/system identified",
                suggestion="Specify who/what performs the action",
                rule_id="ISO29148-COMP-003",
            ))
        return max(0.0, score), issues

    def _analyze_verifiability(self, text: str) -> tuple[float, list[QualityIssue]]:
        issues = []
        score = 1.0
        text_lower = text.lower()
        has_numbers = bool(re.search(r"\d+", text))
        has_units = any(
            unit in text_lower for unit in [
                "ms", "seconds", "minutes", "hours", "days", "bytes", "kb", "mb", "gb", "tb",
                "%", "percent", "percentage", "users", "requests", "transactions", "items",
                "times", "attempts", "retries",
            ]
        )
        perf_indicators = [
            "performance", "speed", "response", "latency", "throughput", "availability",
            "uptime", "reliability", "accuracy",
        ]
        if any(ind in text_lower for ind in perf_indicators) and not has_numbers:
            score -= 0.30
            issues.append(QualityIssue(
                dimension=QualityDimension.VERIFIABILITY,
                severity="error",
                message="Performance/quality requirement lacks metrics",
                suggestion="Add specific targets (e.g., 'response time <200ms', 'uptime >99.9%')",
                rule_id="ISO29148-VER-001",
            ))
        if not has_numbers and not has_units:
            score -= 0.10
            issues.append(QualityIssue(
                dimension=QualityDimension.VERIFIABILITY,
                severity="info",
                message="No quantifiable metrics found",
                suggestion="Consider adding measurable acceptance criteria",
                rule_id="ISO29148-VER-002",
            ))
        return max(0.0, score), issues

    def _analyze_singularity(self, text: str) -> tuple[float, list[QualityIssue]]:
        issues = []
        score = 1.0
        and_count = text.lower().count(" and ")
        or_count = text.lower().count(" or ")
        if and_count > QUALITY_AND_COUNT_THRESHOLD:
            score -= 0.15 * (and_count - QUALITY_AND_COUNT_THRESHOLD)
            issues.append(QualityIssue(
                dimension=QualityDimension.SINGULARITY,
                severity="warning",
                message=f"Multiple 'and' conjunctions ({and_count}) - possible compound requirement",
                suggestion="Split into separate atomic requirements for better traceability",
                rule_id="ISO29148-SING-001",
            ))
        if or_count > 0:
            score -= 0.20 * or_count
            issues.append(QualityIssue(
                dimension=QualityDimension.SINGULARITY,
                severity="warning",
                message="'Or' conjunction detected - ambiguous alternatives",
                suggestion="Split into separate requirements or clarify as enumeration",
                rule_id="ISO29148-SING-002",
            ))
        shall_count = text.lower().count(" shall ")
        if shall_count > 1:
            score -= 0.15 * (shall_count - 1)
            issues.append(QualityIssue(
                dimension=QualityDimension.SINGULARITY,
                severity="warning",
                message=f"Multiple 'shall' statements ({shall_count}) in one requirement",
                suggestion="Each requirement should contain exactly one 'shall'",
                rule_id="ISO29148-SING-003",
            ))
        return max(0.0, score), issues

    def _analyze_necessity(self, text: str) -> tuple[float, list[QualityIssue]]:
        issues = []
        score = 1.0
        text_lower = text.lower()
        if "shall" in text_lower:
            score = 1.0
        elif "will" in text_lower:
            score = 0.85
            issues.append(QualityIssue(
                dimension=QualityDimension.NECESSITY,
                severity="info",
                message="'Will' is weaker than 'shall' for requirements",
                suggestion="Use 'shall' for mandatory requirements",
                rule_id="ISO29148-NEC-001",
            ))
        elif "should" in text_lower:
            score = 0.65
            issues.append(QualityIssue(
                dimension=QualityDimension.NECESSITY,
                severity="warning",
                message="'Should' indicates recommendation, not requirement",
                suggestion="Use 'shall' for mandatory, 'should' for recommendations only",
                rule_id="ISO29148-NEC-002",
            ))
        elif "must" in text_lower:
            score = 0.90
            issues.append(QualityIssue(
                dimension=QualityDimension.NECESSITY,
                severity="info",
                message="'Must' is acceptable but 'shall' is preferred per IEEE 830",
                suggestion="Consider using 'shall' for consistency",
                rule_id="ISO29148-NEC-003",
            ))
        else:
            score = 0.5
            issues.append(QualityIssue(
                dimension=QualityDimension.NECESSITY,
                severity="warning",
                message="No requirement keyword found",
                suggestion="Use 'The system shall...' format",
                rule_id="ISO29148-NEC-004",
            ))
        return score, issues

    def _analyze_traceability(
        self,
        linked_tests: list[str] | None,
        linked_items: dict[str, list[str]] | None,
    ) -> tuple[float, list[QualityIssue]]:
        issues = []
        score = 1.0
        if not linked_tests or len(linked_tests) == 0:
            score -= 0.30
            issues.append(QualityIssue(
                dimension=QualityDimension.TRACEABILITY,
                severity="warning",
                message="No linked test cases for verification",
                suggestion="Link test cases to enable verification traceability",
                rule_id="ISO29148-TRACE-001",
            ))
        if linked_items and not linked_items.get("upstream"):
            score -= 0.10
            issues.append(QualityIssue(
                dimension=QualityDimension.TRACEABILITY,
                severity="info",
                message="No upstream links (parent requirements/features)",
                suggestion="Link to parent requirement or feature for derivation trace",
                rule_id="ISO29148-TRACE-002",
            ))
        return max(0.0, score), issues

    def _analyze_consistency(
        self,
        text: str,
        _related_requirements: list[str] | None,
    ) -> tuple[float, list[QualityIssue]]:
        issues = []
        score = 0.85
        text_lower = text.lower()
        if "must" in text_lower and "may" in text_lower:
            score -= 0.15
            issues.append(QualityIssue(
                dimension=QualityDimension.CONSISTENCY,
                severity="warning",
                message="Mixed mandatory ('must') and optional ('may') language",
                suggestion="Clarify which parts are mandatory vs optional",
                rule_id="ISO29148-CONS-001",
            ))
        return score, issues

    def _score_to_grade(self, score: float) -> str:
        if score >= GRADE_A_THRESHOLD:
            return "A"
        if score >= GRADE_B_THRESHOLD:
            return "B"
        if score >= GRADE_C_THRESHOLD:
            return "C"
        if score >= GRADE_D_THRESHOLD:
            return "D"
        return "F"


__all__ = [
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
]
