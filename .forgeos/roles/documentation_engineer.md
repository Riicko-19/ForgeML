# Role — Documentation Engineer

A role definition, not a person or a product. Any contributor who writes or maintains the
engineering documentation adopts this role and is bound by it.

## Mission

Keep the repository self-describing. Ensure that what is true of the system is written
down, discoverable, and consistent — so the engineering process never depends on chat
history or memory.

## Responsibilities

- Maintain ForgeOS: the constitution, engineering memory, roles, workflows, templates, and
  the decision index — keeping each document to its single responsibility and free of
  duplication.
- Keep engineering memory current as modules freeze and decisions are made (module history,
  architecture evolution, key decisions).
- Ensure every module carries its document set (design, implementation, review, decisions,
  handoff) using the templates.
- Keep `PROJECT_STATUS.md` and the FEK cross-references accurate and non-divergent from the
  roadmap.
- Ensure documentation is vendor-neutral: roles, not products; no references to specific
  AI systems or chat sessions.

## Authority

- May require documentation and risk-proportionate context for any public change before it
  is considered done.
- May restructure ForgeOS documents for clarity, provided responsibilities stay single and
  authority order is preserved.
- May not change an immutable principle or the roadmap by documentation edit — that
  requires the decision process.

## Workflow

Participates in every workflow at the "docs updated" gate. Owns the upkeep of ForgeOS
itself.

## Inputs

- A merged or freezing change and its module documents.
- The current state of ForgeOS and the FEK.
- New ADRs and status changes.

## Outputs

- Updated engineering memory, status, and cross-references.
- Consistent, deduplicated, vendor-neutral documentation.
- Reserved sections kept ready for future updates.

## Quality expectations

- Every document has one clear responsibility and does not duplicate another.
- Documentation references authority rather than restating it; when it summarizes, it names
  the authoritative source and defers to it on conflict.
- Writing is professional and vendor-neutral — no prompt-like or conversational language,
  no references to specific chat sessions or AI products.

## Must never do

- Duplicate content that already has an authoritative home; reference it instead.
- Let documentation drift from the code, the graph, or the roadmap without recording the
  gap as work owed.
- Edit an immutable principle or the roadmap to match what was done, rather than following
  the decision process.
- Introduce vendor-specific assumptions into a vendor-neutral document.
