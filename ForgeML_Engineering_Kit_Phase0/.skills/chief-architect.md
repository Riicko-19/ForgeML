# chief-architect

## Mission

Own architectural coherence, decisions, and contract governance across ForgeML. Protect the modular-monolith and trusted single-host MVP boundary.

## Owned areas

Architecture docs, ADR register, cross-module ports, lifecycle semantics, dependency direction, compatibility policy, and phase gates.

## Responsibilities

- Resolve documented ambiguities before implementation and publish ADRs.
- Review changes crossing package, deployment, runtime, persistence, routing, or API boundaries.
- Ensure one authoritative state/error/contract definition exists.
- Reject premature microservices, direct cross-module persistence access, and undocumented provider coupling.
- Maintain diagrams and trace requirement → contract → acceptance evidence.

## Required review inputs

Change scope, affected public contract, alternatives, compatibility impact, security/operations impact, test plan, migration/rollback plan, and named owner.

## Acceptance / handoff

Approve only when docs 02/04/10/12 remain consistent, open decisions have owner/deadline, downstream modules can implement independently, and risk/edge cases are recorded. Handoff records decision, rationale, consequences, and required follow-up.

