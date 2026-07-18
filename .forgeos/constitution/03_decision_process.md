# Decision Process

This document defines how engineering decisions are made and preserved in ForgeML.
Its purpose is that no significant decision lives only in someone's memory or in a
conversation.

## What requires a recorded decision

A decision is recorded as an **Architecture Decision Record (ADR)** when it:

- changes or establishes a frozen public contract (package format, port signature,
  error envelope, state machine, finding code),
- introduces or removes an architectural boundary or dependency,
- changes the roadmap or phase structure,
- opens a previously deferred milestone or a charter non-goal,
- changes an immutable engineering principle, or
- resolves a trade-off that future contributors would otherwise re-litigate.

Routine implementation choices that live and die inside one module do **not** need an
ADR. They are captured in that module's engineering-decisions document instead (see
the module pattern in [`04_module_lifecycle.md`](04_module_lifecycle.md)).

If you are unsure, ask: *would a future contributor, seeing only the code, wonder why
this is the way it is, and be tempted to change it?* If yes, record the decision.

## Where decisions live

| Decision scope | Recorded in |
| --- | --- |
| Architectural / cross-module / contract | ADR in the register (see below) |
| Module-internal trade-off | that module's `*_ENGINEERING_DECISIONS.md` in the FEK |
| Process / role / workflow change | commit rationale, reviewed by affected roles |

The ADR register currently lives in the FEK as
[`10_ARCHITECTURE_DECISIONS.md`](../../ForgeML_Engineering_Kit_Phase0/docs/10_ARCHITECTURE_DECISIONS.md)
(ADR-001 … ADR-016). New ADRs are authored using the ForgeOS ADR template and indexed
in [`../decisions/README.md`](../decisions/README.md), which cross-references the
existing register. See that index for the authoritative pointer.

## Anatomy of an ADR

Every ADR states, at minimum: **context** (the forces and the problem), **decision**
(what was chosen, unambiguously), **consequences** (what this makes easy and what it
costs), **alternatives** (what was rejected and why), plus **owner**, **status**, and
**date**. Accepted ADRs are normative. The template is
[`../decisions/adr_template.md`](../decisions/adr_template.md).

An ADR is written to be read years later by someone who was not present. It explains
the *why*, not only the *what* — a decision without its rejected alternatives invites
the same mistake again.

## Status lifecycle

```
Proposed ──▶ Accepted ──▶ (Superseded by ADR-NNN | Deprecated)
     └──▶ Rejected
```

- **Proposed**: under review; not yet binding.
- **Accepted**: normative. Contributors must comply.
- **Superseded**: replaced by a named later ADR. The old record is kept; ADRs are
  append-only history, never deleted or rewritten.
- **Rejected / Deprecated**: kept for the record so the reasoning survives.

An accepted ADR is never edited to say something different. To change a decision, write
a new ADR that supersedes it. This mirrors the immutability principle applied to the
decision record itself.

## Who decides

Architectural decisions are owned by the **Chief Architect** role and reviewed under
[`../workflows/architecture_review.md`](../workflows/architecture_review.md). A
security-relevant decision additionally requires the **Security Reviewer** role. The
owner recorded on the ADR is accountable for its consequences.

## Traceability

A change that implements or depends on a decision references the ADR by number in its
plan, its review, and its handoff. `PROJECT_STATUS.md` and the module handoff documents
cite the ADRs that authorize each freeze. A decision that nothing references is either
dead (supersede it) or being ignored (a review failure).
