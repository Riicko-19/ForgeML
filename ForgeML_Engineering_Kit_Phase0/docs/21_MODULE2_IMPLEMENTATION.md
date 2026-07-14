# Module 2 — Metadata Layer Implementation

**Status: FROZEN**
**Freeze date: 2026-07-14**
**Freeze authority: ADR-014 (satisfied normally — no exception)**
**Frozen baseline: `2c8c8721e3739529ae4862d5c712b3ba1b93a11e`**
**CI evidence: `Backend quality` on `2c8c8721` — conclusion `success`**

Verified independently against the GitHub Actions API: the workflow ran on the
frozen SHA itself, which is also local HEAD and remote `main`. Not a local-only
claim.

## What was implemented

The durable metadata layer: package records, validation persistence, durable
operations with idempotency and crash recovery, an append-only audit trail, the
repository pattern, a unit of work, the PostgreSQL schema, and Alembic
migrations.

Module 2 deliberately ships **no HTTP surface** (phase 3) and **no Docker,
runtime, or build behaviour** (phases 4+). Nothing for those phases is stubbed.

## Files created

| Layer | File |
| --- | --- |
| domain | `domain/operations/{models,ports}.py` — `Operation`, `OperationState`, `OperationType`, `OperationFailure`, `OperationStore` |
| domain | `domain/audit/{models,ports}.py` — `AuditEvent`, `ActorType`, `AuditLog` |
| application | `application/unit_of_work.py` — the `UnitOfWork` protocol |
| infrastructure | `infrastructure/database/models.py` — the only SQLAlchemy mappings |
| infrastructure | `infrastructure/database/mappers.py` — ORM row ↔ immutable domain record |
| infrastructure | `infrastructure/database/repositories.py` — the three port adapters |
| infrastructure | `infrastructure/database/unit_of_work.py` — `SqlAlchemyUnitOfWork` |
| infrastructure | `infrastructure/database/engine.py` — engine and session factory |
| migrations | `alembic.ini`, `migrations/env.py`, `migrations/versions/0d7adf1f94cf_*.py` |
| tests | `tests/fakes.py`, `tests/contract/test_port_conformance.py`, `tests/integration/database/*`, `tests/unit/domain/test_metadata_records.py`, `tests/unit/infrastructure/test_mappers.py` |

## Files modified

| File | Change | Amendment class |
| --- | --- | --- |
| `domain/package/models.py` (frozen M1) | **Added** `PackageState`, `Package` | Additive — no existing symbol changed |
| `domain/package/ports.py` (frozen M1) | **Added** `PackageCatalog`, `PackagePage` | Additive — pre-declared in docs 19 |
| `core/config.py` (frozen M0) | **Added** `database_url` (SecretStr), pool size, statement timeout, `require_database_url()` | Additive |
| `.github/workflows/backend-quality.yml` | Added `postgres:16` service | Required — ADR-009 forbids SQLite |
| `pyproject.toml`, both locks | `sqlalchemy==2.0.51`, `alembic==1.18.5`, `psycopg[binary]==3.3.4` | Additive |
| `tests/architecture/test_dependency_direction.py` | Added ORM-confinement gate | Additive |

Both frozen-module changes are purely additive and change no existing symbol's
meaning, but they are still amendments to frozen modules and are recorded here
rather than made silently.

## Public interfaces

```
PackageCatalog   get_or_create · find_by_id · find_by_checksum
                 save_validation · list · findings_for
OperationStore   begin · get · claim_next · complete · fail · recover_orphaned
AuditLog         record · for_target · for_correlation
UnitOfWork       __enter__/__exit__ · commit · rollback → .packages .operations .audit
```

## Database schema

`packages` (sha256 UNIQUE — the idempotency mechanism), `package_validations`
(ordered findings as JSONB; UNIQUE on package + validator version), `operations`
(UNIQUE on idempotency_key + type + target_id; partial index on pending rows for
the claim query), `audit_events` (append-only).

Three triggers enforce what the ORM cannot: package checksum and artifact are
immutable, terminal operations are immutable, audit events reject UPDATE and
DELETE. They defend the invariants against an operator with `psql` open, which
ADR-004 explicitly anticipates.

## Migrations

One revision, `0d7adf1f94cf`. Verified: `upgrade → downgrade → upgrade` clean,
offline `--sql` generation works, downgrade removes its own trigger functions,
and `alembic check` reports **no drift** from the models.

## Engineering decisions

Recorded in full in `23_MODULE2_ENGINEERING_DECISIONS.md`.

## Tradeoffs

- **Findings as JSONB, not a child table** — bounded, always read whole, never
  filtered by code. Reversible by migration if phase 9 wants to query them.
- **`operations.target_id` is typed text with no FK** — an operation targets a
  package (sha256) or, from phase 5, a version (uuid); no single FK spans both.
  Referential integrity for operation targets lives in the repository. This is
  the weakest joint in the schema and is deliberately visible.
- **`expire_on_commit=False`** — safe only because mappers rebuild every value
  as a frozen record before it leaves infrastructure.

## Technical debt

- Retention/GC (ADR-012) is not implemented; the columns and indexes it needs
  exist. Owned by its phase.
- `PackageCatalog.list` does not bound `limit`; docs 12 bounds it at the HTTP
  boundary (phase 3).
- `validator_version` is a hand-maintained string. A validator bugfix that does
  not bump it retains the stale verdict. Flagged in the audit; fix is scheduled.

## Known limitations

- No HTTP surface and no worker process: `claim_next`/`recover_orphaned` exist
  and are tested, but nothing calls them until phase 3/5.
- Only `OperationType.PACKAGE_VALIDATE` exists. Build, start, stop, activate,
  and reconcile arrive with the modules that can execute them.

## CI evidence

All gates pass locally on Python 3.11 against real PostgreSQL 16:

| Gate | Result |
| --- | --- |
| black / ruff / mypy --strict | clean (73 source files) |
| pytest (unit, integration, contract, architecture) | **366 passed** |
| coverage (branch, gate 95%) | **99%** |
| migrations: up/down/up, offline SQL, drift | clean |
| concurrency: SKIP LOCKED, forced insert races | pass |
| architecture: layering, ORM confinement, no-execution | pass |
| graphify | 1184 nodes, **no import cycles** |

GitHub Actions evidence: **`Backend quality` on `2c8c8721` — `success`.**
ADR-014 is satisfied on its ordinary terms.

## Amendment after freeze (Module 3)

Module 3 required one **additive** port method, recorded here rather than made
silently: `OperationStore.claim(operation_id)`. An inline executor must run *its
own* operation; `claim_next()` takes the oldest pending one, which under
concurrent uploads would execute another request's work and report the wrong
result. No existing symbol changed meaning; the conformance suite covers it.
