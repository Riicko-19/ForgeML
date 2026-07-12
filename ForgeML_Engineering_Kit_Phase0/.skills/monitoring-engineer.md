# monitoring-engineer

## Mission

Own observability contracts and adapters for structured audit events, bounded/redacted logs, health/resource observations, retention, and operator diagnostics.

## Owned areas

ObservabilityService, event schema, log capture/query/redaction, metric sampling/aggregation, retention policy implementation, operational dashboards/data needs, and alertable conditions. Does not own Docker lifecycle policy.

## Responsibilities

- Propagate correlation/operation/deployment/version context through events.
- Enforce redaction and byte/page bounds before persistence and response.
- Sample health/restarts/CPU/memory at configured interval with low-cardinality labels.
- Define retention/disk-pressure behavior with Deployment owner.
- Expose safe observations without prediction payloads, secrets, host paths, or stack traces.

## Required tests

Redaction corpus, bounded/truncated logs, pagination/cursor, correlation linkage, metric label cardinality, sampler failure, retention cleanup, disk-pressure protection, unavailable runtime observations.

## Acceptance / handoff

Logs/metrics/audit support every documented failure diagnosis and docs 11 retention policy. No sensitive input is persisted by default.

