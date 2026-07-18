# Role — Chief Architect

A role definition, not a person or a product. Any contributor — human or AI — who holds
architectural authority for a piece of work adopts this role and is bound by it.

## Mission

Keep ForgeML coherent over time. Own the architecture, the contracts, and the decisions
that future contributors will build on. Ensure the system stays within its charter and
that every module fits the whole.

## Responsibilities

- Own the system, high-level, and low-level design (FEK docs 02–04) and the repository
  architecture (doc 05).
- Own the ADR register: author, review, accept, and supersede architectural decisions
  under [`../constitution/03_decision_process.md`](../constitution/03_decision_process.md).
- Define and freeze cross-module contracts before dependents are built.
- Approve module designs at the architecture-review gate.
- Guard scope against the charter non-goals; require an ADR to open any deferred milestone.

## Authority

- May freeze, and may authorize the change of, a public contract — only through a recorded
  ADR, never by edit.
- May block a module design that violates a principle, a standard, or the authority order.
- May not override the FEK or an accepted ADR without a superseding ADR.

## Workflow

Follows [`../workflows/architecture_review.md`](../workflows/architecture_review.md) for
designs and [`../constitution/03_decision_process.md`](../constitution/03_decision_process.md)
for decisions.

## Inputs

- The charter, requirements, and roadmap (FEK docs 00, 01, 06).
- A proposed module design or contract change.
- The current frozen contracts and the knowledge graph.

## Outputs

- Accepted or superseded ADRs (using [`../decisions/adr_template.md`](../decisions/adr_template.md)).
- Approved module designs with the frozen upstream contract named.
- Updates to engineering memory when a decision changes the system's shape.

## Quality expectations

- Every decision states context, decision, consequences, and rejected alternatives.
- Every frozen contract is named by the modules that depend on it.
- No architectural drift: the code, the graph, and the design documents agree, or the
  disagreement is recorded as work owed.

## Must never do

- Change a frozen contract or an accepted ADR by editing rather than superseding.
- Approve a design that depends on an unfrozen upstream contract.
- Allow scope outside the charter without an ADR that opens it.
- Confuse a recorded exception (ADR-014, Module 0) with a passing gate.
