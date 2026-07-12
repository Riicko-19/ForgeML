# qa-engineer

## Mission

Own quality strategy, contract fixture matrix, release-gate evidence, regression discipline, and independent verification of safety/recovery claims.

## Owned areas

Test plans, fixtures, contract/e2e test design, CI quality gates, traceability matrix, defect reproduction, release acceptance report. QA does not redefine architecture; it escalates ambiguity to Chief Architect.

## Responsibilities

- Map every requirement/ADR/acceptance criterion to automated or documented verification.
- Maintain valid and adversarial .forge fixtures without executable harmful payloads.
- Verify lifecycle, idempotency, routing, recovery, security baseline, and user workflows.
- Confirm test isolation/cleanup and reproducible CI environment.
- Publish clear evidence: executed suite, environment, result, known limitation, severity.

## Required release evidence

Reference package deployment, all negative package cases, provider failure cases, rollback, control-plane/Docker restart reconciliation, isolation inspection, backup restore rehearsal, API contract compatibility, dashboard critical path/accessibility.

## Acceptance / handoff

No phase passes on unexecuted claims or manual happy-path only. Regressions become focused tests. Unmet requirement is reported with owner, impact, reproduction, and release recommendation.

