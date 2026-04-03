# FR-TRAC-012: Kanban Board

## ID
- **FR-ID**: FR-TRAC-012
- **Repository**: Tracera
- **Domain**: PM

## Description

The system SHALL provide a Kanban board with requirement cards showing ID, title, assignee, priority badge, and coverage badges, supporting drag-and-drop status updates and filtering.

## Acceptance Criteria

- [ ] Displays cards with all metadata
- [ ] Drag-and-drop updates status
- [ ] Grouping by status/assignee/epic
- [ ] Search/filter capabilities

## Test References

| Test File | Function | FR Reference |
|-----------|----------|--------------|
| `tests/pm_tests.rs` | `test_kanban_board` | `// @trace FR-PM-002` |

## Code References

| File | Function/Struct | FR Reference |
|------|-----------------|--------------|
| `src/pm/kanban.rs` | `KanbanBoard` | `// @trace FR-PM-002` |

## Related FRs

- FR-TRAC-011: Requirement Status Lifecycle

## Status

- **Current**: implemented
- **Since**: 2026-03-05
