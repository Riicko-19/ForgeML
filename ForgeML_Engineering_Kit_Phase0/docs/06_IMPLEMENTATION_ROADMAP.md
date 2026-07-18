# Implementation Roadmap

## Delivery rule

Work proceeds in vertical, reviewable modules, but shared contracts freeze before dependent implementation begins. “Complete one module before starting the next” applies to unfinished dependency-bearing work, not independent docs/test-fixture preparation. Do not begin a phase until its entry gate passes.

## Phases and gates

| Phase | Scope | Entry gate | Exit / acceptance gate |
| --- | --- | --- | --- |
| 0 Foundation | Config, composition, error envelope, logging, test harness | Phase-0 docs approved | Service boots without provider side effects; lint/type/unit baseline |
| 1 Forge Package | Archive schema, streaming store, validation, fixtures | Docs 04/12 package contract frozen | Fixture matrix passes; validator executes no package code |
| 2 Metadata | Records, repositories, migrations, UoW, audit | Package IDs/states frozen | Transaction/concurrency/migration tests |
| 3 Backend API | Commands/queries, operation resource, error mapping | Package/metadata ports stable | HTTP contract/idempotency tests |
| 4 Analyzer/Generator | Contract analysis/deterministic build context | Package contract stable | Same input gives same artifact identity |
| 5 Deployment | Lifecycle, worker, reconciliation | Runtime port/states frozen | Transition/failure/retry/recovery tests with fake runtime |
| 6 Docker Runtime | Image/container/network/health adapter | Deployment semantics frozen | Disposable Docker test proves labels, limits, isolation, cleanup |
| 7 Routing/Versioning | Stable route, activation/rollback, retention | Ready/active semantics frozen | Replacement/rollback tests |
| 8 Monitoring | Logs, observations, retention | Runtime labels/events stable | Redaction, bounds, query tests |
| 9 Dashboard | Package/deployment/version/observability flow | REST contracts frozen | Accessibility and end-to-end happy/failure flows |
| 10 Hardening/Release | Backups, security, docs, performance/recovery | Feature gates passed | Release checklist/reference deployment |

## Required order

Phase 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10. A role may prepare tests/docs concurrently inside a phase but may not silently change a frozen upstream contract.

## Epics (cross-cutting track)

Amended by **ADR-022**. Phases above are unchanged: same numbering, same order, same gates.

Some capabilities cut across every phase and cannot sit inside one. They are delivered as **epics**, which carry the same discipline as a phase — entry gate, exit gate, ADRs, CI freeze evidence under ADR-014 — but hold no position in the phase ordering.

| Epic | Scope | Entry gate | Exit gate |
| --- | --- | --- | --- |
| 1 Identity & Authentication | Principal model, API-key credential, authentication boundary, actor attribution in audit | Phases 0–7 implemented; ADR-018/019 accepted | Every `/v1` route authenticated; audit carries actor identity; security review complete |
| 2 Authorization | Permission model, per-command checks, scoped keys, HTTP key management | Epic 1 frozen | Every command authorizes; no privilege-escalation path |

**Epic 1 runs before Phase 8.** This is a dependency, not a reordering: Monitoring without an actor yields observations that cannot be attributed, and a Dashboard built before authentication is one that has authentication retrofitted into it.

An epic may not weaken a phase gate. Where an epic changes a frozen module's public contract it names that surface in its own ADR, exactly as a phase would.

## Deferred milestone reclassified

"Multi-user auth" below remains deferred. Epic 1 delivers **single-kind operator authentication** (ADR-023): one principal type, no users, no tenants, no groups. The multi-user identity model that entry refers to is still a V2 concern requiring its own ADR.

## Definition of done

1. Contract and ADR impact reviewed.
2. Unit, integration, and relevant contract tests pass in CI.
3. Failure paths and telemetry are verified.
4. Docs, diagrams, configuration reference, and migration/rollback notes updated.
5. Security/resource-boundary impact reviewed.
6. Review confirms no placeholder, bypass, hidden global state, or undocumented dependency.
7. Owner records evidence and hands off stable public interface.

## Reference test matrix

Release includes minimal valid CPU package, invalid manifest, path traversal, duplicate upload, unsupported framework, dependency-build failure, readiness timeout, input-schema failure, model execution failure, activation rollback, Docker container removed out-of-band, and control-plane restart reconciliation.

## Deferred milestones

Multi-user auth, remote orchestration, GPU policy, registries, package signing, and canary releases require ADRs; they are not Phase-1 “small additions.”

## Acceptance criteria

- Every downstream phase names its frozen upstream contract.
- No phase is done without test evidence and operational documentation.
- Reference deployment is reproducible on a clean supported host from docs/configuration.
- Module 0 and later backend changes pass the repository's GitHub Actions backend
  quality workflow; local-only evidence does not normally satisfy the CI gate. The
  one-time Module 0 evidence exception recorded in ADR-014 is the sole approved
  deviation and does not apply to later modules or backend changes.
