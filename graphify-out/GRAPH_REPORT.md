# Graph Report - ForgeML  (2026-07-14)

## Corpus Check
- 127 files · ~51,139 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1376 nodes · 2443 edges · 102 communities (83 shown, 19 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 461 edges (avg confidence: 0.71)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2c8c8721`
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

## God Nodes (most connected - your core abstractions)
1. `AppError` - 65 edges
2. `AppSettings` - 59 edges
3. `UnitOfWork` - 49 edges
4. `ErrorDetail` - 43 edges
5. `PackageLimits` - 40 edges
6. `ASGITestClient` - 36 edges
7. `build_forge()` - 34 edges
8. `AuditEvent` - 30 edges
9. `ZipArchiveReader` - 30 edges
10. `Operation` - 28 edges

## Surprising Connections (you probably didn't know these)
- `test_limits_are_immutable()` --calls--> `PackageLimits`  [INFERRED]
  backend/tests/unit/core/test_package_limits.py → backend/src/forgeml/core/config.py
- `test_limits_that_contradict_each_other_are_rejected()` --calls--> `PackageLimits`  [INFERRED]
  backend/tests/unit/core/test_package_limits.py → backend/src/forgeml/core/config.py
- `test_defaults_bound_every_dimension_of_an_untrusted_archive()` --calls--> `load_settings()`  [INFERRED]
  backend/tests/unit/core/test_package_limits.py → backend/src/forgeml/core/config.py
- `test_limits_are_overridable_from_the_environment()` --calls--> `load_settings()`  [INFERRED]
  backend/tests/unit/core/test_package_limits.py → backend/src/forgeml/core/config.py
- `test_invalid_codes_are_rejected()` --calls--> `ErrorDetail`  [INFERRED]
  backend/tests/unit/core/test_errors.py → backend/src/forgeml/core/errors.py

## Import Cycles
- None detected.

## Communities (102 total, 19 thin omitted)

### Community 0 - "AppSettings"
Cohesion: 0.22
Nodes (6): Frozen HTTP wire contract tests., test_framework_error_wire_shape_omits_empty_details(), test_health_wire_shapes_and_header(), test_unavailable_readiness_uses_the_frozen_error_envelope(), FastAPI, Minimal synchronous facade over HTTPX's in-process ASGI transport.

### Community 1 - "error_handlers.py"
Cohesion: 0.06
Nodes (56): app_error_handler(), _detail_response(), error_response(), http_error_handler(), internal_error_response(), Exception, FastAPI, JSONResponse (+48 more)

### Community 2 - "test_request_logging.py"
Cohesion: 0.06
Nodes (46): ASGIApp, Own the canonical request ID for one HTTP request., RequestContextMiddleware, _correlation_id(), UUID, Package routes (docs 12)., The client-supplied name, reduced to something safe to store and echo.      A fi, _safe_filename() (+38 more)

### Community 3 - "ConfigurationFailure"
Cohesion: 0.18
Nodes (23): ConfigurationFailure, load_settings(), Exception, Resolve and validate the installed ForgeML distribution version., Load settings from an explicit mapping or the process environment., Fail-closed configuration error safe to classify at bootstrap., resolve_service_version(), MonkeyPatch (+15 more)

### Community 4 - "JsonEventFormatter"
Cohesion: 0.22
Nodes (16): JsonEventFormatter, Render a strict allowlisted JSON event., BaseException, LogRecord, TracebackType, Structured logging policy tests., _record(), test_event_and_fields_are_bounded() (+8 more)

### Community 5 - "AppError"
Cohesion: 0.05
Nodes (82): ErrorDetail, A bounded, safe detail for an expected application error., ArchiveEntry, ArchiveInspection, AssetSpec, EntrypointSection, Finding, is_supported_schema_dialect() (+74 more)

### Community 6 - "test_application_boot.py"
Cohesion: 0.14
Nodes (13): CI Status, Current Development Stage, Current Module, Current Version, Engineering Authority, ForgeML Project Status, Frozen Modules, Last Frozen Milestone (+5 more)

### Community 7 - "_run_handler"
Cohesion: 0.23
Nodes (24): Reads .forge archive structure from a seekable binary stream., ZipArchiveReader, test_an_unreadable_artifact_fails_the_operation(), Path, ZIP reader against real archives, including safe extraction., reader(), stream(), test_a_directory_named_forge_yaml_is_not_a_manifest() (+16 more)

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
Cohesion: 0.10
Nodes (20): _fingerprint(), is_accepted(), _latest(), PackageDetail, PackageService, BinaryIO, UUID, Package upload, validation, and read use cases.  Validation runs inside the requ (+12 more)

### Community 12 - "test_process_signals.py"
Cohesion: 0.28
Nodes (7): database_url(), migrated(), Shared database setup for the HTTP integration tests., Bring the schema to head once, via the migration the operator would run., _available_loopback_port(), Real-process signal and graceful-shutdown integration., test_sigterm_stops_installed_process_without_traceback()

### Community 18 - "Architecture Decision Records"
Cohesion: 0.11
Nodes (17): ADR-001 — Trusted packages; defense-in-depth runtime isolation, ADR-002 — Modular monolith control plane, ADR-003 — Immutable content-addressed packages/images, ADR-004 — Metadata desired state; Docker reconciliation, ADR-005 — One active version and platform route, ADR-006 — Asynchronous durable operations, ADR-007 — Storage/database behind ports, ADR-008 — Initial runtime compatibility matrix (+9 more)

### Community 19 - "AuditEvent"
Cohesion: 0.20
Nodes (9): ErrorCategory, StrEnum, Transport-neutral classes of expected application failure., AuditEvent, One append-only record of a state change.      Metadata is bounded and redacted, AuditEventRow, Append-only audit trail enlisted in the caller's transaction., SqlAlchemyAuditLog (+1 more)

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
Cohesion: 0.15
Nodes (12): Configuration, Dependency locks and package smoke, Forge package contract, ForgeML Backend — Module 0 Foundation, Module 1 Forge Package System, Frozen HTTP and correlation contracts, Known limitations, Logging contract, Metadata layer (+4 more)

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
Nodes (46): BaseException, Protocol, TracebackType, The transaction boundary owned by the application layer.  A use case opens one u, One atomic metadata transaction.      Leaving the context without committing rol, Begin the transaction., Commit on a clean exit that called commit; otherwise roll back., Commit the transaction. (+38 more)

### Community 28 - "SqlAlchemyOperationStore"
Cohesion: 0.19
Nodes (12): OperationRow, _conflict(), _decode_cursor(), _encode_cursor(), _not_found(), Any, datetime, UUID (+4 more)

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
Cohesion: 0.14
Nodes (19): FakeServer, BaseException, LogCaptureFixture, MonkeyPatch, Bootstrap and composition integration tests., test_configuration_failure_is_safe_and_exits_two(), test_logging_conflict_exits_one(), test_module_entrypoint_returns_bootstrap_exit_code() (+11 more)

### Community 53 - "test_openapi_contract.py"
Cohesion: 0.23
Nodes (8): artifact_uri(), FilesystemArtifactStore, BinaryIO, Path, Content-addressed artifact storage on a local filesystem (ADR-007, ADR-009)., The opaque reference callers hold instead of a filesystem path., Streams archives to disk under their own SHA-256, atomically.      A partial wri, test_artifact_is_addressed_by_its_own_checksum()

### Community 62 - "OperationStore"
Cohesion: 0.19
Nodes (27): body(), client(), Any, MonkeyPatch, Path, Response, The package and operation HTTP surface, end to end.  A real application, a real, test_a_malformed_identifier_is_a_validation_error() (+19 more)

### Community 63 - "_NoAliasLoader"
Cohesion: 0.15
Nodes (12): CI evidence, Database schema, Engineering decisions, Files created, Files modified, Known limitations, Migrations, Module 2 — Metadata Layer Implementation (+4 more)

### Community 64 - "create_application"
Cohesion: 0.18
Nodes (8): AuditLog, Protocol, UUID, The audit trail port (docs 04)., Append-only audit trail.      `record` enlists in the caller's unit of work, bec, Append one audit event to the current transaction., Read the audit trail of one target, newest first., Read every event recorded under one correlation ID.

### Community 65 - "config.py"
Cohesion: 0.25
Nodes (8): Environment, LogLevel, StrEnum, Typed, fail-closed Module 0 configuration., Supported deployment environments., Supported process log levels., _require_postgresql(), SecretStr

### Community 66 - "Operation"
Cohesion: 0.14
Nodes (10): OperationFailure, A safe, classified failure. Never a trace, a host path, or a payload., _Clock, InMemoryOperationStore, InMemoryPackageCatalog, Any, datetime, UUID (+2 more)

### Community 67 - "SqlAlchemyPackageCatalog"
Cohesion: 0.13
Nodes (15): PackageLimits, Operator policy bounding work spent on an untrusted .forge archive.      Every b, ArchiveUnreadable, Exception, The bytes are not a readable ZIP container at all., _NoAliasLoader, Any, BinaryIO (+7 more)

### Community 68 - "AppSettings"
Cohesion: 0.11
Nodes (28): Container, create_application(), FastAPI, FastAPI application composition root., The dependency graph, wired once and shared by the routes., Create the control-plane application with its dependencies wired., AppSettings, Immutable settings consumed by composition and bootstrap. (+20 more)

### Community 69 - "OperationType"
Cohesion: 0.09
Nodes (21): Operation, OperationState, OperationType, StrEnum, Durable operation records (ADR-006).  An operation is the durable intent behind, The kinds of durable work the control plane performs.      Only the package oper, Operation lifecycle. SUCCEEDED and FAILED are terminal and immutable., One durable unit of asynchronous work. (+13 more)

### Community 70 - "SqlAlchemyUnitOfWork"
Cohesion: 0.16
Nodes (7): BaseException, Session, sessionmaker, TracebackType, The SQLAlchemy unit of work: one session, one transaction, three repositories., One atomic metadata transaction.      All three repositories are built from the, SqlAlchemyUnitOfWork

### Community 71 - "PackageCatalog"
Cohesion: 0.06
Nodes (29): UnitOfWorkFactory, Package, A stored package. Checksum and artifact are immutable (ADR-003).      manifest_v, ArchiveReader, ArtifactStore, PackageCatalog, PackagePage, BinaryIO (+21 more)

### Community 72 - "main"
Cohesion: 0.21
Nodes (10): main(), Exception, _raise_shutdown_requested(), Fail-closed ForgeML process bootstrap., Translate Uvicorn's re-raised SIGTERM into a clean process exit., Validate configuration and run the single ForgeML ASGI worker., _safe_bootstrap_failure(), _ShutdownRequested (+2 more)

### Community 73 - "ArchiveReader"
Cohesion: 0.15
Nodes (10): DatabaseProvider, Engine, Exception, Session, sessionmaker, Lazy database lifecycle: engine, unit of work factory, and readiness.  The compo, Owns the engine and hands out units of work., Return operations abandoned by a previous process to the queue.          ADR-016 (+2 more)

### Community 74 - "test_invariants.py"
Cohesion: 0.35
Nodes (11): _insert_package(), Engine, Invariants the database enforces, independently of our repositories.  These test, test_a_package_artifact_cannot_be_repointed(), test_a_package_cannot_have_zero_size(), test_a_package_checksum_cannot_be_rewritten(), test_a_package_state_may_still_advance(), test_a_terminal_operation_cannot_be_rewritten() (+3 more)

### Community 75 - "_run_handler"
Cohesion: 0.18
Nodes (10): §1 — The highest-risk code (25 min), §2 — The tests that decide whether you can trust the above (20 min), §3 — Skim only (15 min), §4 — Questions you should answer (15 min), §5 — Implementation risks, `infrastructure/database/repositories.py` — read in full (15 min), `infrastructure/database/unit_of_work.py` — read in full (5 min), `migrations/versions/0d7adf1f94cf_*.py` — read the trigger DDL only (5 min) (+2 more)

### Community 76 - "ArtifactStore"
Cohesion: 0.22
Nodes (4): InMemoryUnitOfWork, BaseException, TracebackType, A unit of work whose rollback really does discard writes.      Repositories writ

### Community 77 - "test_package_limits.py"
Cohesion: 0.22
Nodes (8): installed_version(), MonkeyPatch, Package limits are operator policy loaded through the fail-closed loader., test_an_invalid_limit_fails_closed(), test_defaults_bound_every_dimension_of_an_untrusted_archive(), test_limits_are_immutable(), test_limits_are_overridable_from_the_environment(), test_limits_that_contradict_each_other_are_rejected()

### Community 78 - "_database_url"
Cohesion: 0.32
Nodes (7): _database_url(), Alembic environment.  The database URL comes from the same typed, fail-closed co, The URL supplied by the caller, else the application's own configuration.      T, Emit SQL without a connection, so an operator can review DDL first., Run migrations against a live database., run_migrations_offline(), run_migrations_online()

### Community 79 - "event"
Cohesion: 0.18
Nodes (16): _deep_schema(), _encrypted_member(), _non_utf8_name(), Any, Path, The .forge reference fixture matrix.  Each case drives a real archive through th, test_findings_carry_a_stable_path(), test_minimal_valid_package_is_accepted() (+8 more)

### Community 80 - "models.py"
Cohesion: 0.16
Nodes (8): Base, PackageRow, PackageValidationRow, SQLAlchemy mappings. The only ORM classes in ForgeML.  Nothing here leaves this, Session, Package records backed by PostgreSQL., SqlAlchemyPackageCatalog, DeclarativeBase

### Community 81 - "_reject_wildcard_host"
Cohesion: 0.33
Nodes (5): _reject_wildcard_host(), Shared Module 0 test fixtures., settings(), IPv4Address, IPv6Address

### Community 82 - "_EnvironmentSettings"
Cohesion: 0.22
Nodes (8): Acceptance criteria — status, Changes from the frozen design, Layering (as built), Module 2 — Metadata Layer Design (as built), Schema, Scope, Scope audit, Transaction boundaries

### Community 83 - "PackagePage"
Cohesion: 0.22
Nodes (8): D-1 — Orphaned operations: startup reconciliation, not a lease, D-2 — Concurrency is delegated to PostgreSQL, never to application checks, D-3 — Unit of Work in the application layer, not `core`, D-4 — Database-enforced immutability, not repository discipline alone, D-5 — Findings persist as an ordered JSONB array, D-6 — `manifest_version` is null until validation, D-7 — The fakes are held to the real adapters' contract, Module 2 — Engineering Decisions

### Community 85 - "configure_logging"
Cohesion: 0.17
Nodes (11): Server-owned request correlation and bounded request logging., _bounded(), configure_logging(), LoggingConfigurationConflict, LogRecord, Bounded structured process logging., Configure process logging once for an immutable settings fingerprint., Raised when process logging is reconfigured incompatibly. (+3 more)

### Community 89 - "ConfigurationIssue"
Cohesion: 0.29
Nodes (5): ConfigurationIssue, ValidationError, The metadata database URL, or a fail-closed configuration error.          Module, A safe configuration finding without an input value., _safe_issues()

### Community 90 - "ValidationError"
Cohesion: 0.17
Nodes (12): manifest(), Any, ZipInfo, Builders for .forge archive fixtures.  Fixtures are constructed in memory rather, A ZIP member whose mode marks it a symbolic link., A valid manifest with top-level sections replaced., symlink_member(), The manifest model is the closed shape of forge.yaml. (+4 more)

### Community 91 - "Path"
Cohesion: 0.16
Nodes (9): provider(), BinaryIO, Path, Startup recovery and the platform-failure path.  These are the paths that only r, ADR-016, end to end: a worker dies mid-operation and the platform heals., Stores an archive, then loses it before anything can read it.      A disk failur, test_startup_recovery_is_harmless_when_nothing_was_abandoned(), test_startup_returns_an_abandoned_operation_to_the_queue() (+1 more)

### Community 92 - "MonkeyPatch"
Cohesion: 0.18
Nodes (12): AppError, Exception, An immutable expected application failure., Payload, BaseModel, Application error invariant tests., test_detail_count_is_bounded(), test_details_must_be_typed() (+4 more)

### Community 93 - "test_artifact_store.py"
Cohesion: 0.27
Nodes (9): Path, Filesystem artifact store against a real directory., store(), test_an_artifact_reference_that_is_not_a_digest_is_refused(), test_delete_removes_the_artifact_and_tolerates_absence(), test_failed_write_leaves_no_staging_residue(), test_oversized_upload_is_rejected_and_leaves_no_artifact(), test_reading_an_absent_artifact_is_a_not_found_error() (+1 more)

### Community 94 - "OperationService"
Cohesion: 0.25
Nodes (5): OperationService, UnitOfWorkFactory, UUID, Reading durable operations (ADR-006: clients poll an operation resource)., Reads operations for polling clients.

### Community 95 - "create_health_router"
Cohesion: 0.33
Nodes (5): create_health_router(), APIRouter, Operational health routes., Create health routes bound to immutable service identity.      Liveness answers, ReadinessCheck

### Community 96 - "errors.py"
Cohesion: 0.47
Nodes (3): Provider-neutral application error contracts., _validate_code(), _validate_message()

### Community 97 - "PackageValidationService"
Cohesion: 0.40
Nodes (3): PackageValidationService, Validate a stored .forge artifact against the format version 1 contract., Runs archive validation over a stored artifact.      Asset checksums are the onl

## Knowledge Gaps
- **279 isolated node(s):** `forgeml`, `graphify`, `Mission`, `Owned areas`, `Responsibilities` (+274 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AppError` connect `MonkeyPatch` to `error_handlers.py`, `test_request_logging.py`, `_run_handler`, `session_factory`, `_EnvironmentSettings`, `AuditEvent`, `UnitOfWork`, `SqlAlchemyOperationStore`, `test_openapi_contract.py`, `Operation`, `SqlAlchemyPackageCatalog`, `OperationType`, `ArchiveReader`, `ArtifactStore`, `models.py`, `Path`, `test_artifact_store.py`, `OperationService`, `errors.py`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Why does `AppSettings` connect `AppSettings` to `AppSettings`, `config.py`, `_EnvironmentSettings`, `ConfigurationFailure`, `JsonEventFormatter`, `session_factory`, `ArchiveReader`, `_reject_wildcard_host`, `test_application_boot.py`, `configure_logging`, `ConfigurationIssue`, `MonkeyPatch`, `OperationService`, `create_health_router`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Why does `DatabaseProvider` connect `ArchiveReader` to `ConfigurationFailure`, `AppSettings`, `_run_handler`, `Path`, `AuditEvent`, `UnitOfWork`, `MonkeyPatch`, `OperationService`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Are the 54 inferred relationships involving `AppError` (e.g. with `app_error_handler()` and `register_error_handlers()`) actually correct?**
  _`AppError` has 54 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `AppSettings` (e.g. with `Container` and `JsonEventFormatter`) actually correct?**
  _`AppSettings` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `UnitOfWork` (e.g. with `OperationService` and `PackageDetail`) actually correct?**
  _`UnitOfWork` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `ErrorDetail` (e.g. with `.__post_init__()` and `ArchiveEntry`) actually correct?**
  _`ErrorDetail` has 24 INFERRED edges - model-reasoned connections that need verification._