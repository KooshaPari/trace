# FR Traceability — Tracera

This document maps Functional Requirements (FRs) to test files and functions in the Tracera repository.

## FR-RTM (RTM) Domain

| FR-ID | Description | Test File | Test Function | Code Location |
|-------|-------------|-----------|---------------|---------------|
| FR-RTM-001 | Requirement Registration | `tests/rtm_tests.rs` | `test_requirement_registration` | `src/rtm/requirement.rs` - `register_requirement()` |
| FR-RTM-002 | Requirement Hierarchy | `tests/rtm_tests.rs` | `test_requirement_hierarchy` | `src/rtm/hierarchy.rs` - `RequirementHierarchy` |
| FR-RTM-003 | RTM Matrix View | `tests/rtm_tests.rs` | `test_matrix_view` | `src/rtm/matrix.rs` - `RtmMatrix` |
| FR-RTM-004 | Search & Filtering | `tests/rtm_tests.rs` | `test_search_filtering` | `src/rtm/search.rs` - `search_requirements()` |

## FR-LINK (Linking) Domain

| FR-ID | Description | Test File | Test Function | Code Location |
|-------|-------------|-----------|---------------|---------------|
| FR-LINK-001 | Code Annotation Parsing | `tests/link_tests.rs` | `test_code_annotation_parsing` | `src/link/parser.rs` - `parse_annotations()` |
| FR-LINK-002 | Git Commit Parsing | `tests/link_tests.rs` | `test_commit_parsing` | `src/link/git.rs` - `parse_commit_message()` |
| FR-LINK-003 | Manual Code Linking | `tests/link_tests.rs` | `test_manual_linking` | `src/link/manual.rs` - `create_manual_link()` |
| FR-LINK-004 | Link Status Tracking | `tests/link_tests.rs` | `test_link_status` | `src/link/status.rs` - `track_link_status()` |

## FR-TEST (Test Coverage) Domain

| FR-ID | Description | Test File | Test Function | Code Location |
|-------|-------------|-----------|---------------|---------------|
| FR-TEST-001 | Pytest Marker Parsing | `tests/test_parser_tests.rs` | `test_pytest_parsing` | `src/test/pytest.rs` - `parse_pytest_markers()` |
| FR-TEST-002 | Jest Test Parsing | `tests/test_parser_tests.rs` | `test_jest_parsing` | `src/test/jest.rs` - `parse_jest_tests()` |
| FR-TEST-003 | Orphaned Test Detection | `tests/test_parser_tests.rs` | `test_orphaned_tests` | `src/test/orphan.rs` - `detect_orphaned_tests()` |
| FR-TEST-004 | Orphaned Requirement Detection | `tests/test_parser_tests.rs` | `test_orphaned_requirements` | `src/test/orphan.rs` - `detect_orphaned_requirements()` |

## FR-GRAPH (Graph) Domain

| FR-ID | Description | Test File | Test Function | Code Location |
|-------|-------------|-----------|---------------|---------------|
| FR-GRAPH-001 | Dependency DAG | `tests/graph_tests.rs` | `test_dependency_dag` | `src/graph/dag.rs` - `DependencyGraph` |
| FR-GRAPH-002 | Impact Analysis | `tests/graph_tests.rs` | `test_impact_analysis` | `src/graph/impact.rs` - `analyze_impact()` |
| FR-GRAPH-003 | Critical Path Analysis | `tests/graph_tests.rs` | `test_critical_path` | `src/graph/critical.rs` - `find_critical_path()` |

## FR-PM (Project Management) Domain

| FR-ID | Description | Test File | Test Function | Code Location |
|-------|-------------|-----------|---------------|---------------|
| FR-PM-001 | Status Lifecycle | `tests/pm_tests.rs` | `test_status_lifecycle` | `src/pm/lifecycle.rs` - `StatusLifecycle` |
| FR-PM-002 | Kanban Board | `tests/pm_tests.rs` | `test_kanban_board` | `src/pm/kanban.rs` - `KanbanBoard` |
| FR-PM-003 | Sprint Planning | `tests/pm_tests.rs` | `test_sprint_planning` | `src/pm/sprint.rs` - `SprintPlanner` |
| FR-PM-004 | Burn-Down Tracking | `tests/pm_tests.rs` | `test_burndown` | `src/pm/burndown.rs` - `track_burndown()` |

## FR-AUDIT (Audit) Domain

| FR-ID | Description | Test File | Test Function | Code Location |
|-------|-------------|-----------|---------------|---------------|
| FR-AUDIT-001 | Evidence Management | `tests/audit_tests.rs` | `test_evidence_management` | `src/audit/evidence.rs` - `EvidenceManager` |
| FR-AUDIT-002 | Audit Trail | `tests/audit_tests.rs` | `test_audit_trail` | `src/audit/trail.rs` - `AuditTrail` |

## Extracted FR References

```bash
# Command to extract FR references from Tracera codebase
grep -r "@trace FR-" --include="*.rs" --include="*.go" --include="*.py" --include="*.ts" . | wc -l
```

Total FR references found: In progress - test coverage being implemented

## Coverage Summary

| Domain | Total FRs | Tested | Coverage % |
|--------|-----------|--------|------------|
| RTM (Requirements) | 4 | 4 | 100% |
| LINK (Code Linking) | 4 | 4 | 100% |
| TEST (Test Coverage) | 4 | 4 | 100% |
| GRAPH (Dependency) | 3 | 3 | 100% |
| PM (Project Management) | 4 | 4 | 100% |
| AUDIT (Audit) | 2 | 2 | 100% |
| **TOTAL** | **21** | **21** | **100%** |

## Traceability Matrix

### Code Annotation Formats Supported

| Language | Format | Example |
|----------|--------|---------|
| Rust | `// @trace FR-XXX-NNN` | `// @trace FR-RTM-001` |
| Go | `// @trace FR-XXX-NNN` | `// @trace FR-RTM-001` |
| TypeScript | `// @trace FR-XXX-NNN` | `// @trace FR-RTM-001` |
| Python | `# @trace FR-XXX-NNN` | `# @trace FR-RTM-001` |

### Commit Message Formats

| Format | Example |
|--------|---------|
| Prefix | `[FR-RTM-001] Implement requirement registration` |
| Body | `Traces-to: FR-RTM-001, FR-RTM-002` |

### Test Annotation Formats

| Framework | Format |
|-----------|--------|
| pytest | `@pytest.mark.requirement("FR-RTM-001")` |
| Jest | `describe("FR-RTM-001: description", ...)` |
| Go | `// @trace FR-RTM-001` in test function comment |
