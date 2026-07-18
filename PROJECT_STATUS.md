# ForgeML Project Status

Single source of truth for repository progress.

The phase list below mirrors the frozen roadmap in
`ForgeML_Engineering_Kit_Phase0/docs/06_IMPLEMENTATION_ROADMAP.md`. That document is
the authority; this file reports against it and may not diverge from it. Changing the
phase structure requires an ADR, not an edit here.

Last updated: 2026-07-17

---

## Current Version

ForgeML V1

---

## Current Development Stage

Backend Development

---

## Overall Progress

| Phase | Module | Status |
| --- | --- | --- |
| 0 | Foundation | ██████████ Frozen |
| 1 | Forge Package | ██████████ Frozen |
| 2 | Metadata | ██████████ Frozen |
| 3 | Backend API | ⬛ Implemented — freeze pending CI |
| 4 | Analyzer / Generator | ⬛ Implemented — freeze pending CI |
| 5 | Deployment | ⬛ Implemented — freeze pending CI |
| 6 | Docker Runtime | ⬛ Implemented — freeze pending CI |
| 7 | Routing / Versioning | ⬛ Implemented — freeze pending CI |
| 8 | Monitoring | ⬜ Not Started |
| 9 | Dashboard | ⬜ Not Started |
| 10 | Hardening / Release | ⬜ Not Started |

Overall completion: **~18%** (2 of 11 phases frozen)

The percentage counts frozen phases against the eleven the roadmap defines. It is not
weighted by effort; later phases (Docker runtime, deployment) are larger than the two
completed so far, so treat this as a position in the required order rather than a
schedule estimate.

---

## Frozen Modules

### Module 0 — Foundation

Status: **Frozen**
Freeze date: 2026-07-13
Freeze authority: ADR-014 (Module 0 evidence exception)
Baseline: `fdc1e9eb7923127b0570c9b4b08f7e9a5b429711`

Typed fail-closed configuration, explicit application composition, safe error
envelope, server-owned request IDs, bounded JSON logging, health endpoints, quality
gates.

Note: Module 0 was frozen under the one-time evidence exception recorded in ADR-014,
because no usable repository or remote was available at the time. That exception is
closed and does not extend to any later module.

---

### Module 1 — Forge Package System

Status: **Frozen**
Implementation date: 2026-07-14
Freeze date: 2026-07-14
Freeze authority: ADR-014 (satisfied normally — no exception)
Baseline: `4aa140cd7d19fd9db4b4e3d5248c27c22e33a894`
Design: `ForgeML_Engineering_Kit_Phase0/docs/19_MODULE1_PACKAGE_DESIGN.md`

Completed features:

- .forge package format (format version 1, closed manifest)
- Manifest parsing and validation
- JSON Schema Draft 2020-12 validation with depth and node bounds
- Dependency validation (ADR-011 exact PEP 508 pins)
- Content-addressed artifact storage with atomic writes (ADR-003, ADR-007)
- Safe archive extraction into caller-owned staging
- Package validation service
- Reference fixture matrix, integration tests, architecture tests

Quality:

- 224 tests, 99% branch coverage (gate: 95%)
- black, ruff, mypy strict: clean
- Dependency locks reproducible; installed-wheel smoke passes
- GitHub Actions `Backend quality` on `4aa140c`: **success**

Frozen public surface: the .forge format contract, the validation finding codes, and
the `ArtifactStore` / `ArchiveReader` ports. Changing a finding code or the meaning of
a manifest field is a package major version.

Known limitations carried forward:

- No HTTP surface (`POST /packages` is phase 3) and no package persistence
  (`PackageCatalog` is phase 2). Neither is stubbed.
- Validation is synchronous and in-process; ADR-006 wraps it in a durable operation in
  phase 3.
- Asset content is verified only for assets that declare a checksum.
- The compression-ratio floor is a fixed 1 MiB rather than operator policy.

---

### Module 2 — Metadata Layer

Status: **Frozen**
Freeze date: 2026-07-14
Freeze authority: ADR-014 (satisfied normally — no exception)
Baseline: `2c8c8721e3739529ae4862d5c712b3ba1b93a11e`
CI evidence: `Backend quality` on `2c8c8721` — **success**

PostgreSQL metadata layer, SQLAlchemy models, Alembic migration with immutability
triggers, `PackageCatalog` / `OperationStore` / `AuditLog`, `UnitOfWork`,
in-memory fakes held to the same conformance suite as the real adapters, and
ADR-016 (operation lease, crash recovery, retry).

366 tests, 99% branch coverage. Docs: 20 design · 21 implementation ·
22 review guide · 23 decisions · **24 handoff**.

---

## Current Module

**Module 7 — Platform Routing & Version Activation**

Status: **Implementation complete. NOT frozen** — ADR-014 requires passing
GitHub Actions evidence on the frozen SHA, and the changes are not yet pushed.

Scope (doc 06): stable route, activation/rollback, retention.
Entry gate: ready/active semantics frozen — satisfied by the Module 5 state machine.
Exit gate: replacement/rollback tests — **all passing**.

Delivered: `activate_version` (durable, health-gated, atomic route swap under the
deployment lock) and rollback as activation of a prior version; `mark_active` /
`mark_deactivated` transition rules; route removal on stop-of-active; `RouteManager`
and the platform prediction route `POST /v1/deployments/{name}/predict`; a
provider-neutral `PredictionGateway` port with a standard-library HTTP adapter.

Local evidence: full suite green (583 tests), 97% branch coverage, mypy strict /
ruff / black clean; activation/rollback/health-refusal and the prediction proxy
(input 422, unavailable 503, runtime-failure 502) are all covered.

Design: docs 37

RouteManager depends only on the deployment service and the `RuntimeManager` /
`PredictionGateway` ports; the frozen `RuntimeManager` contract is unchanged; no
Module 8 (monitoring) functionality was introduced.

---

## Upcoming Roadmap

Required order (doc 06): 2 Metadata → 3 Backend API → 4 Analyzer/Generator →
5 Deployment → 6 Docker Runtime → 7 Routing/Versioning → 8 Monitoring → 9 Dashboard →
10 Hardening/Release.

A phase may not begin until its entry gate passes.

---

## Engineering Authority

| Authority | State |
| --- | --- |
| ForgeML Engineering Kit (FEK) | Active |
| Architecture Decision Records (ADR-001 … ADR-015) | Active |
| Engineering Execution Protocol | Active |
| Scope Enforcement Protocol | Active |

Authority order: FEK → ADR → protocols → frozen modules → graph → repository.

---

## CI Status

GitHub Actions `Backend quality`: **PASS** on `4aa140c` (2026-07-14).

CI is development governance only; it adds no runtime or cloud service to ForgeML
(ADR-014).

---

## Last Frozen Milestone

Module 1 — Forge Package System (2026-07-14)

---

## Notes

The repository is in a stable state. All future work begins from the frozen Module 1
baseline. No V2 functionality has been introduced, and the V1 scope audit found
nothing to remove: no Kubernetes, MLflow, Redis, Kafka, queueing, autoscaling, plugin,
marketplace, cloud, distributed, microservice, enterprise, LLM, or GPU-scheduling
concept exists in the repository.
