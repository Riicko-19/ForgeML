# ForgeML Platform Readiness Report

**Milestone:** ForgeML 0.9.1 — Platform Freeze & Release Readiness
**Date:** 2026-07-18
**Baseline SHA:** `f6a2c3c` (plus the documentation commit carrying this report)
**Supersedes:** the 0.9 report of the same name

This is the official checkpoint between ForgeML 0.9.1 and the authentication
module. It replaces the 0.9 report rather than sitting beside it: one readiness
document, always describing the current baseline.

**What changed in method.** The 0.9 report scored a repository largely by
reading it. This one re-derived every claim from a clean clone — the test count,
the coverage figure, the build, the wheel, the lock files, and the determinism of
the package format were all reproduced from scratch. Three of the scores moved
because measurement disagreed with documentation, and one security issue was
found that no amount of reading would have surfaced.

---

## Executive Summary

ForgeML 0.9.1 is a verified engineering baseline. No features were added. The
milestone's product is confidence: the difference between a repository that
describes itself accurately and one that has been checked.

Four things came out of the verification that reading had not found.

**A real vulnerability.** `python-multipart` 0.0.20 carried six advisories, five
of them reachable, all on the multipart parser behind package upload — an
endpoint with no authentication in front of it. Two denial-of-service paths, an
unbounded read triggered by a negative `Content-Length`, and a urlencoded parser
differential. Upgrading to 0.0.32 clears every one. This is the single most
valuable finding of the milestone and it existed for the entire 0.9 cycle
undetected, because nothing in the repository ever ran an advisory check.

**A claimed invariant that nothing tested.** `ActivationService` documents that
the route swap is atomic under the deployment row lock, and the lock is
deliberately plain `FOR UPDATE` rather than `SKIP LOCKED` so a second activation
waits instead of proceeding in parallel. No test drove two callers at one
deployment. There is one now, against real PostgreSQL, and it was verified to
fail when the lock is weakened — a concurrency test that cannot fail is
decoration. This closes the last remaining High finding from the pre-auth review.

**A version wrong on the wire.** `/health` and `/ready` report the installed
distribution version, which was still the `0.1.0` scaffold default while every
document said 0.9.

**Reproducibility that holds.** A clean clone builds, tests, packages, and
smoke-tests with no undocumented step. Both lock files recompile byte-identically.
The example `.forge` package rebuilds to the same SHA-256 — ADR-003's determinism
claim demonstrated rather than asserted.

**The one thing this milestone could not do is the one thing that matters most
for freezing.** Phase 1 required pushing and collecting CI evidence. The working
environment has no git credentials and no `gh`, so nothing was pushed and no
workflow was observed. Every CI step was reproduced locally instead — including
the two lock-verification steps historically most likely to fail — but ADR-014 is
explicit that local green is not freeze evidence. Modules 3–7 remain unfrozen.

---

## Scores

| Category | 0.9 | 0.9.1 | Direction |
| --- | --- | --- | --- |
| Repository Overview / Health | 9.0 | **9.5** | ↑ |
| Architecture Health | 9.5 | **9.5** | → |
| Documentation Health | 9.0 | **9.5** | ↑ |
| Governance Health | 9.0 | **9.0** | → |
| Release Readiness | — | **8.0** | new |
| Testing Confidence | — | **9.0** | new |
| Dependency Health | — | **9.0** | new |
| Security Readiness (pre-auth) | 8.0 | **8.5** | ↑ |
| Developer Experience | 9.5 | **9.5** | → |
| **Overall** | | **9.1 / 10** | |

---

### Repository Overview / Health — 9.5 / 10

244 tracked files, 1.7 MB. 7,063 source lines across 71 Python files; 7,650 test
lines. A 1.08 : 1 test-to-source ratio, which for infrastructure software is the
right side of healthy.

A fresh clone produces an immediately clean `git status` — verified by actually
cloning, not by inspecting `.gitignore`. No generated artifacts, no temporary
outputs, no obsolete archives, no duplicated assets.

The remaining half point is the three-root documentation layout (`FEK`,
`.forgeos`, `docs/`). `GOVERNANCE.md` maps it well and the boundary is defensible,
but a newcomer still meets three directories before one line of code.

### Architecture Health — 9.5 / 10

Unchanged, and unchanged is the correct outcome for a freeze milestone. No
architectural change was made and none was needed.

Dependency direction is enforced by AST tests rather than convention. Ports are
pinned by a single conformance suite that runs against both the real adapter and
the in-memory fake, so the fakes cannot drift into fiction. The domain is
framework-independent apart from the accepted, documented Pydantic dependency.

The 0.9 split of `DeploymentService` into four services holds up under the only
test that matters: the new concurrency test landed in exactly one file, and
`ActivationService` is small enough that the invariant it protects is legible at
a glance. That is what the split was for.

Half a point withheld for the same reason as before: `reconcile()` still issues
N+1 inspects and prediction still costs a `docker inspect`. Both are Module 8's
by design and forbidden here.

### Documentation Health — 9.5 / 10

34 engineering documents, 21 ADRs, and — after this milestone — no internal
contradictions that verification could find.

Two were found and fixed. `docs/RELEASE.md` assigned authentication to Module 9
while `PROJECT_STATUS.md` recorded phase 9 as Dashboard with authentication
deliberately unassigned; the release document now defers to the roadmap and names
ADR-022. The distribution version contradicted every document that mentioned a
version.

`CHANGELOG.md` and `docs/DEPENDENCY_REPORT.md` were added, closing the two
documentation gaps a public release would have exposed.

### Governance Health — 9.0 / 10

Unchanged and deliberately so.

The authority order holds: FEK → ADR → ForgeOS → frozen modules → repository.
ADR-014's freeze discipline was respected under pressure — it would have been
easy to mark Modules 3–7 frozen on the strength of local green, and the report
declines to.

The open authentication-phase decision remains open, correctly. It was raised
during 0.9 rather than settled by edit, and 0.9.1 did not settle it either,
because the milestone forbids changing ADR decisions. ADR-022 is the named
instrument and it is the next governance action.

The missing point is unchanged: `.forgeos/decisions/` holds no decisions, and
governance that exists only in documents describing governance is thinner than it
looks.

### Release Readiness — 8.0 / 10

New category. Everything a release needs exists and was exercised:

| Artifact | State |
| --- | --- |
| `LICENSE` (Apache-2.0), `NOTICE` | ✅ |
| `CHANGELOG.md` | ✅ new |
| `CONTRIBUTING.md`, `SECURITY.md`, `GOVERNANCE.md` | ✅ |
| `CODEOWNERS`, issue and PR templates | ✅ |
| `docs/RELEASE.md` | ✅ corrected |
| Release draft | ✅ `docs/releases/v0.9.1-draft.md` |
| Version consistent across code and docs | ✅ fixed |
| Wheel and sdist build | ✅ `forgeml-0.9.1` |
| Installed-wheel smoke test | ✅ passed |

Two points withheld, both for the same root cause: **no tag can be cut and no
release published, because CI has not run.** The draft is complete and the
checklist is honest about which boxes only the remote can tick. Release
automation also remains unimplemented by choice (ADR-021), so every step here is
manual.

### Testing Confidence — 9.0 / 10

**594 tests, all passing, 97% branch coverage against a 95% gate, ~35 seconds.**

Measured, not quoted. The suite is fast enough that no one is tempted to skip it,
which is a real property and not a vanity metric.

**Skip audit.** Exactly one skip mechanism exists in the entire suite: the two
Docker integration tests, marked `skipif` with the reason `"docker is not
available"`. There are no `xfail`s, no unconditional skips, and no silently
disabled tests. For this release **the Docker tests ran** — they are the two
slowest in the suite (9.0s and 1.6s), which is itself evidence they executed.

**Slowest tests:** Docker full lifecycle 8.99s, Docker build failure 1.63s, API
smoke 1.18s, SIGTERM handling 0.91s. Nothing else exceeds 0.5s. The slow tests
are slow for legitimate reasons — they build real images and start real
containers.

**The activation-race gap is closed.** This was one of the two High findings the
0.9 report honestly reported as unaddressed. The new test holds a `FOR UPDATE`
lock in one live session, starts a second in a thread, asserts it blocks, and
asserts it proceeds once the first commits. It was mutation-checked: weakening
the lock to `SKIP LOCKED` makes it fail.

**The remaining point is the Docker skip, which is a reporting flaw rather than a
coverage flaw.** On a machine with no daemon the suite prints green while
proving nothing about Module 6, and green-when-unproven is the failure mode that
matters. Closing it needs a CI assertion that the Docker tests were collected and
run — a small change, but a workflow change, and this milestone does not make
them.

### Dependency Health — 9.0 / 10

Full report: [`docs/DEPENDENCY_REPORT.md`](docs/DEPENDENCY_REPORT.md).

| Check | Result |
| --- | --- |
| Vulnerabilities, both locks | **0** (was 6) |
| License conflicts | 0 |
| Unpinned dependencies | 0 |
| Unused declared dependencies | 0 |
| Duplicates | 0 |
| Outdated (patch drift) | 7, none carrying an advisory |

Ten runtime dependencies, every one `==` pinned and hash-locked, installed with
`--require-hashes`, with both locks recompiling byte-identically. That is a
stronger supply-chain posture than most projects at 1.0.

One license obligation is now on the record rather than assumed: **psycopg is
LGPL-3.0-only.** Compatible with Apache-2.0 as ForgeML uses it — separately
installed, unmodified, not redistributed — and the report states the reasoning
and the condition under which it changes, which is publishing a container image
that bundles it.

The missing point is process, not state: **no scheduled advisory check.** The six
advisories fixed here were found because this milestone happened to look. Nothing
in CI would have caught them, and nothing will catch the next one.

### Security Readiness (pre-authentication) — 8.5 / 10

Up half a point: six real advisories closed on the unauthenticated upload path.

Unchanged strengths: runtime hardening under ADR-001 (non-root, read-only
rootfs, all capabilities dropped, no new privileges, no Docker socket, egress-free
internal network, resource limits); content-addressed immutable artifacts;
archive extraction that resists traversal and bombs; a single error envelope that
never leaks a trace; server-owned request IDs; bounded JSON logging; no secrets
in the repository; Docker driven through an injectable CLI seam rather than a
socket-mounted SDK.

Unchanged, honestly stated limits: no authentication, control-plane
root-equivalence through the Docker daemon, packages trusted by design, and a
build step less isolated than runtime.

The remaining 1.5 points are authentication itself and the build-time isolation
gap. Neither is in scope here; both are documented in `SECURITY.md`.

### Developer Experience — 9.5 / 10

Unchanged, and the fresh-clone exercise is the evidence. From `git clone` to a
running control plane is four documented commands, each of which does exactly
what a developer would do by hand. `make verify` is one checkpoint whose
definition lives in the Makefile, so CI cannot drift from it — a property that
paid off directly here, since every CI gate was reproducible locally.

`make help` is discoverable. `CONTRIBUTING.md` explains the checkpoint, the
architectural rules, and the review order. Test names read as sentences.

Half a point for the three documentation roots and the fact that a full run needs
both Docker and PostgreSQL, which `make db` eases but does not remove.

---

## Known Risks

| # | Risk | Severity | State |
| --- | --- | --- | --- |
| 1 | **No CI evidence since `4aa140c`** | **Blocking (freeze)** | Open — needs a push; not a code change |
| 2 | Authentication has no roadmap phase | **Blocking (scheduling)** | Open by decision — needs ADR-022 |
| 3 | Docker tests skip silently | High | Open — ran for this release; no CI assertion |
| 4 | ~~No activation-race test~~ | ~~High~~ | ✅ **Closed in 0.9.1** |
| 5 | No scheduled advisory scanning | High | **New** — found six live advisories by hand |
| 6 | Unbounded prediction request body | High | Deferred to authentication (ADR-019) |
| 7 | Build-time isolation gap | High | Documented in `SECURITY.md`; Module 10 |
| 8 | Per-prediction `docker inspect` | High | Module 8 by design |
| 9 | Blocking work in the request pool | High | The deferred worker (ADR-006/010) |
| 10 | No version-listing endpoint | High | Deferred with an owner (ADR-020) |
| 11 | Egress isolation unverified | Medium | Module 10 |
| 12 | `max_entries` unenforced on extract | Medium | Module 10 |
| 13 | No retention / GC | Medium | ADR-012, Module 10 |
| 14 | No rate limiting | Medium | Deferred to authentication (ADR-019) |
| 15 | `reconcile()` N+1 inspects | Medium | Module 8 |
| 16 | Domain depends on Pydantic | Medium | Accepted, documented |
| 17 | FEK numbering gap (24→30) | Low | Accepted |
| 18 | `.forgeos/decisions/` holds no ADRs | Low | Documented in `GOVERNANCE.md` |
| 19 | Truncated image identity (48-bit) | Low | Accepted |

**Risk 5 is new and it is the honest lesson of this milestone.** A dependency
sat six advisories deep on an unauthenticated code path for an entire release
cycle, and the repository's own quality gates — black, ruff, mypy strict,
pytest, 97% coverage — all reported green throughout. Coverage measures whether
code runs, not whether it is safe. A scheduled `pip-audit` job is the smallest
thing that would have caught it.

---

## Deferred Work

**Module 8 — Monitoring.** Cached readiness gate replacing the per-prediction
inspect · batched reconciliation · logs and usage sampling · `restart_count`
finally getting a consumer · retention of observations (ADR-012).

**Authentication (phase unassigned).** Principal plumbed through every command
(ADR-018) · the additive-nullable `actor_id` migration · authentication
middleware and authorization checks at the ADR-019 boundaries · architecture
tests enforcing those boundaries · rate limiting · request-body bounds ·
`GET /v1/deployments/{id}/versions` authorized on arrival ·
`/v1/admin/reconcile` → `/v1/reconciliations`.

**Module 9 — Dashboard.** Per the frozen roadmap.

**Module 10 — Hardening / Release.** Build-time isolation ADR and socket proxy ·
retention and disk-pressure enforcement · `max_entries` on extraction ·
internal-network verification · `DELETE` semantics · SBOM and scanning · release
automation · backup and restore.

**Recommended for the next milestone regardless of which it is:** a CI assertion
that Docker tests ran, and a scheduled `pip-audit`. Both are small, both close
places where the pipeline currently over-reports confidence, and neither is a
feature.

---

## Authentication Prerequisites

| Prerequisite | State |
| --- | --- |
| Actor identity model | ✅ ADR-018 — principal, `actor_id`, additive-nullable migration, no backfill |
| Authentication / authorization boundary | ✅ ADR-019 — auth in the API layer, authz in the application layer |
| Trust boundaries enumerated | ✅ ADR-019 (T1–T4) and `SECURITY.md` |
| Resource identity settled | ✅ ADR-020 — control plane by id, serving path by name |
| Versioning and compatibility policy | ✅ ADR-021 |
| Services small enough to authorize | ✅ four services, verified by the concurrency test landing in one file |
| Dependency direction enforced | ✅ AST architecture tests |
| Ports pinned against drift | ✅ conformance suite, real adapter and fake |
| Audit log ready for an actor | ✅ ADR-018 accepted; migration not yet written |
| Repository suitable for contributors | ✅ license, contributing, security, governance, templates |
| Test suite trustworthy | ✅ 594 passing, activation race now proven |
| Dependencies free of known vulnerabilities | ✅ both locks audit clean |
| **CI evidence for Modules 3–7** | ❌ **not collected — the blocking prerequisite** |
| **Phase assignment for authentication** | ❌ **ADR-022 not written** |

---

## Final Recommendation

### Is ForgeML ready to begin Authentication?

## YES WITH MINOR CONDITIONS

Both conditions are administrative. Neither requires code, architecture, or
design work. Both can be discharged in an afternoon.

### Why YES

The architectural preconditions are met and were checked rather than assumed.

Authentication is invasive in a way most features are not: it touches every
entry point, every command, and the audit trail. A codebase absorbs it well or
badly depending on properties that must exist *before* the work starts, and
ForgeML has them.

Dependency direction is enforced by tests, so authorization cannot quietly leak
into the domain — a violation fails the build. Ports are pinned by a conformance
suite, so adding a principal to a port signature cannot silently desynchronize
the fakes. The four deployment services are small enough that authorization
checks land in four legible places instead of one 615-line file; the new
concurrency test landing entirely inside `ActivationService` is direct evidence
that the seams are real. The trust boundaries are enumerated in advance, the
actor-identity migration is designed as additive-nullable with no backfill, and
the audit log already exists and simply gains a column.

The verification behind those claims is stronger than at 0.9. 594 tests pass at
97% branch coverage. The one High-severity untested invariant is now tested, and
mutation-checked. A clean clone builds, packages, and smoke-tests. Both locks
reproduce byte-identically. Dependencies audit clean after a real vulnerability
was found and fixed. The example package rebuilds bit-for-bit.

Most persuasive is what the milestone did when measurement disagreed with
documentation: it changed the documentation. The version was wrong, the release
document contradicted the roadmap, the test conftest truncated the wrong tables,
and a dependency was six advisories deep. All four were found by checking, all
four were fixed or recorded, and none was quietly smoothed over. A repository
that behaves that way under audit is one that will absorb an invasive feature
honestly.

### The conditions

**1. Push, and record the CI evidence.** Nothing since `4aa140c` has been
verified by GitHub Actions, because nothing has been pushed. Every CI step was
reproduced locally — including both lock-verification steps and the installed
wheel smoke test — but ADR-014 is explicit that local green is not freeze
evidence, and this report will not pretend otherwise. Until that run exists,
Modules 3–7 cannot freeze and `v0.9.1` cannot be tagged. This is the single
highest-value action available and it is one command.

**2. Write ADR-022 and assign authentication a phase.** The frozen roadmap
defines no authentication phase; security work sits inside Phase 10, where
multi-user auth is explicitly flagged as requiring an ADR. ADR-018 through
ADR-021 prepared everything except *when*. Starting the module without settling
this means building against a roadmap that does not describe it — the exact drift
ADR-014 exists to prevent. Three options remain open: insert authentication as a
new phase and shift Dashboard and Hardening; replace Dashboard in V1 and move it
to V2; or deliver authentication inside Phase 10.

### Why not unconditional YES

Because freezing on unverified evidence is precisely the failure ADR-014 was
written to prevent, and because beginning a module the roadmap does not contain
is how a governed project stops being governed. Both conditions are cheap. That
is why they are conditions and not blockers.

### Why not NO

Nothing architectural is missing. Every prerequisite that requires design
judgement is decided, recorded, and — as of this milestone — verified rather than
asserted. The two open items are a `git push` and a decision the project has
already framed and only needs to make. Holding a repository in this state is not
caution; it is delay.

---

**Baseline established.** ForgeML 0.9.1 is the reference point from which
Authentication, Monitoring, and the eventual 1.0 release evolve. Every metric in
this report is reproducible with `make verify` and the commands in
[`docs/DEPENDENCY_REPORT.md`](docs/DEPENDENCY_REPORT.md).
