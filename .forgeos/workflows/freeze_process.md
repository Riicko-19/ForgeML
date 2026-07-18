# Workflow — Freeze Process

The process that turns a reviewed, merged module into a **frozen** one whose public contract
downstream modules may depend on. Freezing requires evidence, not assertion (ADR-014).

**Primary role:** Release Manager, with the Chief Architect confirming the frozen public
surface.

## Inputs

- A reviewed, merged module that passed implementation review.
- Its handoff document (`../templates/handoff.md`) and applicable ADRs.
- The exact commit proposed as the frozen baseline.

## Outputs

- CI evidence verified on the frozen commit.
- The frozen public surface recorded, with carried-forward limitations.
- `PROJECT_STATUS.md` updated: baseline commit, freeze date, freeze authority.

## Decision gates

A module freezes only if all of the following hold:

- [ ] The GitHub Actions backend quality workflow **passed on the exact frozen commit** —
      verified against the Actions API, not accepted on a report (ADR-014).
- [ ] The phase's exit-gate evidence passed (the specific tests the roadmap names).
- [ ] The frozen public surface is explicitly listed: the contracts downstream may rely on
      exactly as written.
- [ ] Known limitations are carried forward in the handoff — explicit, not implied.
- [ ] The definition of done (constitution doc 04) holds in full.

## The one exception

The single closed exception is ADR-014's Module 0 evidence exception, necessitated by the
absence of a usable repository or remote at the time. It does not extend to any later
module. A recorded exception is **never** described as a passing run: the test report must
identify the CI run as not executed.

## Recording the freeze

On success, record in `PROJECT_STATUS.md`: status **Frozen**, freeze date, freeze authority
(the ADR), and the baseline commit SHA. Add the module summary to
[`../engineering_memory/module_history.md`](../engineering_memory/module_history.md) and any
newly frozen contract to
[`../engineering_memory/architecture_evolution.md`](../engineering_memory/architecture_evolution.md).

## Exit criteria

The module is recorded as frozen with a cited baseline commit and the CI run that proves it,
its public surface is fixed, and its limitations are carried forward. From here the contract
is law for its consumers and changes only by a superseding ADR.

## Failure handling

- **CI did not pass on the frozen commit:** do not freeze. Fix and re-run; local success does
  not substitute.
- **CI evidence is on a different commit:** do not freeze; the baseline and the evidence must
  be the same SHA. A later remote does not retroactively constitute evidence.
- **Public surface unclear:** do not freeze until it is enumerated — an unstated contract
  cannot be depended on safely.
