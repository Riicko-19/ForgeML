# Engineering Principles

These are the durable principles ForgeML is engineered by. They are stable across
modules and intended to remain true for years. They describe *how we build*, never
how any single module is implemented.

## 1. The repository is the source of truth

If knowledge matters, it is committed. Design, decisions, and history live in version
control, not in conversation or memory. A fact that exists only in a chat log does not
exist.

## 2. Contracts freeze before dependents are built

Shared contracts are stabilized and frozen before any downstream module depends on
them. A module names the frozen upstream contract it relies on. A frozen contract is
changed only by a recorded, versioned decision — never silently.

## 3. Immutability by default

Packages, images, and audit records are immutable and content-addressed where
identity matters. A package is identified by the SHA-256 of its bytes; a build
artifact's identity includes its inputs. Duplicate work is idempotent. History is
preserved to support diagnosis and rollback.

## 4. Desired state is durable; observed state is reconciled

Durable metadata records intent. External systems (Docker) hold observed state.
Reconciliation records and heals mismatches through documented actions only. External
state is never treated as a database, and recovery never guesses.

## 5. Depend on ports, not providers

Domain and application code depends on ports (interfaces) owned by the consumer, not
on provider implementations. Storage, database, and runtime are adapters behind ports.
A port is pinned by a conformance suite that runs against both the real adapter and its
in-memory fake, so the fake cannot drift from the contract.

## 6. Side effects are explicit and bounded

Every external interaction has a timeout, a classified failure, a correlation ID, and
idempotency or cleanup as appropriate. Long-running work becomes a durable operation
with a terminal state and restart-safe recovery. No database transaction spans provider
work (an artifact read, a build, a network call).

## 7. Deterministic domain policy

Domain policy is pure and deterministic: immutable value objects, explicit lifecycle
transition methods, no hidden I/O. Time, IDs, checksums, and configuration are injected
so behavior is testable. Analyzer and generator logic that performs no I/O is a pure
function, not a port.

## 8. Errors are typed and mapped once

Failures are typed domain errors, mapped to a transport representation exactly once at
the boundary. Internal detail — container IDs, host paths, stack traces, credentials,
raw provider errors — is never exposed publicly. A platform fault and a user-visible
verdict are never confused for each other.

## 9. Trust boundary is explicit

A package is a trusted administrative artifact, not input from an anonymous user.
Runtime isolation is defense-in-depth, not a safe sandbox for untrusted code. Anonymous
upload and multi-tenant execution are prohibited. Validate at the transport boundary and
revalidate critical invariants in the domain.

## 10. Observability is bounded and redacted

Structured events carry timestamp, severity, component, operation/correlation IDs, and
redacted context. Metric labels are low-cardinality; package names, inputs, and error
text are never labels. Logs and every unbounded collection are paginated and size-bounded
under a retention policy.

## 11. No placeholders, no silent fallbacks

Unimplemented behavior is absent and documented as absent, never stubbed to look present.
A fallback that hides a failure is prohibited. Degradation is a stable, explicit error —
never a guessed success.

## 12. Evidence over assertion

"Done" means proven. A module is complete when its tests pass in CI, its failure paths
and telemetry are verified, and its evidence is recorded. A passing review is not a
substitute for a passing gate, and a recorded exception is never described as a passing
run.

---

These principles are elaborated with concrete rules in
[`05_engineering_standards.md`](05_engineering_standards.md) and derive from the FEK
standards and the ADR register. Where a principle needs a mechanism, the ADR that
supplies it is named in engineering memory
([`../engineering_memory/key_decisions.md`](../engineering_memory/key_decisions.md)).
