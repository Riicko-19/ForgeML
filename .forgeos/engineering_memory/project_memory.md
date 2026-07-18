# Project Memory

Long-term, durable knowledge about ForgeML that a new contributor needs and that the
code alone does not make obvious. This is not implementation detail — it is the "why"
and the "where things stand" that would otherwise live only in memory or chat.

Current state of record is always [`PROJECT_STATUS.md`](../../PROJECT_STATUS.md). This
document holds the stable context around it.

## What ForgeML is

ForgeML makes a packaged machine-learning inference workload deployable as a
predictable, observable HTTP API without requiring its operator to author Docker or
FastAPI plumbing. It is a clean, modular, self-hosted deployment path for **trusted**
models on **one server**.

It standardizes the path: package → validate → build an immutable image → deploy an
isolated local Docker container → expose a platform-managed prediction route with
health, logs, status, and basic metrics → preserve history for diagnosis and rollback.

It is **inference only**. It does not manage model development, training, or
experiments.

## What ForgeML is deliberately not

The V1 scope excludes, by charter: Kubernetes, distributed execution, multi-host
scheduling, autoscaling, multi-tenancy, user/team management, billing, a marketplace,
MLflow, DVC, training pipelines, experiments, GPU scheduling, canary traffic splitting,
and arbitrary public package execution. Authentication beyond a deployment-level
administrative boundary is deferred.

A package is a **trusted administrative artifact**, not a file accepted from untrusted
internet users. This single fact shapes the entire security model (ADR-001).

None of the excluded concepts exists in the repository, and a scope audit is expected to
keep finding nothing to remove. Adding any of them requires an ADR that opens the
milestone — none is a "small addition" (roadmap, deferred milestones).

## The shape of the system

- A **modular monolith** control plane: one FastAPI deployable hosting application and
  domain modules that talk through in-process ports and DTOs (ADR-002). Model runtimes
  are separate Docker containers.
- **Ports and adapters** throughout: storage, database, and runtime live behind ports
  owned by their consumers (ADR-007). PostgreSQL 16 and local filesystem artifacts are
  the initial adapters (ADR-009).
- **Durable operations**: validation, build, start, stop, activation, and reconciliation
  are asynchronous durable operations with correlation and idempotency (ADR-006), driven
  by a single restart-safe worker (ADR-010) with startup reconciliation recovery
  (ADR-016).
- **Desired vs observed state**: metadata is desired state and audit; Docker is observed
  state, reconciled through documented actions only (ADR-004).
- **Immutability and content addressing**: packages are identified by SHA-256 of their
  bytes; images and build contexts are immutable and labeled with their identities
  (ADR-003).

## Where knowledge lives

| Need | Location |
| --- | --- |
| How we engineer | `.forgeos/constitution/` |
| Detailed architecture | FEK docs 02–05 |
| Standards and contracts | FEK docs 07, 08, 11, 12 |
| Roadmap and gates | FEK doc 06 |
| Decisions | FEK doc 10 (ADR register); `.forgeos/decisions/` |
| Per-module detail | FEK docs 13–35 |
| Current status | `PROJECT_STATUS.md` |
| Code map | `graphify-out/` (see `CLAUDE.md`) |

## Reserved for future updates

Append durable, non-obvious project facts here as they become true — new scope
decisions, changed assumptions, cross-module lessons. Do not record implementation
detail (that belongs to the module documents) or transient status (that belongs to
`PROJECT_STATUS.md`).
