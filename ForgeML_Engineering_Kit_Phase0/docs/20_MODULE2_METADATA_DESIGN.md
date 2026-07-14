# Module 2 — Metadata Layer Design (as built)

Owner: Database Engineer. Reviewed by Chief Architect, Backend, Security, QA,
Documentation. Subordinate to FEK, the ADR register, and docs 04/05/12.

Status: implementation complete; freeze pending CI evidence (ADR-014).

## Scope

Docs 06 phase 2: *"Records, repositories, migrations, UoW, audit."* Entry gate
(package IDs/states frozen) was satisfied by the Module 1 freeze. Exit gate:
transaction, concurrency, and migration tests — all present and passing.

Not in this module: HTTP (phase 3), analyzer (4), deployment/runtime tables
(5–8), retention enforcement (ADR-012, later phase). None of them is stubbed.

## Scope audit

Clean. No Redis, Kafka, Celery, RabbitMQ, or external broker: ADR-010 makes the
`operations` table the queue and says so explicitly ("does not require an
external queue"). Adding a broker would contradict an accepted ADR, not merely
exceed scope.

## Layering (as built)

```
application/unit_of_work.py      UnitOfWork protocol (consumer-owned)
        │
domain/package|operations|audit  immutable records + ports. No SQLAlchemy.
        ▲
infrastructure/database/         models · mappers · repositories · uow · engine
migrations/                      Alembic
```

`domain/package/ports.py` gains `PackageCatalog` per docs 02's ownership table
(the Package module owns `PackageCatalog`). The `UnitOfWork` protocol lives in
`application/`, not `core/` — see decision D-3; `core → domain` would form an
import cycle against Module 1's existing `domain → core`.

**Enforced, not asserted:** an AST test fails the build if `sqlalchemy`,
`alembic`, or `psycopg` is imported anywhere outside `infrastructure/database/`.

## Changes from the frozen design

Three, all discovered during implementation:

1. **ADR-016 recovery semantics** (D-1) — the design carried `claimed_at` and
   `attempts` with no rule consuming them. Added `recover_orphaned` and
   `claim_next(types=...)` lanes.
2. **`manifest_version` is nullable** (D-6) — the design implied it was set at
   creation, which would have stored a format version before anything read one.
3. **`AuditEvent` carries `id` and `occurred_at`** — docs 04 requires both on
   the record; the original port returned events without them.

## Schema

See `21_MODULE2_IMPLEMENTATION.md`. Four tables, three immutability triggers, one
partial index on claimable operations, one row-value keyset cursor.

## Transaction boundaries

One unit of work per state change. Validation runs *outside* the transaction;
the transaction opens only once the verdict is known and then does three things
atomically: persist the validation, transition the package, append the audit
event. Docs 04 forbids a database transaction spanning provider work, and
nothing here holds a UoW across an artifact read or a Docker call.

## Acceptance criteria — status

| Criterion | Evidence |
| --- | --- |
| Duplicate upload idempotent via a real unique index | `test_insert_races.py` |
| Same key + fingerprint → original operation; changed fingerprint → 409 | conformance suite |
| Two concurrent claims never take the same operation | `test_concurrency.py` |
| State mutation and its audit record share one transaction | conformance suite |
| Checksum/artifact immutable at the database | `test_invariants.py` |
| upgrade/downgrade/upgrade clean; no model drift | `test_migrations.py` |
| Domain imports no SQLAlchemy | architecture test |
| Coverage ≥95% branch | 99% |
