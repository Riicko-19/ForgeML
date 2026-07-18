# Role — Technical Reviewer

A role definition, not a person or a product. Any contributor who reviews a change adopts
this role and is bound by it. The reviewer is not the author; a change is not self-reviewed.

## Mission

Ensure a change is correct, safe, within scope, and consistent with the architecture and
the standards before it merges — and that a failing gate blocks the merge.

## Responsibilities

- Review against the module's review guide and
  [`../workflows/implementation_review.md`](../workflows/implementation_review.md).
- Verify ownership and dependency direction, compatibility, validation, idempotency, error
  transparency, redaction, cleanup, tests, docs, and migration/operations.
- Confirm the change stays within the approved design and the charter scope.
- Confirm the evidence: tests, coverage, and CI status on the correct commit.

## Authority

- May block a merge for any failing gate, missing evidence, or standards violation.
- May require additional tests, documentation, or an ADR where a decision was made
  implicitly.
- May not wave through a change on trust; the evidence must exist and be checked.

## Workflow

Follows [`../workflows/implementation_review.md`](../workflows/implementation_review.md).
For a design (not code), follows
[`../workflows/architecture_review.md`](../workflows/architecture_review.md).

## Inputs

- The change (diff or PR) and its review guide.
- The approved design and the applicable ADRs.
- The test and CI evidence.

## Outputs

- A review verdict: approve, or block with specific, addressable findings.
- Findings recorded where the team can act on them (PR comments or a review report).

## Quality expectations

- Every finding is specific: a location, the defect, and what would resolve it.
- Risk is stated with severity and mitigation.
- The review distinguishes a platform fault from a user-visible verdict, and a real bug
  from a style preference.

## Must never do

- Review one's own change as the sole reviewer.
- Approve without checking that the claimed evidence actually exists on the correct commit.
- Confuse a recorded exception with a passing gate.
- Let scope creep or an undocumented decision pass silently.
