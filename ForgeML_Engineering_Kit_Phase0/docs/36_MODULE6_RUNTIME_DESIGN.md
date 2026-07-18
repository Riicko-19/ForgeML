# Module 6 — Docker Runtime (engineering note)

Owner: Senior Implementation Engineer. Subordinate to docs 02/03/04/06/11 and the
ADR register. Roadmap scope (docs 06 phase 6): *image/container/network/health
adapter*; exit gate: *a disposable Docker test proves labels, limits, isolation,
and cleanup*.

## What this module delivers

- **`DockerRuntimeManager`** (`infrastructure/runtime/docker.py`): the real
  `RuntimeManager`, implemented against Docker. It replaces `FakeRuntimeManager`
  in the live application; nothing above the port changes.
- **Serving harness** (`infrastructure/runtime/serving.py`): the standard-library
  HTTP server (`/health`, `/predict`) that Module 4's generator deliberately
  leaves to the runtime module, plus the Dockerfile serving layer
  (COPY/ENV/HEALTHCHECK/CMD) appended to the frozen generated Dockerfile.
- **Composition wiring** (`core/composition.py`): `DeploymentService` is composed
  onto the Docker adapter and the deployment/admin routers are mounted — the wiring
  Module 5 explicitly deferred to this module.
- **Disposable Docker integration test**
  (`tests/integration/runtime/`): builds a real image, starts a real container,
  drives it to health, predicts through it, reconciles it, and removes it.

## The adapter speaks CLI, behind one seam

The control plane drives Docker through its command-line interface, not an SDK. It
adds no pinned runtime dependency, and the daemon is reached the same way either
approach would reach it. Every invocation goes through the `DockerCli` seam —
`SubprocessDockerCli` in production, a scripted fake in tests — which is the only
code in the module that touches `subprocess`. Everything else is pure argument
building and output parsing, so build/start/stop/inspect/reconcile are unit-tested
without Docker and proven end to end by the integration test.

`docker` is imported nowhere: the architecture test that forbids the Docker SDK in
the domain, application, and API layers stays satisfied, and the runtime adapter
lives in `infrastructure/runtime/`, outside the package paths that forbid
`subprocess`.

## Runtime behaviour

`build` assembles a context directory (the package `src/` extracted through the
artifact store, the generated files, the serving harness, the augmented
Dockerfile), builds a deterministically tagged image (`forgeml/<identity[:12]>`),
and labels it. `start` ensures the isolated network, clears any stale container of
the same deterministic name, runs the container hardened, and polls `inspect`
until the Docker health check reports healthy — failing terminally if the
container exits or never becomes ready. `inspect`, `reconcile`, and `stop` parse
Docker state into the provider-neutral records the port defines. Failure
classification is explicit: an unreachable daemon is `RuntimeUnavailable`
(retriable, 503); a genuine build/start failure is `RuntimeExecutionError`
(terminal for the attempt), carrying a safe classified code and never raw Docker
output (docs 07).

## Security (ADR-001)

Containers run as a non-root user, with a read-only root filesystem, all
capabilities dropped, `no-new-privileges`, CPU/memory/pid limits, and a scoped
`tmpfs` for `/tmp`. They join an internal, egress-free network (ADR-011) and
publish no host ports (ADR-005); the Docker socket, host network, and host mounts
are never granted. The integration test asserts each of these against a live
`docker inspect`. Labels (`forgeml.managed`, `forgeml.version_id`,
`forgeml.image_identity`) let reconciliation enumerate exactly what the platform
owns (ADR-004).

## Docker assumptions

- A reachable Docker daemon on the control-plane host; the control plane starts
  without it (packages still work) and deployment operations return 503 until it
  is reachable.
- The generated base image (`python:3.11-slim`, ADR-008) is pullable at build time;
  runtime egress is disabled.
- The runtime network is created on demand as `--internal`; making its name,
  timeouts, resource defaults, and run-user operator-configurable (`RuntimeSettings`)
  is a small additive follow-up, not a contract change.

## Prerequisite correction (ADR-017)

Module 6 is the first code to build and import Module 4's generated adapter. That
surfaced a latent defect — schemas embedded as JSON (`false`/`true`/`null`) into
Python source, a `NameError` on import — which was fixed under ADR-017 after an
investigation report. A generated runtime artifact must be exercised by an
execution test, not only static checks; the integration test now provides that.

## Deferred to later modules

- **Prediction routing across versions** — the platform route, activation, and
  rollback are Module 7. A single container serving its own endpoint is this
  module; routing *to* it is not.
- **Logs and usage sampling** — Module 8. The port leaves room for them; the
  adapter reports only structured status today.
- **Background worker daemon** — execution is inline, exactly as Module 5 left it;
  the durable operation makes moving it behind a worker a later change with no
  HTTP-contract impact.
