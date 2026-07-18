## What this changes

<!-- One or two sentences. What behaviour is different after this merges? -->

## Why

<!-- The problem, not the solution. Link the issue if there is one. -->

## Module

<!-- Which module does this belong to? See 06_IMPLEMENTATION_ROADMAP.md.
     If it belongs to no module, say so and explain why it should land anyway. -->

Module:

## Contract impact

- [ ] No frozen contract is touched
- [ ] A frozen contract changes — ADR: <!-- ADR-0XX -->
- [ ] A new architectural decision is required — ADR: <!-- ADR-0XX -->

Frozen surfaces include the `.forge` format, validation finding codes, the port
protocols, the HTTP contract, and the database schema.

## Checklist

- [ ] `make verify` is green locally
- [ ] Tests added at the right layer (unit / contract / integration / architecture)
- [ ] If a port gained a method, the conformance suite covers it
- [ ] Docstrings explain *why*; deliberate shortcuts carry a `ponytail:` note
- [ ] No internal detail (host paths, provider output, traces) crosses the HTTP boundary
- [ ] Docs updated if behaviour or status changed (`PROJECT_STATUS.md` is the source of truth)

## Testing notes

<!-- How did you verify this? If Docker-dependent tests were involved, confirm
     Docker was running so they actually executed rather than skipped. -->
