# ForgeML Backend — Module 0 Foundation

This backend currently implements only the frozen Module 0 foundation: typed startup
configuration, explicit application composition, safe errors, server-owned request
IDs, bounded JSON logs, health endpoints, and quality gates.

It does not contain package, database, Docker, deployment, worker, routing, monitoring,
authentication, frontend, or other later-module behavior.

## Requirements

- CPython 3.11
- Runtime dependencies installed from requirements.lock with hash enforcement
- Development dependencies installed from requirements-dev.lock with hash enforcement

The pyproject file is authoritative for direct dependencies. Lock files are generated
with pip-tools using the exact commands in the frozen Module 0 design.

## Configuration

| Variable | Required/default | Constraint |
| --- | --- | --- |
| FORGEML_ENVIRONMENT | Required | development, test, or production |
| FORGEML_LOG_LEVEL | INFO | DEBUG, INFO, WARNING, ERROR, or CRITICAL |
| FORGEML_BIND_HOST | 127.0.0.1 | Non-wildcard IP address; 0.0.0.0 and :: are rejected |
| FORGEML_BIND_PORT | 8000 | 1–65535 |
| FORGEML_GRACEFUL_SHUTDOWN_SECONDS | 30 | 1–300 |

Configuration names are case-sensitive. Empty values and unknown FORGEML-prefixed
keys fail startup. ForgeML reads no environment file automatically.

## Running

From an environment containing the installed package:

    FORGEML_ENVIRONMENT=development python -m forgeml

The process uses one Uvicorn worker, disables reload, proxy-header trust, and Uvicorn
access logs, and emits JSON logs only.

Operational endpoints:

- GET /healthz
- GET /readyz

Interactive docs and public OpenAPI routes are disabled in Module 0.

## Frozen HTTP and correlation contracts

Successful health responses contain only status, service, and version. Every response,
including an error, has a server-generated UUIDv4 X-Request-ID header. Inbound
X-Request-ID values are removed before routing and are never reflected or logged.

Errors contain code, message, request_id, and optional non-empty details. Empty details
are omitted, never null. Framework mappings are: malformed request 400, missing route
404, method not allowed 405, validation 422, unexpected control-plane failure 500,
upstream prediction failure 502, and unavailable dependency/readiness 503. Every 500
uses code internal_error and message “An unexpected error occurred.”

Error codes are lower snake case up to 64 characters. Safe messages are limited to 512
characters; details are limited to 100 and logical paths to 32 bounded segments. The
authoritative bounds and mappings are in the frozen Module 0 design.

## Logging contract

Logging is JSON-only. Base event fields are timestamp, severity, service, version,
environment, component, event, message, and request_id when a request is active.
Unknown third-party logger messages and arguments are suppressed. Raw URLs, queries,
headers, payloads, exception messages, tracebacks, environment dumps, and host paths
are prohibited. Uvicorn access logs are disabled; ForgeML emits one bounded
request_completed event using the matched route template.

## Startup and exit codes

- 0: clean server shutdown, including SIGINT or SIGTERM.
- 1: logging, composition, bind, server construction, or startup failure.
- 2: invalid configuration or unavailable installed package metadata.

Startup failures emit fixed safe events without raw configuration values or traces.

## Dependency locks and package smoke

pyproject.toml is the sole direct-dependency source. Generate the runtime lock with:

    python -m piptools compile pyproject.toml --resolver=backtracking --generate-hashes --strip-extras --no-header --no-emit-index-url --output-file requirements.lock

Generate the development/build lock with:

    python -m piptools compile pyproject.toml --resolver=backtracking --generate-hashes --strip-extras --no-header --no-emit-index-url --extra dev --all-build-deps --allow-unsafe --output-file requirements-dev.lock

Install locks with --require-hashes. Build with python -m build --no-isolation after
installing the development lock. The clean smoke gate installs the runtime lock, then
the wheel with --no-deps, changes outside the source tree, and runs
tests/smoke/installed_package_smoke.py.

## Quality gates

Run from backend:

    python -m black --check src tests
    python -m ruff check src tests
    python -m mypy src tests
    python -m coverage run --branch -m pytest tests/unit tests/integration tests/contract tests/architecture
    python -m coverage report --fail-under=95
    python -m build --no-isolation

The GitHub Actions backend-quality workflow runs the same gates with Python 3.11.

## Known limitations

Module 0 readiness means configuration and application composition succeeded; no
provider exists yet. The control plane must remain behind the protected administrative
network. Package APIs, database, Docker, workers, routing, monitoring, frontend, and
authentication are later V1 modules. No V2 capability is scaffolded.
