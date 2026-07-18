# Graph Report - ForgeML  (2026-07-18)

## Corpus Check
- 196 files · ~91,187 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2184 nodes · 4048 edges · 185 communities (162 shown, 23 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 710 edges (avg confidence: 0.71)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6c4b92c6`
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
- unit_of_work.py
- .__enter__
- .commit
- .rollback
- Role — Technical Reviewer
- Review Guide — <module/change>
- Pull Request — <title>
- VanishingArtifactStore
- Engineering Standards
- Module History
- Architecture Diff — <contract/boundary>
- Engineering Report — <subject>
- Release Checklist — <version / milestone>
- Workflow — Architecture Review
- Workflow — Freeze Process
- repositories.py
- Decision Process
- Workflow — Implementation Review
- test_two_simultaneous_uploads_resolve_to_one_package
- ADR-NNN — <short decision title>
- ForgeML
- runtime
- _EnvironmentSettings
- Session
- Architecture Evolution
- analyze
- create_session_factory
- Project Memory
- validated
- OperationService
- test_error_handling.py
- Engineering Governance
- errors.py
- _EnvironmentSettings
- packages.py
- augment_dockerfile
- Architecture Decision Records
- reset_request_id
- test_engine.py
- _building_version
- .request
- decode_cursor
- .__exit__

## God Nodes (most connected - your core abstractions)
1. `AppError` - 89 edges
2. `UnitOfWork` - 61 edges
3. `AppSettings` - 59 edges
4. `PackageLimits` - 53 edges
5. `DeploymentService` - 50 edges
6. `ErrorDetail` - 44 edges
7. `ASGITestClient` - 39 edges
8. `Operation` - 38 edges
9. `ErrorCategory` - 36 edges
10. `AuditEvent` - 36 edges

## Surprising Connections (you probably didn't know these)
- `_require_key()` --calls--> `AppError`  [INFERRED]
  backend/src/forgeml/api/v1/deployments.py → backend/src/forgeml/core/errors.py
- `test_limits_are_immutable()` --calls--> `PackageLimits`  [INFERRED]
  backend/tests/unit/core/test_package_limits.py → backend/src/forgeml/core/config.py
- `test_limits_that_contradict_each_other_are_rejected()` --calls--> `PackageLimits`  [INFERRED]
  backend/tests/unit/core/test_package_limits.py → backend/src/forgeml/core/config.py
- `test_details_must_be_typed()` --calls--> `AppError`  [INFERRED]
  backend/tests/unit/core/test_errors.py → backend/src/forgeml/core/errors.py
- `_zip_bomb()` --calls--> `build_forge()`  [INFERRED]
  backend/tests/contract/test_package_fixtures.py → backend/tests/packages.py

## Import Cycles
- None detected.

## Communities (185 total, 23 thin omitted)

### Community 0 - "AppSettings"
Cohesion: 0.12
Nodes (21): GeneratedBuildContext, A deterministic set of build files plus their content-addressed identity., _ArchiveExtractor, _ArtifactSource, container_name(), DockerCli, image_ref(), _labels_of() (+13 more)

### Community 1 - "error_handlers.py"
Cohesion: 0.13
Nodes (24): StrEnum, The lifecycle of one immutable deployment version/attempt (docs 03/04).      BUI, VersionState, can_transition(), _guard(), mark_built(), mark_failed(), mark_ready() (+16 more)

### Community 2 - "test_request_logging.py"
Cohesion: 0.20
Nodes (23): app_error_handler(), _detail_response(), error_response(), http_error_handler(), internal_error_response(), Exception, FastAPI, JSONResponse (+15 more)

### Community 3 - "ConfigurationFailure"
Cohesion: 0.17
Nodes (21): ConfigurationFailure, Exception, Resolve and validate the installed ForgeML distribution version., Fail-closed configuration error safe to classify at bootstrap., resolve_service_version(), MonkeyPatch, Configuration contract tests., test_explicit_mapping_is_not_supplemented_by_process_environment() (+13 more)

### Community 4 - "JsonEventFormatter"
Cohesion: 0.22
Nodes (15): JsonEventFormatter, Render a strict allowlisted JSON event., BaseException, LogRecord, TracebackType, Structured logging policy tests., _record(), test_event_and_fields_are_bounded() (+7 more)

### Community 5 - "AppError"
Cohesion: 0.21
Nodes (21): ManifestV1, forge.yaml for format version 1., asset_checksum_findings(), _asset_findings(), _dependency_findings(), _detail(), _entry_findings(), _entrypoint_findings() (+13 more)

### Community 6 - "test_application_boot.py"
Cohesion: 0.15
Nodes (13): Configuration, Dependency locks and package smoke, Forge package contract, ForgeML Backend — Module 0 Foundation, Module 1 Forge Package System, Frozen HTTP and correlation contracts, HTTP API (v1), Known limitations, Logging contract (+5 more)

### Community 7 - "_run_handler"
Cohesion: 0.12
Nodes (24): Container, create_application(), FastAPI, FastAPI application composition root., The dependency graph, wired once and shared by the routes., Create the control-plane application with its dependencies wired., AppSettings, Immutable settings consumed by composition and bootstrap. (+16 more)

### Community 8 - "session_factory"
Cohesion: 0.21
Nodes (14): postgres_engine(), Engine, alembic_config(), migrated_engine(), Engine, Migration gates (docs 06 phase 2 exit criteria)., An empty autogenerate diff.      This is the gate that catches a model changed w, Docs 11 requires an operator to be able to review DDL before applying it. (+6 more)

### Community 9 - "test_dependency_direction.py"
Cohesion: 0.30
Nodes (13): _imports(), Path, AST-enforced dependency direction., The ORM is confined to one package.      If SQLAlchemy can be imported anywhere, Docs 02: the API adapter may depend on application use cases, and must     not r, test_api_adapts_application_and_never_reaches_a_provider(), test_application_depends_on_domain_not_providers(), test_bootstrap_imports_core_not_api() (+5 more)

### Community 10 - "_reject_wildcard_host"
Cohesion: 0.08
Nodes (24): 10. Design review record, 1. Purpose and scope, 2. Architecture, 3. Folder structure and complete file plan, 4. Technology and dependency decisions, 5. Interfaces, 6. Public HTTP API, 7. Testing and traceability (+16 more)

### Community 11 - "_EnvironmentSettings"
Cohesion: 0.05
Nodes (24): Package, A stored package. Checksum and artifact are immutable (ADR-003).      manifest_v, PackageCatalog, PackagePage, UUID, Ports owned by the package domain.  Callers never receive a filesystem path. An, One page of packages, newest first., Durable package records. Duplicate checksums resolve to one package. (+16 more)

### Community 12 - "test_process_signals.py"
Cohesion: 0.09
Nodes (41): analyze(), _normalized_schema(), Any, Derive the normalized inference contract from a validated manifest.  Module 4's, Return the schema with the supported dialect made explicit.      Validation acce, Derive the inference contract from a validated manifest. Pure., _adapter(), _dockerfile() (+33 more)

### Community 18 - "Architecture Decision Records"
Cohesion: 0.11
Nodes (18): ADR-001 — Trusted packages; defense-in-depth runtime isolation, ADR-002 — Modular monolith control plane, ADR-003 — Immutable content-addressed packages/images, ADR-004 — Metadata desired state; Docker reconciliation, ADR-005 — One active version and platform route, ADR-006 — Asynchronous durable operations, ADR-007 — Storage/database behind ports, ADR-008 — Initial runtime compatibility matrix (+10 more)

### Community 19 - "AuditEvent"
Cohesion: 0.10
Nodes (20): UnitOfWorkFactory, PackageValidationService, Validate a stored .forge artifact against the format version 1 contract., Runs archive validation over a stored artifact.      Asset checksums are the onl, PackageLimits, Operator policy bounding work spent on an untrusted .forge archive.      Every b, ArchiveReader, ArtifactStore (+12 more)

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
Nodes (20): _accept_package(), _body(), _create_deployment(), _post(), Any, Response, UUID, HTTP contract for the deployment routes (docs 12).  The deployment router is not (+12 more)

### Community 24 - "Operations and Security"
Cohesion: 0.20
Nodes (10): Acceptance criteria, Backup/restore, Configuration inventory, Default limits and operator policy, Monitoring/retention, Operations and Security, Package/build safety, Reconciliation/incidents (+2 more)

### Community 25 - "Project Charter"
Cohesion: 0.20
Nodes (9): Acceptance criteria, Assumptions and constraints, Goals, Non-goals and boundaries, Problem statement, Project Charter, Stakeholders, Success measures (+1 more)

### Community 26 - "Product Requirements"
Cohesion: 0.20
Nodes (9): Deploy journey, Edge cases, Failure and recovery, Functional requirements, Non-functional requirements, Out-of-scope check, Personas and access, Primary outcome (+1 more)

### Community 27 - "UnitOfWork"
Cohesion: 0.06
Nodes (56): BaseException, Protocol, TracebackType, The transaction boundary owned by the application layer.  A use case opens one u, One atomic metadata transaction.      Leaving the context without committing rol, Begin the transaction., Commit on a clean exit that called commit; otherwise roll back., Commit the transaction. (+48 more)

### Community 28 - "SqlAlchemyOperationStore"
Cohesion: 0.12
Nodes (15): _deploy_fingerprint(), _latest_contract(), _mismatch_reason(), UUID, Deployment lifecycle use cases (docs 03/04; Module 5).  The service turns an acc, Build and start a new version of an accepted package., Stop a READY version and remove its container., Compare runtime resources against records and record mismatches. (+7 more)

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
Cohesion: 0.25
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
Cohesion: 0.18
Nodes (16): LoggingConfigurationConflict, Raised when process logging is reconfigured incompatibly., FakeServer, BaseException, LogCaptureFixture, MonkeyPatch, Bootstrap and composition integration tests., test_configuration_failure_is_safe_and_exits_two() (+8 more)

### Community 53 - "test_openapi_contract.py"
Cohesion: 0.11
Nodes (29): ErrorDetailResponse, Safe, bounded validation detail., CreateDeploymentRequest, CreateVersionRequest, DeploymentListResponse, DeploymentResource, encode_cursor(), OperationFailureResponse (+21 more)

### Community 62 - "OperationStore"
Cohesion: 0.15
Nodes (29): Resolved runtime resource bounds for a version (docs 12).      Requested in the, ResourcePolicy, a_context(), err(), FakeStore, inspect_json(), make_manager(), BinaryIO (+21 more)

### Community 63 - "_NoAliasLoader"
Cohesion: 0.14
Nodes (13): Amendment after freeze (Module 3), CI evidence, Database schema, Engineering decisions, Files created, Files modified, Known limitations, Migrations (+5 more)

### Community 64 - "create_application"
Cohesion: 0.16
Nodes (7): BaseException, Session, sessionmaker, TracebackType, The SQLAlchemy unit of work: one session, one transaction, three repositories., One atomic metadata transaction.      All three repositories are built from the, SqlAlchemyUnitOfWork

### Community 65 - "config.py"
Cohesion: 0.22
Nodes (11): Exception, Docker itself is unreachable. Retriable; the API maps this to 503., A build or start genuinely failed. Terminal for the attempt.      Carries a safe, RuntimeExecutionError, RuntimeUnavailable, DockerRuntimeManager, looks_unavailable(), Whether a CLI failure means the daemon is unreachable (retriable). (+3 more)

### Community 66 - "Operation"
Cohesion: 0.14
Nodes (17): AssetSpec, EntrypointSection, is_supported_schema_dialect(), ModelSection, BaseModel, Immutable .forge format model for package format version 1.  The manifest models, Display identity of the packaged model. Not a deployment key., Runtime the package requires; the ADR-008 matrix pins this to 3.11. (+9 more)

### Community 67 - "SqlAlchemyPackageCatalog"
Cohesion: 0.13
Nodes (31): body(), client(), Any, MonkeyPatch, Path, Response, The package and operation HTTP surface, end to end.  A real application, a real, test_a_malformed_identifier_is_a_validation_error() (+23 more)

### Community 68 - "AppSettings"
Cohesion: 0.22
Nodes (7): Base, PackageRow, PackageValidationRow, SQLAlchemy mappings. The only ORM classes in ForgeML.  Nothing here leaves this, Package records backed by PostgreSQL., SqlAlchemyPackageCatalog, DeclarativeBase

### Community 69 - "OperationType"
Cohesion: 0.07
Nodes (22): DeploymentPage, DeploymentRepository, Protocol, UUID, Ports the deployment module drives (docs 04).  `RuntimeManager` is the provider-, Start a container for a built image and wait for readiness., Stop and remove a container. Stopping an absent one is not an error., Observe one container's current state and health. (+14 more)

### Community 70 - "SqlAlchemyUnitOfWork"
Cohesion: 0.14
Nodes (13): ArchiveUnreadable, Exception, The bytes are not a readable ZIP container at all., _NoAliasLoader, Any, BinaryIO, ZipInfo, ZIP adapter for .forge archives.  This is the only module that knows a .forge fi (+5 more)

### Community 71 - "PackageCatalog"
Cohesion: 0.29
Nodes (9): ErrorDetail, A bounded, safe detail for an expected application error., Application error invariant tests., test_detail_count_is_bounded(), test_details_must_be_typed(), test_invalid_codes_are_rejected(), test_invalid_messages_are_rejected(), test_invalid_paths_are_rejected() (+1 more)

### Community 72 - "main"
Cohesion: 0.21
Nodes (10): main(), Exception, _raise_shutdown_requested(), Fail-closed ForgeML process bootstrap., Translate Uvicorn's re-raised SIGTERM into a clean process exit., Validate configuration and run the single ForgeML ASGI worker., _safe_bootstrap_failure(), _ShutdownRequested (+2 more)

### Community 73 - "ArchiveReader"
Cohesion: 0.20
Nodes (29): DeploymentService, Creates deployments and drives version build/start/stop/reconcile., InMemoryUnitOfWork, A unit of work whose rollback really does discard writes.      Repositories writ, env(), _accept_package(), _context(), _deploy() (+21 more)

### Community 74 - "test_invariants.py"
Cohesion: 0.35
Nodes (11): _insert_package(), Engine, Invariants the database enforces, independently of our repositories.  These test, test_a_package_artifact_cannot_be_repointed(), test_a_package_cannot_have_zero_size(), test_a_package_checksum_cannot_be_rewritten(), test_a_package_state_may_still_advance(), test_a_terminal_operation_cannot_be_rewritten() (+3 more)

### Community 75 - "_run_handler"
Cohesion: 0.18
Nodes (10): §1 — The highest-risk code (25 min), §2 — The tests that decide whether you can trust the above (20 min), §3 — Skim only (15 min), §4 — Questions you should answer (15 min), §5 — Implementation risks, `infrastructure/database/repositories.py` — read in full (15 min), `infrastructure/database/unit_of_work.py` — read in full (5 min), `migrations/versions/0d7adf1f94cf_*.py` — read the trigger DDL only (5 min) (+2 more)

### Community 76 - "ArtifactStore"
Cohesion: 0.18
Nodes (16): _deep_schema(), _encrypted_member(), _non_utf8_name(), Any, Path, The .forge reference fixture matrix.  Each case drives a real archive through th, test_findings_carry_a_stable_path(), test_minimal_valid_package_is_accepted() (+8 more)

### Community 77 - "test_package_limits.py"
Cohesion: 0.14
Nodes (16): load_settings(), Load settings from an explicit mapping or the process environment., installed_version(), MonkeyPatch, The engine the control plane actually builds, against a real database.  Every ot, settings(), test_a_non_postgresql_url_fails_closed(), test_the_database_url_is_never_disclosed() (+8 more)

### Community 78 - "_database_url"
Cohesion: 0.27
Nodes (15): ArchiveEntry, ArchiveInspection, Header-level facts about one archive member.      Populated from the ZIP central, What an archive reader can learn without executing or importing anything., codes(), entry(), Validation policy over header-level facts, with no archive present., test_entry_limit_short_circuits_before_any_other_rule() (+7 more)

### Community 79 - "event"
Cohesion: 0.14
Nodes (13): ConfigurationIssue, Environment, LogLevel, StrEnum, ValidationError, Typed, fail-closed Module 0 configuration., The metadata database URL, or a fail-closed configuration error.          Module, Supported deployment environments. (+5 more)

### Community 80 - "models.py"
Cohesion: 0.32
Nodes (7): _database_url(), Alembic environment.  The database URL comes from the same typed, fail-closed co, The URL supplied by the caller, else the application's own configuration.      T, Emit SQL without a connection, so an operator can review DDL first., Run migrations against a live database., run_migrations_offline(), run_migrations_online()

### Community 81 - "_reject_wildcard_host"
Cohesion: 0.20
Nodes (15): contract_from_json(), contract_to_json(), failure_to_json(), finding_from_json(), finding_to_json(), manifest_to_json(), Any, Translation between ORM rows and immutable domain records.  This is the membrane (+7 more)

### Community 82 - "_EnvironmentSettings"
Cohesion: 0.18
Nodes (11): create_health_router(), APIRouter, Operational health routes., Create health routes bound to immutable service identity.      Liveness answers, ErrorEnvelope, HealthResponse, BaseModel, Frozen Module 0 HTTP response schemas. (+3 more)

### Community 83 - "PackagePage"
Cohesion: 0.22
Nodes (8): D-1 — Orphaned operations: startup reconciliation, not a lease, D-2 — Concurrency is delegated to PostgreSQL, never to application checks, D-3 — Unit of Work in the application layer, not `core`, D-4 — Database-enforced immutability, not repository discipline alone, D-5 — Findings persist as an ordered JSONB array, D-6 — `manifest_version` is null until validation, D-7 — The fakes are held to the real adapters' contract, Module 2 — Engineering Decisions

### Community 85 - "configure_logging"
Cohesion: 0.13
Nodes (22): AppError, Exception, An immutable expected application failure., artifact_uri(), FilesystemArtifactStore, BinaryIO, Path, Content-addressed artifact storage on a local filesystem (ADR-007, ADR-009). (+14 more)

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
Cohesion: 0.13
Nodes (12): DatabaseProvider, Engine, Exception, Session, sessionmaker, Lazy database lifecycle: engine, unit of work factory, and readiness.  The compo, Owns the engine and hands out units of work., Return operations abandoned by a previous process to the queue.          ADR-016 (+4 more)

### Community 93 - "test_artifact_store.py"
Cohesion: 0.16
Nodes (11): OperationState, OperationType, StrEnum, Durable operation records (ADR-006).  An operation is the durable intent behind, The kinds of durable work the control plane performs.      Package validation an, Operation lifecycle. SUCCEEDED and FAILED are terminal and immutable., to_operation(), OperationRow (+3 more)

### Community 94 - "OperationService"
Cohesion: 0.33
Nodes (5): _reject_wildcard_host(), Shared Module 0 test fixtures., settings(), IPv4Address, IPv6Address

### Community 95 - "create_health_router"
Cohesion: 0.18
Nodes (13): ASGIApp, Server-owned request correlation and bounded request logging., Own the canonical request ID for one HTTP request., RequestContextMiddleware, Request middleware lifecycle tests., _receive(), _send(), test_cancelled_request_cleans_context() (+5 more)

### Community 96 - "errors.py"
Cohesion: 0.24
Nodes (9): create_admin_router(), create_deployment_router(), APIRouter, Deployment routes (docs 12).  The lifecycle-bearing endpoints -- create a versio, Operator reconciliation route (docs 12)., Create the deployment routes bound to the deployment use cases., _require_key(), OperationResource (+1 more)

### Community 97 - "PackageValidationService"
Cohesion: 0.22
Nodes (8): CI evidence, Engineering decisions, Files created, Files modified, Known limitations, Module 3 — Backend API Implementation, Public interfaces, Technical debt

### Community 98 - "VanishingArtifactStore"
Cohesion: 0.22
Nodes (11): BuiltImage, ManagedRuntime, A built runtime image, addressed provider-neutrally., A ForgeML-labelled runtime resource seen during reconciliation (ADR-004)., The `docker run` argv for a hardened, labelled runtime container (ADR-001)., Operator policy for the Docker runtime.      Defaulted so the runtime is usable, run_args(), RuntimeSettings (+3 more)

### Community 102 - "Module 3 — Review Guide"
Cohesion: 0.22
Nodes (8): §1 — The file that matters (20 min), §2 — The contract tests (15 min), §3 — Skim (10 min), §4 — Questions you should answer, §5 — Risks, `application/package/services.py` — read in full, If you have 10 minutes, Module 3 — Review Guide

### Community 103 - "services.py"
Cohesion: 0.23
Nodes (13): _await_boot(), _await_operation(), _free_port(), Any, Path, The ForgeML golden path, end to end, against a real server.  Every other HTTP te, Poll one operation until it reaches a terminal state (ADR-006)., Run `python -m forgeml` on a free port and yield its base URL.      This repeats (+5 more)

### Community 104 - ".inspect"
Cohesion: 0.13
Nodes (10): Deployment, DesiredState, Immutable deployment records and lifecycle states (docs 03/04).  A deployment is, What the operator wants a deployment to be doing.      Desired state is the oper, A named deployment. The name is immutable and DNS-label shaped (docs 12)., Create a named deployment. A duplicate name raises CONFLICT (docs 12)., Read one deployment by its immutable name., Persist changes to a deployment (desired state, active version). (+2 more)

### Community 105 - "packages.py"
Cohesion: 0.21
Nodes (26): Reads .forge archive structure from a seekable binary stream., ZipArchiveReader, Path, ZIP reader against real archives, including safe extraction., reader(), stream(), test_a_directory_named_forge_yaml_is_not_a_manifest(), test_bytes_that_are_not_a_zip_container_are_unreadable() (+18 more)

### Community 106 - "PackageValidation"
Cohesion: 0.39
Nodes (6): event(), Domain records for the metadata layer., test_a_well_formed_audit_event_is_accepted(), test_audit_metadata_is_bounded(), test_unsafe_audit_metadata_is_refused(), test_unsafe_audit_text_is_refused()

### Community 107 - "test_health.py"
Cohesion: 0.20
Nodes (9): Before you import, Common failures, Files, ForgeML — Postman, Import, Run order, Things that will confuse you once, Trying a rejection (+1 more)

### Community 108 - "validated"
Cohesion: 0.13
Nodes (12): OperationStore, Any, Protocol, UUID, The durable operation store (ADR-006, ADR-010, ADR-016)., Durable operations, claimed by one worker at a time.      This store is the queu, Create the operation, or return the original one for a repeated request., Claim the oldest pending operation, or None.          `types` selects a lane. Wi (+4 more)

### Community 109 - "PackageResource"
Cohesion: 0.15
Nodes (12): OperationFailure, A safe, classified failure. Never a trace, a host path, or a payload., FakeRuntimeManager, A scriptable in-memory RuntimeManager for deployment lifecycle tests.  Module 5, runtime(), The fake RuntimeManager honours the provider-neutral port contract., test_an_unhealthy_container_is_reported_not_raised(), test_build_failure_is_a_terminal_execution_error() (+4 more)

### Community 110 - "create_health_router"
Cohesion: 0.23
Nodes (9): manifest(), Any, Builders for .forge archive fixtures.  Fixtures are constructed in memory rather, A valid manifest with top-level sections replaced., The manifest model is the closed shape of forge.yaml., test_control_characters_are_rejected_in_package_authored_text(), test_metadata_may_not_be_unbounded(), test_schema_is_read_from_the_declared_field_name_only() (+1 more)

### Community 111 - "create_operation_router"
Cohesion: 0.22
Nodes (6): CliResult, The outcome of one Docker CLI invocation., Run `docker <args>`. Raise RuntimeUnavailable if docker is absent,         Timeo, FakeCli, ok(), Handler

### Community 113 - ".__enter__"
Cohesion: 0.50
Nodes (3): predict(), The entrypoint of the example package.  ForgeML never imports or executes this f, Receive one document matching input.schema, return one matching output.schema.

### Community 115 - ".__exit__"
Cohesion: 0.33
Nodes (5): Frozen semantics for Module 7, Module 5 — Deployment (engineering note), Resource policy, Two deliberate, non-blocking deferrals, What this module delivers

### Community 116 - "test_engine.py"
Cohesion: 0.33
Nodes (8): PackageValidation, The result of validating one archive. Findings are ordered and stable., Reject bytes that are not a readable archive container at all., Reject an otherwise valid package because a content check failed., _reject(), rejected_with(), unreadable_archive(), test_unreadable_archive_reports_one_stable_finding()

### Community 117 - "unit_of_work.py"
Cohesion: 0.20
Nodes (10): CI Status, Current Development Stage, Current Module, Current Version, Engineering Authority, ForgeML Project Status, Last Frozen Milestone, Notes (+2 more)

### Community 118 - "Session"
Cohesion: 0.18
Nodes (12): _fingerprint(), is_accepted(), _latest(), PackageService, BinaryIO, UUID, Package upload, validation, and read use cases.  Validation runs inside the requ, Claim the operation, validate, and record the verdict atomically. (+4 more)

### Community 120 - ".__enter__"
Cohesion: 0.22
Nodes (8): Deferred to later modules, Docker assumptions, Module 6 — Docker Runtime (engineering note), Prerequisite correction (ADR-017), Runtime behaviour, Security (ADR-001), The adapter speaks CLI, behind one seam, What this module delivers

### Community 121 - "Package"
Cohesion: 0.21
Nodes (8): _bounded(), configure_logging(), LogRecord, Bounded structured process logging., Configure process logging once for an immutable settings fingerprint., _strip_controls(), MonkeyPatch, test_configure_logging_is_idempotent_and_rejects_conflict()

### Community 122 - "event"
Cohesion: 0.17
Nodes (12): Definition of done, Design, Entry gate, Exit gate, Freeze, Implementation, Module Lifecycle, Review (+4 more)

### Community 123 - "forge_pack.py"
Cohesion: 0.28
Nodes (7): database_url(), migrated(), Shared database setup for the HTTP integration tests., Bring the schema to head once, via the migration the operator would run., _available_loopback_port(), Real-process signal and graceful-shutdown integration., test_sigterm_stops_installed_process_without_traceback()

### Community 124 - "repositories.py"
Cohesion: 0.20
Nodes (10): Applicable ADRs, Deferrals, Domain model, Exit-gate evidence, Frozen upstream contract, Module Plan — <module number> <module name>, Ports introduced, Scope (+2 more)

### Community 125 - "ArtifactStore"
Cohesion: 0.22
Nodes (9): Authority, Inputs, Mission, Must never do, Outputs, Quality expectations, Responsibilities, Role — Release Manager (+1 more)

### Community 126 - "create_package_router"
Cohesion: 0.22
Nodes (9): Finding, PackageState, StrEnum, Persisted package lifecycle (docs 04).      ValidationState is the validator's v, Stable machine codes reported by package validation.      These codes are part o, Terminal outcome of validating one archive., ValidationState, to_package() (+1 more)

### Community 131 - ".request"
Cohesion: 0.33
Nodes (6): Exit criteria, Failure handling, Inputs, Required artifacts, Steps and gates, Workflow — Module Development

### Community 132 - ".__exit__"
Cohesion: 0.50
Nodes (4): Decisions still owed, Key Engineering Decisions, Reserved for future updates, The decisions that shape everything

### Community 133 - "APIRouter"
Cohesion: 0.25
Nodes (7): create_package_router(), APIRouter, Create the package routes bound to the package use cases., PackageResource, A package as clients see it (docs 12)., PackageDetail, A package together with its most recent validation verdict.

### Community 134 - "BaseModel"
Cohesion: 0.22
Nodes (11): Exception, Handler, JSONResponse, Direct error-mapping branch tests., _run_handler(), test_mismatched_registered_handler_inputs_fail_safe(), test_non_json_validation_error_without_location_is_safe(), test_terminal_error_handlers_are_generic() (+3 more)

### Community 135 - "UnitOfWorkFactory"
Cohesion: 0.20
Nodes (9): Authority, Inputs, Mission, Must never do, Outputs, Quality expectations, Responsibilities, Role — Documentation Engineer (+1 more)

### Community 136 - "Any"
Cohesion: 0.20
Nodes (9): Common mistakes, Entry gate for the next module — satisfied?, Handoff — <module number> <module name>, How it fits together, Invariants and how they are enforced, Public contracts, The one idea, What the next module may depend upon (+1 more)

### Community 137 - "Response"
Cohesion: 0.22
Nodes (9): Directory structure, ForgeOS — ForgeML Engineering Operating System, How to use ForgeOS, If you are a new human contributor, If you are an AI system, If you are reviewing or releasing, Mission, Philosophy (+1 more)

### Community 138 - "unit_of_work.py"
Cohesion: 0.22
Nodes (9): Authority, Inputs, Mission, Must never do, Outputs, Quality expectations, Responsibilities, Role — Chief Architect (+1 more)

### Community 139 - ".__enter__"
Cohesion: 0.22
Nodes (9): Authority, Inputs, Mission, Must never do, Outputs, Quality expectations, Responsibilities, Role — Senior Implementation Engineer (+1 more)

### Community 140 - ".commit"
Cohesion: 0.22
Nodes (7): Decision gates, Exit criteria, Failure handling, Inputs, Note on scope, Outputs, Workflow — Release Process

### Community 141 - ".rollback"
Cohesion: 0.22
Nodes (9): Authority, Inputs, Mission, Must never do, Outputs, Quality expectations, Responsibilities, Role — Security Reviewer (+1 more)

### Community 142 - "Role — Technical Reviewer"
Cohesion: 0.22
Nodes (9): Authority, Inputs, Mission, Must never do, Outputs, Quality expectations, Responsibilities, Role — Technical Reviewer (+1 more)

### Community 143 - "Review Guide — <module/change>"
Cohesion: 0.22
Nodes (8): If you have <n> minutes, Questions the reviewer should answer, Read in full (<n> min), Review Guide — <module/change>, Risks, Skim (<n> min), The tests that pin behavior (<n> min), Where the risk is

### Community 144 - "Pull Request — <title>"
Cohesion: 0.22
Nodes (8): Change summary, Checklists, Deferrals, Evidence, Pull Request — <title>, Reviewer, Scope, What and why

### Community 145 - "VanishingArtifactStore"
Cohesion: 0.21
Nodes (8): provider(), BinaryIO, Path, Startup recovery and the platform-failure path.  These are the paths that only r, Stores an archive, then loses it before anything can read it.      A disk failur, test_an_unreadable_artifact_fails_the_operation(), test_startup_recovery_is_harmless_when_nothing_was_abandoned(), VanishingArtifactStore

### Community 146 - "Engineering Standards"
Cohesion: 0.25
Nodes (8): Acceptance, API and data, Design, Engineering Standards, Observability and security, Reliability, Review and CI, Testing

### Community 147 - "Module History"
Cohesion: 0.25
Nodes (8): Module 0 — Foundation · Frozen (2026-07-13), Module 1 — Forge Package System · Frozen (2026-07-14), Module 2 — Metadata Layer · Frozen (2026-07-14), Module 3 — Backend API · Implemented, freeze pending CI, Module 4 — Analyzer / Generator · Implemented, freeze pending CI, Module 5 — Deployment · Implemented, freeze pending CI, Module History, Reserved — Modules 6–10

### Community 148 - "Architecture Diff — <contract/boundary>"
Cohesion: 0.25
Nodes (7): Architecture Diff — <contract/boundary>, Compatibility, Decision record, The contract today, The proposed change, Who depends on it, Why it is safe / why the break is justified

### Community 149 - "Engineering Report — <subject>"
Cohesion: 0.25
Nodes (7): Engineering Report — <subject>, Evidence, How it satisfies the design, Key decisions, Known limitations carried forward, What downstream may depend upon, What was delivered

### Community 150 - "Release Checklist — <version / milestone>"
Cohesion: 0.25
Nodes (8): Data and recovery, Documentation, Frozen inputs, Reference test matrix, Release Checklist — <version / milestone>, Reproducibility, Security and boundaries, Sign-off

### Community 151 - "Workflow — Architecture Review"
Cohesion: 0.25
Nodes (8): Architecture diff, Decision gates, Exit criteria, Failure handling, Inputs, Outputs, Review loop, Workflow — Architecture Review

### Community 152 - "Workflow — Freeze Process"
Cohesion: 0.25
Nodes (8): Decision gates, Exit criteria, Failure handling, Inputs, Outputs, Recording the freeze, The one exception, Workflow — Freeze Process

### Community 153 - "repositories.py"
Cohesion: 0.16
Nodes (12): to_version(), DeploymentVersionRow, _conflict(), _decode_cursor(), _encode_cursor(), _not_found(), Any, datetime (+4 more)

### Community 154 - "Decision Process"
Cohesion: 0.29
Nodes (7): Anatomy of an ADR, Decision Process, Status lifecycle, Traceability, What requires a recorded decision, Where decisions live, Who decides

### Community 155 - "Workflow — Implementation Review"
Cohesion: 0.29
Nodes (7): Decision gates, Exit criteria, Failure handling, Inputs, Outputs, Review loop, Workflow — Implementation Review

### Community 156 - "test_two_simultaneous_uploads_resolve_to_one_package"
Cohesion: 0.39
Nodes (7): BaseException, Session, sessionmaker, True insert races, forced rather than hoped for.  The sequential tests never rea, _run_racing(), test_two_simultaneous_retries_resolve_to_one_operation(), test_two_simultaneous_uploads_resolve_to_one_package()

### Community 157 - "ADR-NNN — <short decision title>"
Cohesion: 0.33
Nodes (6): ADR-NNN — <short decision title>, Alternatives, Consequences, Context, Decision, Supersession

### Community 158 - "ForgeML"
Cohesion: 0.25
Nodes (8): Configuration, Development, Documentation, ForgeML, Postman, Quickstart, Security, What a .forge package is

### Community 159 - "runtime"
Cohesion: 0.33
Nodes (5): _docker(), Path, Disposable-Docker integration tests for the runtime adapter.  Roadmap phase 6 ex, runtime(), CompletedProcess

### Community 161 - "_EnvironmentSettings"
Cohesion: 0.15
Nodes (13): 10. Observability is bounded and redacted, 11. No placeholders, no silent fallbacks, 12. Evidence over assertion, 1. The repository is the source of truth, 2. Contracts freeze before dependents are built, 3. Immutability by default, 4. Desired state is durable; observed state is reconciled, 5. Depend on ports, not providers (+5 more)

### Community 162 - "Session"
Cohesion: 0.10
Nodes (19): ActorType, AuditEvent, StrEnum, Audit events (docs 04: append-only; no payloads, no secrets)., Who caused a state change., One append-only record of a state change.      Metadata is bounded and redacted, _safe_text(), AuditLog (+11 more)

### Community 163 - "Architecture Evolution"
Cohesion: 0.29
Nodes (6): Architecture Evolution, Contracts frozen so far, Recurring patterns that emerged, Reserved for future updates, Standing architectural risks, The layering, in the order it was built

### Community 164 - "analyze"
Cohesion: 0.30
Nodes (11): Engine, Session, sessionmaker, Concurrency guarantees that only a real database can prove (ADR-009, ADR-010)., The ADR-010 claim guarantee, proven with two live transactions.      FOR UPDATE, Two uploads race; the unique index arbitrates and the loser reads the winner., test_a_second_begin_with_a_conflicting_fingerprint_still_conflicts(), test_a_third_worker_finds_nothing_while_two_rows_are_held() (+3 more)

### Community 165 - "create_session_factory"
Cohesion: 0.20
Nodes (10): create_database_engine(), create_session_factory(), Engine, Session, sessionmaker, Engine and session factory for the metadata database (ADR-009)., Build the metadata engine from typed settings.      `pool_pre_ping` costs one ro, Session factory for the unit of work.      `expire_on_commit=False` is deliberat (+2 more)

### Community 166 - "Project Memory"
Cohesion: 0.29
Nodes (6): Project Memory, Reserved for future updates, The shape of the system, What ForgeML is, What ForgeML is deliberately not, Where knowledge lives

### Community 167 - "validated"
Cohesion: 0.47
Nodes (6): What an inspection can observe about one container (docs 11).      An observatio, RuntimeStatus, Parse one `docker inspect` object into a provider-neutral status., status_from_inspect(), test_status_from_inspect_reads_running_and_health(), test_status_from_malformed_object_is_not_running()

### Community 168 - "OperationService"
Cohesion: 0.17
Nodes (9): create_operation_router(), APIRouter, Operation polling route (ADR-006)., Create the operation routes bound to the operation use cases., OperationService, UnitOfWorkFactory, UUID, Reading durable operations (ADR-006: clients poll an operation resource). (+1 more)

### Community 169 - "test_error_handling.py"
Cohesion: 0.36
Nodes (7): _client_with_failure_routes(), LogCaptureFixture, HTTP error normalization tests., test_404_and_405_use_frozen_envelope(), test_expected_application_error_is_mapped(), test_request_validation_is_sanitized(), test_unexpected_error_is_opaque()

### Community 170 - "Engineering Governance"
Cohesion: 0.33
Nodes (6): Authority order, Engineering Governance, How governance changes, Roles hold authority; vendors do not, Scope discipline, What a frozen contract means

### Community 172 - "errors.py"
Cohesion: 0.47
Nodes (3): Provider-neutral application error contracts., _validate_code(), _validate_message()

### Community 175 - "packages.py"
Cohesion: 0.33
Nodes (6): _correlation_id(), UUID, Package routes (docs 12)., The client-supplied name, reduced to something safe to store and echo.      A fi, _safe_filename(), UploadFile

### Community 176 - "augment_dockerfile"
Cohesion: 0.50
Nodes (3): augment_dockerfile(), The in-container serving harness Module 6 adds around Module 4's adapter.  Modul, Append the serving layer the frozen generated Dockerfile leaves to us.      The

### Community 177 - "Architecture Decision Records"
Cohesion: 0.40
Nodes (5): Architecture Decision Records, How to add an ADR, Index, Known decisions still owed, Where the ADRs live

### Community 178 - "reset_request_id"
Cohesion: 0.12
Nodes (20): _request_id(), _correlation_id(), UUID, current_request_id(), new_request_id(), Request-local server correlation context., Create a canonical server-owned request identifier., Set a request identifier and return the reset token. (+12 more)

### Community 179 - "test_engine.py"
Cohesion: 0.39
Nodes (7): database_url(), engine(), Session, sessionmaker, A real PostgreSQL 16 for the database gates.  ADR-009 rules SQLite out: durable, session(), session_factory()

### Community 180 - "_building_version"
Cohesion: 0.70
Nodes (4): main(), _members(), pack(), Path

### Community 181 - ".request"
Cohesion: 0.50
Nodes (4): Frozen Modules, Module 0 — Foundation, Module 1 — Forge Package System, Module 2 — Metadata Layer

## Knowledge Gaps
- **556 isolated node(s):** `forgeml`, `Mission`, `Philosophy`, `Directory structure`, `If you are a new human contributor` (+551 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AppError` connect `configure_logging` to `error_handlers.py`, `test_request_logging.py`, `APIRouter`, `_EnvironmentSettings`, `VanishingArtifactStore`, `repositories.py`, `UnitOfWork`, `SqlAlchemyOperationStore`, `Session`, `analyze`, `OperationService`, `errors.py`, `test_openapi_contract.py`, `decode_cursor`, `AppSettings`, `SqlAlchemyUnitOfWork`, `PackageCatalog`, `ArchiveReader`, `MonkeyPatch`, `test_artifact_store.py`, `errors.py`, `.inspect`, `packages.py`, `Session`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Why does `PackageLimits` connect `AuditEvent` to `AppSettings`, `APIRouter`, `AppError`, `_EnvironmentSettings`, `VanishingArtifactStore`, `runtime`, `_EnvironmentSettings`, `OperationStore`, `config.py`, `SqlAlchemyUnitOfWork`, `ArtifactStore`, `test_package_limits.py`, `_database_url`, `event`, `configure_logging`, `VanishingArtifactStore`, `packages.py`, `create_operation_router`, `Session`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `AppSettings` connect `_run_handler` to `ConfigurationFailure`, `JsonEventFormatter`, `create_session_factory`, `BaseModel`, `test_error_handling.py`, `test_package_limits.py`, `_EnvironmentSettings`, `event`, `_reject_wildcard_host`, `_EnvironmentSettings`, `test_application_boot.py`, `configure_logging`, `Package`, `MonkeyPatch`, `OperationService`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 75 inferred relationships involving `AppError` (e.g. with `app_error_handler()` and `register_error_handlers()`) actually correct?**
  _`AppError` has 75 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `UnitOfWork` (e.g. with `DeploymentService` and `OperationService`) actually correct?**
  _`UnitOfWork` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `AppSettings` (e.g. with `Container` and `JsonEventFormatter`) actually correct?**
  _`AppSettings` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `PackageLimits` (e.g. with `PackageDetail` and `PackageService`) actually correct?**
  _`PackageLimits` has 29 INFERRED edges - model-reasoned connections that need verification._