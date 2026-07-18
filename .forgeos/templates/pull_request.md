# Pull Request — <title>

> Template. Copy into the PR description and fill in. Delete these quotes when using it.

## What and why

One paragraph: what this change does and the problem it solves. Link the module plan or the
issue.

## Scope

- Module / phase: <n>
- Frozen upstream contract relied upon: <named, with the ADR/module that froze it>
- ADRs applied or introduced: <ADR-NNN …>

## Change summary

The notable files and what each does at a high level. Point to the review guide for where the
risk is.

## Evidence

- [ ] Unit / contract / integration tests pass; new port methods added to the conformance
      suite
- [ ] End-to-end / regression tests where relevant
- [ ] Type, lint, format clean
- [ ] CI (`backend-quality.yml`) status: <status> on <SHA> — stated honestly
- [ ] Coverage meets the module gate: <value>

## Checklists

- [ ] No frozen contract changed silently (a change would carry an architecture diff + ADR)
- [ ] Side effects have timeout, classified failure, correlation, idempotency/cleanup
- [ ] No transaction spans provider work
- [ ] Errors typed and mapped once; no internal detail on a public surface
- [ ] No placeholder, stub-as-feature, or hidden global state
- [ ] Docs updated (implementation note, handoff, config/migration/rollback)
- [ ] Security / resource-boundary impact reviewed

## Deferrals

What this PR deliberately does not do, and why each deferral is non-blocking.

## Reviewer

Review guide: <link>. The author does not self-approve; a failing gate blocks merge.
