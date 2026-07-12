# External Contracts

Base path is /v1. JSON is UTF-8. Times are UTC ISO-8601 strings; IDs are opaque UUID strings. Undocumented fields are not stable.

## Common response rules

Reads return resource documents. Long-running commands return 202 with Operation and Location to /v1/operations/{operation_id}. Mutations require Idempotency-Key. Lists use limit 1–100 (default 50) and opaque cursor.

Error envelope fields: code (stable machine code), message (safe summary), request_id, optional details (structured findings). Standard mapping: 400 malformed, 404 absent, 409 state/idempotency conflict, 422 validation, 429 policy limit if configured, 500 unexpected platform error, 502 prediction upstream failure, 503 unavailable dependency/runtime.

The server generates the canonical UUIDv4 request_id for each request and returns it
in X-Request-ID. Inbound X-Request-ID headers are ignored and are never reflected or
logged.

Package input.schema and output.schema use JSON Schema Draft 2020-12. External references are prohibited; references may use only local JSON Pointer targets within the same schema document. The platform validates the full Draft 2020-12 vocabulary implemented by its pinned validator, including local refs and $defs. Schema validation has a configurable depth/node limit and fails package validation when that limit is exceeded.

## Resources

| Resource | Key fields |
| --- | --- |
| Package | id, sha256, size_bytes, manifest, validation_state, validation_findings, created_at |
| Deployment | id, name, active_version_id nullable, desired_state, timestamps |
| Version | id, deployment_id, package_id, attempt, state, endpoint nullable, resource_policy, failure nullable |
| Operation | id, type, target, state, correlation_id, result/failure nullable, timestamps |
| Observation | version_id, health, restart_count, cpu_percent, memory_bytes, sampled_at |

## Control-plane endpoints

| Method/path | Purpose | Success |
| --- | --- | --- |
| POST /packages | Stream .forge upload and begin validation | 202 Operation; its result references Package |
| GET /packages; GET /packages/{id} | List/read package | 200 |
| POST /deployments | Create named deployment | 201 |
| GET /deployments; GET /deployments/{id} | List/read deployment | 200 |
| POST /deployments/{id}/versions | Create build/deploy attempt | 202 operation |
| GET /deployments/{id}/versions/{version_id} | Read version | 200 |
| POST /deployments/{id}/versions/{version_id}/activate | Activate ready version | 202 operation |
| POST /deployments/{id}/versions/{version_id}/stop | Stop version | 202 operation |
| DELETE /deployments/{id}/versions/{version_id} | Delete eligible inactive version | 202 operation or 204 |
| GET /deployments/{id}/versions/{version_id}/logs | Redacted paginated logs | 200 |
| GET /deployments/{id}/versions/{version_id}/observations | Health/resource samples | 200 |
| GET /operations/{id} | Poll operation | 200 |
| POST /admin/reconcile | Operator reconciliation | 202 operation |
| GET /healthz; GET /readyz | Liveness/readiness | 200 or 503 |

Version creation requires package_id and optional resource_policy. The policy fields are cpu_millicores (integer), memory_mib (integer), and pids_limit (integer); omitted values use the server policy default and all supplied values must be within server minima/maxima.

Deployment name is a lower-case DNS-label-like identifier matching [a-z][a-z0-9-]{0,62}; it is immutable after creation. Model name is a 1–128-character display string without control characters. The platform rejects unknown request fields for mutation endpoints in API version 1.

## Prediction

POST /v1/deployments/{name}/predict accepts exactly one JSON document matching active input.schema. Success returns one JSON document matching output.schema with 200. Invalid input: 422 prediction_input_invalid. No active healthy runtime: 503 deployment_unavailable. Model crash/invalid output: 502 prediction_runtime_failed with request_id; detail stays in protected logs.

Content-Type is application/json. Binary, streaming, multipart, batch, and async inference are out of scope. Configurable request/response limits are enforced before proxying.

## Package manifest summary

| Field | Type/constraint |
| --- | --- |
| forge_version | Integer 1 |
| model.name | Non-empty normalized display name |
| model.framework | Allowed compatibility-matrix value |
| model.version | Non-empty model-authored string |
| runtime.python | Allowed matrix value/range |
| entrypoint.module | Dotted module path under src |
| entrypoint.callable | Identifier exported by module |
| input.schema/output.schema | Supported JSON Schema document |
| dependencies | Optional list of exact name==version PEP 508 pins; no URL, VCS, local, editable, or ranged requirement |
| assets | Optional relative paths/checksums in archive |
| resources | Optional CPU/memory request within maxima |
| metadata | Optional bounded non-secret labels |

Manifest/schema contain no secrets. Unknown fields at every manifest level are rejected in format version 1. Runtime health is platform-generated and not package-configurable.

## Compatibility

Additive response fields/new optional manifest fields are compatible. Removing/renaming fields, changing type/meaning, lifecycle/error code, or prediction schema semantics needs new API/package major version or explicit negotiation. A created version is immutable; correction means new checksum/version.

## Acceptance criteria

- OpenAPI/JSON Schema and package fixtures validate from one reviewed source of truth.
- Every error code/lifecycle path has contract test.
- Consumer invokes prediction without Docker/container/image knowledge.
- Authorization-boundary behavior is documented before public exposure.
