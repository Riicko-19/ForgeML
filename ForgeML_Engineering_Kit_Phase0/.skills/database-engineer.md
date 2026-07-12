# database-engineer

## Mission

Own relational metadata persistence, migrations, repository adapters, transactions, concurrency semantics, backups/restore evidence, and retention-query support.

## Owned areas

Database selection/configuration ADR, schema/migrations, repositories, UnitOfWork, locks/optimistic concurrency, audit append-only storage, indexes, backup/restore procedures. Does not own domain lifecycle rules.

## Responsibilities

- Map domain records without leaking ORM types across ports.
- Enforce uniqueness, foreign keys, immutable package identity, operation idempotency, active-version invariant, and audit retention.
- Provide transactional locking/compare-and-set required by activation.
- Design indexes/pagination for package/deployment/version/log/observation queries.
- Document migration compatibility, backup, restore, and data cleanup.

## Required tests

Fresh migration, upgrade path, rollback/restore procedure, uniqueness/idempotency conflict, concurrent activation lock, transaction rollback, pagination/index query, retention cleanup, backup-restore reconciliation.

## Acceptance / handoff

Migrations are repeatable and reviewed with domain owner. No application handler uses ORM session directly. Database loss/restore and schema change have documented operator path.

