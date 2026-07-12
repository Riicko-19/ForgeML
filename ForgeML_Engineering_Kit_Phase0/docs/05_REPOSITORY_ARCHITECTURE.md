# Repository Architecture

## Repository layout

~~~text
backend/
  src/forgeml/
    api/                 HTTP adapters and dependency wiring
    application/         Use cases, commands, queries, DTOs
    domain/
      package/
      analyzer/
      api_generator/
      deployment/
      runtime/
      monitoring/
      versioning/
    infrastructure/      Docker, storage, database, routing adapters
    core/                configuration, DI composition, errors, logging
  migrations/
  tests/
    unit/
    integration/
    contract/
    e2e/
frontend/
  app/                   Next.js routes/pages
  features/              deployment/package/observability feature modules
  components/            shared presentation components
  lib/                   typed API client, utilities
docs/
diagrams/
deploy/                  compose, reverse-proxy, systemd/manifests; no app logic
scripts/                 developer/CI operational scripts only
tests/                   cross-service/e2e fixtures if required
uploads/                 ignored transient upload staging
storage/                 ignored local artifact/log/database development volume
.skills/
~~~

## Dependency direction

~~~mermaid
flowchart LR
  API[api] --> APP[application]
  APP --> DOMAIN[domain]
  INFRA[infrastructure] --> DOMAIN
  INFRA --> APP
  COMPOSE[core composition] --> API
  COMPOSE --> APP
  COMPOSE --> INFRA
~~~

Domain imports neither FastAPI, SQLAlchemy, Docker SDK, filesystem APIs, nor frontend concepts. Application imports domain ports/models only. Infrastructure implements ports and may import vendor libraries. API maps transport DTOs to application commands and must not contain lifecycle rules.

## Module anatomy

Each domain module contains, at minimum:

| Directory/concept | Purpose |
| --- | --- |
| models | Immutable value objects, entities, transition policy |
| ports | Interfaces owned by consuming domain/application |
| services | Domain policy not naturally an entity method |
| use_cases | Application command/query handlers for owned workflow |
| adapters | Provider implementation only when local; otherwise infrastructure |
| tests | Unit tests plus contract fixtures |
| docs | Module decisions, compatibility, operational notes |

Avoid a generic utilities or common dumping ground. A cross-cutting abstraction belongs in core only when two independent modules need it and it has no business meaning. Otherwise it stays module-owned.

## Ownership and allowed coupling

| Owner | May change directly | Requires review from |
| --- | --- | --- |
| Package | Format, validation, artifact ports | Deployment/API Generator for contract changes |
| Deployment | Lifecycle/application orchestration | Runtime/Database for port/state changes |
| Runtime | Runtime port and Docker adapter | Deployment for semantic changes |
| Database | Repository adapter, migrations | Domain owner for record/schema changes |
| Frontend | Feature UI and typed-client use | API owner for contract changes |
| Monitoring | Observation adapters/retention | Runtime/Deployment for event semantics |

No module reads another module's tables, filesystem locations, or private classes. Cross-module work uses a published port, application command, or immutable DTO.

## Configuration, secrets, tests

Typed settings at composition root distinguish safe runtime settings, operator policy, and secrets. Secrets are environment/secret supplied, redacted, absent from frontend bundles, and never in manifests. Commit only non-working examples.

Unit tests use fakes and no providers. Integration tests use isolated real adapters. Contract tests validate package fixtures and HTTP schemas. End-to-end tests deploy a safe reference package to disposable Docker resources. Fixtures contain no production model, credential, or personal data.

## Acceptance criteria

- A contributor can locate feature API, use case, domain policy, adapter, and tests.
- Import/lint rules prevent forbidden dependency direction.
- Resource names, paths, and tables are not hard-coded outside adapters/config.
- Ignored storage/upload directories cannot be committed.

