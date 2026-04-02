# FR-TRAC-015: Audit Trail

## ID
- **FR-ID**: FR-TRAC-015
- **Repository**: Tracera
- **Domain**: AUDIT

## Description

The system SHALL maintain an immutable audit trail of all requirement changes with timestamp, actor, change type, before/after values, and cryptographic hash chain for integrity.

## Acceptance Criteria

- [ ] Records all requirement changes
- [ ] Includes timestamp and actor
- [ ] Immutable after write
- [ ] Cryptographic hash chain

## Test References

| Test File | Function | FR Reference |
|-----------|----------|--------------|
| `tests/audit_tests.rs` | `test_audit_trail` | `// @trace FR-AUDIT-002` |

## Code References

| File | Function/Struct | FR Reference |
|------|-----------------|--------------|
| `src/audit/trail.rs` | `AuditTrail` | `// @trace FR-AUDIT-002` |

## Related FRs

- FR-TRAC-014: Evidence Management

## Status

- **Current**: implemented
- **Since**: 2026-03-20
