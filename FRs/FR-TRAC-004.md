# FR-TRAC-004: Requirement Search & Filtering

## ID
- **FR-ID**: FR-TRAC-004
- **Repository**: Tracera
- **Domain**: RTM

## Description

The system SHALL support full-text search and filtering by status, priority, assignee, team, epic, and coverage status with sub-500ms query times and paginated results.

## Acceptance Criteria

- [ ] Full-text search on ID/title/description
- [ ] Filter by status/priority/assignee
- [ ] Filter by coverage status
- [ ] Returns <500ms for 1M+ requirements

## Test References

| Test File | Function | FR Reference |
|-----------|----------|--------------|
| `tests/rtm_tests.rs` | `test_search_filtering` | `// @trace FR-RTM-004` |

## Code References

| File | Function/Struct | FR Reference |
|------|-----------------|--------------|
| `src/rtm/search.rs` | `search_requirements()` | `// @trace FR-RTM-004` |

## Related FRs

- FR-TRAC-003: RTM Matrix View

## Status

- **Current**: implemented
- **Since**: 2026-01-25
