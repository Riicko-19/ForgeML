# Architecture Decision Records

This register holds decisions required for MVP implementation. A new decision records context, decision, consequences, alternatives, owner, status, and date. Accepted ADRs are normative.

## ADR-001 — Trusted packages; defense-in-depth runtime isolation

**Status:** Accepted  
**Context:** A .forge package includes Python/dependency/model content that may execute during image build and inference. Full safe sandboxing is incompatible with the single-host MVP.

**Decision:** Only the trusted operator submits packages. Runtimes use non-root user, no Docker socket, no host network, no host artifact mounts, internal network only, dropped capabilities, read-only filesystem where compatible, scoped writable temporary storage, and CPU/memory/pid limits.

**Consequences:** This reduces blast radius but does not make untrusted code safe. Public anonymous upload and multi-tenant execution are prohibited.

## ADR-002 — Modular monolith control plane

**Status:** Accepted  
**Decision:** One FastAPI deployable hosts application/domain modules. Modules use in-process ports and DTOs; Docker model runtimes remain separate containers.

**Consequences:** Lower operational complexity and transactional consistency. Future extraction requires preserving port semantics; no domain-module network calls now.

## ADR-003 — Immutable content-addressed packages/images

**Status:** Accepted  
**Decision:** Package SHA-256 identifies bytes. Build context identity includes package checksum, generator version, and runtime/base-image version. Images are immutable and labeled with identities.

**Consequences:** Duplicate upload is idempotent and reproducibility improves. Artifact retention/garbage collection is required.

## ADR-004 — Metadata desired state; Docker reconciliation

**Status:** Accepted  
**Decision:** Durable metadata is desired state/audit record; Docker is observed state. Docker resources carry ForgeML labels. Startup/scheduled reconciliation records mismatches and repairs only through documented actions.

**Consequences:** Restart recovery does not treat Docker as a database. Operators must avoid manual managed-resource mutation except documented recovery.

## ADR-005 — One active version and platform route

**Status:** Accepted  
**Decision:** A deployment has at most one active version. Platform proxy resolves active healthy target; runtimes publish no host ports.

**Consequences:** Deterministic rollback/stable consumer URL. Weighted traffic requires future ADR.

## ADR-006 — Asynchronous durable operations

**Status:** Accepted  
**Decision:** Validation, build, start, stop, activation, and reconciliation use durable operation records with correlation/idempotency. Long-running HTTP commands return an operation resource.

**Consequences:** Clients poll and handle eventual completion. Worker/recovery mechanism must be restart-safe.

## ADR-007 — Storage/database behind ports

**Status:** Accepted  
**Decision:** Local filesystem artifact storage and one relational database are initial adapters. Application/domain depend on ports.

**Consequences:** Simple single-host deployment. Object storage/new relational adapter can be added without changing package/deployment rules.

## ADR-008 — Initial runtime compatibility matrix

**Status:** Accepted  
**Decision:** Format version 1 supports model.framework = python-callable only, Python 3.11 only, and a platform-owned Python 3.11 slim base image identified by immutable digest in configuration. The package entrypoint is the only executable integration point. Framework-specific adapters are future additive capabilities.

**Consequences:** The MVP has one deterministic runtime contract and does not need to introspect or deserialize framework artifacts during validation. Packages may include framework libraries as pinned dependencies, but platform support is for the callable interface, not framework-specific behavior.

## ADR-009 — PostgreSQL metadata and local filesystem artifacts

**Status:** Accepted  
**Decision:** PostgreSQL 16 is the MVP metadata database. The initial ArtifactStore is local filesystem storage on a dedicated persistent volume. The database worker uses PostgreSQL transaction/locking semantics.

**Consequences:** SQLite is not a supported production adapter because concurrent lifecycle operations and durable worker claims require stronger locking semantics. Backups must include PostgreSQL and artifact volume consistently.

## ADR-010 — Dynamic routing and worker execution

**Status:** Accepted  
**Decision:** A Caddy reverse proxy terminates TLS and forwards dashboard/control-plane traffic. The control plane owns dynamic prediction routing through RouteManager; it resolves the active target in metadata and proxies only to the internal Docker network. One separately supervised control-plane worker process claims durable operations from PostgreSQL using row locking; it is restart-safe and does not require an external queue.

**Consequences:** Caddy configuration does not change per deployment. One worker is the MVP limit; multiple workers may be enabled later only after claim/lease tests prove safe concurrency.

## ADR-011 — Dependency and build supply-chain policy

**Status:** Accepted  
**Decision:** Dependencies are an optional list of exact PEP 508 name==version pins. Editable requirements, local paths, direct URLs, VCS references, hashes-only requirements, and unpinned ranges are rejected. Builder egress is limited to the configured approved package index; runtime egress is disabled by default. Builds record base-image digest, resolved dependencies, and a CycloneDX SBOM. A build fails when the configured scanner reports a Critical vulnerability, unless an explicitly time-bounded operator exception is recorded in audit metadata.

**Consequences:** Reproducibility and provenance are explicit. Offline mirrors are supported by changing the approved index configuration, not package semantics.

## ADR-012 — Retention and disk-pressure policy

**Status:** Accepted  
**Decision:** Keep package artifacts while referenced by any retained version, then for 30 days. Keep active versions, the newest READY rollback candidate, and all in-progress operation artifacts regardless of normal cleanup. Retain operation/build logs for 30 days with a 10 MiB cap per version; retain raw observations for 7 days and hourly aggregates for 90 days; retain audit events for 365 days. At disk-pressure threshold, delete eligible observations first, then eligible logs, then unreferenced artifacts; never delete protected items automatically.

**Consequences:** Operators receive bounded storage behavior and predictable rollback protection. Disk thresholds are configuration with documented defaults, not per-package settings.

## ADR-013 — Control-plane Python support

**Status:** Accepted  
**Decision:** The ForgeML V1 backend/control plane supports CPython >=3.11,<3.12.
Runtime, CI, locks, and production packaging use Python 3.11. Patch updates remain
normal dependency maintenance.

**Consequences:** The control plane and generated runtime share one Python minor line;
supporting another minor requires a compatibility decision and CI evidence.

## ADR-014 — Backend CI authority

**Status:** Accepted; Module 0 evidence exception approved 2026-07-13
**Decision:** GitHub Actions is the V1 repository CI provider. The backend quality
workflow lives at .github/workflows/backend-quality.yml, is owned by Backend
Engineering, reviewed by QA, and enforces locks, format, lint, type, tests, contract,
build, and installed-package smoke gates on Python 3.11.

**Consequences:** CI is development governance only and adds no runtime/cloud service
to ForgeML. Module completion requires passing workflow evidence.

**Module 0 evidence exception:** The user explicitly authorized Module 0 freeze on
2026-07-13 after the configured workflow could not run during iteration-3 review
because no usable Git repository or remote was then available. For Module 0 only, the
recorded execution of every command and environment boundary represented by the
workflow, together with the three-iteration architecture, backend/security, QA,
documentation, and scope reviews, satisfies the completion evidence gate. The test
report must identify the CI run as not executed and must not describe it as passing.
This exception neither removes the workflow nor permits local-only evidence for later
modules or later backend changes.
The frozen implementation baseline is local commit
`fdc1e9eb7923127b0570c9b4b08f7e9a5b429711`; the later presence of a configured remote
does not retroactively constitute workflow evidence.

**Module 1 evidence (no exception required):** The backend quality workflow ran against
commit `4aa140cd7d19fd9db4b4e3d5248c27c22e33a894` — the Module 1 frozen baseline itself
— and completed with conclusion `success` on 2026-07-14. Module 1 therefore satisfies
this ADR on its ordinary terms. The Module 0 exception above remains closed and is not
extended.

**Module 2 evidence (no exception required):** The backend quality workflow — now
including a PostgreSQL 16 service, without which the ADR-009 concurrency and migration
gates cannot run at all — ran against commit
`2c8c8721e3739529ae4862d5c712b3ba1b93a11e`, the Module 2 frozen baseline, and completed
with conclusion `success` on 2026-07-14. Verified against the Actions API rather than
accepted on report.

## ADR-015 — Server-owned request identifiers

**Status:** Accepted  
**Decision:** The control plane generates a UUIDv4 request ID for every request.
Inbound X-Request-ID values are ignored and never logged or reflected. The generated
ID is returned in the X-Request-ID response header and used for request-scoped logs.

**Consequences:** Untrusted clients cannot create collisions or inject log identifiers.
Trusted upstream trace propagation requires a future approved proxy-boundary decision.

## ADR-016 — Operation lease, crash recovery, and retry

**Status:** Accepted 2026-07-14
**Context:** ADR-006 requires a "restart-safe" worker and ADR-010 repeats the
requirement, but neither specifies a mechanism. A worker that claims an operation
and is then killed leaves the row RUNNING forever: the claim query selects only
PENDING rows, so nothing ever reclaims it, and the client polls an operation that
can never reach a terminal state. Module 2's schema carried `claimed_at` and
`attempts` with no rule that consumed them, so ADR-006 was unsatisfied in fact.

**Decision:** Recovery is a **startup reconciliation sweep**, not a lease. ADR-010
supervises exactly one worker, which makes "every RUNNING row at startup belongs
to the process that died" provable rather than heuristic. `recover_orphaned()`
returns such rows to PENDING, or terminally fails them as `operation_abandoned`
once `attempts` reaches MAX_ATTEMPTS (3). There is **no automatic retry** in V1:
docs 04 already makes retry an operator action that creates a new immutable
attempt. Claims are lane-aware (`claim_next(types=...)`) so a long build cannot
block a fast validation behind it in a single queue.

**Alternatives:** A lease/visibility timeout re-queues RUNNING rows older than N,
but a lease shorter than a legitimately slow build causes double execution —
expensive for a build, dangerous for an activation. Fencing tokens are correct
under N workers and unjustifiable under one.

**Consequences:** Restart safety has a mechanism with no double-execution window.
Recovery heals only at startup, so a worker that hangs without dying still holds
its row. Lifting ADR-010's single-worker cap invalidates this decision and
requires a lease or fencing token; `recover_orphaned` is the single place that
assumption lives.

## ADR-017 — Generated runtime adapter emits valid Python literals

**Status:** Accepted 2026-07-18
**Owner:** Chief Architect (fix implemented under Module 6)

**Context:** Module 4's generator embedded the inference schemas into the generated
`forge_adapter.py` with `json.dumps`, producing JSON literals (`false`, `true`, `null`)
as Python source. These are syntactically valid identifiers, so `compile`/`ast.parse`
and every Module 4 test passed, but they are undefined *names* at runtime: importing
the module raises `NameError`. Module 5 drove the lifecycle against a fake runtime and
never imported the adapter, so the defect was latent until Module 6 built and started a
real container, where the reference package's `additionalProperties: false` crashed the
runtime before it could become healthy.

**Decision:** The generated adapter must be valid, importable Python. The generator
emits the schemas as deterministic Python literals via `pprint.pformat(schema,
sort_dicts=True)` — `True`/`False`/`None`, key-sorted for byte-stability — instead of
`json.dumps`. This is a correctness fix to a frozen module, authorized here rather than
edited silently: the Senior Implementation Engineer surfaced it as an investigation
report and it was approved before the change.

**Consequences:** The generated `forge_adapter.py` content changes, so the Module 4
artifact identity (`GeneratedBuildContext.identity`) changes value. Determinism and
input-sensitivity — the actual Module 4 exit-gate properties — are preserved, and no
test or persisted record pins a specific identity value, so nothing downstream breaks.
No package needs rebuilding: no version had yet been built through the real runtime
(Module 6 is the first). Static validity is necessary but not sufficient for generated
code; a generated runtime artifact must be exercised by an execution test, which the
Module 6 disposable-Docker integration test now provides.

**Alternatives:** Repairing the adapter from inside Module 6's serving harness (importing
the model entrypoint directly) was rejected: the entrypoint lives only in the generated
adapter, so reconstructing it would duplicate Module 4's responsibility and pull manifest
parsing into the runtime adapter's lane.

## ADR-018 — Principal model and actor identity

**Status:** Accepted 2026-07-18
**Owner:** Chief Architect (ForgeML 0.9; consumed by the authentication module)

**Context:** The audit record `AuditEvent` carries `actor_type` (`OPERATOR` | `SYSTEM`)
but no actor *identity*. Every state change is therefore attributable to a kind of
actor and to a correlation id, never to a principal. Authentication without
attribution is a lock with no logbook: "who deactivated this version" has no answer.
`AuditEvent` and the `audit_events` table belong to Module 2, which is **frozen**, so
adding identity is a change to a frozen surface and must be decided before the authentication module
rather than discovered inside it.

**Decision:** ForgeML V1 has exactly one kind of principal: an **operator**, identified
by a stable opaque `actor_id`.

1. A `Principal` is a frozen value object in `domain/audit` carrying `actor_type` and
   `actor_id: str`. It holds no credential, no secret, and no transport detail — a
   principal is *who*, never *how they proved it*.
2. `AuditEvent` gains an optional `actor_id: str | None`. Optional, because `SYSTEM`
   actions (reconciliation, startup recovery) have no principal and must not invent one.
3. The `audit_events` table gains a nullable `actor_id` column, indexed for the
   "everything this principal did" query that any real audit review begins with.
4. Every value is bounded and control-character-filtered by the same `_safe_text` rule
   the existing audit fields use. An audit row still describes *what* changed and never
   the content that changed (docs 04).
5. Machine-to-machine callers are operators. ForgeML V1 has no user model, no tenants,
   no groups, and no delegation. Multi-tenancy is a V2 concern and inventing a subject
   hierarchy now would be exactly the speculative generality the FEK forbids.

**Migration strategy:** Additive and reversible, in this order.

- Alembic migration adds `actor_id` as nullable with no backfill. Historical rows keep
  `NULL`, which is truthful: those actions genuinely had no recorded principal, and
  writing a synthetic value would forge the audit trail this ADR exists to protect.
- The immutability trigger on `audit_events` is unchanged; the column is append-only
  like every other.
- The domain field defaults to `None`, so every existing construction site keeps
  compiling and every existing test keeps passing. The authentication module then populates it at the
  call sites that have a principal.
- Rollback is dropping the column; no code path requires it to be present.

**Consequences:** The authentication module inherits a place to put identity instead of negotiating one
mid-implementation. The frozen Module 2 surface changes by exactly one nullable column
and one optional field, under an ADR, on the escalation path ADR-017 established. The
audit trail can answer "who" for everything after the migration and honestly reports
"unknown" for everything before it. Because `actor_id` is optional, a bug in that module that
forgets to pass a principal degrades to an unattributed row rather than a crash — so
That module must assert attribution on authenticated paths in tests; the type system will
not do it for them.

**Alternatives:** A required `actor_id` was rejected: it forces a synthetic principal
for `SYSTEM` actions and a fabricated backfill for history. A separate `principals`
table with a foreign key was rejected for V1: there is no principal *record* to store
beyond the identifier until there is a user model, and an empty join table is a schema
that lies about its own importance. Reusing `correlation_id` as identity was rejected
outright — it identifies a request, not an actor, and conflating them would make the
audit trail unusable for exactly the security review it exists to serve.

## ADR-019 — Authentication, authorization, and trust boundaries

**Status:** Accepted 2026-07-18
**Owner:** Chief Architect + Security Reviewer (ForgeML 0.9; consumed by the authentication module)

**Context:** Authentication and authorization have no assigned phase in the frozen
roadmap (`06_IMPLEMENTATION_ROADMAP.md` defines Phase 9 as Dashboard and places
security inside Phase 10). Assigning them a phase is a roadmap amendment requiring
its own ADR and is deliberately **not** decided here. This ADR decides only *where
the code goes* when that work is scheduled. Both concerns are
cross-cutting, and cross-cutting concerns are what erode layered architectures: a
check leaks into the domain, a credential ends up in a repository signature, and the
dependency direction is gone two modules later. Where these checks live must be decided
before any of them is written.

**Decision — trust boundaries.** ForgeML V1 recognises four, and they are ordered by
decreasing trust:

| # | Boundary | Trust | Crossing rule |
| --- | --- | --- | --- |
| T1 | Operator → control-plane HTTP API | Untrusted until authenticated | Authenticate, then authorize, then admit |
| T2 | Control plane → PostgreSQL / filesystem | Trusted | Same host, operator-owned; no additional check |
| T3 | Control plane → Docker daemon | **Trusted and root-equivalent** | Never influenced by request content |
| T4 | Control plane → runtime container | Semi-trusted | Platform-internal endpoint only, never a client-supplied URL |

T3 is the boundary that sets the stakes: the control plane can drive the Docker daemon,
and the daemon is root. The authentication boundary is therefore not protecting model
metadata, it is protecting host root. Its threat model must say so in those words.

**Decision — security domains.** Three, with no path between them except the ones named:

- **Public** — nothing. ForgeML exposes no anonymous surface (ADR-001 forbids public
  upload).
- **Operator** — the authenticated control-plane API. Every `/v1` route lives here.
- **Runtime** — the egress-free internal Docker network. Reachable only from the control
  plane, never from a client, and it cannot reach the operator domain.

**Decision — the authentication boundary is the API layer.** Authentication is a
transport concern: it reads a header, verifies a credential, and produces a `Principal`.
It belongs in `forgeml.api` — as middleware for the credential and a FastAPI dependency
for the resulting principal — and nowhere else. No credential, header, token, or request
object may cross into `forgeml.application`. The application layer receives a
`Principal`, which is a domain value object, exactly as it already receives a
`correlation_id`.

**Decision — the authorization boundary is the application layer.** Whether *this*
principal may perform *this* command is a use-case decision, not a routing decision. It
belongs at the entry of each application service method, where the target resource is
already known. This is precisely why ForgeML 0.9 split `DeploymentService` into four
services: the authorization checks land in four small files, each with one reason to
change, rather than threading through one 615-line class.

The domain layer holds **no** authorization logic. Domain rules are policy over values
and must stay decidable without knowing who asked.

**Decision — health endpoints stay unauthenticated.** `/healthz` and `/readyz` are
consumed by process supervisors and load balancers that have no credential to present.
They already expose no state beyond liveness and database reachability. `/v1/openapi.json`
moves inside the operator domain with the rest of `/v1`.

**Decision — enforcement is mechanical.** The architecture test suite gains rules
mirroring the ones that already hold the other boundaries: no `forgeml.application` or
`forgeml.domain` module may import a transport credential type, and no `forgeml.domain`
module may reference authorization. A boundary defended only by review is a boundary
already lost.

**Consequences:** That module has one place for authentication, one place for
authorization, and a test suite that fails the build if either moves. `401` and `403`
become two members of `ErrorCategory` and two entries in `_CATEGORY_STATUS` — the error
envelope needs no other change. Every command signature gains a `Principal`, which is a
wide but mechanical diff, and one the four-way service split has already made
tractable. Rate limiting is explicitly **not** decided here; it belongs with the identity
it keys on and is deferred to that module's own design.

**Alternatives:** Authorization in the API layer was rejected: the router would have to
re-read the target resource to decide, duplicating the query the service performs anyway
and creating a check that can silently disagree with the command it guards.
Authorization in the domain was rejected: it makes pure policy depend on a caller and
would break the determinism the domain is built on. A single `@requires_permission`
decorator over the routers was rejected as the same mistake in more convenient
packaging.

## ADR-020 — Deployment resource identity and API consistency

**Status:** Accepted 2026-07-18
**Owner:** Chief Architect (ForgeML 0.9)

**Context:** Deployment routes key on `{deployment_id}` (a UUID) everywhere except the
prediction route, which keys on `{name}`. Authorization scopes bind to resource
identifiers, so a resource with two identifiers grows two scope models — and an
authorization bypass shaped like a naming inconsistency. This must be settled before
the authentication module writes its first scope.

**Decision:** A deployment has **two identifiers, with defined roles**, and this is
deliberate rather than accidental:

1. `id` (UUID) is the **control-plane identifier**. Every administrative route — create,
   read, list, deploy, activate, stop — uses it. It is stable, opaque, and unguessable.
2. `name` is the **data-plane identifier**. Exactly one route uses it:
   `POST /v1/deployments/{name}/predict`. A caller running predictions should not need
   to know a UUID, and the name is already immutable and unique by database constraint,
   so it is a legitimate natural key.

The rule that makes this safe and non-arbitrary: **the control plane is addressed by
id; the serving path is addressed by name.** A route that changes deployment state
takes a UUID. A route that runs a model takes a name.

Authorization scopes bind to the **UUID**. The prediction route resolves
name → deployment inside the query service and authorizes against the resolved id, so
there is exactly one scope model and the name is never itself a permission subject.

**Decision — deferred API items.** Recorded here so they are decisions rather than
omissions, and none of them is implemented in ForgeML 0.9:

- `GET /v1/deployments/{id}/versions` — genuinely missing. `list_versions` exists on the
  repository port with no HTTP route, so a client cannot enumerate versions to choose a
  rollback target. Deferred to the authentication module, which must authorize it on arrival; adding an
  unauthenticated enumeration endpoint now would be a route to retrofit rather than
  build.
- `/v1/admin/reconcile` — `admin` is a role, not a resource. It is renamed to
  `POST /v1/reconciliations` (returning an operation, like every other durable command)
  when The authentication module introduces roles, because the move and the role that justifies it should
  land in one change.
- `DELETE` on deployments and packages — deferred to Module 10 with retention (ADR-012).
  Deletion without a retention policy is a way to lose artifacts that other versions
  still reference.
- Typed prediction responses in OpenAPI — the route returns `Any`. Each active version
  has a known output schema; publishing it per deployment is an enhancement for the authentication module or later.

**Consequences:** The identity question is closed and written down, so the authentication module writes
one scope model. The naming split is now a documented rule a reviewer can enforce rather
than an inconsistency a reviewer must rediscover. Four known API gaps have owners and
target modules instead of living in a review document.

**Alternatives:** Making every route name-based was rejected: names are immutable today,
but a rename feature would silently break every stored reference and every audit row.
Making the prediction route UUID-based was rejected: it degrades the one path a
non-operator client actually calls, for internal consistency the caller cannot see.

## ADR-021 — Versioning, compatibility, and release policy

**Status:** Accepted 2026-07-18
**Owner:** Release Manager (ForgeML 0.9)

**Context:** ForgeML approaches a public v1.0 with no stated versioning scheme,
compatibility promise, or deprecation path. Contributors cannot tell what may change,
and operators cannot tell what will break them.

**Decision — Semantic Versioning 2.0.0** for the distribution, with ForgeML's three
public contracts versioned explicitly:

| Contract | Versioned by | Breaking change means |
| --- | --- | --- |
| HTTP API | URL prefix (`/v1`) | A new prefix (`/v2`); `/v1` keeps its promise |
| `.forge` package format | `format_version` in the manifest | A new format version; the old one stays readable |
| Python distribution | SemVer | Major bump |

**Decision — pre-1.0 status.** ForgeML is `0.x` until Modules 8–10 complete. Under
SemVer, `0.x` carries no compatibility guarantee, and ForgeML states plainly that it
has none yet. This honesty is the point: the alternative is an implied promise the
project cannot keep.

**Decision — compatibility promise from 1.0.** Within a major version: no endpoint is
removed, no field is removed from a response, no field becomes required in a request, no
error `code` changes meaning, and no `.forge` manifest field changes meaning. Adding an
optional request field, a response field, a new endpoint, or a new error code is a minor
release. Clients must tolerate unknown response fields.

**Decision — deprecation.** A deprecated surface is announced in the release notes,
marked in the OpenAPI description, and kept working for **at least one minor release**
before removal in the next major. Nothing is removed in a patch.

**Decision — database migrations.** Forward-only via Alembic. Every migration is
additive or reversible, and one is never squashed after release. A release note names
every migration it carries and whether it holds a lock.

**Decision — branch and support policy.** `main` is always releasable and is the only
long-lived branch; work merges via pull request with the `make verify` checkpoint green.
Releases are annotated tags (`v0.9.0`). Only the latest minor of the latest major is
supported before 1.0; the security policy in `SECURITY.md` governs fixes.

**Decision — freeze policy is unchanged.** ADR-014 governs module freezes and this ADR
does not weaken it: a module is frozen only on passing CI evidence at a named SHA.
Release versioning and module freezing are separate mechanisms answering separate
questions — what an operator can rely on, and what an engineer may still edit.

**Consequences:** Contributors and operators can both predict what will change.
Release automation is explicitly *not* implemented here; this ADR is the policy the
automation will later encode.

**Alternatives:** CalVer was rejected: it communicates recency, and ForgeML's users need
to know about breakage. Promising compatibility before 1.0 was rejected as a promise the
project cannot yet keep.
