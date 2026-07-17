# Module 5 — Deployment (engineering note)

Owner: Lead ForgeML Engineer. Subordinate to docs 02/03/04/06/10/11/12 and the
ADR register. Roadmap scope (docs 06 phase 5): *lifecycle, worker,
reconciliation*; exit gate: *transition/failure/retry/recovery tests with a fake
runtime*.

## What this module delivers

- **Deployment domain** (`domain/deployment/`): `Deployment`,
  `DeploymentVersion`, `VersionState`, `DesiredState`, `ResourcePolicy`, and the
  pure transition rules (`mark_built/ready/failed/stopped`). Functions, not
  Protocols, following `validate_package` — deterministic policy with no I/O.
- **Ports**: `RuntimeManager` (provider-neutral build/start/stop/inspect/
  reconcile) and `DeploymentRepository`. The real Docker adapter is Module 6.
- **Persistence**: `deployments` and `deployment_versions` tables (additive,
  reversible migration), mappers, repository, unit-of-work wiring, and the
  deployment `OperationType`s.
- **Lifecycle service** (`application/deployment/services.py`): drives an
  accepted package through BUILDING → STARTING → READY against the runtime, with
  failure, retry-as-new-attempt, stop, and reconciliation. Intent is persisted
  before every side effect and no database transaction spans runtime work
  (docs 04).
- **HTTP surface**: deployment and version routes plus `/admin/reconcile`
  (docs 12), contract-tested against the fake runtime.

## Frozen semantics for Module 7

`VersionState` includes `ACTIVE`, and the transition table permits READY ↔
ACTIVE, so the routing module's entry gate (*ready/active semantics frozen*) is
satisfied. Module 5 never drives a version into ACTIVE: activation, the route,
rollback, and retention are Module 7. `Deployment.active_version_id` is a
nullable column with no foreign key yet for the same reason.

## Two deliberate, non-blocking deferrals

1. **Execution is inline**, exactly as package validation is (Module 3, D-1).
   The durable, idempotent operation makes moving execution behind a background
   **worker daemon** a later change with no HTTP-contract impact — the operation
   would carry its inputs and be claimed by `claim_next`. That daemon is the one
   piece of "worker" not yet built.
2. **The router is not mounted in the live application.** It needs a real
   `RuntimeManager`; wiring it in with the Docker adapter is the first Module 6
   task. Until then it is exercised in-process against the fake runtime.

## Resource policy

The deploy request accepts an optional `resource_policy`; it is validated
against the docs-12 maxima and persisted on the immutable version. Enforcing
server *minima/defaults* at deploy time is a small additive config follow-up,
not yet wired (no bounding configuration exists today).
