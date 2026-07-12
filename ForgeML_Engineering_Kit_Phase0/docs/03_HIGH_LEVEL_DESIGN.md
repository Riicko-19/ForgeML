# High Level Design

## Component responsibilities

| Component | Responsibility | Input | Output |
| --- | --- | --- | --- |
| Frontend | Operator workflows; never lifecycle work | REST resources/events | Commands/view models |
| Package Service | Safe archive acceptance/storage/validation | Upload stream | Package record/findings |
| Model Analyzer | Normalized inference contract | Validated manifest | Contract/errors |
| API Generator | Deterministic runtime adapter assets | Contract + runtime version | Generated artifact identity |
| Deployment Engine | Build/start/activate/rollback workflow | Deployment command | Durable attempt |
| Runtime Manager | Docker image/container/network/health primitives | Runtime command | Provider-neutral result |
| Monitoring | Bounded logs, health, resource observations | Runtime identity | Queryable observations |
| Persistence | Transactional metadata/audit history | Domain records | Repositories/UoW |

## Deployment lifecycle

~~~mermaid
stateDiagram-v2
  [*] --> DRAFT
  DRAFT --> VALIDATING: upload accepted
  VALIDATING --> VALIDATED: package valid
  VALIDATING --> REJECTED: validation error
  VALIDATED --> BUILDING: create version
  BUILDING --> STARTING: image build succeeds
  BUILDING --> FAILED: build fails
  STARTING --> READY: readiness succeeds
  STARTING --> FAILED: start/readiness fails
  READY --> ACTIVE: activate
  ACTIVE --> READY: activate replacement
  READY --> STOPPED: stop
  ACTIVE --> STOPPED: deactivate/stop
  STOPPED --> STARTING: restart
  FAILED --> BUILDING: explicit retry; new attempt
~~~

VALIDATING/VALIDATED/REJECTED describe package state; the other states describe an immutable deployment version/attempt. FAILED is terminal for an attempt. Retry always creates a new attempt.

## Happy-path sequence

~~~mermaid
sequenceDiagram
  participant O as Operator
  participant A as Control plane
  participant P as Package/Analyzer
  participant D as Deployment service
  participant R as Docker runtime
  participant M as Metadata store
  O->>A: Upload .forge
  A->>P: Store, inspect, validate
  P->>M: Persist package/result
  A-->>O: Validation operation
  O->>A: Poll operation; package accepted/rejected
  O->>A: Create named deployment/version
  A->>D: Start idempotent operation
  D->>M: Persist BUILDING intent
  D->>R: Generate/build/start
  R-->>D: Healthy runtime identity
  D->>M: Persist READY observation
  O->>A: Activate ready version
  A->>D: Atomically point route
  D->>M: Persist ACTIVE version
~~~

## Routing

For deployment name d, ForgeML exposes /v1/deployments/{d}/predict. The platform resolves the active ready version and forwards to its internal target. Containers never bind host ports. If no version is active/healthy, the route returns 503 with a stable error code. Consumers do not select container addresses. Creating the deployment name and creating a package-backed version are separate commands.

## Failure/compensation

1. Validate before build; rejected packages produce no runtime work.
2. Persist intent before external side effects; persist image/container IDs immediately when known.
3. On build/start failure, collect bounded logs, clean failed container best-effort, retain diagnostic metadata, and mark FAILED.
4. Change route only after candidate is READY; failed routing leaves prior active version unchanged.
5. On restart, reconcile Docker labels/health before accepting a duplicate command.

## Extension points

New package formats, builders, runtimes, stores, databases, and observability sinks are adapter changes behind named ports. New model frameworks are package/runtime-adapter capabilities, not forks of deployment workflow. Extensions retain lifecycle semantics and error codes.

## Acceptance criteria

- A failed operation never receives traffic or is represented as ready.
- Replacement activation never intentionally drops a known-ready active version before candidate health succeeds.
- A route maps to at most one active version.
- Docker resources carry package, deployment, version, and operation labels.
