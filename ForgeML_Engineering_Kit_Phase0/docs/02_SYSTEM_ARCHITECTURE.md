# System Architecture

## Architectural style

ForgeML is a modular-monolith control plane with isolated Docker runtime containers. The control plane is FastAPI with a Next.js dashboard. API/UI adapters call application use cases; use cases depend only on domain models and ports; infrastructure implements ports. This is intentionally not a microservice system: one deployable control plane suits the MVP while ports preserve future extraction options.

~~~mermaid
flowchart TD
  O[Trusted Operator] --> UI[Next.js dashboard]
  O --> API[Control-plane REST API]
  C[API Consumer] --> RP[Platform route proxy]
  UI --> API
  API --> APP[Application use cases]
  APP --> PKG[Package port]
  APP --> REP[Metadata repository port]
  APP --> RUN[Runtime port]
  APP --> OBS[Observability port]
  PKG --> ART[(Artifact storage)]
  REP --> DB[(Metadata database)]
  RUN --> DKR[Local Docker Engine]
  DKR --> RT[Isolated model runtime]
  OBS --> DB
  OBS --> DKR
  RP --> RT
~~~

## Boundaries

| Boundary | Responsibility | May depend on | Must not depend on |
| --- | --- | --- | --- |
| Dashboard | Operator workflow/presentation | Control-plane API contracts | Database, Docker, artifact storage |
| API adapter | HTTP parsing, auth-boundary integration, response mapping | Application use cases | Docker SDK, ORM in handlers |
| Application | Orchestration, lifecycle rules, transactions | Domain models/ports | FastAPI, Next.js, Docker types |
| Domain modules | Package, deployment, runtime, versioning policy | Declared ports/models | Another module's tables/repositories |
| Infrastructure | Storage, database, Docker, log/metric adapters | Ports/vendor clients | UI/business decisions |
| Model runtime | Inference adapter/model dependencies | Package assets/generated adapter | Docker socket, host mounts, control-plane DB |

## Modules and ownership

| Module | Owns | Public port |
| --- | --- | --- |
| Package | Ingestion, extraction safety, manifest validation, artifact identity | PackageCatalog, ArtifactStore |
| Analyzer | Manifest semantics and derived inference contract | PackageAnalyzer |
| API Generator | Deterministic adapter/config generation | RuntimeArtifactGenerator |
| Deployment | Build/start/activate/rollback workflow | DeploymentService |
| Runtime | Docker lifecycle, health, routing target details | RuntimeManager |
| Monitoring | Logs, health observations, resource sampling | ObservabilityService |
| Database | Metadata transactions and migrations | Repositories, UnitOfWork |
| Frontend | Views/operator interaction | Typed control-plane client |

## Decisions

- Local Docker Engine is the sole MVP runtime adapter; its port is backend-neutral.
- Package bytes are immutable and content-addressed by SHA-256.
- Database records desired state; Docker is observed/reconciled state.
- A deployment has zero or one active version. Activation is explicit.
- The platform owns the external route; runtimes use an internal network and no host ports.
- Runtime execution is trusted-code execution with defense-in-depth, not a sandbox.

## Data/control flow

Upload and deployment are durable asynchronous operations. HTTP returns an operation resource; the dashboard polls it. The application persists intent before Docker work, applies idempotency, and reconciles after restart. Detailed state/error contracts are normative in docs 04 and 12.

## Architecture acceptance criteria

- No HTTP handler reaches Docker, artifact storage, or database except through application ports/use cases.
- Runtime backends can be faked/replaced without changing deployment business rules.
- Dashboard has no Docker, storage, or database credentials.
- Runtimes cannot access Docker socket, control-plane DB, host artifact directory, or host network.
- Reconciliation preserves one container identity per deployment attempt and reports every mismatch.

