# Authentication Guide

How to authenticate against a ForgeML control plane, and what you need to know about the keys you
create.

Design: [`IDENTITY_AND_AUTH.md`](IDENTITY_AND_AUTH.md) · Security analysis:
[`SECURITY_REVIEW_EPIC_1.md`](SECURITY_REVIEW_EPIC_1.md)

---

## Read this first

> **Every API key is a root credential for the host.**
>
> The control plane drives the Docker daemon, and the Docker daemon runs as root. Anyone holding a
> valid key can cause containers to be built and run on your machine.
>
> ForgeML has authentication but **not yet authorization** (that is Epic 2). There are no
> read-only keys and no scopes: every key can do everything. Treat a ForgeML key with the same
> care as an SSH private key for the host.

---

## First run

Authentication is always on. There is no way to disable it, so minting a key is part of setup:

```bash
make setup && make db && make migrate
make key                       # mint your first key
make run
```

`make key` prints something like:

```
API key created.

  key id  976756b99e978c1a
  name    local-dev

  forge_976756b99e978c1a_NGCKuEm6nxtd2gzIt_R5IQGW92TP4wZxg2zC7IaxzgY

This is the only time the token is shown. Only its SHA-256 digest is stored,
so it cannot be recovered -- if you lose it, revoke this key and create another.
```

**Copy the token now.** Only its digest is stored. Losing it means revoking and re-issuing — there
is no recovery, by design.

---

## Using a key

Send it as a bearer token:

```bash
export FORGE_TOKEN='forge_976756b99e978c1a_NGCKuEm6...'

curl -H "Authorization: Bearer $FORGE_TOKEN" \
     http://127.0.0.1:8000/v1/deployments
```

The scheme is case-insensitive — `bearer` works as well as `Bearer`.

```python
import httpx

client = httpx.Client(
    base_url="http://127.0.0.1:8000",
    headers={"Authorization": f"Bearer {token}"},
)
client.get("/v1/deployments")
```

### What needs a key

Everything under `/v1`, including `/v1/openapi.json`.

Exactly two paths do not: **`/healthz`** and **`/readyz`**. Process supervisors and load balancers
hold no credential, and those endpoints expose nothing beyond liveness and database reachability.

---

## Managing keys

Key administration is a CLI, not an HTTP API. That is deliberate: with authentication and no
authorization, an authenticated key-creation endpoint would let *every* key mint more keys, so a
leaked key could issue itself a permanent replacement (ADR-026). HTTP key management arrives with
Epic 2, where a key can carry a scope.

The CLI needs database access, so run it on the host:

```bash
cd backend

# Create — one key per consumer, so revocation is surgical
.venv/bin/python -m forgeml.identity create --name "ci-pipeline"
.venv/bin/python -m forgeml.identity create --name "deploy-bot" --expires-days 90

# List — secrets are never shown
.venv/bin/python -m forgeml.identity list

# Revoke — takes effect on the very next request
.venv/bin/python -m forgeml.identity revoke 976756b99e978c1a
```

`list` output:

```
KEY ID            NAME                    STATE     LAST USED
976756b99e978c1a  ci-pipeline             active    2026-07-18T14:22:01+00:00
a1b2c3d4e5f60718  deploy-bot              active    never
0f1e2d3c4b5a6978  old-laptop              revoked   2026-06-02T09:14:55+00:00
```

Revoke the `KEY ID`, not the full token.

---

## Troubleshooting

### `401 authentication_required`

Every authentication failure returns the same response — missing header, malformed header, unknown
key, wrong secret, expired key, revoked key. That is intentional: telling a caller *which* one
applied would help an attacker enumerate valid keys.

You are not stuck, though: **the server logs the real reason.**

```json
{"event": "authentication_failed", "reason": "revoked", "key_id": "976756b99e978c1a"}
```

`reason` is one of `malformed_token`, `unknown_key`, `wrong_secret`, `expired`, or `revoked`.
Check the server log and `forgeml.identity list`.

Common causes, in rough order of likelihood:

| Symptom | Cause |
| --- | --- |
| 401 on every request | No `Authorization` header, or the scheme is missing |
| 401 after a while | Key expired — check `list` |
| 401 suddenly | Key revoked |
| 401 with a token you just copied | Truncated paste — the token is ~66 characters |
| 401 on `/v1/openapi.json` | Expected. It is authenticated |

### `configuration error: configuration_invalid` from the CLI

Configuration is fail-closed on **any** unknown `FORGEML_*` environment variable. The usual
culprit is `FORGEML_TEST_DATABASE_URL` left exported in your shell — that is a test-harness
variable, not a setting. Unset it.

### `404` where you expected `401`, or vice versa

Authentication runs *before* routing, so an unknown path returns `401` to an anonymous caller and
`404` once authenticated. This is intentional: route existence should not be discoverable without
a credential.

---

## Operating advice

**One key per consumer.** Your laptop, each CI pipeline, each deploy bot. Then revoking a
compromised key affects exactly one thing.

**Set expiry on automated keys.** `--expires-days 90` for anything machine-held. Keys do not
expire by default so that a first-run key does not die mid-deployment, but an unbounded automated
credential is a liability.

**Review `last_used_at` and revoke what is dormant.** A key that has not been used in months is
either unnecessary or in the wrong hands.

**Put TLS in front of the control plane.** ForgeML does not terminate TLS — a bearer token over
plaintext HTTP is readable by anything on the path. Terminate TLS at a reverse proxy.

**Do not expose the control plane to an untrusted network.** Until Epic 2, authentication is the
only control, and every key has full authority.

**Rotate by overlap.** Create the new key, deploy it, confirm traffic on the new `key_id` via
`last_used_at`, then revoke the old one. Revocation is immediate and has no grace period, so
revoking first means downtime.

---

## Rotating a compromised key

```bash
# 1. Revoke immediately — effective on the next request, no cache
.venv/bin/python -m forgeml.identity revoke <compromised-key-id>

# 2. Issue a replacement
.venv/bin/python -m forgeml.identity create --name "ci-pipeline (rotated)"

# 3. Find out what was done with it
```

For step 3, the audit trail is keyed by `actor_id`, which is the `key_id`:

```sql
SELECT occurred_at, action, target_type, target_id
FROM audit_events
WHERE actor_id = '<compromised-key-id>'
ORDER BY occurred_at DESC;
```

That answers "what did this credential do", which is the question an incident actually starts
with. Note that rows written before Epic 1, and all `SYSTEM` actions, carry `NULL` — the trail
reports "unknown" rather than guessing.

---

## What is not here yet

| Capability | Arrives in |
| --- | --- |
| Scoped / read-only keys | Epic 2 — Authorization |
| HTTP key management | Epic 2 |
| Rate limiting | Epic 2 |
| Users, teams, SSO | V2 — needs an identity provider |
| JWT / OAuth2 / OIDC | When there is an identity provider to talk to |

The seam for the last row already exists: a new credential type implements one Protocol with one
method and is composed in the composition root. Nothing in the identity model, the API layer, or
the audit trail has to change.
