# ForgeML Project Status

**Single source of truth for repository progress.** Every other document — the
README included — summarises this file and may not contradict it. If they
disagree, this file is right and the other is a bug.

The phase list mirrors the frozen roadmap in
`ForgeML_Engineering_Kit_Phase0/docs/06_IMPLEMENTATION_ROADMAP.md`. That document
is the authority; this one reports against it. Changing the phase structure
requires an ADR, not an edit here.

**Last updated:** 2026-07-18 (Epic 1 — Identity & Authentication)

---

## Current version

**ForgeML 0.9.1** — pre-1.0. No compatibility guarantee (ADR-021).

## Current stage

Backend development complete through Module 7. Stabilization (0.9) and freeze
verification (0.9.1) complete. **Epic 1 (Identity & Authentication) implemented.**
Phases 8–10 not started; Epic 2 (Authorization) not started.

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

### Epics (ADR-022)

Cross-cutting capabilities. Same gates and freeze rules as a phase; no position
in the phase ordering.

| Epic | Capability | Implementation | Freeze |
| --- | --- | --- | --- |
| 1 | Identity & Authentication | Complete | Pending CI evidence |
| 2 | Authorization | Not started | — |

**Implemented: 8 of 11 phases (0–7), and 1 of 2 epics.**
**Frozen: 3 of 11 phases (0–2), and 0 of 2 epics.**

Those two numbers differ on purpose and both are true. *Implemented* means the
code is written, tested, and green locally. *Frozen* means ADR-014 is satisfied:
GitHub Actions passed on a named SHA and the public surface may no longer change
without an ADR. Modules 3–7 are complete but their freeze evidence has not been
recorded, because the work is not yet pushed to the remote.

Neither number is weighted by effort. Later phases are larger than earlier ones,
so treat this as a position in a required order, not a schedule estimate.

---

## Repository metrics

Measured at `c114d50` on 2026-07-18. Reproduce with `make verify`.

| Metric | Value | Change since 0.9.1 |
| --- | --- | --- |
| Tests | 774 | +180 |
| Branch coverage | 98% (gate: 95%) | +1 |
| Test lines | 9,058 | +1,408 |
| Test suite runtime | ~31s (with Docker) | — |
| Source lines (`backend/src`) | 8,107 across 81 files | +1,044, +10 files |
| Architecture decisions | 26 (ADR-001 … ADR-026) | +5 |
| Runtime dependencies | 10, `==` pinned and hash-locked | **unchanged** |
| Known vulnerabilities | 0 (both locks) | — |
| Quality gates | black, ruff, mypy strict, pytest, coverage | — |

Epic 1 added authentication without adding a dependency: the entire subsystem
uses `hashlib`, `hmac`, and `secrets` from the standard library.

The Docker-dependent integration tests are included in the 774 only when a Docker
daemon is reachable; they skip silently otherwise. A run without Docker is not
evidence for Module 6. **They ran for this measurement.**

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

**Amended by Epic 1:** ADR-018's change to this frozen surface has landed —
`AuditEvent` and the `audit_events` table now carry a nullable `actor_id`,
added additively with no backfill. Historical rows keep `NULL`, which is
truthful: those actions had no recorded principal.

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

---

## ForgeML 0.9.1 — Platform freeze milestone

Not a module. A verification milestone: every claim the repository makes about
itself re-derived from a clean clone rather than carried forward from a document.

**Delivered:**

- **Security** — `python-multipart` 0.0.20 → 0.0.32, clearing six advisories,
  five of them reachable on the unauthenticated package upload path. Both locks
  now audit clean.
- **Concurrency proof** — the activation row lock is now tested with two live
  PostgreSQL sessions, and the test was verified to fail when the lock is
  weakened to `SKIP LOCKED`. This closes the last open High finding from the
  pre-authentication review.
- **Version correctness** — the distribution version was still the `0.1.0`
  placeholder, which `/health` and `/ready` report on the wire. Now `0.9.1`.
- **Test isolation** — the database conftest truncated four of six tables;
  `deployments` and `deployment_versions` leaked between tests.
- **Reproducibility** — fresh clone, fresh venv, locked install, `make verify`,
  wheel and sdist build, hash-locked install, and installed-wheel smoke test all
  executed from scratch. Both lock files recompile byte-identically. The example
  `.forge` package rebuilds to the same SHA-256.
- **Release metadata** — `CHANGELOG.md`, `docs/DEPENDENCY_REPORT.md`, and the
  `v0.9.1` release draft added; `docs/RELEASE.md` corrected where it contradicted
  this file on authentication's phase.

**Not delivered:** CI evidence. The working environment had no git credentials,
so nothing was pushed and no workflow was observed. Every CI step was reproduced
locally, but ADR-014 does not accept that as freeze evidence.

**Reports:** `PLATFORM_READINESS_REPORT.md`, `CHANGELOG.md`,
`docs/DEPENDENCY_REPORT.md`, `docs/releases/v0.9.1-draft.md`

---

## Epic 1 — Identity & Authentication

Cross-cutting capability, delivered ahead of Phase 8 by dependency rather than
by reordering (ADR-022): monitoring without an actor produces observations
nobody can attribute, and a dashboard built before authentication is one that
has authentication retrofitted into it.

**Delivered:**

- **Identity model** — `Principal`, `AuthenticationContext`, `ApiKey` in a new
  `domain/identity` package. One principal kind (ADR-023); every unimplemented
  identity concept has a recorded attachment point that does not require
  changing `Principal`.
- **API-key credential** — `forge_<key_id>_<secret>` with 256 bits of CSPRNG
  entropy, stored only as a SHA-256 digest, constant-time comparison, and an
  equal-cost miss path so an unknown key cannot be distinguished by latency
  (ADR-024).
- **Always-on enforcement** — every `/v1` route authenticated, no bypass in any
  form, `/healthz` and `/readyz` the only exemptions, uniform 401s (ADR-025).
- **Attribution** — operator commands carry `actor_id` into the append-only
  audit trail; crash-recovered work and reconciliation findings record `SYSTEM`
  rather than inventing an actor.
- **Out-of-band key administration** — `python -m forgeml.identity`, because an
  authenticated key-creation endpoint would let every key mint more keys
  (ADR-026).
- **Mechanical boundaries** — architecture tests forbid transport types below
  the API layer, restrict the principal contextvar to one reader, and assert no
  authorization logic has appeared yet.

**Explicitly not delivered:** authorization, scopes, rate limiting, HTTP key
management, users, sessions, JWT, OAuth2, OIDC. All are Epic 2 or later.

**Known limitation:** every valid key has full authority, and the control plane
is root-equivalent through Docker. Until Epic 2, an API key is a root credential
for the host.

**Reports:** `docs/IDENTITY_AND_AUTH.md`, `docs/SECURITY_REVIEW_EPIC_1.md`,
`docs/AUTHENTICATION_GUIDE.md`, `ENGINEERING_REPORT_IDENTITY_AUTH.md`

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
