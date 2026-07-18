# Release Checklist — <version / milestone>

> Template. Copy and fill in. Every box needs evidence, not a checkmark on trust.
> Delete these quotes when using it.

**Release manager:** <role/name> · **Date:** <YYYY-MM-DD> · **Composed of modules:** <list>

## Frozen inputs

- [ ] Every module in the release is **Frozen** with CI evidence on its baseline commit
      (per [`../workflows/freeze_process.md`](../workflows/freeze_process.md))
- [ ] Each frozen baseline commit is recorded: <module → SHA …>

## Reference test matrix

Each case passes (contract-correctness proof):

- [ ] Minimal valid CPU package deploys to an active route
- [ ] Invalid manifest rejected with a finding
- [ ] Path-traversal archive rejected before extraction
- [ ] Duplicate upload is idempotent
- [ ] Unsupported framework rejected
- [ ] Dependency-build failure diagnosed, not hidden
- [ ] Readiness timeout handled with a terminal reason
- [ ] Input-schema failure surfaced to the caller
- [ ] Model-execution failure surfaced with correlation and bounded logs
- [ ] Activation rollback restores the prior active version
- [ ] Docker container removed out-of-band is reconciled
- [ ] Control-plane restart reconciles in-flight operations

## Reproducibility

- [ ] Reference deployment reproduces on a clean supported host from docs + configuration
      alone (no private assumptions)
- [ ] Endpoint ready within the charter target for the reference CPU package

## Data and recovery

- [ ] Backups cover PostgreSQL and the artifact volume consistently (ADR-009)
- [ ] Restore procedure documented and exercised
- [ ] Rollback triggers and procedure documented before shipping

## Security and boundaries

- [ ] Isolation baseline verified (non-root, no Docker socket/host network/host mounts,
      limits) — Security Reviewer sign-off
- [ ] No secrets, raw provider errors, or internal identifiers on any public surface
- [ ] Supply-chain policy satisfied: pins, approved index, SBOM, base-image digest,
      vulnerability gate (ADR-011)

## Documentation

- [ ] Operations and configuration reference current
- [ ] Deferred concerns enumerated (not implied); each deferred milestone still needs an ADR
      to enter scope
- [ ] `PROJECT_STATUS.md` and engineering memory updated

## Sign-off

- [ ] Release Manager · [ ] Security Reviewer · [ ] Documentation Engineer
