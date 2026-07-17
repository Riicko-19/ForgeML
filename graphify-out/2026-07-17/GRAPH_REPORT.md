# Graph Report - ForgeML  (2026-07-17)

## Corpus Check
- 144 files · ~64,059 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1526 nodes · 2553 edges · 130 communities (102 shown, 28 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 416 edges (avg confidence: 0.71)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `91221ff6`
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
- _EnvironmentSettings
- .request
- __init__.py
- Module 3 — Review Guide
- services.py
- event
- packages.py
- database_url
- test_health.py
- Finding
- PackageResource
- PackageSummary
- session_factory
- test_two_simultaneous_uploads_resolve_to_one_package
- .__enter__
- .rollback
- packages.py
- test_engine.py
- .__exit__
- Session
- unit_of_work.py
- ArchiveUnreadable
- client
- patch_general_purpose_flags
- Exception
- StrEnum
- datetime
- Session
- UUID
- Engine

## God Nodes (most connected - your core abstractions)
1. `AppSettings` - 59 edges
2. `AppError` - 53 edges
3. `PackageLimits` - 37 edges
4. `ASGITestClient` - 36 edges
5. `ZipArchiveReader` - 29 edges
6. `create_application()` - 27 edges
7. `build_forge()` - 27 edges
8. `PackageValidation` - 26 edges
9. `load_settings()` - 24 edges
10. `ErrorCategory` - 24 edges

## Surprising Connections (you probably didn't know these)
- `test_limits_are_immutable()` --calls--> `PackageLimits`  [INFERRED]
  backend/tests/unit/core/test_package_limits.py → backend/src/forgeml/core/config.py
- `test_limits_that_contradict_each_other_are_rejected()` --calls--> `PackageLimits`  [INFERRED]
  backend/tests/unit/core/test_package_limits.py → backend/src/forgeml/core/config.py
- `test_defaults_bound_every_dimension_of_an_untrusted_archive()` --calls--> `load_settings()`  [INFERRED]
  backend/tests/unit/core/test_package_limits.py → backend/src/forgeml/core/config.py
- `test_limits_are_overridable_from_the_environment()` --calls--> `load_settings()`  [INFERRED]
  backend/tests/unit/core/test_package_limits.py → backend/src/forgeml/core/config.py
- `test_details_must_be_typed()` --calls--> `AppError`  [INFERRED]
  backend/tests/unit/core/test_errors.py → backend/src/forgeml/core/errors.py

## Import Cycles
- None detected.

## Communities (130 total, 28 thin omitted)

### Community 0 - "AppSettings"
Cohesion: 0.15
Nodes (13): Operation, OperationFailure, OperationState, OperationType, StrEnum, Durable operation records (ADR-006).  An operation is the durable intent behind, The kinds of durable work the control plane performs.      Only the package oper, Operation lifecycle. SUCCEEDED and FAILED are terminal and immutable. (+5 more)

### Community 1 - "error_handlers.py"
Cohesion: 0.11
Nodes (27): ErrorDetailResponse, Safe, bounded validation detail., create_package_router(), APIRouter, Create the package routes bound to the package use cases., decode_cursor(), encode_cursor(), OperationFailureResponse (+19 more)

### Community 2 - "test_request_logging.py"
Cohesion: 0.05
Nodes (62): ASGIApp, app_error_handler(), _detail_response(), error_response(), http_error_handler(), internal_error_response(), Exception, FastAPI (+54 more)

### Community 3 - "ConfigurationFailure"
Cohesion: 0.17
Nodes (24): ConfigurationFailure, load_settings(), Exception, Resolve and validate the installed ForgeML distribution version., Load settings from an explicit mapping or the process environment., Fail-closed configuration error safe to classify at bootstrap., resolve_service_version(), test_a_non_postgresql_url_fails_closed() (+16 more)

### Community 4 - "JsonEventFormatter"
Cohesion: 0.12
Nodes (24): _bounded(), configure_logging(), JsonEventFormatter, LoggingConfigurationConflict, LogRecord, Bounded structured process logging., Configure process logging once for an immutable settings fingerprint., Raised when process logging is reconfigured incompatibly. (+16 more)

### Community 5 - "AppError"
Cohesion: 0.06
Nodes (69): ErrorDetail, Provider-neutral application error contracts., A bounded, safe detail for an expected application error., _validate_code(), _validate_message(), ArchiveEntry, ArchiveInspection, AssetSpec (+61 more)

### Community 6 - "test_application_boot.py"
Cohesion: 0.05
Nodes (35): Configuration, Dependency locks and package smoke, Forge package contract, ForgeML Backend — Module 0 Foundation, Module 1 Forge Package System, Frozen HTTP and correlation contracts, HTTP API (v1), Known limitations, Logging contract (+27 more)

### Community 7 - "_run_handler"
Cohesion: 0.19
Nodes (26): Reads .forge archive structure from a seekable binary stream., ZipArchiveReader, test_an_unreadable_artifact_fails_the_operation(), Path, ZIP reader against real archives, including safe extraction., reader(), stream(), test_a_directory_named_forge_yaml_is_not_a_manifest() (+18 more)

### Community 8 - "session_factory"
Cohesion: 0.24
Nodes (13): alembic_config(), migrated_engine(), Engine, Migration gates (docs 06 phase 2 exit criteria)., An empty autogenerate diff.      This is the gate that catches a model changed w, Docs 11 requires an operator to be able to review DDL before applying it., test_a_closed_unit_of_work_cannot_be_committed(), test_a_fresh_database_reaches_head() (+5 more)

### Community 9 - "test_dependency_direction.py"
Cohesion: 0.30
Nodes (13): _imports(), Path, AST-enforced dependency direction., The ORM is confined to one package.      If SQLAlchemy can be imported anywhere, Docs 02: the API adapter may depend on application use cases, and must     not r, test_api_adapts_application_and_never_reaches_a_provider(), test_application_depends_on_domain_not_providers(), test_bootstrap_imports_core_not_api() (+5 more)

### Community 10 - "_reject_wildcard_host"
Cohesion: 0.08
Nodes (24): 10. Design review record, 1. Purpose and scope, 2. Architecture, 3. Folder structure and complete file plan, 4. Technology and dependency decisions, 5. Interfaces, 6. Public HTTP API, 7. Testing and traceability (+16 more)

### Community 11 - "_EnvironmentSettings"
Cohesion: 0.18
Nodes (12): _fingerprint(), is_accepted(), _latest(), PackageService, BinaryIO, UUID, Package upload, validation, and read use cases.  Validation runs inside the requ, Claim the operation, validate, and record the verdict atomically. (+4 more)

### Community 12 - "test_process_signals.py"
Cohesion: 0.22
Nodes (24): body(), Any, Response, The package and operation HTTP surface, end to end.  A real application, a real, test_a_malformed_identifier_is_a_validation_error(), test_a_mutation_without_an_idempotency_key_is_refused(), test_a_rejected_package_still_completes_its_operation(), test_an_invalid_cursor_is_a_bad_request() (+16 more)

### Community 18 - "Architecture Decision Records"
Cohesion: 0.11
Nodes (17): ADR-001 — Trusted packages; defense-in-depth runtime isolation, ADR-002 — Modular monolith control plane, ADR-003 — Immutable content-addressed packages/images, ADR-004 — Metadata desired state; Docker reconciliation, ADR-005 — One active version and platform route, ADR-006 — Asynchronous durable operations, ADR-007 — Storage/database behind ports, ADR-008 — Initial runtime compatibility matrix (+9 more)

### Community 19 - "AuditEvent"
Cohesion: 0.12
Nodes (12): PackageCatalog, PackagePage, UUID, Ports owned by the package domain.  Callers never receive a filesystem path. An, One page of packages, newest first., Durable package records. Duplicate checksums resolve to one package., Return the package for these bytes, creating it in DRAFT if absent.          Sto, Read one package by its opaque identifier. (+4 more)

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
Cohesion: 0.16
Nodes (9): provider(), BinaryIO, Path, Startup recovery and the platform-failure path.  These are the paths that only r, ADR-016, end to end: a worker dies mid-operation and the platform heals., Stores an archive, then loses it before anything can read it.      A disk failur, test_startup_recovery_is_harmless_when_nothing_was_abandoned(), test_startup_returns_an_abandoned_operation_to_the_queue() (+1 more)

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
Cohesion: 0.05
Nodes (65): PackageValidationService, Validate a stored .forge artifact against the format version 1 contract., Runs archive validation over a stored artifact.      Asset checksums are the onl, analyze(), _normalized_schema(), Any, Derive the normalized inference contract from a validated manifest.  Module 4's, Return the schema with the supported dialect made explicit.      Validation acce (+57 more)

### Community 28 - "SqlAlchemyOperationStore"
Cohesion: 0.23
Nodes (6): Package, A stored package. Checksum and artifact are immutable (ADR-003).      manifest_v, PackageRow, Package records backed by PostgreSQL., SqlAlchemyPackageCatalog, PackagePage

### Community 29 - "High Level Design"
Cohesion: 0.22
Nodes (8): Acceptance criteria, Component responsibilities, Deployment lifecycle, Extension points, Failure/compensation, Happy-path sequence, High Level Design, Routing

### Community 30 - "Low Level Design"
Cohesion: 0.22
Nodes (8): Acceptance criteria, Concurrency and idempotency, Domain records, Error taxonomy, .forge contract, Lifecycle rules, Low Level Design, Ports

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
Cohesion: 0.08
Nodes (31): FakeServer, BaseException, LogCaptureFixture, MonkeyPatch, Bootstrap and composition integration tests., test_configuration_failure_is_safe_and_exits_two(), test_logging_conflict_exits_one(), test_module_entrypoint_returns_bootstrap_exit_code() (+23 more)

### Community 53 - "test_openapi_contract.py"
Cohesion: 0.14
Nodes (20): AppError, Exception, An immutable expected application failure., artifact_uri(), FilesystemArtifactStore, BinaryIO, Path, Content-addressed artifact storage on a local filesystem (ADR-007, ADR-009). (+12 more)

### Community 62 - "OperationStore"
Cohesion: 0.12
Nodes (23): create_application(), FastAPI, FastAPI application composition root., Create the control-plane application with its dependencies wired., AppSettings, Immutable settings consumed by composition and bootstrap., Frozen HTTP wire contract tests., test_framework_error_wire_shape_omits_empty_details() (+15 more)

### Community 63 - "_NoAliasLoader"
Cohesion: 0.14
Nodes (13): Amendment after freeze (Module 3), CI evidence, Database schema, Engineering decisions, Files created, Files modified, Known limitations, Migrations (+5 more)

### Community 64 - "create_application"
Cohesion: 0.16
Nodes (7): BaseException, Session, sessionmaker, TracebackType, The SQLAlchemy unit of work: one session, one transaction, three repositories., One atomic metadata transaction.      All three repositories are built from the, SqlAlchemyUnitOfWork

### Community 65 - "config.py"
Cohesion: 0.14
Nodes (13): ConfigurationIssue, Environment, LogLevel, StrEnum, ValidationError, Typed, fail-closed Module 0 configuration., The metadata database URL, or a fail-closed configuration error.          Module, Supported deployment environments. (+5 more)

### Community 66 - "Operation"
Cohesion: 0.18
Nodes (6): _Clock, InMemoryPackageCatalog, datetime, UUID, In-memory implementations of the Module 2 ports.  Module 3 will test its use cas, Monotonic timestamps, so ordering is deterministic without sleeping.

### Community 67 - "SqlAlchemyPackageCatalog"
Cohesion: 0.18
Nodes (10): _NoAliasLoader, Any, BinaryIO, ZipInfo, ZIP adapter for .forge archives.  This is the only module that knows a .forge fi, Safe YAML loader that also refuses aliases.      yaml.safe_load still expands al, _to_entry(), _unsafe_member() (+2 more)

### Community 68 - "AppSettings"
Cohesion: 0.33
Nodes (4): Base, PackageValidationRow, SQLAlchemy mappings. The only ORM classes in ForgeML.  Nothing here leaves this, DeclarativeBase

### Community 69 - "OperationType"
Cohesion: 0.14
Nodes (11): OperationStore, Any, Protocol, UUID, The durable operation store (ADR-006, ADR-010, ADR-016)., Durable operations, claimed by one worker at a time.      This store is the queu, Create the operation, or return the original one for a repeated request., Claim one named operation, or None if it is not pending.          An inline exec (+3 more)

### Community 70 - "SqlAlchemyUnitOfWork"
Cohesion: 0.18
Nodes (11): _client_with_failure_routes(), Payload, BaseModel, LogCaptureFixture, HTTP error normalization tests., test_404_and_405_use_frozen_envelope(), test_expected_application_error_is_mapped(), test_request_validation_is_sanitized() (+3 more)

### Community 71 - "PackageCatalog"
Cohesion: 0.11
Nodes (18): UnitOfWorkFactory, PackageLimits, Operator policy bounding work spent on an untrusted .forge archive.      Every b, ArchiveReader, ArtifactStore, BinaryIO, Protocol, Extract the archive into a fresh, empty staging directory. (+10 more)

### Community 72 - "main"
Cohesion: 0.21
Nodes (10): main(), Exception, _raise_shutdown_requested(), Fail-closed ForgeML process bootstrap., Translate Uvicorn's re-raised SIGTERM into a clean process exit., Validate configuration and run the single ForgeML ASGI worker., _safe_bootstrap_failure(), _ShutdownRequested (+2 more)

### Community 73 - "ArchiveReader"
Cohesion: 0.09
Nodes (17): OperationService, UnitOfWorkFactory, UUID, Reading durable operations (ADR-006: clients poll an operation resource)., Reads operations for polling clients., Container, The dependency graph, wired once and shared by the routes., DatabaseProvider (+9 more)

### Community 74 - "test_invariants.py"
Cohesion: 0.35
Nodes (11): _insert_package(), Engine, Invariants the database enforces, independently of our repositories.  These test, test_a_package_artifact_cannot_be_repointed(), test_a_package_cannot_have_zero_size(), test_a_package_checksum_cannot_be_rewritten(), test_a_package_state_may_still_advance(), test_a_terminal_operation_cannot_be_rewritten() (+3 more)

### Community 75 - "_run_handler"
Cohesion: 0.18
Nodes (10): §1 — The highest-risk code (25 min), §2 — The tests that decide whether you can trust the above (20 min), §3 — Skim only (15 min), §4 — Questions you should answer (15 min), §5 — Implementation risks, `infrastructure/database/repositories.py` — read in full (15 min), `infrastructure/database/unit_of_work.py` — read in full (5 min), `migrations/versions/0d7adf1f94cf_*.py` — read the trigger DDL only (5 min) (+2 more)

### Community 76 - "ArtifactStore"
Cohesion: 0.18
Nodes (11): create_health_router(), APIRouter, Operational health routes., Create health routes bound to immutable service identity.      Liveness answers, ErrorEnvelope, HealthResponse, BaseModel, Frozen Module 0 HTTP response schemas. (+3 more)

### Community 77 - "test_package_limits.py"
Cohesion: 0.22
Nodes (8): installed_version(), MonkeyPatch, Package limits are operator policy loaded through the fail-closed loader., test_an_invalid_limit_fails_closed(), test_defaults_bound_every_dimension_of_an_untrusted_archive(), test_limits_are_immutable(), test_limits_are_overridable_from_the_environment(), test_limits_that_contradict_each_other_are_rejected()

### Community 78 - "_database_url"
Cohesion: 0.32
Nodes (7): _database_url(), Alembic environment.  The database URL comes from the same typed, fail-closed co, The URL supplied by the caller, else the application's own configuration.      T, Emit SQL without a connection, so an operator can review DDL first., Run migrations against a live database., run_migrations_offline(), run_migrations_online()

### Community 79 - "event"
Cohesion: 0.22
Nodes (8): Acceptance criteria — status, Changes from the frozen design, Layering (as built), Module 2 — Metadata Layer Design (as built), Schema, Scope, Scope audit, Transaction boundaries

### Community 80 - "models.py"
Cohesion: 0.16
Nodes (18): InferenceContract, The normalized contract for serving one packaged model (docs 03/04).      Derive, contract_from_json(), contract_to_json(), finding_from_json(), finding_to_json(), manifest_to_json(), Any (+10 more)

### Community 81 - "_reject_wildcard_host"
Cohesion: 0.33
Nodes (5): _reject_wildcard_host(), Shared Module 0 test fixtures., settings(), IPv4Address, IPv6Address

### Community 82 - "_EnvironmentSettings"
Cohesion: 0.22
Nodes (4): InMemoryUnitOfWork, BaseException, TracebackType, A unit of work whose rollback really does discard writes.      Repositories writ

### Community 83 - "PackagePage"
Cohesion: 0.22
Nodes (8): D-1 — Orphaned operations: startup reconciliation, not a lease, D-2 — Concurrency is delegated to PostgreSQL, never to application checks, D-3 — Unit of Work in the application layer, not `core`, D-4 — Database-enforced immutability, not repository discipline alone, D-5 — Findings persist as an ordered JSONB array, D-6 — `manifest_version` is null until validation, D-7 — The fakes are held to the real adapters' contract, Module 2 — Engineering Decisions

### Community 85 - "configure_logging"
Cohesion: 0.39
Nodes (7): AppError, _conflict(), _decode_cursor(), _encode_cursor(), _not_found(), PostgreSQL implementations of the package, operation, and audit ports.  Concurre, datetime

### Community 89 - "ConfigurationIssue"
Cohesion: 0.17
Nodes (11): Common mistakes, Database, Module 2 — Handoff, Module 3 entry gate — satisfied, Public contracts, Repositories, The one idea, Transaction boundaries (+3 more)

### Community 90 - "ValidationError"
Cohesion: 0.20
Nodes (9): Acceptance criteria — status, Correlation, Error mapping, Idempotency (docs 04), Layering, Module 3 — Backend API Design, Readiness, Scope (+1 more)

### Community 91 - "Path"
Cohesion: 0.20
Nodes (9): D-1 — Validation runs inline; the operation resource stays, D-2 — A rejected package succeeds its operation, D-3 — `OperationStore.claim(operation_id)` (frozen-module amendment), D-4 — The pagination cursor is opaque and URL-safe, D-5 — Multipart upload, and a synchronous handler, D-6 — 422 is declared explicitly on every route, D-7 — The published schema, but no interactive docs, D-8 — Readiness now checks the database; startup fails closed (+1 more)

### Community 93 - "test_artifact_store.py"
Cohesion: 0.29
Nodes (5): ActorType, StrEnum, Audit events (docs 04: append-only; no payloads, no secrets)., Who caused a state change., _safe_text()

### Community 94 - "OperationService"
Cohesion: 0.30
Nodes (11): Engine, Session, sessionmaker, Concurrency guarantees that only a real database can prove (ADR-009, ADR-010)., The ADR-010 claim guarantee, proven with two live transactions.      FOR UPDATE, Two uploads race; the unique index arbitrates and the loser reads the winner., test_a_second_begin_with_a_conflicting_fingerprint_still_conflicts(), test_a_third_worker_finds_nothing_while_two_rows_are_held() (+3 more)

### Community 95 - "create_health_router"
Cohesion: 0.22
Nodes (11): Operation, to_operation(), OperationRow, Any, Operation, Durable operations, claimed with row locking (ADR-010, ADR-016)., Reclaim work abandoned by a dead worker (ADR-016).          ADR-010 supervises e, SqlAlchemyOperationStore (+3 more)

### Community 96 - "errors.py"
Cohesion: 0.40
Nodes (4): create_operation_router(), APIRouter, Operation polling route (ADR-006)., Create the operation routes bound to the operation use cases.

### Community 97 - "PackageValidationService"
Cohesion: 0.22
Nodes (8): CI evidence, Engineering decisions, Files created, Files modified, Known limitations, Module 3 — Backend API Implementation, Public interfaces, Technical debt

### Community 98 - "_EnvironmentSettings"
Cohesion: 0.27
Nodes (8): manifest(), Any, A valid manifest with top-level sections replaced., The manifest model is the closed shape of forge.yaml., test_control_characters_are_rejected_in_package_authored_text(), test_metadata_may_not_be_unbounded(), test_schema_is_read_from_the_declared_field_name_only(), test_unknown_fields_are_rejected_at_every_level()

### Community 99 - ".request"
Cohesion: 0.22
Nodes (9): create_database_engine(), create_session_factory(), Engine, Session, sessionmaker, Engine and session factory for the metadata database (ADR-009)., Build the metadata engine from typed settings.      `pool_pre_ping` costs one ro, Session factory for the unit of work.      `expire_on_commit=False` is deliberat (+1 more)

### Community 102 - "Module 3 — Review Guide"
Cohesion: 0.22
Nodes (8): §1 — The file that matters (20 min), §2 — The contract tests (15 min), §3 — Skim (10 min), §4 — Questions you should answer, §5 — Risks, `application/package/services.py` — read in full, If you have 10 minutes, Module 3 — Review Guide

### Community 103 - "services.py"
Cohesion: 0.23
Nodes (13): _await_boot(), _await_operation(), _free_port(), Any, Path, The ForgeML golden path, end to end, against a real server.  Every other HTTP te, Poll one operation until it reaches a terminal state (ADR-006)., Run `python -m forgeml` on a free port and yield its base URL.      This repeats (+5 more)

### Community 105 - "packages.py"
Cohesion: 0.13
Nodes (16): ArchiveReader, ArtifactStore, Finding, Stable machine codes reported by package validation.      These codes are part o, _deep_schema(), Any, Path, The .forge reference fixture matrix.  Each case drives a real archive through th (+8 more)

### Community 106 - "database_url"
Cohesion: 0.28
Nodes (7): database_url(), migrated(), Shared database setup for the HTTP integration tests., Bring the schema to head once, via the migration the operator would run., _available_loopback_port(), Real-process signal and graceful-shutdown integration., test_sigterm_stops_installed_process_without_traceback()

### Community 107 - "test_health.py"
Cohesion: 0.20
Nodes (9): Before you import, Common failures, Files, ForgeML — Postman, Import, Run order, Things that will confuse you once, Trying a rejection (+1 more)

### Community 108 - "Finding"
Cohesion: 0.33
Nodes (6): PackageState, Persisted package lifecycle (docs 04).      ValidationState is the validator's v, Terminal outcome of validating one archive., ValidationState, to_package(), StrEnum

### Community 109 - "PackageResource"
Cohesion: 0.15
Nodes (11): AuditEvent, One append-only record of a state change.      Metadata is bounded and redacted, AuditLog, Protocol, UUID, The audit trail port (docs 04)., Append-only audit trail.      `record` enlists in the caller's unit of work, bec, Append one audit event to the current transaction. (+3 more)

### Community 110 - "PackageSummary"
Cohesion: 0.70
Nodes (4): main(), _members(), pack(), Path

### Community 111 - "session_factory"
Cohesion: 0.39
Nodes (7): database_url(), engine(), Session, sessionmaker, A real PostgreSQL 16 for the database gates.  ADR-009 rules SQLite out: durable, session(), session_factory()

### Community 112 - "test_two_simultaneous_uploads_resolve_to_one_package"
Cohesion: 0.39
Nodes (7): BaseException, Session, sessionmaker, True insert races, forced rather than hoped for.  The sequential tests never rea, _run_racing(), test_two_simultaneous_retries_resolve_to_one_operation(), test_two_simultaneous_uploads_resolve_to_one_package()

### Community 113 - ".__enter__"
Cohesion: 0.50
Nodes (3): predict(), The entrypoint of the example package.  ForgeML never imports or executes this f, Receive one document matching input.schema, return one matching output.schema.

### Community 116 - "test_engine.py"
Cohesion: 0.33
Nodes (5): installed_version(), MonkeyPatch, The engine the control plane actually builds, against a real database.  Every ot, settings(), test_the_database_url_is_never_disclosed()

### Community 117 - ".__exit__"
Cohesion: 0.13
Nodes (10): BaseException, Protocol, TracebackType, The transaction boundary owned by the application layer.  A use case opens one u, One atomic metadata transaction.      Leaving the context without committing rol, Begin the transaction., Commit on a clean exit that called commit; otherwise roll back., Commit the transaction. (+2 more)

### Community 118 - "Session"
Cohesion: 0.25
Nodes (5): AuditEventRow, AuditEvent, Append-only audit trail enlisted in the caller's transaction., SqlAlchemyAuditLog, Session

### Community 120 - "unit_of_work.py"
Cohesion: 0.40
Nodes (4): Analyzer and Generator are pure functions, not Protocols, Determinism, Module 4 — Analyzer / Generator (engineering note), The `PackageValidation.contract` field is a planned completion, not a change

### Community 121 - "ArchiveUnreadable"
Cohesion: 0.50
Nodes (4): ArchiveUnreadable, The bytes are not a readable ZIP container at all., test_bytes_that_are_not_a_zip_container_are_unreadable(), Exception

### Community 122 - "client"
Cohesion: 0.67
Nodes (3): client(), MonkeyPatch, Path

## Knowledge Gaps
- **339 isolated node(s):** `The `PackageValidation.contract` field is a planned completion, not a change`, `Analyzer and Generator are pure functions, not Protocols`, `Determinism`, `forgeml`, `graphify` (+334 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AppError` connect `test_openapi_contract.py` to `AppSettings`, `error_handlers.py`, `test_request_logging.py`, `SqlAlchemyPackageCatalog`, `Operation`, `AppError`, `SqlAlchemyUnitOfWork`, `_run_handler`, `ArchiveReader`, `_EnvironmentSettings`, `PackageResource`, `_EnvironmentSettings`, `ForgeML Backend — Module 0 Foundation, Module 1 Forge Package System`, `OperationService`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Why does `AppSettings` connect `OperationStore` to `config.py`, `test_request_logging.py`, `ConfigurationFailure`, `JsonEventFormatter`, `.request`, `SqlAlchemyUnitOfWork`, `event`, `ArchiveReader`, `ArtifactStore`, `models.py`, `_reject_wildcard_host`, `test_application_boot.py`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `PackageLimits` connect `PackageCatalog` to `config.py`, `error_handlers.py`, `SqlAlchemyPackageCatalog`, `AppError`, `_run_handler`, `event`, `_EnvironmentSettings`, `test_package_limits.py`, `AuditEvent`, `test_openapi_contract.py`, `ForgeML Backend — Module 0 Foundation, Module 1 Forge Package System`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `AppSettings` (e.g. with `Container` and `JsonEventFormatter`) actually correct?**
  _`AppSettings` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 45 inferred relationships involving `AppError` (e.g. with `app_error_handler()` and `register_error_handlers()`) actually correct?**
  _`AppError` has 45 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `PackageLimits` (e.g. with `PackageDetail` and `PackageService`) actually correct?**
  _`PackageLimits` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `ASGITestClient` (e.g. with `test_framework_error_wire_shape_omits_empty_details()` and `test_health_wire_shapes_and_header()`) actually correct?**
  _`ASGITestClient` has 9 INFERRED edges - model-reasoned connections that need verification._