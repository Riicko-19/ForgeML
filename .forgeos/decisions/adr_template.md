# ADR-NNN — <short decision title>

> Template. Copy to `ADR-NNN-<slug>.md`, fill in, and add a row to `README.md`. An accepted
> ADR is normative and append-only: it is superseded, never edited to say something
> different. Delete these quotes when using it.

**Status:** Proposed | Accepted | Superseded by ADR-NNN | Rejected | Deprecated
**Owner:** <role/name>
**Date:** <YYYY-MM-DD>

## Context

The forces at play and the problem being decided. What made this decision necessary now?
State the constraints (charter, trust model, single-host MVP, existing frozen contracts) that
bound the choice. Enough that a reader years later, who was not present, understands why this
was even a question.

## Decision

What is chosen, unambiguously. Written so a contributor can comply without guessing. If it
establishes or changes a frozen contract, say exactly what the contract now is.

## Consequences

What this makes easy, and what it costs. Include the obligations it creates (e.g. "requires
artifact garbage collection", "backups must include X and Y consistently") and what it
forecloses without a further decision.

## Alternatives

What was considered and rejected, and why. A decision without its rejected alternatives
invites the same mistake again. Name the option and the specific reason it loses here.

## Supersession

If this ADR replaces an earlier one, name it and state what changed. If it is later
superseded, record the superseding ADR here — but never delete or rewrite the original text.
