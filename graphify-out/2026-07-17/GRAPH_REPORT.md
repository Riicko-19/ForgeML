# Graph Report - ForgeML  (2026-07-17)

## Corpus Check
- 159 files · ~72,058 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1822 nodes · 3368 edges · 138 communities (113 shown, 25 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 551 edges (avg confidence: 0.72)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a21c7385`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AppSettings
- error_handlers.py
- test_request_logging.py
- ConfigurationFailure
- JsonEventFormatter
- AppError
- test_application_boot.py
- _run_handler
- session_factory
- test_dependency_direction.py
- _reject_wildcard_host
- _EnvironmentSettings
- test_process_signals.py
- __init__.py
- __init__.py
- __init__.py
- installed_package_smoke.py
- forgeml
- Architecture Decision Records
- AuditEvent
- Module 0 Completion Report
- Module 1 — Forge Package System Design
- Module 0 Architecture Clarification Report
- ForgeML Backend — Module 0 Foundation, Module 1 Forge Package System
- Operations and Security
- Project Charter
- Product Requirements
- UnitOfWork
- SqlAlchemyOperationStore
- High Level Design
- Low Level Design
- Implementation Roadmap
- Engineering Standards
- External Contracts
- System Architecture
- Repository Architecture
- Coding Guidelines
- Phase 1 Engineering Operating Contract
- Module 0 Scope Verification Report
- Module 0 Test Report
- Module 0 Engineering Blocker Report
- ForgeML Engineering Kit — Phase 0
- backend-engineer
- chief-architect
- database-engineer
- deployment-engineer
- documentation-engineer
- frontend-engineer
- monitoring-engineer
- package-engineer
- qa-engineer
- runtime-engineer
- test_application_boot.py
- test_openapi_contract.py
- __init__.py
- __init__.py
- __init__.py
- __init__.py
- __init__.py
- CLAUDE.md
- __init__.py
- OperationStore
- _NoAliasLoader
- create_application
- config.py
- Operation
- SqlAlchemyPackageCatalog
- AppSettings
- OperationType
- SqlAlchemyUnitOfWork
- PackageCatalog
- main
- ArchiveReader
- test_invariants.py
- _run_handler
- ArtifactStore
- test_package_limits.py
- _database_url
- event
- models.py
- _reject_wildcard_host
- _EnvironmentSettings
- PackagePage
- 0d7adf1f94cf_module_2_metadata_layer.py
- configure_logging
- __init__.py
- __init__.py
- __init__.py
- ConfigurationIssue
- ValidationError
- Path
- MonkeyPatch
- test_artifact_store.py
- OperationService
- create_health_router
- errors.py
- PackageValidationService
- VanishingArtifactStore
- __init__.py
- Module 3 — Review Guide
- services.py
- .inspect
- packages.py
- PackageValidation
- test_health.py
- validated
- PackageResource
- create_health_router
- create_operation_router
- Finding
- .__enter__
- .rollback
- .__exit__
- test_engine.py
- unit_of_work.py
- Session
- .__enter__
- Package
- event
- forge_pack.py
- repositories.py
- ArtifactStore
- create_package_router
- create_health_router
- Container
- .request
- .__exit__
- APIRouter
- BaseModel
- UnitOfWorkFactory
- Any
- Response

## God Nodes (most connected - your core abstractions)
1. `AppError` - 71 edges
2. `UnitOfWork` - 59 edges
3. `AppSettings` - 59 edges
4. `ErrorDetail` - 44 edges
5. `DeploymentService` - 43 edges
6. `PackageLimits` - 40 edges
7. `ASGITestClient` - 36 edges
8. `build_forge()` - 34 edges
9. `AuditEvent` - 32 edges
10. `InMemoryUnitOfWork` - 32 edges

## Surprising Connections (you probably didn't know these)
- `test_limits_are_immutable()` --calls--> `PackageLimits`  [INFERRED]
  backend/tests/unit/core/test_package_limits.py → backend/src/forgeml/core/config.py
- `test_limits_that_contradict_each_other_are_rejected()` --calls--> `PackageLimits`  [INFERRED]
  backend/tests/unit/core/test_package_limits.py → backend/src/forgeml/core/config.py
- `test_details_must_be_typed()` --calls--> `AppError`  [INFERRED]
  backend/tests/unit/core/test_errors.py → backend/src/forgeml/core/errors.py
- `_zip_bomb()` --calls--> `build_forge()`  [INFERRED]
  backend/tests/contract/test_package_fixtures.py → backend/tests/packages.py
- `create_deployment_router()` --indirect_call--> `DeploymentListResponse`  [INFERRED]
  backend/src/forgeml/api/v1/deployments.py → backend/src/forgeml/api/v1/schemas.py

## Import Cycles
- None detected.

## Communities (138 total, 25 thin omitted)

### Community 0 - "AppSettings"
Cohesion: 0.18
Nodes (10): ArchiveUnreadable, Exception, The bytes are not a readable ZIP container at all., Any, BinaryIO, ZipInfo, ZIP adapter for .forge archives.  This is the only module that knows a .forge fi, _to_entry() (+2 more)

### Community 1 - "error_handlers.py"
Cohesion: 0.14
Nodes (23): The lifecycle of one immutable deployment version/attempt (docs 03/04).      BUI, VersionState, can_transition(), _guard(), mark_built(), mark_failed(), mark_ready(), mark_stopped() (+15 more)

### Community 2 - "test_request_logging.py"
Cohesion: 0.07
Nodes (37): ASGIApp, Server-owned request correlation and bounded request logging., Own the canonical request ID for one HTTP request., RequestContextMiddleware, _correlation_id(), UUID, Package routes (docs 12)., The client-supplied name, reduced to something safe to store and echo.      A fi (+29 more)

### Community 3 - "ConfigurationFailure"
Cohesion: 0.17
Nodes (21): ConfigurationFailure, Exception, Resolve and validate the installed ForgeML distribution version., Fail-closed configuration error safe to classify at bootstrap., resolve_service_version(), MonkeyPatch, Configuration contract tests., test_explicit_mapping_is_not_supplemented_by_process_environment() (+13 more)

### Community 4 - "JsonEventFormatter"
Cohesion: 0.22
Nodes (15): JsonEventFormatter, Render a strict allowlisted JSON event., BaseException, LogRecord, TracebackType, Structured logging policy tests., _record(), test_event_and_fields_are_bounded() (+7 more)

### Community 5 - "AppError"
Cohesion: 0.21
Nodes (22): ManifestV1, forge.yaml for format version 1., asset_checksum_findings(), _asset_findings(), _dependency_findings(), _detail(), _entry_findings(), _entrypoint_findings() (+14 more)

### Community 6 - "test_application_boot.py"
Cohesion: 0.05
Nodes (35): Configuration, Dependency locks and package smoke, Forge package contract, ForgeML Backend — Module 0 Foundation, Module 1 Forge Package System, Frozen HTTP and correlation contracts, HTTP API (v1), Known limitations, Logging contract (+27 more)

### Community 7 - "_run_handler"
Cohesion: 0.16
Nodes (29): body(), client(), Any, MonkeyPatch, Path, Response, The package and operation HTTP surface, end to end.  A real application, a real, test_a_malformed_identifier_is_a_validation_error() (+21 more)

### Community 8 - "session_factory"
Cohesion: 0.05
Nodes (56): create_database_engine(), create_session_factory(), Engine, Session, sessionmaker, Engine and session factory for the metadata database (ADR-009)., Build the metadata engine from typed settings.      `pool_pre_ping` costs one ro, Session factory for the unit of work.      `expire_on_commit=False` is deliberat (+48 more)

### Community 9 - "test_dependency_direction.py"
Cohesion: 0.30
Nodes (13): _imports(), Path, AST-enforced dependency direction., The ORM is confined to one package.      If SQLAlchemy can be imported anywhere, Docs 02: the API adapter may depend on application use cases, and must     not r, test_api_adapts_application_and_never_reaches_a_provider(), test_application_depends_on_domain_not_providers(), test_bootstrap_imports_core_not_api() (+5 more)

### Community 10 - "_reject_wildcard_host"
Cohesion: 0.08
Nodes (24): 10. Design review record, 1. Purpose and scope, 2. Architecture, 3. Folder structure and complete file plan, 4. Technology and dependency decisions, 5. Interfaces, 6. Public HTTP API, 7. Testing and traceability (+16 more)

### Community 11 - "_EnvironmentSettings"
Cohesion: 0.09
Nodes (11): ErrorCategory, StrEnum, Transport-neutral classes of expected application failure., _NoAliasLoader, Safe YAML loader that also refuses aliases.      yaml.safe_load still expands al, _Clock, InMemoryDeploymentRepository, datetime (+3 more)

### Community 12 - "test_process_signals.py"
Cohesion: 0.09
Nodes (39): analyze(), _normalized_schema(), Any, Derive the normalized inference contract from a validated manifest.  Module 4's, Return the schema with the supported dialect made explicit.      Validation acce, Derive the inference contract from a validated manifest. Pure., _adapter(), _dockerfile() (+31 more)

### Community 18 - "Architecture Decision Records"
Cohesion: 0.11
Nodes (17): ADR-001 — Trusted packages; defense-in-depth runtime isolation, ADR-002 — Modular monolith control plane, ADR-003 — Immutable content-addressed packages/images, ADR-004 — Metadata desired state; Docker reconciliation, ADR-005 — One active version and platform route, ADR-006 — Asynchronous durable operations, ADR-007 — Storage/database behind ports, ADR-008 — Initial runtime compatibility matrix (+9 more)

### Community 19 - "AuditEvent"
Cohesion: 0.10
Nodes (21): UnitOfWorkFactory, PackageValidationService, Validate a stored .forge artifact against the format version 1 contract., Runs archive validation over a stored artifact.      Asset checksums are the onl, PackageLimits, Operator policy bounding work spent on an untrusted .forge archive.      Every b, ArchiveReader, ArtifactStore (+13 more)

### Community 20 - "Module 0 Completion Report"
Cohesion: 0.14
Nodes (13): Acceptance checklist, Documentation, External HTTP, Files added, Interfaces, Known limitations, Module 0 Completion Report, Operator/process (+5 more)

### Community 21 - "Module 1 — Forge Package System Design"
Cohesion: 0.14
Nodes (13): Acceptance checklist, Artifact identity and storage, Dependencies added, Freeze status, Known limitations, Layering, Module 1 — Forge Package System Design, Resource bounds (+5 more)

### Community 22 - "Module 0 Architecture Clarification Report"
Cohesion: 0.15
Nodes (12): 1. Reason for stopping, 2. Approval decisions, 3. Design corrections that do not require architecture approval, 4. Dependency approval inventory, 5. Review iteration accounting, 6. Approval request, AC-001 — Control-plane Python support, AC-002 — V1 CI provider and ownership (+4 more)

### Community 23 - "ForgeML Backend — Module 0 Foundation, Module 1 Forge Package System"
Cohesion: 0.29
Nodes (20): Any, _accept_package(), _body(), _create_deployment(), _post(), UUID, HTTP contract for the deployment routes (docs 12).  The deployment router is not, test_a_duplicate_name_is_a_conflict() (+12 more)

### Community 24 - "Operations and Security"
Cohesion: 0.18
Nodes (10): Acceptance criteria, Backup/restore, Configuration inventory, Default limits and operator policy, Monitoring/retention, Operations and Security, Package/build safety, Reconciliation/incidents (+2 more)

### Community 25 - "Project Charter"
Cohesion: 0.20
Nodes (9): Acceptance criteria, Assumptions and constraints, Goals, Non-goals and boundaries, Problem statement, Project Charter, Stakeholders, Success measures (+1 more)

### Community 26 - "Product Requirements"
Cohesion: 0.20
Nodes (9): Deploy journey, Edge cases, Failure and recovery, Functional requirements, Non-functional requirements, Out-of-scope check, Personas and access, Primary outcome (+1 more)

### Community 27 - "UnitOfWork"
Cohesion: 0.07
Nodes (55): Protocol, The transaction boundary owned by the application layer.  A use case opens one u, One atomic metadata transaction.      Leaving the context without committing rol, Begin the transaction., Commit the transaction., Roll back the transaction., UnitOfWork, AppError (+47 more)

### Community 28 - "SqlAlchemyOperationStore"
Cohesion: 0.06
Nodes (62): AppError, AuditEvent, _deploy_fingerprint(), DeploymentService, _latest_contract(), _mismatch_reason(), Deployment, DeploymentVersion (+54 more)

### Community 29 - "High Level Design"
Cohesion: 0.22
Nodes (8): Acceptance criteria, Component responsibilities, Deployment lifecycle, Extension points, Failure/compensation, Happy-path sequence, High Level Design, Routing

### Community 30 - "Low Level Design"
Cohesion: 0.09
Nodes (20): Acceptance criteria, Concurrency and idempotency, Domain records, Error taxonomy, .forge contract, Lifecycle rules, Low Level Design, Ports (+12 more)

### Community 31 - "Implementation Roadmap"
Cohesion: 0.22
Nodes (8): Acceptance criteria, Deferred milestones, Definition of done, Delivery rule, Implementation Roadmap, Phases and gates, Reference test matrix, Required order

### Community 32 - "Engineering Standards"
Cohesion: 0.22
Nodes (8): Acceptance criteria, API/data standards, Core standards, Design rules, Engineering Standards, Observability/security, Reliability standards, Testing/review

### Community 33 - "External Contracts"
Cohesion: 0.22
Nodes (8): Acceptance criteria, Common response rules, Compatibility, Control-plane endpoints, External Contracts, Package manifest summary, Prediction, Resources

### Community 34 - "System Architecture"
Cohesion: 0.25
Nodes (7): Architectural style, Architecture acceptance criteria, Boundaries, Data/control flow, Decisions, Modules and ownership, System Architecture

### Community 35 - "Repository Architecture"
Cohesion: 0.25
Nodes (7): Acceptance criteria, Configuration, secrets, tests, Dependency direction, Module anatomy, Ownership and allowed coupling, Repository Architecture, Repository layout

### Community 36 - "Coding Guidelines"
Cohesion: 0.25
Nodes (7): Acceptance criteria, Coding Guidelines, Forbidden patterns, Naming, errors, quality, Python, Technology baseline, TypeScript/frontend

### Community 37 - "Phase 1 Engineering Operating Contract"
Cohesion: 0.25
Nodes (7): Collaboration rules, Exit acceptance, Handoff template, Objective, Phase 1 Engineering Operating Contract, Phase 1 scope, Required workflow

### Community 38 - "Module 0 Scope Verification Report"
Cohesion: 0.25
Nodes (7): Compliance confirmation, Deferred improvements, Module 0 Scope Verification Report, Unnecessary abstractions and dependencies, V1 requirements implemented, V2 detection matrix, V2 features detected and removed

### Community 39 - "Module 0 Test Report"
Cohesion: 0.25
Nodes (7): Automated suite, Dependency and build evidence, Failed runs and corrections, GitHub Actions, Module 0 Test Report, Real process evidence, Static quality

### Community 40 - "Module 0 Engineering Blocker Report"
Cohesion: 0.25
Nodes (7): Completed evidence, Module 0 Engineering Blocker Report, Resolution, Resolution options recorded at the time of block, Root cause, Three-iteration review history, Unblock procedure

### Community 41 - "ForgeML Engineering Kit — Phase 0"
Cohesion: 0.29
Nodes (6): Document control, ForgeML Engineering Kit — Phase 0, How to use this kit, Phase-0 completion, Review and change control, Scope at a glance

### Community 42 - "backend-engineer"
Cohesion: 0.29
Nodes (6): Acceptance / handoff, backend-engineer, Mission, Owned areas, Required tests, Responsibilities

### Community 43 - "chief-architect"
Cohesion: 0.29
Nodes (6): Acceptance / handoff, chief-architect, Mission, Owned areas, Required review inputs, Responsibilities

### Community 44 - "database-engineer"
Cohesion: 0.29
Nodes (6): Acceptance / handoff, database-engineer, Mission, Owned areas, Required tests, Responsibilities

### Community 45 - "deployment-engineer"
Cohesion: 0.29
Nodes (6): Acceptance / handoff, deployment-engineer, Mission, Owned areas, Required tests, Responsibilities

### Community 46 - "documentation-engineer"
Cohesion: 0.29
Nodes (6): Acceptance / handoff, documentation-engineer, Mission, Owned areas, Required checks, Responsibilities

### Community 47 - "frontend-engineer"
Cohesion: 0.29
Nodes (6): Acceptance / handoff, frontend-engineer, Mission, Owned areas, Required tests, Responsibilities

### Community 48 - "monitoring-engineer"
Cohesion: 0.29
Nodes (6): Acceptance / handoff, Mission, monitoring-engineer, Owned areas, Required tests, Responsibilities

### Community 49 - "package-engineer"
Cohesion: 0.29
Nodes (6): Acceptance / handoff, Mission, Owned areas, package-engineer, Required tests, Responsibilities

### Community 50 - "qa-engineer"
Cohesion: 0.29
Nodes (6): Acceptance / handoff, Mission, Owned areas, qa-engineer, Required release evidence, Responsibilities

### Community 51 - "runtime-engineer"
Cohesion: 0.29
Nodes (6): Acceptance / handoff, Mission, Owned areas, Required tests, Responsibilities, runtime-engineer

### Community 52 - "test_application_boot.py"
Cohesion: 0.20
Nodes (14): FakeServer, BaseException, LogCaptureFixture, MonkeyPatch, Bootstrap and composition integration tests., test_configuration_failure_is_safe_and_exits_two(), test_logging_conflict_exits_one(), test_module_entrypoint_returns_bootstrap_exit_code() (+6 more)

### Community 53 - "test_openapi_contract.py"
Cohesion: 0.11
Nodes (19): CreateDeploymentRequest, CreateVersionRequest, decode_cursor(), DeploymentListResponse, DeploymentResource, encode_cursor(), PackageSummary, Deployment (+11 more)

### Community 62 - "OperationStore"
Cohesion: 0.29
Nodes (5): Protocol, Stop and remove a container. Stopping an absent one is not an error., Enumerate ForgeML-labelled runtime resources and their status., Provider-neutral runtime primitives (docs 04). Labels/idempotency.      Raises R, RuntimeManager

### Community 63 - "_NoAliasLoader"
Cohesion: 0.14
Nodes (13): Amendment after freeze (Module 3), CI evidence, Database schema, Engineering decisions, Files created, Files modified, Known limitations, Migrations (+5 more)

### Community 64 - "create_application"
Cohesion: 0.16
Nodes (7): BaseException, Session, sessionmaker, TracebackType, The SQLAlchemy unit of work: one session, one transaction, three repositories., One atomic metadata transaction.      All three repositories are built from the, SqlAlchemyUnitOfWork

### Community 65 - "config.py"
Cohesion: 0.09
Nodes (19): ActorType, AuditEvent, StrEnum, Audit events (docs 04: append-only; no payloads, no secrets)., Who caused a state change., One append-only record of a state change.      Metadata is bounded and redacted, _safe_text(), AuditLog (+11 more)

### Community 66 - "Operation"
Cohesion: 0.14
Nodes (17): AssetSpec, EntrypointSection, is_supported_schema_dialect(), ModelSection, BaseModel, Immutable .forge format model for package format version 1.  The manifest models, Display identity of the packaged model. Not a deployment key., Runtime the package requires; the ADR-008 matrix pins this to 3.11. (+9 more)

### Community 67 - "SqlAlchemyPackageCatalog"
Cohesion: 0.20
Nodes (10): _bounded(), configure_logging(), LoggingConfigurationConflict, LogRecord, Bounded structured process logging., Configure process logging once for an immutable settings fingerprint., Raised when process logging is reconfigured incompatibly., _strip_controls() (+2 more)

### Community 68 - "AppSettings"
Cohesion: 0.25
Nodes (7): PackageRow, _decode_cursor(), _encode_cursor(), datetime, PostgreSQL implementations of the package, operation, and audit ports.  Concurre, Package records backed by PostgreSQL., SqlAlchemyPackageCatalog

### Community 69 - "OperationType"
Cohesion: 0.18
Nodes (12): Resolved runtime resource bounds for a version (docs 12).      Requested in the, ResourcePolicy, BuiltImage, Start a container for a built image and wait for readiness., A built runtime image, addressed provider-neutrally., A started container and the internal endpoint it serves on., Build the image for a version.          The generated context supplies the Docke, RunningContainer (+4 more)

### Community 70 - "SqlAlchemyUnitOfWork"
Cohesion: 0.11
Nodes (12): DeploymentRepository, UUID, Durable deployment and version records with a transactional lock., Read one deployment by id., Read one deployment by its immutable name., Lock a deployment for update (the activation lock, docs 04).          Frozen her, Persist changes to a deployment (desired state, active version)., Persist a new immutable version attempt. (+4 more)

### Community 71 - "PackageCatalog"
Cohesion: 0.19
Nodes (12): ErrorDetail, Provider-neutral application error contracts., A bounded, safe detail for an expected application error., _validate_code(), _validate_message(), Application error invariant tests., test_detail_count_is_bounded(), test_details_must_be_typed() (+4 more)

### Community 72 - "main"
Cohesion: 0.21
Nodes (10): main(), Exception, _raise_shutdown_requested(), Fail-closed ForgeML process bootstrap., Translate Uvicorn's re-raised SIGTERM into a clean process exit., Validate configuration and run the single ForgeML ASGI worker., _safe_bootstrap_failure(), _ShutdownRequested (+2 more)

### Community 73 - "ArchiveReader"
Cohesion: 0.14
Nodes (11): OperationStore, Any, Protocol, UUID, The durable operation store (ADR-006, ADR-010, ADR-016)., Durable operations, claimed by one worker at a time.      This store is the queu, Create the operation, or return the original one for a repeated request., Claim one named operation, or None if it is not pending.          An inline exec (+3 more)

### Community 74 - "test_invariants.py"
Cohesion: 0.35
Nodes (11): _insert_package(), Engine, Invariants the database enforces, independently of our repositories.  These test, test_a_package_artifact_cannot_be_repointed(), test_a_package_cannot_have_zero_size(), test_a_package_checksum_cannot_be_rewritten(), test_a_package_state_may_still_advance(), test_a_terminal_operation_cannot_be_rewritten() (+3 more)

### Community 75 - "_run_handler"
Cohesion: 0.18
Nodes (10): §1 — The highest-risk code (25 min), §2 — The tests that decide whether you can trust the above (20 min), §3 — Skim only (15 min), §4 — Questions you should answer (15 min), §5 — Implementation risks, `infrastructure/database/repositories.py` — read in full (15 min), `infrastructure/database/unit_of_work.py` — read in full (5 min), `migrations/versions/0d7adf1f94cf_*.py` — read the trigger DDL only (5 min) (+2 more)

### Community 76 - "ArtifactStore"
Cohesion: 0.12
Nodes (32): app_error_handler(), _detail_response(), error_response(), http_error_handler(), internal_error_response(), Exception, FastAPI, JSONResponse (+24 more)

### Community 77 - "test_package_limits.py"
Cohesion: 0.22
Nodes (10): load_settings(), Load settings from an explicit mapping or the process environment., installed_version(), MonkeyPatch, Package limits are operator policy loaded through the fail-closed loader., test_an_invalid_limit_fails_closed(), test_defaults_bound_every_dimension_of_an_untrusted_archive(), test_limits_are_immutable() (+2 more)

### Community 78 - "_database_url"
Cohesion: 0.27
Nodes (15): ArchiveEntry, ArchiveInspection, Header-level facts about one archive member.      Populated from the ZIP central, What an archive reader can learn without executing or importing anything., codes(), entry(), Validation policy over header-level facts, with no archive present., test_entry_limit_short_circuits_before_any_other_rule() (+7 more)

### Community 79 - "event"
Cohesion: 0.10
Nodes (15): ConfigurationIssue, Environment, _EnvironmentSettings, LogLevel, BaseModel, StrEnum, ValidationError, Typed, fail-closed Module 0 configuration. (+7 more)

### Community 80 - "models.py"
Cohesion: 0.32
Nodes (7): _database_url(), Alembic environment.  The database URL comes from the same typed, fail-closed co, The URL supplied by the caller, else the application's own configuration.      T, Emit SQL without a connection, so an operator can review DDL first., Run migrations against a live database., run_migrations_offline(), run_migrations_online()

### Community 81 - "_reject_wildcard_host"
Cohesion: 0.22
Nodes (14): contract_from_json(), contract_to_json(), failure_to_json(), finding_from_json(), finding_to_json(), manifest_to_json(), Any, Translation between ORM rows and immutable domain records.  This is the membrane (+6 more)

### Community 82 - "_EnvironmentSettings"
Cohesion: 0.15
Nodes (9): PackageCatalog, UUID, Durable package records. Duplicate checksums resolve to one package., Return the package for these bytes, creating it in DRAFT if absent.          Sto, Read one package by its opaque identifier., Read one package by the SHA-256 of its bytes., Persist a validation result and transition the package accordingly.          Rai, List packages newest first, bounded by limit. (+1 more)

### Community 83 - "PackagePage"
Cohesion: 0.22
Nodes (8): D-1 — Orphaned operations: startup reconciliation, not a lease, D-2 — Concurrency is delegated to PostgreSQL, never to application checks, D-3 — Unit of Work in the application layer, not `core`, D-4 — Database-enforced immutability, not repository discipline alone, D-5 — Findings persist as an ordered JSONB array, D-6 — `manifest_version` is null until validation, D-7 — The fakes are held to the real adapters' contract, Module 2 — Engineering Decisions

### Community 85 - "configure_logging"
Cohesion: 0.06
Nodes (26): DatabaseProvider, Engine, Exception, Session, sessionmaker, Lazy database lifecycle: engine, unit of work factory, and readiness.  The compo, Owns the engine and hands out units of work., Return operations abandoned by a previous process to the queue.          ADR-016 (+18 more)

### Community 89 - "ConfigurationIssue"
Cohesion: 0.17
Nodes (11): Common mistakes, Database, Module 2 — Handoff, Module 3 entry gate — satisfied, Public contracts, Repositories, The one idea, Transaction boundaries (+3 more)

### Community 90 - "ValidationError"
Cohesion: 0.20
Nodes (9): Acceptance criteria — status, Correlation, Error mapping, Idempotency (docs 04), Layering, Module 3 — Backend API Design, Readiness, Scope (+1 more)

### Community 91 - "Path"
Cohesion: 0.20
Nodes (9): D-1 — Validation runs inline; the operation resource stays, D-2 — A rejected package succeeds its operation, D-3 — `OperationStore.claim(operation_id)` (frozen-module amendment), D-4 — The pagination cursor is opaque and URL-safe, D-5 — Multipart upload, and a synchronous handler, D-6 — 422 is declared explicitly on every route, D-7 — The published schema, but no interactive docs, D-8 — Readiness now checks the database; startup fails closed (+1 more)

### Community 92 - "MonkeyPatch"
Cohesion: 0.25
Nodes (7): Exception, Ports the deployment module drives (docs 04).  `RuntimeManager` is the provider-, Docker itself is unreachable. Retriable; the API maps this to 503., A build or start genuinely failed. Terminal for the attempt.      Carries a safe, RuntimeExecutionError, RuntimeUnavailable, test_docker_unavailable_is_retriable()

### Community 93 - "test_artifact_store.py"
Cohesion: 0.31
Nodes (6): DeploymentVersion, One immutable build/run attempt of an accepted package (docs 04).      `attempt`, to_version(), DeploymentVersionRow, Deployment and version records backed by PostgreSQL., SqlAlchemyDeploymentRepository

### Community 94 - "OperationService"
Cohesion: 0.33
Nodes (5): _reject_wildcard_host(), Shared Module 0 test fixtures., settings(), IPv4Address, IPv6Address

### Community 95 - "create_health_router"
Cohesion: 0.21
Nodes (7): OperationRow, _not_found(), Any, UUID, Durable operations, claimed with row locking (ADR-010, ADR-016)., Reclaim work abandoned by a dead worker (ADR-016).          ADR-010 supervises e, SqlAlchemyOperationStore

### Community 96 - "errors.py"
Cohesion: 0.17
Nodes (14): APIRouter, ASGITestClient, _correlation_id(), create_admin_router(), create_deployment_router(), UUID, Deployment routes (docs 12).  The lifecycle-bearing endpoints -- create a versio, Operator reconciliation route (docs 12). (+6 more)

### Community 97 - "PackageValidationService"
Cohesion: 0.22
Nodes (8): CI evidence, Engineering decisions, Files created, Files modified, Known limitations, Module 3 — Backend API Implementation, Public interfaces, Technical debt

### Community 98 - "VanishingArtifactStore"
Cohesion: 0.22
Nodes (9): Finding, PackageState, StrEnum, Persisted package lifecycle (docs 04).      ValidationState is the validator's v, Stable machine codes reported by package validation.      These codes are part o, Terminal outcome of validating one archive., ValidationState, to_package() (+1 more)

### Community 102 - "Module 3 — Review Guide"
Cohesion: 0.22
Nodes (8): §1 — The file that matters (20 min), §2 — The contract tests (15 min), §3 — Skim (10 min), §4 — Questions you should answer, §5 — Risks, `application/package/services.py` — read in full, If you have 10 minutes, Module 3 — Review Guide

### Community 103 - "services.py"
Cohesion: 0.23
Nodes (13): _await_boot(), _await_operation(), _free_port(), Any, Path, The ForgeML golden path, end to end, against a real server.  Every other HTTP te, Poll one operation until it reaches a terminal state (ADR-006)., Run `python -m forgeml` on a free port and yield its base URL.      This repeats (+5 more)

### Community 104 - ".inspect"
Cohesion: 0.18
Nodes (10): Deployment, DesiredState, StrEnum, Immutable deployment records and lifecycle states (docs 03/04).  A deployment is, What the operator wants a deployment to be doing.      Desired state is the oper, A named deployment. The name is immutable and DNS-label shaped (docs 12)., Create a named deployment. A duplicate name raises CONFLICT (docs 12)., to_deployment() (+2 more)

### Community 105 - "packages.py"
Cohesion: 0.20
Nodes (27): Reads .forge archive structure from a seekable binary stream., ZipArchiveReader, test_an_unreadable_artifact_fails_the_operation(), Path, ZIP reader against real archives, including safe extraction., reader(), stream(), test_a_directory_named_forge_yaml_is_not_a_manifest() (+19 more)

### Community 106 - "PackageValidation"
Cohesion: 0.39
Nodes (6): event(), Domain records for the metadata layer., test_a_well_formed_audit_event_is_accepted(), test_audit_metadata_is_bounded(), test_unsafe_audit_metadata_is_refused(), test_unsafe_audit_text_is_refused()

### Community 107 - "test_health.py"
Cohesion: 0.20
Nodes (9): Before you import, Common failures, Files, ForgeML — Postman, Import, Run order, Things that will confuse you once, Trying a rejection (+1 more)

### Community 108 - "validated"
Cohesion: 0.13
Nodes (13): Operation, OperationState, OperationType, StrEnum, Durable operation records (ADR-006).  An operation is the durable intent behind, The kinds of durable work the control plane performs.      Package validation an, Operation lifecycle. SUCCEEDED and FAILED are terminal and immutable., One durable unit of asynchronous work. (+5 more)

### Community 109 - "PackageResource"
Cohesion: 0.17
Nodes (9): OperationFailureResponse, DeploymentVersion, Operation, ResourcePolicy, A safe classified failure. Never a trace or a host path., Requested runtime resources, bounded by server policy at deploy time., A deployment version as clients see it (docs 12)., ResourcePolicyModel (+1 more)

### Community 110 - "create_health_router"
Cohesion: 0.18
Nodes (16): _deep_schema(), _encrypted_member(), _non_utf8_name(), Any, Path, The .forge reference fixture matrix.  Each case drives a real archive through th, test_findings_carry_a_stable_path(), test_minimal_valid_package_is_accepted() (+8 more)

### Community 111 - "create_operation_router"
Cohesion: 0.11
Nodes (29): create_application(), Create the control-plane application with its dependencies wired., AppSettings, Immutable settings consumed by composition and bootstrap., Frozen HTTP wire contract tests., test_framework_error_wire_shape_omits_empty_details(), test_health_wire_shapes_and_header(), test_unavailable_readiness_uses_the_frozen_error_envelope() (+21 more)

### Community 112 - "Finding"
Cohesion: 0.21
Nodes (7): AuditEventRow, Base, PackageValidationRow, SQLAlchemy mappings. The only ORM classes in ForgeML.  Nothing here leaves this, Append-only audit trail enlisted in the caller's transaction., SqlAlchemyAuditLog, DeclarativeBase

### Community 113 - ".__enter__"
Cohesion: 0.50
Nodes (3): predict(), The entrypoint of the example package.  ForgeML never imports or executes this f, Receive one document matching input.schema, return one matching output.schema.

### Community 115 - ".__exit__"
Cohesion: 0.22
Nodes (11): Exception, JSONResponse, Direct error-mapping branch tests., _run_handler(), test_mismatched_registered_handler_inputs_fail_safe(), test_non_json_validation_error_without_location_is_safe(), test_terminal_error_handlers_are_generic(), test_unapproved_http_status_fails_safe() (+3 more)

### Community 116 - "test_engine.py"
Cohesion: 0.22
Nodes (10): is_accepted(), Only an accepted package may be deployed (docs 04)., PackageValidation, The result of validating one archive. Findings are ordered and stable., Reject bytes that are not a readable archive container at all., Reject an otherwise valid package because a content check failed., rejected_with(), unreadable_archive() (+2 more)

### Community 117 - "unit_of_work.py"
Cohesion: 0.08
Nodes (26): create_operation_router(), APIRouter, Operation polling route (ADR-006)., Create the operation routes bound to the operation use cases., OperationService, UnitOfWorkFactory, UUID, Reading durable operations (ADR-006: clients poll an operation resource). (+18 more)

### Community 118 - "Session"
Cohesion: 0.18
Nodes (12): _fingerprint(), _latest(), PackageDetail, PackageService, BinaryIO, UUID, Package upload, validation, and read use cases.  Validation runs inside the requ, Claim the operation, validate, and record the verdict atomically. (+4 more)

### Community 120 - ".__enter__"
Cohesion: 0.40
Nodes (3): DeploymentPage, One page of deployments, newest first., List deployments newest first, bounded by limit.

### Community 121 - "Package"
Cohesion: 0.23
Nodes (9): manifest(), Any, Builders for .forge archive fixtures.  Fixtures are constructed in memory rather, A valid manifest with top-level sections replaced., The manifest model is the closed shape of forge.yaml., test_control_characters_are_rejected_in_package_authored_text(), test_metadata_may_not_be_unbounded(), test_schema_is_read_from_the_declared_field_name_only() (+1 more)

### Community 123 - "forge_pack.py"
Cohesion: 0.70
Nodes (4): main(), _members(), pack(), Path

### Community 124 - "repositories.py"
Cohesion: 0.27
Nodes (5): Package, A stored package. Checksum and artifact are immutable (ADR-003).      manifest_v, PackagePage, One page of packages, newest first., InMemoryPackageCatalog

### Community 125 - "ArtifactStore"
Cohesion: 0.20
Nodes (5): ManagedRuntime, Observe one container's current state and health., What an inspection can observe about one container (docs 11).      An observatio, A ForgeML-labelled runtime resource seen during reconciliation (ADR-004)., RuntimeStatus

### Community 126 - "create_package_router"
Cohesion: 0.22
Nodes (8): create_package_router(), APIRouter, Create the package routes bound to the package use cases., PackageListResponse, PackageResource, One page of packages, newest first., A package as clients see it (docs 12)., PackageDetail

### Community 127 - "create_health_router"
Cohesion: 0.33
Nodes (5): create_health_router(), APIRouter, Operational health routes., Create health routes bound to immutable service identity.      Liveness answers, ReadinessCheck

### Community 128 - "Container"
Cohesion: 0.40
Nodes (4): Container, FastAPI, FastAPI application composition root., The dependency graph, wired once and shared by the routes.

### Community 132 - ".__exit__"
Cohesion: 0.50
Nodes (3): BaseException, TracebackType, Commit on a clean exit that called commit; otherwise roll back.

## Knowledge Gaps
- **339 isolated node(s):** `forgeml`, `graphify`, `Mission`, `Owned areas`, `Responsibilities` (+334 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AppError` connect `UnitOfWork` to `AppSettings`, `error_handlers.py`, `test_request_logging.py`, `session_factory`, `_EnvironmentSettings`, `SqlAlchemyOperationStore`, `config.py`, `AppSettings`, `PackageCatalog`, `ArtifactStore`, `configure_logging`, `test_artifact_store.py`, `create_health_router`, `.inspect`, `packages.py`, `validated`, `create_operation_router`, `Finding`, `unit_of_work.py`, `Session`, `repositories.py`?**
  _High betweenness centrality (0.162) - this node is a cross-community bridge._
- **Why does `AppSettings` connect `create_operation_router` to `Container`, `SqlAlchemyPackageCatalog`, `JsonEventFormatter`, `ConfigurationFailure`, `session_factory`, `test_package_limits.py`, `event`, `.__exit__`, `test_application_boot.py`, `unit_of_work.py`, `configure_logging`, `OperationService`, `create_health_router`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `DeploymentService` connect `SqlAlchemyOperationStore` to `errors.py`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 60 inferred relationships involving `AppError` (e.g. with `app_error_handler()` and `register_error_handlers()`) actually correct?**
  _`AppError` has 60 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `UnitOfWork` (e.g. with `OperationService` and `PackageDetail`) actually correct?**
  _`UnitOfWork` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `AppSettings` (e.g. with `Container` and `JsonEventFormatter`) actually correct?**
  _`AppSettings` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `ErrorDetail` (e.g. with `.__post_init__()` and `ArchiveEntry`) actually correct?**
  _`ErrorDetail` has 25 INFERRED edges - model-reasoned connections that need verification._