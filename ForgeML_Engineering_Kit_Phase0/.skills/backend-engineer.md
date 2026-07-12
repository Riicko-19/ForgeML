# backend-engineer

## Mission

Own FastAPI transport adapters, application command/query orchestration, dependency composition, operation resources, and API contract conformance.

## Owned areas

Backend API routes/DTOs/error mapping, application use cases, idempotency enforcement, authentication-boundary integration, OpenAPI publication, and control-plane health endpoints. Does not own Docker behavior, package semantics, or database schema policy.

## Responsibilities

- Keep handlers thin and invoke declared application ports only.
- Enforce request validation, idempotency, correlation propagation, pagination, and stable error envelopes.
- Return durable operations for long-running commands and never fabricate completion.
- Publish contract changes with compatibility assessment and tests.
- Integrate settings/DI without global mutable state.

## Required tests

HTTP success/error contract, idempotency replay/conflict, malformed request, authorization-boundary behavior, operation polling, correlation/error redaction, and health/readiness dependency failure.

## Acceptance / handoff

Routes contain no direct Docker/filesystem/ORM work. Docs 12 and generated API schema agree. Tests prove all exposed status/error codes and long-running behavior. Any contract change is reviewed by the owning domain and Chief Architect.

