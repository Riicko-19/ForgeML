# ForgeOS — ForgeML Engineering Operating System

ForgeOS is the operating manual for the engineering organization behind ForgeML.
It exists so that any contributor — human or AI — can clone the repository, read
this directory, and begin contributing correctly without prior conversation
history.

The repository is the source of truth. Conversations are temporary. Everything
required to engineer ForgeML correctly is written down here or in the documents
this directory points to.

---

## Mission

Make ForgeML self-describing. The engineering process must not depend on any
running conversation with an AI assistant or on any single person's memory. A new
contributor should be able to answer, from the repository alone:

- how ForgeML is engineered
- how work flows from idea to frozen module
- how architecture is reviewed and recorded
- how decisions are made and preserved
- how engineering quality is maintained
- how releases are performed

---

## Philosophy

**Repository first.** Knowledge lives in version control, not in chat. If a fact
matters, it is committed.

**AI-agnostic.** ForgeOS defines *engineering roles*, never vendors. Any AI system
(or person) adopts a role — Chief Architect, Implementation Engineer, Technical
Reviewer, Release Manager, Security Reviewer, Documentation Engineer — and works to
its charter. Nothing here assumes a specific model or product.

**Long-term stability.** ForgeOS documents engineering *principles*, not the
implementation of any one module. Implementation detail belongs to the module's own
documents and to the code.

**Minimalism.** Every document has one clear responsibility. ForgeOS references
existing authority rather than restating it. No document duplicates another.

**Scalability.** The structure supports Modules 1–100, multiple contributors,
multiple AI systems, CI, CD, ADRs, research, and release management without
structural redesign.

---

## Directory structure

```
.forgeos/
  README.md              This file — the entry point.
  constitution/          Immutable engineering principles. How we engineer.
  engineering_memory/    Long-term project knowledge. What happened and why.
  roles/                 Engineering job descriptions, vendor-neutral.
  workflows/             The engineering process, step by step.
  templates/             Reusable engineering artifacts.
  decisions/             Architecture Decision Record system.
```

| Directory | Answers | Read it when |
| --- | --- | --- |
| `constitution/` | "How do we engineer software inside ForgeML?" | Onboarding; before proposing any process change. |
| `engineering_memory/` | "What has been built, and why did it matter?" | Getting oriented; before touching a frozen module. |
| `roles/` | "What is my responsibility on this change?" | Before starting work in any capacity. |
| `workflows/` | "What are the steps and the gates?" | Developing a module, reviewing, freezing, releasing. |
| `templates/` | "What artifact do I produce, and in what shape?" | Writing a plan, review, handoff, ADR, or PR. |
| `decisions/` | "What has been decided and cannot be silently changed?" | Before changing a contract or architectural boundary. |

---

## How to use ForgeOS

### If you are a new human contributor

1. Read this README.
2. Read `constitution/` in order. It is short and it is binding.
3. Read `engineering_memory/project_memory.md` and `module_history.md` to learn
   what exists.
4. Find your `roles/` document for the work you are about to do.
5. Follow the matching `workflows/` document. Produce artifacts from `templates/`.

### If you are an AI system

You are not a vendor here; you are a role. Determine which role the task assigns
you (the requester will name it, or the workflow implies it), read that
`roles/` document, and operate strictly within its authority and its "must never
do" list. Then follow the relevant workflow. Treat the constitution and the ADR
register as binding constraints, not suggestions. When a decision would change a
frozen contract, stop and follow `decisions/` — do not proceed on assumption.

### If you are reviewing or releasing

Go straight to the relevant workflow (`implementation_review.md`,
`architecture_review.md`, `freeze_process.md`, or `release_process.md`). Each names
its inputs, its decision gates, and its exit criteria.

---

## Relationship with the repository

ForgeOS is the **governance and process layer**. It does not replace the detailed
engineering documents that already exist — it organizes the process around them and
points to them as authority.

The **detailed architectural authority** is the ForgeML Engineering Kit (FEK) in
[`ForgeML_Engineering_Kit_Phase0/docs/`](../ForgeML_Engineering_Kit_Phase0/docs/):
the charter, requirements, system/high/low-level design, repository architecture,
roadmap, standards, coding guidelines, operations/security, external contracts, the
ADR register, and each module's design, implementation, review, decisions, and
handoff documents.

The **current progress** is [`PROJECT_STATUS.md`](../PROJECT_STATUS.md) at the
repository root.

The relationship is deliberate and one-directional:

```
ForgeOS (this directory)  ──references──▶  FEK docs, ADR register, PROJECT_STATUS, code
   governance & process                       detailed architecture & current state
```

ForgeOS tells you *how the organization works*. The FEK tells you *how the system
is designed*. When they appear to conflict, the authority order in
[`constitution/01_governance.md`](constitution/01_governance.md) resolves it.

ForgeOS is documentation architecture only. It introduces no code, no tooling, no
automation, and no runtime service.
