# Module 3 — Backend API Implementation

Status: implementation complete; **freeze pending CI evidence (ADR-014)**.

## Files created

| Layer | File |
| --- | --- |
| api | `api/v1/packages.py` — upload, list, read |
| api | `api/v1/operations.py` — poll |
| api | `api/v1/schemas.py` — wire models, opaque cursor codec |
| application | `application/package/services.py` — `PackageService`, `PackageDetail` |
| application | `application/operations/services.py` — `OperationService` |
| infrastructure | `infrastructure/database/provider.py` — lazy engine, readiness, ADR-016 startup recovery |
| tests | `tests/integration/api/{conftest,test_packages_api,test_lifecycle_and_failures}.py` |

## Files modified

| File | Change | Amendment class |
| --- | --- | --- |
| `core/composition.py` (M0) | Wires the container; lifespan; publishes OpenAPI | Behavior |
| `api/health.py` (M0) | `/readyz` proves the database answers | **Behavior** |
| `domain/operations/ports.py` (M2) | **Added** `claim(operation_id)` | Additive |
| `infrastructure/database/repositories.py` (M2) | Implements `claim` | Additive |
| `tests/architecture/...` (M0) | API may import `application` (docs 02) | Corrects a rule that contradicted the FEK |
| `tests/contract/test_openapi_contract.py` (M0) | Asserts the real v1 surface | Behavior |
| `tests/integration/api/test_health.py` (M0) | Readiness fails closed with no database | Behavior |
| `tests/integration/api/test_process_signals.py` (M0) | Real process needs a real database | Behavior |
| `tests/smoke/installed_package_smoke.py` (M0) | Expects the v1 paths | Behavior |
| `pyproject.toml`, both locks | `python-multipart==0.0.20` | Additive |

Module 0's architecture rule forbade `api → application` outright, because no
application layer existed when it was written. Docs 02 *requires* that
dependency. The rule was corrected, not bypassed: the API still may not import
`infrastructure`, `sqlalchemy`, or `docker`, and that is AST-enforced.

## Public interfaces

```
PackageService   upload(stream, filename, idempotency_key, correlation_id) -> Operation
                 get(package_id) -> PackageDetail
                 list(limit, cursor) -> PackagePage
OperationService get(operation_id) -> Operation
DatabaseProvider unit_of_work() · check_readiness() · recover_orphaned_operations() · dispose()
```

## Engineering decisions

`33_MODULE3_ENGINEERING_DECISIONS.md`.

## Technical debt

- Upload spools to a temporary file before the artifact store hashes it, so a
  large archive touches disk twice (D-5).
- The audit trail is written but has no read endpoint; docs 12 does not define
  one for V1.
- No rate limiting. Docs 12 makes 429 conditional on configuration, and rate
  limiting without authentication is theatre.

## Known limitations

- **No authentication.** Docs 11 keeps the control plane on an administrative
  network until an authorization ADR exists. This remains the single largest
  open risk in ForgeML and is unchanged by this module.
- Validation runs inline; the worker arrives with the deployment module (D-1).
- Only `package_validate` operations exist.

## CI evidence

All gates pass locally on Python 3.11 against real PostgreSQL 16:

| Gate | Result |
| --- | --- |
| black / ruff / mypy --strict | clean, 84 source files |
| pytest (unit, integration, contract, architecture) | **411 passed** |
| coverage (branch, gate 95%) | **99%** |
| locks reproducible · wheel build | pass |
| graphify | 1376 nodes, **no import cycles** |

GitHub Actions: **pending push**. Module 3 is not frozen until `Backend quality`
passes on its frozen SHA (ADR-014).
