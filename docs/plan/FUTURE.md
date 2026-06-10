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

**收敛三阶段（A 写入纪律 / B 读路径收敛 / C 清理与 test）已于 2026-06-10 全部验收合并——代码与 11 概念模型对齐完成。** 下一批工作从 Post-convergence Backlog 中提升：

1. **MCP / toolkit 对齐**：暴露 build / search / expand_source / create / propose 最小工具集，全部走共享 handler。
2. **Operator UI 对齐**：UI 跟随新契约（proposed / patch 队列展示、golden_questions、build 产物；wander 面板已随后端删除）。
3. **文档与示例**：USER_GUIDE / INTEGRATION / project_structure / `examples/` 随新术语更新。
4. **eval harness**：ContextPack vs 原文全文 vs 无记忆的对照实验，把 PRD 产品成功标准变成可测数字。

排期前按 Planning Rules 第 5 条确认是否需要先更新 prd / architecture。

---

## Superseded Backlog Items

随 2026-06-10 memory-as-code 重建被取代或废除的旧条目：

- **P1.4 ContextPack / resolve v2** → 由阶段 B 取代（`include_sources` / `disclosure_level` 概念已废除，按需展开由 build 预算 + `source expand` 覆盖）。
- **P1.5 Migration Compiler v2** → importer "产出默认 proposal" 的纪律在阶段 A 后自然对齐，不再单列。
- **P3.1 Companion Layer Profile** → 已废除（见 `docs/prd.md` 非目标；历史探索在 `docs/reference/`）。
- **P3.2 Advanced Recall Strategies** → 词法排序并入阶段 B；语义召回仍为非目标（`docs/prd.md` 第 8 章）。

---

## Completed Roadmap Items

### 2026-06-10 — 阶段 C：清理与 test

**Completed in:** `3e11331`（merge of `sprint/phase-c-cleanup-and-test`）

**Acceptance signals met:**

- `grep intensity src/` 仅剩 2 处 deprecated 别名（skeletonize `--min-intensity` 与 `@intensity`）；
- `codememory test <entry>` 导出题集 + 装配上下文 JSON，空题集退出码 0 + notice；
- `propose → proposals → merge` 全链路：patch 经 update 应用（version++、change_log），队列清空；
- focus / overview / wander 与 `compute_retrieval_probability` 不复存在；models 无 4 个 heat 字段；validate 无 DECAY-WARN；
- 单测 + API 197 passed、集成 21/21（断言迁移后零回归）。

详细记录见 `docs/plan/HISTORY.md`。

---

### 2026-06-10 — 阶段 B：读路径收敛

**Completed in:** `b778abd`（merge of `sprint/phase-b-read-path`）

**Acceptance signals met:**

- 三命令一致性：`build --format plain-markdown` ≡ `resolve`、`build` ≡ `context-pack`（剔除时间戳后逐字符相等，金测试 + CLI diff 双重固化）；
- 裁剪金测试：预算不足时 target 全文保留、低价值 required 叶子降级 summary、related 预算外 skipped；
- 排序金测试：多 token 多字段命中排在 body 弱命中之前，单 token 行为兼容；
- 装配不再写 maturity / stability（惰性元数据契约金测试）；
- 单测 184 passed（断言迁移后零回归）、集成 24/24。

详细记录见 `docs/plan/HISTORY.md`。

---

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
