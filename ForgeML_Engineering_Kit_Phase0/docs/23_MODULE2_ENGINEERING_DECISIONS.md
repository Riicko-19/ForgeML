# Module 2 — Engineering Decisions

## D-1 — Orphaned operations: startup reconciliation, not a lease

**Problem.** ADR-006 requires a "restart-safe" worker but specifies no mechanism.
A worker that claims an operation and is then killed leaves the row `RUNNING`
forever; `claim_next` only selects `PENDING`, so the client polls an operation
that can never terminate. The design as originally written did not satisfy the
ADR it cited.

**Alternatives.**
1. *Lease / visibility timeout* — `RUNNING` rows older than N re-enter the queue.
   Self-healing, but if the lease is shorter than a legitimately slow build you
   get double execution, which for an image build is expensive and for an
   activation is dangerous.
2. *Startup reconciliation sweep* — on boot, any `RUNNING` row is an orphan.
3. *Fencing tokens* — correct for N workers, unjustifiable for one.

**Chosen.** (2), plus a bounded attempt count. ADR-010 supervises exactly one
worker, which makes "every `RUNNING` row at startup belongs to the process that
died" a *provable* statement rather than a guess. Recovery returns the row to
`PENDING`, or fails it as `operation_abandoned` once attempts are exhausted.

**Reason.** It is the smallest thing that satisfies ADR-006 under ADR-010's
single-worker cap, and it has **no double-execution window at all** — unlike a
lease, which is a race by construction.

**Tradeoff.** It heals only at startup. If a worker hangs without dying, nothing
reclaims the row.

**Future implications.** The day ADR-010's single-worker cap is lifted, this
becomes wrong and must be replaced by a lease or fencing token. That dependency
is explicit, and `recover_orphaned` is the single place it lives.

---

## D-2 — Concurrency is delegated to PostgreSQL, never to application checks

**Problem.** Two identical uploads race; two retries of the same request race.

**Alternatives.** (a) `if not exists: insert` in the repository. (b) An advisory
lock around the read-modify-write. (c) Insert and let a unique index arbitrate.

**Chosen.** (c). `packages.sha256` and `operations (idempotency_key, type,
target_id)` are unique indexes; the writer that loses catches `IntegrityError`
on a savepoint and reads the winner's row.

**Reason.** (a) is simply wrong — both transactions pass the existence check and
both insert. (b) serialises every upload to protect against a rare race.

**Tradeoff.** The happy path carries a `try/except` that only fires under
contention, so it is easy to leave untested — and it initially *was*. It is now
covered by `test_insert_races.py`, which forces both transactions past their
existence check with a barrier so the race genuinely occurs.

---

## D-3 — Unit of Work in the application layer, not `core`

**Problem.** Docs 04 lists `UnitOfWork` as a port; docs 02 assigns it to the
Database module; docs 07 requires ports to be owned by their *consumer*.

**Alternatives.** (a) `core/persistence.py`. (b) `application/unit_of_work.py`.

**Chosen.** (b).

**Reason.** A `UnitOfWork` in `core` must import domain ports to type its
repository properties, creating `core → domain` while Module 1 already has
`domain → core` — a package-level import cycle that graphify and the
architecture test would both reject. Transactions are orchestrated by use cases,
so the application layer is also where it *belongs*.

**Future implications.** Docs 02's ownership table contradicts docs 07 and should
be amended. Flagged in the stabilization review; not resolved by this module.

---

## D-4 — Database-enforced immutability, not repository discipline alone

**Problem.** ADR-003 makes checksum and artifact immutable; docs 04 makes
terminal operations and audit events immutable. Repository code can honour that.
An operator with `psql` cannot be made to.

**Chosen.** Three plpgsql triggers, plus repository-level guards.

**Reason.** ADR-004 explicitly anticipates operators touching the database
directly and warns against it. An invariant that only holds when our code is the
only writer is not an invariant.

**Tradeoff.** Triggers are invisible to a reader of the ORM models, and they
must be dropped and recreated by migrations. `test_invariants.py` bypasses the
repositories on purpose to prove the invariant holds *at the database*.

---

## D-5 — Findings persist as an ordered JSONB array

**Problem.** Where do validation findings live?

**Alternatives.** A `findings` child table, or a JSONB column.

**Chosen.** JSONB array on `package_validations`.

**Reason.** Findings are bounded (≤51 by Module 1's frozen cap), always read as
a whole, and never filtered by code. A child table buys a join on every read to
support a query nobody has asked for.

**Tradeoff.** "Show me every package failing `dependency_not_pinned`" needs a
migration. Reversible; `test_findings_survive_persistence_in_order_and_with_
their_paths` pins the ordering and the path, which is the part that actually
matters to docs 12.

---

## D-6 — `manifest_version` is null until validation

**Problem.** `get_or_create` originally wrote `manifest_version=1` for a DRAFT
package — before anything had parsed the archive.

**Chosen.** Nullable; populated from `manifest.forge_version` at validation.

**Reason.** The engineering standards prohibit placeholders. Recording a format
version we have not read is a fabricated fact in a durable record, and it would
have been *wrong* for any package that declared something other than 1 — a
package we reject, whose stored record would nonetheless have claimed 1.

**Tradeoff.** One more nullable column and a `NULL OR > 0` check constraint.

---

## D-7 — The fakes are held to the real adapters' contract

**Problem.** Module 3 will test its use cases against in-memory fakes. A fake
that quietly disagrees with PostgreSQL makes every such test a lie.

**Chosen.** One conformance suite, parametrized over `[memory, postgres]`.

**Reason.** It is the executable form of the port freeze. It has already earned
this: it caught `claim_next(types=())` claiming *all* work in PostgreSQL while
claiming *none* in the fake (empty tuple is falsy), and it caught the fake
returning audit events with no `id` or `occurred_at` where PostgreSQL assigns
both. Both would have surfaced as inexplicable Module 3 bugs.

**Future implications.** Every new port method must be added to the conformance
suite, not merely to both implementations.
