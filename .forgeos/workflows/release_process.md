# Workflow — Release Process

The process for cutting a ForgeML release. In V1 this culminates in the hardening/release
phase (roadmap phase 10), but the checklist discipline applies to any release built from
frozen modules.

**Primary role:** Release Manager, with the Security Reviewer for the security gate and the
Documentation Engineer for the docs gate.

## Inputs

- The set of frozen modules composing the release.
- The release checklist (`../templates/release_checklist.md`).
- The reference test matrix (roadmap) and the operations/security documentation.

## Outputs

- A completed release checklist with evidence.
- A reproducible reference deployment on a clean supported host.
- Recorded backup, rollback, and recovery procedures.

## Decision gates

A release proceeds only if all of the following hold:

- [ ] Every module in the release is **frozen** with CI evidence on its baseline (per the
      freeze process).
- [ ] The reference test matrix passes: minimal valid CPU package, invalid manifest, path
      traversal, duplicate upload, unsupported framework, dependency-build failure, readiness
      timeout, input-schema failure, model-execution failure, activation rollback, Docker
      container removed out-of-band, and control-plane restart reconciliation.
- [ ] The reference deployment is reproducible on a clean supported host from the docs and
      configuration alone.
- [ ] Backups cover PostgreSQL and the artifact volume consistently (ADR-009); restore is
      documented.
- [ ] The security and resource-boundary review passes; the isolation baseline is verified.
- [ ] Rollback triggers and procedures are documented before shipping.

## Exit criteria

The release checklist is complete with evidence, the reference deployment reproduces, and the
backup/rollback/recovery procedures are recorded and tested. Deferred concerns are enumerated,
not implied.

## Failure handling

- **A module is not frozen:** it is not in the release. Freeze it first, or cut the release
  without it.
- **A reference matrix case fails:** the release is blocked until fixed; the matrix is the
  contract-correctness proof.
- **Reference deployment is not reproducible:** block; a release that only the author can
  deploy is not a release.
- **Backup/restore unproven:** block; recovery is part of the release, not an afterthought.

## Note on scope

Deferred milestones (multi-user auth, remote orchestration, GPU policy, registries, package
signing, canary releases) are not release "small additions." Each requires an ADR to enter
scope. A release documents what is deferred; it does not quietly include it.
