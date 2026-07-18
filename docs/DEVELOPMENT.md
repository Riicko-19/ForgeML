# Development Workflow

How work actually moves through ForgeML, from an idea to a frozen module.
[`CONTRIBUTING.md`](../CONTRIBUTING.md) covers setup and pull-request mechanics;
this document covers the process those mechanics serve.

---

## The shape of the work

ForgeML is built **module by module**, not feature by feature. Each module has an
entry gate, a scope, and an exit gate, all defined in
[`06_IMPLEMENTATION_ROADMAP.md`](../ForgeML_Engineering_Kit_Phase0/docs/06_IMPLEMENTATION_ROADMAP.md).
A module may not begin until its entry gate passes, and it is not finished when
the code works — it is finished when it is **frozen**.

```
design → implement → verify → report → freeze
```

The reason for this is narrow and practical: later modules depend on earlier
contracts. Module 5 froze `RuntimeManager` and drove it against a fake; Module 6
implemented it against Docker and nothing above the port changed. That only works
if the contract was actually settled before the dependent module started.

---

## Where a change belongs

| Change | Path |
| --- | --- |
| Bug fix inside an implemented module | Pull request, no ceremony |
| New behaviour in the current module | Pull request against the module's design doc |
| Behaviour in a *future* module | Wait. Its entry gate has not opened |
| Anything touching a frozen contract | **Stop.** Investigation report → ADR → approval → change |
| A new architectural rule | ADR first |

### Frozen contracts

Frozen means: the `.forge` format, validation finding codes, port protocols, the
HTTP contract, and the database schema of any frozen module. Changing one is not
forbidden — ADR-017 changed a frozen generator to fix a real defect — but it
follows a defined path:

1. Stop implementing.
2. Write an investigation report: what is wrong, what it breaks, what the options
   are, what each costs.
3. Get approval.
4. Record the decision as an ADR.
5. Then change the code.

The failure this prevents is a frozen surface drifting silently, which is how a
dependent module's assumptions quietly stop being true.

---

## Daily loop

```bash
make db                # once per session
# ... edit ...
make lint              # format and fix
make verify            # the gate — must be green before pushing
```

`make verify` is the same command CI runs. There is no second list of checks.

**Watch for silent skips.** Docker-dependent integration tests skip when the
daemon is unreachable, and a skip looks like a pass in the summary. If you
touched `infrastructure/runtime`, confirm Docker is running.

---

## Module lifecycle

### 1. Design

A design document in `ForgeML_Engineering_Kit_Phase0/docs/`, numbered in
sequence. It states scope, what is explicitly out of scope, the ports involved,
and the exit gate. Out-of-scope is the important half — it is what keeps a module
from absorbing the next one.

### 2. Implement

Against the design. If implementation reveals the design was wrong, amend the
design and say so; do not let the code and the document diverge silently.

### 3. Verify

`make verify` green, plus the module's own exit gate. Coverage floor is 95%
branch; the project has run at 97%.

### 4. Report

An engineering report recording what was delivered, what was deferred and why,
what was learned, and readiness for the next module. This is where deferred work
gets its owner — deferral without a record is just forgetting.

### 5. Freeze

Per [ADR-014](../ForgeML_Engineering_Kit_Phase0/docs/10_ARCHITECTURE_DECISIONS.md):
a module is frozen when GitHub Actions passes on a named SHA. Local green is not
evidence. The freeze is recorded in
[`PROJECT_STATUS.md`](../PROJECT_STATUS.md) with the baseline SHA.

---

## Artifact types

Four kinds of document, with distinct jobs. Using the wrong one is how a
repository ends up with decisions buried in status reports.

| Artifact | Answers | Lives in |
| --- | --- | --- |
| **ADR** | "What did we decide, and why, and what did we give up?" | `10_ARCHITECTURE_DECISIONS.md` |
| **Engineering Report** | "What did this module deliver, defer, and learn?" | `ForgeML_Engineering_Kit_Phase0/docs/` |
| **Investigation Report** | "Something is wrong. What are the options?" | `ForgeML_Engineering_Kit_Phase0/docs/` |
| **Engineering note** (`ponytail:`) | "This is a deliberate shortcut, and here is its ceiling" | Inline, in code |

An ADR is normative and permanent. A report is a snapshot. If a report contains a
decision, that decision belongs in an ADR.

---

## Testing strategy

| Layer | Answers |
| --- | --- |
| Unit | Is this logic right? |
| Contract | Do the real adapter and the fake behave identically? |
| Integration | Does it work against real PostgreSQL, real Docker, real HTTP? |
| Architecture | Are the boundaries still where we said? |
| Smoke | Does the installed wheel actually run? |

The contract layer is the one people skip and shouldn't. Every port is exercised
against both its real adapter and its in-memory fake by the *same* suite. A fake
tested separately from its real counterpart will drift, and every test built on
that fake becomes quietly meaningless.

---

## Definition of done

- [ ] `make verify` green
- [ ] Tested at the right layer
- [ ] No frozen contract changed without an ADR
- [ ] Architecture tests still pass unmodified (if you changed them, you changed the architecture)
- [ ] Docstrings explain why; shortcuts carry `ponytail:` notes
- [ ] `PROJECT_STATUS.md` updated if module status changed
