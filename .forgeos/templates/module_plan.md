# Module Plan — <module number> <module name>

> Template. Copy and fill in. A module plan is the design artifact reviewed at the
> architecture-review gate. Delete these quotes when using it.

**Owner:** <role/name> · **Status:** Draft | In review | Approved · **Date:** <YYYY-MM-DD>

## Scope

The roadmap phase scope this module delivers (FEK doc 06, phase <n>). One paragraph. State
what is in and, briefly, what is explicitly out.

## Frozen upstream contract

The exact upstream contract this module depends on, and the module/ADR that froze it. If any
dependency is not yet frozen, this module cannot begin — say so and stop.

## Domain model

The value objects, states, and transitions introduced. Keep it deterministic; no I/O here.

## Ports introduced

| Port | Owned by | Responsibility | Adapter(s) |
| --- | --- | --- | --- |
| | | | real + fake |

Each port is pinned by the conformance suite against both its real adapter and its fake.

## Side effects

For each external interaction: timeout, classified failure, correlation, idempotency or
cleanup. Confirm no database transaction spans provider work.

## Applicable ADRs

List the ADRs that govern this module and any new decision this design requires (route new
decisions through the [decision process](../constitution/03_decision_process.md)).

## Deferrals

What this module deliberately does not deliver, and why each deferral is non-blocking.
Nothing is stubbed to look present.

## Exit-gate evidence

The specific test evidence the phase's exit gate requires, and how this design produces it.

## Security and resource-boundary impact

Trust-boundary and isolation impact, assessed against the trust model and ADR-001.
