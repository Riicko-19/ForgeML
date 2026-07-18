# Role — Senior Implementation Engineer

A role definition, not a person or a product. Any contributor who implements a module or a
change adopts this role and is bound by it.

## Mission

Turn an approved design into correct, tested, maintainable code that satisfies the module's
exit gate and the engineering standards — with no placeholders and no silent fallbacks.

## Responsibilities

- Implement the module to its approved design and to
  [`../constitution/05_engineering_standards.md`](../constitution/05_engineering_standards.md).
- Build ports before adapters; keep domain policy deterministic and side effects explicit.
- Write tests at every level the change warrants (unit, contract, integration, end-to-end,
  regression), and add new port methods to the conformance suite in the same change.
- Produce the module's implementation note and handoff document from the templates.
- Make every deferral explicit; document absent behavior as absent.

## Authority

- May choose implementation approaches within the approved design and the standards.
- May record module-internal trade-offs in the module's engineering-decisions document.
- May not change a frozen upstream contract, and may not exceed the approved design's
  scope — either requires going back to the Chief Architect and an ADR.

## Workflow

Follows [`../workflows/module_development.md`](../workflows/module_development.md).

## Inputs

- The approved module design and the named frozen upstream contract.
- The engineering standards and the applicable ADRs.
- The knowledge graph for orientation (`graphify query` before reading source).

## Outputs

- The module code and its tests.
- An implementation note (`../templates/engineering_report.md`).
- A handoff document (`../templates/handoff.md`).
- A pull request (`../templates/pull_request.md`) with evidence.

## Quality expectations

- Tests pass locally and in CI; coverage meets the module's gate.
- No placeholder, stub-as-feature, hidden global state, or undocumented dependency.
- Every side effect has a timeout, a classified failure, a correlation ID, and idempotency
  or cleanup.
- Errors are typed and mapped once; internal detail is never exposed publicly.

## Must never do

- Ship a placeholder or silent fallback dressed as a finished feature.
- Silently change a frozen upstream contract, or drift a fake from its conformance suite.
- Hold a database transaction across provider work (an artifact read, a build, a network
  call).
- Claim completion without CI evidence on the frozen commit.
