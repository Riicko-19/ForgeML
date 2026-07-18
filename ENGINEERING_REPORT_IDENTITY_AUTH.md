# Engineering Report — Epic 1: Identity & Authentication

**Date:** 2026-07-18 · **Baseline:** `c114d50` + documentation
**Scope:** ForgeML's first security capability
**Companion documents:** [`docs/IDENTITY_AND_AUTH.md`](docs/IDENTITY_AND_AUTH.md) ·
[`docs/SECURITY_REVIEW_EPIC_1.md`](docs/SECURITY_REVIEW_EPIC_1.md) ·
[`docs/AUTHENTICATION_GUIDE.md`](docs/AUTHENTICATION_GUIDE.md) ·
[ADR-022 … ADR-026](ForgeML_Engineering_Kit_Phase0/docs/10_ARCHITECTURE_DECISIONS.md)

---

## Executive Summary

ForgeML was, until this epic, an entirely unauthenticated control plane with root-equivalent
authority over its host. That was the single largest gap in the repository, and it is now closed:
every `/v1` route requires a credential, every operator command is attributed in an append-only
audit trail, and there is no configuration, header, or environment that turns any of it off.

**The epic added no dependency.** The whole subsystem is `hashlib`, `hmac`, and `secrets` from the
standard library.

Four things are worth a reader's attention above the rest.

**The two most serious findings were design-level, and both were closed before code existed.** An
authenticated `POST /v1/api-keys` would have let *every* key mint more keys — a leaked CI key could
issue itself a permanent replacement, and revoking the original would achieve nothing. A
`FORGEML_AUTH_ENABLED` flag would have been a root bypass switch on a root-equivalent service.
Neither was implemented and then removed; both were refused in an ADR. That is the return on
ADR-019 having decided *where* authentication lives months before deciding *when* to build it.

**The architecture absorbed a cross-cutting concern without a redesign.** No layer moved, no port
changed shape, and the dependency direction held — mechanically, not by review. The 0.9 split of
`DeploymentService` into four services is what made principal threading a mechanical diff rather
than surgery on a 615-line class.

**Coverage went up, not down: 97% → 98%, on 774 tests (+180).** Because ADR-025 left no bypass,
every existing API test now runs through the real verifier. The authenticated path is not a
special case in the test suite; it is the only path.

**Writing the tests found two real defects** that reading the code had not: control characters
decoded as valid ASCII and reached the credential verifier, and the key CLI leaked its database
connection. Fixing the second surfaced a latent landmine — `AppError` is a frozen slots dataclass
and cannot propagate through a `@contextmanager`, because `contextlib` unwinds by assigning to
`__traceback__`.

**What this epic explicitly did not do is limit what an authenticated caller may ask for.** ForgeML
now knows *who* is asking. Every valid key can still do everything, and because the control plane
drives a root daemon, **an API key is a root credential for the host** until Epic 2.

---

## Architecture Decisions

Five ADRs. Each records the alternatives it rejected and why, so a future reader can tell a
decision from an accident.

| ADR | Decision | The reasoning that mattered |
| --- | --- | --- |
| **022** | Epics as a cross-cutting track | The frozen roadmap had no authentication phase. Renumbering it would invalidate every "Module 8/9/10" reference across 34 documents to solve a filing problem. Epics are additive: phases unchanged, nothing renumbered. |
| **023** | One principal kind; absence is `None` | An `ANONYMOUS` singleton type-checks everywhere an authenticated principal is expected. `None` cannot. The absence of identity must be a compile-time error, not a runtime value with weak privileges. |
| **024** | API keys; SHA-256, not a KDF | A KDF imposes cost on *guessing*, and there is no guess space in 256 CSPRNG bits. Its work factor would be paid on every request — a DoS amplifier any anonymous caller could trigger. |
| **025** | Always on, no bypass | The flag that makes local development pleasant is the flag that gets copied into a production environment file. On a service that drives a root daemon, that flag is a root bypass. |
| **026** | Key administration off HTTP | With authentication and no authorization, an authenticated key-creation endpoint is privilege escalation delivered as a convenience feature. |

**ADR-022 also settled a governance question two prior milestones had deliberately left open.**
ForgeML 0.9 and 0.9.1 both recorded that authentication had a home in the code and none in the
plan, and both declined to fix it by editing a frozen document. That restraint is what made it
possible to resolve it properly here rather than discovering the conflict mid-implementation.

---

## Security Assessment

Full analysis: [`docs/SECURITY_REVIEW_EPIC_1.md`](docs/SECURITY_REVIEW_EPIC_1.md).

| # | Finding | Severity | State |
| --- | --- | --- | --- |
| 1 | HTTP key management would be privilege escalation | **Critical** | Closed by design (ADR-026) |
| 2 | A bypass flag would be a root bypass | **Critical** | Closed by design (ADR-025) |
| 3 | Control characters reached the verifier | Medium | **Fixed** |
| 4 | CLI leaked its database connection | Low | **Fixed** |
| 5 | Any valid key has full authority | **High** | **Accepted — Epic 2** |
| 6 | No rate limiting on the auth path | Medium | Open — Epic 2 |
| 7 | Keys do not expire by default | Medium | Open — operator discipline |
| 8 | No transport security enforced | Medium | Open — deployment concern |
| 9 | `last_used_at` write on every request | Low | Accepted |

**No Critical or High finding is open and unmitigated.** Finding 5 is High and accepted, because it
*is* the epic boundary — it is stated in the README, `SECURITY.md`, the guide, the changelog, and
the readiness section below, rather than buried.

Specific attacks analysed and closed: timing (equal-cost miss path; secret verified *before*
expiry/revocation so revocation is not detectable by timing), enumeration (uniform failures;
authentication before routing so route existence is not observable), credential leakage (asserted
against both rendered messages and structured log fields), identity spoofing (a `Principal` is only
ever constructed from a verified key), and audit forgery (attribution is truthful or absent, never
synthetic).

**Session fixation and CSRF are not applicable** — there are no sessions and no cookies, so there is
no ambient authority a browser could be tricked into using. This is a property worth defending: if
the Dashboard phase introduces cookie sessions, CSRF enters scope and that analysis must be redone.

---

## Test Results

```
774 passed in 30.87s          (was 594 at 0.9.1 — +180)
98% branch coverage           (was 97% — gate is 95%)
0 skipped                     Docker tests ran
```

| Module | Coverage |
| --- | --- |
| `api/authentication.py` | **100%** |
| `core/principal.py` | **100%** |
| `domain/identity/credentials.py` | **100%** |
| `domain/identity/models.py` | **100%** |
| `domain/identity/ports.py` | **100%** |
| `application/identity/services.py` | 97% |

**Coverage rose while adding a subsystem**, which is the direct consequence of ADR-025: with no
bypass, every pre-existing API test now exercises the real verifier.

What the new tests actually hold:

- **Token policy, exhaustively** — it is pure, so there is no excuse not to. Includes the
  underscore-bearing secret a naive `split("_")` would silently truncate into a prefix comparison.
- **The 256-bit width is asserted**, because ADR-024's hashing decision rests on it. A silent
  narrowing would invalidate the reasoning without failing anything else.
- **Route coverage is enumerated from the live application**, not a maintained list, so a route
  added tomorrow is covered today. A hand-kept list would drift silently and in the unsafe
  direction.
- **Failures are asserted indistinguishable** — unknown, wrong, revoked, expired, and malformed all
  collapse to one outcome, because anything richer eventually becomes an enumeration oracle.
- **The absence of a bypass is asserted structurally** — no configuration field containing "auth",
  "secure", or "insecure" may exist.
- **The boundary is enforced by AST tests** — no transport type below the API layer, exactly one
  reader of the principal contextvar, no authorization identifier anywhere yet.

The concurrency test added at 0.9.1 is now the third-slowest test in the suite, which is a good
sign: it is doing real work against real PostgreSQL rather than asserting against a mock.

---

## Documentation Summary

| Document | Purpose |
| --- | --- |
| `docs/IDENTITY_AND_AUTH.md` | Design, with class/sequence/layer/state/trust-boundary diagrams |
| `docs/SECURITY_REVIEW_EPIC_1.md` | Threat model, nine findings, OWASP assessment, attack analysis |
| `docs/AUTHENTICATION_GUIDE.md` | Operator guide: first run, troubleshooting, rotation, incident queries |
| ADR-022 … ADR-026 | The decisions and their rejected alternatives |
| `CHANGELOG.md` | Breaking change stated first, with the upgrade commands |
| `SECURITY.md`, `README.md`, `PROJECT_STATUS.md` | Posture, quick start, and progress reconciled |

Four documents rather than the ten originally scoped. `REPOSITORY_REVIEW.md` and
`ARCHITECTURE_REVIEW.md` would have restated the 0.9.1 readiness report, and a separate
`SECURITY_GUIDE.md` would have been the security review rewritten for a second audience. **Fewer
documents that stay accurate beat more documents that drift** — and every document above has a
distinct reader.

The README quick start was updated because it would otherwise have been *wrong*: those `curl`
commands now return 401 without a key.

---

## Technical Debt

**Introduced by this epic:** essentially none. No dependency, no new layer, no port changed shape,
no abstraction with one implementation beyond the `CredentialVerifier` seam — which exists to be
implemented twice and is the mechanism by which JWT arrives without a redesign.

Two items worth naming:

| Item | Severity | Note |
| --- | --- | --- |
| `AppError` cannot cross a `@contextmanager` | Low | A latent landmine, not new. Documented at the fix site; it will bite again. |
| `last_used_at` writes on every authenticated read | Low | Accepted; needed for compromise review, and its failure cannot reject a valid credential |

**Carried, unchanged:** the build-time isolation gap (Phase 10), unbounded artifact accumulation
(ADR-012, Phase 10), per-prediction `docker inspect` (Phase 8), `reconcile()` N+1 (Phase 8), and
the Docker-tests-skip-silently reporting flaw (recommended for the next milestone).

**The largest debt is not code.** Modules 3–7 and Epic 1 are all implemented and unfrozen, because
ADR-014 requires CI evidence at a named SHA and none has been recorded since `4aa140c`. Commits are
pushed; the run's result has not been read back into `PROJECT_STATUS.md`.

---

## Deferred Work

**Epic 2 — Authorization.** Permission model, per-command checks at the entry of each application
service (ADR-019 already fixed the location), scoped and read-only keys, HTTP key management with
a scope to guard it, and rate limiting keyed on identity.

**Later:** users and teams (needs an identity provider), sessions (Dashboard phase), JWT/OAuth2/OIDC
(a new `CredentialVerifier`, composed in one line), tenancy (V2).

**Recommended before Epic 2, neither of which is a feature:** a CI assertion that the Docker tests
actually ran, and a scheduled `pip-audit`. Both close places where the pipeline currently
over-reports confidence — the second is how 0.9.1 found six live advisories, by hand.

---

## Authorization Readiness

Epic 2 is a smaller job than Epic 1 because Epic 1 did not cut corners on placement.

| Prerequisite | State |
| --- | --- |
| A principal exists at every command entry point | ✅ Threaded as an argument, not ambient |
| Authorization has a decided home | ✅ ADR-019 — application layer, at each service method |
| Services small enough to authorize individually | ✅ Four deployment services, one reason to change each |
| The domain stays free of caller identity | ✅ AST-enforced |
| Audit answers "who did what" | ✅ `actor_id` indexed; incident query documented |
| A credential record to hang scopes on | ✅ `api_keys` exists and is additively extensible |
| No authorization logic to unpick | ✅ Asserted by test — nothing was built early |
| Key management design not yet fixed | ✅ Deliberately deferred, so Epic 2 designs it freely |

That last row is the one most likely to be undervalued. Shipping a key-management endpoint in Epic
1 would have forced Epic 2 to stay compatible with a shape designed before the authorization model
existed. Deferring it means the endpoint gets designed *from* the permission model rather than the
model being reverse-engineered from an endpoint.

---

## Overall Engineering Score

| Dimension | Score | Notes |
| --- | --- | --- |
| Architecture fit | **10 / 10** | Cross-cutting concern absorbed with no layer moved and no port reshaped |
| Security | **9 / 10** | Two Criticals closed at design time; finding 5 open by definition, not oversight |
| Test quality | **9.5 / 10** | Enumerated rather than listed; two real defects found by writing them |
| Documentation | **9.5 / 10** | Four documents, distinct readers, reasoning recorded not asserted |
| Governance | **9.5 / 10** | An open decision two milestones old, settled by ADR rather than by edit |
| Simplicity | **10 / 10** | Zero dependencies added; one Protocol with one method is the entire extension mechanism |
| Release readiness | **7 / 10** | Complete and green locally; **no CI evidence, so nothing can freeze** |
| **Overall** | **9.2 / 10** | |

---

## Lessons Learned

**Deciding placement before scheduling paid for itself.** ADR-019 fixed where authentication and
authorization live long before either was built. That is why the two Critical findings appear as
"closed by design" — they were caught by an ADR asking "where does this go?", which is a question
that surfaces privilege problems that "how do I implement this?" does not.

**Removing the bypass improved the tests, not just the security posture.** The expected cost was a
mechanical migration of every API test. The unexpected benefit was that the authenticated path
stopped being a special case — coverage went *up*, and the code that runs in production is now the
code the tests run.

**Writing tests found what reading did not.** Both defects came from writing an adversarial case,
not from reviewing the implementation. The control-character case in particular looked fine on
inspection: `\x00` is valid ASCII, decodes without error, and only misbehaves once you ask what
happens next.

**Two regex-driven bulk edits over-applied**, both times by matching a repository method that
happened to share a name with a service method — the same class of mistake as the 0.9 `sed`
incident. The type checker caught both immediately and listed the exact call sites. **Mechanical
edits need a mechanical check**, and mypy strict is that check.

**The audit trail's honesty required refusing to fill in blanks.** It was tempting to attribute
crash-recovered work and reconciliation findings to whoever triggered them. Both would have been
false — the request is gone in one case, and the container drifted on its own in the other. In an
append-only record, a wrong answer is permanent and a missing one is correctable.

---

## Recommendations

1. **Read the CI result and record it.** Everything since `4aa140c` is unfrozen. This is one
   action and it unblocks freezing Modules 3–7 and Epic 1.
2. **Tag `v0.10.0`, not `v0.9.2`.** Requiring a credential on every route is a breaking change to
   the only public surface ForgeML has. Under `0.x` that carries no promise, but the version should
   still say what happened.
3. **Add the two pipeline guards** — assert the Docker tests ran; schedule `pip-audit`. Small,
   not features, and both close over-reporting.
4. **Start Epic 2 with scopes, not endpoints.** Design the permission model first and let key
   management fall out of it. ADR-026 deliberately left that door open.
5. **Revisit key expiry defaults when scopes land.** A short-lived scoped key is a much easier
   default to justify than a short-lived all-powerful one.
6. **Re-examine CSRF if the Dashboard introduces cookies.** Today's "not applicable" depends
   entirely on there being no ambient authority.

---

## Is ForgeML ready to begin Epic 2 — Authorization?

# YES

Not "yes with conditions". The conditions that qualified the two previous milestones were about
*authentication* — its ADRs, its phase assignment, its prerequisites — and this epic discharged
them. What remains is a release action, not an engineering one.

**The evidence:**

Every architectural precondition for authorization exists and is enforced rather than intended. A
`Principal` reaches every command entry point as an explicit argument, so an authorization check
has something to decide on. ADR-019 already fixed where those checks go, and an AST test fails the
build if the domain reaches for a caller. The four deployment services each have one reason to
change, so checks land in four legible places instead of threading through a god class. The audit
trail can already answer "who did what", which is what makes an authorization decision reviewable
after the fact.

Nothing has to be unpicked first. A test asserts that no authorization identifier exists anywhere
in the source — Epic 1 did not build ahead of itself, so Epic 2 inherits no early guesses to stay
compatible with. Key management was deliberately not shipped, which means the endpoint will be
designed *from* the permission model rather than the model reverse-engineered from an endpoint.

The verification is real: 774 tests at 98% branch coverage, route coverage enumerated from the live
application, the absence of a bypass asserted structurally, and the security review reaching no
open Critical or High finding that is not the epic boundary itself.

**The honest qualification, which is not a condition on starting:**

CI evidence has still not been recorded, so Modules 3–7 and Epic 1 remain unfrozen under ADR-014.
That blocks *tagging a release*, and it should be cleared. It does not block starting Epic 2,
because freezing protects a public surface from changing silently — and Epic 2 will change that
surface deliberately, under its own ADRs, which is exactly the process ADR-014 exists to enforce.

**And the reason Epic 2 should start promptly:** finding 5 is High and open. Until authorization
exists, every API key is a root credential for the host. Epic 1 made ForgeML able to say *who*.
The reason to build Epic 2 is that knowing who is asking is only half of a security boundary.
