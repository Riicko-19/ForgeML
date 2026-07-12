# Architecture Decision Records

This register holds decisions required for MVP implementation. A new decision records context, decision, consequences, alternatives, owner, status, and date. Accepted ADRs are normative.

## ADR-001 — Trusted packages; defense-in-depth runtime isolation

**Status:** Accepted  
**Context:** A .forge package includes Python/dependency/model content that may execute during image build and inference. Full safe sandboxing is incompatible with the single-host MVP.

**Decision:** Only the trusted operator submits packages. Runtimes use non-root user, no Docker socket, no host network, no host artifact mounts, internal network only, dropped capabilities, read-only filesystem where compatible, scoped writable temporary storage, and CPU/memory/pid limits.

**Consequences:** This reduces blast radius but does not make untrusted code safe. Public anonymous upload and multi-tenant execution are prohibited.

## ADR-002 — Modular monolith control plane

**Status:** Accepted  
**Decision:** One FastAPI deployable hosts application/domain modules. Modules use in-process ports and DTOs; Docker model runtimes remain separate containers.

**Consequences:** Lower operational complexity and transactional consistency. Future extraction requires preserving port semantics; no domain-module network calls now.

## ADR-003 — Immutable content-addressed packages/images

**Status:** Accepted  
**Decision:** Package SHA-256 identifies bytes. Build context identity includes package checksum, generator version, and runtime/base-image version. Images are immutable and labeled with identities.

**Consequences:** Duplicate upload is idempotent and reproducibility improves. Artifact retention/garbage collection is required.

## ADR-004 — Metadata desired state; Docker reconciliation

**Status:** Accepted  
**Decision:** Durable metadata is desired state/audit record; Docker is observed state. Docker resources carry ForgeML labels. Startup/scheduled reconciliation records mismatches and repairs only through documented actions.

**Consequences:** Restart recovery does not treat Docker as a database. Operators must avoid manual managed-resource mutation except documented recovery.

## ADR-005 — One active version and platform route

**Status:** Accepted  
**Decision:** A deployment has at most one active version. Platform proxy resolves active healthy target; runtimes publish no host ports.

**Consequences:** Deterministic rollback/stable consumer URL. Weighted traffic requires future ADR.

## ADR-006 — Asynchronous durable operations

**Status:** Accepted  
**Decision:** Validation, build, start, stop, activation, and reconciliation use durable operation records with correlation/idempotency. Long-running HTTP commands return an operation resource.

**Consequences:** Clients poll and handle eventual completion. Worker/recovery mechanism must be restart-safe.

## ADR-007 — Storage/database behind ports

**Status:** Accepted  
**Decision:** Local filesystem artifact storage and one relational database are initial adapters. Application/domain depend on ports.

**Consequences:** Simple single-host deployment. Object storage/new relational adapter can be added without changing package/deployment rules.

## ADR-008 — Initial runtime compatibility matrix

**Status:** Accepted  
**Decision:** Format version 1 supports model.framework = python-callable only, Python 3.11 only, and a platform-owned Python 3.11 slim base image identified by immutable digest in configuration. The package entrypoint is the only executable integration point. Framework-specific adapters are future additive capabilities.

**Consequences:** The MVP has one deterministic runtime contract and does not need to introspect or deserialize framework artifacts during validation. Packages may include framework libraries as pinned dependencies, but platform support is for the callable interface, not framework-specific behavior.

## ADR-009 — PostgreSQL metadata and local filesystem artifacts

**Status:** Accepted  
**Decision:** PostgreSQL 16 is the MVP metadata database. The initial ArtifactStore is local filesystem storage on a dedicated persistent volume. The database worker uses PostgreSQL transaction/locking semantics.

**Consequences:** SQLite is not a supported production adapter because concurrent lifecycle operations and durable worker claims require stronger locking semantics. Backups must include PostgreSQL and artifact volume consistently.

## ADR-010 — Dynamic routing and worker execution

**Status:** Accepted  
**Decision:** A Caddy reverse proxy terminates TLS and forwards dashboard/control-plane traffic. The control plane owns dynamic prediction routing through RouteManager; it resolves the active target in metadata and proxies only to the internal Docker network. One separately supervised control-plane worker process claims durable operations from PostgreSQL using row locking; it is restart-safe and does not require an external queue.

**Consequences:** Caddy configuration does not change per deployment. One worker is the MVP limit; multiple workers may be enabled later only after claim/lease tests prove safe concurrency.

## ADR-011 — Dependency and build supply-chain policy

**Status:** Accepted  
**Decision:** Dependencies are an optional list of exact PEP 508 name==version pins. Editable requirements, local paths, direct URLs, VCS references, hashes-only requirements, and unpinned ranges are rejected. Builder egress is limited to the configured approved package index; runtime egress is disabled by default. Builds record base-image digest, resolved dependencies, and a CycloneDX SBOM. A build fails when the configured scanner reports a Critical vulnerability, unless an explicitly time-bounded operator exception is recorded in audit metadata.

**Consequences:** Reproducibility and provenance are explicit. Offline mirrors are supported by changing the approved index configuration, not package semantics.

## ADR-012 — Retention and disk-pressure policy

**Status:** Accepted  
**Decision:** Keep package artifacts while referenced by any retained version, then for 30 days. Keep active versions, the newest READY rollback candidate, and all in-progress operation artifacts regardless of normal cleanup. Retain operation/build logs for 30 days with a 10 MiB cap per version; retain raw observations for 7 days and hourly aggregates for 90 days; retain audit events for 365 days. At disk-pressure threshold, delete eligible observations first, then eligible logs, then unreferenced artifacts; never delete protected items automatically.

**Consequences:** Operators receive bounded storage behavior and predictable rollback protection. Disk thresholds are configuration with documented defaults, not per-package settings.

## ADR-013 — Control-plane Python support

**Status:** Accepted  
**Decision:** The ForgeML V1 backend/control plane supports CPython >=3.11,<3.12.
Runtime, CI, locks, and production packaging use Python 3.11. Patch updates remain
normal dependency maintenance.

**Consequences:** The control plane and generated runtime share one Python minor line;
supporting another minor requires a compatibility decision and CI evidence.

## ADR-014 — Backend CI authority

**Status:** Accepted  
**Decision:** GitHub Actions is the V1 repository CI provider. The backend quality
workflow lives at .github/workflows/backend-quality.yml, is owned by Backend
Engineering, reviewed by QA, and enforces locks, format, lint, type, tests, contract,
build, and installed-package smoke gates on Python 3.11.

**Consequences:** CI is development governance only and adds no runtime/cloud service
to ForgeML. Module completion requires passing workflow evidence.

## ADR-015 — Server-owned request identifiers

**Status:** Accepted  
**Decision:** The control plane generates a UUIDv4 request ID for every request.
Inbound X-Request-ID values are ignored and never logged or reflected. The generated
ID is returned in the X-Request-ID response header and used for request-scoped logs.

**Consequences:** Untrusted clients cannot create collisions or inject log identifiers.
Trusted upstream trace propagation requires a future approved proxy-boundary decision.
