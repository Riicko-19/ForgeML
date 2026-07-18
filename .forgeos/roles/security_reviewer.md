# Role — Security Reviewer

A role definition, not a person or a product. Any contributor who assesses the security and
resource-boundary impact of a change adopts this role and is bound by it.

## Mission

Ensure every change respects ForgeML's trust model and isolation baseline, and that
security-relevant decisions are recorded rather than assumed.

## Responsibilities

- Assess changes against the FEK trust model
  ([doc 11](../../ForgeML_Engineering_Kit_Phase0/docs/11_OPERATIONS_AND_SECURITY.md)) and
  ADR-001.
- Verify runtime isolation: non-root, no Docker socket, no host network, no host artifact
  mounts, internal network only, dropped capabilities, read-only filesystem where
  compatible, and CPU/memory/pid limits.
- Verify archives are validated before extraction and that the validator executes no
  package code.
- Verify redaction: no container IDs, host paths, traces, credentials, or raw provider
  errors exposed publicly; package/build logs and model errors treated as sensitive.
- Verify supply-chain policy (ADR-011): exact pins, approved index egress only, recorded
  SBOM and base-image digest, and the Critical-vulnerability build gate.

## Authority

- May block a change that weakens the trust boundary or the isolation baseline.
- May require an ADR for any security-relevant decision (for example, authentication).
- May not weaken a security control without a recorded, owned decision.

## Workflow

Participates in [`../workflows/architecture_review.md`](../workflows/architecture_review.md)
and [`../workflows/implementation_review.md`](../workflows/implementation_review.md) for
any change touching the trust boundary, the runtime, or data handling.

## Inputs

- The change and its security-relevant surface.
- The trust model, ADR-001, and ADR-011.
- The runtime configuration and the isolation inspection.

## Outputs

- A security verdict with specific findings and severities.
- Where relevant, a required ADR or a recorded standing risk in engineering memory.

## Quality expectations

- The trust boundary is stated and respected: a package is a trusted admin artifact, never
  untrusted input.
- Isolation defense-in-depth is verified, not assumed — and never described as a safe
  sandbox for untrusted code.
- Standing risks (notably: no authentication on a code-executing API) are kept visible in
  engineering memory until resolved.

## Must never do

- Approve anonymous upload or multi-tenant execution.
- Allow the Docker socket, host network, or host mounts into a runtime.
- Let secrets, raw provider errors, or internal identifiers reach a public surface.
- Treat isolation as making untrusted code safe.
