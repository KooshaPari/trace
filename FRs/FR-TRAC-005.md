# FR-TRAC-005: Code Annotation Parsing

## ID
- **FR-ID**: FR-TRAC-005
- **Repository**: Tracera
- **Domain**: LINK

## Description

The system SHALL parse code annotations linking requirements to implementation, detecting `// Traces to: FR-XXX-NNN` in Go/TypeScript/Rust and `# Traces to:` in Python, extracting file path, line number, and code snippet.

## Acceptance Criteria

- [ ] Detects traces in Go/Rust/TypeScript
- [ ] Detects traces in Python
- [ ] Extracts file/line/context
- [ ] Indexes with commit SHA

## Test References

| Test File | Function | FR Reference |
|-----------|----------|--------------|
| `tests/link_tests.rs` | `test_code_annotation_parsing` | `// @trace FR-LINK-001` |

## Code References

| File | Function/Struct | FR Reference |
|------|-----------------|--------------|
| `src/link/parser.rs` | `parse_annotations()` | `// @trace FR-LINK-001` |

## Related FRs

- FR-TRAC-006: Git Commit Parsing

## Status

- **Current**: implemented
- **Since**: 2026-02-01
