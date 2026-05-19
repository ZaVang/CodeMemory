# CodeMemory Future Roadmap

> **Purpose:** Long-term roadmap and backlog. Product truth stays in `docs/prd.md`; architecture truth stays in `docs/architecture.md`.

---

## Planning Rules

1. Keep exactly one active sprint in `docs/plan/SPRINT.md`.
2. Keep long-term roadmap and unscheduled backlog here.
3. When a sprint item is accepted, remove it from `SPRINT.md`; follow-up work returns here.
4. Do not store agent logs, audit reports, or one-off execution notes in `docs/plan/`.
5. If a backlog item changes product or architecture direction, update `prd.md` or `architecture.md` before implementation.

---

## Roadmap Priority

1. **Source Artifact Registry** — preserve and index original documents without treating them as atoms.
2. **`source_refs`** — connect atoms and ContextPacks to Source Artifacts.
3. **`expand_source`** — retrieve source excerpt/full content by explicit request.
4. **ContextPack / resolve v2** — make progressive disclosure the default context assembly model.
5. **Migration Compiler v2** — compile Markdown into Source Artifacts, Anchor Atoms, and Derived Atom proposals.
6. **MCP / harness integration** — expose stable `context_pack` and `expand_source` tools.
7. **UI support for source refs and migration review** — show refs, expansion, and review status in the operator UI.
8. **Companion Layer later** — design as a separate Layer Profile after Work Layer contracts are stable.

---

## Completed Roadmap Items

### 2026-05-19 — P1.3 `expand_source`

**Completed in:** `3ebfa50 feat: add explicit source expansion`

**Acceptance signals met:**

- Core can return a source excerpt or full source by artifact id.
- Expansion output includes artifact id, uri/path, hash/status, content, range, truncation, and structured message fields.
- Missing artifacts/files, stale files, and unsupported source kinds return structured status/message results.
- CLI and REST API paths call shared core behavior.

---

### 2026-05-19 — P1.2 `source_refs`

**Completed in:** `9d671b5 feat: add source refs to memory and context packs`

**Acceptance signals met:**

- Atom metadata can carry `source_refs`.
- Reindex preserves `source_refs` into the index model.
- Validation distinguishes broken imports from broken source refs.
- ContextPack renders source refs in JSON, Markdown, and XML-tagged Markdown without expanding full source content.

---

### 2026-05-19 — Source Artifact Registry foundation

**Completed in:** `b93add5 Add source artifact registry docs and checks`

**Acceptance signals met:**

- Source artifact metadata persists under `.codememory/sources/index.json`.
- Artifacts have stable `id`, `kind`, `uri`, `sha256`, `summary`, and `status`.
- Core can add, list, get, and save artifacts without frontend involvement.
- Missing and stale artifacts are detected by tests and `validate`.

---

## P1 Backlog

### P1.4 ContextPack / resolve v2

**Goal:** Make ContextPack the canonical agent handoff object and keep resolve as compatibility rendering.

**Acceptance signals:**

- ContextPack supports `include_sources` and `disclosure_level`.
- Default output includes source anchors/refs, not full source bodies.
- Resolve output is consistent with ContextPack ordering and budget behavior.

### P1.5 Migration Compiler v2

**Goal:** Upgrade Markdown migration from “segment into atoms” to “Source Artifact + Anchor Atom + Derived Atom proposals”.

**Acceptance signals:**

- Compiler registers source artifacts before proposing atoms.
- Review sets include artifact provenance for every proposal.
- Materialization writes only approved memory files.

---

## P2 Backlog

### P2.1 MCP / Harness Tools

**Goal:** Expose Source Artifact and ContextPack capabilities to mainstream agent runtimes.

**Acceptance signals:**

- Tool definitions include `context_pack` and `expand_source`.
- CLI, MCP, REST, and toolkit paths call shared core handlers.
- Tool output is stable enough for OpenAI / Anthropic style function calling.

### P2.2 Operator UI for Sources

**Goal:** Let users inspect source refs and migration review from the frontend.

**Acceptance signals:**

- Memory detail shows source refs.
- ContextPack panel shows disclosure level and available source expansions.
- Migration review can distinguish source artifact, anchor atom, and derived atom proposals.

### P2.3 Documentation and Examples

**Goal:** Keep docs and examples aligned with the Work Layer substrate model.

**Acceptance signals:**

- User guide explains Source Artifact vs Atom vs ContextPack.
- Example datasets include at least one source-backed memory flow.
- Integration guide documents current CLI/API/tool contracts.

---

## P3 Backlog

### P3.1 Companion Layer Profile

**Goal:** Design companion behavior as a separate Layer Profile after Work Layer is stable.

**Acceptance signals:**

- Companion rules do not change Core contracts.
- Memory timing, affect, and forgetting are profile-level policies.
- Historical companion docs remain reference material, not v1 product truth.

### P3.2 Advanced Recall Strategies

**Goal:** Add richer recall policies only after deterministic context assembly is reliable.

**Acceptance signals:**

- Advanced recall never bypasses required imports.
- Any semantic or salience-based recall remains explainable.
- Work Layer defaults remain deterministic.
