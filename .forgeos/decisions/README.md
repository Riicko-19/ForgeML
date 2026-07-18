# Architecture Decision Records

The ADR system records the architectural decisions that shape ForgeML, so that no
significant decision lives only in memory or conversation. This directory holds the ADR
**template** and this **index**. It establishes the structure; it does not restate the
existing decisions.

## Where the ADRs live

The **authoritative register** for the decisions made during Modules 0–5 is the FEK:
[`ForgeML_Engineering_Kit_Phase0/docs/10_ARCHITECTURE_DECISIONS.md`](../../ForgeML_Engineering_Kit_Phase0/docs/10_ARCHITECTURE_DECISIONS.md).
That register (ADR-001 … ADR-016) remains the source of truth for those decisions — it is not
copied here.

**New ADRs** from this point may be authored as individual files in this directory using
[`adr_template.md`](adr_template.md), named `ADR-NNN-<slug>.md`, and added to the index below.
The numbering continues the existing register (the next new ADR is ADR-017). Either location
is valid; the index below is the single place to look up any ADR and find it.

## How to add an ADR

1. Copy [`adr_template.md`](adr_template.md) to `ADR-NNN-<slug>.md` (or, for a small register
   change, add to the FEK register — but index it here either way).
2. Fill in context, decision, consequences, alternatives, owner, status, date.
3. Follow the [decision process](../constitution/03_decision_process.md): Proposed → Accepted,
   reviewed by the Chief Architect (and Security Reviewer if security-relevant).
4. Add a row to the index below.
5. To change an accepted decision, write a new ADR that **supersedes** it. Never edit an
   accepted ADR to say something different.

## Index

Full text and reasoning for ADR-001 … ADR-016 are in the FEK register. A one-line "why it
matters" memory of each is in
[`../engineering_memory/key_decisions.md`](../engineering_memory/key_decisions.md).

| ADR | Title | Status | Location |
| --- | --- | --- | --- |
| 001 | Trusted packages; defense-in-depth runtime isolation | Accepted | FEK doc 10 |
| 002 | Modular monolith control plane | Accepted | FEK doc 10 |
| 003 | Immutable content-addressed packages/images | Accepted | FEK doc 10 |
| 004 | Metadata desired state; Docker reconciliation | Accepted | FEK doc 10 |
| 005 | One active version and platform route | Accepted | FEK doc 10 |
| 006 | Asynchronous durable operations | Accepted | FEK doc 10 |
| 007 | Storage/database behind ports | Accepted | FEK doc 10 |
| 008 | Initial runtime compatibility matrix | Accepted | FEK doc 10 |
| 009 | PostgreSQL metadata and local filesystem artifacts | Accepted | FEK doc 10 |
| 010 | Dynamic routing and worker execution | Accepted | FEK doc 10 |
| 011 | Dependency and build supply-chain policy | Accepted | FEK doc 10 |
| 012 | Retention and disk-pressure policy | Accepted | FEK doc 10 |
| 013 | Control-plane Python support | Accepted | FEK doc 10 |
| 014 | Backend CI authority (+ closed Module 0 evidence exception) | Accepted | FEK doc 10 |
| 015 | Server-owned request identifiers | Accepted | FEK doc 10 |
| 016 | Operation lease, crash recovery, and retry | Accepted | FEK doc 10 |
| 017 | Generated runtime adapter emits valid Python literals | Accepted | FEK doc 10 |
| 018+ | *(next new decision)* | — | this directory |

## Known decisions still owed

Recorded so the debt is visible (see
[`../engineering_memory/key_decisions.md`](../engineering_memory/key_decisions.md)):
authentication on the code-executing API; multiple workers (would invalidate ADR-016 as
written); and any deferred milestone entering scope. Each requires an ADR when its time comes.
