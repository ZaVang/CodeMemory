# CodeMemory Sprint History

This file records accepted sprint outcomes. Current work belongs in `docs/plan/SPRINT.md`; long-term backlog belongs in `docs/plan/FUTURE.md`.

---

## 2026-06-10 — memory-as-code 文档重建（非 sprint 流程）

**Status:** Accepted（owner 逐节批准 + 独立验收）。

**Commits:** `66cad6d`…`f09f4e7`（prd / agent-memory-guide / CLAUDE.md / architecture / FUTURE 重建）

**Delivered:**

- `docs/prd.md` 按唯一公理重建：记忆按代码方式组织——原子化、显式依赖、按需装配；三组 11 概念，含实现状态标注与旧概念对照表（附录 A）。
- `docs/agent-memory-guide.md` 重写为记忆库贡献规范（CONTRIBUTING），示例域从投资换为工作。
- `.claude/CLAUDE.md` 同步新术语，修复陈旧文件清单。
- `docs/architecture.md` 重建为契约级参考：三层结构、概念→模块映射、字段表、proposal 状态机、build/search/check/test 管线契约、收敛三阶段（A/B/C）。
- `docs/plan/FUTURE.md`：roadmap 替换为收敛三阶段，旧条目标注 Superseded。

**设计记录：** `docs/superpowers/specs/2026-06-10-*.md`（两份 spec）、`docs/superpowers/plans/2026-06-10-memory-as-code-docs-rebuild.md`（执行计划）。

**Acceptance evidence:** 三份文档与计划内嵌文本逐字节一致；计划内全部 grep 验证通过；`pytest tests/unit` 153 passed（零代码变更）。

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
