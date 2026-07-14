# Graph Report - ForgeML  (2026-07-14)

## Corpus Check
- 112 files · ~43,272 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1184 nodes · 2038 edges · 89 communities (72 shown, 17 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 353 edges (avg confidence: 0.72)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4aa140cd`
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

## God Nodes (most connected - your core abstractions)
1. `AppSettings` - 51 edges
2. `AppError` - 47 edges
3. `UnitOfWork` - 44 edges
4. `ErrorDetail` - 43 edges
5. `PackageLimits` - 35 edges
6. `AuditEvent` - 26 edges
7. `ZipArchiveReader` - 26 edges
8. `build_forge()` - 24 edges
9. `load_settings()` - 22 edges
10. `validate_package()` - 22 edges

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

## Communities (89 total, 17 thin omitted)

### Community 0 - "AppSettings"
Cohesion: 0.16
Nodes (13): Frozen HTTP wire contract tests., test_framework_error_wire_shape_omits_empty_details(), test_health_wire_shapes_and_header(), Health endpoint integration tests., test_docs_and_openapi_routes_are_not_public(), test_health_and_readiness_contract(), test_inbound_request_ids_are_ignored(), ASGITestClient (+5 more)

### Community 1 - "error_handlers.py"
Cohesion: 0.12
Nodes (32): app_error_handler(), _detail_response(), error_response(), http_error_handler(), internal_error_response(), Exception, FastAPI, JSONResponse (+24 more)

### Community 2 - "test_request_logging.py"
Cohesion: 0.08
Nodes (32): ASGIApp, Server-owned request correlation and bounded request logging., Own the canonical request ID for one HTTP request., RequestContextMiddleware, current_request_id(), new_request_id(), Request-local server correlation context., Create a canonical server-owned request identifier. (+24 more)

### Community 3 - "ConfigurationFailure"
Cohesion: 0.18
Nodes (23): ConfigurationFailure, load_settings(), Exception, Resolve and validate the installed ForgeML distribution version., Load settings from an explicit mapping or the process environment., Fail-closed configuration error safe to classify at bootstrap., resolve_service_version(), MonkeyPatch (+15 more)

### Community 4 - "JsonEventFormatter"
Cohesion: 0.15
Nodes (19): _bounded(), JsonEventFormatter, LogRecord, Bounded structured process logging., Render a strict allowlisted JSON event., _strip_controls(), BaseException, LogRecord (+11 more)

### Community 5 - "AppError"
Cohesion: 0.05
Nodes (85): ErrorDetail, A bounded, safe detail for an expected application error., ArchiveEntry, ArchiveInspection, ArchiveUnreadable, AssetSpec, EntrypointSection, Finding (+77 more)

### Community 6 - "test_application_boot.py"
Cohesion: 0.14
Nodes (13): CI Status, Current Development Stage, Current Module, Current Version, Engineering Authority, ForgeML Project Status, Frozen Modules, Last Frozen Milestone (+5 more)

### Community 7 - "_run_handler"
Cohesion: 0.08
Nodes (51): Reads .forge archive structure from a seekable binary stream., ZipArchiveReader, _deep_schema(), _encrypted_member(), _non_utf8_name(), Any, Path, The .forge reference fixture matrix.  Each case drives a real archive through th (+43 more)

### Community 8 - "session_factory"
Cohesion: 0.05
Nodes (56): create_database_engine(), create_session_factory(), Engine, Session, sessionmaker, Engine and session factory for the metadata database (ADR-009)., Build the metadata engine from typed settings.      `pool_pre_ping` costs one ro, Session factory for the unit of work.      `expire_on_commit=False` is deliberat (+48 more)

### Community 9 - "test_dependency_direction.py"
Cohesion: 0.32
Nodes (12): _imports(), Path, AST-enforced dependency direction., The ORM is confined to one package.      If SQLAlchemy can be imported anywhere, test_api_never_imports_bootstrap_or_future_modules(), test_application_depends_on_domain_not_providers(), test_bootstrap_imports_core_not_api(), test_domain_depends_on_no_provider_transport_or_filesystem() (+4 more)

### Community 10 - "_reject_wildcard_host"
Cohesion: 0.08
Nodes (24): 10. Design review record, 1. Purpose and scope, 2. Architecture, 3. Folder structure and complete file plan, 4. Technology and dependency decisions, 5. Interfaces, 6. Public HTTP API, 7. Testing and traceability (+16 more)

### Community 11 - "_EnvironmentSettings"
Cohesion: 0.29
Nodes (5): PackageValidationService, Validate a stored .forge artifact against the format version 1 contract., Runs archive validation over a stored artifact.      Asset checksums are the onl, PackageLimits, Operator policy bounding work spent on an untrusted .forge archive.      Every b

### Community 12 - "test_process_signals.py"
Cohesion: 0.67
Nodes (3): _available_loopback_port(), Real-process signal and graceful-shutdown integration., test_sigterm_stops_installed_process_without_traceback()

### Community 18 - "Architecture Decision Records"
Cohesion: 0.12
Nodes (16): ADR-001 — Trusted packages; defense-in-depth runtime isolation, ADR-002 — Modular monolith control plane, ADR-003 — Immutable content-addressed packages/images, ADR-004 — Metadata desired state; Docker reconciliation, ADR-005 — One active version and platform route, ADR-006 — Asynchronous durable operations, ADR-007 — Storage/database behind ports, ADR-008 — Initial runtime compatibility matrix (+8 more)

### Community 19 - "AuditEvent"
Cohesion: 0.05
Nodes (30): ErrorCategory, StrEnum, Transport-neutral classes of expected application failure., ActorType, AuditEvent, StrEnum, Audit events (docs 04: append-only; no payloads, no secrets)., Who caused a state change. (+22 more)

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
Cohesion: 0.17
Nodes (11): Configuration, Dependency locks and package smoke, Forge package contract, ForgeML Backend — Module 0 Foundation, Module 1 Forge Package System, Frozen HTTP and correlation contracts, Known limitations, Logging contract, Quality gates (+3 more)

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
Cohesion: 0.18
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
Cohesion: 0.18
Nodes (16): LoggingConfigurationConflict, Raised when process logging is reconfigured incompatibly., FakeServer, BaseException, LogCaptureFixture, MonkeyPatch, Bootstrap and composition integration tests., test_configuration_failure_is_safe_and_exits_two() (+8 more)

### Community 53 - "test_openapi_contract.py"
Cohesion: 0.08
Nodes (30): AppError, Exception, Provider-neutral application error contracts., An immutable expected application failure., _validate_code(), _validate_message(), artifact_uri(), FilesystemArtifactStore (+22 more)

### Community 62 - "OperationStore"
Cohesion: 0.14
Nodes (11): OperationStore, Any, Protocol, UUID, The durable operation store (ADR-006, ADR-010, ADR-016)., Durable operations, claimed by one worker at a time.      This store is the queu, Create the operation, or return the original one for a repeated request., Claim the oldest pending operation, or None.          `types` selects a lane. Wi (+3 more)

### Community 63 - "_NoAliasLoader"
Cohesion: 0.18
Nodes (10): _NoAliasLoader, Any, BinaryIO, ZipInfo, ZIP adapter for .forge archives.  This is the only module that knows a .forge fi, Safe YAML loader that also refuses aliases.      yaml.safe_load still expands al, _to_entry(), _unsafe_member() (+2 more)

### Community 64 - "create_application"
Cohesion: 0.14
Nodes (13): APIRouter, create_health_router(), Operational health routes., Create health routes bound to immutable service identity., create_application(), FastAPI, FastAPI application composition root., Create an isolated Module 0 application without provider side effects. (+5 more)

### Community 65 - "config.py"
Cohesion: 0.14
Nodes (13): ConfigurationIssue, Environment, LogLevel, StrEnum, ValidationError, Typed, fail-closed Module 0 configuration., The metadata database URL, or a fail-closed configuration error.          Module, Supported deployment environments. (+5 more)

### Community 66 - "Operation"
Cohesion: 0.27
Nodes (7): Operation, One durable unit of asynchronous work., InMemoryOperationStore, InMemoryPackageCatalog, Any, UUID, In-memory implementations of the Module 2 ports.  Module 3 will test its use cas

### Community 67 - "SqlAlchemyPackageCatalog"
Cohesion: 0.20
Nodes (6): Package, A stored package. Checksum and artifact are immutable (ADR-003).      manifest_v, PackageRow, Session, Package records backed by PostgreSQL., SqlAlchemyPackageCatalog

### Community 68 - "AppSettings"
Cohesion: 0.23
Nodes (11): AppSettings, Immutable settings consumed by composition and bootstrap., _client_with_failure_routes(), Payload, BaseModel, LogCaptureFixture, HTTP error normalization tests., test_404_and_405_use_frozen_envelope() (+3 more)

### Community 69 - "OperationType"
Cohesion: 0.19
Nodes (9): OperationFailure, OperationState, OperationType, StrEnum, Durable operation records (ADR-006).  An operation is the durable intent behind, The kinds of durable work the control plane performs.      Only the package oper, Operation lifecycle. SUCCEEDED and FAILED are terminal and immutable., A safe, classified failure. Never a trace, a host path, or a payload. (+1 more)

### Community 70 - "SqlAlchemyUnitOfWork"
Cohesion: 0.16
Nodes (7): BaseException, Session, sessionmaker, TracebackType, The SQLAlchemy unit of work: one session, one transaction, three repositories., One atomic metadata transaction.      All three repositories are built from the, SqlAlchemyUnitOfWork

### Community 71 - "PackageCatalog"
Cohesion: 0.18
Nodes (8): PackageCatalog, UUID, Durable package records. Duplicate checksums resolve to one package., Return the package for these bytes, creating it in DRAFT if absent.          Sto, Read one package by its opaque identifier., Read one package by the SHA-256 of its bytes., Persist a validation result and transition the package accordingly.          Rai, Read the validation history of one package, newest first.

### Community 72 - "main"
Cohesion: 0.21
Nodes (10): main(), Exception, _raise_shutdown_requested(), Fail-closed ForgeML process bootstrap., Translate Uvicorn's re-raised SIGTERM into a clean process exit., Validate configuration and run the single ForgeML ASGI worker., _safe_bootstrap_failure(), _ShutdownRequested (+2 more)

### Community 73 - "ArchiveReader"
Cohesion: 0.20
Nodes (8): ArchiveReader, BinaryIO, Protocol, Extract the archive into a fresh, empty staging directory., Open a stored artifact for reading., Reads .forge archive structure without importing or executing its content., Read member headers and the manifest document.          Raises ArchiveUnreadable, Compute the SHA-256 of the named members, reading bounded bytes only.

### Community 74 - "test_invariants.py"
Cohesion: 0.35
Nodes (11): _insert_package(), Engine, Invariants the database enforces, independently of our repositories.  These test, test_a_package_artifact_cannot_be_repointed(), test_a_package_cannot_have_zero_size(), test_a_package_checksum_cannot_be_rewritten(), test_a_package_state_may_still_advance(), test_a_terminal_operation_cannot_be_rewritten() (+3 more)

### Community 75 - "_run_handler"
Cohesion: 0.24
Nodes (10): Exception, JSONResponse, Direct error-mapping branch tests., _run_handler(), test_mismatched_registered_handler_inputs_fail_safe(), test_non_json_validation_error_without_location_is_safe(), test_terminal_error_handlers_are_generic(), test_unapproved_http_status_fails_safe() (+2 more)

### Community 76 - "ArtifactStore"
Cohesion: 0.22
Nodes (7): ArtifactStore, Ports owned by the package domain.  Callers never receive a filesystem path. An, An immutable, content-addressed archive held by the artifact store., Streaming, content-addressed, atomically written artifact storage., Store the stream, returning its identity. Writing the same bytes twice         i, Delete a stored artifact. Deleting an absent artifact is not an error., StoredArtifact

### Community 77 - "test_package_limits.py"
Cohesion: 0.22
Nodes (8): installed_version(), MonkeyPatch, Package limits are operator policy loaded through the fail-closed loader., test_an_invalid_limit_fails_closed(), test_defaults_bound_every_dimension_of_an_untrusted_archive(), test_limits_are_immutable(), test_limits_are_overridable_from_the_environment(), test_limits_that_contradict_each_other_are_rejected()

### Community 78 - "_database_url"
Cohesion: 0.32
Nodes (7): _database_url(), Alembic environment.  The database URL comes from the same typed, fail-closed co, The URL supplied by the caller, else the application's own configuration.      T, Emit SQL without a connection, so an operator can review DDL first., Run migrations against a live database., run_migrations_offline(), run_migrations_online()

### Community 79 - "event"
Cohesion: 0.39
Nodes (6): event(), Domain records for the metadata layer., test_a_well_formed_audit_event_is_accepted(), test_audit_metadata_is_bounded(), test_unsafe_audit_metadata_is_refused(), test_unsafe_audit_text_is_refused()

### Community 80 - "models.py"
Cohesion: 0.33
Nodes (4): Base, PackageValidationRow, SQLAlchemy mappings. The only ORM classes in ForgeML.  Nothing here leaves this, DeclarativeBase

### Community 81 - "_reject_wildcard_host"
Cohesion: 0.33
Nodes (5): _reject_wildcard_host(), Shared Module 0 test fixtures., settings(), IPv4Address, IPv6Address

### Community 83 - "PackagePage"
Cohesion: 0.40
Nodes (3): PackagePage, One page of packages, newest first., List packages newest first, bounded by limit.

### Community 85 - "configure_logging"
Cohesion: 0.50
Nodes (4): configure_logging(), Configure process logging once for an immutable settings fingerprint., MonkeyPatch, test_configure_logging_is_idempotent_and_rejects_conflict()

## Knowledge Gaps
- **244 isolated node(s):** `forgeml`, `graphify`, `Mission`, `Owned areas`, `Responsibilities` (+239 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AppError` connect `test_openapi_contract.py` to `error_handlers.py`, `Operation`, `SqlAlchemyPackageCatalog`, `AppSettings`, `OperationType`, `test_request_logging.py`, `_run_handler`, `session_factory`, `AuditEvent`, `PackagePage`, `UnitOfWork`, `SqlAlchemyOperationStore`, `_NoAliasLoader`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Why does `AppSettings` connect `AppSettings` to `create_application`, `config.py`, `AppSettings`, `ConfigurationFailure`, `JsonEventFormatter`, `test_request_logging.py`, `session_factory`, `_reject_wildcard_host`, `_EnvironmentSettings`, `test_application_boot.py`, `configure_logging`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Why does `PackageLimits` connect `_EnvironmentSettings` to `config.py`, `AppError`, `PackageCatalog`, `_run_handler`, `ArchiveReader`, `ArtifactStore`, `test_package_limits.py`, `_EnvironmentSettings`, `PackagePage`, `test_openapi_contract.py`, `_NoAliasLoader`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `AppSettings` (e.g. with `JsonEventFormatter` and `LoggingConfigurationConflict`) actually correct?**
  _`AppSettings` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 39 inferred relationships involving `AppError` (e.g. with `app_error_handler()` and `register_error_handlers()`) actually correct?**
  _`AppError` has 39 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `UnitOfWork` (e.g. with `AuditLog` and `SqlAlchemyUnitOfWork`) actually correct?**
  _`UnitOfWork` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `ErrorDetail` (e.g. with `.__post_init__()` and `ArchiveEntry`) actually correct?**
  _`ErrorDetail` has 24 INFERRED edges - model-reasoned connections that need verification._