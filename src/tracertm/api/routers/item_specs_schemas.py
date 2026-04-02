"""Pydantic models for enhanced Item specifications.

Provides response and input models for RequirementSpec, TestSpec, EpicSpec,
UserStorySpec, TaskSpec, and DefectSpec entities.
"""

from datetime import datetime

from pydantic import BaseModel

RISK_THRESHOLD_CRITICAL = 80
RISK_THRESHOLD_HIGH = 60
RISK_THRESHOLD_MEDIUM = 40
SIMILARITY_DUPLICATE_THRESHOLD = 0.95


class RequirementSpecResponse(BaseModel):
    id: str
    item_id: str
    project_id: str
    requirement_type: str
    risk_level: str
    verification_status: str
    quality_score: float
    impact_score: float | None = None
    traceability_index: float
    acceptance_criteria: str
    verification_evidence: list[dict[str, object]] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RequirementSpecListResponse(BaseModel):
    specs: list[RequirementSpecResponse]
    total: int


class TestSpecResponse(BaseModel):
    id: str
    item_id: str
    project_id: str
    test_type: str
    coverage_percentage: float
    pass_rate: float
    flakiness_score: float
    is_quarantined: bool
    quarantine_reason: str | None = None
    last_run: datetime | None = None
    average_duration_ms: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TestSpecListResponse(BaseModel):
    specs: list[TestSpecResponse]
    total: int


class EpicSpecResponse(BaseModel):
    id: str
    item_id: str
    project_id: str
    epic_type: str
    story_points: int | None = None
    business_value: str
    timeline: str | None = None
    dependencies: list[str] = []
    child_items: list[str] = []
    completion_percentage: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EpicSpecListResponse(BaseModel):
    specs: list[EpicSpecResponse]
    total: int


class UserStorySpecResponse(BaseModel):
    id: str
    item_id: str
    project_id: str
    user_persona: str
    business_value: str
    acceptance_criteria: list[str]
    story_points: int | None = None
    priority: str
    dependencies: list[str] = []
    definition_of_done: list[str] = []
    test_coverage: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserStorySpecListResponse(BaseModel):
    specs: list[UserStorySpecResponse]
    total: int


class TaskSpecResponse(BaseModel):
    id: str
    item_id: str
    project_id: str
    task_type: str
    effort_estimate_hours: float
    actual_effort_hours: float | None = None
    subtasks: list[str] = []
    assigned_to: str | None = None
    due_date: datetime | None = None
    dependencies: list[str] = []
    completion_percentage: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskSpecListResponse(BaseModel):
    specs: list[TaskSpecResponse]
    total: int


class DefectSpecResponse(BaseModel):
    id: str
    item_id: str
    project_id: str
    defect_type: str
    severity: str
    reproduced: bool
    reproduction_steps: list[str]
    root_cause: str | None = None
    affected_components: list[str] = []
    related_defects: list[str] = []
    resolution_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DefectSpecListResponse(BaseModel):
    specs: list[DefectSpecResponse]
    total: int


class RequirementQualityStats(BaseModel):
    total_requirements: int
    verified_count: int
    unverified_count: int
    verification_rate: float
    average_quality_score: float
    high_risk_count: int
    critical_risk_count: int
    high_impact_count: int
    average_traceability: float
    timestamp: datetime


class TestHealthStats(BaseModel):
    total_tests: int
    passing_tests: int
    failing_tests: int
    quarantined_tests: int
    average_pass_rate: float
    average_coverage: float
    flaky_test_count: int
    average_duration_ms: float
    timestamp: datetime


class DefectMetrics(BaseModel):
    total_defects: int
    open_defects: int
    closed_defects: int
    deferred_defects: int
    blocker_count: int
    critical_count: int
    average_resolution_time_hours: float | None = None
    timestamp: datetime


class ItemSpecStats(BaseModel):
    project_id: str
    total_items: int
    requirements_stats: RequirementQualityStats
    tests_stats: TestHealthStats
    defects_stats: DefectMetrics
    timestamp: datetime


class RequirementSpecCreate(BaseModel):
    item_id: str
    requirement_type: str
    risk_level: str
    acceptance_criteria: str
    metadata: dict[str, object] | None = None


class RequirementSpecUpdate(BaseModel):
    requirement_type: str | None = None
    risk_level: str | None = None
    acceptance_criteria: str | None = None
    metadata: dict[str, object] | None = None


class TestSpecCreate(BaseModel):
    item_id: str
    test_type: str
    coverage_percentage: float
    metadata: dict[str, object] | None = None


class TestSpecUpdate(BaseModel):
    test_type: str | None = None
    coverage_percentage: float | None = None
    metadata: dict[str, object] | None = None


class EpicSpecCreate(BaseModel):
    item_id: str
    epic_type: str
    story_points: int | None = None
    business_value: str
    timeline: str | None = None
    metadata: dict[str, object] | None = None


class EpicSpecUpdate(BaseModel):
    epic_type: str | None = None
    story_points: int | None = None
    business_value: str | None = None
    timeline: str | None = None
    metadata: dict[str, object] | None = None


class UserStorySpecCreate(BaseModel):
    item_id: str
    user_persona: str
    business_value: str
    acceptance_criteria: list[str]
    story_points: int | None = None
    priority: str
    definition_of_done: list[str] | None = None
    metadata: dict[str, object] | None = None


class UserStorySpecUpdate(BaseModel):
    user_persona: str | None = None
    business_value: str | None = None
    acceptance_criteria: list[str] | None = None
    story_points: int | None = None
    priority: str | None = None
    definition_of_done: list[str] | None = None
    metadata: dict[str, object] | None = None


class TaskSpecCreate(BaseModel):
    item_id: str
    task_type: str
    effort_estimate_hours: float
    assigned_to: str | None = None
    due_date: datetime | None = None
    metadata: dict[str, object] | None = None


class TaskSpecUpdate(BaseModel):
    task_type: str | None = None
    effort_estimate_hours: float | None = None
    actual_effort_hours: float | None = None
    assigned_to: str | None = None
    due_date: datetime | None = None
    metadata: dict[str, object] | None = None


class DefectSpecCreate(BaseModel):
    item_id: str
    defect_type: str
    severity: str
    reproduced: bool
    reproduction_steps: list[str]
    affected_components: list[str] | None = None
    metadata: dict[str, object] | None = None


class DefectSpecUpdate(BaseModel):
    defect_type: str | None = None
    severity: str | None = None
    reproduced: bool | None = None
    reproduction_steps: list[str] | None = None
    root_cause: str | None = None
    affected_components: list[str] | None = None
    resolution_status: str | None = None
    metadata: dict[str, object] | None = None


__all__ = [
    "RISK_THRESHOLD_CRITICAL",
    "RISK_THRESHOLD_HIGH",
    "RISK_THRESHOLD_MEDIUM",
    "SIMILARITY_DUPLICATE_THRESHOLD",
    "DefectMetrics",
    "DefectSpecCreate",
    "DefectSpecListResponse",
    "DefectSpecResponse",
    "DefectSpecUpdate",
    "EpicSpecCreate",
    "EpicSpecListResponse",
    "EpicSpecResponse",
    "EpicSpecUpdate",
    "ItemSpecStats",
    "RequirementQualityStats",
    "RequirementSpecCreate",
    "RequirementSpecListResponse",
    "RequirementSpecResponse",
    "RequirementSpecUpdate",
    "TaskSpecCreate",
    "TaskSpecListResponse",
    "TaskSpecResponse",
    "TaskSpecUpdate",
    "TestHealthStats",
    "TestSpecCreate",
    "TestSpecListResponse",
    "TestSpecResponse",
    "TestSpecUpdate",
    "UserStorySpecCreate",
    "UserStorySpecListResponse",
    "UserStorySpecResponse",
    "UserStorySpecUpdate",
]
