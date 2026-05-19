# CodeMemory Current Sprint

> **Active sprint:** Source Artifact Registry foundation
> **Goal:** Implement the backend/core foundation for Source Artifacts without introducing frontend dependency.

---

## Sprint Rules

1. This file tracks only the current sprint.
2. Completed and accepted work is removed from this file.
3. Follow-up ideas move to `docs/plan/FUTURE.md`.
4. Product or architecture changes must update `docs/prd.md` or `docs/architecture.md`.
5. Runtime implementation should be TDD-first.

---

## Scope

Build the foundation for Source Artifact Registry:

- source artifact model and storage contract;
- registry load/save/list/get/add primitives;
- missing/stale artifact detection;
- minimal CLI/API exposure only after core primitives are stable;
- docs update after tests pass.

Not in scope:

- frontend source-ref UI;
- full ContextPack v2 rollout;
- full Migration Compiler v2;
- Companion Layer behavior.

---

## Tasks

### Task 1 — Define Source Artifact model and storage contract

- [x] Add core model for Source Artifact metadata.
- [x] Define supported initial fields: `id`, `kind`, `uri`, `sha256`, `summary`, `status`.
- [x] Define storage location as `.codememory/sources/index.json`.
- [x] Add tests for model serialization and default values.

**Acceptance:** A source artifact can be represented as stable JSON without touching frontend code.

### Task 2 — Add registry primitives

- [x] Add load/save helpers for `.codememory/sources/index.json`.
- [x] Add list/get/add primitives.
- [x] Ensure parent directories are created on save.
- [x] Ensure missing registry loads as an empty registry.
- [x] Add tests for add/list/get/save/reload.

**Acceptance:** Artifacts persist and reload from `.codememory/sources/index.json`.

### Task 3 — Detect missing and stale source artifacts

- [x] Add hash computation for local file artifacts.
- [x] Mark missing local files as detectable.
- [x] Mark changed local files as stale when hash differs.
- [x] Add tests for fresh, missing, and stale artifacts.

**Acceptance:** Tests prove stale/missing artifacts are detectable.

### Task 4 — Expose minimal core-facing interface

- [x] Add handler functions only after core primitives pass tests.
- [x] Add CLI commands only if the handler contract is stable.
- [x] Defer REST/API exposure unless CLI/core tests make the contract clear.

**Acceptance:** Any exposed interface calls shared core primitives and does not duplicate registry logic.

### Task 5 — Update docs after implementation

- [x] Update `docs/architecture.md` with implemented Source Artifact behavior.
- [x] Update `docs/USER_GUIDE.md` with current commands if CLI exposure is added.
- [x] Update `docs/project_structure.md` with new source registry files.
- [ ] Move completed sprint items out of this file after user acceptance.

**Acceptance:** Docs describe implemented behavior, not speculative behavior.

---

## Sprint Acceptance Criteria

- Artifact metadata persists under `.codememory/sources/index.json`.
- Artifacts have stable `id`, `kind`, `uri`, `sha256`, `summary`, and `status`.
- Stale/missing artifacts are detectable.
- No frontend dependency is introduced.
- Tests cover add/list/get/stale detection.
