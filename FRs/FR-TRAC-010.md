# FR-TRAC-010: Impact Analysis

## ID
- **FR-ID**: FR-TRAC-010
- **Repository**: Tracera
- **Domain**: GRAPH

## Description

The system SHALL compute requirements affected by a change, returning downstream dependents with estimated impact including direct/transitive counts and tests needed.

## Acceptance Criteria

- [ ] Computes downstream dependents
- [ ] Returns impact estimation
- [ ] Response time <1s for 500+ nodes
- [ ] Visualizes impact path

## Test References

| Test File | Function | FR Reference |
|-----------|----------|--------------|
| `tests/graph_tests.rs` | `test_impact_analysis` | `// @trace FR-GRAPH-002` |

## Code References

| File | Function/Struct | FR Reference |
|------|-----------------|--------------|
| `src/graph/impact.rs` | `analyze_impact()` | `// @trace FR-GRAPH-002` |

## Related FRs

- FR-TRAC-009: Dependency DAG

## Status

- **Current**: implemented
- **Since**: 2026-02-25
