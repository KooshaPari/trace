# FR-TRAC-013: Sprint Planning

## ID
- **FR-ID**: FR-TRAC-013
- **Repository**: Tracera
- **Domain**: PM

## Description

The system SHALL support sprint creation with capacity planning, requirement assignment to sprints, burndown charts, and velocity tracking.

## Acceptance Criteria

- [ ] Creates sprints with dates/capacity
- [ ] Assigns requirements to sprints
- [ ] Shows burndown chart
- [ ] Calculates velocity

## Test References

| Test File | Function | FR Reference |
|-----------|----------|--------------|
| `tests/pm_tests.rs` | `test_sprint_planning` | `// @trace FR-PM-003` |

## Code References

| File | Function/Struct | FR Reference |
|------|-----------------|--------------|
| `src/pm/sprint.rs` | `SprintPlanner` | `// @trace FR-PM-003` |

## Related FRs

- FR-TRAC-012: Kanban Board

## Status

- **Current**: implemented
- **Since**: 2026-03-10
