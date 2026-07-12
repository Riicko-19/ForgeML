# Module 0 Architecture Clarification Report

**Status:** APPROVED by user instruction to fix, freeze, and implement Module 0  
**Raised by:** Chief Architect, design review iteration 1  
**Affected module:** Module 0 — Foundation  
**Implementation state:** Not started  
**Decision rule:** AC-001 through AC-004 accepted; design iteration 2 authorized

## 1. Reason for stopping

The Module 0 scope audit passed and no V2 feature was detected. The design review did
not pass because several behaviors that become foundational contracts are undefined
or inconsistent in the FEK. Under the Engineering Authority Protocol, implementation
and the next design iteration are paused rather than allowing implementation choices
to become accidental architecture.

This report proposes the smallest additions necessary to make Module 0 deterministic.
It does not add product functionality.

## 2. Approval decisions

### AC-001 — Control-plane Python support

**Gap:** ADR-008 fixes Python 3.11 for generated model runtimes but does not define the
control-plane Python range. Coding Guidelines require a documented supported range.

**Proposed decision:** ForgeML V1 backend/control plane supports CPython `>=3.11,<3.12`.
All backend CI, locks, package metadata, and production images use Python 3.11. Patch
updates are accepted after the normal dependency/test review and are not architectural
changes.

**Why this is minimal:** It reuses the only Python minor version already accepted by
the FEK and avoids maintaining two interpreter targets.

**FEK change after approval:** Add an ADR or one sentence to docs 08 and record the
decision in docs 10.

**Approval:** ACCEPTED.

### AC-002 — V1 CI provider and ownership

**Gap:** Engineering Standards require CI to enforce formatting, linting, typing,
tests, and contracts, but no CI provider, owner, or configuration location is defined.
Module 0 cannot meet its exit gate using local commands alone.

**Proposed decision:** Use one GitHub Actions workflow at
`.github/workflows/backend-quality.yml`, owned by the Backend Engineer and reviewed by
QA. It runs on Linux with the supported Python 3.11 range and enforces dependency-lock
verification, Black check, Ruff lint, mypy, unit, integration, contract, package build,
and installed-package smoke tests. It introduces no deployment, release, cloud, or
matrix infrastructure.

**Why this is minimal:** One hosted workflow enforces the FEK gate without adding a
service to the ForgeML runtime architecture. The same repository commands remain the
source of truth locally and in CI.

**Alternative if GitHub is not the repository authority:** Approve provider-neutral
quality scripts in Module 0 and name the exact later phase/provider that must add CI.
This alternative requires a narrow FEK exception because Module 0 would not satisfy
the current CI acceptance statement.

**FEK change after approval:** Record provider, path, ownership, and mandatory gates
in docs 06/07.

**Approval:** ACCEPTED.

### AC-003 — Request-ID authority

**Gap:** The FEK requires correlation IDs but does not say whether an untrusted client
may supply the canonical request ID. The draft accepted `X-Request-ID`, which permits
client-selected collisions and log confusion and would become a frozen HTTP contract.

**Proposed decision:** ForgeML always generates a UUIDv4 request ID at the control-plane
boundary. Any inbound `X-Request-ID` is ignored and never logged or reflected. Every
HTTP response, including errors, returns the server-generated ID in `X-Request-ID`,
and the same value appears in request-scoped structured events. Trusted upstream trace
propagation is deferred until the FEK defines an authenticated proxy boundary.

**Why this is minimal:** It supplies correlation without a trust registry, proxy
configuration, additional header, or client-controlled canonical identifier.

**FEK change after approval:** Add the authority and response-header behavior to docs
07, 11, and 12.

**Approval:** ACCEPTED.

### AC-004 — Prediction runtime error status inconsistency

**Gap:** Low-Level Design classifies a model execution failure as opaque HTTP 500,
while the higher-authority External Contracts document defines HTTP 502 with code
`prediction_runtime_failed`.

**Proposed decision:** Preserve docs 12 as authoritative: prediction upstream failure
is HTTP 502 with code `prediction_runtime_failed`. Amend docs 04 to match. HTTP 500 is
reserved for unexpected control-plane failures.

**Why this is minimal:** It applies the FEK's documented conflict-resolution order and
does not introduce new behavior.

**FEK change after approval:** Correct the single conflicting row in docs 04.

**Approval:** ACCEPTED; docs 04 corrected to the higher-authority docs 12 contract.

## 3. Design corrections that do not require architecture approval

After AC-001 through AC-004 are decided, design iteration 2 will apply these review
corrections without expanding scope:

1. Move the application composition factory to `core/composition.py`; keep the root
   bootstrap/entry point as a process adapter.
2. Classify composition functions and aggregate settings types as internal Python
   surfaces. Freeze operator configuration keys and HTTP/error/log wire contracts,
   not the evolving composition signature.
3. Define Module 0 readiness as HTTP 200 after successful composition. The 503 branch
   remains an external FEK status for a later owning provider module and is not
   fabricated or tested as Module 0 behavior.
4. Define exact ErrorEnvelope, ErrorDetail, health schemas, omission/null rules,
   content type, and status/code mappings for 400, 404, 405, 409, 422, 429, 500, 502,
   and 503. Only the wire envelope is frozen; internal categories remain additive.
5. Use an allowlisted structured failure event containing exception class/category
   only. Never serialize exception arguments, message, repr, traceback, host paths,
   raw environment values, headers, or payloads.
6. Disable Uvicorn access logs. Emit one bounded JSON request-completion event with
   method, matched route template (or `unmatched`), status, duration, and request ID;
   never log raw target/query.
7. Make application construction free of process-global logging mutation. A process
   bootstrap validates settings, configures logging once, constructs the app, and
   runs one Uvicorn worker. Configuration failure emits a fixed safe JSON event to
   stderr and exits nonzero without a traceback.
8. Reject unknown `FORGEML_*` keys in the composed Module 0 namespace and sanitize
   Pydantic errors to field location/type without input values. Later modules extend
   the recognized allowlist through owned settings groups.
9. Select setuptools as build backend and `pip-tools` as the lock generator.
   `pyproject.toml` is authoritative for direct dependencies; hashed runtime/dev lock
   files are generated from it and verified unchanged. Black owns formatting; Ruff
   owns linting; mypy owns static typing; coverage.py enforces branch coverage.
10. Add `tests/contract` for health/error/OpenAPI/header shapes and an AST-based
    dependency-direction test requiring no new library.
11. Disable public OpenAPI/docs/Redoc routes in Module 0; contract tests call the
    in-process schema generator. Phase 3 may add the documented API publication path.
12. Define exact process bind, port, worker, reload, proxy-header, graceful-shutdown,
    and exit behavior, plus exact quality commands and a requirement-to-test matrix.
13. Add negative cases for malformed requests, 404/405, configuration casing/empty
    values, repeated construction, logging initialization, request cancellation,
    concurrency isolation, package metadata absence, and graceful shutdown.

## 4. Dependency approval inventory

No dependency will be installed until the clarification is approved and exact
compatible pins are reviewed in implementation iteration 1.

| Dependency | Scope | Necessity |
| --- | --- | --- |
| FastAPI | Runtime | FEK-mandated HTTP framework |
| Pydantic v2 | Runtime | FEK-mandated transport/settings validation baseline |
| Uvicorn | Runtime | Single-process ASGI server needed to boot the service |
| setuptools | Build | Standard Python package build backend |
| pytest | Development | Required unit/integration/contract test runner |
| HTTPX | Development | In-process ASGI HTTP contract testing |
| Black | Development | FEK-mandated formatter |
| Ruff | Development | FEK-mandated linter |
| mypy | Development | Required static type gate |
| coverage.py | Development | Enforces the specified critical branch coverage gate |
| pip-tools | Development | Generates reproducible hashed dependency locks |
| build | Development | Verifies wheel/sdist creation and clean installed smoke test |

No DI framework, logging framework, architecture-test framework, task runner, service,
message broker, cache, database, Docker client, or frontend dependency is approved for
Module 0.

## 5. Review iteration accounting

| Iteration | Result | Disposition |
| --- | --- | --- |
| 1 — initial design | FAIL | Scope PASS; clarification and deterministic contract corrections required. |
| 2 — revised design | NOT STARTED | Begins only after AC-001 through AC-004 approval. |
| 3 — final polish | RESERVED | Used only if iteration 2 reviewers find remaining issues. |

If iteration 3 still fails, Module 0 will stop with the detailed blocker report required
by the EEP. No implementation review iteration has been consumed because no code has
been written.

## 6. Approval request

Approve, reject, or amend AC-001, AC-002, AC-003, and AC-004. Approval authorizes the
Chief Architect and Documentation Engineer to make only the stated FEK corrections
and complete design iteration 2. It does not authorize implementation; implementation
may begin only after every design review records PASS.
