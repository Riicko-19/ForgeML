# Module 3 — Engineering Decisions

## D-1 — Validation runs inline; the operation resource stays

**Problem.** ADR-006 requires durable operations; ADR-010 says a worker claims
them. No worker exists until the deployment module.

**Alternatives.** (a) Create the operation PENDING and let it sit. (b) Validate
synchronously and return the package directly, dropping the operation. (c)
Validate inline but still create and complete the durable operation.

**Chosen.** (c).

**Reason.** (a) ships a system where uploads never complete — a placeholder, not
a deferral. (b) breaks the docs 12 contract and would be a breaking API change
the day the worker lands. (c) satisfies ADR-006 exactly (durable, idempotent,
correlated, terminal) while doing bounded in-process work that needs no Docker.

**Tradeoff.** Upload latency includes validation. That is bounded by
`PackageLimits`, and validation never touches the network.

**Future implications.** When the worker arrives, `PackageService._execute` moves
behind `claim_next()` and **no client changes** — which is precisely why the
operation resource exists.

---

## D-2 — A rejected package succeeds its operation

**Problem.** Does uploading an invalid package produce a failed operation, or a
succeeded operation with a rejected package?

**Chosen.** Succeeded operation; the package carries the verdict and findings.
The operation FAILS only when the platform could not do the work (for example an
unreadable artifact).

**Reason.** The operation describes *doing the validation*, not the verdict.
FR-01 says the operation's result references the package; FR-03 says the package
carries the findings. Conflating a bad package with a broken platform makes both
unactionable: an operator cannot tell "fix your manifest" from "your disk died".

**Tradeoff.** A client must read the package to learn the verdict — one extra
call after polling. It is the honest shape.

---

## D-3 — `OperationStore.claim(operation_id)` (frozen-module amendment)

**Problem.** An inline executor must run *its own* operation. `claim_next()`
returns the oldest pending one.

**Chosen.** Add `claim(operation_id)` — additive, recorded, conformance-tested.

**Reason.** Without it, two concurrent uploads would each claim the other's
operation and report the wrong result. That is a correctness failure, which is
one of the few grounds for touching a frozen module.

**Tradeoff.** The Module 2 port grew. It is additive: no existing symbol changed.

---

## D-4 — The pagination cursor is opaque and URL-safe

**Problem.** Module 2's keyset cursor is `<iso-timestamp>|<uuid>`. Over HTTP the
`+` in the UTC offset decodes as a space, so **pagination was simply broken**.
The integration test caught it on the second page.

**Chosen.** Base64url-encode at the API boundary; decode on the way in.

**Reason.** Docs 12 requires an *opaque* cursor. The raw form is neither opaque
nor URL-safe, and encoding at the boundary keeps the repository's internal
ordering keys internal — a client cannot hand-build a cursor and take a
dependency on our sort order.

**Tradeoff.** None worth naming.

---

## D-5 — Multipart upload, and a synchronous handler

**Problem.** The artifact store takes a synchronous `BinaryIO`; FastAPI is async.
Bridging an async request stream into a blocking store is a source of subtle bugs.

**Chosen.** `multipart/form-data` with one `file` field, and a **`def`** handler
(not `async def`), which FastAPI runs in a threadpool. `UploadFile.file` is a
`SpooledTemporaryFile` — exactly the sync stream the store wants, spilling to
disk rather than buffering a 500 MiB archive in memory.

**Reason.** It is the simplest correct bridge, and it gives us the filename for
free. Hand-rolling an async-to-sync adapter over `request.stream()` would be more
code and more risk for no benefit.

**Tradeoff.** The bytes land in a spool file before the artifact store hashes them
into place, so a large upload touches disk twice. Acceptable; revisit if upload
throughput ever matters.

---

## D-6 — 422 is declared explicitly on every route

**Problem.** FastAPI auto-documents its own `HTTPValidationError` shape for any
route with a validated parameter. The handler actually returns ForgeML's frozen
envelope, so the **published schema advertised a body the API never sends**.

**Chosen.** Declare 422 → `ErrorEnvelope` on every route, and add a contract test
asserting that *every* 4xx/5xx response in the OpenAPI document uses the envelope.

**Reason.** A client generated from the schema would have parsed the wrong body.
The runtime was right and the contract was lying, which is the worst combination
because nothing fails until someone trusts the docs.

---

## D-7 — The published schema, but no interactive docs

**Chosen.** `openapi_url=/v1/openapi.json`; `docs_url` and `redoc_url` stay
disabled.

**Reason.** Docs 12 needs the schema published — it is the API's source of truth.
But docs 11 keeps the control plane on an administrative network until an
authorization ADR exists, and a browsable console on an unauthenticated,
code-executing control plane invites exactly the exposure that decision has not
been made yet.

---

## D-8 — Readiness now checks the database; startup fails closed

**Problem.** `/readyz` returned "ready" without checking anything. Since Module 2
the control plane cannot serve a single request without PostgreSQL.

**Chosen.** Readiness executes `SELECT 1` and returns 503 when it cannot. The
lifespan runs ADR-016 crash recovery at startup, which both performs the recovery
and proves the database answers (docs 11: startup fails closed).

**Reason.** A readiness probe that ignores its own database is a lie, and an
operator who trusts it routes traffic at a process that cannot serve.

**Tradeoff.** Two frozen Module 0 tests changed their expectations, and the real
process test now needs a real database. Both are the *correct* new behaviour, and
both are recorded as amendments rather than quietly patched.
