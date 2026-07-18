# Dependency Report — ForgeML 0.9.1

**Audited:** 2026-07-18 · **Baseline:** `backend/requirements.lock`,
`backend/requirements-dev.lock` · **Tools:** `pip-audit`, `pip-licenses`,
`pip list --outdated`

Reproduce with the commands in [Method](#method).

---

## Summary

| Check | Result |
| --- | --- |
| Known vulnerabilities (runtime lock) | **0** — was 6, all fixed in this release |
| Known vulnerabilities (dev lock) | **0** |
| License conflicts with Apache-2.0 | **0** — one obligation to note (psycopg) |
| Unpinned dependencies | **0** — every dependency is `==` pinned and hash-locked |
| Unused declared dependencies | **0** |
| Duplicate / conflicting versions | **0** |
| Outdated (patch drift, non-blocking) | 7 |

---

## Vulnerabilities

### Fixed in this release

`python-multipart` 0.0.20 carried six advisories. This is the multipart parser
behind package upload — an endpoint with no authentication in front of it — so
five of the six were reachable by any client that can reach the control plane.

| ID | Impact | Applies | Fixed in |
| --- | --- | --- | --- |
| `PYSEC-2026-3039` | Unbounded part-header count/size → denial of service | Yes | 0.0.27 |
| `PYSEC-2026-3038` | Inefficient preamble/epilogue parsing → denial of service | Yes | 0.0.26 |
| `PYSEC-2026-3040` | Negative `Content-Length` → read-until-EOF, whole body in memory | Yes | 0.0.31 |
| `PYSEC-2026-3037` | `;` treated as a urlencoded separator → parser differential | Yes | 0.0.30 |
| `PYSEC-2026-3036` | Quadratic separator lookup on `;` bodies | Yes | 0.0.30 |
| `PYSEC-2026-1852` | Path traversal via kept upload filename | **No** | 0.0.22 |

`PYSEC-2026-1852` requires `UPLOAD_DIR` together with `UPLOAD_KEEP_FILENAME`.
ForgeML uses neither: uploads arrive through Starlette, which spools to a
temporary file, and the artifact store names files by SHA-256 (ADR-003) rather
than by any attacker-supplied name.

Resolved by pinning `python-multipart==0.0.32`, which clears all six. Both locks
re-audit clean.

### Current state

```
runtime lock:  No known vulnerabilities found
dev lock:      No known vulnerabilities found
```

---

## Licenses

ForgeML is Apache-2.0. Every runtime dependency is compatible.

| License | Count | Packages |
| --- | --- | --- |
| MIT | 15 | SQLAlchemy, alembic, fastapi, pydantic, pydantic_core, jsonschema, jsonschema-specifications, referencing, rpds-py, anyio, attrs, annotated-doc, annotated-types, typing-inspection, Mako, PyYAML, h11 |
| BSD-3-Clause | 5 | starlette, uvicorn, click, idna, MarkupSafe |
| Apache-2.0 | 1 | python-multipart |
| Apache-2.0 OR BSD-2-Clause | 1 | packaging |
| PSF-2.0 | 1 | typing_extensions |
| MIT AND PSF-2.0 | 1 | greenlet |
| **LGPL-3.0-only** | 2 | **psycopg, psycopg-binary** |

### The one obligation: psycopg is LGPL-3.0

This is compatible with an Apache-2.0 project and does not make ForgeML LGPL,
but the reasoning should be on the record rather than assumed:

- ForgeML **uses** psycopg as a separately installed, unmodified package. It does
  not vendor it, statically link it, or distribute it. `pip` fetches it from
  PyPI at install time.
- The LGPL's copyleft attaches to modifications of the library and to
  distributions that deny the user the ability to replace it. Neither applies:
  a user can swap the installed psycopg for their own build without touching
  ForgeML.
- ForgeML distributes only its own wheel and sdist, which contain no psycopg
  code.

**If that ever changes** — vendoring psycopg, shipping a container image that
bundles it, or patching it — the obligation changes with it, and the image or
bundle must carry the LGPL text and an offer of source. Worth re-checking when
ForgeML starts publishing images.

No GPL, AGPL, SSPL, BUSL, or commercial-restricted licenses are present.

---

## Outdated packages

Patch-level drift only. **Not upgraded** — this release upgrades exactly one
dependency, for security, and a freeze baseline is the wrong moment to absorb
unforced change.

| Package | Pinned | Latest | Kind |
| --- | --- | --- | --- |
| coverage | 7.15.0 | 7.15.2 | dev |
| fastapi | 0.139.0 | 0.139.2 | runtime |
| mypy | 2.2.0 | 2.3.0 | dev |
| pip-tools | 7.5.3 | 7.6.0 | dev |
| platformdirs | 4.10.0 | 4.10.1 | transitive (dev) |
| pydantic_core | 2.46.4 | 2.47.0 | transitive (runtime) |
| ruff | 0.15.21 | 0.15.22 | dev |

None carries an advisory. `mypy` 2.3.0 is a minor bump and may surface new
strict-mode findings; take it deliberately after the freeze, not inside it.

---

## Pinning and supply chain

- Every dependency is pinned with `==` in `pyproject.toml` (ADR-011 applies the
  same rule to `.forge` packages, so the project holds itself to what it demands
  of its users).
- Both lock files carry `--hash` for every artifact. Installs use
  `--require-hashes`, so a substituted artifact fails the install rather than
  running.
- CI recompiles both locks and `cmp`s them against the committed files. A lock
  that only reproduces on one machine fails the build.
- `setuptools==83.0.0` is pinned as the build backend; builds run with
  `--no-build-isolation` against the locked set.
- Verified for this release: both locks recompile byte-identically on a clean
  machine.

**Not yet in place:** no automated dependency-update job, and no scheduled
`pip-audit` run in CI. Advisories are found when someone looks. That is the
main supply-chain gap and is recorded in the readiness report.

---

## Unused and duplicate dependencies

Each of the ten declared runtime dependencies is imported by `backend/src`:

| Package | Used for |
| --- | --- |
| alembic | migrations |
| fastapi | HTTP application |
| jsonschema | `.forge` manifest validation (Draft 2020-12) |
| packaging | PEP 508 dependency-pin parsing (ADR-011) |
| psycopg[binary] | PostgreSQL driver (ADR-009) |
| pydantic | configuration and API schemas |
| python-multipart | package upload parsing |
| pyyaml | manifest documents |
| sqlalchemy | metadata persistence |
| uvicorn | ASGI server |

No package appears at two versions in either lock.

---

## Method

```bash
# Advisories
pip-audit -r backend/requirements.lock --no-deps
pip-audit -r backend/requirements-dev.lock --no-deps

# Licenses (in a venv holding only the runtime lock)
python3.11 -m venv /tmp/lic-venv
/tmp/lic-venv/bin/pip install --require-hashes -r backend/requirements.lock
/tmp/lic-venv/bin/pip install pip-licenses
/tmp/lic-venv/bin/pip-licenses --format=markdown --order=license

# Drift
backend/.venv/bin/python -m pip list --outdated

# Lock reproducibility (what CI enforces)
cd backend
python -m piptools compile pyproject.toml --resolver=backtracking \
  --generate-hashes --strip-extras --no-header --no-emit-index-url \
  --output-file /tmp/requirements.lock
cmp requirements.lock /tmp/requirements.lock
```

`pip-audit` and `pip-licenses` are deliberately **not** development dependencies.
They are audit tools, not build tools, and adding them to the locked set would
enlarge the hash-verified surface that every contributor installs in order to run
something nobody runs on every commit.
