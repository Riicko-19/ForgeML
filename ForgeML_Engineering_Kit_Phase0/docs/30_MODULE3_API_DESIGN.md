# Module 3 — Backend API Design

Owner: Backend Engineer. Reviewed by Chief Architect, Security, QA, Documentation.
Subordinate to FEK, the ADR register, and docs 04/12.

Status: implementation complete; freeze pending CI evidence (ADR-014).

## Scope

Docs 06 phase 3: *"Commands/queries, operation resource, error mapping."* Entry
gate (package/metadata ports stable) satisfied by the Module 2 freeze. Exit gate:
HTTP contract and idempotency tests.

**Surface delivered** (docs 12):

| Method / path | Purpose | Success |
| --- | --- | --- |
| `POST /v1/packages` | Stream a .forge upload and validate it | 202 + Operation + `Location` |
| `GET /v1/packages` | List packages, newest first | 200 |
| `GET /v1/packages/{id}` | Read a package with its findings | 200 |
| `GET /v1/operations/{id}` | Poll a durable operation | 200 |
| `GET /healthz` · `GET /readyz` | Liveness · readiness | 200 / 503 |
| `GET /v1/openapi.json` | The published schema | 200 |

**Not in this module:** deployments, versions, activation, prediction. Those
endpoints belong to the modules that can actually execute them (phases 5–7). No
route is stubbed to "look complete".

## Layering

```
api/v1/{packages,operations,schemas}.py   transport only
        │
application/{package,operations}/services.py   use cases, transaction boundaries
        │
domain ports  ──  infrastructure adapters (Module 1 + Module 2)
```

`core/composition.py` is the only place the graph is wired. The API imports
application use cases (docs 02) and never an ORM, an artifact path, or Docker —
AST-enforced.

## The two decisions that shape everything

**1. Validation runs inline, and still returns an operation.** ADR-010's worker
arrives with the deployment module. Leaving operations PENDING with nothing to
execute them would be a broken system, not a deferral. So the request validates
the archive itself — but it still creates the durable, idempotent operation
record ADR-006 requires and returns 202 with it. When the worker lands, execution
moves behind the same contract and no client changes.

**2. A rejected package is a verdict, not a failure.** The operation *succeeds*
because the validation ran. The package carries `validation_state: rejected` and
its findings. An operation only FAILS when the platform could not do the work —
for example the artifact is unreadable. Blaming the operator for an
infrastructure fault, or reporting a platform fault as a bad package, are both
wrong, and the tests pin the distinction.

## Idempotency (docs 04)

Every mutation requires `Idempotency-Key`. For an upload the target is the
computed SHA-256 and the fingerprint covers the checksum plus declared metadata.
So:

- same key, same bytes, same filename → the **original** operation, no second
  package, no second validation;
- same key, same bytes, **different filename** → `409 idempotency_conflict`;
- same key, **different bytes** → a different target, hence a different
  operation. The key is scoped per target by docs 04, so this is not a conflict.

## Error mapping

Reused wholesale from frozen Module 0. Every repository and service failure is an
`AppError` with a category, which the existing handler maps to a status code and
the frozen envelope. Module 3 adds **no** error-handling machinery — that is the
point of having built it once.

## Correlation

ADR-015: the server generates the request ID; it becomes the operation's
`correlation_id`, so an operation, its audit events, and its logs are all
joinable by one identifier the client cannot forge.

## Readiness

Since Module 2 the control plane cannot serve without its database, so `/readyz`
proves the database answers and returns 503 when it does not. The application
lifespan also runs ADR-016 crash recovery at startup and fails closed if the
database is unavailable (docs 11).

## Acceptance criteria — status

| Criterion | Evidence |
| --- | --- |
| 202 + operation + `Location` on upload | `test_packages_api.py` |
| Idempotent replay; conflict on reused key | `test_packages_api.py` |
| Duplicate bytes resolve to one package | `test_packages_api.py` |
| Findings surface with codes and paths | `test_packages_api.py` |
| Every error uses the frozen envelope | `test_openapi_contract.py` (all 4xx/5xx) |
| OpenAPI publishes exactly the v1 surface | `test_openapi_contract.py` |
| API imports no provider | architecture test |
| Coverage ≥95% branch | 99% |
