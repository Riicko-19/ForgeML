# Module Lifecycle

ForgeML is built in vertical, reviewable **modules**. This document defines the life
of a module from entry to freeze. It is the constitutional summary; the step-by-step
process is [`../workflows/module_development.md`](../workflows/module_development.md),
and the current phase list is
[`PROJECT_STATUS.md`](../../PROJECT_STATUS.md) against the frozen roadmap
([FEK doc 06](../../ForgeML_Engineering_Kit_Phase0/docs/06_IMPLEMENTATION_ROADMAP.md)).

## The delivery rule

Work proceeds in vertical modules, but **shared contracts freeze before dependent
implementation begins**. A module may not begin until its entry gate passes. A role may
prepare independent docs and test fixtures concurrently, but may never silently change
a frozen upstream contract.

## The stages

```
ENTRY GATE ──▶ DESIGN ──▶ IMPLEMENTATION ──▶ REVIEW ──▶ EXIT GATE ──▶ FREEZE
     │            │              │              │           │            │
  upstream     design doc     code + tests   review    CI evidence   handoff +
  contract     names frozen   under          guide     on frozen     frozen public
  is frozen    deps           standards      + fixes   SHA (ADR-014) surface recorded
```

### Entry gate

The upstream contract the module depends on is frozen. The module's design document
names it explicitly. Nothing downstream begins on an unfrozen dependency.

### Design

Produce a module design document: scope (from the roadmap phase), the frozen upstream
contract relied upon, the domain model, the ports introduced, the deferrals made
explicit, and the ADRs that apply. Design is reviewed under
[`../workflows/architecture_review.md`](../workflows/architecture_review.md).

### Implementation

Build the module to the engineering standards
([`05_engineering_standards.md`](05_engineering_standards.md)): ports before adapters,
deterministic domain policy, explicit side effects, typed errors, no placeholders. Tests
are written at every level the change warrants (unit, contract, integration,
end-to-end, regression).

### Review

The change is reviewed under
[`../workflows/implementation_review.md`](../workflows/implementation_review.md) against
a review guide. A failing gate blocks merge. Review covers ownership and dependency
direction, compatibility, validation, idempotency, error transparency, redaction,
cleanup, tests, docs, and migration/operations.

### Exit gate

The phase's acceptance gate passes — the specific test evidence the roadmap names for
that phase (for example, "same input gives same artifact identity" for the generator, or
"transition/failure/retry/recovery tests with a fake runtime" for deployment).

### Freeze

Under [`../workflows/freeze_process.md`](../workflows/freeze_process.md): the GitHub
Actions backend quality workflow passes on the exact frozen commit (ADR-014), the frozen
public surface is recorded, known limitations are carried forward, and a handoff document
is written for whoever inherits the module. The freeze is recorded in `PROJECT_STATUS.md`
with its baseline commit and freeze authority.

## Definition of done

A module is done only when all of the following hold:

1. Contract and ADR impact reviewed.
2. Unit, integration, and relevant contract tests pass in CI.
3. Failure paths and telemetry verified.
4. Docs, diagrams, configuration reference, and migration/rollback notes updated.
5. Security and resource-boundary impact reviewed.
6. Review confirms no placeholder, bypass, hidden global state, or undocumented
   dependency.
7. Owner records evidence and hands off the stable public interface.

## The module document set

Each module carries a consistent set of documents (see the FEK docs 19–35 for the
established examples). ForgeOS provides the reusable templates for them in
[`../templates/`](../templates/):

| Document | Purpose | Template |
| --- | --- | --- |
| Design | scope, model, ports, deferrals | `templates/module_plan.md` |
| Implementation note | what was built and how it satisfies the design | `templates/engineering_report.md` |
| Review guide | where the risk is, what to read | `templates/architecture_review.md` |
| Engineering decisions | module-internal trade-offs | (in the module's decisions doc) |
| Handoff | what the next engineer must know | `templates/handoff.md` |

## What a module must never do

- Begin before its entry gate passes.
- Silently change a frozen upstream contract.
- Ship a placeholder, stub, or silent fallback dressed as a finished feature.
- Claim completion without CI evidence on the frozen commit.
- Introduce scope outside the charter without an ADR.
