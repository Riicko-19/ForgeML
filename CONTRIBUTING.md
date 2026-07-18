# Contributing to ForgeML

Thank you for considering a contribution. This document tells you how ForgeML is
built, what the review will check, and where decisions are recorded — enough to
make a change without having lived through the project's history.

ForgeML is licensed under the [Apache License 2.0](LICENSE). Contributions are
accepted under the same license (Apache-2.0 §5).

---

## Before you start

ForgeML is not built feature-first. It is built **module by module**, and each
module's public surface is frozen before anything depends on it. This is the one
convention that explains most of the others.

| If you want to | Read first |
| --- | --- |
| Fix a bug or improve something small | This file, then open a pull request |
| Add or change behaviour | [`ForgeML_Engineering_Kit_Phase0/docs/06_IMPLEMENTATION_ROADMAP.md`](ForgeML_Engineering_Kit_Phase0/docs/06_IMPLEMENTATION_ROADMAP.md) — work belongs to a module |
| Change an architectural boundary or a frozen contract | [`10_ARCHITECTURE_DECISIONS.md`](ForgeML_Engineering_Kit_Phase0/docs/10_ARCHITECTURE_DECISIONS.md) — this needs an ADR |
| Understand where the project is | [`PROJECT_STATUS.md`](PROJECT_STATUS.md) — the single source of truth for progress |
| Understand how decisions get made | [`.forgeos/README.md`](.forgeos/README.md) |

---

## Development setup

Requires **Python 3.11** (ADR-013) and **Docker** (for PostgreSQL and the runtime).

```bash
make setup     # create the venv and install locked dependencies
make db        # start PostgreSQL 16 in Docker
make migrate   # apply schema migrations
make verify    # the checkpoint — run this before every push
```

`make help` lists every target. PostgreSQL is required: SQLite cannot express the
row-locking semantics durable operations depend on (ADR-009), so it is not a
supported fallback.

---

## The checkpoint

```bash
make verify
```

This is the whole gate. It runs formatting, linting, strict type checking, the
full test suite, and the coverage floor — and it is the **same command CI runs**.
If `make verify` is green locally, CI will be green. If you add a quality gate,
add it to the `Makefile`, never only to the workflow, or the two will drift.

What it enforces:

| Gate | Tool | Threshold |
| --- | --- | --- |
| Formatting | `black --check` | no diff |
| Linting | `ruff` | no findings |
| Types | `mypy` | strict, no errors |
| Tests | `pytest` | all pass |
| Coverage | `coverage` | ≥ 95% branch |

Some integration tests need Docker and skip without it. If you touched
`infrastructure/runtime`, make sure Docker is running so those tests actually
execute — a silent skip is not a pass.

---

## Architectural rules

These are enforced by `backend/tests/architecture/test_dependency_direction.py`,
which parses every module's imports. They fail the build, not the review.

```
api  →  application  →  domain
             ↓
          ports  ←  infrastructure (adapters)
```

- **The domain is pure.** No FastAPI, no SQLAlchemy, no Docker, no `zipfile`, no
  `pathlib`, no `os`. Domain code is policy over values, and it must stay
  decidable without I/O.
- **SQLAlchemy never leaves `infrastructure/database`.** If a mapped object
  escapes, a lazy load eventually fires outside a session in production.
- **The API layer never touches a provider.** It maps transport to commands.
- **No package-validation path may import or execute package content.** No
  `importlib`, `pickle`, `subprocess`, `eval`, or `exec` anywhere near a `.forge`
  archive. This is the acceptance gate for untrusted input.
- **Providers live behind ports.** Every external dependency — database,
  filesystem, archive format, container runtime, prediction transport — sits
  behind a port with an in-memory fake, and both are held to the same
  conformance suite in `tests/contract/test_port_conformance.py`.

If your change needs one of these rules relaxed, that is an ADR, not a pull
request.

---

## Code style

Beyond what the tools enforce:

- **Docstrings explain why, not what.** The signature already says what. Cite the
  FEK doc or ADR that motivated the decision.
- **Comment the surprising, not the obvious.** If a line looks wrong but is right,
  say why it is right.
- **Mark deliberate shortcuts.** If you knowingly take a simplification with a
  ceiling, leave a `ponytail:` comment naming the ceiling and the upgrade path:
  ```python
  # ponytail: string match on the daemon-connectivity message; Docker has no
  # stable exit code that distinguishes "daemon down" from "command failed".
  ```
- **Errors never leak internals.** No host paths, no raw provider output, no
  stack traces across the HTTP boundary. Classify the failure and keep the detail
  in the logs.

---

## Tests

Every change needs a test that fails without it. The suite is layered, and where
your test belongs depends on what you changed:

| Layer | Path | For |
| --- | --- | --- |
| Unit | `tests/unit/` | Pure logic, domain rules |
| Contract | `tests/contract/` | Port behaviour — runs against the real adapter *and* the fake |
| Integration | `tests/integration/` | Real PostgreSQL, real Docker, real HTTP |
| Architecture | `tests/architecture/` | Boundaries and dependency direction |
| Smoke | `tests/smoke/` | The installed wheel |

If you add a method to a port, add it to the conformance suite. A port whose fake
and real implementation are tested separately will drift.

---

## Pull requests

1. Branch from `main`.
2. Make the change, with tests.
3. Run `make verify` until it is green.
4. Open a pull request using the template — it asks which module the change
   belongs to and whether any ADR applies.

What reviewers check, in order:

1. Does it belong to a module, and is that module's gate open?
2. Does it cross a frozen contract? (If yes: where is the ADR?)
3. Does it hold the architectural rules above?
4. Is it tested at the right layer?
5. Is `make verify` green?

Commits should be small and self-describing. Use conventional prefixes
(`feat(module-7):`, `fix:`, `docs:`, `build:`, `refactor:`).

---

## Reporting a security issue

Do **not** open a public issue. See [`SECURITY.md`](SECURITY.md).

---

## Questions

Open a discussion or an issue with the `question` label. If the answer turns out
to be architectural, it will become an ADR — which is the intended path, not a
detour.
