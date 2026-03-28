# Architecture Decision Records — TracerTM

**Project:** TracerTM (Requirements Traceability Matrix)
**Last Updated:** 2026-03-27

---

## ADR-001: Python Backend with FastAPI
**Date:** 2026-03-25
**Status:** Accepted

**Context:** TracerTM requires a backend capable of serving REST and gRPC endpoints, integrating with PostgreSQL, Neo4j, and Redis, and supporting async I/O for WebSocket collaboration. Python was the team's primary language for ML/NLP workloads (requirement classification, embedding generation).

**Decision:** Use Python 3.13 with FastAPI as the HTTP framework and Hatchling as the build backend. The package is published as `tracertm` via `pyproject.toml`.

**Consequences:**
- FastAPI provides async-first request handling and auto-generated OpenAPI docs.
- Python's ML ecosystem (sentence-transformers, scikit-learn) is available for embedding-based search without a separate service.
- Trade-off: Python is slower than Go/Rust for CPU-bound tasks; mitigated by keeping heavy computation in background tasks.

---

## ADR-002: Bun Monorepo for Frontend
**Date:** 2026-03-25
**Status:** Accepted

**Context:** The frontend spans a main application (`apps/`) and shared packages (`packages/`). A monorepo build system is needed that supports TypeScript throughout and fast install/build cycles.

**Decision:** Use Bun as the package manager and runtime with Turborepo (`turbo.json`) for task orchestration across workspace packages.

**Consequences:**
- Bun's native TypeScript execution and fast installs accelerate CI.
- Turborepo caches build artifacts across packages, reducing rebuild time.
- Turborepo's task graph ensures packages are built in dependency order.

---

## ADR-003: PostgreSQL as Primary Relational Store
**Date:** 2026-03-25
**Status:** Accepted

**Context:** Requirements, traces, projects, and users have well-defined relational structure with foreign key constraints. ACID compliance is required for audit log integrity.

**Decision:** PostgreSQL via SQLAlchemy async ORM (`asyncpg` driver). Migrations managed with Alembic.

**Consequences:**
- Full ACID compliance for requirement and trace mutations.
- Alembic provides version-controlled schema migrations.
- Trade-off: PostgreSQL is a network dependency; local-only workflows require Docker or a local install.

---

## ADR-004: Neo4j for Dependency Graph Queries
**Date:** 2026-03-25
**Status:** Accepted

**Context:** Requirement dependency graphs require efficient transitive traversal (impact analysis, cycle detection, critical path). Relational self-joins on large graphs are slow and complex.

**Decision:** Neo4j Community Edition for graph-based queries. Requirement nodes and dependency edges are mirrored from PostgreSQL to Neo4j asynchronously.

**Consequences:**
- Cypher queries express impact analysis and cycle detection concisely.
- Data is eventually consistent between PostgreSQL (source of truth) and Neo4j (query store).
- Trade-off: additional infrastructure dependency; mitigated by making Neo4j optional for non-graph queries.

---

## ADR-005: gRPC Service Layer
**Date:** 2026-03-25
**Status:** Accepted

**Context:** Agent-to-service communication requires low-latency, typed message passing. REST is adequate for human clients but gRPC provides better throughput for agent automation workloads.

**Decision:** Expose a gRPC service layer (`src/tracertm/grpc/`) with proto definitions in `proto/`. The gRPC service mirrors the core REST API surface.

**Consequences:**
- Strongly typed proto-defined contracts prevent schema drift between client and server.
- gRPC streaming enables real-time event push to agent subscribers.
- Trade-off: proto compilation step added to CI; `buf` is used for proto linting and generation.

---

## ADR-006: MCP Server for AI Agent Integration
**Date:** 2026-03-25
**Status:** Accepted

**Context:** Claude Code and compatible AI agents use the Model Context Protocol (MCP) for structured tool interactions. A dedicated MCP adapter enables agents to read and write requirements without raw HTTP calls.

**Decision:** Implement a Python MCP server (`src/tracertm/mcp/`) that exposes requirement CRUD, trace linking, and coverage queries as MCP tools.

**Consequences:**
- Agents can use `add_requirement`, `link_trace`, `get_coverage_report` as first-class tools.
- MCP tools are strongly typed with JSON schema definitions auto-generated from Pydantic models.

---

## ADR-007: Observability via Prometheus, Loki, Jaeger
**Date:** 2026-03-25
**Status:** Accepted

**Context:** Production deployments need metrics, structured logs, and distributed traces. A unified observability stack simplifies dashboards and on-call tooling.

**Decision:** Prometheus for metrics (via `prometheus-client`), Loki for log aggregation (structured JSON logs shipped via Promtail), Jaeger for distributed tracing (OpenTelemetry SDK).

**Consequences:**
- All three systems are OSS and self-hostable.
- OpenTelemetry SDK provides vendor-neutral instrumentation.
- Trade-off: three additional services in `docker-compose.yml`; local development uses `docker-compose.yml` to start all dependencies.

---

## ADR-008: SLSA Provenance and Signed Attestations
**Date:** 2026-03-25
**Status:** Accepted

**Context:** Enterprise compliance requires verifiable provenance for deployed artifacts. SLSA level 2 is the minimum for regulated environments.

**Decision:** Generate SLSA provenance attestations for container images and package artifacts in CI. Attestations signed with Sigstore/cosign.

**Consequences:**
- SLSA provenance enables consumers to verify artifact integrity without trusting the CI pipeline alone.
- Sigstore/cosign is OSS and requires no paid key management service.
