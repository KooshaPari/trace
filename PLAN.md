# Implementation Plan — TracerTM

**Version:** 1.0
**Date:** 2026-03-27
**Status:** Active

---

## Phase 1: Core Domain and Storage

### P1.1 — Requirement Domain Model
- **Status:** Complete
- **Depends on:** —
- **Deliverable:** `Requirement`, `RequirementLink`, `Project`, `User` SQLAlchemy models with Alembic migrations. FR-{CATEGORY}-{NNN} ID format enforced at model level.

### P1.2 — PostgreSQL Repository Layer
- **Status:** Complete
- **Depends on:** P1.1
- **Deliverable:** Async repository classes in `src/tracertm/repositories/` for CRUD on all domain entities. Full test coverage via pytest-asyncio.

### P1.3 — Alembic Migration Pipeline
- **Status:** Complete
- **Depends on:** P1.1
- **Deliverable:** `alembic/` directory with versioned migrations. `alembic upgrade head` succeeds on a fresh PostgreSQL instance.

### P1.4 — Neo4j Mirror Sync
- **Status:** Complete
- **Depends on:** P1.1
- **Deliverable:** Background task that mirrors requirement nodes and dependency edges to Neo4j after each write. Cypher queries for cycle detection, impact analysis, and critical path.

---

## Phase 2: REST API and gRPC

### P2.1 — FastAPI REST Endpoints
- **Status:** Complete
- **Depends on:** P1.2
- **Deliverable:** Full CRUD REST API in `src/tracertm/api/` for requirements, traces, projects, and users. OpenAPI schema auto-generated and served at `/docs`.

### P2.2 — Proto Definitions and gRPC Service
- **Status:** Complete
- **Depends on:** P1.2
- **Deliverable:** `.proto` files in `proto/`; generated stubs in `src/tracertm/generated/`; gRPC server in `src/tracertm/grpc/`. `buf lint` passes with zero warnings.

### P2.3 — WebSocket Real-Time Collaboration
- **Status:** Complete
- **Depends on:** P2.1
- **Deliverable:** WebSocket endpoint at `/ws` delivering requirement update events to connected clients. Multi-user conflict resolution via optimistic locking (version field).

### P2.4 — MCP Server
- **Status:** Complete
- **Depends on:** P2.1
- **Deliverable:** Python MCP server in `src/tracertm/mcp/` exposing tools: `add_requirement`, `link_trace`, `get_coverage_report`, `run_impact_analysis`. JSON schema for all tools auto-generated from Pydantic models.

---

## Phase 3: Frontend Application

### P3.1 — Bun Monorepo Scaffold
- **Status:** Complete
- **Depends on:** —
- **Deliverable:** Turborepo workspace with `apps/` and `packages/` directories. `bun install && bun run build` succeeds with zero errors.

### P3.2 — RTM Matrix View
- **Status:** Complete
- **Depends on:** P3.1, P2.1
- **Deliverable:** Spreadsheet-like matrix component with requirements as rows and implementation lenses (Code, Test, API, Database, Deployment) as columns. Color-coded coverage indicators. Sortable/filterable.

### P3.3 — Graph Visualization
- **Status:** Complete
- **Depends on:** P3.1, P2.1
- **Deliverable:** Interactive dependency graph (zoom, pan, node filtering) powered by Neo4j data. Impact analysis panel showing all downstream requirements for a selected node.

### P3.4 — Kanban Board
- **Status:** Complete
- **Depends on:** P3.1, P2.1
- **Deliverable:** Drag-and-drop Kanban board with requirement state columns. Sprint planning view with capacity and burn-down tracking.

### P3.5 — Specification Verification Dashboard
- **Status:** Complete
- **Depends on:** P3.1, P2.1
- **Deliverable:** Dashboard showing VERIFIED / GAPS / INCOMPLETE status per project. Drill-down to uncovered requirements and orphaned tests. Export in JSON, CSV, HTML.

---

## Phase 4: Observability and Compliance

### P4.1 — Prometheus Metrics
- **Status:** Complete
- **Depends on:** P2.1
- **Deliverable:** Prometheus metrics exported at `/metrics`: request count, latency histograms, requirement CRUD counts, WebSocket connection gauge.

### P4.2 — Structured Logging (Loki-Compatible)
- **Status:** Complete
- **Depends on:** P2.1
- **Deliverable:** All log output structured as JSON with `level`, `ts`, `logger`, `msg`, and request context fields. Compatible with Promtail log shipping.

### P4.3 — Distributed Tracing (Jaeger)
- **Status:** Complete
- **Depends on:** P2.1
- **Deliverable:** OpenTelemetry SDK instrumentation in `src/tracertm/observability/`. Traces exported to Jaeger via OTLP. All API handlers wrapped with span creation.

### P4.4 — SLSA Provenance
- **Status:** Complete
- **Depends on:** —
- **Deliverable:** CI workflow generates SLSA provenance attestations for container images signed with cosign/Sigstore.

---

## Phase 5: Quality Gates and Security

### P5.1 — Lint and Type Check Pipeline
- **Status:** Complete
- **Depends on:** P1.1
- **Deliverable:** ruff (Python lint + format), basedpyright (type checking), golangci-lint (Go), stylelint (CSS). All gates pass with zero errors. `Taskfile.yml` targets: `lint`, `typecheck`, `quality`.

### P5.2 — Test Suite
- **Status:** Complete
- **Depends on:** P1.2, P2.1
- **Deliverable:** pytest suite in `tests/` and `src/tracertm/tests/` with `@pytest.mark.requirement("FR-XXX-NNN")` markers on all test functions. Coverage >= 80%.

### P5.3 — Security Scanning
- **Status:** Complete
- **Depends on:** P1.1
- **Deliverable:** Bandit (Python SAST), Semgrep, gitleaks, pip-audit integrated into `Taskfile.yml` quality gate. Zero high/critical findings.

### P5.4 — Load Testing
- **Status:** Complete
- **Depends on:** P2.1
- **Deliverable:** Load test suite in `load-tests/` targeting REST and WebSocket endpoints. Baseline: <500ms p95 for requirement queries at 1M+ rows.
