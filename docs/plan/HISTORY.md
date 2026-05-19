# CodeMemory Sprint History

This file records accepted sprint outcomes. Current work belongs in `docs/plan/SPRINT.md`; long-term backlog belongs in `docs/plan/FUTURE.md`.

---

## 2026-05-19 — P1.3 `expand_source`

**Status:** Accepted and archived.

**Commit:** `3ebfa50 feat: add explicit source expansion`

**Delivered:**

- Added `SourceExpansion` as the structured result contract for explicit source expansion.
- Added `expand_source_artifact()` for local Markdown/text/code Source Artifacts.
- Added full-content expansion, character-range excerpts, and `max_chars` truncation.
- Added structured `fresh`, `stale`, `missing`, and `unsupported` statuses.
- Added `codememory source expand` CLI output as machine-readable JSON.
- Added `GET /api/sources/expand` REST endpoint backed by the same core behavior.
- Updated architecture, user guide, integration, project structure, and sprint docs.
- Added unit/API coverage for expansion model, full content, bounded excerpts, missing artifact/file, stale hash detection, unsupported sources, handler JSON, and REST response shape.

**Acceptance evidence:**

- `python -m pytest -q tests/unit tests/test_api.py` → `162 passed`
- CLI smoke for `codememory source expand` → passed
- Markdown local link check → `checked 13 markdown files; no missing local doc links`
- old plan path check → `no stale old plan paths outside pitfalls/reference notes`
- `git diff --check` → passed

**Deferred:**

- semantic section lookup
- PDF/binary parsing beyond unsupported notices
- frontend source expansion UI
- MCP/harness exposure for `expand_source`
- Migration Compiler v2 source-aware proposals

---

## 2026-05-19 — P1.2 `source_refs`

**Status:** Accepted and archived.

**Commit:** `9d671b5 feat: add source refs to memory and context packs`

**Delivered:**

- Added `SourceRef` metadata and attached it to `MemoryEntry`.
- Preserved `source_refs` during reindex from atom frontmatter into the index model.
- Added validation for missing Source Artifact refs as source-ref warnings, separate from missing import errors.
- Rendered source refs in ContextPack JSON, Markdown, and XML-tagged Markdown.
- Kept source expansion out of ContextPack output; `expand_source` remains a later explicit retrieval contract.
- Updated architecture, user guide, project structure, and sprint docs.
- Added unit coverage for model parsing, index preservation, validation distinction, and ContextPack rendering.

**Acceptance evidence:**

- `python -m pytest -q tests/unit tests/test_api.py` → `154 passed`
- Markdown local link check → `checked 13 markdown files; no missing local doc links`
- old plan path check → `no stale old plan paths outside pitfalls`
- `git diff --check` → passed

**Deferred:**

- `expand_source`
- section/range source retrieval
- ContextPack / resolve v2 disclosure options
- Migration Compiler v2 source-aware proposals
- frontend source-ref UI

---

## 2026-05-19 — Source Artifact Registry foundation

**Status:** Accepted and archived.

**Commit:** `b93add5 Add source artifact registry docs and checks`

**Delivered:**

- Added `SourceArtifact`, `SourceRegistry`, and source check models.
- Added `.codememory/sources/index.json` load/save registry primitives.
- Added add/list/get/check source operations.
- Added CLI commands: `codememory source add|list|get|check`.
- Added validation warnings for missing and stale local Source Artifacts.
- Updated architecture, user guide, project structure, and sprint docs.
- Added unit coverage for source serialization, persistence, handler exposure, fresh/stale/missing checks, and validate integration.

**Acceptance evidence:**

- `python -m pytest -q tests/unit tests/test_api.py` → `148 passed`
- `git diff --check` → passed
- Markdown local link check → `checked 11 markdown files; no missing local doc links`
- old plan path check → `no stale old plan paths`
- manual CLI source flow verified add/check/validate behavior

**Deferred:**

- `source_refs`
- `expand_source`
- ContextPack / resolve v2 source disclosure
- Migration Compiler v2 Source Artifact integration
- frontend source-ref UI
