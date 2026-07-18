# Engineering Governance

This document defines who holds engineering authority in ForgeML, in what order
that authority applies, and how it may change. It is binding on every contributor,
human or AI.

## Authority order

When two sources appear to conflict, the higher source wins:

```
1. ForgeML Engineering Kit (FEK)      — charter, requirements, architecture, standards
2. Architecture Decision Records      — ADR-001 … ADR-016 and successors
3. Engineering protocols              — execution protocol, scope enforcement protocol
4. Frozen modules                     — a frozen public contract is law for its consumers
5. Knowledge graph (graphify-out/)    — derived map of the code as it is
6. Repository code                    — the implementation
```

ForgeOS (this directory) governs *process* and sits alongside this order: it tells
you how to work within it, and it never overrides a higher source. If a ForgeOS
document and an FEK document conflict on a matter of architecture, the FEK wins and
the ForgeOS document is defective and must be corrected.

The FEK is the detailed architectural authority. It is located at
[`ForgeML_Engineering_Kit_Phase0/docs/`](../../ForgeML_Engineering_Kit_Phase0/docs/).
The current status of work against it is
[`PROJECT_STATUS.md`](../../PROJECT_STATUS.md).

## What a frozen contract means

A **frozen** public contract — a package format, a finding code, a port signature,
an error-envelope shape, a state machine — may not be changed silently. Downstream
modules are permitted to depend on it exactly as written. Changing it is a versioned,
recorded decision (see `03_decision_process.md`), never an edit.

Freezing requires evidence, not assertion. Under ADR-014, a module is frozen only
when the repository's GitHub Actions backend quality workflow has passed on the exact
frozen commit. The single closed exception (Module 0) is recorded in ADR-014 and does
not extend to any later module.

## Roles hold authority; vendors do not

Engineering authority is vested in **roles**, defined in
[`../roles/`](../roles/), not in any person or AI product. A contributor acquires
authority by adopting a role for a piece of work and is bound by that role's charter,
including its "must never do" list. No role may exceed its defined authority, and no
role may silently assume another's.

## How governance changes

The constitution documents change through the decision process, not through casual
edits:

- A change to an **immutable principle** (this directory) requires an ADR that states
  what principle is changing and why, plus review under
  [`../workflows/architecture_review.md`](../workflows/architecture_review.md).
- A change to the **phase structure or roadmap** requires an ADR; `PROJECT_STATUS.md`
  reports against the roadmap and may not diverge from it.
- A change to a **role, workflow, or template** requires review by the affected roles
  and a recorded rationale in the commit, but not necessarily an ADR.

Editing a constitution document to match what someone did, rather than deciding first
and then acting, is a governance failure.

## Scope discipline

ForgeML has an explicit V1 scope and an explicit non-goals list (FEK charter). No
contributor introduces functionality outside that scope — no orchestration,
multi-tenancy, autoscaling, GPU scheduling, marketplace, or any deferred milestone —
without an ADR that opens it. "Small addition" is not a category that bypasses this;
the roadmap names the deferred milestones that specifically may not be treated as
small additions.
