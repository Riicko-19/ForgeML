# Module 0 — Foundation Design

**Status:** FROZEN — design review iteration 3 PASS  
**Implementation owner:** Backend Engineer  
**Architecture owner:** Chief Architect  
**Reviewers:** Backend, Security, QA, Documentation  
**Authority:** FEK documents 00–12, approved AC-001 through AC-004, EEP, and EAP

## 1. Purpose and scope

Module 0 creates the smallest executable backend foundation: typed configuration,
process bootstrap, application composition, safe HTTP errors, server-generated request
correlation, structured logging, liveness/readiness endpoints, reproducible dependency
inputs, CI, and test/quality gates.

It contains no package, model, database, Docker, worker, deployment, routing, monitoring,
authentication, authorization, frontend, or provider implementation.

### Scope audit

| ID | V1 requirement | FEK authority | Result |
| --- | --- | --- | --- |
| M0-R01 | Typed, fail-closed configuration | docs 06, 09, 11 | Included |
| M0-R02 | Explicit composition root with no provider side effects | docs 02, 05, 06 | Included |
| M0-R03 | Common error envelope and safe mappings | docs 07, 12 | Included |
| M0-R04 | Structured logs and request correlation | docs 01, 07, 11 | Included |
| M0-R05 | Liveness/readiness endpoints | docs 06, 12 | Included |
| M0-R06 | Unit, integration, contract, architecture, and smoke tests | docs 05–08 | Included |
| M0-R07 | Black, Ruff, mypy, lock, and CI gates | docs 06–08; AC-002 | Included |
| M0-R08 | Python 3.11-only control plane | AC-001 | Included |
| M0-R09 | No V2 feature or speculative provider abstraction | EEP/EAP | Included |

No Kubernetes, cloud orchestration, multi-node behavior, broker, distributed worker,
Redis, MLOps platform, multi-tenancy, RBAC, billing, notifications, autoscaling, GPU,
LLM, plugin, marketplace, or future-provider scaffold is present.

## 2. Architecture

### Responsibilities

1. **Configuration:** convert the Module 0 FORGEML environment namespace into one
   immutable typed settings value.
2. **Composition:** create an isolated FastAPI application from explicit settings.
3. **Process bootstrap:** validate environment settings, configure logging once, create
   the app, and run one Uvicorn worker.
4. **HTTP foundation:** install request-correlation middleware, safe error handlers,
   and health routes.
5. **Quality foundation:** provide reproducible dependencies and automated local/CI
   gates.

### Construction and startup

~~~mermaid
sequenceDiagram
  participant Entry as __main__
  participant Bootstrap as process bootstrap
  participant Config as settings loader
  participant Logging as logging setup
  participant Compose as core composition
  participant Server as Uvicorn
  Entry->>Bootstrap: main()
  Bootstrap->>Config: load Module 0 environment
  alt invalid settings
    Config-->>Bootstrap: sanitized ConfigurationFailure
    Bootstrap-->>Entry: fixed safe JSON stderr event; exit 2
  else valid settings
    Config-->>Bootstrap: immutable AppSettings
    Bootstrap->>Logging: configure once
    Bootstrap->>Compose: create_application(settings)
    Compose-->>Bootstrap: isolated FastAPI app
    Bootstrap->>Server: run one worker
  end
~~~

Application construction performs no environment read, global logging mutation,
network call, filesystem or package-metadata lookup, or provider initialization.
Process bootstrap owns all process-global work, including version resolution.

### Dependency direction

~~~mermaid
flowchart LR
  MAIN[__main__] --> BOOT[bootstrap]
  BOOT --> CONFIG[core.config]
  BOOT --> LOG[core.logging]
  BOOT --> COMPOSE[core.composition]
  COMPOSE --> API[api routes/handlers/middleware]
  API --> SCHEMAS[api.schemas]
  API --> ERRORS[core.errors]
  API --> CORR[core.correlation]
  LOG --> CORR
~~~

- api may import provider-neutral core contracts.
- core.config, core.errors, core.correlation, and core.logging do not import FastAPI.
- core.composition is the sole core module allowed to import API registration functions
  and FastAPI because FEK assigns composition to core.
- bootstrap is a process adapter and imports core only.
- No module imports a future domain, application, or infrastructure package.
- An AST-based architecture test enforces this matrix without another dependency.

Composition functions and aggregate settings are internal Python surfaces that may
grow additively as later FEK modules are composed. Frozen Module 0 surfaces are the
operator configuration keys and HTTP/error/log schemas listed below.

## 3. Folder structure and complete file plan

Implementation root is /home/og-abijith/ForgeML. The FEK remains in its existing
documentation bundle.

~~~text
.gitignore
.github/
  workflows/
    backend-quality.yml
ForgeML_Engineering_Kit_Phase0/
  README.md
  docs/
    06_IMPLEMENTATION_ROADMAP.md
    13_MODULE0_FOUNDATION_DESIGN.md
    14_MODULE0_ARCHITECTURE_CLARIFICATION.md
    15_MODULE0_COMPLETION_REPORT.md
    16_MODULE0_SCOPE_VERIFICATION_REPORT.md
    17_MODULE0_TEST_REPORT.md
backend/
  README.md
  pyproject.toml
  requirements.lock
  requirements-dev.lock
  src/
    forgeml/
      __init__.py
      __main__.py
      bootstrap.py
      api/
        __init__.py
        error_handlers.py
        health.py
        middleware.py
        schemas.py
      core/
        __init__.py
        composition.py
        config.py
        correlation.py
        errors.py
        logging.py
  tests/
    conftest.py
    support.py
    unit/
      api/
        test_error_handlers.py
      core/
        test_config.py
        test_correlation.py
        test_errors.py
        test_logging.py
    integration/
      api/
        test_application_boot.py
        test_error_handling.py
        test_health.py
        test_process_signals.py
        test_request_logging.py
    contract/
      test_http_contract.py
      test_openapi_contract.py
    architecture/
      test_dependency_direction.py
    smoke/
      installed_package_smoke.py
~~~

| File/group | Purpose |
| --- | --- |
| .gitignore | Exclude virtual environments, caches, builds, coverage, and local settings. |
| backend-quality.yml | Enforce the exact local quality gates on Python 3.11. |
| FEK README/docs 06, 13, 14 | Index, roadmap, approved design/clarification, freeze state. |
| FEK docs 15, 16, 17 | Completion, scope verification, and executed test reports; Documentation and QA own updates. |
| pyproject.toml | Canonical direct dependencies, package metadata, and tool policy. |
| requirements.lock | Hashed complete runtime dependency graph generated from pyproject. |
| requirements-dev.lock | Hashed complete runtime plus development graph generated from pyproject dev extra. |
| backend/README.md | Setup, configuration, commands, contracts, boundaries, and limitations. |
| forgeml package markers | Package version/export policy; no behavior or side effects. |
| __main__.py | Thin delegate to bootstrap.main; no configuration or framework logic. |
| bootstrap.py | Safe startup failure, one-time logging, Uvicorn process configuration. |
| core/composition.py | Pure create_application(settings) composition root. |
| core/config.py | AppSettings, parsing rules, and sanitized ConfigurationFailure. |
| core/correlation.py | Request-local server request ID context access/reset. |
| core/errors.py | Immutable provider-neutral AppError and ErrorDetail contracts. |
| core/logging.py | JSON event formatting, allowlisting, and one-time process setup. |
| api/schemas.py | Exact health, ErrorEnvelope, and ErrorDetail transport schemas. |
| api/middleware.py | Server request ID lifecycle and bounded request-completion event. |
| api/error_handlers.py | Framework/application error-to-envelope mapping. |
| api/health.py | GET /healthz and GET /readyz. |
| tests, including support.py | Requirement-linked unit, integration, contract, architecture, and minimal in-process ASGI HTTP evidence. |

No empty application/domain/infrastructure directories, generic utilities module,
deployment artifact, provider port, or placeholder file is created.

## 4. Technology and dependency decisions

### Runtime and build

| Item | Decision | Justification |
| --- | --- | --- |
| Python | CPython >=3.11,<3.12 | Approved AC-001; one backend/runtime minor line. |
| HTTP | FastAPI | FEK mandate. |
| Validation/settings | Pydantic v2 | FEK typed boundary; direct mapping validation prevents ambient settings sources. |
| ASGI | Plain Uvicorn, without optional standard extras | Single-process HTTP boot without reload, dotenv, WebSocket, alternate loop/parser, or watcher dependencies. |
| Logging | Python standard logging | Avoid an unnecessary logging framework. |
| Build backend | setuptools | Standard minimal backend with no project-specific build system. |
| Dependency source | pyproject.toml | One authoritative list of direct runtime/dev dependencies. |
| Locks | pip-tools generated hashed lock files | Reproducible complete installs; locks are generated artifacts. |

Runtime direct dependencies are FastAPI, Pydantic, and Uvicorn.
Development direct dependencies are pytest, HTTPX, Black, Ruff, mypy, coverage.py,
pip-tools, and build. Setuptools is a build-system requirement. No other direct
dependency is approved.

Black alone owns formatting. Ruff owns linting and import checks. Mypy owns static
typing. Coverage.py measures branch coverage. Exact compatible versions are selected
and pinned together during implementation; changing a direct dependency requires the
EAP dependency review.

Lock workflow:

1. Edit direct dependency constraints only in pyproject.toml.
2. Generate requirements.lock with: python -m piptools compile pyproject.toml
   --resolver=backtracking --generate-hashes --strip-extras --no-header
   --no-emit-index-url --output-file requirements.lock.
3. Generate requirements-dev.lock with the same flags plus --extra dev,
   --all-build-deps, and --allow-unsafe so the pinned setuptools build requirement is
   included, writing requirements-dev.lock.
4. Install using the relevant lock with hash enforcement.
5. Regenerate into temporary files in CI and compare byte-for-byte with committed
   locks; drift fails CI.

### Process policy

The supported process entry is python -m forgeml. Module 0 process settings are:

| Environment key | Type/default | Rule |
| --- | --- | --- |
| FORGEML_ENVIRONMENT | required: development, test, production | Trimmed lower-case value; empty/unknown fails. |
| FORGEML_LOG_LEVEL | INFO default; DEBUG/INFO/WARNING/ERROR/CRITICAL | Trimmed upper-case value. |
| FORGEML_BIND_HOST | 127.0.0.1 default | Non-empty IP address only; hostname/wildcard requires later deployment approval. |
| FORGEML_BIND_PORT | 8000 default | Integer 1–65535. |
| FORGEML_GRACEFUL_SHUTDOWN_SECONDS | 30 default | Integer 1–300. |

Logging is JSON-only in every environment. Configuration names are case-sensitive. Values are trimmed before enum/numeric
validation; an empty value is invalid, not a default request. Unknown FORGEML-prefixed
keys fail startup in Module 0. The environment is the only production configuration
source. Tests may pass an explicit settings object to composition. No .env file,
command-line override, reload mode, or proxy-header trust is supported.

Uvicorn runs one worker, reload disabled, proxy headers disabled, access logging
disabled, and uses the configured graceful shutdown. SIGINT/SIGTERM initiate graceful
shutdown and return process exit 0 when clean. Configuration failure exits 2; bind or
unexpected server startup failure exits 1 after a safe structured event.

## 5. Interfaces

Names are descriptive typed contracts, not implementation code.

### Internal composition interfaces

| Interface | Inputs | Result/failure |
| --- | --- | --- |
| load_settings | Environment mapping or process environment | Immutable AppSettings; raises sanitized ConfigurationFailure. |
| create_application | Required AppSettings | New isolated FastAPI application; does not configure logging. |
| bootstrap.main | No arguments | Integer process exit code; owns logging/server lifecycle. |
| configure_logging | Required AppSettings | First call configures; same fingerprint is a no-op; conflicting fingerprint raises LoggingConfigurationConflict. |

Logging configuration is tested in isolated subprocesses; no production test-reset
interface exists. Its fingerprint is exactly the immutable tuple (service_name,
service_version, environment, log_level). create_application never calls
configure_logging.

Service identity is fixed as forgeml-control-plane. Bootstrap resolves service_version
only from installed distribution metadata for package forgeml. The value must be 1–64
printable ASCII characters containing only letters, digits, period, plus, hyphen, or
exclamation mark. Missing or invalid metadata raises ConfigurationFailure with safe
code service_metadata_unavailable; bootstrap emits event configuration_invalid without
the underlying exception/message/metadata and exits 2. There is no development
fallback. Tests and pure composition pass an explicit valid service_version in
AppSettings.

### Provider-neutral error interfaces

ErrorDetail is immutable and contains required code and message plus optional path.
Path is an ordered tuple of string or non-negative integer segments. AppError is
immutable and contains code, safe message, one ErrorCategory, and an immutable tuple
of details. Neither contains HTTP status, exception object, raw provider output, or
request data.

The exact current ErrorCategory values are BAD_REQUEST, NOT_FOUND, CONFLICT,
VALIDATION, POLICY_LIMIT, UPSTREAM_FAILURE, DEPENDENCY_UNAVAILABLE, and INTERNAL,
mapped respectively to 400, 404, 409, 422, 429, 502, 503, and 500. The enum may grow
additively after FEK review. An exception that is not a valid AppError, including an
unrecognized category from an incompatible object, follows the unexpected 500 path.

Codes must match lower snake case [a-z][a-z0-9_]{0,63}. Messages contain 1–512 Unicode
characters and no control characters except ordinary spaces. An error has at most 100
details. Each detail follows the same code/message rules and has at most 32 path
segments; string segments are 1–128 characters without control characters and integer
segments are 0–2,147,483,647. Invalid construction raises ValueError before transport.
The API never truncates or repairs an invalid application error.

### Correlation interfaces

ForgeML generates a new UUIDv4 for every HTTP request. Inbound X-Request-ID headers,
including duplicates, are ignored and never logged. The server ID is stored in
request-local context, available through a read-only current_request_id accessor,
returned as X-Request-ID on every response, and cleared using its context token after
success, handled failure, unexpected failure, or cancellation.

### Structured event interface

Each JSON log line has exactly these base fields:

| Field | Type | Rule |
| --- | --- | --- |
| timestamp | string | UTC RFC 3339 with microseconds and Z suffix |
| severity | string | DEBUG/INFO/WARNING/ERROR/CRITICAL |
| service | string | forgeml-control-plane |
| version | string | Installed distribution version |
| environment | string | Configured environment |
| component | string | Sanitized logger name, 1–128 characters |
| event | string | Lower snake case, 1–64 characters |
| message | string | Allowlisted safe summary, 1–512 characters |
| request_id | UUID string, omitted | Present only in request context |

Oversized component and message values are truncated deterministically to the maximum,
using the final three characters for ellipsis. Invalid event names are replaced with
invalid_log_event. Optional identifiers are allowlisted later by their owning modules.
Generic exception events may include exception_type only, sanitized and truncated to
128 characters; exception message, args, repr, traceback, host path, environment dump,
raw URL/query, headers, and payload are prohibited. Third-party records discard their
message and arguments and are normalized to event=third_party_event and fixed message
Third-party log event suppressed. Uvicorn access logs are disabled.

One request_completed event includes method (maximum 16 characters), matched route
template (maximum 256 characters) or unmatched, status_code, non-negative duration_ms
rounded to three decimals, and request_id. It excludes raw target/query and bodies.

### HTTP schemas and mappings

All bodies are JSON UTF-8. Transport schemas reject/omit unknown properties.

HealthResponse has required status, service, and version strings and rejects extra
fields. status is exactly ok for liveness and ready for readiness; service is exactly
forgeml-control-plane; version follows the 1–64-character metadata rule. ErrorDetailResponse has required code/message
and optional path array; path is omitted when absent. ErrorEnvelope has required code,
message, and request_id plus optional non-empty details array; details is omitted when
empty and is never null.

| Condition/category | HTTP | Stable code | Safe message |
| --- | ---: | --- | --- |
| Malformed request syntax/JSON | 400 | request_malformed | Request is malformed. |
| Unknown route/resource at framework boundary | 404 | route_not_found | Resource not found. |
| Unsupported method | 405 | method_not_allowed | Method not allowed. |
| Conflict category | 409 | request_conflict | Request conflicts with current state. |
| Framework/schema validation | 422 | request_validation_failed | Request validation failed. |
| Policy limit category | 429 | policy_limit_exceeded | Request limit exceeded. |
| Unexpected control-plane failure | 500 | internal_error | An unexpected error occurred. |
| Prediction upstream failure | 502 | prediction_runtime_failed | Prediction runtime failed. |
| Dependency unavailable category | 503 | dependency_unavailable | A required service is unavailable. |
| Future readiness false state | 503 | service_not_ready | Service is not ready. |

Application errors may provide a more specific FEK-approved stable code/message while
retaining the category status. Framework 404/405/422 and all 500 responses use the
exact rows above. Validation detail paths are sanitized logical locations, never input
values.

Middleware outermost request-ID handling must cover routing, request validation, known
errors, and unexpected errors so every response includes the same request_id as its
envelope and logs.

## 6. Public HTTP API

Only these operational endpoints are exposed:

| Method/path | Response |
| --- | --- |
| GET /healthz | 200 HealthResponse with status=ok |
| GET /readyz | 200 HealthResponse with status=ready |

A successfully running Module 0 application is always ready because it has no provider
dependency. It does not fabricate a 503 branch. The first later V1 module that adds a
required provider must define readiness ownership while preserving the approved 503
wire contract.

GET bodies are ignored according to HTTP framework semantics; no body-dependent
behavior exists. HEAD is not separately exposed. Other methods receive the standard
405 envelope. Public /openapi.json, /docs, and /redoc routes are disabled. Contract
tests inspect the in-process OpenAPI schema and assert that only the two health paths
exist.

## 7. Testing and traceability

| Requirement | Planned evidence |
| --- | --- |
| M0-R01 | unit config matrix; startup subprocess failures; unknown-key and safe-error tests |
| M0-R02 | isolated app construction; import-side-effect and architecture tests |
| M0-R03 | unit mapper table; HTTP error contract and OpenAPI schema tests |
| M0-R04 | request ID success/error/cancellation/concurrency tests; log allowlist/redaction tests |
| M0-R05 | health integration and schema contract tests |
| M0-R06 | separated unit/integration/contract/architecture suites and package smoke test |
| M0-R07 | exact local commands plus GitHub Actions result |
| M0-R08 | project metadata, CI interpreter, clean Python 3.11 install |
| M0-R09 | pre/post implementation scope scans and dependency inventory |

Negative cases include missing/empty/mixed-case/unknown settings; unavailable package
metadata; repeated/conflicting logging configuration; duplicate/empty/non-ASCII/long
inbound request-ID headers (all ignored); 404/405/422; malformed JSON on a test-only
route; known and unexpected handler failure; context cleanup after success/error/
cancellation; concurrent request isolation; bind failure; SIGTERM; and no raw secret,
path, traceback, query, header, or payload in response/log capture.

Exact gates, executed from backend unless stated:

- python -m black --check src tests
- python -m ruff check src tests
- python -m mypy src tests
- python -m coverage run --branch -m pytest tests/unit tests/integration tests/contract tests/architecture
- python -m coverage report --fail-under=95
- python -m build --no-isolation after installing requirements-dev.lock with
  --require-hashes; setuptools and build are therefore supplied by the locked environment
- create a clean Python 3.11 environment, install requirements.lock with
  --require-hashes, install the wheel with pip --no-deps, change outside the source
  tree, and execute tests/smoke/installed_package_smoke.py
- regenerate both lock files into temporary paths and compare with committed locks

Coverage must be 100% branch coverage for configuration validation, error mapping,
correlation lifecycle, and health behavior; the repository-wide minimum is 95%.
Warnings are errors except a documented dependency warning with owner and expiry.

## 8. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Foundation becomes a shared dumping ground | Only named cross-cutting contracts; architecture review for any addition. |
| Composition signature constrains later modules | Composition is internal and may grow additively; wire/config contracts alone freeze. |
| Process-global logging contaminates app tests | Pure app factory; process-only logging; subprocess logging tests. |
| Raw Uvicorn/exception data bypasses policy | Disable access logs and traceback output; allowlisted formatter/events. |
| Correlation leaks across requests | Context token reset on all paths plus cancellation/concurrency tests. |
| Readiness overstates future providers | Module 0 means composition-ready only; provider readiness must be added by owner. |
| Strict unknown setting keys block later modules | Later modules extend the composed allowlist in their own reviewed design. |
| Lock and pyproject drift | pyproject is sole direct source; hashed locks regenerated and compared in CI. |
| Python 3.11 unavailable locally | Verification must use an isolated approved Python 3.11 environment; absence blocks freeze. |
| CI platform unavailable | Local gates may run, but Module 0 cannot freeze without required CI evidence or approved exception. |

## 9. Acceptance criteria

### Design freeze

- [ ] Chief Architect PASS: FEK, boundaries, dependencies, folder layout.
- [ ] Backend PASS: simplicity, maintainability, exact interfaces.
- [ ] Security PASS: configuration, logs, correlation, public errors.
- [ ] QA PASS: traceability, negative cases, reproducible gates.
- [ ] Documentation PASS: no contradictions or ambiguous contract.

### Implementation completion

- [ ] All M0-R01 through M0-R09 evidence passes.
- [ ] Every planned file exists and no unplanned production file is introduced.
- [ ] No TODO/FIXME, placeholder, fabricated success, duplicated policy, unsafe Any,
      mutable global application state, import cycle, or forbidden import.
- [ ] No secret, traceback, host path, raw query/header/payload, or environment value
      leaks through logs or responses.
- [ ] Locks, build, clean Python 3.11 install, local quality gates, and CI pass.
- [ ] Backend README, FEK decisions, reports, and implementation remain synchronized.
- [ ] Final V2 scan reports none and no dependency exists for hypothetical future work.

## 10. Design review record

| Review | Iteration 1 | Iteration 2 | Iteration 3 |
| --- | --- | --- | --- |
| Scope audit | PASS | PASS | PASS |
| Chief Architect | FAIL — clarification | FAIL — dependency/log/version precision | PASS |
| Backend maintainability | FAIL — contracts missing | FAIL — deterministic policies | PASS |
| Security | FAIL — logging/trust | FAIL — third-party/error boundaries | PASS |
| QA | FAIL — evidence incomplete | FAIL — bounds/build/reports | PASS |
| Documentation | FAIL — FEK conflicts | FAIL — exact interface gaps | PASS |

All iteration-3 reviews passed. This design is frozen before implementation. Changes
require a bug fix, approved architecture change, or documented interface-preserving
refactor under the EEP/EAP.
