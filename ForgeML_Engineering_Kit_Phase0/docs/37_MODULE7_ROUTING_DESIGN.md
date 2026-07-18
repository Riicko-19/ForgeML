# Module 7 — Platform Routing & Version Activation (engineering note)

Owner: Senior Implementation Engineer. Subordinate to docs 02/03/04/12 and the
ADR register (ADR-005 one active version and platform route; ADR-010 dynamic
routing). Roadmap scope (docs 06 phase 7): *stable route, activation/rollback,
retention*; exit gate: *replacement/rollback tests*.

## What this module delivers

- **Activation** (`application/deployment/services.py`): `activate_version`, a
  durable operation that makes one READY version the deployment's ACTIVE route
  target. Rollback is the same command aimed at an earlier version.
- **Transition rules** (`domain/deployment/rules.py`): `mark_active`
  (READY→ACTIVE) and `mark_deactivated` (ACTIVE→READY), the edges Module 5 froze
  but never drove.
- **RouteManager** (`application/routing/services.py`): resolves a deployment's
  active version and proxies a prediction to its runtime.
- **PredictionGateway** (`domain/routing/ports.py`) and its HTTP adapter
  (`infrastructure/runtime/http_gateway.py`): the provider-neutral forwarding
  boundary and its standard-library implementation.
- **Prediction route** (`api/v1/predictions.py`): `POST
  /v1/deployments/{name}/predict`, and the activation route `POST
  .../versions/{version_id}/activate`.

## Activation is atomic and health-gated

A version becomes ACTIVE only after its runtime is confirmed present, running,
and healthy. The health recheck happens *outside* any transaction (docs 04: no
database transaction spans runtime work). The route change itself is one
transaction under the deployment lock (`lock_deployment`, SELECT FOR UPDATE): the
previous active version steps down to READY and the candidate takes the route, or
neither does. If the candidate is unhealthy or the runtime is unreachable, the
operation fails and the previous ACTIVE version is untouched — the invariant docs
04 requires. Re-activating the current active version is an idempotent success.

There is a narrow, deliberate TOCTOU window between the health recheck and the
locked swap: a runtime can fail in that interval. That is inherent to a
metadata/observed split (ADR-004) and is healed by reconciliation and by the
per-request health gate on the prediction path; it is not closed by holding a
lock across runtime work, which docs 04 forbids.

## Rollback

Rollback is not a separate mechanism: activating a prior READY version *is* the
rollback. The previous active version is left READY (runnable), not stopped, so a
roll-forward or roll-back is always one activation away. Stopping the active
version removes the route first (clears `active_version_id` under the lock) before
the container is stopped, so a prediction never resolves to a version about to
disappear.

## Prediction flow

```
client -> POST /v1/deployments/{name}/predict
       -> RouteManager.predict
       -> DeploymentService.resolve_active_target(name)   (metadata: active version + endpoint + schemas)
       -> RuntimeManager.inspect(container)               (health gate)
       -> PredictionGateway.predict(endpoint, payload)    (HTTP forward, internal network)
       -> validate output against the model schema
       -> return the model output
```

The client speaks only to ForgeML and never sees a container, image, or endpoint
(docs 12). Errors map to the platform envelope and leak no runtime detail:

| Condition | Result |
| --- | --- |
| Input fails the model input schema | 422 `prediction_input_invalid` |
| No deployment, no active version, or unhealthy runtime | 503 `deployment_unavailable` |
| Runtime unreachable | 503 `deployment_unavailable` |
| Runtime errors, times out, or returns an invalid output | 502 `prediction_runtime_failed` |

## Provider independence

RouteManager depends on the deployment service (metadata), the `RuntimeManager`
port (health), and the `PredictionGateway` port (forwarding). It never imports
Docker or HTTP. The frozen `RuntimeManager` contract is unchanged: forwarding a
prediction is a distinct concern with its own consumer-owned port, not a new
lifecycle primitive. The HTTP gateway uses the standard library rather than a new
pinned dependency, consistent with the runtime adapter's CLI choice.

## Deferred to later modules

- **Traffic splitting, canary, blue/green, A/B** — out of scope by charter; a
  deployment has exactly one active version (ADR-005). Weighted routing needs a
  future ADR.
- **Prediction logs and latency metrics** — Module 8 (monitoring). The route
  manager reports only pass/fail today.
- **Retention/garbage collection of stopped versions** — the roadmap groups
  retention with this phase, but it is a metadata sweep with no routing impact;
  the columns exist and the sweeper remains a later addition (ADR-012).

## Ponytails

- **Per-request health inspect.** `RouteManager.predict` inspects the runtime on
  every prediction to honour docs 12's "no active healthy runtime → 503". A
  cached readiness gate (Module 8) would remove the per-prediction inspect cost;
  it is not built here to avoid introducing monitoring state in the routing
  module.
- **Runtime endpoint reachability** is a Docker-network topology concern
  (ADR-010): the control plane must share the internal network with the runtime
  to resolve `http://forgeml-<version>:8000`. The HTTP gateway's forwarding
  logic is proven against a local server; the production topology is an
  operational prerequisite, not adapter logic.
