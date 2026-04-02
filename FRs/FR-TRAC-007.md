# FR-TRAC-007: Pytest Marker Parsing

## ID
- **FR-ID**: FR-TRAC-007
- **Repository**: Tracera
- **Domain**: TEST

## Description

The system SHALL extract requirement IDs from pytest test markers, parsing `@pytest.mark.requirement("FR-XXX-NNN")` and `@pytest.mark.trace("FR-XXX-NNN")`, correlating test results (pass/fail/skip) with requirements.

## Acceptance Criteria

- [ ] Parses `@pytest.mark.requirement`
- [ ] Parses `@pytest.mark.trace`
- [ ] Correlates test results
- [ ] Calculates coverage percentage

## Test References

| Test File | Function | FR Reference |
|-----------|----------|--------------|
| `tests/test_parser_tests.rs` | `test_pytest_parsing` | `// @trace FR-TEST-001` |

## Code References

| File | Function/Struct | FR Reference |
|------|-----------------|--------------|
| `src/test/pytest.rs` | `parse_pytest_markers()` | `// @trace FR-TEST-001` |

## Related FRs

- FR-TRAC-008: Jest Test Parsing

## Status

- **Current**: implemented
- **Since**: 2026-02-10
