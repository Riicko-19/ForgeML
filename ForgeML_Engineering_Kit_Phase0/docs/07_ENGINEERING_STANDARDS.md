# Engineering Standards

## Core standards

ForgeML applies SOLID and DRY pragmatically: consolidate accidental duplicated mechanics, not independent domain concepts. Use explicit types, narrow interfaces, service/application layers, dependency injection, structured logging, and unit plus integration tests. Placeholders and silent fallbacks are prohibited.

## Design rules

- Prefer immutable value objects and explicit lifecycle transition methods.
- Keep side effects at adapter/application boundaries; domain policy is deterministic.
- Depend on a port owned by its consumer, not a provider implementation.
- Use typed/domain errors and map them once at transport boundary.
- Inject time, IDs, checksums, and configuration where test determinism needs it.
- Make idempotency, retry, timeout, cleanup, and cancellation explicit for external work.
- Version persisted/transmitted schemas and document compatibility.

## API/data standards

- Use the versioned REST namespace and error envelope in docs 12.
- Validate at transport boundary and revalidate critical domain invariants.
- Schema change requires migration plus forward safety and rollback/restore procedure.
- Never expose container IDs, host paths, traces, credentials, or raw provider errors publicly.
- Use UTC, opaque IDs, immutable checksums, and append-only audit records.
- Paginate/bound logs and all unbounded collections.

## Reliability standards

| Concern | Required practice |
| --- | --- |
| External calls | Timeout, classified failure, correlation ID, bounded retry only if idempotent |
| Docker lifecycle | Labels, idempotency token, desired/observed reconciliation, cleanup |
| Async work | Durable operation record/terminal state/restart-safe worker |
| Data write | Transactional metadata; no long transaction over build/network |
| Degradation | Stable unavailable/error; never guessed success |
| Recovery | Reconciliation plus documented operator action |

## Observability/security

Events contain timestamp, severity, component, operation/correlation IDs, deployment/version when available, event name, redacted context. Use low-cardinality metric labels; never use package names, inputs, or error text as labels. Apply retention/size policy.

Follow docs 11 trust model. Validate archive before extraction; run non-root limited network/container; redact secrets; exclude Docker socket. Package/build logs/model errors are potentially sensitive. Pin or otherwise reproduce dependencies/base images under build policy.

## Testing/review

| Level | Must prove |
| --- | --- |
| Unit | Invariants, transitions, validation branches, error mapping |
| Contract | Package/REST/port compatibility |
| Integration | Database/Docker/storage adapters and migrations |
| End-to-end | Reference package to active prediction route and failures |
| Regression | Focused automated bug reproducer |

Review ownership/dependency direction, compatibility, validation, idempotency, error transparency, redaction, cleanup, tests, docs, and migration/operations. A failing gate blocks merge.

## Acceptance criteria

- CI enforces formatting, lint, type, test, and contract gates.
- The V1 CI implementation is .github/workflows/backend-quality.yml, owned by the
  Backend Engineer and reviewed by QA. It runs the repository-defined gates on Linux
  with supported Python 3.11.
- Every side effect has timeout, diagnosis, and appropriate idempotency/cleanup.
- Public changes carry documentation and risk-proportionate tests.
