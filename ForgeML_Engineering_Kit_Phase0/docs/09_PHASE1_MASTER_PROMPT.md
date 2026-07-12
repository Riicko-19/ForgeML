# Phase 1 Engineering Operating Contract

This is the working brief for Phase 1. It governs collaboration; it does not override architecture documents.

## Objective

Deliver Foundation and Forge Package phases from docs 06: typed configuration/composition, error/logging conventions, and validated immutable .forge package capability. Do not begin deployment/runtime implementation before this exit gate passes.

## Required workflow

1. **Read:** Review docs 00–12, diagrams, and assigned role profile.
2. **Plan:** State boundary, public contract, assumptions, risks, acceptance tests.
3. **Review:** Chief Architect checks contract/ADR conflict and assigns owner.
4. **Implement:** Stay inside owned boundary and docs 02/05 direction.
5. **Test:** Add/execute unit, contract, and relevant integration tests including negative cases.
6. **Document:** Update contract, ADR, operations, diagram, or role profile for behavior change.
7. **Freeze/handoff:** Record interface, evidence, risks, migration/rollback notes. Dependents start only against frozen interface.

## Collaboration rules

- One agent owns one module/change; others use its public contract.
- Escalate upstream ambiguity as architecture decision; do not solve it locally.
- Do not implement a future module as shortcut; add/extend the relevant port.
- Shared contract edits have one editor; independent artifacts may proceed concurrently.
- Test failure, undocumented assumption, or security violation blocks handoff.
- Done means documented and verified, not merely compiling.

## Phase 1 scope

**In:** typed configuration/composition, error envelope, correlation/structured logging, streaming artifact store, manifest parser/validator, immutable package catalog, valid/invalid fixtures, package contract tests.

**Out:** Docker build/start, model import/execution, runtime probing, routing, dashboard, database-provider optimization, monitoring UI.

## Exit acceptance

- Valid upload yields immutable checksum-backed metadata and normalized manifest.
- Validator covers docs 04/12 rejection cases without importing package code.
- Duplicate upload, archive safety, schema/version/framework checks, redaction, cleanup have automated evidence.
- Ports are stable/documented/usable with fakes.
- Docs 06–08 quality gates pass.

## Handoff template

| Item | Evidence |
| --- | --- |
| Scope | Files/modules/public interfaces |
| Contract | Link/name/version/compatibility |
| Tests | Commands/suites/results |
| Failure | Error codes, cleanup, telemetry |
| Security | Inputs, boundary, redaction/isolation |
| Operations | Config, migrations, rollback/reconciliation |
| Open items | Owner and decision deadline |

Never claim tests not executed or replace acceptance with informal demo.

