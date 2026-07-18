# Changelog

All notable changes to ForgeML are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the versioning policy
is [ADR-021](ForgeML_Engineering_Kit_Phase0/docs/10_ARCHITECTURE_DECISIONS.md)
and the process is [`docs/RELEASE.md`](docs/RELEASE.md).

ForgeML is pre-1.0 and **carries no compatibility guarantee**. The compatibility
rules take effect at 1.0.

This file begins at 0.9.1. Earlier work is recorded per module in
[`PROJECT_STATUS.md`](PROJECT_STATUS.md), which remains the authority for what is
implemented and what is frozen.

---

## [Unreleased]

Nothing yet.

---

## [0.9.1] — 2026-07-18

**Platform Freeze & Release Readiness.** No features. This release converts a
stabilized repository into a verified engineering baseline: every claim the
repository makes about itself was re-derived from a clean clone rather than
carried forward from a document.

### Security

- **`python-multipart` upgraded 0.0.20 → 0.0.32**, clearing six advisories.
  Five apply to ForgeML because they sit on the package upload path, which has
  no authentication in front of it:
  - `PYSEC-2026-3039` — unbounded part-header count and size (denial of service)
  - `PYSEC-2026-3038` — inefficient preamble/epilogue parsing (denial of service)
  - `PYSEC-2026-3040` — negative `Content-Length` turned a bounded read into
    read-until-EOF, loading the whole body into memory at once
  - `PYSEC-2026-3037` — `;` treated as a field separator in urlencoded bodies,
    a parser differential against the WHATWG standard and `urllib.parse`
  - `PYSEC-2026-3036` — quadratic separator lookup on `;`-separated bodies

  `PYSEC-2026-1852` (path traversal) does not apply: it requires `UPLOAD_DIR`
  with `UPLOAD_KEEP_FILENAME`, which ForgeML does not use.

  Both lock files re-audit clean under `pip-audit`.

### Fixed

- **Distribution version was the `0.1.0` placeholder** while every document said
  0.9. `/health` and `/ready` report this value from installed distribution
  metadata, so the version was wrong on the wire, not just in packaging. Now
  `0.9.1`.
- **The database test conftest truncated four of six tables**, omitting
  `deployments` and `deployment_versions`. Rows leaked between tests in that
  package. All six are truncated now.
- **`docs/RELEASE.md` assigned authentication to Module 9**, contradicting
  `PROJECT_STATUS.md`, where phase 9 is Dashboard and authentication has no
  phase at all. The 1.0 readiness table now shows authentication as unassigned
  pending ADR-022.

### Added

- **`CHANGELOG.md`** — this file.
- **An activation concurrency test.** `lock_deployment` is plain `FOR UPDATE`
  and the atomicity of the route swap depends on it, but nothing exercised two
  callers contending for the same deployment. The new test drives two live
  PostgreSQL sessions and asserts the second blocks until the first commits. It
  was verified to fail when the lock is weakened to `SKIP LOCKED` — a
  concurrency test that cannot fail proves nothing.

### Changed

- Nothing in the public API, the `.forge` format, the database schema, or the
  architecture. No endpoint, request field, response field, or error code
  changed in this release.

### Migrations

None. No schema change.

### Known limitations

Carried forward and documented rather than closed — see
[`PLATFORM_READINESS_REPORT.md`](PLATFORM_READINESS_REPORT.md):

- Authentication has no phase assignment. ADR-022 is required.
- Docker integration tests skip silently when no daemon is present, so a run
  without Docker is not evidence for Module 6. They ran for this release.
- Artifacts accumulate without bound. ADR-012's retention policy is recorded
  but not implemented.
- Build-time package execution is not isolated to the degree runtime is. The
  gap is documented in [`SECURITY.md`](SECURITY.md).
- The control plane is root-equivalent through the Docker daemon by design.

[Unreleased]: https://github.com/Riicko-19/ForgeML/compare/v0.9.1...HEAD
[0.9.1]: https://github.com/Riicko-19/ForgeML/releases/tag/v0.9.1
