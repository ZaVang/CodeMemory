# CodeMemory Current Sprint

> **Active sprint:** P1.2 `source_refs`
> **Goal:** Connect atoms and ContextPacks to Source Artifacts without mixing source provenance into imports.

---

## Sprint Rules

1. This file tracks only the current sprint.
2. Completed and accepted work is removed from this file.
3. Follow-up ideas move to `docs/plan/FUTURE.md`.
4. Product or architecture changes must update `docs/prd.md` or `docs/architecture.md`.
5. Runtime implementation should be TDD-first.

---

## Scope

Build the minimal `source_refs` bridge:

- atom metadata can carry `source_refs`;
- reindex preserves `source_refs` into `MemoryEntry`;
- validation distinguishes missing/broken source refs from missing imports;
- ContextPack includes and renders source refs without expanding source content;
- docs describe current behavior and explicitly defer `expand_source`.

Not in scope:

- full source expansion;
- section/range retrieval;
- frontend source-ref UI;
- Migration Compiler v2 source-aware proposals.

---

## Tasks

### Task 1 — Add `SourceRef` metadata model

- [x] Add a core model for Source Ref metadata.
- [x] Add `source_refs` to `MemoryEntry`.
- [x] Preserve `source_refs` during reindex.
- [x] Add tests for model parsing and index preservation.

**Acceptance:** Atom frontmatter with `source_refs` survives reindex into the index model.

### Task 2 — Validate broken source refs separately from imports

- [x] Add source-ref validation using the Source Artifact registry.
- [x] Missing memory imports remain errors.
- [x] Missing source artifact refs are reported as source-ref warnings.
- [x] Add tests proving the counts and messages are distinct.

**Acceptance:** Broken imports and broken source refs are not conflated.

### Task 3 — Render source refs in ContextPack

- [x] Add `source_refs` to ContextPack nodes.
- [x] Render source refs in JSON.
- [x] Render source refs in Markdown and XML-tagged Markdown.
- [x] Do not expand source artifact bodies.
- [x] Add tests for ContextPack output.

**Acceptance:** Agents can see which Source Artifacts support each memory without receiving full source text.

### Task 4 — Update docs and sprint records

- [x] Update architecture/user/project docs with implemented `source_refs` behavior.
- [x] Update sprint checklist as tasks complete.
- [ ] Append history and pitfalls at closeout after acceptance.

**Acceptance:** Docs describe implemented behavior, not planned behavior.

---

## Sprint Acceptance Criteria

- Atom metadata can carry `source_refs`.
- Validation distinguishes broken imports from broken source refs.
- ContextPack can render source refs without expanding full source content.
- Tests cover reindex preservation, validation, and ContextPack rendering.
