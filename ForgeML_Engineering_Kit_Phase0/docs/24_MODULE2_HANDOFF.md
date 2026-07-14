# Module 2 — Handoff

For the engineer who inherits the metadata layer. Read this before you touch it.

## The one idea

**Concurrency is delegated to PostgreSQL, never to application code.** Every
idempotent write here is an INSERT that expects to lose a race sometimes,
catches the constraint violation on a savepoint, and reads the winner's row. If
you ever find yourself writing `if not exists: insert`, you have introduced a
bug: two transactions both pass that check and both insert.

## Public contracts

```
PackageCatalog   get_or_create · find_by_id · find_by_checksum
                 save_validation · list · findings_for
OperationStore   begin · get · claim · claim_next · complete · fail · recover_orphaned
AuditLog         record · for_target · for_correlation
UnitOfWork       context manager · commit · rollback → .packages .operations .audit
```

These are the laws Module 3 and later may rely on. They are pinned by
`tests/contract/test_port_conformance.py`, which runs against **both** the
in-memory fakes and real PostgreSQL. **Add a port method, add it to that suite** —
otherwise the fakes drift and every downstream test built on them is a lie. This
has already happened twice and the suite caught it both times.

## Repositories

`SqlAlchemyPackageCatalog`, `SqlAlchemyOperationStore`, `SqlAlchemyAuditLog`. All
take a `Session` and return **immutable domain records**, never ORM objects.
`mappers.py` is the membrane; an AST test fails the build if `sqlalchemy` is
imported anywhere outside `infrastructure/database/`.

## UnitOfWork

One session, one transaction, three repositories. Exiting the context **rolls
back** unless you called `commit()`. That is deliberate: a use case that raises
halfway must leave no trace, and one that forgets to commit must not silently
persist.

```python
with uow:
    package = uow.packages.get_or_create(...)
    uow.packages.save_validation(package.id, validation)
    uow.audit.record(AuditEvent(...))
    uow.commit()
```

**Never hold a unit of work across provider work** (an artifact read, a Docker
build). Docs 04 forbids it, and `PackageService` shows the pattern: close the
transaction, do the work, open a new one to record the result.

## Database

PostgreSQL 16 only (ADR-009). SQLite cannot express the row-locking semantics
operation claims depend on, so it is not a supported adapter — not even for
tests. Four tables, and three triggers that enforce what application code cannot
be trusted to:

| Invariant | Enforced by |
| --- | --- |
| A package checksum and artifact never change (ADR-003) | `packages_immutable` trigger |
| A terminal operation never changes (docs 04) | `operations_terminal` trigger |
| Audit events reject UPDATE and DELETE | `audit_append_only` trigger |
| One package per checksum | `uq_packages_sha256` |
| One operation per (key, type, target) | `uq_operations_...` |

The triggers exist because ADR-004 explicitly anticipates an operator with a
`psql` prompt. An invariant that only holds when our code is the sole writer is
not an invariant.

## Transaction boundaries

A state change and the audit record describing it are **one transaction**. If
they could commit separately, the audit trail would be a record of things that
might not have happened.

## Common mistakes

1. **Checking existence before inserting.** See "the one idea". Use the unique
   index.
2. **Using `claim_next()` when you mean `claim(id)`.** `claim_next` takes the
   *oldest pending* operation, which under concurrency is somebody else's work.
   An inline executor must claim its own operation by id.
3. **Treating an empty lane as no lane.** `claim_next(types=())` selects
   *nothing*, not *everything*. Truthiness here is a production incident.
4. **Returning an ORM row.** It lazy-loads after the session closes. Map it.
5. **Assuming `recover_orphaned` runs itself.** It is called once, from the
   application lifespan. Recovery that is never called is a comment.
6. **Bumping a model without a migration.** `test_the_models_match_the_migration`
   will fail you, which is the point.
7. **Storing a fact you have not read.** `manifest_version` is null until
   validation parses the archive. Do not "helpfully" default it.

## Module 3 entry gate — satisfied

Docs 06: *"Package/metadata ports stable."* They are, and they are pinned by an
executable conformance suite rather than a promise.

## What Module 3 (and later) may depend upon

- Package identity is the SHA-256 of the bytes; duplicate upload is idempotent.
- `begin()` returns the *original* operation for a replayed request, and raises
  `AppError(CONFLICT, idempotency_conflict)` for a reused key with a different
  fingerprint. The HTTP layer maps that to 409 with no extra work.
- Every repository failure is an `AppError` with a category, which Module 0's
  error mapping already turns into the right status code. **Do not catch and
  re-raise; just let it propagate.**
- Findings persist in order, with their paths, and round-trip exactly — they are
  the docs 12 error-envelope details.
- Operations are durable and terminal-immutable, so a poll is always truthful.

## What Module 2 deliberately does not give you

- No worker. `claim_next` and `recover_orphaned` exist and are tested; the worker
  process that drives them arrives with the deployment module (ADR-010).
- No retention or garbage collection (ADR-012). The columns and indexes are
  there; the sweeper is not.
- No bound on `list(limit=...)`. Docs 12 bounds it at the HTTP boundary, and
  Module 3 does.
