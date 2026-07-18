# Repository Labels

The label taxonomy for issues and pull requests. This document is the source of
truth; the labels themselves are created in the GitHub UI to match it.

Four namespaces, each answering one question. A label that answers no question
nobody asks is a label that will be applied inconsistently and then ignored.

---

## `type:` — what kind of work is this?

Exactly one per issue.

| Label | Colour | Meaning |
| --- | --- | --- |
| `type:bug` | `#d73a4a` | Behaviour differs from what is documented |
| `type:feature` | `#0e8a16` | A capability ForgeML does not have |
| `type:docs` | `#0075ca` | Documentation is wrong, missing, or misleading |
| `type:refactor` | `#c5def5` | Internal change, no behaviour change |
| `type:security` | `#b60205` | Security-relevant (public issues only; vulnerabilities go to advisories) |
| `type:debt` | `#fef2c0` | Known shortcut coming due — usually from a `ponytail:` note |

## `module:` — where does it belong?

Mirrors the frozen roadmap. Exactly one; `module:none` if it genuinely spans the
repository.

| Label | Module |
| --- | --- |
| `module:0-foundation` | Config, composition, errors, logging, health |
| `module:1-package` | `.forge` format and validation |
| `module:2-metadata` | PostgreSQL, repositories, operations, audit |
| `module:3-api` | HTTP surface |
| `module:4-analyzer` | Contract analysis and artifact generation |
| `module:5-deployment` | Version lifecycle |
| `module:6-runtime` | Docker adapter |
| `module:7-routing` | Activation, rollback, prediction routing |
| `module:8-monitoring` | Not started |
| `module:9-auth` | Not started |
| `module:10-hardening` | Not started |
| `module:none` | Tooling, CI, governance, repository-wide |

## `status:` — what is it waiting on?

At most one. No label means "open, not yet triaged into a state."

| Label | Colour | Meaning |
| --- | --- | --- |
| `needs:triage` | `#ededed` | Not yet assessed. Applied automatically by issue templates |
| `needs:adr` | `#5319e7` | Blocked: touches a frozen contract or architectural rule |
| `needs:info` | `#d4c5f9` | Waiting on the reporter |
| `blocked` | `#000000` | Blocked by another issue or an unopened module gate |
| `good-first-issue` | `#7057ff` | Self-contained, with a clear definition of done |
| `help-wanted` | `#008672` | Maintainers would welcome a contributor here |

## `resolution:` — why did it close without a merge?

| Label | Meaning |
| --- | --- |
| `resolution:duplicate` | Tracked elsewhere |
| `resolution:wontfix` | Deliberate; usually a documented non-goal |
| `resolution:out-of-scope` | A real idea, outside V1 scope (see the README's non-goals) |
| `resolution:deferred` | Valid, belongs to a later module |

---

## Conventions

- **Every open issue** carries a `type:` and a `module:`.
- **`needs:adr` is a hard block.** Work does not start on it until the ADR is
  accepted — that is the whole point of the label.
- **`type:debt`** items should reference the `ponytail:` comment or engineering
  report they came from, so the shortcut and its ledger entry stay connected.
- **Security vulnerabilities never get a label**, because they never get an
  issue. See [`SECURITY.md`](../SECURITY.md).
- Labels are for filtering, not for narrating status. If a label is never used in
  a query, delete it.
