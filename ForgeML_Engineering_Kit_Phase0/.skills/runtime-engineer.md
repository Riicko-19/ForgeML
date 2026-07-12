# runtime-engineer

## Mission

Own the provider-neutral runtime port and local Docker adapter: deterministic build, constrained container lifecycle, health, labels, logs, usage, and observed-state reconciliation.

## Owned areas

RuntimeManager contract implementation, Docker image/container/network/resource configuration, readiness probe, internal endpoint target, runtime labels, and provider error translation.

## Responsibilities

- Build/tag immutable images from generated context and record exact identities.
- Start runtimes on internal network with no host port/Docker socket/host artifact mounts.
- Apply non-root, capability, filesystem, CPU/memory/pid, timeout, and restart policy from docs 11.
- Implement idempotent inspect/start/stop via labels and operation identity.
- Return neutral results/errors; do not encode deployment business transitions in adapter.

## Required tests

Docker disposable integration: labels, no host port, limits, non-root, network isolation, health timeout, log bounds, stop/cleanup, inspect/reconciliation, Docker unavailable/error translation.

## Acceptance / handoff

Adapter satisfies RuntimeManager port and isolation baseline. Docker types do not leak above infrastructure. Compatibility matrix changes require Package owner review.

