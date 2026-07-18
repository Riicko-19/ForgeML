# Engineering Standards

Concrete rules that make the principles in [`02_principles.md`](02_principles.md)
enforceable. These summarize and organize the binding standards; the detailed
authority is the FEK
([doc 07 Engineering Standards](../../ForgeML_Engineering_Kit_Phase0/docs/07_ENGINEERING_STANDARDS.md),
[doc 08 Coding Guidelines](../../ForgeML_Engineering_Kit_Phase0/docs/08_CODING_GUIDELINES.md),
[doc 11 Operations and Security](../../ForgeML_Engineering_Kit_Phase0/docs/11_OPERATIONS_AND_SECURITY.md),
[doc 12 External Contracts](../../ForgeML_Engineering_Kit_Phase0/docs/12_EXTERNAL_CONTRACTS.md)).
Where this document and the FEK differ, the FEK wins.

## Design

- Apply SOLID and DRY pragmatically: consolidate accidental duplicated mechanics, not
  independent domain concepts.
- Prefer immutable value objects and explicit lifecycle transition methods.
- Keep side effects at adapter and application boundaries; domain policy is deterministic.
- Depend on a port owned by its consumer, not on a provider implementation.
- Use typed domain errors and map them once at the transport boundary.
- Inject time, IDs, checksums, and configuration wherever test determinism needs it.
- Make idempotency, retry, timeout, cleanup, and cancellation explicit for external work.
- Version every persisted or transmitted schema and document its compatibility.
- No placeholders and no silent fallbacks. Absent behavior is documented as absent.

## API and data

- Use the versioned REST namespace and the single error envelope defined in FEK doc 12.
- Validate at the transport boundary and revalidate critical domain invariants inside.
- A schema change requires a migration plus a forward-safety and rollback/restore
  procedure.
- Never expose container IDs, host paths, traces, credentials, or raw provider errors
  publicly.
- Use UTC, opaque IDs, immutable checksums, and append-only audit records.
- Paginate and bound logs and every unbounded collection.

## Reliability

| Concern | Required practice |
| --- | --- |
| External calls | Timeout, classified failure, correlation ID; bounded retry only if idempotent |
| Docker lifecycle | Labels, idempotency token, desired/observed reconciliation, cleanup |
| Async work | Durable operation record, terminal state, restart-safe worker |
| Data write | Transactional metadata; no long transaction spanning build or network |
| Degradation | Stable unavailable/error; never a guessed success |
| Recovery | Reconciliation plus a documented operator action |

## Observability and security

- Events carry timestamp, severity, component, operation/correlation IDs, deployment and
  version when available, event name, and redacted context.
- Metric labels are low-cardinality. Package names, inputs, and error text are never
  labels.
- Apply the retention and size policy (ADR-012).
- Follow the FEK doc 11 trust model: validate archives before extraction; run non-root
  with limited network and container capabilities; redact secrets; exclude the Docker
  socket. Treat package/build logs and model errors as potentially sensitive.
- Pin or otherwise reproduce dependencies and base images under the build supply-chain
  policy (ADR-011).

## Testing

| Level | Must prove |
| --- | --- |
| Unit | Invariants, transitions, validation branches, error mapping |
| Contract | Package / REST / port compatibility (run against real adapters *and* fakes) |
| Integration | Database, Docker, and storage adapters, and migrations |
| End-to-end | Reference package to an active prediction route, and its failure paths |
| Regression | A focused automated reproducer for each fixed bug |

A port's conformance suite runs against both the real adapter and its in-memory fake. A
new port method is added to that suite in the same change; a fake that drifts from the
contract makes every downstream test built on it a lie.

## Review and CI

- Review ownership and dependency direction, compatibility, validation, idempotency,
  error transparency, redaction, cleanup, tests, docs, and migration/operations.
- A failing gate blocks merge.
- CI enforces formatting, lint, type, test, contract, build, and installed-package smoke
  gates on the supported Python (ADR-013: CPython >=3.11,<3.12).
- The V1 CI implementation is `.github/workflows/backend-quality.yml` (ADR-014). Module
  completion requires passing workflow evidence on the frozen commit. A recorded exception
  is never reported as a passing run.

## Acceptance

- Every side effect has a timeout, a diagnosis path, and appropriate idempotency or
  cleanup.
- Public changes carry documentation and risk-proportionate tests.
- CI enforces the gates above; local-only evidence does not satisfy the freeze gate
  except under the single closed ADR-014 exception.
