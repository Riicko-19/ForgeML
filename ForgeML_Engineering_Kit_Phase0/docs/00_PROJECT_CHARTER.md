# Project Charter

**Status:** Approved for Phase 1 planning  
**Product owner:** ForgeML maintainer  
**Architecture owner:** Chief Architect  
**Delivery scope:** Single-server MVP

## Vision and mission

ForgeML makes a packaged machine-learning inference workload deployable as a predictable, observable HTTP API without requiring its operator to author Docker or FastAPI plumbing. Its mission is a clean, modular self-hosted deployment path for trusted models on one server.

## Problem statement

Model authors commonly have serialized models and ad-hoc inference code but no repeatable way to package dependencies, validate inputs, build a runtime, expose an endpoint, and diagnose a deployment. ForgeML standardizes that path; it does not manage the model-development lifecycle.

## Goals

1. Define a deterministic .forge package format and validation process.
2. Build an immutable image from a valid package and deploy it as an isolated local Docker container.
3. Expose a platform-managed prediction route, health, logs, status, and basic resource metrics for each deployed version.
4. Preserve package, build, deployment, and version history to support diagnosis and rollback.
5. Keep domain modules replaceable through explicit ports and dependency injection.

## Non-goals and boundaries

The MVP excludes Kubernetes, distributed execution, multi-host scheduling, autoscaling, multi-tenancy, user/team management, billing, a marketplace, MLflow, DVC, training pipelines, experiments, GPU scheduling, canary traffic splitting, and arbitrary public package execution. Authentication beyond a deployment-level administrative boundary is deferred.

ForgeML supports inference only. A package is a trusted administrative artifact, not a file accepted from untrusted internet users.

## Success measures

| Measure | MVP target | Measurement |
| --- | --- | --- |
| Happy-path deployment | Endpoint ready within 5 minutes for reference CPU package | Upload acceptance to readiness |
| Deployment reliability | ≥95% valid reference deployments require no manual repair | Release test runs |
| Contract correctness | 100% documented contract tests pass | CI |
| Failure diagnosis | Every failure has terminal reason, correlation ID, and bounded logs | Integration tests |
| Isolation baseline | Every runtime has limits and no Docker socket/host mounts | Runtime inspection |

Inference latency is model-owned and reported by the platform, not guaranteed by it.

## Assumptions and constraints

- One Linux host runs the control plane and Docker Engine.
- The operator is authorized to upload and execute packages and administer Docker.
- Initial runtimes are CPU-only. Dependency fetching is permitted only at build time from configured sources.
- Persistent local storage exists for metadata, artifacts, and retained logs.
- Availability is best-effort single-host operation; no HA claim is made.

## Stakeholders

| Stakeholder | Accountable outcome |
| --- | --- |
| Operator | Supplies trusted packages, configures host/reverse proxy, deploys and rolls back |
| Model author | Publishes conforming package and owns inference/schema semantics |
| Platform maintainer | Owns contracts, releases, security fixes, and backups |
| API consumer | Sends contract-valid requests to an operator-exposed endpoint |

## Acceptance criteria

- Scope, non-goals, trust model, and success measures are explicit and approved.
- Package, HTTP, lifecycle, persistence, and runtime-boundary contracts enable independent implementation without private assumptions.
- Each delivery phase has entry/exit criteria and a responsible role.
- Deferred concerns are enumerated instead of implied.

