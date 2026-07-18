# Engineering Report — <subject>

> Template. Copy and fill in. Use for a module implementation note or any report of
> completed engineering work. Delete these quotes when using it.

**Owner:** <role/name> · **Status:** <e.g. Implemented, freeze pending CI> ·
**Date:** <YYYY-MM-DD> · **Commit:** <SHA>

## What was delivered

A concise list of what was built, in terms of capability, not line count. Point to the
files/ports/tables rather than restating them.

## How it satisfies the design

For each design commitment, one line on how the implementation meets it. Note any deviation
from the approved design and the decision that authorized it.

## Key decisions

Module-internal trade-offs made during implementation, with the reasoning. Architectural
decisions go to an ADR instead; link them here.

## Evidence

| Gate | Result |
| --- | --- |
| Tests | <count>, <coverage>% branch |
| Type / lint / format | <clean?> |
| CI (`backend-quality.yml`) | <status> on <SHA> — or: not yet run |
| Exit-gate evidence | <the phase's specific proof> |

State CI honestly: a recorded exception is never described as a passing run.

## Known limitations carried forward

Explicit, not implied. What this work deliberately does not do, and which later module or
ADR addresses it.

## What downstream may depend upon

The stable surface this work exposes — the contracts a later module may rely on exactly as
written.
