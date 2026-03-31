# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.1] - 2026-03-29

### Added
- Evidence gallery with lightbox UI component (#240)
- Geist dark theme overhaul with hover-expand tooltips and clickable timeline cards (#242, #209, #212)
- Perf benchmarks and topo-sort unit tests (#247)
- Go benchmark CI workflow (#256)
- Docs-site scaffold and verification harness (#259)
- ADR.md with 12 architecture decisions derived from codebase (#253)
- Root-level PRD.md and PLAN.md spec documents (#244)
- Process-compose.yml for local dev stack (#214)
- Automated alert-to-issue sync workflow (#185)

### Changed
- Migrated top 20 TODOs to GitHub Issues (#238)
- Modernized tooling to 2026 standards (#193)
- Replaced BMAD/spec-kitty with AgilePlus governance (#195)
- Migrated kitty-specs to AgilePlus format, archived BMAD refs (#211)
- Unified docs IA with VitePress super-categories (#154)
- Added no-new-todos and markdownlint precommit hooks (#239)

### Fixed
- TypeScript errors in web frontend (#260)
- Vite 8 beta + rolldown build failures (#251)
- @types/react and @types/react-dom missing dev dependencies (#257)
- YAML syntax errors in ci.yml and qa-governance.yml (#241, #215)
- Node OOM on tsc --build — increased heap size (#246)
- Tailwind/Geist UI types-node upgrade (#249)
- phenodocsTheme undefined breaking VitePress build (#216)
- @types/node for tailwind.config.ts type resolution (#213)
- Broken CI workflow configurations (#221)
- Duplicate 'with' key in setup-node step (#255)
- Removed duplicated governance blocks, referenced thegent templates (#210)

### Security
- Untracked vault tokens, env files, and k8s secrets (#206)

## [2.0.0] - 2026-02-23

### Added
- **TraceRTM v2 Architecture** - Complete specification-driven development system
  - ADR-0001: Layered Transformation approach with 4 new layers
  - Specification Engine with ADR management, formal contracts, invariant engine
  - BDD Scenario Engine with Gherkin parser and step definitions
  - Visual UI Engine with graph canvas, RTM heat maps, coverage dashboards
  - MCP Native CLI using FastMCP 2.14+ for AI agent integration

- **FastMCP Integration** (ADR-0002)
  - MCP server with 50+ tools for AI agent interaction
  - Support for stdio, HTTP, and SSE transports
  - Bearer auth and JWT verification support

- **Frontend Implementation**
  - React/TypeScript application with MobX state management
  - Graph visualization using Cytoscape.js
  - Monaco code editor integration
  - MSW for API mocking in tests

- **Backend Services** (Go)
  - RESTful API with FastAPI
  - NATS messaging integration
  - MinIO object storage support
  - PostgreSQL database with SQLAlchemy ORM

- **Comprehensive Test Suite**
  - Phase 1-9 test coverage initiatives completed
  - 1,400+ tests across CLI, API, services, and E2E
  - Pytest-asyncio configuration for async testing
  - 92.6% pass rate achieved

- **Documentation System**
  - 15 Architecture Decision Records (ADR-0001 through ADR-0015)
  - Product Requirements Document (PRD)
  - Functional Requirements (FR-1 through FR-50+)
  - Organized docs/ structure with guides, reference, research, reports

- **Graph Data Structure** (ADR-0014)
  - NetworkX-based graph implementation
  - Impact analysis algorithms
  - Shortest path calculations
  - Coverage analysis

- **Import/Export Capabilities** (ADR-0015)
  - Multiple format support
  - Bulk operations
  - Data migration tools

### Changed
- Migrated from CRUD-based to specification-driven development
- Transitioned from basic CLI to MCP-native tooling
- Enhanced from simple list views to visual graph interfaces

### Deprecated
- Basic list/detail views (replaced by graph visualization)
- Standalone CLI commands (superseded by MCP tools)

### Removed
- Legacy non-MCP command structure

### Fixed
- 67+ failing tests fixed in Phase 1
- CLI command structure refactored
- Storage layer mocking patterns established
- Async test configuration issues resolved

### Security
- JWT authentication provider integration
- Bearer auth support for MCP server

## [1.1.0] - 2025-01-31

### Added
- Initial stable changelog release entry.

## [1.0.0] - 2025-11-29

### Added
- Initial project release.
