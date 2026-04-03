# FR-TRAC-011: Requirement Status Lifecycle

## ID
- **FR-ID**: FR-TRAC-011
- **Repository**: Tracera
- **Domain**: PM

## Description

The system SHALL track requirements through workflow states (draft, review, approved, in_progress, testing, shipped) with Kanban board columns, state transition logging, and restrictions (can't ship without tests).

## Acceptance Criteria

- [ ] Supports all workflow states
- [ ] Kanban board columns per state
- [ ] Logs transitions with timestamp
- [ ] Enforces restrictions

## Test References

| Test File | Function | FR Reference |
|-----------|----------|--------------|
| `tests/pm_tests.rs` | `test_status_lifecycle` | `// @trace FR-PM-001` |

## Code References

| File | Function/Struct | FR Reference |
|------|-----------------|--------------|
| `src/pm/lifecycle.rs` | `StatusLifecycle` | `// @trace FR-PM-001` |

## Related FRs

- FR-TRAC-012: Kanban Board

## Status

- **Current**: implemented
- **Since**: 2026-03-01
