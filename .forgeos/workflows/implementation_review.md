# Workflow — Implementation Review

Review of a code change against its design and the engineering standards, before it merges.
A failing gate blocks the merge.

**Primary role:** Technical Reviewer, with the Security Reviewer for any change touching the
trust boundary, the runtime, or data handling. The author does not review their own change.

## Inputs

- The change (diff or PR, using `../templates/pull_request.md`).
- The module's review guide (`../templates/architecture_review.md` produces it) — where the
  risk is and what to read.
- The approved design, the applicable ADRs, and the test/CI evidence.

## Outputs

- A verdict: approve, or block with specific findings.
- Findings recorded where they can be acted on (inline PR comments or a review report).

## Decision gates

The change passes only if all of the following hold:

- [ ] **Ownership and dependency direction** — code depends on ports owned by the consumer;
      no forbidden imports across boundaries (e.g. ORM types outside the database layer).
- [ ] **Compatibility** — no frozen contract changed silently; schema changes carry a
      migration with forward-safety and rollback.
- [ ] **Validation** — validated at the transport boundary and critical invariants
      revalidated in the domain.
- [ ] **Idempotency** — replays are safe; unique constraints, not check-then-insert.
- [ ] **Error transparency** — typed errors mapped once; a platform fault and a user-visible
      verdict are not confused.
- [ ] **Redaction** — no container IDs, host paths, traces, credentials, or raw provider
      errors on a public surface; sensitive logs treated as sensitive.
- [ ] **Cleanup** — every side effect has a timeout, a classified failure, and idempotency
      or cleanup.
- [ ] **Tests** — unit, contract, integration, and (where relevant) end-to-end and
      regression; new port methods added to the conformance suite; coverage meets the gate.
- [ ] **Docs** — implementation note, handoff, and any config/migration/rollback notes are
      present and accurate.
- [ ] **Scope** — the change stays within the approved design; no placeholder, bypass, or
      hidden global state.

## Exit criteria

Every gate passes and every finding is resolved; the change is approved with its evidence
verified on the correct commit. Otherwise it is blocked with a specific, addressable list of
findings.

## Failure handling

- **A gate fails:** block the merge; do not merge around it.
- **Evidence missing or on the wrong commit:** block until it exists and is verified against
  the Actions API, not a report.
- **An implicit decision surfaced:** require it to be recorded — a module decision, or an ADR
  if it is architectural.
- **Scope creep:** block; route the extra scope back through design/decision as its own work.

## Review loop

Blocked changes return to the build step of
[`module_development.md`](module_development.md). Re-review after fixes; approval is only
valid against the reviewed commit.
