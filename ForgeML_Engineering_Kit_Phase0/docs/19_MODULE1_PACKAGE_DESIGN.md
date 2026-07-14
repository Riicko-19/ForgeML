# Module 1 — Forge Package System Design

Owner: Package Engineer. Reviewed by Chief Architect, Backend, Security, QA, and
Documentation. This document is normative for the .forge format implementation and
is subordinate to FEK, the ADR register, and docs 04/12.

## Scope

Roadmap phase 1 delivers "archive schema, streaming store, validation, fixtures".
This module implements exactly that surface:

- the format version 1 manifest model,
- content-addressed streaming artifact storage,
- archive validation that executes no package code,
- safe extraction into a caller-owned staging directory,
- the reference fixture matrix.

Explicitly **not** in this module, by roadmap order: `POST /packages` and any other
HTTP surface (phase 3), package metadata persistence and the `PackageCatalog` adapter
(phase 2), inference-contract analysis (phase 4), Docker, deployment, and runtime
(phases 5+). No placeholder or stub for those is introduced, per the roadmap
definition-of-done rule against placeholders and bypasses.

## Scope audit

The V1 scope audit found nothing to remove. No Kubernetes, MLflow, Redis, Kafka,
queueing, autoscaling, plugin, marketplace, cloud, distributed, microservice,
enterprise, LLM, or GPU-scheduling concept enters the package path. Validation runs
in-process and synchronously; ADR-006 durable operations wrap it in phase 3, not here.

## Layering

Docs 05 forbids the domain from importing a provider, a transport, or a filesystem
API. The .forge format is therefore split so that "a package is a ZIP" is knowledge
held only by the infrastructure adapter:

| Layer | Component | Responsibility |
| --- | --- | --- |
| domain | `domain/package/models.py` | Manifest model, archive facts, finding codes, validation result |
| domain | `domain/package/ports.py` | `ArtifactStore`, `ArchiveReader`, `StoredArtifact` |
| domain | `domain/package/rules.py` | All validation policy, as pure functions |
| application | `application/package/validate_package.py` | `PackageValidationService`, composing store and reader |
| infrastructure | `infrastructure/package/zip_archive.py` | `ZipArchiveReader`: the only ZIP-aware module |
| infrastructure | `infrastructure/storage/artifact_store.py` | `FilesystemArtifactStore`: atomic content-addressed writes |

`domain/package/rules.py` imports `jsonschema` and `packaging`. Both are pure
validation libraries with no I/O, no provider, and no transport; docs 12 requires the
platform to validate the *full Draft 2020-12 vocabulary implemented by its pinned
validator*, which makes the validator a normative part of package policy rather than
an adapter detail. The domain remains free of `yaml`, `zipfile`, `pathlib`, `os`, and
every provider SDK, and `tests/architecture/test_dependency_direction.py` enforces
that list by AST.

## Dependencies added

Approved for this module; all three are forced by frozen contracts:

| Dependency | Why it cannot be avoided |
| --- | --- |
| `pyyaml==6.0.3` | forge.yaml is YAML (docs 04) |
| `jsonschema==4.26.0` | docs 12 mandates a pinned Draft 2020-12 validator |
| `packaging==26.2` | ADR-011 requires PEP 508 pin enforcement |

They are control-plane dependencies. ADR-011 governs *package* dependencies and does
not apply to them. Both hash-locks were regenerated with the pip-tools commands the
CI workflow verifies by `cmp`.

## Artifact identity and storage

ADR-003: the SHA-256 of the archive bytes is the package identity. `put` streams the
upload in 1 MiB chunks, hashing as it goes, into a staging file under
`<root>/.staging`, then fsyncs and `os.replace`s it to `<root>/ab/cd/<sha256>`. The
rename is atomic, so a partial or failed write never becomes an artifact; the staging
file is removed on every path. Storing bytes that are already present returns the
existing artifact, which is what makes duplicate upload idempotent (ADR-003).

Callers never receive a filesystem path. An artifact is referenced by
`artifact://<sha256>`, and any reference that is not a lower-case 64-character digest
is refused before it can touch the filesystem, which closes the path-traversal route
into the store.

## Validation

Validation is staged, and each stage is a precondition for the next:

1. **Archive structure**, from ZIP central-directory headers only. No member content
   has been read at this point, so a hostile archive is rejected before the validator
   spends bytes on it.
2. **Manifest document** — present, within the size cap, parsable, a mapping.
3. **Manifest shape** — the closed `ManifestV1` model; unknown fields rejected at
   every level.
4. **Compatibility matrix** (ADR-008) — forge_version 1, python-callable, Python 3.11.
5. **Cross-checks** — entrypoint module present under `src/`, dependency pins,
   JSON Schema documents, declared assets present.
6. **Asset checksums** — the only rule that reads member bytes, and it runs only
   after the archive is known safe and the manifest is known valid.

Findings are `core.errors.ErrorDetail` values, reused from Module 0 rather than
reinvented: they already carry the stable `code` / `message` / `path` triple that the
package owner's handoff requires and that docs 12 renders as error-envelope `details`.
Findings are emitted in a fixed stage order and are capped at 50 plus a
`findings_truncated` marker, so a hostile archive cannot produce an unbounded report.

Archive-supplied names are sanitized before being placed in a finding path — stripped
of control characters and truncated to 128 characters. Without that, a hostile member
name would make the error contract itself raise.

### Resource bounds

`PackageLimits` is operator policy loaded through the Module 0 fail-closed loader, so
an unknown or invalid `FORGEML_PACKAGE_*` key still fails startup rather than falling
back to a default. Every bound is checked before the corresponding bytes are read.

| Setting | Default | Bounds |
| --- | --- | --- |
| FORGEML_PACKAGE_MAX_ARCHIVE_BYTES | 268435456 | 1 KiB – 16 GiB |
| FORGEML_PACKAGE_MAX_UNCOMPRESSED_BYTES | 1073741824 | ≥ max archive bytes |
| FORGEML_PACKAGE_MAX_ENTRIES | 10000 | 1 – 1000000 |
| FORGEML_PACKAGE_MAX_COMPRESSION_RATIO | 100 | 1 – 10000 |
| FORGEML_PACKAGE_MAX_MANIFEST_BYTES | 1048576 | ≤ max archive bytes |
| FORGEML_PACKAGE_MAX_SCHEMA_NODES | 1000 | 1 – 100000 |
| FORGEML_PACKAGE_MAX_SCHEMA_DEPTH | 20 | 1 – 256 |
| FORGEML_ARTIFACT_ROOT | storage/artifacts | — |

The schema walk runs *before* the pinned validator: a schema deeper than policy would
otherwise recurse inside `jsonschema` before any limit could reject it.

## Security review

- **No package code is imported, executed, or deserialized.** An architecture test
  parses every package-path module and fails on any import of `importlib`, `runpy`,
  `pickle`, `marshal`, `shelve`, `subprocess`, `joblib`, or `torch`, and on any call
  to `eval`, `exec`, `compile`, or `__import__`. This is the package owner's
  acceptance gate, enforced mechanically rather than by review.
- **Zip-slip** is rejected at validation (absolute, traversal, non-normalized,
  duplicate, and non-UTF-8 member paths) and again at extraction, which re-resolves
  every target against the destination root and refuses anything outside it.
- **Symbolic links and encrypted members** are rejected; both are also refused at
  extraction.
- **Zip bombs** are bounded by entry count, total expansion, and a per-member
  compression ratio applied above a 1 MiB floor, so ordinary small text files are not
  misreported.
- **YAML alias bombs**: `yaml.safe_load` still expands aliases, so a small forge.yaml
  can allocate gigabytes through repeated references. The manifest loader derives from
  `SafeLoader` and additionally refuses aliases outright, which a manifest never needs.
- **A lying ZIP header** cannot smuggle an oversized manifest: the declared size is
  checked, and the delivered length is checked again after the bounded read.

## Tests

224 tests pass with 99% branch coverage (gate: 95%).

- `tests/contract/test_package_fixtures.py` — the reference fixture matrix: 30 hostile
  or invalid archives, each asserting the stable finding code a client receives, plus
  the minimal valid CPU package, a valid package with a verified asset, finding-path
  stability, and determinism across repeated runs. Archives are built in memory, so no
  model, credential, or personal data is committed.
- `tests/unit/domain/package/` — validation policy over synthetic archive facts, and
  the closed manifest model.
- `tests/integration/package/`, `tests/integration/storage/` — the real ZIP reader and
  the real artifact store, including idempotent duplicate upload, refusal of oversized
  uploads with no residue, staging cleanup on failure, and safe extraction.
- `tests/architecture/` — dependency direction and the no-execution gate.

## Known limitations

- `PackageCatalog` is not implemented. Package records, validation persistence, and
  `Package`/`PackageValidation` durability are phase 2, and the port is introduced
  there with its adapter rather than as an unused interface here.
- Validation is synchronous and in-process. ADR-006 wraps it in a durable operation in
  phase 3; nothing in this module assumes a synchronous caller.
- Asset checksum verification reads only the assets that declare a checksum. Members
  without a declared checksum are checked for presence, not content.
- The compression-ratio floor is a fixed 1 MiB rather than policy. It is marked in the
  source and can become a setting if a real package trips it.

## Acceptance checklist

| Gate | Evidence |
| --- | --- |
| Validation executes no package code | Architecture test over every package-path module |
| Findings stable, ordered, code/path/message | Contract matrix; determinism test |
| Atomic checksum-verified writes, no residue on failure | Artifact store integration tests |
| Duplicate upload idempotent | Artifact store integration test |
| Docs 04/12 and fixtures agree | Contract matrix asserts the docs 12 manifest table |
| Consumers receive DTOs, not filesystem paths | `artifact://` URI; ports return `StoredArtifact` |
| Lint, format, strict types | black, ruff, mypy strict all clean |
| Coverage ≥ 95% branch | 99% |
| Locks reproducible | Both locks regenerate byte-identically |
| Installed wheel smoke | Clean 3.11 venv, runtime lock, wheel installed `--no-deps` |
| **CI workflow evidence** | **Not yet run — see below** |

## Freeze status

**Module 1 is implementation-complete but NOT frozen.**

ADR-014 requires passing GitHub Actions backend-quality workflow evidence for module
completion, and records explicitly that the Module 0 evidence exception "neither
removes the workflow nor permits local-only evidence for later modules or later
backend changes." Every gate the workflow runs has been executed locally on Python
3.11 and passes, but local execution is not the workflow. Freezing Module 1 requires
the changes to be pushed and the workflow to pass.
