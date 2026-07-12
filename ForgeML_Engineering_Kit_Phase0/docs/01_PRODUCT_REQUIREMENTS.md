# Product Requirements

## Personas and access

ForgeML has one MVP role: **operator**. The operator may be a student, ML engineer, or startup developer, but is equally trusted to submit executable packages and manage deployments. An **API consumer** may invoke an endpoint exposed by the operator's network boundary but cannot use the dashboard or control-plane API. Fine-grained identity and authorization are deferred.

## Primary outcome

As an operator, I upload a valid .forge package and receive a versioned working REST prediction endpoint with inspectable status, logs, and metrics, without writing Docker or FastAPI code.

## Functional requirements

| ID | Requirement | Acceptance criteria |
| --- | --- | --- |
| FR-01 | Upload package | Stream one archive under configured limit, retain it atomically, return a durable validation operation whose result references package ID/checksum. |
| FR-02 | Validate package | Reject malformed, unsafe-path, unsupported, or schema-invalid archives before build; return machine-readable findings. |
| FR-03 | Inspect package | Show immutable manifest, derived input/output contract, checksum, validation result, and package metadata. |
| FR-04 | Create deployment | Create a named deployment, then create a version from a validated package and resource policy within configured limits. |
| FR-05 | Build runtime | Create immutable image tagged by package checksum and build version; record logs; never report ready before health passes. |
| FR-06 | Route prediction | Provide stable route that forwards to exactly one active, ready runtime version. |
| FR-07 | Observe runtime | Return lifecycle state, recent logs, health, restart count, and sampled CPU/memory. |
| FR-08 | Manage versions | List history; activate ready prior version; stop versions; delete only inactive versions subject to retention. |
| FR-09 | Recover control plane | On restart reconcile metadata and Docker without silently creating duplicate containers. |

## Deploy journey

1. The model author produces a conforming .forge archive.
2. The operator uploads it; ForgeML stores and validates it.
3. The operator creates a named deployment and a version from the accepted package.
4. ForgeML generates a runtime adapter, builds an image, starts a constrained container, checks readiness, and records its endpoint.
5. The operator activates the ready version and invokes the stable prediction route.

## Failure and recovery

Validation failure creates no build. Build/start failure ends the deployment attempt in FAILED, retaining classified reason and bounded logs. Retry creates a new attempt; it does not mutate failed history. If an active version becomes unhealthy, the route returns an unavailable response and the operator may activate a ready prior version.

## Non-functional requirements

| ID | Requirement | MVP definition |
| --- | --- | --- |
| NFR-01 | Modularity | Modules depend on abstractions, never another module's tables or provider client. |
| NFR-02 | Testability | All ports have fakes; package, API, and lifecycle contracts have integration tests. |
| NFR-03 | Security | Trusted uploads only; runtimes are non-root, resource-limited, host-isolated, and lack Docker socket access. |
| NFR-04 | Reliability | State transitions are durable/idempotent; retries do not duplicate an image/container for one attempt. |
| NFR-05 | Observability | Operations have correlation IDs, structured events, and redacted logs. |
| NFR-06 | Extensibility | Storage/runtime providers can be added through ports without deployment-rule changes. |
| NFR-07 | Usability | Dashboard shows actionable state, endpoint, and next step without raw Docker knowledge. |

## Edge cases

- Identical archive bytes resolve to the existing package by checksum; a new deployment remains permitted.
- A deployment name is unique while retained. Reuse occurs only after deletion and retention cleanup.
- Requests during activation/deactivation receive deterministic unavailability, never a stopping runtime.
- Logs are bounded and redacted; secrets and prediction payloads are never retained by default.
- Missing Docker containers discovered by reconciliation become visible failed/stopped records, not assumed healthy.
- Input schema violations are client errors; model execution errors are opaque server errors.

## Out-of-scope check

No MVP API, UI, or record implies multi-user ownership, traffic splitting, remote Docker hosts, training, registry integration, GPU allocation, or a claim that arbitrary third-party Python dependencies are safe.
