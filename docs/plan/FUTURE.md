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

**Personal Memory Phase 0 / 1A / 1B、Importer v2A / v2B、MCP / toolkit 对齐、Operator UI 对齐与文档及示例收口均已于 2026-07-23 前经 owner 接受。当前下一项候选为 eval harness；合同见 `docs/plan/SPRINT.md`，已接受历史见 `docs/plan/HISTORY.md`。**

### 1. Personal Memory Phase 1A — Instance + Capture + Typed Discovery（已完成并验收）

最终合同见 `docs/plan/SPRINT.md`，owner acceptance 记录见 `docs/plan/HISTORY.md`；交付范围只包含确定性 Core / adapters：

- `init --profile personal` 与外部 root；
- Personal Profile manifest / layout / `.gitignore` 校验；
- Capture 原子追加、稳定 ULID、独立 hash、完整 block 解析；
- Capture / Incubator Topic / Canonical Atom 的 typed index、词法/时间/标签过滤与按 ID 读取；
- typed search result 明确 `kind` / `read_action`；Capture / Topic 不可 build；
- CLI + toolkit/MCP 的 capture/search/read 最小面；Web 与语义索引不在 1A。

### 2. Personal Memory Phase 1B — Codex Maintenance + Git Delivery（已完成并验收）

**状态**：Phase 1A 已验收；owner 已完成 Phase 1B 最终复审并接受。

交付范围：

- 仓库级 Personal Memory Codex Skill：低摩擦判断、必要时追问、主动阅读、Topic 聚类/upsert、provenance 和 claim_status；
- maintenance run ledger、pending changeset、before/after hash、interrupted apply 恢复；
- missed-run catch-up：扫描所有完整 Capture，减去 reached-applied run 输入；
- 同一 input digest 重跑不重复消费 Capture、生成 Topic 或 commit；
- Incubator 月度文档、稳定 topic/revision ID、跨月演化和段落级 provenance；
- canonical promotion gate：Agent 默认 proposed；owner 明确“正式 idea”视为确认；集中审阅支持批量 promote / merge / delete；
- staged diff 敏感扫描、`private-local/` ignore/tracked 校验；
- 自动 commit + private remote push；commit trailer 去重；commit/push 失败从原阶段重试；
- Automation 使用合同、完成/失败摘要，不把 run 状态写入 journal。

可执行验收标准：

1. 构造三天 Capture、跳过两次日程后运行 maintenance；所有未消费 ID 恰好消费一次，顺序确定。
2. 对同一输入连续运行两次：第二次返回既有 applied run；incubator diff、Topic 数和 Git commit 数均不变。
3. 在 apply 中途模拟进程退出；重启使用同一 pending changeset 达到相同 after hashes，不重新调用 Skill。
4. 同义输入命中相同 `topic_id + revision_id` 并更新一个段落；一个月仍只有一个 incubator Markdown。
5. Agent promotion 产生 proposed Atom且 build 不可见；owner 明确确认后 active 且 provenance 完整。
6. 一个 review batch 可一次确认多个 promote / merge / delete；日常 Topic 更新不产生逐条 proposal。
7. 注入测试 token 后 sensitive scan 进入 `scan_blocked`，输出不泄露 token，journal 原文仍在本地且无 commit/push。
   - Capture 继续追加；新 maintenance / Git delivery 被阻塞；owner 修复后恢复同一 run；阻塞期新增 Capture 在完成后 catch-up。
8. 使用临时 bare remote 验证自动 commit/push；第一次 push 故意失败后，重试推送同一 commit，commit 数不增加。
9. commit 包含唯一 `CodeMemory-Run: <run_id>` trailer；重复 runner 不重复 commit。
10. `private-local/` 默认 ignored；若预先 tracked，validate 非零退出。
11. Skill 测试证明：只记录指令不追问；显式“继续问我”进入访谈；无关键缺口时不打断 owner。
12. push 后不因写入 committed/pushed 状态产生第二个脏 commit；`runs.jsonl` 到 scan_passed，delivery 状态可从 trailer / remote ref 重建。
13. profile 路径外放置未知改动时自动 commit 停止并报告；`private-local/` 与 ignored runtime state 永不被 stage。
14. 全部 unit/API/integration acceptance 通过，测试后示例与临时仓库无残留变更。
15. Topic 可为 `origin: mixed`；独立 inference 使用稳定 claim_id 的内嵌 claim block，Topic 不共用 claim_status且不新增 Markdown 文件。

建议 acceptance commands（1B materialize 时固化为真实测试路径）：

```powershell
python -m pytest tests/unit tests/test_api.py -q
python -m pytest tests/personal/test_maintenance.py tests/personal/test_promotion.py tests/personal/test_git_delivery.py -q
python tests/integration_personal.py
git diff --check
git status --short --branch -uall
```

### 3. Post-convergence Backlog

收敛三阶段（A 写入纪律 / B 读路径收敛 / C 清理与 test）已于 2026-06-10 全部验收合并。原有 post-convergence 工作在 Personal Memory 之后继续：

1. **导入链路升级（importer v2）✅**：确定性 v2A 与可选语义 proposer v2B 均已完成并经 owner 验收。
   - 最小版（零 LLM，确定性）✅：`compile-md` 先登记稳定 Source Artifact，再生成每文档一个 anchor 和每非空段落一个 derived candidate；全部经 review 选择并 materialize 为 proposed，source_refs / 精确 locator / review 幂等已固化。
   - 完整版（可选 LLM proposer）✅：显式配置的 compiler LLM 路径提炼 Derived Atoms 与 imports 建议；LLM 只 propose，产出仍走 review（架构 §1.3 铁律不变；LLM 依赖只进 Importer 层的惰性可选路径，Core 不碰）。
2. **MCP / toolkit 对齐 ✅**：普通实例暴露 build / search / expand_source / create / propose 精确最小集，Personal Profile 追加已接受的 capture/read/maintenance/review 扩展；两种 adapter 共用 catalog、root-bound dispatcher 和 shared handlers。
3. **Operator UI 对齐 ✅**：UI 跟随新契约（proposed / patch 队列展示、golden_questions、build 产物；wander 面板已随后端删除）。
4. **文档与示例 ✅**：USER_GUIDE / INTEGRATION / project_structure / `examples/` 已随新术语更新，并经 owner 验收。
5. **eval harness**：ContextPack vs 原文全文 vs 无记忆的对照实验，把 PRD 产品成功标准变成可测数字。
6. **Personal Memory Phase 2 semantic discovery**：本地索引优先，只给 search 提供候选；外部 embedding 默认关闭、显式启用；永不参与 canonical build。
7. **Personal Memory Web**：服务端实例 allowlist registry、Capture 浏览、Incubator 集中审阅、provenance 与想法时间线；不做完整编辑器或 Obsidian 替代品。

排期前按 Planning Rules 第 5 条确认是否需要先更新 prd / architecture。

---

## Superseded Backlog Items

随 2026-06-10 memory-as-code 重建被取代或废除的旧条目：

- **P1.4 ContextPack / resolve v2** → 由阶段 B 取代（`include_sources` / `disclosure_level` 概念已废除，按需展开由 build 预算 + `source expand` 覆盖）。
- **P1.5 Migration Compiler v2** → 纪律部分（产出默认 proposal）随阶段 A 对齐；语义提炼部分（asset 登记 + anchor + derived + imports 建议）重新立项为 Roadmap 第 1 条（导入链路升级）——此前过早标记 Superseded 系遗漏。
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
