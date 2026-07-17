# ForgeML — Postman

A complete collection for the ForgeML V1 control-plane API, with assertions, worked
examples, and automatic variable extraction.

## Files

| File | Purpose |
| --- | --- |
| `ForgeML.postman_collection.json` | The API: Health, Packages, Operations |
| `ForgeML.postman_environment.json` | `baseUrl` (localhost) plus the ids the collection fills in for you |

## Before you import

The backend must be running and its database migrated. From the repository root:

```bash
make setup     # once
make db        # PostgreSQL 16 in Docker
make migrate   # apply the schema
make run       # serve on http://127.0.0.1:8000
make example   # build examples/hello-model.forge (in another terminal)
```

## Import

1. Postman → **Import** → both JSON files in this directory.
2. Top-right environment selector → choose **ForgeML — Local**.

`baseUrl` defaults to `http://127.0.0.1:8000`. Change it there if you bound elsewhere.

## Run order

1. **Health → Liveness** — proves the process is up.
2. **Health → Readiness** — proves PostgreSQL answers. **A 503 here means every other
   request will fail.** Fix it before continuing.
3. **Packages → Upload package** — ⚠️ **open the Body tab and attach a `.forge` file.**
   Postman cannot store a file path in an exported collection, so this is the one
   manual step. Use `examples/hello-model.forge`.
4. **Operations → Poll operation** — the upload already saved `operationId`.
5. **Packages → Read package** — the upload already saved `packageId`. This is where
   the verdict and any findings live.
6. **Packages → List packages**.

## Variables the collection sets for you

| Variable | Set by | Meaning |
| --- | --- | --- |
| `operationId` | Upload | The durable operation to poll |
| `packageId` | Upload, Poll | The package to read |
| `correlationId` | every request | The server-issued `X-Request-ID` (ADR-015) |
| `cursor` | List | Next page, when there is one |

You never paste an id by hand.

## Things that will confuse you once

**Upload returns an operation, not a package.** Long-running commands return `202` and
an operation resource (ADR-006). Poll it, then read the package it references.

**A rejected package produces a *succeeded* operation.** The operation reports whether
the validation *ran*, not whether the package was any good. Read the package to find
`validation_state: rejected` and its `validation_findings`. An operation only *fails*
when the platform could not do the work — for example an unreadable artifact. This
separation means you can always tell "fix your manifest" from "the platform is broken".

**Uploading the same bytes twice gives you one package.** A package is identified by
the SHA-256 of its bytes (ADR-003). A second upload is a new *operation* but never a
second package.

**The idempotency key is scoped to the request, not the session.** Replaying the same
key with the same file returns the original operation and does no work twice. Reusing
that key for a *different* request is a `409 idempotency_conflict`. The collection uses
`{{$guid}}` so each new upload gets a fresh key; pin it to a literal string if you want
to test replay.

**Swagger UI is deliberately disabled.** The schema is published at
`/v1/openapi.json`, but the browsable console is off: docs 11 keeps the control plane
on an administrative network until an authorization ADR exists, and a console invites
exactly the exposure that decision has not been made yet.

## Trying a rejection

Editing the example is the fastest way to see findings:

```bash
cp -r examples/hello-model /tmp/broken
sed -i 's/^dependencies: \[\]/dependencies:\n  - numpy>=2.1.0/' /tmp/broken/forge.yaml
python3 scripts/forge_pack.py /tmp/broken -o /tmp/broken.forge
```

Upload `/tmp/broken.forge` and read the package. You will see:

```json
{
  "code": "dependency_not_pinned",
  "message": "dependency must be an exact name==version pin",
  "path": ["dependencies", 0]
}
```

ADR-011 requires exact `name==version` pins; a range is not reproducible.

## Common failures

| Symptom | Meaning |
| --- | --- |
| `503 dependency_unavailable` on `/readyz` | PostgreSQL is down or `FORGEML_DATABASE_URL` is unset. Run `make db && make migrate`. |
| `ECONNREFUSED` | The backend is not running (`make run`), or you bound a different port. |
| `400 idempotency_key_required` | The `Idempotency-Key` header is missing or disabled. |
| `409 idempotency_conflict` | You reused a key for a different request. Use a new key. |
| `422` with `request_validation_failed` | A path or query parameter is malformed — usually an id that is not a UUID, or `limit` outside 1–100. |
| `422 archive_too_large` | The archive exceeds `FORGEML_PACKAGE_MAX_ARCHIVE_BYTES`. |
| Upload 400 with no obvious cause | You did not attach a file in the Body tab. |
