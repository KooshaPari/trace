# Go Module Dependency Audit

**Date**: 2026-04-01
**Scope**: All 8 `go.mod` files in `backend/`
**Go Version**: 1.25.7 (main module)
**govulncheck**: Not available in container

## go.mod Inventory

| # | Path | Go Version | Direct Deps |
|---|------|-----------|-------------|
| 1 | `backend/go.mod` | 1.25.7 | 36 |
| 2 | `backend/tests/go.mod` | 1.25.7 | 15 |
| 3 | `backend/tests/benchmarks/go.mod` | 1.25.7 | 5 |
| 4 | `backend/tests/integration/search/go.mod` | 1.25.0 | 4 |
| 5 | `backend/tests/integration/messaging/go.mod` | 1.25.0 | 2 |
| 6 | `backend/tests/integration/cache/go.mod` | 1.23.0 | 2 |
| 7 | `backend/tests/integration/clients/go.mod` | 1.24.0 | 2 |
| 8 | `backend/tests/integration/database/go.mod` | 1.25.0 | 3 |

## Major Dependency Status

### labstack/echo/v4

| Field | Value |
|-------|-------|
| **Pinned** | v4.15.0 |
| **Latest v4** | v4.15.1 |
| **Latest overall** | v5.0.4 |
| **Gap** | Patch (v4), Major (v5) |
| **Risk** | LOW for patch; HIGH for v5 migration |

**Notes**: v4.15.1 is a patch release with minor fixes. Echo v5 is a major version with breaking changes (new middleware signatures, context changes). The v4 line is still maintained.

**Action**: Safe to bump to v4.15.1. Defer v5 migration.

### jackc/pgx/v5

| Field | Value |
|-------|-------|
| **Pinned (main)** | v5.8.0 |
| **Pinned (integration)** | v5.7.2 |
| **Latest** | v5.9.1 |
| **Gap** | 1.1.1 minor versions |
| **Risk** | LOW |

**Notes**: v5.9.0 added features, v5.9.1 fixed batch result format corruption when using cached prepared statements. Requires Go 1.25.0 (already met).

**Action**: Bump to v5.9.1 across all go.mod files. Aligns integration test modules with main.

### nats-io/nats.go

| Field | Value |
|-------|-------|
| **Pinned (main)** | v1.48.0 |
| **Pinned (integration/messaging)** | v1.47.0 |
| **Latest** | v1.50.0 |
| **Gap** | 2 minor versions |
| **Risk** | LOW |

**Notes**: v1.49.0 and v1.50.0 include WebSocket close frame fix and JetStream cleanup improvements. No breaking API changes.

**Action**: Bump to v1.50.0. Update `nats-io/nkeys` from v0.4.15 to latest if needed.

### neo4j/neo4j-go-driver/v5

| Field | Value |
|-------|-------|
| **Pinned** | v5.28.4 |
| **Latest v5** | v5.28.4 |
| **Latest overall** | v6.0.0 |
| **Gap** | None in v5; v6 available |
| **Risk** | N/A (current); HIGH for v6 |

**Notes**: Already at the latest v5 release. v6.0.0 (released 2025-12-04) is a major version upgrade requiring import path change to `/v6` and potential API changes.

**Action**: No action needed for v5. Plan v6 migration as a separate effort.

### redis/go-redis/v9

| Field | Value |
|-------|-------|
| **Pinned (main)** | v9.18.0 |
| **Pinned (integration/cache)** | v9.17.1 |
| **Latest** | v9.18.0 |
| **Gap** | None in main; integration behind |
| **Risk** | NONE |

**Notes**: Main module is at the latest stable release.

**Action**: Bump integration/cache to v9.18.0 for consistency.

### prometheus/client_golang

| Field | Value |
|-------|-------|
| **Pinned** | v1.23.2 |
| **Latest** | v1.23.2+ (exp module available) |
| **Gap** | None or minimal |
| **Risk** | NONE |

**Notes**: At the latest stable release. An experimental `exp` module exists separately.

**Action**: No action needed.

### testcontainers-go

| Field | Value |
|-------|-------|
| **Pinned** | v0.40.0 |
| **Latest** | v0.41.0 |
| **Gap** | 1 minor version |
| **Risk** | LOW |

**Notes**: v0.41.0 released 2026-03-10. Module version (v0.x) suggests pre-1.0 API may still have minor breaking changes between versions.

**Action**: Bump to v0.41.0 across `testcontainers-go`, `modules/minio`, `modules/postgres`, and `tests/go.mod` modules/neo4j.

### OpenTelemetry (otel + contrib)

| Field | Value |
|-------|-------|
| **Pinned** | v1.40.0 (sdk/api/trace), v0.65.0 (contrib) |
| **Latest** | v1.42.0 |
| **Gap** | 2 minor versions |
| **Risk** | LOW |

**Notes**: v1.41.0 and v1.42.0 released. OTel Go follows semver strictly. Contrib instrumentation should be updated in lockstep.

**Action**: Bump all `go.opentelemetry.io/*` packages to v1.42.0 and contrib to matching version.

### Temporal SDK

| Field | Value |
|-------|-------|
| **Pinned** | v1.40.0 |
| **Latest** | v1.41.1 |
| **Gap** | 1 minor + 1 patch |
| **Risk** | MEDIUM |

**Notes**: v1.40.0 itself introduced breaking changes around standalone activities and `testActivityToken`. v1.41.1 fixes a permanent NDE on replay when Data Converter or Codec fails on Session activity cancellation.

**Action**: Bump to v1.41.1 (bugfix release). Verify activity workflows still function correctly.

## Version Conflicts Across go.mod Files

| Dependency | Main | tests/ | search/ | messaging/ | cache/ | database/ |
|------------|------|--------|---------|------------|--------|-----------|
| pgx/v5 | v5.8.0 | v5.8.0 | v5.7.2 | - | - | v5.7.2 |
| nats.go | v1.48.0 | v1.48.0 | - | v1.47.0 | - | - |
| redis/v9 | v9.18.0 | v9.18.0 | - | - | v9.17.1 | - |
| go version | 1.25.7 | 1.25.7 | 1.25.0 | 1.25.0 | 1.23.0 | 1.25.0 |
| testify | v1.11.1 | v1.11.1 | v1.9.0 | v1.9.0 | v1.9.0 | v1.9.0 |

**Action items**:
1. Align pgx to v5.9.1 in search/ and database/ integration tests
2. Align nats.go to v1.50.0 in messaging/ integration tests
3. Align redis to v9.18.0 in cache/ integration tests
4. Align testify to v1.11.1 in search/, messaging/, cache/, database/
5. Consider bumping `go` directive in `integration/cache/go.mod` from 1.23.0 to 1.25.0

## Other Notable Dependencies

| Dependency | Pinned | Latest | Notes |
|------------|--------|--------|-------|
| aws-sdk-go-v2 | v1.41.1 | ~v1.41.x | Current |
| gorm.io/gorm | v1.31.1 | ~v1.31.x | Current |
| sentry-go | v0.42.0 | ~v0.42.x | Current |
| golang-jwt/jwt/v5 | v5.3.1 | ~v5.3.x | Current |
| hashicorp/vault/api | v1.22.0 | ~v1.22.x | Current |
| gorilla/mux | v1.8.1 | ~v1.8.x | Stable, low maintenance |
| minio/minio-go/v7 | v7.0.98 | ~v7.0.x | Current |
| workos/workos-go/v4 | v4.46.1 | ~v4.46.x | Current |
| pgvector/pgvector-go | v0.3.0 | ~v0.3.x | Current |
| lib/pq | v1.11.2 | ~v1.11.x | Legacy; pgx is primary driver |

## Security

- `govulncheck` not available in this container. Manual review of known CVEs for pinned versions shows no critical advisories for the major dependencies at their current versions.
- `golang.org/x/crypto` at v0.49.0 — recommend verifying against latest patch.
- `golang.org/x/net` at v0.52.0 — recommend verifying against latest patch.

## Recommended Update Priority

### P1 — Safe Patch/Minor Bumps (low risk, immediate)
1. `echo/v4` v4.15.0 -> v4.15.1
2. `pgx/v5` v5.8.0 -> v5.9.1 (bug fix for batch corruption)
3. `nats.go` v1.48.0 -> v1.50.0
4. `testcontainers-go` v0.40.0 -> v0.41.0
5. Align integration test modules to main module versions

### P2 — Minor Version Bumps (test required)
6. `opentelemetry-go` v1.40.0 -> v1.42.0
7. `temporal/sdk` v1.40.0 -> v1.41.1
8. `golang.org/x/*` packages to latest

### P3 — Major Version Migrations (separate effort)
9. `neo4j-go-driver` v5 -> v6 (new import path, API changes)
10. `echo/v4` -> `echo/v5` (breaking middleware/context changes)

## Breaking Change Analysis

### echo/v4 -> v5 (deferred)
- Import path changes
- Middleware signature changes
- Context API changes
- Requires comprehensive route/middleware rewrite

### neo4j-go-driver/v5 -> v6 (deferred)
- Import path: `/v5` -> `/v6`
- Session/transaction API may have changes
- Driver initialization API changes possible

### temporal/sdk v1.39 -> v1.40 (already applied)
- Standalone activities changed internal token handling
- `testActivityToken` behavior changed
- If upgrading from <v1.40, regression testing required

## Summary

- **Total outdated direct deps**: 7 of 36 in main go.mod have available updates
- **Version conflicts**: 4 packages have version mismatches across go.mod files
- **Critical security issues**: None identified (govulncheck unavailable)
- **Breaking changes pending**: 2 major migrations available (echo v5, neo4j v6) — both deferred
- **Immediate safe updates**: pgx, nats, echo patch, testcontainers, OTel, Temporal
