# Module 4 — Analyzer / Generator (engineering note)

Owner: Lead ForgeML Engineer. Subordinate to docs 02/03/04/06 and the ADR register.

## The `PackageValidation.contract` field is a planned completion, not a change

The analyzed inference contract was designed in from the start and deferred to
this module, not omitted by accident:

- [04_LOW_LEVEL_DESIGN.md](04_LOW_LEVEL_DESIGN.md) lists "analyzed contract" among
  the required `PackageValidation` fields, defines the `PackageAnalyzer`
  ("derive inference contract; validated manifest only; no Docker/storage"), and
  reserves "get manifest/contract" on `PackageCatalog`.
- [20_MODULE2_METADATA_DESIGN.md](20_MODULE2_METADATA_DESIGN.md) states plainly:
  *"Not in this module: HTTP (phase 3), analyzer (4) … None of them is stubbed."*
- Module 2's decision D-6 established the pattern this follows: a field is
  nullable until the lifecycle stage that legitimately computes it
  (`manifest_version` was made null-until-validated for the same reason).

Adding the column now **activates a documented extension point**. It is
additive (nullable JSONB), reversible (drop_column), and backwards compatible:
existing rows stay null and no existing behaviour changes when the contract is
absent. Modules 0–3 are unchanged. This is architectural completion, not a
redesign, and does not reopen Module 2.

## Analyzer and Generator are pure functions, not Protocols

Repository precedent decides this: `PackageValidator` is listed as a "port" in
the LLD yet ships as the pure function `validate_package()` in rules.py. Every
actual Protocol in the codebase abstracts an I/O boundary (`ArtifactStore`,
`PackageCatalog`, `ArchiveReader`, …). The analyzer and generator perform no I/O
and are deterministic, so they are functions — `analyze()` in analyzer.py and
the generator in generator.py — following the same split.

## Determinism

The generator's artifact identity is a SHA-256 over the canonically serialized
generated file set. Identical `(contract, generator version, runtime, checksum)`
inputs produce byte-identical files and therefore an identical identity; any
meaningful input change changes it. No timestamps, absolute paths, or ordering
nondeterminism enter the generated output.
