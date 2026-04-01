# ADR-0016: MCP-Native Agent Dispatch Pattern

**Status:** Accepted
**Date:** 2026-04-01
**Deciders:** Development Team
**Supersedes:** N/A

---

## Context

TracerTM's multi-agent development workflow requires a structured dispatch system to coordinate parallel AI agents across a shared codebase. Existing agent coordination (ADR-0013) focused on swarm patterns and checkpoint/restore, but lacked a formalized dispatch model with role-based specialization, lifecycle state machines, and convoy-level coordination.

The Gastown integration introduces:
1. **Polecat agents:** Autonomous workers (named after Mustelidae) that execute discrete work items
2. **Beads:** Atomic units of work with a defined lifecycle state machine
3. **Convoys:** Groups of related beads coordinated toward a shared objective
4. **MCP (Model Context Protocol) tooling:** Standardized interfaces for agent-to-orchestrator communication

KiloCode's Architect/Coder/Debugger role pattern provides the foundation for agent specialization, ensuring each agent operates within a bounded responsibility scope.

## Decision

We will implement an MCP-native agent dispatch pattern built on three pillars:

1. **Role-based agent taxonomy** (Architect, Coder, Debugger — from KiloCode)
2. **Bead lifecycle state machine** (open → in_progress → in_review → closed)
3. **Convoy coordination** via `gt_sling` / `gt_sling_batch` dispatch primitives

All agent coordination will flow through MCP tool calls, with the orchestrator (Gastown) maintaining global state.

## Rationale

### Agent Role Taxonomy

Derived from KiloCode's proven multi-mode pattern, agents are classified by capability scope:

```
┌─────────────────────────────────────────────────────────┐
│                    Gastown Orchestrator                   │
│  (TownDO — manages rig lifecycle, triage, merge queue)   │
│                                                           │
│  Responsibilities:                                        │
│    ├─ Bead lifecycle management                           │
│    ├─ Agent dispatch (sling)                             │
│    ├─ Triage & escalation routing                        │
│    └─ Merge queue / refinery coordination                │
└──────────────────────────┬──────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌─────▼──────┐  ┌──────▼──────┐
   │  Architect   │  │   Coder    │  │  Debugger    │
   │              │  │            │  │              │
   │  - ADRs      │  │  - Features│  │  - Bug fixes │
   │  - Design    │  │  - Tests   │  │  - Failures  │
   │  - Review    │  │  - Refactor│  │  - Perf      │
   │  - Spec      │  │  - Docs    │  │  - Diagnose  │
   └─────────────┘  └────────────┘  └─────────────┘
```

**Role mapping to KiloCode modes:**

| KiloCode Mode | Gastown Role | Bead Types Handled |
|---------------|-------------|-------------------|
| Architect | Architect agent | `convoy`, `design`, review requests |
| Code | Coder agent (polecat) | `issue`, `merge_request` |
| Debug | Debugger agent | `escalation`, hotfix, diagnostic |
| Ask | Orchestrator (TownDO) | `triage_request`, coordination |

**Why this pattern:**
- Bounded responsibility prevents agents from overstepping (e.g., coders don't merge)
- Role-specific context windows reduce token usage (coder doesn't need ADR history)
- KiloCode validation: proven across 10K+ agent sessions

### Bead Lifecycle State Machine

Each bead (work item) follows a deterministic state machine:

```
                    ┌──────┐
         create ──▶ │ open │
                    └──┬───┘
                       │ gt_sling (assign to agent)
                       ▼
                  ┌───────────┐
                  │in_progress│ ◀─── agent working, checkpointing
                  └─────┬─────┘
                       │ gt_done (push branch, submit review)
                       ▼
                  ┌───────────┐
                  │ in_review │ ◀─── refinery reviews
                  └─────┬─────┘
                        │
              ┌─────────┴─────────┐
              │                   │
              ▼                   ▼
     ┌──────────────┐    ┌──────────────┐
     │   closed     │    │ in_progress  │
     │  (merged)    │    │  (rework)    │
     └──────────────┘    └──────────────┘
```

**State transitions:**

| From | To | Trigger | Actor |
|------|----|---------|-------|
| — | `open` | Bead created | Orchestrator / user |
| `open` | `in_progress` | `gt_sling` assigns agent | Orchestrator |
| `in_progress` | `in_review` | `gt_done` — agent signals complete | Agent (polecat) |
| `in_review` | `closed` | Review passes, branch merged | Refinery |
| `in_review` | `in_progress` | `gt_request_changes` — rework needed | Refinery |
| any | `closed` | `gt_bead_close` — manual close | Orchestrator |

**Bead types:**

| Type | Purpose | Typical Role |
|------|---------|-------------|
| `issue` | Implementation task | Coder |
| `merge_request` | Code review request | Refinery (Architect) |
| `convoy` | Multi-bead coordination | Architect |
| `escalation` | Blocked/unresolved issue | Debugger |
| `triage_request` | Needs human/triage decision | Orchestrator |

### Convoy Coordination

Convoys group related beads toward a shared feature branch. Each convoy:
- Has a unique ID and feature branch (e.g., `convoy/trace-stabilization/ccb126c4/head`)
- Tracks child beads via `parent_bead_id` / `convoy_id` metadata
- Merges all child branches into the convoy feature branch
- The convoy feature branch merges into `main` when all beads complete

```
convoy/feature-x/abc123/head
├── convoy/feature-x/abc123/gt/coder-1/task-a   (polecat branch)
├── convoy/feature-x/abc123/gt/coder-2/task-b   (polecat branch)
├── convoy/feature-x/abc123/gt/debugger/task-c  (polecat branch)
└── convoy/feature-x/abc123/gt/architect/review (refinery branch)
```

### Dispatch Model: gt_sling / gt_sling_batch

Agent dispatch uses two primitives:

**`gt_sling(bead_id, agent_id)`** — Assign a single bead to an agent:
```bash
# Assign bead to a polecat coder
gt_sling 5cd7d4db-4222-476d-ac45-866ad85fcc36 2993b274-e877-441e-9e21-5d9209a06292
```

**`gt_sling_batch(bead_ids, agent_id)`** — Assign multiple beads to an agent (or distribute):
```bash
# Batch dispatch for wave execution
gt_sling_batch "bead-1 bead-2 bead-3 bead-4" agent-pool-coders
```

**Dispatch flow:**
1. Orchestrator identifies ready beads (dependencies met, no agent assigned)
2. Orchestrator matches bead type → agent role (issue → Coder, escalation → Debugger)
3. Orchestrator calls `gt_sling` or `gt_sling_batch`
4. Agent receives bead context via `gt_prime` (auto-injected on session start)
5. Agent works, checkpoints via `gt_checkpoint`, signals via `gt_done`
6. Orchestrator routes to review queue or rework

**Agent coordination primitives:**

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `gt_prime` | Refresh agent context (hooked bead, mail, open beads) | Session start, context refresh |
| `gt_bead_status` | Inspect bead state | Before dispatch, during review |
| `gt_bead_close` | Force-close a bead | Stale/cancelled work |
| `gt_done` | Agent signals work complete, push branch | End of bead execution |
| `gt_mail_send` | Async message to another agent | Cross-agent coordination |
| `gt_mail_check` | Read pending messages | Periodic polling |
| `gt_escalate` | Create escalation bead | Agent is blocked |
| `gt_checkpoint` | Write crash-recovery state | After significant progress |
| `gt_status` | Dashboard status update | Phase transitions |
| `gt_request_changes` | Reject review, trigger rework | Refinery review failure |

## Alternatives Rejected

### Alternative 1: Monolithic Single-Agent Workflow

- **Description:** One agent handles all work types (design, code, debug, review)
- **Pros:** Simple coordination, no dispatch overhead
- **Cons:** Context overload (1M tokens fills fast), no specialization, sequential bottleneck
- **Why Rejected:** KiloCode's mode-separated pattern proven 10x faster. Single agent can't parallelize across 20+ beads.

### Alternative 2: Pure LLM-Orchestrated Dispatch

- **Description:** Let the LLM decide agent routing based on natural language
- **Pros:** Flexible, no rigid state machine
- **Cons:** Non-deterministic, can't guarantee lifecycle invariants, hard to debug
- **Why Rejected:** State machine ensures predictable lifecycle transitions. LLM routing adds latency and cost without reliability benefit.

### Alternative 3: GitHub Actions as Orchestrator

- **Description:** Use GitHub Actions workflow_dispatch for agent coordination
- **Pros:** Native CI integration, existing infrastructure
- **Cons:** No state persistence, no real-time coordination, rate-limited, opaque failure modes
- **Why Rejected:** Gastown provides stateful orchestration with bead persistence, real-time mail, and escalation routing. GitHub Actions are stateless by design.

### Alternative 4: Direct Agent-to-Agent Communication

- **Description:** Agents communicate directly without orchestrator mediation
- **Pros:** Lower latency, simpler protocol
- **Cons:** Race conditions (two agents editing same file), no global visibility, no audit trail
- **Why Rejected:** Anti-pattern from ADR-0013 — agent conflict loops when multiple agents edit same file. Orchestrator provides serialization and conflict resolution.

## Consequences

### Positive

- **Role specialization:** Each agent operates within bounded context, reducing token usage by ~40%
- **Deterministic lifecycle:** Bead state machine prevents orphaned work, ensures review coverage
- **Convoy parallelism:** Multiple beads execute simultaneously within a convoy, 5-10x throughput vs sequential
- **Crash recovery:** `gt_checkpoint` + bead persistence means work resumes after container restart
- **Audit trail:** Every state transition logged, bead history queryable via `gt_bead_status`
- **MCP-native:** All coordination via standardized MCP tools — no custom protocols, composable with other MCP servers

### Negative

- **Orchestrator single point of failure:** Gastown orchestrator down → no dispatch, no reviews
- **State machine rigidity:** Edge cases (emergency hotfix, cross-convoy dependency) require manual override
- **Learning curve:** New agents must understand bead lifecycle, tool vocabulary, role boundaries
- **Overhead for simple tasks:** Single-file fix still requires full bead lifecycle (create → dispatch → work → review → close)

### Neutral

- **Naming convention:** Polecat/Mustelidae theme is project-specific; can be abstracted
- **Branch naming:** Convoy branch structure is convention, not enforced by git
- **Mail vs nudge:** Two communication channels (async mail, real-time nudge) — agents must choose appropriately

## Implementation

### Affected Components

- `AGENTS.md` — Agent handbook with tool vocabulary and workflow
- `docs/adr/ADR-0016-mcp-native-agent-dispatch.md` — This ADR
- `docs/02-architecture/ROOT_ORCHESTRATOR_DESIGN.md` — Orchestrator design (existing)
- Gastown orchestration layer (external, MCP tools: `gt_sling`, `gt_prime`, `gt_done`, etc.)
- Rig configuration (worktree-per-agent, pre-configured branches)

### Migration Strategy

**Phase 1: Foundation (Complete)**
- Bead lifecycle state machine implemented in Gastown
- Core MCP tools available (`gt_prime`, `gt_sling`, `gt_done`, `gt_checkpoint`)
- Polecat agent role established

**Phase 2: Convoy Coordination (Current)**
- Convoy feature branch model operational
- `gt_sling_batch` for wave dispatch
- Cross-convoy dependency tracking via metadata

**Phase 3: Advanced Patterns (Planned)**
- Automated role assignment based on bead labels
- Dynamic agent pool scaling
- Cross-rig dispatch (multi-rig convoys)
- Refinery automation (auto-approve low-risk reviews)

### Rollout Plan

- **Phase 1:** Single-agent beads, manual dispatch — validate lifecycle
- **Phase 2:** Convoy coordination, batch dispatch — validate parallelism
- **Phase 3:** Full automation — orchestrator dispatches without human intervention

### Success Criteria

- [x] Bead lifecycle state machine operational (open → in_progress → in_review → closed)
- [x] `gt_sling` single-bead dispatch functional
- [x] `gt_checkpoint` crash recovery tested
- [x] Convoy feature branches merge correctly
- [ ] `gt_sling_batch` wave dispatch validated across 5+ concurrent beads
- [ ] Cross-convoy dependency resolution
- [ ] <30s dispatch latency (bead creation → agent receiving work)
- [ ] >95% bead completion rate (beads reaching `closed` without manual intervention)

## References

- [ADR-0013: AI Agent Coordination Architecture](ADR-0013-ai-agent-coordination.md)
- [ADR-0002: FastMCP 2.14 Integration](ADR-0002-fastmcp-2-14-integration.md)
- [ROOT_ORCHESTRATOR_DESIGN.md](../02-architecture/ROOT_ORCHESTRATOR_DESIGN.md)
- [AGENTS.md](../../AGENTS.md) — Agent handbook and tool reference
- [KiloCode Multi-Mode Pattern](https://kilo.ai/docs)

---

**Notes:**
- **Naming:** Polecat agents named after Mustelidae (weasel family) — Maple, Flint, Reed, Thorn, Dusk, Slate, Pike
- **Rig isolation:** Each rig has isolated worktrees; agents cannot modify files outside their worktree
- **Refinery:** Review queue that processes `in_review` beads; refiners can approve (`gt_bead_close`) or reject (`gt_request_changes`)
- **Escalation path:** Polecat → Debugger → Architect → TownDO (orchestrator) → Mayor (human)
- **Token budget:** Polecat agents target <100K tokens per bead; complex beads may split into sub-beads
