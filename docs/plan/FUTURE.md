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

## Roadmap Priority — 收敛三阶段

依据 `docs/architecture.md` 第 6 章的收敛路径执行，每阶段一个 sprint、独立可合并、独立验收：

1. **阶段 B 读路径收敛**：`build` 命令落地（resolve / context-pack 变薄别名）+ 两遍式 trim + search 词法排序。
2. **阶段 C 清理与 test**：intensity 全链路移除 + 删 focus/overview/wander + models 瘦身 + test 契约落地 + 修改类 proposal patch 队列。

（阶段 A 写入纪律已于 2026-06-10 验收合并，见 Completed Roadmap Items。）

验收信号见 `docs/architecture.md` 第 6 章；概念依据见 `docs/prd.md` 第 4 章。

---

## Post-convergence Backlog

收敛三阶段完成后再排期：

- **MCP / toolkit 对齐**：暴露 build / search / expand_source / create / propose 最小工具集，全部走共享 handler（原 P2.1 的新表述）。
- **Operator UI 对齐**：UI 跟随新契约展示 proposed 队列、golden_questions 与 build 产物（原 P2.2）。
- **文档与示例**：USER_GUIDE / INTEGRATION / project_structure / `examples/` 随新术语更新；examples 增加 asset 背书的记忆流（原 P2.3）。
- **eval harness**：ContextPack vs 原文全文 vs 无记忆的对照实验，把 PRD 产品成功标准变成可测数字。

---

## Superseded Backlog Items

随 2026-06-10 memory-as-code 重建被取代或废除的旧条目：

- **P1.4 ContextPack / resolve v2** → 由阶段 B 取代（`include_sources` / `disclosure_level` 概念已废除，按需展开由 build 预算 + `source expand` 覆盖）。
- **P1.5 Migration Compiler v2** → importer "产出默认 proposal" 的纪律在阶段 A 后自然对齐，不再单列。
- **P3.1 Companion Layer Profile** → 已废除（见 `docs/prd.md` 非目标；历史探索在 `docs/reference/`）。
- **P3.2 Advanced Recall Strategies** → 词法排序并入阶段 B；语义召回仍为非目标（`docs/prd.md` 第 8 章）。

---

## Completed Roadmap Items

### 2026-06-10 — 阶段 A：写入纪律

**Completed in:** `ae30ee8`（merge of `sprint/phase-a-write-discipline`）

**Acceptance signals met:**

- `create --propose` 产出的 atom 默认 search 不可见、build 不装配（有 notice）；
- `merge` 后可见可装配，`reject` 后归档，均留审计日志；
- validate 报 proposed 积压与"active 引用非可装配节点"警告；
- `create --intensity 8` 不再自动 protected（解耦完成）；
- `update --source-ref` 绑定 asset，经 reindex 进入 index 并被 context-pack 渲染；
- 单测 171 passed（零回归）、集成 24/24、合同冒烟全过。

详细记录见 `docs/plan/HISTORY.md`。

---

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
