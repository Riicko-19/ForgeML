# Module History

Concise, durable summaries of each module: what changed, why it mattered, and what
architectural capability it introduced. This is not a reimplementation of the module
documents — it is the memory of the project's shape over time. Detailed authority is the
per-module FEK document; current status is
[`PROJECT_STATUS.md`](../../PROJECT_STATUS.md).

Status legend: **Frozen** (CI evidence on the frozen SHA) · **Implemented, freeze
pending CI** · **Not started**.

---

## Module 0 — Foundation · Frozen (2026-07-13)

**What changed.** Typed fail-closed configuration, explicit application composition, a
safe error envelope, server-owned request IDs, bounded JSON logging, health endpoints,
and the quality gates.

**Why it mattered.** It established that the system boots without provider side effects
and fails closed on misconfiguration, and it fixed the error-envelope and correlation-ID
contracts that every later module reuses for free.

**Capability introduced.** A composable, observable, fail-closed control-plane skeleton.

**Note.** Frozen under the one-time evidence exception in ADR-014 (no usable repository
or remote existed at the time). The exception is closed and extends to no later module.
Baseline `fdc1e9e`.

---

## Module 1 — Forge Package System · Frozen (2026-07-14)

**What changed.** The `.forge` package format (format version 1, closed manifest),
manifest parsing and validation, JSON Schema Draft 2020-12 validation with depth and node
bounds, exact PEP 508 dependency pins (ADR-011), content-addressed artifact storage with
atomic writes (ADR-003, ADR-007), safe archive extraction into caller-owned staging, and
the package validation service.

**Why it mattered.** It froze the package contract — the format, the finding codes, and
the `ArtifactStore` / `ArchiveReader` ports — that everything downstream depends on. The
validator executes no package code.

**Capability introduced.** A deterministic, safe, content-addressed package intake.

**Evidence.** 224 tests, 99% branch coverage; CI `success` on the frozen baseline
`4aa140c`.

---

## Module 2 — Metadata Layer · Frozen (2026-07-14)

**What changed.** A PostgreSQL 16 metadata layer: SQLAlchemy models, an Alembic migration
with immutability triggers, the `PackageCatalog` / `OperationStore` / `AuditLog` ports and
their `UnitOfWork`, in-memory fakes held to the same conformance suite as the real
adapters, and the operation lease / crash-recovery / retry mechanism (ADR-016).

**Why it mattered.** It made concurrency the database's job, never application code's:
idempotent writes are INSERTs that expect to lose a race and read the winner. Triggers
enforce immutability even against an operator with a `psql` prompt. It also supplied the
restart-safe recovery mechanism (`recover_orphaned`) that ADR-006/010 required but had not
specified.

**Capability introduced.** Durable, concurrency-safe, audited desired-state persistence
behind conformance-pinned ports.

**Evidence.** 366 tests, 99% branch coverage; CI `success` on the frozen baseline
`2c8c872` (with a PostgreSQL 16 service, without which the concurrency and migration gates
cannot run).

---

## Module 3 — Backend API · Implemented, freeze pending CI

**What changed.** Commands and queries, the operation resource, and error mapping:
`POST /v1/packages` (streaming, idempotent, `202` + operation), `GET /v1/packages`,
`GET /v1/packages/{id}`, `GET /v1/operations/{id}`, a published OpenAPI schema,
database-backed readiness, and ADR-016 crash recovery wired at startup.

**Why it mattered.** It exposed the frozen package/metadata contracts over HTTP while
reusing the error envelope, correlation ID, idempotency index, and transaction boundary
that Modules 0–2 already froze — almost all risk concentrated in one service file. It also
surfaced the largest standing risk: no authentication on a code-executing API (needs an
ADR).

**Capability introduced.** A contract-tested, idempotent HTTP intake for packages and
operations.

**Evidence (local).** 411 tests, 99% branch coverage; mypy strict / ruff / black clean;
no import cycles. Freeze awaits passing CI on the frozen SHA (ADR-014).

---

## Module 4 — Analyzer / Generator · Implemented, freeze pending CI

**What changed.** A pure inference-contract analyzer (`analyze()`) that derives the
contract from the validated manifest with no Docker or storage access; persistence of the
analyzed contract into the previously reserved nullable `PackageValidation.contract`
field; and a deterministic runtime artifact generator whose identity is a SHA-256 over the
canonically serialized generated file set.

**Why it mattered.** It activated a documented extension point (nullable JSONB column,
reversible, backwards compatible) rather than reopening Module 2, and it established that
identical `(contract, generator version, runtime, checksum)` inputs produce byte-identical
artifacts — the foundation for reproducible builds. Analyzer and generator are pure
functions, following the `validate_package` precedent, because they perform no I/O.

**Capability introduced.** Deterministic, reproducible derivation of a runtime build
context from a validated package.

---

## Module 5 — Deployment · Implemented, freeze pending CI

**What changed.** The deployment domain (`Deployment`, `DeploymentVersion`,
`VersionState`, `DesiredState`, `ResourcePolicy`, and pure transition rules); the
provider-neutral `RuntimeManager` and `DeploymentRepository` ports; persistence
(`deployments` and `deployment_versions` tables, mappers, repository, UoW wiring,
deployment operation types); the lifecycle service driving a package through
BUILDING → STARTING → READY against the runtime with failure, retry-as-new-attempt, stop,
and reconciliation; and the deployment/version HTTP surface plus `/admin/reconcile`,
contract-tested against a fake runtime.

**Why it mattered.** It froze the ready/active state semantics that Module 7 (routing)
needs, without ever driving a version to ACTIVE (activation, the route, rollback, and
retention are Module 7). Intent is persisted before every side effect, and no database
transaction spans runtime work.

**Capability introduced.** A durable, reconcilable deployment lifecycle against an
abstract runtime — the real Docker adapter is Module 6.

**Deliberate deferrals.** Execution is inline (the durable operation makes a background
worker daemon a later change with no HTTP-contract impact); the router is exercised
in-process against the fake runtime and is mounted for real with the Module 6 Docker
adapter.

---

## Reserved — Modules 6–10

Not started. Required order (roadmap): 6 Docker Runtime → 7 Routing/Versioning →
8 Monitoring → 9 Dashboard → 10 Hardening/Release. Each begins only when its entry gate
passes. Append summaries here as they freeze, in the same shape as above.
