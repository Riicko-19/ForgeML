# Architecture Evolution

How ForgeML's architecture grew, capability by capability. This traces the *shape* of the
system over the modules, so a new contributor understands not just what exists but the
order in which the load-bearing decisions were made and why each layer could only come
after the one beneath it.

## The layering, in the order it was built

```
M0  Foundation      composable, fail-closed, observable skeleton
      │  error envelope · correlation ID · health · quality gates
M1  Package         deterministic, safe, content-addressed intake
      │  .forge format · finding codes · ArtifactStore/ArchiveReader ports (FROZEN)
M2  Metadata        durable, concurrency-safe, audited desired state
      │  PackageCatalog/OperationStore/AuditLog ports · UoW · recovery (FROZEN)
M3  Backend API     idempotent HTTP intake reusing all of the above
      │  POST/GET packages · operation resource · error mapping
M4  Analyzer/Gen    deterministic build-context derivation (pure functions)
      │  analyzed contract · reproducible artifact identity
M5  Deployment      durable, reconcilable lifecycle against an abstract runtime
      │  RuntimeManager/DeploymentRepository ports · ready/active semantics (FROZEN)
M6  Docker Runtime  ← next: the real adapter behind the M5 runtime port
M7  Routing         ← active version, stable route, rollback, retention
M8  Monitoring      ← logs, observations, retention
M9  Dashboard       ← the operator surface over the REST contracts
M10 Hardening       ← backups, security, release
```

Each layer depends only on frozen contracts beneath it. This is why the roadmap order is
mandatory rather than a preference: Module 3 was small precisely because Modules 0–2 had
already frozen the envelope, the correlation ID, the idempotency index, and the
transaction boundary.

## Recurring patterns that emerged

These patterns were not designed up front as a framework; they recurred because each
solved a real problem, and they are now the house style. A new module is expected to
follow them.

**Ports owned by consumers, pinned by conformance suites.** Every I/O boundary is a port
with a real adapter and an in-memory fake, both run against one conformance suite. A new
port method is added to the suite in the same change. This is what lets modules be built
and tested against fakes before the real adapter exists (M5 against a fake runtime; M3/M4
against in-memory metadata).

**Pure functions for deterministic policy.** Logic with no I/O is a function, not a port:
`validate_package`, `analyze`, the generator, and the deployment transition rules. Only
I/O boundaries become Protocols. This keeps the domain deterministic and trivially
testable.

**Nullable-until-computed fields as planned extension points.** A field is added nullable
and populated by the lifecycle stage that legitimately computes it —
`manifest_version` (null until validation), `PackageValidation.contract` (null until the
analyzer, M4), `Deployment.active_version_id` (null until routing, M7). Activating such a
field later is additive and reversible, not a redesign, and does not reopen the module
that reserved it.

**Durable operations with startup recovery.** Long work is a durable, idempotent
operation with a terminal state. Recovery is a startup reconciliation sweep under a single
supervised worker (ADR-016), not a lease — provable rather than heuristic, with no
double-execution window.

**Intent persisted before every side effect.** The lifecycle service writes desired state,
then performs the runtime side effect, then records the result — never holding a database
transaction across provider work. Reconciliation heals the gap.

## Contracts frozen so far

| Frozen contract | Since | Consumed by |
| --- | --- | --- |
| `.forge` format v1, finding codes, `ArtifactStore` / `ArchiveReader` | M1 | M3, M4, M5 |
| `PackageCatalog` / `OperationStore` / `AuditLog` / `UnitOfWork` | M2 | M3, M5 |
| Error envelope, correlation ID, health contract | M0 | all |
| Reproducible artifact identity | M4 | M5, M6 |
| `VersionState` ready/active semantics, `RuntimeManager` port | M5 | M6, M7 |

## Standing architectural risks

- **No authentication** on a code-executing API. Documented since M3; the largest risk in
  ForgeML. Needs an ADR before or during hardening.
- **Single worker** (ADR-010). Lifting the cap invalidates the ADR-016 recovery assumption
  and requires a lease or fencing token; `recover_orphaned` is the single place that
  assumption lives.

## Reserved for future updates

Append the next capability and any newly frozen contracts as each module lands, keeping
the layering diagram and the frozen-contracts table current.
