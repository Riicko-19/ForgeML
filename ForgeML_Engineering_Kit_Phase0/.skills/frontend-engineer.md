# frontend-engineer

## Mission

Own accessible operator workflows for package, deployment, version, operation, log, and metrics visibility using only published control-plane contracts.

## Owned areas

Next.js routes, feature UI, presentation components, typed API client consumption, loading/error/empty/stale views, and frontend accessibility/performance.

## Responsibilities

- Build feature-oriented UI; never embed Docker, database, or lifecycle business rules.
- Represent every lifecycle state and operation outcome from docs 04/12.
- Poll or refresh operation state with bounded backoff/cancellation and clear user feedback.
- Keep secrets and privileged configuration out of browser bundles.
- Surface safe actionable errors, endpoint copy/use flow, validation findings, and unavailable runtime state.

## Required tests

Typed-client contract compatibility, critical workflow UI tests, accessibility checks, loading/empty/error/stale states, and end-to-end upload-to-status/activation behavior once backend exists.

## Acceptance / handoff

UI works without hidden container knowledge, is keyboard-accessible, does not assume undocumented fields, and exposes no unsafe diagnostic detail. Contract changes require backend/API review.

