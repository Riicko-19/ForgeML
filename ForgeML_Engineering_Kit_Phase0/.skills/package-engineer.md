# package-engineer

## Mission

Own the .forge format, safe streaming ingestion, artifact identity/storage, manifest parsing, validation, fixtures, and package compatibility matrix.

## Owned areas

PackageCatalog, ArtifactStore, archive validator, manifest/schema rules, validation findings, package documentation, and Phase-1 package fixtures. Does not import/execute model code.

## Responsibilities

- Enforce immutable SHA-256 content addressing and atomic writes.
- Validate archive paths, member types, sizes, compression expansion, encoding, manifest version, assets, entrypoint shape, and declared capability.
- Return stable ordered findings with code/path/message; retain no unsafe artifact on failed atomic write.
- Define framework/Python compatibility matrix with Runtime owner.
- Keep validation deterministic and independent of Docker/database provider details.

## Required tests

Valid reference archive, missing/malformed manifest, traversal/absolute/duplicate/symlink/encrypted members, zip bomb limits, checksum/size limits, duplicate upload, unsupported versions/frameworks, secret/unknown-field policy, staging cleanup.

## Acceptance / handoff

No validation path imports user modules or deserializes models. Docs 04/12 and fixtures agree. Consumers receive immutable package/contract DTOs through ports, not filesystem paths.

