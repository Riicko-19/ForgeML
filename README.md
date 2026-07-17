# ForgeML

Upload a packaged model, get a versioned REST prediction endpoint — without writing
Docker or FastAPI code.

**Status: V1 in progress.** Modules 0–2 are frozen; Module 3 (the HTTP API) is
implemented. See [PROJECT_STATUS.md](PROJECT_STATUS.md) for exactly what works today.
What works right now is **package upload, validation, and inspection**. Building and
running model containers arrives in later modules.

## Quickstart

Requirements: **Python 3.11** (ADR-013), **Docker** (only to run PostgreSQL), and
**PostgreSQL 16** (ADR-009 — SQLite is not a supported adapter, because durable
operation claims need row-locking semantics it cannot express).

```bash
make setup     # create the venv, install hash-locked dependencies
make db        # start PostgreSQL 16 in Docker
make migrate   # apply the schema (required before the first run)
make run       # serve on http://127.0.0.1:8000
```

In another terminal:

```bash
make example   # build examples/hello-model.forge

curl http://127.0.0.1:8000/readyz

curl -X POST http://127.0.0.1:8000/v1/packages \
  -H "Idempotency-Key: $(uuidgen)" \
  -F "file=@examples/hello-model.forge"
```

You get back **202 and an operation**, whose `result.package_id` you can then read:

```bash
curl http://127.0.0.1:8000/v1/packages/<package_id>
```

`make help` lists every task.

## Postman

A complete collection with assertions, examples, and automatic variable extraction is
in [docs/postman/](docs/postman/). Import both files, run **Health → Readiness**, then
**Packages → Upload**, and the rest of the collection is wired up for you.

## Configuration

Nothing is read from a file; everything is an environment variable, and an unknown
`FORGEML_*` key fails startup rather than being ignored.

| Variable | Required? | Notes |
| --- | --- | --- |
| `FORGEML_ENVIRONMENT` | **required** | `development`, `test`, or `production` |
| `FORGEML_DATABASE_URL` | **required** | `postgresql+psycopg://…`. Startup fails closed without it. |
| `FORGEML_BIND_HOST` | default `127.0.0.1` | Wildcard addresses are rejected |
| `FORGEML_BIND_PORT` | default `8000` | |
| `FORGEML_ARTIFACT_ROOT` | default `storage/artifacts` | Relative to the working directory |

The full table, including package limits, is in [backend/README.md](backend/README.md).

## What a .forge package is

A ZIP containing a root-level `forge.yaml` and a `src/` tree. See
[examples/hello-model/](examples/hello-model/) and build it with
`python3 scripts/forge_pack.py examples/hello-model`.

ForgeML **never imports or executes your package** while validating it. That is the
package system's central security guarantee, and it is enforced by a test that fails
the build if any validation path so much as imports `pickle`.

## Security

**There is no authentication.** ForgeML V1 assumes a single trusted operator on a
protected administrative network (ADR-001, docs 11), and the control plane builds and
runs code that packages supply. **Do not expose it to a network you do not control.**
An authorization ADR is a prerequisite for public exposure and does not exist yet.

## Documentation

- [PROJECT_STATUS.md](PROJECT_STATUS.md) — what is frozen, what is next
- [backend/README.md](backend/README.md) — configuration, API, quality gates
- `ForgeML_Engineering_Kit_Phase0/docs/` — architecture, ADRs, module designs
- [docs/postman/](docs/postman/) — the API, hands-on

## Development

```bash
make test   # full suite (needs `make db`)
make lint   # black, ruff, mypy --strict
```

CI runs the same gates on Python 3.11 against a real PostgreSQL 16.
