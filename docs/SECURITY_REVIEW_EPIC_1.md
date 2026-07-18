# Security Review — Epic 1: Identity & Authentication

**Reviewed:** 2026-07-18 · **Baseline:** `c114d50` · **Reviewer role:** Principal Security Engineer
**Scope:** the identity and authentication subsystem only. Authorization is Epic 2 and is
explicitly out of scope — see [What this review does not cover](#what-this-review-does-not-cover).

---

## What is actually being protected

ADR-019 records the fact that sets every stake in this document, and it deserves restating
in plain language before any finding:

> The ForgeML control plane drives the Docker daemon, and the Docker daemon is root.

The authentication boundary is not protecting model metadata. **It is protecting host root.**
Anyone who can reach `/v1` with a valid credential can cause containers to be built and run on
the host. Every decision below was made against that threat, not against a generic "protect the
API" threat, and the severity ratings reflect it.

---

## Threat model

### Assets

| Asset | Why it matters |
| --- | --- |
| The Docker daemon | Root-equivalent. The real prize. |
| API keys | Bearer credentials for the above. |
| The audit trail | The only record of who did what. Append-only, so corruption is permanent. |
| Package artifacts | Contain model code that will be executed. |
| The metadata database | Holds key digests, deployment state, audit history. |

### Actors

| Actor | Capability |
| --- | --- |
| Anonymous network caller | Can reach the listening port. No credential. |
| Holder of a valid key | Full control-plane authority. **No privilege separation until Epic 2.** |
| Holder of a revoked or expired key | Should have nothing. |
| Operator with shell + database access | Everything, including key minting. Already root-equivalent. |
| Someone holding a database dump | Has key digests, audit history, deployment state. |

### Trust boundaries (ADR-019)

```
                     ┌─────────────────────────────────────────┐
   T1  untrusted     │  Operator  ──HTTP──▶  Control plane     │
   ─────────────────▶│            Bearer token                 │
   authenticate,     │                 │                       │
   then admit        │        ┌────────┴────────┐              │
                     │        ▼                 ▼              │
                     │  T2 PostgreSQL     T3 Docker daemon     │
                     │  trusted           TRUSTED + ROOT       │
                     │  same host              │               │
                     │                         ▼               │
                     │                  T4 runtime container   │
                     │                  semi-trusted,          │
                     │                  egress-free network    │
                     └─────────────────────────────────────────┘
```

Epic 1 hardens **T1 only**. T2, T3, and T4 are unchanged.

---

## Findings

Nine findings. **No Critical or High findings remain open.** Two Critical issues were
identified and closed during design rather than implementation — recorded here because a
review that only lists what survived hides the decisions that mattered most.

| # | Finding | Severity | State |
| --- | --- | --- | --- |
| 1 | Key management over HTTP would be privilege escalation | **Critical** | **Closed by design** (ADR-026) |
| 2 | A bypass flag would be a root bypass | **Critical** | **Closed by design** (ADR-025) |
| 3 | Control characters reached the verifier | Medium | **Fixed** in this epic |
| 4 | CLI leaked its database connection | Low | **Fixed** in this epic |
| 5 | Any valid key has full authority | **High** | **Accepted, Epic 2** |
| 6 | No rate limiting on the authentication path | Medium | Open — Epic 2 (ADR-019) |
| 7 | Keys do not expire by default | Medium | Open — operator discipline |
| 8 | No transport security enforced by ForgeML | Medium | Open — deployment concern |
| 9 | `last_used_at` write amplifies read load | Low | Accepted |

---

### 1. Key management over HTTP would be privilege escalation — Critical, closed by design

**The finding.** The obvious design is `POST /v1/api-keys`, authenticated like everything else.
With authentication and no authorization, *every valid key could mint more keys*. A key leaked
from a CI log could issue itself a fresh permanent credential, and revoking the original would
accomplish nothing — the attacker holds a key the operator never knew existed.

This is the most serious issue in the epic, and it is invisible until you notice that
"authenticated" and "authorized to do this specific thing" are different questions.

**Resolution.** ADR-026: Epic 1 exposes no key-management HTTP surface at all. Keys are minted
out-of-band by a CLI whose authorization is possession of the database credential and shell
access — authority that is already root-equivalent, so the tool grants nothing new.

**Verified by:** `test_no_authorization_check_has_appeared_yet` (no permission logic exists yet),
and the absence of any `api_keys` route in `test_every_route_that_is_not_public_refuses_an_anonymous_caller`.

---

### 2. A bypass flag would be a root bypass — Critical, closed by design

**The finding.** `FORGEML_AUTH_ENABLED=false` is the convenience nearly every framework ships.
It is also the single most reliable way to run an unauthenticated production service, because
the flag that makes local development pleasant is the flag that gets copied into an environment
file. On a control plane that drives a root daemon, that flag is a root bypass.

**Resolution.** ADR-025: no such setting exists. No environment variable, no header, no
"development mode", no localhost exemption. The public path list is a two-element constant in
code, not configuration.

**Verified by:** `test_there_is_no_setting_that_disables_authentication` asserts structurally
that no configuration field containing "auth", "secure", or "insecure" has appeared;
`test_the_public_list_is_exactly_the_two_documented_paths` makes widening the list require
deleting an assertion.

**Cost, honestly stated.** A developer must run `make key` before their first request, and every
API test carries a header. Both were paid. The payoff is that the authenticated path is the only
path, so the code that runs in production is the code the tests run.

---

### 3. Control characters reached the verifier — Medium, fixed

**The finding.** `b"Bearer \x00\x01"` decodes as valid ASCII, so a token consisting of control
characters passed header parsing and reached `verify()`. It was ultimately rejected by token
parsing, but control bytes should not travel that far — they end up in query parameters and log
formatters, and each of those is somewhere a control character can do something surprising.

Found by writing `test_undecodable_header_bytes_are_refused_not_crashed`, not by reading the code.

**Fix.** `_presented_token` now rejects any token containing a character below `0x20` or equal to
`0x7f`.

---

### 4. CLI leaked its database connection — Low, fixed

The key CLI created a `DatabaseProvider` and never disposed it. Harmless in a short-lived
process, but it is how a leak reaches a long-running caller later. Fixed with an explicit
`try/finally`.

**A landmine worth recording:** the first fix used `@contextmanager`, which broke. `AppError` is
a frozen slots dataclass, and `contextlib` unwinds by assigning to `exc.__traceback__` — which
such a class refuses, converting a clean "no such key" into an unrelated `TypeError`. **No
`AppError` may propagate through a `@contextmanager` anywhere in this codebase.** A comment at
the fix site records this.

---

### 5. Any valid key has full authority — High, accepted, Epic 2

**The finding.** Epic 1 delivers authentication, not authorization. Every valid key can do
everything: upload packages, deploy versions, activate, stop, reconcile. There is no read-only
key, no scope, and no separation between a CI pipeline's key and an administrator's.

Given that the control plane is root-equivalent through Docker, **every API key is effectively a
root credential for the host.**

**Why accepted.** This is the definition of the epic boundary, not an oversight. Authorization
without an identity model is what produces permission systems bolted to endpoints; ADR-019 fixed
the order deliberately.

**Required mitigations until Epic 2 lands** — these belong in the operator documentation and are
in `docs/AUTHENTICATION_GUIDE.md`:

- Treat every API key as a root credential for the host.
- Issue one key per consumer so revocation is surgical.
- Do not place the control plane on an untrusted network.
- Review `last_used_at` and revoke anything dormant.

---

### 6. No rate limiting on the authentication path — Medium, open

An anonymous caller can present credentials as fast as the server accepts connections. This does
not meaningfully help them guess a 256-bit secret, but it is a cheap denial-of-service vector and
it makes the audit log noisy.

Deferred to Epic 2 by ADR-019, which is correct: rate limiting belongs with the identity it keys
on, and keying it on IP alone would be both weaker and harder to reason about.

**Interim mitigation:** a reverse proxy in front of the control plane.

---

### 7. Keys do not expire by default — Medium, open

`--expires-days` exists but is optional, and a key created without it lives until revoked. The
default was chosen so that a first-run key does not silently stop working mid-deployment, which
is its own incident — but the safer default is arguable and should be revisited when scoped keys
arrive.

**Interim mitigation:** pass `--expires-days` for anything automated, and audit `list` output.

---

### 8. No transport security enforced by ForgeML — Medium, open

A bearer token over plaintext HTTP is readable by anything on the path, and ForgeML does not
require TLS or refuse to start without it. This is deliberate — TLS termination is a deployment
concern and forcing it into the process would duplicate what a reverse proxy does better — but
it means **the credential's confidentiality depends entirely on the operator's deployment.**

**Interim mitigation:** terminate TLS in front of the control plane. Documented in the guide.

This is also why HMAC request signing was rejected in ADR-024: it protects against exactly this,
but at a usability cost, and it does not help if the endpoint is reachable at all.

---

### 9. `last_used_at` write amplifies read load — Low, accepted

Every authenticated request performs a small write. On a single-server control plane with human-
scale traffic this is not a concern, and the data is genuinely needed for compromise review. The
write is outside the request's transaction and its failure cannot reject a valid credential
(`test_authentication_survives_a_failure_to_record_use`).

---

## OWASP Top 10 (2021) assessment

| Category | Assessment |
| --- | --- |
| **A01 Broken Access Control** | **Partially addressed.** Authentication enforced on every non-public route, verified by enumeration. Authorization does not exist — finding 5. |
| **A02 Cryptographic Failures** | Addressed. 256-bit CSPRNG secrets; only SHA-256 digests stored; constant-time comparison; secrets never logged, never echoed, shown once. Transport security is the operator's — finding 8. |
| **A03 Injection** | Addressed. All queries are SQLAlchemy-parameterised; `key_id` is validated as lowercase hex before reaching a query; control characters rejected at the header. |
| **A04 Insecure Design** | Addressed as the central concern. The two Critical findings were both design-level and both closed by ADR before code existed. |
| **A05 Security Misconfiguration** | Addressed. No bypass to misconfigure; fail-closed configuration rejects unknown `FORGEML_*` variables; the public path list is code, not config. |
| **A06 Vulnerable Components** | Addressed at 0.9.1 (six advisories cleared). No dependency added by Epic 1 — the entire subsystem uses `hashlib`, `hmac`, and `secrets` from the standard library. |
| **A07 Identification and Authentication Failures** | Addressed. Uniform failures, no enumeration oracle, no session fixation surface (no sessions), immediate revocation, no default credential. |
| **A08 Software and Data Integrity** | Addressed for identity. Audit rows are append-only with an immutability trigger; attribution is truthful or absent, never synthetic. |
| **A09 Logging and Monitoring Failures** | **Partially addressed.** Every authentication failure is logged with a reason and `key_id`; every operator command is attributed. There is no alerting or metrics — Phase 8. |
| **A10 SSRF** | Not applicable to this epic; unchanged from ADR-001 (runtime containers are egress-free and endpoints are platform-internal). |

---

## Specific attack analysis

**Replay.** A bearer token is inherently replayable by anyone who obtains it; this is true of all
bearer schemes. Mitigated by transport security (operator-provided) and immediate revocation. The
alternative — HMAC request signing with a nonce — was rejected in ADR-024 as disproportionate for
a single-server control plane, and it does not help against a stolen key, only against a passive
observer.

**Timing.** Two paths were considered and both were closed. An unknown `key_id` spends the same
work as a wrong secret via `absorb_miss` against a fixed dummy digest; the secret comparison uses
`hmac.compare_digest`. **Additionally, the secret is verified before the key's expiry and
revocation state** — checking state first would let an attacker detect revocation by timing,
which reveals that a `key_id` is real.

**Enumeration.** All failures produce identical responses (`test_every_failure_is_indistinguishable_to_the_caller`),
and authentication runs before routing, so route existence is not observable without a credential
(`test_an_unknown_path_is_401_before_it_is_404`). `key_id` values are not secret and their
enumeration gains nothing without the paired secret.

**Credential leakage.** The secret is never logged (asserted against both the rendered message and
every structured field), never returned in an error, never stored, and displayed exactly once.
`key_id` is logged deliberately and is safe by construction.

**Authentication bypass.** No bypass exists to find. Enumerated over the live route table rather
than a maintained list, so a new route is covered on the day it is added.

**Confused deputy.** Not introduced. The control plane already acts on the Docker daemon on a
caller's behalf; Epic 1 narrows who may ask, and adds no new indirect authority.

**Session fixation, CSRF.** Not applicable. There are no sessions and no cookies — authentication
is a header on every request, so there is no ambient authority a browser could be tricked into
using. This is a property worth preserving when the Dashboard arrives: **if the Dashboard
introduces cookie sessions, CSRF becomes in scope and this analysis must be redone.**

**Audit integrity.** Attribution is truthful or absent. Crash-recovered work records `SYSTEM`
rather than inventing the operator who originally asked, and reconciliation findings stay `SYSTEM`
because the container drifted on its own. A synthetic actor would be a false claim in an
append-only record.

**Identity spoofing.** A `Principal` is only ever constructed from a verified key
(`ApiKey.principal()`) or explicitly as `SYSTEM`. No request field influences it, and no header
maps to `actor_id`.

---

## What this review does not cover

- **Authorization.** Epic 2. Finding 5 states the consequence plainly.
- **The build-time isolation gap.** Pre-existing, documented in `SECURITY.md`, owned by Phase 10.
- **Docker daemon exposure.** Pre-existing and architectural (ADR-001, ADR-019 T3).
- **Package content trust.** Deploying a package means running its code. Unchanged by this epic.
- **Transport security.** Deployment concern; finding 8.

---

## Conclusion

Epic 1 closes the largest security gap ForgeML had — an entirely unauthenticated root-equivalent
control plane — and closes it without introducing a bypass, a default credential, an enumeration
oracle, or a privilege-escalation path.

The two Critical findings were both caught at design time, and both would have been genuinely
serious had they shipped: an authenticated key-minting endpoint, and a development bypass flag.
That they appear here as "closed by design" rather than "fixed" is the substantive result of
ADR-019 having decided placement before any code was written.

**The one thing an operator must understand:** until Epic 2, every API key is a root credential
for the host. ForgeML now knows *who* is asking. It does not yet limit *what* they may ask for.
