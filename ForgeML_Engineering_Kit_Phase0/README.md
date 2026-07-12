# ForgeML Engineering Kit — Phase 0

ForgeML is a self-hosted, single-server platform that turns a trusted, versioned machine-learning package (.forge) into a managed HTTP prediction endpoint. This kit is the implementation contract for the MVP: decisions, interfaces, operational constraints, quality gates, and ownership. It contains no application implementation.

## How to use this kit

Read documents in numeric order. Documents 00–09 define product and delivery. Documents 10–12 record decisions, operations, and external contracts. Mermaid files in diagrams/ are maintained source diagrams.

| Area | Authoritative document |
| --- | --- |
| Scope and outcomes | docs/00_PROJECT_CHARTER.md |
| Requirements and acceptance | docs/01_PRODUCT_REQUIREMENTS.md |
| Architecture and decisions | docs/02_SYSTEM_ARCHITECTURE.md; docs/10_ARCHITECTURE_DECISIONS.md |
| Flows and modules | docs/03_HIGH_LEVEL_DESIGN.md |
| Internal and external contracts | docs/04_LOW_LEVEL_DESIGN.md; docs/12_EXTERNAL_CONTRACTS.md |
| Repository and delivery | docs/05–09 |
| Security and operations | docs/11_OPERATIONS_AND_SECURITY.md |
| Module 0 design, implementation, and blocker reports | docs/13_MODULE0_FOUNDATION_DESIGN.md–docs/18_MODULE0_BLOCKER_REPORT.md |

## Document control

| Document set | Accountable owner | Status |
| --- | --- | --- |
| 00–01 product scope/requirements | Product owner | Approved baseline |
| 02–04 architecture/design | Chief Architect | Approved baseline |
| 05–08 repository/delivery/standards | Chief Architect with relevant domain owners | Approved baseline |
| 09 role workflow | Chief Architect | Approved baseline |
| 10 decisions | Chief Architect | Accepted decisions only |
| 11 operations/security | Deployment, Runtime, Database owners | Approved baseline |
| 12 external contracts | Backend, Package, Deployment owners | Approved baseline |
| diagrams and role profiles | Documentation owner and named domain owner | Approved baseline |

## Scope at a glance

The MVP accepts a valid .forge archive, builds an immutable runtime image, starts an isolated container per deployed version, exposes a stable platform route, and retains package/build/deployment history, logs, and basic health/resource metrics. ForgeML has one trusted administrative operator; it is not a multi-tenant code-execution service.

## Review and change control

An architectural change requires updates to the affected document, relevant diagram, and acceptance criteria. Resolve conflicts in this order: approved ADRs, external contracts, low-level design, high-level design, then product requirements. Implementation must not invent behavior where documentation says TBD: the named owner must close the decision.

## Phase-0 completion

Phase 0 is complete when every document has an approved owner/date, all TBDs are decided or explicitly deferred, and the Phase 1 entry gate passes. No application code belongs to this phase.
