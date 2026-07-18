# ForgeML Governance

ForgeML keeps its engineering process in the repository rather than in anyone's
memory. That produced three documentation roots, and a new contributor's first
question is reasonably "which one do I read?"

This document answers that. It owns the **map**; it duplicates none of the
content it points to.

---

## The three roots

| Root | Owns | Answers |
| --- | --- | --- |
| **`ForgeML_Engineering_Kit_Phase0/`** (FEK) | The product and its decisions | *What* are we building, and what did we decide? |
| **`.forgeos/`** (ForgeOS) | The process | *How* does work move from idea to frozen module? |
| **`docs/`** | Contributor-facing guides | How do I actually do this today? |

One sentence each:

- **The FEK is the specification.** Charter, requirements, architecture, module
  designs, external contracts, and the ADR register. It is normative and it is
  where a decision becomes binding.
- **ForgeOS is the operating manual.** Principles, decision process, module
  lifecycle, roles, workflows, templates, and engineering memory. It governs how
  the FEK gets written and how modules get frozen.
- **`docs/` is the practical layer.** Setup, daily loop, release steps, labels.
  It is derived from the other two and never contradicts them.

---

## Authority order

When two documents disagree, the higher entry wins:

```
1. FEK              specification and ADRs
2. ADRs             the decision register within the FEK
3. ForgeOS          process and protocols
4. Frozen modules   a frozen contract outranks a plan to change it
5. Repository       the code, as the record of what is actually true
```

This order is already stated in `PROJECT_STATUS.md` and in
`.forgeos/constitution/05_engineering_standards.md` ("where this document and the
FEK differ, the FEK wins"). It is restated here because the authority order is
useless if you have to already know where it lives.

---

## Known overlaps, and who owns what

Two pairs of documents cover related ground. Both are **deliberate**, and
ownership is defined so neither drifts.

### Engineering standards

| Document | Role |
| --- | --- |
| `FEK/docs/07_ENGINEERING_STANDARDS.md` | **Authoritative.** The binding standard |
| `FEK/docs/08_CODING_GUIDELINES.md` | **Authoritative.** Code-level rules |
| `.forgeos/constitution/05_engineering_standards.md` | **Derived.** Organizes the above into enforceable process rules |
| `CONTRIBUTING.md` | **Derived.** The subset a contributor needs on day one |

A standard is *changed* in the FEK. The other two are updated to follow.

### Roles

Two taxonomies, answering different questions. Neither is redundant:

| Set | Axis | Example |
| --- | --- | --- |
| `.forgeos/roles/` | **Process role** — authority in a workflow | Chief Architect, Technical Reviewer, Release Manager |
| `FEK/.skills/` | **Domain specialisation** — subject-matter scope | Runtime Engineer, Database Engineer, Package Engineer |

A single contributor holds a process role *and* a domain specialisation. Where
the names collide (`chief_architect`, `documentation_engineer`), `.forgeos/roles/`
is authoritative for **authority** and `.skills/` for **scope**.

### Decisions

`.forgeos/decisions/` holds the ADR **template and process**. The ADRs
themselves live in `FEK/docs/10_ARCHITECTURE_DECISIONS.md`, as one register in
one file, so the whole decision history is readable in one pass. Do not start a
second register.

---

## How decisions are made

1. **Something is contested, irreversible, or crosses a boundary.** If it is
   none of those, it is a pull request, not a decision.
2. **Write it up** using `.forgeos/decisions/adr_template.md`: context, decision,
   consequences, alternatives, owner, status, date.
3. **Get approval** from the Chief Architect role.
4. **Append it** to the FEK register with the next number. ADRs are never
   renumbered and never deleted — a superseded ADR is marked superseded and
   points at its replacement.
5. **Then write the code.**

An accepted ADR is normative. Code that contradicts one is a bug in the code, or
a missing ADR.

### When a frozen contract is involved

Stop implementing. Write an investigation report — what is wrong, what it
breaks, the options and their costs — and get approval before touching anything.
[ADR-017](ForgeML_Engineering_Kit_Phase0/docs/10_ARCHITECTURE_DECISIONS.md) is
the worked example: a real defect in frozen Module 4, surfaced rather than
silently patched.

---

## Module lifecycle

```
design → implement → verify → report → freeze
```

Governed by `.forgeos/constitution/04_module_lifecycle.md` and
`.forgeos/workflows/module_development.md`. A module is frozen only on **passing
CI evidence at a named SHA** (ADR-014) — local green is not evidence. Freezes are
recorded in `PROJECT_STATUS.md` with the baseline SHA.

Order is fixed by `FEK/docs/06_IMPLEMENTATION_ROADMAP.md`. A module may not begin
until its entry gate passes.

---

## Document types

| Type | Job | Normative? | Home |
| --- | --- | --- | --- |
| ADR | Records a decision and what it cost | Yes | FEK register |
| Module design | Specifies a module before it is built | Yes | FEK docs |
| Engineering report | What a module delivered, deferred, learned | No | FEK docs |
| Investigation report | Surfaces a problem and its options | No | FEK docs |
| Review | Assesses repository health at a point in time | No | FEK docs |
| Engineering note (`ponytail:`) | Marks a deliberate shortcut and its ceiling | No | Inline in code |

The distinction that matters: **a report is a snapshot, an ADR is binding.** If a
report contains a decision, that decision belongs in an ADR.

---

## Single sources of truth

Each of these facts has exactly one home. Everything else cites it.

| Fact | Source |
| --- | --- |
| Module status, freezes, progress | `PROJECT_STATUS.md` |
| Architectural decisions | `FEK/docs/10_ARCHITECTURE_DECISIONS.md` |
| Module order and gates | `FEK/docs/06_IMPLEMENTATION_ROADMAP.md` |
| Engineering standards | `FEK/docs/07` and `08` |
| External contracts | `FEK/docs/12_EXTERNAL_CONTRACTS.md` |
| Quality gate | `Makefile` (`make verify`) |
| How to contribute | `CONTRIBUTING.md` |
| Security posture | `SECURITY.md` |
| Versioning and release | ADR-021 and `docs/RELEASE.md` |

The README summarises; it is never the source. If the README and
`PROJECT_STATUS.md` disagree about progress, `PROJECT_STATUS.md` is right and the
README is a bug.
