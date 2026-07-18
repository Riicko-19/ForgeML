# Review Guide — <module/change>

> Template. Copy and fill in. A review guide tells a reviewer where the risk is and what to
> read, so the review is fast and targeted. Delete these quotes when using it.

**Estimated review time:** ~<n> minutes · **Author:** <role/name> · **Commit:** <SHA>

## Where the risk is

One or two sentences. Which file or decision carries almost all of the risk. If most of the
module is transport over already-frozen contracts, say so.

## Read in full (<n> min)

| File / unit | Why it matters |
| --- | --- |
| `<path>` | <the load-bearing logic; what breaks if it is wrong> |

## The tests that pin behavior (<n> min)

| Test | What it pins |
| --- | --- |
| `<test name>` | <the invariant or decision it protects> |

## Skim (<n> min)

The remaining files, named, with a one-line reason each is safe to skim.

## Questions the reviewer should answer

Numbered, specific, arguable. The decisions most likely to be questioned — state them plainly
so the reviewer engages them rather than missing them.

## Risks

| Risk | Severity | Mitigation |
| --- | --- | --- |
| | Low/Med/High | |

## If you have <n> minutes

The one or two things to read if time is short. If those are right, the change is right.
