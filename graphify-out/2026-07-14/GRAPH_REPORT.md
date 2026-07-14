# Graph Report - ForgeML  (2026-07-14)

## Corpus Check
- 87 files · ~33,563 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 832 nodes · 1348 edges · 57 communities (45 shown, 12 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 247 edges (avg confidence: 0.72)
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
- Module 0 Completion Report
- Module 1 — Forge Package System Design
- Module 0 Architecture Clarification Report
- ForgeML Backend — Module 0 Foundation, Module 1 Forge Package System
- Operations and Security
- Project Charter
- Product Requirements
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
- test_openapi_contract.py
- __init__.py
- __init__.py
- __init__.py
- __init__.py
- __init__.py
- CLAUDE.md
- __init__.py

## God Nodes (most connected - your core abstractions)
1. `AppSettings` - 48 edges
2. `ErrorDetail` - 37 edges
3. `PackageLimits` - 33 edges
4. `ZipArchiveReader` - 30 edges
5. `AppError` - 25 edges
6. `build_forge()` - 24 edges
7. `validate_package()` - 22 edges
8. `FilesystemArtifactStore` - 22 edges
9. `create_application()` - 19 edges
10. `JsonEventFormatter` - 18 edges

## Surprising Connections (you probably didn't know these)
- `test_limits_are_immutable()` --calls--> `PackageLimits`  [INFERRED]
  backend/tests/unit/core/test_package_limits.py → backend/src/forgeml/core/config.py
- `test_limits_that_contradict_each_other_are_rejected()` --calls--> `PackageLimits`  [INFERRED]
  backend/tests/unit/core/test_package_limits.py → backend/src/forgeml/core/config.py
- `test_details_must_be_typed()` --calls--> `AppError`  [INFERRED]
  backend/tests/unit/core/test_errors.py → backend/src/forgeml/core/errors.py
- `_request_id()` --calls--> `current_request_id()`  [INFERRED]
  backend/src/forgeml/api/error_handlers.py → backend/src/forgeml/core/correlation.py
- `_request_id()` --calls--> `new_request_id()`  [INFERRED]
  backend/src/forgeml/api/error_handlers.py → backend/src/forgeml/core/correlation.py

## Import Cycles
- None detected.

## Communities (57 total, 12 thin omitted)

### Community 0 - "AppSettings"
Cohesion: 0.06
Nodes (51): create_application(), FastAPI, FastAPI application composition root., Create an isolated Module 0 application without provider side effects., AppSettings, Immutable settings consumed by composition and bootstrap., Frozen HTTP wire contract tests., test_framework_error_wire_shape_omits_empty_details() (+43 more)

### Community 1 - "error_handlers.py"
Cohesion: 0.10
Nodes (36): APIRouter, app_error_handler(), _detail_response(), error_response(), http_error_handler(), internal_error_response(), Exception, FastAPI (+28 more)

### Community 2 - "test_request_logging.py"
Cohesion: 0.08
Nodes (32): ASGIApp, Server-owned request correlation and bounded request logging., Own the canonical request ID for one HTTP request., RequestContextMiddleware, current_request_id(), new_request_id(), Request-local server correlation context., Create a canonical server-owned request identifier. (+24 more)

### Community 3 - "ConfigurationFailure"
Cohesion: 0.08
Nodes (42): ConfigurationFailure, ConfigurationIssue, Environment, load_settings(), LogLevel, Exception, StrEnum, ValidationError (+34 more)

### Community 4 - "JsonEventFormatter"
Cohesion: 0.06
Nodes (45): main(), Exception, _raise_shutdown_requested(), Fail-closed ForgeML process bootstrap., Translate Uvicorn's re-raised SIGTERM into a clean process exit., Validate configuration and run the single ForgeML ASGI worker., _safe_bootstrap_failure(), _ShutdownRequested (+37 more)

### Community 5 - "AppError"
Cohesion: 0.06
Nodes (76): ErrorDetail, A bounded, safe detail for an expected application error., ArchiveEntry, ArchiveInspection, AssetSpec, EntrypointSection, Finding, is_supported_schema_dialect() (+68 more)

### Community 6 - "test_application_boot.py"
Cohesion: 0.14
Nodes (13): CI Status, Current Development Stage, Current Module, Current Version, Engineering Authority, ForgeML Project Status, Frozen Modules, Last Frozen Milestone (+5 more)

### Community 7 - "_run_handler"
Cohesion: 0.06
Nodes (63): ArchiveUnreadable, Exception, The bytes are not a readable ZIP container at all., _NoAliasLoader, Any, BinaryIO, ZipInfo, ZIP adapter for .forge archives.  This is the only module that knows a .forge fi (+55 more)

### Community 9 - "test_dependency_direction.py"
Cohesion: 0.38
Nodes (10): _imports(), Path, AST-enforced dependency direction., test_api_never_imports_bootstrap_or_future_modules(), test_application_depends_on_domain_not_providers(), test_bootstrap_imports_core_not_api(), test_domain_depends_on_no_provider_transport_or_filesystem(), test_no_package_path_can_import_or_deserialize_package_content() (+2 more)

### Community 10 - "_reject_wildcard_host"
Cohesion: 0.08
Nodes (24): 10. Design review record, 1. Purpose and scope, 2. Architecture, 3. Folder structure and complete file plan, 4. Technology and dependency decisions, 5. Interfaces, 6. Public HTTP API, 7. Testing and traceability (+16 more)

### Community 11 - "_EnvironmentSettings"
Cohesion: 0.09
Nodes (22): PackageValidationService, Validate a stored .forge artifact against the format version 1 contract., Runs archive validation over a stored artifact.      Asset checksums are the onl, _EnvironmentSettings, PackageLimits, BaseModel, Operator policy bounding work spent on an untrusted .forge archive.      Every b, ArchiveReader (+14 more)

### Community 12 - "test_process_signals.py"
Cohesion: 0.67
Nodes (3): _available_loopback_port(), Real-process signal and graceful-shutdown integration., test_sigterm_stops_installed_process_without_traceback()

### Community 18 - "Architecture Decision Records"
Cohesion: 0.12
Nodes (16): ADR-001 — Trusted packages; defense-in-depth runtime isolation, ADR-002 — Modular monolith control plane, ADR-003 — Immutable content-addressed packages/images, ADR-004 — Metadata desired state; Docker reconciliation, ADR-005 — One active version and platform route, ADR-006 — Asynchronous durable operations, ADR-007 — Storage/database behind ports, ADR-008 — Initial runtime compatibility matrix (+8 more)

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

### Community 53 - "test_openapi_contract.py"
Cohesion: 0.10
Nodes (26): AppError, ErrorCategory, Exception, StrEnum, Provider-neutral application error contracts., Transport-neutral classes of expected application failure., An immutable expected application failure., _validate_code() (+18 more)

## Knowledge Gaps
- **244 isolated node(s):** `forgeml`, `graphify`, `Mission`, `Owned areas`, `Responsibilities` (+239 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AppSettings` connect `AppSettings` to `error_handlers.py`, `test_request_logging.py`, `ConfigurationFailure`, `JsonEventFormatter`, `_EnvironmentSettings`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Why does `PackageLimits` connect `_EnvironmentSettings` to `test_openapi_contract.py`, `ConfigurationFailure`, `AppError`, `_run_handler`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Why does `ErrorDetail` connect `AppError` to `AppSettings`, `error_handlers.py`, `test_openapi_contract.py`, `_run_handler`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `AppSettings` (e.g. with `JsonEventFormatter` and `LoggingConfigurationConflict`) actually correct?**
  _`AppSettings` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `ErrorDetail` (e.g. with `.__post_init__()` and `ArchiveEntry`) actually correct?**
  _`ErrorDetail` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `PackageLimits` (e.g. with `PackageValidationService` and `ArchiveReader`) actually correct?**
  _`PackageLimits` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `ZipArchiveReader` (e.g. with `PackageLimits` and `AppError`) actually correct?**
  _`ZipArchiveReader` has 8 INFERRED edges - model-reasoned connections that need verification._