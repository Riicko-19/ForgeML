# Coding Guidelines

## Technology baseline

Backend: Python, FastAPI, SQLAlchemy, Pydantic v2. Frontend: Next.js, TypeScript, Tailwind, shadcn/ui. Ruff/Black enforce Python quality; ESLint/Prettier frontend quality. Tool versions are repository-pinned and deliberately upgraded with CI evidence.

The ForgeML V1 control plane supports CPython >=3.11,<3.12. Patch updates within
Python 3.11 are maintenance changes subject to normal lock and test review.

## Python

- Use documented supported Python range and modern types consistently.
- Type public functions, DTOs, ports, and provider boundaries; avoid unbounded Any at boundaries.
- Pydantic is transport/configuration; domain entities/value objects do not leak ORM concerns.
- FastAPI routes only parse, depend, dispatch, and map responses: no Docker, filesystem, transaction, or lifecycle rules.
- SQLAlchemy stays infrastructure/database and maps at repository boundary.
- Inject ports/settings/clock/ID generator at composition; do not construct provider client in use case.
- Use explicit errors and one API error mapper. Broad exception handling is permitted only at process boundary for safe logging/mapping.
- Use pathlib/safe archive APIs; never concatenate user path components.
- Do not run blocking Docker/filesystem work in event-loop handlers without approved execution boundary.

## TypeScript/frontend

- Generate/type API response models from published contract; do not duplicate lifecycle unions.
- Organize by feature. Keep API access in feature service/shared typed client, not visual component.
- Model loading, empty, permission, error, and stale-operation states.
- Use semantic accessible HTML, labels, keyboard operation, visible focus, and status announcement.
- Browser code contains no control-plane secret/Docker configuration. Backend validation remains authoritative.

## Naming, errors, quality

Use intent names such as create_deployment and validate_archive. Keep files focused and avoid import cycles; cycles signal an ownership problem. Errors carry stable machine code and safe context. Log once where actionable context exists; never log credentials, headers, package bytes, raw inputs, or unredacted dependency output. Comments explain constraints, not obvious code.

Repository automation defines commands. Contributors run format/lint/type/unit and changed contract/integration tests; CI is authoritative.

## Forbidden patterns

- Direct Docker/ORM/filesystem access from HTTP handler or UI.
- Mutable global deployment/cache/configuration state.
- Raw SQL outside migration/repository policy.
- Placeholder/stub response that fabricates success.
- Silent runtime/dependency/active-version fallback.
- Broad lint/type suppression without narrow documented justification.
- User-controlled archive extraction path or shell construction.
- Frontend lifecycle rule that diverges from backend state machine.

## Acceptance criteria

- Static quality gates are machine-enforced.
- Public interfaces are typed, documented, and contract-tested.
- Review traces provider interaction through port and public error to stable code.
