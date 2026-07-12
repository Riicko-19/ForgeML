# Operations and Security

## Supported topology

One Linux host runs control plane, relational metadata database, local artifact/log storage, route proxy, and Docker Engine. Reverse proxy/TLS may be colocated. Model containers run on internal Docker network; only platform proxy reaches inference port. Expose dashboard/control plane only on protected administrative network until authorization ADR exists.

## Configuration inventory

| Category | Examples | Handling |
| --- | --- | --- |
| Platform | environment, public base URL, build version | Typed safe settings |
| Storage | artifact root, retention, archive/unpacked limits | Operator policy |
| Runtime | frameworks/base images, CPU/memory/pids, readiness, egress | Operator policy |
| Database | connection/migration state | Secret/config as appropriate |
| Docker/proxy | socket endpoint, internal network, route config | Privileged config; never frontend |
| Secrets | DB password, package-index credential | Secret mechanism; redacted/rotated |

Startup fails closed for missing/invalid required config or unavailable Docker/database/artifact storage. Production may not silently use development defaults.

The control plane owns the canonical request ID. It ignores inbound X-Request-ID
values, generates UUIDv4 identifiers, returns them on every HTTP response, and records
only the generated value in structured events.

## Default limits and operator policy

The documented defaults are: 500 MiB compressed archive, 2 GiB unpacked archive, 10,000 archive members, 100:1 maximum compression expansion ratio, 10 MiB prediction request and response bodies, 1,000 millicores/1,024 MiB/256 pids default runtime limit, and 4,000 millicores/8,192 MiB/512 pids maximum runtime limit. The platform rejects a package or command exceeding a limit before allocation. An operator may lower or raise these values only through typed server policy; changes are recorded at startup and apply to new operations, never silently mutate a running runtime.

## Runtime hardening

- Unprivileged UID; no Docker socket, host PID namespace, privileged mode, or host network.
- No runtime host port; designated internal network and explicit proxy access.
- CPU, memory, pids, filesystem, timeout, restart policy from operator policy.
- Drop capabilities and prohibit privilege escalation where compatible.
- Read-only root plus explicitly scoped temporary writable storage where feasible.
- Never mount host package/artifact directories into runtime.
- Pin/record base-image digest and dependency provenance; generate an SBOM and enforce ADR-011 vulnerability policy.
- Treat package/build logs as untrusted; redact secrets and bound stored/output bytes.

## Package/build safety

Prevent zip slip, zip bomb, symlink, duplicate path, and malicious metadata before extraction. Validation never imports Python, deserializes models, or runs entrypoint. Build-time dependency execution remains trusted-package execution; build worker gets minimum practical privilege and no production data access.

## Backup/restore

Back up metadata and immutable artifact store together on an operator schedule. A valid backup records timestamp, database migration version, artifact checksum inventory, and restore-test result. Restore: provision compatible host/config; restore DB; restore artifacts; apply only documented migration path; start control plane; reconcile; inspect mismatches before route activation.

Images/containers are reproducible/ephemeral, not authoritative backup. Missing retained artifact makes version non-redeployable and alerts operator.

## Reconciliation/incidents

At startup/schedule compare deployment records with Docker labels/state/health. Missing, unexpected, duplicate, unhealthy, or label-mismatched resources produce audit/alert events. Do not auto-delete unknown containers. Delete an orphan only with ForgeML label, retention eligibility, and explicit cleanup operation.

For active failure, remove route only after confirmed unhealthiness, return 503, retain evidence, offer ready rollback. For Docker unavailability, reject new lifecycle operations as retriable unavailable; do not mark healthy version stopped without observation.

## Monitoring/retention

Bound/paginate logs; sample CPU/memory/restarts/health at configured interval; expire/aggregate samples per disk policy. Use low-cardinality metric labels. Surface disk pressure before cleanup threatens active, rollback-capable, or in-progress artifacts.

## Acceptance criteria

- Reference deployment proves isolation and no host-published model port.
- Restore rehearsal reconstructs package metadata/artifacts and produces reconciliation report.
- Control-plane/Docker restart tests create no duplicate managed containers.
- Logs/API/UI disclose no secrets, raw input payloads, host paths, or stack traces.
- Disk policy protects active version, newest ready rollback version, and active operation artifacts.
