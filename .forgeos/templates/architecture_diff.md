# Architecture Diff — <contract/boundary>

> Template. Copy and fill in. Use whenever a change alters an existing contract or
> architectural boundary. A contract change without a diff and an ADR is not reviewable.
> Delete these quotes when using it.

**Author:** <role/name> · **Date:** <YYYY-MM-DD> · **ADR:** <ADR-NNN that authorizes this>

## The contract today

What the contract is now — signature, shape, states, or invariant — exactly as frozen, and
the module/ADR that froze it.

## The proposed change

What it becomes. Show before → after precisely.

```
- <before>
+ <after>
```

## Who depends on it

Every module or consumer that relies on the current contract. Name them; a change whose
blast radius is unknown is not safe.

## Compatibility

- [ ] Additive and backwards compatible (existing consumers unaffected), **or**
- [ ] A versioned break — the version bump and the migration/compat path are stated below.

Migration and rollback path (if a break):

## Why it is safe / why the break is justified

The reasoning. If additive, why existing behavior is untouched. If a break, why it is
necessary and what the deferred alternative would have cost.

## Decision record

This diff is authorized by ADR-<NNN>. Link it. A frozen contract changes only by a
superseding ADR, never by edit.
