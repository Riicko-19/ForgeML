# Low Level Design

Logical interface names below are normative behavioral contracts; language-specific signatures may vary only when behavior and error mapping remain equivalent.

## Domain records

| Record | Required fields | Invariants |
| --- | --- | --- |
| Package | ID, SHA-256, filename, byte size, manifest version, validation state, artifact URI, created time | Checksum/artifact immutable; only accepted package deploys. |
| PackageValidation | package ID, validator version, findings, analyzed contract, completed time | Findings ordered with code/path/message. |
| Deployment | ID, unique name, active version ID nullable, desired state, timestamps | Zero or one active version; normalized unique retained name. |
| DeploymentVersion | ID, deployment ID, package ID, attempt, state, image ID/tag, container ID, target, policy, error | State follows lifecycle; attempt monotonic. |
| Operation | ID, idempotency key, type, target ID, state, timestamps, correlation ID, error | Same key/type/target has one result; terminal immutable. |
| RuntimeObservation | version ID, observed state, health, restart count, CPU, memory, sampled time | Does not overwrite lifecycle history. |
| AuditEvent | ID, actor type, action, target, correlation ID, timestamp, redacted metadata | Append-only; no payloads/secrets. |

Use opaque UUIDs and UTC ISO-8601 timestamps. Human names are never primary keys. Manifest model.version is metadata, not a deployment-version key.

## Ports

| Port | Operations | Behavioral constraint |
| --- | --- | --- |
| ArtifactStore | put stream, open checksum, delete eligible artifact | Atomic checksum-verified writes; no caller paths. |
| PackageCatalog | create/find, save validation, get manifest/contract | Immutable package view; duplicate checksum idempotent. |
| PackageValidator | inspect archive, validate manifest/files/dependencies | Never imports package code; returns safe findings. |
| PackageAnalyzer | derive inference contract | Validated manifest only; no Docker/storage dependency. |
| RuntimeArtifactGenerator | generate build context | Deterministic for checksum + generator version + runtime. |
| RuntimeManager | build/start/stop/inspect/logs/usage/reconcile | Labels/idempotency; provider-neutral results/errors. |
| DeploymentRepository | lock/find/save deployment/version/operation | Transactional activation lock. |
| UnitOfWork | begin/commit/rollback | Metadata only; never held over Docker work. |
| RouteManager | point/remove/resolve route | Atomic target change or prior target remains. |
| ObservabilityService | record/query logs, observations, audit | Redaction/retention/size limits. |

## .forge contract

A .forge file is a ZIP archive with UTF-8 paths. It contains one root-level forge.yaml, a src/ tree, and declared model assets. Required manifest fields: forge_version (1), model.name, model.framework, model.version, runtime.python, entrypoint.module, entrypoint.callable, input.schema, output.schema. Optional: dependencies, assets, resources, metadata. Runtime health is platform-generated in format version 1; packages cannot override it.

Input/output schema use the supported JSON Schema draft in docs 12. The callable receives one validated input document and returns one output document matching output.schema. Format version 1 accepts only the python-callable framework and Python 3.11; unsupported framework/runtime is a validation error, never a best-effort build.

Validation rejects absolute or traversal paths, symlinks, duplicate normalized paths, non-UTF-8 names, encrypted members, missing/extra manifest roots, unlisted executable entrypoints, size-limit violations, checksum mismatches, and unsupported versions. It extracts only to a fresh staging directory after archive checks, then removes staging after build/failure.

## Lifecycle rules

| From | Command/event | To | Preconditions |
| --- | --- | --- | --- |
| DRAFT | validation begins | VALIDATING | artifact persisted |
| VALIDATING | succeeds/fails | VALIDATED / REJECTED | result persisted |
| VALIDATED | deploy | BUILDING | accepted package and idempotency lock |
| BUILDING | build succeeds/fails | STARTING / FAILED | image ref persisted on success |
| STARTING | readiness succeeds/fails | READY / FAILED | container ID persisted |
| READY | activate | ACTIVE | current health and route update success |
| ACTIVE | replacement activation | READY | candidate atomically active |
| READY/ACTIVE | stop | STOPPED | route removed first if active |
| FAILED | retry | new BUILDING | new immutable attempt |

Invalid transitions return 409 invalid_state_transition. Docker observations cannot themselves promote a version to READY or ACTIVE.

## Concurrency and idempotency

Mutating requests require Idempotency-Key, unique by operation type/target for configurable 24 hours. Same key and fingerprint returns original operation; same key with changed fingerprint returns 409 idempotency_conflict. For package upload, the target becomes the computed archive SHA-256 after streaming; the request fingerprint includes that checksum and declared upload metadata. Activation acquires deployment lock and rechecks candidate health/current active state. Database transactions never span Docker build/start/stop.

## Error taxonomy

| Class | Examples | Behavior |
| --- | --- | --- |
| Validation | malformed archive, framework/schema failure | 422 with stable findings |
| Conflict | duplicate name, bad transition, key mismatch | 409 |
| Not found | unknown package/deployment/version | 404 |
| Capacity/configuration | Docker unavailable, invalid policy | 503 or 422, no trace |
| Build/runtime | install failure, crash, readiness timeout | Operation FAILED + retained diagnosis |
| Prediction | bad input; model execution failure | 422; opaque 502 prediction_runtime_failed with request ID |

## Acceptance criteria

- Validation executes no user module or model deserialization.
- State mutations have correlation/audit record in their metadata transaction.
- Docker types are isolated to the Docker adapter.
- Tests can drive lifecycle using fake implementations of all external ports.
