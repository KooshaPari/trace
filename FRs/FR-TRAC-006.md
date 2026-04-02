# FR-TRAC-006: Git Commit Message Parsing

## ID
- **FR-ID**: FR-TRAC-006
- **Repository**: Tracera
- **Domain**: LINK

## Description

The system SHALL extract requirement IDs from Git commit messages, detecting `[FR-XXX-NNN]` format in prefix and `Traces-to: FR-XXX-NNN` format in body, indexing with commit SHA, author, and timestamp.

## Acceptance Criteria

- [ ] Detects `[FR-XXX-NNN]` format
- [ ] Detects `Traces-to:` format
- [ ] Extracts SHA/author/timestamp
- [ ] Creates multiple links for multiple FRs

## Test References

| Test File | Function | FR Reference |
|-----------|----------|--------------|
| `tests/link_tests.rs` | `test_commit_parsing` | `// @trace FR-LINK-002` |

## Code References

| File | Function/Struct | FR Reference |
|------|-----------------|--------------|
| `src/link/git.rs` | `parse_commit_message()` | `// @trace FR-LINK-002` |

## Related FRs

- FR-TRAC-005: Code Annotation Parsing

## Status

- **Current**: implemented
- **Since**: 2026-02-05
