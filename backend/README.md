# ForgeML Backend — Module 0 Foundation, Module 1 Forge Package System

This backend implements the frozen Module 0 foundation (typed startup configuration,
explicit application composition, safe errors, server-owned request IDs, bounded JSON
logs, health endpoints, quality gates) and the Module 1 Forge Package System (the
.forge format, content-addressed artifact storage, and archive validation).

It does not contain database, Docker, deployment, worker, routing, monitoring,
authentication, frontend, or other later-module behavior. Module 1 deliberately ships
no HTTP surface: `POST /packages` belongs to phase 3, and package metadata persistence
to phase 2.

## Requirements

- CPython 3.11
- Runtime dependencies installed from requirements.lock with hash enforcement
- Development dependencies installed from requirements-dev.lock with hash enforcement

The pyproject file is authoritative for direct dependencies. Lock files are generated
with pip-tools using the exact commands in the frozen Module 0 design.

For development and tests, install the locked dependencies and then install the local
source without resolving dependencies:

    python -m pip install --require-hashes -r requirements-dev.lock
    python -m pip install --no-deps --no-build-isolation --editable .

## Configuration

| Variable | Required/default | Constraint |
| --- | --- | --- |
| FORGEML_ENVIRONMENT | Required | development, test, or production |
| FORGEML_LOG_LEVEL | INFO | DEBUG, INFO, WARNING, ERROR, or CRITICAL |
| FORGEML_BIND_HOST | 127.0.0.1 | Non-wildcard IP address; 0.0.0.0 and :: are rejected |
| FORGEML_BIND_PORT | 8000 | 1–65535 |
| FORGEML_GRACEFUL_SHUTDOWN_SECONDS | 30 | 1–300 |
| FORGEML_ARTIFACT_ROOT | storage/artifacts | Directory holding content-addressed artifacts |
| FORGEML_PACKAGE_MAX_ARCHIVE_BYTES | 268435456 | 1 KiB – 16 GiB |
| FORGEML_PACKAGE_MAX_UNCOMPRESSED_BYTES | 1073741824 | At least the max archive size |
| FORGEML_PACKAGE_MAX_ENTRIES | 10000 | 1–1000000 |
| FORGEML_PACKAGE_MAX_COMPRESSION_RATIO | 100 | 1–10000 |
| FORGEML_PACKAGE_MAX_MANIFEST_BYTES | 1048576 | At most the max archive size |
| FORGEML_PACKAGE_MAX_SCHEMA_NODES | 1000 | 1–100000 |
| FORGEML_PACKAGE_MAX_SCHEMA_DEPTH | 20 | 1–256 |
| FORGEML_DATABASE_URL | None | postgresql+psycopg URL; required from Module 2 onward |
| FORGEML_DATABASE_POOL_SIZE | 5 | 1–50 |
| FORGEML_DATABASE_STATEMENT_TIMEOUT_MS | 30000 | 100–600000 |

Configuration names are case-sensitive. Empty values and unknown FORGEML-prefixed
keys fail startup. ForgeML reads no environment file automatically.

The package limits are operator policy bounding work spent on an untrusted archive.
Each bound is checked before the corresponding bytes are read, so a hostile archive
cannot make the validator allocate beyond policy.

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

## Forge package contract

A .forge file is a ZIP archive with UTF-8 paths containing one root-level forge.yaml,
a src/ tree, and any declared assets. Format version 1 is closed: unknown manifest
fields are rejected at every level, and only the python-callable framework on Python
3.11 is accepted (ADR-008). Dependencies must be exact `name==version` PEP 508 pins
(ADR-011). Input and output schemas are JSON Schema Draft 2020-12 documents that may
reference only local JSON Pointer targets.

A package is identified by the SHA-256 of its bytes (ADR-003), so storing the same
archive twice is idempotent. Artifacts are referenced as `artifact://<sha256>`;
callers never receive a filesystem path.

Validation never imports, executes, or deserializes package content. It rejects
absolute, traversal, non-normalized, duplicate, and non-UTF-8 member paths, symbolic
links, encrypted members, zip bombs, YAML alias bombs, oversized archives and
manifests, unsupported versions and frameworks, unpinned dependencies, invalid or
external-referencing schemas, and absent or checksum-mismatched assets. Each failure
is reported as a stable finding code with a logical path; the full matrix is in
`tests/contract/test_package_fixtures.py`, and the design is in docs 19.

## Metadata layer

PostgreSQL 16 holds desired state and the audit record (ADR-004, ADR-009). SQLite
is not supported: durable operation claims depend on row-locking semantics it
cannot express.

A package is identified by its SHA-256, and that unique index — not an
application check — is what makes duplicate upload idempotent. A mutating command
carries an idempotency key; the same key with the same request fingerprint
returns the original operation, and with a different fingerprint returns a
conflict. Operations are claimed with `FOR UPDATE SKIP LOCKED`; an operation
orphaned by a killed worker is recovered at startup (ADR-016).

The database enforces what the application cannot be trusted to: package checksum
and artifact are immutable, terminal operations are immutable, and audit events
reject UPDATE and DELETE.

Run migrations with `python -m alembic upgrade head` (the URL comes from
`FORGEML_DATABASE_URL`). `python -m alembic upgrade head --sql` emits DDL for
review without touching the database.

Database tests need a real PostgreSQL 16. Point them at one with
`FORGEML_TEST_DATABASE_URL`, or run `docker run -d --name forgeml-pg -e
POSTGRES_PASSWORD=forgeml -e POSTGRES_USER=forgeml -e POSTGRES_DB=forgeml -p
55432:5432 postgres:16`, which is the default the tests expect.

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

Module 1 provides no HTTP surface and no package persistence: `PackageCatalog` arrives
with its adapter in phase 2, and `POST /packages` in phase 3. Package validation is
synchronous and in-process; ADR-006 wraps it in a durable operation in phase 3. Asset
content is verified only for assets that declare a checksum.

Packages are trusted operator content (ADR-001). Validation reduces blast radius but
does not make untrusted code safe; anonymous upload remains prohibited.
