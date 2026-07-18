# Release Workflow

The policy is [ADR-021](../ForgeML_Engineering_Kit_Phase0/docs/10_ARCHITECTURE_DECISIONS.md);
this document is how to execute it. Release automation is deliberately not
implemented yet — these steps are run by hand until the policy has proven stable.

---

## Versioning

ForgeML follows [Semantic Versioning 2.0.0](https://semver.org/). Three public
contracts version independently:

| Contract | Versioned by | Breaking change |
| --- | --- | --- |
| HTTP API | URL prefix (`/v1`) | New prefix; `/v1` keeps its promise |
| `.forge` package format | `format_version` in the manifest | New format version; old stays readable |
| Python distribution | SemVer | Major bump |

### Current status: `0.x`

ForgeML is pre-1.0 and **carries no compatibility guarantee**. That is what `0.x`
means and the project says it plainly rather than implying a promise it cannot
keep. The compatibility rules below take effect at 1.0.

---

## Compatibility promise (from 1.0)

Within a major version, ForgeML will not:

- remove an endpoint
- remove a field from a response
- make an optional request field required
- change what an error `code` means
- change what a `.forge` manifest field means

These are **minor** releases: a new endpoint, a new optional request field, a new
response field, a new error code, a new manifest field with a default.

**Clients must tolerate unknown response fields.** A client that breaks on a new
field is relying on something never promised.

---

## Deprecation

1. Announce in the release notes of the version that deprecates it.
2. Mark it in the OpenAPI description and its docstring.
3. Keep it working for **at least one minor release**.
4. Remove only in the next major.

Nothing is ever removed in a patch release.

---

## Branch strategy

`main` is the only long-lived branch and is always releasable. Work merges via
pull request with `make verify` green. Releases are annotated tags: `v0.9.0`.

No release branches before 1.0 — with one supported version there is nothing to
back-port to, and an unused branch strategy is a process that exists only to be
followed.

---

## Migrations

Forward-only, via Alembic.

- Every migration is additive or reversible.
- A released migration is never edited or squashed.
- Release notes name every migration and flag any that takes a lock.
- Additive-nullable is the default shape (see ADR-018 for the pattern).

Operators run `make migrate` before starting the new version.

---

## Cutting a release

```bash
# 1. Confirm main is green
git checkout main && git pull
make verify

# 2. Confirm CI passed on this exact SHA — local green is not release evidence
gh run list --branch main --limit 1

# 3. Bump the version in backend/pyproject.toml, then refresh the locks
make setup

# 4. Update PROJECT_STATUS.md and write the release notes

# 5. Commit, tag, push
git commit -am "release: v0.9.0"
git tag -a v0.9.0 -m "ForgeML 0.9.0"
git push origin main --tags
```

### Checklist

- [ ] CI green on the tagged SHA (ADR-014 — this is the evidence, not local green)
- [ ] Version bumped in `backend/pyproject.toml`
- [ ] Lock files regenerated and committed
- [ ] `PROJECT_STATUS.md` reflects reality
- [ ] Release notes list every change, migration, and deprecation
- [ ] Breaking changes called out at the top, with the upgrade path
- [ ] Installed-wheel smoke test passed in CI
- [ ] Tag is annotated, not lightweight

---

## Release notes format

```markdown
## v0.9.0 — 2026-07-18

### Breaking
<!-- Nothing, or: what broke and exactly how to migrate. -->

### Added
### Changed
### Fixed
### Deprecated
<!-- What, why, when it will be removed, what to use instead. -->

### Migrations
<!-- Every migration, and whether it takes a lock. -->
```

---

## Support policy

Before 1.0: only the latest release is supported. See
[`SECURITY.md`](../SECURITY.md) for vulnerability handling.

---

## Release readiness for 1.0

ForgeML reaches 1.0 when Modules 8, 9, and 10 are complete and frozen:

| Requirement | Module | State |
| --- | --- | --- |
| Monitoring and observability | 8 | Not started |
| Authentication and authorization | 9 | ADRs recorded (018–019); not implemented |
| Retention and disk-pressure policy | 10 | ADR-012 recorded; not implemented |
| Build-time isolation hardening | 10 | Gap documented in `SECURITY.md` |
| Rate limiting | 9 | Deferred by ADR-019 |
| Release automation | 10 | Policy recorded here; not implemented |

Declaring 1.0 before these means promising compatibility for a surface that is
still moving.
