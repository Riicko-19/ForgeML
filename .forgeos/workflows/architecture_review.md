# Workflow — Architecture Review

Review of a module design or a proposed contract/architecture change, before implementation
begins. Its purpose is to catch design defects and scope violations while they are cheap.

**Primary role:** Chief Architect, with the Security Reviewer for any change touching the
trust boundary or runtime.

## Inputs

- The proposed design (`../templates/module_plan.md`) or the proposed contract change
  (`../templates/architecture_diff.md`).
- The charter, roadmap, principles, standards, and the applicable ADRs.
- The current frozen contracts and the knowledge graph.

## Outputs

- An approval, or a rejection with specific required changes.
- Any new or superseding ADR the design implies
  ([decision process](../constitution/03_decision_process.md)).

## Decision gates

The design passes only if all of the following hold:

- [ ] The frozen upstream contract it depends on is named and is actually frozen.
- [ ] It stays within the charter scope; any deferred milestone it opens has an ADR.
- [ ] The domain model is deterministic; I/O is behind ports owned by the consumer.
- [ ] Side effects are explicit (timeout, classified failure, correlation, idempotency or
      cleanup); no transaction spans provider work.
- [ ] New or changed contracts are versioned and their compatibility is stated.
- [ ] Deferrals are explicit and non-blocking; nothing is stubbed to look present.
- [ ] Security and resource-boundary impact is assessed against the trust model.
- [ ] The design implies the test evidence the phase's exit gate requires.

## Architecture diff

When the change alters an existing contract or boundary, it is presented as an architecture
diff (`../templates/architecture_diff.md`): what the contract was, what it becomes, who
depends on it, and why the change is safe or what makes it a versioned break. A contract
change without a diff and an ADR is not reviewable.

## Exit criteria

The design is approved and the frozen upstream contract is named, **or** it is rejected with
a specific, addressable list of required changes.

## Failure handling

- **Depends on an unfrozen contract:** reject; the dependency must freeze first.
- **Exceeds scope:** reject, or require an ADR that opens the milestone.
- **Contract change without an ADR:** reject; route through the decision process.
- **Security concern:** block until the Security Reviewer signs off or an ADR records the
  decision.

## Review loop

Rejections return to the design step of
[`module_development.md`](module_development.md). Implementation does not begin until the
design is approved.
