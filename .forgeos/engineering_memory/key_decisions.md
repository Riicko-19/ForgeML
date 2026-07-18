# Key Engineering Decisions

An index of the architectural decisions that shaped ForgeML, with a one-line memory of
why each mattered. This is a navigational memory, not a second copy of the ADRs — the
authoritative text is the ADR register,
[FEK doc 10](../../ForgeML_Engineering_Kit_Phase0/docs/10_ARCHITECTURE_DECISIONS.md), and
the ForgeOS index [`../decisions/README.md`](../decisions/README.md).

Read the ADR itself before depending on or changing anything it governs. An accepted ADR
is normative; it is superseded, never edited.

## The decisions that shape everything

| ADR | Decision | Why it matters (the memory) |
| --- | --- | --- |
| 001 | Trusted packages; defense-in-depth runtime isolation | The whole security model. Isolation reduces blast radius; it does not make untrusted code safe. No anonymous upload, no multi-tenant execution. |
| 002 | Modular monolith control plane | One FastAPI deployable, in-process ports and DTOs. Future extraction must preserve port semantics; no domain-module network calls now. |
| 003 | Immutable content-addressed packages/images | Package identity is SHA-256 of the bytes; build identity includes its inputs. Duplicate upload is idempotent; reproducibility follows. Requires artifact GC. |
| 004 | Metadata desired state; Docker reconciliation | Metadata is intent; Docker is observed. Restart recovery never treats Docker as a database; operators avoid manual mutation except documented recovery. |
| 005 | One active version and a platform route | At most one active version; the platform proxy resolves the active healthy target; runtimes publish no host ports. Deterministic rollback. |
| 006 | Asynchronous durable operations | Long commands return an operation resource; clients poll. The worker/recovery mechanism must be restart-safe. |
| 007 | Storage/database behind ports | Filesystem and one relational DB are just the initial adapters. New adapters do not change package/deployment rules. |
| 008 | Initial runtime compatibility matrix | Format v1 = `python-callable` only, Python 3.11 only, platform-owned slim base image by digest. The entrypoint is the only integration point. |
| 009 | PostgreSQL 16 metadata; local filesystem artifacts | SQLite is not a supported adapter — concurrent lifecycle claims need real row-locking. Backups must include DB and artifact volume consistently. |
| 010 | Dynamic routing; single worker | Caddy terminates TLS and does not change per deployment; the control plane owns dynamic prediction routing. Exactly one restart-safe worker in V1. |
| 011 | Dependency and build supply-chain policy | Exact PEP 508 pins only; builder egress limited to the approved index; builds record base-image digest, resolved deps, and a CycloneDX SBOM; Critical vulns fail the build. |
| 012 | Retention and disk-pressure policy | Bounded storage with predictable rollback protection; protected items are never auto-deleted. Thresholds are configuration, not per-package. |
| 013 | Control-plane Python support | CPython >=3.11,<3.12. Control plane and generated runtime share one Python minor line. |
| 014 | Backend CI authority | GitHub Actions is the V1 CI. Module completion requires passing workflow evidence on the frozen SHA. The Module 0 evidence exception is closed and extends to nothing later. |
| 015 | Server-owned request identifiers | The server generates a UUIDv4 request ID per request; inbound `X-Request-ID` is ignored and never logged or reflected. Prevents client-injected log identifiers. |
| 016 | Operation lease, crash recovery, and retry | Recovery is a startup reconciliation sweep under one supervised worker, not a lease — no double-execution window. No automatic retry; retry is an operator action creating a new attempt. Lifting the single-worker cap invalidates this. |
| 017 | Generated runtime adapter emits valid Python literals | The Module 4 generator embedded schemas as JSON (`false`/`true`/`null`) into Python source — a latent `NameError` that only a fake runtime hid. Fixed to `pprint.pformat` (`True`/`False`/`None`, sorted). Changes artifact identity values (no golden pinned). A generated runtime artifact must be exercised by an execution test, not just static checks. |

## Decisions still owed

These are known gaps that will require an ADR when their module or hardening arrives.
They are recorded here so the debt is not forgotten:

- **Authentication** on the code-executing API (raised in M3 review; the largest standing
  risk).
- **Multiple workers**, if ever needed — requires a lease or fencing token and invalidates
  ADR-016 as written.
- Any **deferred milestone** (multi-user auth, remote orchestration, GPU policy,
  registries, package signing, canary releases) — none is a "small addition."

## Reserved for future updates

As new ADRs are accepted, add a row above and, if the ADR is authored in ForgeOS, create
its file under [`../decisions/`](../decisions/) and index it there.
