# Module 0 Test Report

**Local result:** PASS  
**CI result:** NOT RUN — accepted for Module 0 only under ADR-014 evidence exception
**Freeze evidence result:** PASS — explicit user authorization, 2026-07-13
**Interpreter:** CPython 3.11.14  
**Package:** forgeml 0.1.0

## Automated suite

The complete suite ran outside the restricted network sandbox so the localhost process
signal test could bind an ephemeral loopback port.

| Suite | Result |
| --- | --- |
| Unit | PASS |
| Integration | PASS |
| Contract | PASS |
| Architecture | PASS |
| Total | 118 passed, 0 failed |
| Statement coverage | 100% |
| Branch coverage | 100% |

The suite covers configuration validation/isolation, wildcard rejection, metadata
failure, every error category and safe 500 behavior, bounded error paths, request ID
removal and concurrency/cancellation cleanup, logger spoofing/severity/redaction,
404/405/400/422/500 contracts, health/OpenAPI shapes, bootstrap boundaries, bind/start
failures, SIGINT behavior, real subprocess SIGTERM shutdown, and forbidden imports.

## Static quality

| Gate | Command | Result |
| --- | --- | --- |
| Format | python -m black --check src tests | PASS |
| Lint | python -m ruff check src tests | PASS |
| Types | python -m mypy src tests | PASS |
| Placeholder/suppression scan | rg over source/tests | PASS; no TODO, FIXME, placeholder, noqa, or type-ignore |

## Dependency and build evidence

| Gate | Result |
| --- | --- |
| Runtime hashed lock generation and byte comparison | PASS |
| Development hashed lock generation and byte comparison | PASS |
| Development build requirement included with --allow-unsafe | PASS |
| python -m build --no-isolation | PASS |
| Source distribution | PASS |
| Wheel | PASS |
| Clean Python 3.11 runtime-lock install | PASS |
| Wheel install with --no-deps outside source tree | PASS |
| installed_package_smoke.py | PASS |

## Real process evidence

- Installed wheel started on loopback with JSON-only logs.
- GET /healthz returned HTTP 200, exact HealthResponse, and UUIDv4 X-Request-ID.
- GET /readyz returned HTTP 200, exact HealthResponse, and distinct UUIDv4 request ID.
- Request-completion events used route templates and omitted query values.
- Ctrl-C regression check exited 0 without traceback after the boundary fix.
- Automated SIGTERM subprocess integration exited 0 without traceback.

## Failed runs and corrections

1. Initial TestClient collection failed because current Starlette deprecated HTTPX
   TestClient in favor of another optional package. Tests were moved to the already
   approved HTTPX ASGI transport; no dependency was added.
2. Initial tests found four contract/test issues: provider error kind expectation,
   third-party event selection, post-context log formatting test, and missing OpenAPI
   error schema. Each was corrected with regression coverage.
3. Real Ctrl-C testing found propagated KeyboardInterrupt/traceback; bootstrap now
   normalizes it to clean exit 0.
4. Implementation review found generic-500, wildcard bind, environment isolation,
   logger trust/severity, startup-boundary, request-ID variant, and signal-test gaps.
   All were fixed and covered.
5. Initial SIGTERM subprocess testing exposed Uvicorn re-raising SIGTERM after graceful
   shutdown. Bootstrap now translates that signal to clean exit 0; resource pipes are
   deterministically closed.
6. Iteration-2 review found incomplete metadata failure normalization and unsafe
   fallback mapping of unapproved HTTPException statuses. Metadata reader/type failures
   now become safe configuration failures, and unapproved statuses use the generic 500
   contract.

## GitHub Actions

The workflow exists at .github/workflows/backend-quality.yml and mirrors the successful
local commands. It could not be triggered during iteration-3 review because no usable
Git repository or remote was then available. A remote is now configured, but no
authenticated workflow result was available to the freeze audit. This report does not
claim that CI passed. The user explicitly
approved ADR-014's Module 0-only evidence exception on 2026-07-13, so the complete
recorded local-equivalent results satisfy the Module 0 freeze gate. Actual workflow
evidence remains mandatory for subsequent modules and backend changes.

The frozen implementation evidence corresponds to local commit
`fdc1e9eb7923127b0570c9b4b08f7e9a5b429711`.
