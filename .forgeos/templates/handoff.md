# Handoff — <module number> <module name>

> Template. Copy and fill in. A handoff is written for the engineer who inherits the module.
> It is read before anyone touches the module. Delete these quotes when using it.

For the engineer who inherits <this module>. Read this before you touch it.

## The one idea

The single most important thing to understand about this module — the mental model that, if
missed, leads to the most common bug. State it plainly.

## Public contracts

The stable surface downstream may depend on, exactly as written:

```
<Port/Type>   <methods / fields>
```

These are pinned by <the conformance/contract test>. Add a method, add it to that suite —
otherwise the fakes drift and every downstream test built on them is a lie.

## How it fits together

The key components and how they interact — repositories, services, the transition rules —
each in a line or two. Point to the files; do not restate them.

## Invariants and how they are enforced

| Invariant | Enforced by |
| --- | --- |
| <what must always hold> | <trigger / constraint / test> |

An invariant that only holds when our code is the sole writer is not an invariant.

## Common mistakes

Numbered. The specific traps that have caught people (or would). Each: the mistake, and why
it is wrong.

## Entry gate for the next module — satisfied?

Name the downstream entry gate this module was responsible for, and state whether and how it
is satisfied.

## What the next module may depend upon

The guarantees this module provides, stated as promises the next engineer can build on.

## What this module deliberately does not give you

The explicit deferrals — the columns/ports that exist but whose driver arrives later, the
policy not yet wired — so the next engineer does not assume a capability that is not there.
