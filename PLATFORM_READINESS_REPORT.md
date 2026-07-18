# ForgeML Platform Readiness Report

**Milestone:** ForgeML 0.9 — Stabilization & Platform Readiness
**Date:** 2026-07-18
**Baseline:** `0875662` + the 0.9 stabilization changes
**Predecessor:** [Pre-Authentication Engineering Review](ForgeML_Engineering_Kit_Phase0/docs/38_PRE_AUTH_ENGINEERING_REVIEW.md)

This is the official checkpoint between ForgeML 0.9 and the authentication
module. The engineering review asked *is the architecture healthy?* and answered
"yes, with conditions." This report answers *were those conditions met?* and
records what the repository looks like now.

It is a snapshot, not a decision record. Decisions made during this milestone are
ADR-018 through ADR-021.

---

## Executive Summary

ForgeML 0.9 changed almost no behaviour and a great deal of clarity.

The engineering review found an architecture that had survived seven modules
without a single boundary violation, and a repository that had not kept up with
it: a status file that contradicted itself, three Postman directories, 19 MB of
generated output in version control, no license, and one 615-line service that
the next module would have had to modify five times.

All of that is resolved. The repository now tells one story, the governance says
who owns which document, a fresh clone is clean, and the authentication module
has four accepted ADRs waiting for it instead of four decisions to make under
pressure. `DeploymentService` is four services totalling 820 lines across six
files, and **593 tests pass before and after the split** — verified by running
the suite on both states of the tree, not by assuming.

Two things did not get resolved, and both are honest limitations rather than
oversights. **No CI evidence exists for anything after `4aa140c`**, because the
work has never been pushed; Modules 3–7 therefore cannot be frozen, and no
document in this repository can change that — only a `git push` can.
**Authentication still has no phase number**, because the frozen roadmap assigns
Phase 9 to Dashboard and amending it is an ADR-level decision that was
deliberately left open rather than made by edit.

The verdict is **YES WITH MINOR CONDITIONS**.

---

## Scores

Compared against the pre-milestone review. Same scale, same reviewer standard.

| Dimension | Before | After | Movement |
| --- | --- | --- | --- |
| Repository Health | 6 / 10 | **9 / 10** | +3 |
| Architecture Health | 9 / 10 | **9.5 / 10** | +0.5 |
| Governance Health | 6 / 10 | **9 / 10** | +3 |
| Security Readiness (pre-auth) | 7 / 10 | **8 / 10** | +1 |
| Developer Experience | 8 / 10 | **9.5 / 10** | +1.5 |
| Open Source Readiness | 3 / 10 | **9 / 10** | +6 |

### Repository Health — 9 / 10

A clean clone now produces a clean `git status`. Generated graph output (288
files, 19 MB), Postman's two sync directories, and two redundant kit archives are
untracked and ignored — left on disk, removed from version control, so no local
tooling breaks. Structure is intuitive: `backend/` is the platform, `docs/` is
for contributors, the FEK is the specification, `.forgeos/` is the process.

Not 10: the FEK's document numbering still has a gap at 24→30 and interleaves
designs, reports, and reviews in one flat sequence. Cosmetic, and renumbering
committed documents costs more than it returns.

### Architecture Health — 9.5 / 10

Unchanged where it was already strong — no boundary moved, no dependency
reversed, no provider leaked. The AST-enforced rules still hold, and the split
improved cohesion without touching the dependency graph: `RouteManager` now
depends on `DeploymentQueryService` (a read model) rather than a service that
also builds, activates, and reconciles, which is a smaller and more honest
dependency than it had before.

Not 10: the domain still imports Pydantic (ADR-002's stated "framework
independent" claim is not literally true), and `resolve_active_target` still
returns a routing type from the deployment module. Both are documented, both are
the better of the available options, neither is worth a change now.

### Governance Health — 9 / 10

`GOVERNANCE.md` resolves the question a new contributor actually has: three
documentation roots, which one is authoritative. It defines the authority order,
names both known overlaps (engineering standards, role taxonomies), and assigns
ownership so neither drifts — the FEK owns standards and ForgeOS derives from it;
`.forgeos/roles/` owns process authority and `.skills/` owns domain scope.

Critically, governance was *followed* during this milestone rather than merely
documented. When the instruction to make authentication "Module 9" collided with
the frozen roadmap, the conflict was surfaced and left to an ADR instead of being
resolved by editing the status file. That is the process working under pressure,
which is the only test that counts.

Not 10: `.forgeos/decisions/` still holds only a template while the ADRs live in
the FEK register. Documented in `GOVERNANCE.md`, but two plausible homes remain.

### Security Readiness (pre-authentication) — 8 / 10

The security *model* is now written down and honest. `SECURITY.md` states what
ForgeML does not defend against and why: packages are trusted by design
(ADR-001), the control plane is root-equivalent through the Docker daemon, and
there is no authentication yet. It separates in-scope from out-of-scope reports,
so a researcher does not waste a week rediscovering Module 9.

ADR-019 defines four trust boundaries and three security domains, and places the
authentication check in the API layer and the authorization check in the
application layer — with the rule that the architecture tests will enforce it,
not the review.

Not higher: **no security defect was fixed**, correctly, because this milestone
forbade it. The unbounded prediction body, the unverified internal network, the
`max_entries` gap on extraction, and the build-time isolation gap are all still
open. They are now documented with owners instead of living in a review.

### Developer Experience — 9.5 / 10

`make verify` was already the single gate and remains so. What was missing was
everything around it: `CONTRIBUTING.md` (setup, the checkpoint, the
architectural rules, what review checks), `docs/DEVELOPMENT.md` (how work moves
idea → frozen module), `docs/RELEASE.md`, `docs/LABELS.md`, issue and PR
templates that ask the questions reviewers actually ask ("which module?", "does
this touch a frozen contract?", "where is the ADR?").

A contributor can now clone, read four files, and act correctly without project
history. That was the stated success criterion.

Not 10: the Docker-dependent suite still skips silently. A contributor can run
`make verify`, see green, and have never executed the runtime adapter's tests.

### Open Source Readiness — 9 / 10

The single largest movement, from the single largest gap. `LICENSE`
(Apache-2.0, with the patent grant appropriate to infrastructure), `NOTICE`,
`SECURITY.md` with a private reporting path, `CODEOWNERS` scoped to the places
where a wrong change is expensive, and a versioning and compatibility policy
(ADR-021) that states plainly that pre-1.0 carries no guarantee rather than
implying one.

Not 10: no `CHANGELOG.md` yet — correct, since nothing has been released — and
no CI badge can be trusted until the repository is pushed.

---

## Milestone Delivery

### Phase 1 — Repository Truth ✅

`PROJECT_STATUS.md` rewritten. Every contradiction the review found is resolved:

| Was | Now |
| --- | --- |
| "~18% (2 of 11 frozen)" while listing 3 frozen | Implemented **8/11**, Frozen **3/11**, with the difference explained |
| "Last frozen milestone: Module 1" | Module 2 |
| "ADR-001 … ADR-015" | ADR-001 … ADR-021 |
| Silent about unpushed work | CI gap stated as the largest open item |
| README "583 tests" | 593 — measured, and the stale figure corrected in both files |

The implemented-versus-frozen distinction is now explicit, because conflating
them was the root of most of the drift.

### Phase 2 — Governance Stabilization ✅

`GOVERNANCE.md`: the map, the authority order, ownership of both overlaps, the
decision process, the artifact taxonomy, and a table of single sources of truth.

### Phase 3 — Repository Organization ✅

Untracked (kept on disk): `graphify-out/`, `postman/`, `.postman/`, and two kit
`.zip` archives. `.gitignore` rewritten with a comment per rule explaining *why*
each is ignored. Tracked files: 221.

### Phase 4 — Developer Experience ✅

`LICENSE`, `NOTICE`, `CONTRIBUTING.md`, `SECURITY.md`, `.github/CODEOWNERS`,
`.github/pull_request_template.md`, three issue templates plus `config.yml`
routing security reports away from public issues, `docs/DEVELOPMENT.md`,
`docs/RELEASE.md`, `docs/LABELS.md`.

### Phase 5 — Architecture Preparation ✅

Four ADRs. No implementation.

- **ADR-018** — Principal model and actor identity. One principal kind
  (operator) with an opaque `actor_id`; `AuditEvent` gains an *optional*
  `actor_id`; the `audit_events` table gains a *nullable* column with **no
  backfill**, because inventing historical principals would forge the audit
  trail the ADR exists to protect. Additive, reversible, and explicitly on the
  ADR-017 escalation path for a frozen surface.
- **ADR-019** — Authentication in the API layer, authorization in the
  application layer, nothing in the domain. Four trust boundaries, three security
  domains, health endpoints stay unauthenticated, and the rule is enforced by
  architecture tests.
- **ADR-020** — Resource identity resolved: **control plane by id, serving path
  by name.** Scopes bind to the UUID; the prediction route resolves name → id
  internally so the name is never a permission subject. Four known API gaps get
  owners.
- **ADR-021** — SemVer, three independently versioned contracts, the
  compatibility promise that begins at 1.0, deprecation policy, branch and
  support policy.

### Phase 6 — DeploymentService Preparation ✅

| Before | After |
| --- | --- |
| `services.py` — 615 lines, 5 responsibilities | `queries.py` 78 · `lifecycle.py` 303 · `activation.py` 152 · `reconciliation.py` 100 · `support.py` 123 · `services.py` 64 |

`DeploymentServices` is a bundle, not a facade — it holds the four and forwards
nothing, so a call site names the responsibility it uses
(`services.activation.activate_version(...)`). Authorization checks will land in
four small files.

**Behaviour preservation was measured, not assumed:** the full suite was run on
the pre-refactor tree (593 passed) and the post-refactor tree (593 passed) by
stashing and restoring, and the collected test count was confirmed identical on
both. `make verify` passes at 97% branch coverage.

### Phase 7 — API Consistency ✅ (documented)

Resolved in ADR-020. No endpoint changed — adding routes would have been the
feature creep this milestone forbids, and an unauthenticated enumeration endpoint
added now would need retrofitting the moment authorization arrives.

### Phase 8 — Documentation Refresh ✅

- `api/v1/deployments.py` — removed the docstring claiming the router was not yet
  wired (it has been since Module 6).
- `domain/deployment/ports.py` — `lock_deployment` no longer describes Module 7
  in the future tense; `restart_count` and `list_versions` now say *why* they are
  unused and which module consumes them.
- `domain/package/ports.py` — `ArtifactStore.delete` records that it is ADR-012's
  primitive and that artifacts currently accumulate without bound.
- ADR-015 / ADR-016 reordered.

### Phase 9 — Engineering Standards ✅

Verified: dependency direction holds (AST tests unmodified and passing), naming
is consistent, imports are clean, mypy strict passes on 121 source files, and all
internal markdown links across the eight top-level documents resolve (checked
programmatically — 0 broken).

### Phase 10 — Release Readiness ✅

ADR-021 and `docs/RELEASE.md`. Automation deliberately not implemented.

---

## Remaining Technical Debt

Carried from the review with current status. Nothing here blocks authentication
except where marked.

| # | Item | Severity | Status |
| --- | --- | --- | --- |
| 1 | **No CI evidence since `4aa140c`** | **Blocking (freeze)** | Open — requires `git push`, not a code change |
| 2 | Authentication has no roadmap phase | **Blocking (scheduling)** | Open by decision — needs an ADR amending docs 06 |
| 3 | Docker tests skip silently | High | **Open** — not addressed in 0.9 |
| 4 | No activation-race concurrency test | High | **Open** — not addressed in 0.9 |
| 5 | Unbounded prediction request body | High | Open — deferred to the auth module (ADR-019) |
| 6 | Build-time isolation gap | High | Documented in `SECURITY.md`; Module 10 |
| 7 | Per-prediction `docker inspect` | High | Open — Module 8 by design; forbidden here |
| 8 | Blocking work in the request pool | High | Open — the deferred worker (ADR-006/010) |
| 9 | No version-listing endpoint | High | Deferred with an owner (ADR-020) |
| 10 | Egress isolation unverified | Medium | Open — Module 10 |
| 11 | `max_entries` unenforced on extract | Medium | Open — Module 10 |
| 12 | No retention / GC | Medium | Open — ADR-012, Module 10 |
| 13 | No rate limiting | Medium | Deferred to the auth module (ADR-019) |
| 14 | `reconcile()` N+1 inspects | Medium | Open — Module 8 |
| 15 | Domain depends on Pydantic | Medium | Open — accepted, documented |
| 16 | FEK numbering gap (24→30) | Low | Accepted — renumbering costs more than it returns |
| 17 | `.forgeos/decisions/` holds no ADRs | Low | Documented in `GOVERNANCE.md` |
| 18 | Truncated image identity (48-bit) | Low | Accepted |

**Items 3 and 4 are the honest gaps in this milestone.** Both were rated High by
the review, and neither was in the ten phases this milestone defined. Adding a
concurrency test and a CI Docker gate is the right first work of the next
milestone, whichever it is — not because they block authentication, but because
they are the two places where the test suite currently over-reports confidence.

---

## Deferred Items

### Module 8 — Monitoring

Cached readiness gate replacing the per-prediction inspect · batched
reconciliation · logs and usage sampling · `restart_count` finally getting a
consumer · retention of observations (ADR-012).

### Authentication module (phase unassigned)

Principal plumbed through every command (ADR-018) · `actor_id` migration ·
authentication middleware and authorization checks at the boundaries ADR-019
defines · architecture tests enforcing those boundaries · rate limiting ·
request-body bounds · `GET /v1/deployments/{id}/versions`, authorized on arrival
· `/v1/admin/reconcile` → `/v1/reconciliations`.

### Module 10 — Hardening / Release

Build-time isolation ADR and socket proxy · retention and disk-pressure
enforcement · `max_entries` on extraction · internal-network verification ·
`DELETE` semantics · SBOM and scanning · release automation · backup and restore.

---

## Exit Criteria

| Criterion | Status |
| --- | --- |
| Repository tells one consistent story | ✅ |
| Repository clone is clean | ✅ 31 intended changes, no generated files |
| Governance is internally consistent | ✅ `GOVERNANCE.md` |
| Documentation is synchronized | ✅ README ↔ `PROJECT_STATUS.md` reconciled |
| Repository structure is intuitive | ✅ |
| `DeploymentService` ready for authentication | ✅ four services, behaviour verified identical |
| Authentication ADRs exist | ✅ ADR-018, 019, 020 |
| Actor identity strategy exists | ✅ ADR-018, with migration strategy |
| Trust boundaries documented | ✅ ADR-019, `SECURITY.md` |
| LICENSE exists | ✅ Apache-2.0 |
| CONTRIBUTING exists | ✅ |
| SECURITY policy exists | ✅ |
| Release strategy exists | ✅ ADR-021, `docs/RELEASE.md` |
| Every blocking review issue resolved | ⚠️ **All except CI evidence**, which no document can resolve |

---

## Final Recommendation

### Is ForgeML ready to begin the authentication module?

## YES WITH MINOR CONDITIONS

*(The frozen roadmap assigns Phase 9 to Dashboard and defines no authentication
phase. This answer is about readiness for authentication work, not about a
number. Assigning it one is condition 2.)*

### Why YES

Every condition the engineering review raised as blocking has been closed except
the two that cannot be closed by writing code or documents.

The four decisions that would otherwise have been made mid-implementation — how
a principal is modelled, how identity reaches the audit trail through a frozen
schema, where the checks live, and which identifier scopes bind to — are all
accepted ADRs. The service that would have absorbed five authorization checks is
four services. The status file that gates module entry is now accurate. The audit
model has a migration strategy that is additive, reversible, and refuses to
fabricate history.

More telling than any of that: the governance held under pressure. The
instruction to make authentication "Module 9" conflicted with the frozen
roadmap, and the conflict was surfaced rather than resolved by quietly editing
the authoritative document. A process that survives an inconvenient collision is
a process that will survive the authentication module.

### The conditions

1. **Push and record CI evidence.** Nothing since `4aa140c` has been verified by
   GitHub Actions. Modules 3–7 cannot be frozen without it (ADR-014), which means
   authentication would be built on five unfrozen contracts — precisely the
   situation the freeze discipline exists to prevent. This is a `git push`, and
   this environment has no credentials to perform it.

2. **Assign authentication a phase.** ADR-022 amending `06_IMPLEMENTATION_ROADMAP.md`,
   deciding among: insert as a new phase and shift Dashboard and Hardening;
   replace Dashboard in V1; or deliver inside Phase 10.

3. **Close the two test gaps first.** Make the Docker suite fail rather than skip
   when CI expects a daemon, and add the activation-race concurrency test. Both
   are places where the suite currently reports more confidence than it has, and
   authentication will add authorization checks to the exact activation path that
   is untested under concurrency.

### Why not unconditional YES

Condition 1 is not paperwork. Building authentication against contracts that have
never passed CI means that if a Module 5 defect surfaces later, it will be
unclear whether it predated the authentication work — and the freeze record
exists specifically to make that question answerable.

### Why not NO

Nothing structural is wrong. The architecture that passed the review unchanged is
the same architecture, and every gap remaining is either scheduled, documented
with an owner, or resolvable by a push.

---

**ForgeML 0.9 is complete.** The repository is in the healthiest state it has
been: one story, clean tree, defined governance, stated license, documented
security model, and four decisions banked for the module that comes next.
