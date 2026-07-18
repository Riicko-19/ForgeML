# 38 — Pre-Authentication Engineering Review

Architecture health assessment of ForgeML after Modules 0–7, conducted as a v1.0
readiness gate before Module 9 (Authentication & Authorization).

Reviewer role: Principal Software Architect / Staff Platform Engineer
Scope: review only. No code, architecture, or documentation was changed.
Baseline: `0875662` (main), 6,836 source lines, 332 test functions.

---

## Executive Summary

The architecture has held. Seven implementation modules have been layered onto the
Module 0 foundation without eroding a single boundary: the domain is pure, the ORM
is confined to one package, Docker exists only behind the `RuntimeManager` port,
and every one of those rules is enforced by AST tests rather than convention. The
frozen `RuntimeManager` contract survived a fake-to-Docker swap unchanged, which is
the strongest available evidence that the port design was right.

The weaknesses are not architectural. They are **repository hygiene**,
**documentation drift**, and **one genuine gap in the audit model** that
authentication will collide with immediately. Specifically: `AuditEvent` records
`actor_type` but no actor identity, so the audit trail cannot attribute an action
to a principal — and that record lives in frozen Module 2. That is a decision to
make deliberately, before Module 9, not during it.

The recommendation is **YES WITH CONDITIONS**.

---

## Scores

| Dimension | Score | Basis |
| --- | --- | --- |
| Architecture | 9 / 10 | Boundaries intact and mechanically enforced; one service growing too large |
| Repository organization | 6 / 10 | Three Postman trees, two doc governance roots, 19 MB of generated output committed |
| Maintainability | 8 / 10 | Excellent docstrings and rationale; largest service now mixes five responsibilities |
| Security (pre-auth, as designed) | 7 / 10 | Runtime isolation is genuinely strong; build-time isolation and edge bounds are not |
| Developer experience | 8 / 10 | One-command checkpoint, honest Makefile; no LICENSE, no CONTRIBUTING |

---

## Major Strengths

1. **Enforced dependency direction.** `tests/architecture/test_dependency_direction.py`
   parses every module's AST and fails the build on a forbidden import. The domain
   cannot reach FastAPI, SQLAlchemy, Docker, `zipfile`, or even `pathlib`; SQLAlchemy
   cannot escape `infrastructure/database`; no package-validation path may import
   `importlib`, `pickle`, `subprocess`, or call `eval`/`exec`. These are rules that
   hold under pressure because they are not written in prose.
2. **The port design proved itself.** Module 5 froze `RuntimeManager` and drove it
   against a fake. Module 6 implemented it against Docker. Nothing above the port
   changed. Module 7 then added routing on top of the same frozen contract plus a
   new consumer-owned `PredictionGateway`, and `RouteManager` still never imports
   Docker.
3. **One conformance suite, two implementations.** Every port's real adapter and
   in-memory fake are held to the same 733-line contract test. The fakes are not
   parallel truth; they are the same truth.
4. **Transaction discipline.** No database transaction spans a build, start, or
   stop. Intent is persisted before the side effect. Activation swaps the route
   under a `SELECT … FOR UPDATE` on the deployment row, atomically or not at all.
   Stop clears the route *before* stopping the container.
5. **Archive handling is genuinely hardened.** Path traversal blocked via
   `is_relative_to`, symlinks and encrypted members refused, uncompressed bytes
   capped *during* the write, YAML aliases banned by a custom loader, manifest size
   checked against delivered bytes rather than the header's claim.
6. **Runtime isolation follows ADR-001 completely.** Non-root, read-only rootfs,
   `cap-drop ALL`, `no-new-privileges`, pids/memory/CPU limits, internal network,
   no Docker socket mounted.
7. **Honest engineering notes.** Deliberate shortcuts carry `ponytail:` comments
   naming the ceiling and the upgrade path. Deferred work is stated, not hidden.

---

## Major Weaknesses

1. `PROJECT_STATUS.md` — the declared single source of truth — contradicts itself,
   the README, and the repository.
2. `AuditEvent` has no actor identity. Authentication needs one; the record is frozen.
3. `DeploymentService` (615 lines) now owns five distinct responsibilities and is
   the file Module 9 will have to touch five times.
4. Repository hygiene: 19 MB of regenerated graph output, two redundant zips, and
   three Postman locations are tracked in git.
5. Prediction path costs one `docker inspect` subprocess per request.
6. No LICENSE. For a project presenting itself as open infrastructure, this is the
   one omission that blocks everything downstream of it.

---

## Architecture Findings

### A-1 — Clean Architecture holds. No violations found. (Informational)

Verified by reading every layer and by the AST suite:

| Rule | Status |
| --- | --- |
| Domain imports no provider, transport, or filesystem | Holds |
| Application imports no `fastapi`, `forgeml.api`, `forgeml.infrastructure` | Holds |
| API imports no `forgeml.infrastructure`, `sqlalchemy`, `docker` | Holds |
| SQLAlchemy confined to `infrastructure/database` | Holds |
| No package-validation path can import or deserialize package content | Holds |

The one relaxation is documented in the test itself: Module 0's original rule
forbade the API from importing `forgeml.application`, written when no application
layer existed. Enforcing it today would contradict the dependency direction the
FEK specifies. The relaxation is correct and the reasoning is recorded in the test
docstring — the right place for it.

### A-2 — The domain depends on Pydantic (Medium)

`domain/package/models.py` and `domain/package/rules.py` import Pydantic. The
architecture test's `DOMAIN_FORBIDDEN` list does not include it, so this is
permitted by policy rather than overlooked — but "domain logic remains framework
independent" is not literally true today. Pydantic is a validation library rather
than a transport framework, and the coupling is confined to the package aggregate,
so the practical risk is low. The finding is that the *claim* and the *rule* should
be aligned: either add `pydantic` to the forbidden list and move manifest parsing
outward, or amend the stated principle to "no transport, persistence, or provider
framework" and record why validation is exempt.

### A-3 — `DeploymentService` is becoming a god service (High)

615 lines, and it now owns:

- deployment CRUD (`create_deployment`, `get_deployment`, `list_deployments`)
- version build/start lifecycle (`deploy_version` + `_execute_deploy`)
- activation and rollback with the route swap (`activate_version` + `_execute_activate`)
- stop with route removal (`stop_version` + `_execute_stop`)
- reconciliation (`reconcile` + `_execute_reconcile`)
- a routing read model (`resolve_active_target`)

Each is coherent in isolation and the code is well-factored *within* the class —
this is not a mess, it is a class that has quietly accumulated five reasons to
change. The seams are already visible in the `_execute_*` method names.

This matters specifically because Module 9 will add an authorization check to
every command path in this file. Splitting after that is a much larger diff than
splitting before.

### A-4 — `resolve_active_target` inverts a responsibility (Low)

`DeploymentService.resolve_active_target` returns `ActiveTarget`, a type owned by
`domain/routing/ports.py`. The deployment service now knows about routing's read
model. The alternative — letting `RouteManager` reach the repositories directly —
would be worse, so the current shape is the better of the two. But the method is a
routing query living on a deployment service, and it should be named and located
as such when A-3 is addressed.

### A-5 — Cross-aggregate domain import (Informational)

`domain/deployment/ports.py` imports `GeneratedBuildContext` from
`domain/package/generator.py`. Deployment depends on package. This is a real
coupling but a correct one — a deployment version *is* a built package — and it
stays inside the domain layer. No action.

---

## Hexagonal Findings

### H-1 — Ports with no production caller (Medium)

| Port method | Production callers | Status |
| --- | --- | --- |
| `ArtifactStore.delete()` | 0 | Reserved for retention (ADR-012, unimplemented) |
| `DeploymentRepository.list_versions()` | 0 | Tests only — and the API gap in P-3 |
| `OperationStore.claim_next()` | 0 | Reserved for the deferred worker (ADR-006/010) |
| `RuntimeStatus.restart_count` | 0 | Parsed from Docker, read by no policy |

`claim_next` is documented as deliberately reserved and the docstring explains why
an inline executor must not use it — that one is fine. The other three are
unused flexibility carried in frozen or near-frozen contracts. They are cheap to
keep and expensive to add later, so the recommendation is not to delete them but
to **state in the port docstring which module will consume each**, so a future
reader can tell "reserved" from "forgotten." `restart_count` in particular reads
as a monitoring signal with no monitoring module yet.

### H-2 — Private protocol duplication in the Docker adapter (Low)

`infrastructure/runtime/docker.py` declares private `_ArtifactSource` and
`_ArchiveExtractor` protocols that structurally duplicate the existing
`ArtifactStore` and `ArchiveReader` domain ports. The file already imports from
`domain.package.generator`, so the isolation argument for redeclaring them does not
hold. Two lines of import would replace two protocol declarations.

### H-3 — Missing port: none identified

Every external dependency the system has — database, filesystem, archive format,
container runtime, prediction transport — sits behind a port with a fake. No
provider is reachable without crossing one.

---

## Security Findings

Reviewed without implementing authentication, as instructed.

### S-1 — Every endpoint is unauthenticated (Critical — this is Module 9)

Including `POST /v1/admin/reconcile` and `POST /v1/packages`. The only mitigations
are the default bind to `127.0.0.1` (config rejects wildcard binds — good) and the
docs-11 posture of keeping the control plane on an administrative network. Stated
here for completeness; it is the module under consideration.

### S-2 — The control plane is root-equivalent on its host (Critical)

It drives the Docker daemon. Anyone who reaches the process reaches the daemon,
and the daemon is root. This raises the stakes on S-1 considerably: the auth
boundary is not protecting model metadata, it is protecting host root. Module 9's
threat model should say so explicitly, and Module 10 should consider a dedicated
service account plus a socket proxy restricting the verb set.

### S-3 — Build-time isolation is weaker than run-time isolation (High)

ADR-001's hardening — non-root, read-only, cap-drop, no-new-privileges, limits —
applies to `docker run`. It does not apply to `docker build`. The build installs
the package's own declared dependencies, and Python packaging executes arbitrary
code at install time (`setup.py`, PEP 517 backends). That code runs in the
daemon's build container under the daemon's privileges, outside every control the
ADR specifies.

ADR-011's exact PEP 508 pins reduce *which* code runs but not *whether* arbitrary
code runs. Note also that the control plane locks its own dependencies with
hashes (`--require-hashes`), while user packages pin versions only — the stronger
supply-chain control is applied to the platform and not to the untrusted input.

This deserves its own ADR before v1.0.

### S-4 — No request body bound on the prediction path (High)

`POST /v1/deployments/{name}/predict` takes `Annotated[Any, Body()]`. Package
upload is bounded by `max_archive_bytes`; predictions are bounded by nothing at
the control-plane edge. The in-container harness caps at 10 MiB, but the control
plane buffers and forwards the full body before the container ever sees it. An
unauthenticated caller can drive control-plane memory with a single large POST.

### S-5 — Egress isolation is best-effort and unverified (Medium)

`_ensure_network()` runs `docker network create --internal` inside
`contextlib.suppress(RuntimeUnavailable, TimeoutError)` and ignores the return
code. In steady state the network already exists and creation fails harmlessly —
which is the intent. But if a network named `forgeml-runtime` exists and is *not*
internal, containers join it and ADR-011's egress-free guarantee is silently void.
The adapter never inspects the existing network to confirm it is internal.

### S-6 — `extract()` does not enforce `max_entries` (Medium)

`ZipArchiveReader.extract()` enforces `max_uncompressed_bytes` during the write
but never checks `limits.max_entries`, though the limit is in scope. An archive of
one million empty files passes the byte cap and creates one million inodes in the
build context. `max_entries` is enforced on the validation path, so a hostile
archive must first pass validation to reach here — the exposure is real but
gated.

### S-7 — Validator messages are reflected to the client (Low)

`_input_invalid` embeds the jsonschema validator message (truncated to 512 chars)
in the error envelope. Those messages can quote fragments of the offending input.
Deliberate and useful for debugging; worth a conscious decision once requests are
attributable to a principal.

### S-8 — No rate limiting anywhere (Medium)

Combined with S-4 and the synchronous proxy in P-2, an unauthenticated caller can
exhaust the request thread pool. Module 9 is the natural home for the identity
that a rate limit would key on.

### S-9 — Secret handling is correct (Informational)

`database_url` is `SecretStr`; `ConfigurationIssue` carries a field name and an
error kind but never an input value; `_safe_issues` calls
`errors(include_input=False)`. Error handlers collapse every unexpected exception
to a generic `internal_error`, so a SQLAlchemy exception carrying a DSN cannot
reach a client. Audit metadata is bounded, control-character-filtered, and
documented as describing what changed and never the content. This is done well.

### S-10 — Image tag truncates the content address (Low)

`image_ref` uses `identity[:12]` — 48 bits. Collision is implausible at any
realistic scale, but a truncated content address is being used as an identity.
Note it; no action needed for v1.0.

---

## Performance Findings

### P-1 — One `docker inspect` subprocess per prediction (High)

`RouteManager.predict` calls `self._runtime.inspect(...)` on every request, which
forks a `docker` process. This dominates prediction latency (tens of milliseconds
of pure process spawn) and caps throughput at the process-spawn rate. The code
already flags it:

> `# ponytail: this inspects the runtime per request; a cached readiness gate (Module 8 monitoring) would remove the per-prediction cost.`

The correctness argument for checking is sound — a prediction should not reach an
unhealthy runtime. The fix is a cached readiness view invalidated by lifecycle
events, which is exactly Module 8's remit. This is the single highest-value
performance change available.

### P-2 — Blocking work occupies the request thread pool (High)

Routes are sync `def`, so FastAPI runs them in the default 40-thread pool.
`build` may block for up to 600 s and `start` for 120 s. Concurrent deploys will
saturate the pool and stall predictions on an unrelated deployment. The deferred
worker daemon (ADR-006/010) is the designed answer and is already anticipated in
the service docstring; until it exists, the pool is the de facto concurrency
limit for the whole control plane.

### P-3 — `reconcile()` is N+1 (Medium)

One `docker ps` followed by one `docker inspect` per container. `docker inspect`
accepts multiple ids in a single invocation; the loop could be one call.

### P-4 — `_await_ready` polls by subprocess (Medium)

Up to `start_timeout_seconds / poll_interval_seconds` = 240 `docker inspect`
spawns per container start, each blocking a pool thread from P-2.

### P-5 — Artifacts accumulate without bound (Medium)

Content-addressed storage with no garbage collection. `ArtifactStore.delete()`
exists with zero callers and ADR-012 (retention and disk pressure) is unimplemented.
Disk exhaustion on a single-server deployment is a realistic v1.0 failure mode,
and it is silent until it is total.

### P-6 — Database locking is correctly scoped (Informational)

`lock_deployment` takes a row lock on one deployment. Activation and
stop-of-active serialize per deployment and not globally. This is the right
granularity.

---

## Repository Organization Findings

### R-1 — Three Postman locations (Medium)

| Path | Contents |
| --- | --- |
| `postman/` | Postman-synced YAML tree, 220 KB, includes a stale "ForgeML API" collection |
| `docs/postman/` | Collection JSON + environment JSON + README |
| `.postman/resources.yaml` | Sync metadata |

Two environments differ only in name (`Local ForgeML` vs `ForgeML — Local`).
Nothing states which is authoritative. A contributor cannot tell which to edit.

### R-2 — 19 MB of generated output is committed (High)

`graphify-out/` holds 288 tracked files including an AST cache that is rewritten
on every `graphify update`. `git status` on a clean checkout already shows eleven
modified files and dozens of untracked cache entries. This trains contributors to
ignore a dirty working tree, which is precisely how a real change gets committed
by accident. It belongs in `.gitignore`.

### R-3 — Redundant zip archives (Low)

`ForgeML_Engineering_Kit_Phase0.zip` and
`ForgeML_Engineering_Kit_Phase0_implementation_ready.zip` are tracked alongside
the extracted directory they contain. Three copies of the same documents, two of
them opaque to diff, review, and search.

### R-4 — Two governance roots with overlapping content (Medium)

`.forgeos/` (constitution, roles, workflows, templates) and
`ForgeML_Engineering_Kit_Phase0/` (charter, standards, ADRs, module designs)
both define engineering process. `.forgeos/constitution/05_engineering_standards.md`
and `FEK/docs/07_ENGINEERING_STANDARDS.md` are two files with one name.
`.forgeos/roles/` (6 roles) and `FEK/.skills/` (10 skills) are two role
taxonomies. `PROJECT_STATUS.md` states the authority order — FEK → ADR →
protocols → frozen modules → graph → repository — which resolves conflicts, but
only for a reader who has found that line.

### R-5 — ADRs have two homes, one empty (Low)

`.forgeos/decisions/` contains only `adr_template.md` and a README. The seventeen
actual ADRs live inside `FEK/docs/10_ARCHITECTURE_DECISIONS.md` as sections of one
file. A directory that exists to hold decisions and holds none will attract the
eighteenth one.

### R-6 — FEK doc numbering has gaps and no module index (Low)

Numbering jumps 24 → 30, and the sequence interleaves designs, implementations,
review guides, decisions, and handoffs across seven modules. Finding "the Module 5
design" requires scanning filenames.

### R-7 — Missing repository files (High)

No `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, or `CODEOWNERS`. The README is
honest that the license is not finalized, which is the right disclosure — but
without a license, no one can legally contribute, and the README presents the
project as though they could. This is the highest-priority item in this section
despite being the least technical.

---

## Documentation Findings

### D-1 — `PROJECT_STATUS.md` contradicts itself and the repository (Critical)

It declares itself the single source of truth for progress. It currently states:

| Claim | Reality |
| --- | --- |
| "Overall completion ~18% (2 of 11 phases frozen)" | The same table lists Modules 0, 1, and 2 as Frozen — three, not two |
| "Last Frozen Milestone: Module 1 (2026-07-14)" | Module 2 is listed as Frozen on the same date |
| "CI Status: PASS on `4aa140c` (2026-07-14)" | HEAD is `0875662`, fourteen commits later |
| "ADR-001 … ADR-015" | ADR-016 and ADR-017 both exist and are referenced in source |
| "All future work begins from the frozen Module 1 baseline" | Modules 3–7 are implemented |
| "Last updated: 2026-07-17" | Module 7 and two README commits landed after |

Meanwhile `README.md` advertises "8 / 11 modules built." Neither document is
wrong about the code; they are wrong about each other. A governance model whose
authoritative status file disagrees with itself cannot be used to gate a module,
and Module 9's entry gate is supposed to be checked against exactly this file.

### D-2 — Stale module docstrings (Medium)

`api/v1/deployments.py` opens with:

> "Wiring this router into the live application belongs to Module 6: it needs a
> real RuntimeManager… Until then the router is exercised against the fake runtime."

It has been wired since Module 6 — `core/composition.py:102`. A reader taking the
docstring at face value will look for a wiring gap that does not exist.
`domain/deployment/ports.py` similarly says "Frozen here for the routing module
(Module 7); Module 5 does not activate" in the present tense.

### D-3 — ADR ordering slip (Low)

In `10_ARCHITECTURE_DECISIONS.md`, ADR-016 appears before ADR-015.

### D-4 — Documentation quality is otherwise excellent (Informational)

Module docstrings explain *why*, not *what*; they cite the FEK doc or ADR that
motivated the decision; deliberate shortcuts are marked with their ceiling and
upgrade path. `provider.py`'s "a readiness probe that does not check its own
database is a lie" is the kind of comment that survives a refactor. The
`Makefile` explicitly refuses to hide steps a developer would otherwise run by
hand, and the CI workflow delegates to `make verify` specifically so the two
cannot drift. This is above the standard of most production infrastructure
projects.

---

## Testing Findings

Strategy is strong and layered: unit, contract (port conformance over real and
fake implementations), integration (real PostgreSQL, disposable Docker),
architecture (AST-enforced), and an installed-wheel smoke test. 332 test
functions, 97% branch coverage against a 95% gate.

### T-1 — Docker integration tests skip silently (High)

`tests/integration/runtime/test_docker_runtime_integration.py` carries
`pytestmark = pytest.mark.skipif(not _docker_available(), …)`. If the Docker
daemon is unreachable on a runner, the entire Module 6 adapter suite vanishes from
the run and the build still reports green. The adapter is the module's whole
deliverable. The suite should fail loudly rather than skip when an environment
variable marks Docker as expected — CI sets it, laptops do not.

### T-2 — No concurrency test for activation (High)

`test_concurrency.py` and `test_insert_races.py` cover the metadata layer's
locking. The activation route swap under `lock_deployment` is the newest
concurrency-sensitive invariant in the system — two simultaneous activations of
different versions on one deployment must leave exactly one ACTIVE — and there is
no test that races it. The lock looks correct by reading; that is not the same as
evidence.

### T-3 — `max_entries` is untested on the extract path (Medium)

Follows from S-6: the limit is not enforced there, so there is no test to fail.

### T-4 — No latency or throughput budget (Medium)

Nothing in the suite would catch P-1 becoming ten times worse. For a serving
platform, a coarse latency assertion on the prediction path is worth more than
another unit test.

### T-5 — Fakes are substantial code (Informational)

`tests/fakes.py` (460 lines) plus `fake_runtime.py` (87). They carry their own
defect risk, which is precisely why holding them to the same conformance suite as
the real adapters is the right design. Noted as a strength, not a gap.

---

## Public API Findings

Consistent across the surface: `/v1` prefix, plural resources, `202 Accepted`
with a `Location` header for durable commands, `Idempotency-Key` required on
every mutating command, cursor pagination, and one error envelope carrying
`request_id`. Interactive docs are disabled while the schema stays published,
with the reasoning recorded in `composition.py`. This is well-built.

### P-1 — Two identity schemes for one resource (High)

Every deployment route keys on `{deployment_id}` (UUID) except the prediction
route, which keys on `{name}`:

```
GET  /v1/deployments/{deployment_id}
POST /v1/deployments/{deployment_id}/versions/{version_id}/activate
POST /v1/deployments/{name}/predict          ← different key
```

The name-based prediction path is the better public ergonomics and should
probably stay. But this must be resolved **before** Module 9, because
authorization scopes are written against resource identifiers, and a system with
two identifiers for one resource will grow two scope models.

### P-2 — No version listing endpoint (High)

`DeploymentRepository.list_versions()` exists and is unused (H-1). There is no
`GET /v1/deployments/{id}/versions`. A client therefore cannot enumerate versions
to choose a rollback target — yet rollback-by-activating-a-prior-version is a
headline capability in the README. The functionality exists at every layer except
the one the user touches.

### P-3 — `/v1/admin/reconcile` is not a resource (Medium)

`admin` is a role, not a noun, and it sits on the same unauthenticated surface as
tenant routes. When roles become real, this path will need to move anyway.
`POST /v1/reconciliations` returning an operation would match the rest of the API
and survive the auth model.

### P-4 — Nothing can be deleted (Medium)

No `DELETE` on deployments or packages. Combined with P-5 (no retention),
the system only ever grows.

### P-5 — Prediction responses are untyped in OpenAPI (Low)

The route returns `Any`, so schema consumers get nothing. Each deployment's
active version has a known output schema; publishing it per deployment would make
the generated client meaningfully typed.

---

## Technical Debt Register

| # | Item | Severity | Why |
| --- | --- | --- | --- |
| 1 | `PROJECT_STATUS.md` self-contradiction (D-1) | **Critical** | The file that gates module entry cannot gate anything while it disagrees with itself |
| 2 | `AuditEvent` has no actor identity | **Critical** | Auth cannot attribute actions; the record is in frozen Module 2 |
| 3 | No LICENSE (R-7) | **Critical** | Blocks contribution and any public v1.0 |
| 4 | Unauthenticated root-equivalent surface (S-1, S-2) | **Critical** | Module 9 exists for this |
| 5 | Build-time isolation gap (S-3) | High | Arbitrary code runs outside every ADR-001 control |
| 6 | Unbounded prediction body (S-4) | High | Trivially exploitable pre-auth |
| 7 | `DeploymentService` god service (A-3) | High | Every auth check lands in this one file |
| 8 | Per-prediction `docker inspect` (P-1) | High | Dominates serving latency |
| 9 | Blocking work in the request pool (P-2) | High | A build stalls unrelated predictions |
| 10 | Docker tests skip silently (T-1) | High | Module 6 can lose CI evidence invisibly |
| 11 | No activation concurrency test (T-2) | High | Newest invariant, least evidence |
| 12 | Two identity schemes (API P-1) | High | Auth scopes will inherit the ambiguity |
| 13 | No version listing endpoint (API P-2) | High | Rollback is unreachable from a client |
| 14 | 19 MB generated output committed (R-2) | High | Normalizes a dirty working tree |
| 15 | Egress isolation unverified (S-5) | Medium | Silent loss of a stated guarantee |
| 16 | `max_entries` unenforced on extract (S-6) | Medium | Inode exhaustion behind the validation gate |
| 17 | No retention / GC (P-5, ADR-012) | Medium | Silent disk exhaustion |
| 18 | No rate limiting (S-8) | Medium | Compounds S-4 and P-2 |
| 19 | Three Postman trees (R-1) | Medium | Contributors cannot tell which is real |
| 20 | Two governance roots (R-4) | Medium | Duplicate standards and role taxonomies |
| 21 | Stale module docstrings (D-2) | Medium | Actively misleading about wiring |
| 22 | `reconcile()` N+1 (P-3) | Medium | One call would do |
| 23 | Domain depends on Pydantic (A-2) | Medium | Stated principle and enforced rule disagree |
| 24 | Unused port methods undocumented (H-1) | Medium | "Reserved" is indistinguishable from "forgotten" |
| 25 | Redundant zips (R-3) | Low | Three copies, two unreviewable |
| 26 | Private protocol duplication (H-2) | Low | Two declarations, two imports would do |
| 27 | ADR ordering, doc numbering (D-3, R-6) | Low | Navigation friction |
| 28 | Truncated image identity (S-10) | Low | Note it |

---

## Recommendations

### Before Module 9 begins

1. **Correct `PROJECT_STATUS.md`.** Reconcile the frozen count, the last frozen
   milestone, the CI evidence SHA, and the ADR range; align its framing with the
   README's. Then decide which of the two is authoritative for progress claims
   and make the other cite it.
2. **Record an ADR for the authentication boundary** before any code: where the
   check lives (API adapter vs application command), what a principal is, how it
   reaches the audit record, and whether the runtime-facing paths are exempt.
3. **Resolve the actor-identity question.** `AuditEvent` carries `actor_type`
   (`OPERATOR` / `SYSTEM`) but no actor id. Auth requires attribution. This
   touches frozen Module 2 and the audit table, so it needs an ADR and a
   migration — the same escalation path ADR-017 used, and it must happen before
   Module 9 rather than during it.
4. **Settle the identity scheme** (`{name}` vs `{deployment_id}`) so scopes are
   written once.
5. **Add the LICENSE.**

### Alongside Module 9

6. Split `DeploymentService` along its existing `_execute_*` seams before adding
   five authorization checks to it.
7. Bound the prediction request body and add the rate-limit hook while the
   identity to key it on is being introduced.
8. Make the Docker suite fail rather than skip when CI expects a daemon.
9. Add the activation-race concurrency test.

### Deferred to Modules 8 and 10 (correctly)

10. Cached readiness gate replacing the per-prediction inspect (Module 8).
11. The worker daemon that removes blocking work from the request pool (ADR-006/010).
12. Retention and disk-pressure policy (ADR-012, Module 10).
13. Build-time isolation ADR and socket-proxy hardening (Module 10).

### Repository polish (any time, low risk)

14. `.gitignore` the graph output; drop the two zips; consolidate the Postman
    trees to one; fold `.forgeos` and FEK duplication into a single stated
    hierarchy; correct the stale docstrings in `api/v1/deployments.py` and
    `domain/deployment/ports.py`.

---

## Prioritized Improvement Roadmap

| Phase | Work | Gate |
| --- | --- | --- |
| 0 — Pre-Module-9 (days) | Items 1–5: status truth, auth ADR, actor-identity ADR + migration plan, identity scheme, LICENSE | No Module 9 code before this closes |
| 1 — Module 9 (Auth) | Items 6–9 delivered *with* auth, not after | Activation race test green; Docker suite non-skipping in CI |
| 2 — Module 8 (Monitoring) | Items 10–11: readiness cache, worker daemon | Prediction latency budget asserted in CI |
| 3 — Module 10 (Hardening) | Items 12–13: retention, build isolation, socket proxy | Disk-pressure policy enforced |
| Continuous | Item 14: repository polish | Clean `git status` on a fresh checkout |

---

## Go / No-Go Assessment for Authentication

**Is ForgeML ready to begin Authentication & Authorization?**

## YES WITH CONDITIONS

### Why YES

The architecture is sound and, more importantly, it is *mechanically defended*.
Authentication is a cross-cutting concern, and cross-cutting concerns are exactly
what destroy codebases with soft boundaries — an auth check leaks into the domain,
a principal object ends up in a repository signature, and two modules later the
dependency direction is gone. ForgeML will not fail that way, because the AST
suite will fail the build first.

The insertion points already exist and are singular. There is one composition
root. There is one middleware. There is one error envelope with one category-to-
status map, so `401` and `403` are two entries in `_CATEGORY_STATUS` and two
members of `ErrorCategory`. There is one audit log that every state change already
writes to. `ActorType.OPERATOR` is already a domain concept — the model
anticipated a principal before there was one to record. This is what a codebase
ready for auth looks like.

Nothing in the seven implemented modules would have to be redesigned to
accommodate authentication.

### The conditions, and why each is genuinely blocking

1. **`PROJECT_STATUS.md` must be corrected first.** ForgeML's own governance says
   a phase may not begin until its entry gate passes, and the entry gate is
   checked against this file. It currently claims 18% completion, names Module 1
   as the last frozen milestone while listing Module 2 as frozen, cites CI
   evidence from fourteen commits ago, and stops the ADR range at 015 when 017 is
   live in source. Beginning a module by consulting a document known to be wrong
   sets the precedent that the governance model is decorative. This is an hour of
   work and it is non-negotiable.

2. **The actor-identity decision must precede the code.** `AuditEvent` records
   *what kind* of actor caused a change but not *which* one. An authorization
   system that cannot answer "who deactivated this version" is not finished, and
   adding `actor_id` means amending a record and a table inside frozen Module 2 —
   an ADR and a migration, on the escalation path ADR-017 established. Discovering
   this mid-module forces the choice between stopping to escalate and quietly
   editing a frozen surface. Make the decision now, while it is cheap.

3. **The identity scheme must be settled.** Deployments are addressed by UUID
   everywhere except `POST /v1/deployments/{name}/predict`. Authorization scopes
   bind to resource identifiers. Writing scopes against a resource with two
   identifiers produces two scope models and an authorization bypass shaped like a
   naming inconsistency.

4. **`DeploymentService` should be split before, not after.** Module 9 will touch
   five command paths in a 615-line class. Splitting a class is a mechanical
   refactor; splitting a class that five authorization checks have been threaded
   through is a security-sensitive one.

5. **LICENSE.** Not an engineering condition, but the review is a v1.0 gate and
   this blocks v1.0 unconditionally.

### Why not NO

None of the findings above are architectural defects. There is no boundary
violation, no leaked abstraction, no dependency pointing the wrong way, no
business logic in an adapter, no provider type in the domain. The debt is
concentrated in documentation drift, repository hygiene, and deferred work that
was deliberately deferred with the reasoning written down. A NO would be
proportionate to a structural problem, and there isn't one.

### Why not unconditional YES

Two of the conditions — actor identity and the identity scheme — are decisions
that Module 9 will otherwise be *forced* to make mid-implementation, under
pressure, and one of them touches a frozen module. The whole point of the freeze
discipline is that such decisions get made deliberately and recorded. Waving
Module 9 through unconditionally would mean the process worked for seven modules
and then stopped working at exactly the module where it matters most.

**Verdict: YES WITH CONDITIONS.** Close Phase 0 of the roadmap above — status
truth, the two ADRs, the identity scheme, and the LICENSE — and Module 9 is clear
to start.
