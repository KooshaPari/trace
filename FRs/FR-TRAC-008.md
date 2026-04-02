# FR-TRAC-008: Jest Test Parsing

## ID
- **FR-ID**: FR-TRAC-008
- **Repository**: Tracera
- **Domain**: TEST

## Description

The system SHALL extract requirement IDs from Jest test names, parsing `describe("FR-XXX-NNN: description", () => {})` format, correlating test execution results with requirements and calculating coverage percentage.

## Acceptance Criteria

- [ ] Parses `describe("FR-XXX-NNN:` format
- [ ] Extracts test file/suite/line
- [ ] Correlates pass/fail/skip
- [ ] Calculates coverage per requirement

## Test References

| Test File | Function | FR Reference |
|-----------|----------|--------------|
| `tests/test_parser_tests.rs` | `test_jest_parsing` | `// @trace FR-TEST-002` |

## Code References

| File | Function/Struct | FR Reference |
|------|-----------------|--------------|
| `src/test/jest.rs` | `parse_jest_tests()` | `// @trace FR-TEST-002` |

## Related FRs

- FR-TRAC-007: Pytest Marker Parsing

## Status

- **Current**: implemented
- **Since**: 2026-02-15
