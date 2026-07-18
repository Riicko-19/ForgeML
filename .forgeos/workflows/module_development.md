# Workflow — Module Development

The end-to-end process for developing a module, from entry gate to freeze. This is the
operational form of [`../constitution/04_module_lifecycle.md`](../constitution/04_module_lifecycle.md).

**Primary role:** Senior Implementation Engineer, with the Chief Architect at the design
gate and the Technical Reviewer / Security Reviewer at the review gate.

## Inputs

- The roadmap phase for the module (FEK doc 06): its scope, entry gate, and exit gate.
- The frozen upstream contract the module will depend on.
- The engineering standards and the applicable ADRs.

## Required artifacts

| Artifact | Template | Produced at |
| --- | --- | --- |
| Module design | `../templates/module_plan.md` | Design |
| Implementation note | `../templates/engineering_report.md` | Implementation |
| Review guide | `../templates/architecture_review.md` | Review |
| Handoff | `../templates/handoff.md` | Freeze |
| Pull request | `../templates/pull_request.md` | Merge |

## Steps and gates

```
1. ENTRY GATE ─▶ 2. DESIGN ─▶ 3. BUILD ─▶ 4. REVIEW ─▶ 5. EXIT GATE ─▶ 6. FREEZE
```

**1. Entry gate.** Confirm the upstream contract is frozen. If it is not, stop — the
module may not begin. Independent doc/fixture preparation may proceed; dependency-bearing
implementation may not.

**2. Design.** Write the module design. Name the frozen upstream contract explicitly.
Define the domain model, the ports introduced, the deferrals, and the applicable ADRs.
→ **Gate:** architecture review approves the design
([`architecture_review.md`](architecture_review.md)). A design that depends on an unfrozen
contract or exceeds charter scope is rejected.

**3. Build.** Implement to the design and the standards: ports before adapters,
deterministic domain policy, explicit side effects, typed errors, no placeholders. Write
tests at every warranted level; add new port methods to the conformance suite in the same
change. Orient with `graphify query` before reading source.

**4. Review.** Run the implementation review
([`implementation_review.md`](implementation_review.md)) against the review guide.
→ **Gate:** all findings resolved; a failing gate blocks merge.

**5. Exit gate.** The phase's specific acceptance evidence passes (the roadmap names it per
phase — e.g. reproducible artifact identity, or transition/failure/retry/recovery tests
with a fake runtime).

**6. Freeze.** Run the freeze process ([`freeze_process.md`](freeze_process.md)): CI passes
on the frozen commit, the public surface and limitations are recorded, the handoff is
written, and `PROJECT_STATUS.md` is updated.

## Exit criteria

The definition of done (constitution doc 04) holds in full: contract/ADR impact reviewed;
tests pass in CI; failure paths and telemetry verified; docs updated; security/resource
impact reviewed; no placeholder or hidden dependency; evidence recorded and public
interface handed off.

## Failure handling

- **Entry gate fails** (upstream not frozen): stop; escalate to the Chief Architect to
  freeze the dependency first.
- **Design rejected:** revise and return to the design gate; do not begin building.
- **Review finds a defect:** fix and re-review; do not merge around a failing gate.
- **Exit gate evidence fails:** the module is not done; fix and re-run. Local success does
  not substitute for the gate.
- **A frozen contract turns out wrong:** do not edit it — open an ADR to supersede
  (decision process), then plan the change as its own work.
