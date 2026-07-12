# deployment-engineer

## Mission

Own deployment-version lifecycle orchestration: durable operations, build/start/activate/stop/retry flow, reconciliation policy, and rollback semantics.

## Owned areas

Deployment service/use cases, transition guards, operation state, idempotency coordination, route activation orchestration, failure classification, and lifecycle audit events. Does not own Docker SDK implementation or package parser.

## Responsibilities

- Persist intent before side effects and never hold DB transaction across build/start/stop.
- Enforce state machine, deployment locks, one-active-version invariant, and retry-as-new-attempt.
- Coordinate generator, runtime, route, repository, and observability ports.
- Define compensation and recovery behavior for partial failures/restarts.
- Require readiness before activation and preserve prior route on activation failure.

## Required tests

All valid/invalid transitions, duplicate idempotency key/fingerprint, concurrent activation, build/start/readiness failure, retry history, route failure rollback, restart reconciliation, stop/delete retention guard.

## Acceptance / handoff

Lifecycle behavior matches docs 03/04/12 with fake ports and integration evidence. Every terminal failure is diagnosable and no command can create duplicate runtime work for one operation.

