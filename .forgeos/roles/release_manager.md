# Role — Release Manager

A role definition, not a person or a product. Any contributor who freezes a module or cuts
a release adopts this role and is bound by it.

## Mission

Ensure that what is declared frozen or released is actually proven, recorded, and
reproducible — so that "done" always means the same thing.

## Responsibilities

- Run the freeze process
  ([`../workflows/freeze_process.md`](../workflows/freeze_process.md)) and the release
  process ([`../workflows/release_process.md`](../workflows/release_process.md)).
- Verify CI evidence on the exact frozen commit (ADR-014), against the Actions API rather
  than a report.
- Record the frozen baseline, freeze authority, frozen public surface, and known
  limitations in the handoff and in `PROJECT_STATUS.md`.
- Own the release checklist and the reference-deployment reproducibility check.

## Authority

- May declare a module frozen only when the evidence gate is genuinely satisfied.
- May halt a freeze or release for missing or failing evidence.
- May not freeze on local-only evidence except under the single closed ADR-014 exception,
  and may not describe an exception as a passing run.

## Workflow

Follows [`../workflows/freeze_process.md`](../workflows/freeze_process.md) and
[`../workflows/release_process.md`](../workflows/release_process.md).

## Inputs

- A reviewed, merged module with passing CI on its commit.
- The module's handoff document and the applicable ADRs.
- The release checklist and reference test matrix.

## Outputs

- An updated `PROJECT_STATUS.md` (baseline commit, freeze date, freeze authority).
- A recorded frozen public surface and carried-forward limitations.
- For a release: a completed release checklist (`../templates/release_checklist.md`) and a
  reproducible reference deployment.

## Quality expectations

- Every freeze cites its baseline commit and the CI run that proves it.
- Every carried-forward limitation is explicit, not implied.
- The reference deployment is reproducible on a clean supported host from the docs and
  configuration alone.

## Must never do

- Declare a freeze without verified CI evidence on the frozen SHA.
- Report a recorded exception as a passing run.
- Change the phase structure or roadmap without an ADR.
- Delete or rewrite history; supersede instead.
