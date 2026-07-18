# ForgeML Project Status

**Single source of truth for repository progress.** Every other document — the
README included — summarises this file and may not contradict it. If they
disagree, this file is right and the other is a bug.

The phase list mirrors the frozen roadmap in
`ForgeML_Engineering_Kit_Phase0/docs/06_IMPLEMENTATION_ROADMAP.md`. That document
is the authority; this one reports against it. Changing the phase structure
requires an ADR, not an edit here.

**Last updated:** 2026-07-18 (ForgeML 0.9 — Stabilization & Platform Readiness)

---

## Current version

**ForgeML 0.9** — pre-1.0. No compatibility guarantee (ADR-021).

## Current stage

Backend development complete through Module 7. Stabilization milestone (0.9)
complete. Modules 8–10 not started.

---

## Overall progress

| Phase | Module | Implementation | Freeze |
| --- | --- | --- | --- |
| 0 | Foundation | Complete | **Frozen** — ADR-014 exception |
| 1 | Forge Package | Complete | **Frozen** — CI evidence |
| 2 | Metadata | Complete | **Frozen** — CI evidence |
| 3 | Backend API | Complete | Pending CI evidence |
| 4 | Analyzer / Generator | Complete | Pending CI evidence |
| 5 | Deployment | Complete | Pending CI evidence |
| 6 | Docker Runtime | Complete | Pending CI evidence |
| 7 | Routing / Versioning | Complete | Pending CI evidence |
| 8 | Monitoring | Not started | — |
| 9 | Dashboard | Not started | — |
| 10 | Hardening / Release | Not started | — |

**Implemented: 8 of 11 phases (0–7).**
**Frozen: 3 of 11 phases (0–2).**

Those two numbers differ on purpose and both are true. *Implemented* means the
code is written, tested, and green locally. *Frozen* means ADR-014 is satisfied:
GitHub Actions passed on a named SHA and the public surface may no longer change
without an ADR. Modules 3–7 are complete but their freeze evidence has not been
recorded, because the work is not yet pushed to the remote.

Neither number is weighted by effort. Later phases are larger than earlier ones,
so treat this as a position in a required order, not a schedule estimate.

---

## Repository metrics

Measured at `0875662` on 2026-07-18. Reproduce with `make verify`.

| Metric | Value |
| --- | --- |
| Tests | 593 |
| Branch coverage | 97% (gate: 95%) |
| Source lines (`backend/src`) | 7,049 |
| Architecture decisions | 21 (ADR-001 … ADR-021) |
| Quality gates | black, ruff, mypy strict, pytest, coverage |
| Runtime dependencies | Pinned and hash-locked |

The Docker-dependent integration tests are included in the 593 only when a Docker
daemon is reachable; they skip silently otherwise. A run without Docker is not
evidence for Module 6.

---

## Frozen modules

### Module 0 — Foundation

- **Frozen:** 2026-07-13 · **Baseline:** `fdc1e9eb7923127b0570c9b4b08f7e9a5b429711`
- **Authority:** ADR-014 (one-time evidence exception)

Typed fail-closed configuration, explicit composition, safe error envelope,
server-owned request IDs, bounded JSON logging, health endpoints, quality gates.

The exception was granted because no usable repository or remote existed at the
time. It is closed and extends to no later module.

### Module 1 — Forge Package System

- **Frozen:** 2026-07-14 · **Baseline:** `4aa140cd7d19fd9db4b4e3d5248c27c22e33a894`
- **Authority:** ADR-014, satisfied normally · **CI:** `Backend quality` — success
- **Design:** docs 19

The `.forge` format (v1, closed manifest), manifest validation, JSON Schema
Draft 2020-12 with depth and node bounds, exact PEP 508 dependency pins
(ADR-011), content-addressed artifact storage with atomic writes (ADR-003,
ADR-007), safe archive extraction, and the reference fixture matrix.

**Frozen surface:** the `.forge` format contract, the validation finding codes,
and the `ArtifactStore` / `ArchiveReader` ports. Changing a finding code or the
meaning of a manifest field is a package major version.

**Carried limitations:** asset content is verified only where a checksum is
declared; the compression-ratio floor is a fixed 1 MiB rather than operator
policy.

### Module 2 — Metadata Layer

- **Frozen:** 2026-07-14 · **Baseline:** `2c8c8721e3739529ae4862d5c712b3ba1b93a11e`
- **Authority:** ADR-014, satisfied normally · **CI:** `Backend quality` — success
- **Design:** docs 20–24

PostgreSQL metadata layer, SQLAlchemy models, Alembic migration with
immutability triggers, `PackageCatalog` / `OperationStore` / `AuditLog`,
`UnitOfWork`, in-memory fakes held to the same conformance suite as the real
adapters, and ADR-016 (operation lease, crash recovery, retry).

**Note for the authentication module:** ADR-018 amends this frozen surface —
`AuditEvent` and the `audit_events` table gain a nullable `actor_id`. The ADR is
accepted; the migration is not yet written.

---

## Implemented, freeze pending

Modules 3–7 are complete and green locally. Each requires a passing GitHub
Actions run on its SHA before it can be frozen (ADR-014).

| Module | Delivered | Design |
| --- | --- | --- |
| 3 — Backend API | Versioned `/v1` surface, durable operations, idempotency, cursor pagination, single error envelope | docs 30–33 |
| 4 — Analyzer / Generator | Pure inference-contract analyzer; deterministic, content-addressed build-context generator | docs 34 |
| 5 — Deployment | Version state machine, lifecycle service driving the runtime, deployment persistence, frozen `RuntimeManager` port | docs 35 |
| 6 — Docker Runtime | `DockerRuntimeManager` behind a `DockerCli` seam, ADR-001 isolation, serving harness, reconciliation, disposable-Docker integration tests | docs 36 |
| 7 — Routing / Versioning | Health-gated atomic activation and rollback, route removal on stop, `RouteManager`, `PredictionGateway` port with a stdlib HTTP adapter | docs 37 |

---

## ForgeML 0.9 — Stabilization milestone

Not a module. A stabilization milestone resolving the blocking conditions from
the pre-authentication engineering review (docs 38) before authentication work
begins.

**Delivered:**

- **Repository truth** — this file reconciled with the repository; README metrics
  synchronised; the implemented-versus-frozen distinction made explicit.
- **Governance** — `GOVERNANCE.md` defines the ownership boundary between the
  FEK, ForgeOS, and `docs/`, plus the authority order and the two known
  documentation overlaps.
- **Repository hygiene** — generated graph output, Postman sync directories, and
  duplicate kit archives untracked; a fresh clone now has a clean working tree.
- **Standards** — `LICENSE` (Apache-2.0), `NOTICE`, `CONTRIBUTING.md`,
  `SECURITY.md`, `CODEOWNERS`, issue and pull-request templates,
  `docs/DEVELOPMENT.md`, `docs/RELEASE.md`, `docs/LABELS.md`.
- **Architecture preparation** — ADR-018 (principal model, actor identity,
  migration strategy), ADR-019 (authentication, authorization, and trust
  boundaries), ADR-020 (resource identity and API consistency), ADR-021
  (versioning, compatibility, release policy). Decisions only; no implementation.
- **Service split** — `DeploymentService` (615 lines, five responsibilities) split
  into `DeploymentQueryService`, `DeploymentLifecycleService`, `ActivationService`,
  and `ReconciliationService`, bundled by `DeploymentServices`. Behaviour
  unchanged: 593 tests pass before and after.
- **Documentation refresh** — stale module docstrings corrected; ADR-015/016
  ordering fixed.

**Explicitly not delivered** (out of scope by instruction): authentication,
authorization, monitoring, rate limiting, performance optimization.

**Report:** `PLATFORM_READINESS_REPORT.md`

---

## Upcoming roadmap

Required order (docs 06): **8 Monitoring → 9 Dashboard → 10 Hardening /
Release.**

A phase may not begin until its entry gate passes.

> ### Open decision: where authentication belongs
>
> The frozen roadmap (docs 06) defines no authentication phase. Security work
> sits inside Phase 10 (Hardening/Release), and multi-user auth is listed there
> as requiring an ADR rather than being a "small addition".
>
> ForgeML 0.9 prepared the repository for authentication — ADR-018 (principal
> and actor identity), ADR-019 (authentication, authorization, and trust
> boundaries), and ADR-020 (resource identity) are accepted — but **no phase
> number has been assigned to it**, and assigning one is an amendment to the
> frozen roadmap that requires its own ADR.
>
> Three options remain open: insert authentication as a new phase and shift
> Dashboard and Hardening; replace Dashboard in V1 and move it to V2; or deliver
> authentication inside Phase 10. This is recorded as unresolved rather than
> settled by edit, because `06_IMPLEMENTATION_ROADMAP.md` is the authority and
> this file only reports against it.

---

## Engineering authority

| Authority | State |
| --- | --- |
| ForgeML Engineering Kit (FEK) | Active |
| Architecture Decision Records (ADR-001 … ADR-021) | Active |
| ForgeOS process and protocols | Active |
| Scope Enforcement Protocol | Active |

Authority order: FEK → ADR → ForgeOS → frozen modules → repository. See
`GOVERNANCE.md`.

---

## CI status

**`Backend quality`: last recorded success on `4aa140c` (2026-07-14).**

Commits after that SHA — Modules 2 through 7, the README work, and this
stabilization milestone — have **not** been verified by GitHub Actions, because
they have not been pushed to the remote. They pass `make verify` locally, which
is the same command CI runs, but ADR-014 is explicit that local green is not
freeze evidence.

**This is the single largest open item in the repository.** Pushing `main` and
recording the resulting run is the prerequisite for freezing Modules 3–7.

CI is development governance only; it adds no runtime or cloud service to
ForgeML (ADR-014).

---

## Last frozen milestone

**Module 2 — Metadata Layer** (2026-07-14).

---

## Notes

No V2 functionality has been introduced. The V1 scope audit finds no Kubernetes,
MLflow, Redis, Kafka, queueing, autoscaling, plugin, marketplace, cloud,
distributed, microservice, enterprise, LLM, or GPU-scheduling concept anywhere in
the repository.
