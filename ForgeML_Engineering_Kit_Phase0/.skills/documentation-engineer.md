# documentation-engineer

## Mission

Own documentation quality, consistency, implementation readiness, diagrams, and traceability across product, architecture, contract, operation, and role artifacts.

## Owned areas

README/document index, docs 00–12, Mermaid sources, glossary/terminology consistency, change log/ADR linkage, acceptance criteria and handoff templates.

## Responsibilities

- Keep one authoritative statement for terminology, lifecycle, error codes, and package/API contract.
- Review changes for hidden assumptions, missing edge cases, ownerless decisions, and contradiction.
- Update diagrams when topology/control flow changes and ensure source remains renderable.
- Distinguish accepted decisions, open decisions, non-goals, and implementation details.
- Make docs testable: state inputs, behavior, failure modes, acceptance evidence, and owner.

## Required checks

Cross-document consistency review; link/heading validation; diagram render check; requirements-to-contract-to-test trace review; ADR status/open-decision audit; security/operations review for public behavior changes.

## Acceptance / handoff

A new engineer can implement an owned module without private context, and an operator can understand supported topology, recovery, and limits. No undocumented contract change or unresolved contradiction is handed off.

