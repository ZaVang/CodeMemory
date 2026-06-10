# CodeMemory Sprint History

This file records accepted sprint outcomes. Current work belongs in `docs/plan/SPRINT.md`; long-term backlog belongs in `docs/plan/FUTURE.md`.

---

## 2026-06-10 — 阶段 C：清理与 test

**Status:** Accepted and merged.

**Merge commit:** `3e11331`（branch `sprint/phase-c-cleanup-and-test`，6 commits：`0e7ffb4` / `8a20378` / `5f375f0` / `bdcb4a0` / `65f2f99` 等）

**Delivered:**

- test 契约（`test_contract.py`）：`codememory test <entry>` 导出 `{format_version, entry, context, questions}` JSON，空题集出 notice；`test report` 校验 `{q, answer, pass}` 后写审计日志；validate 新增 `[GOLDEN-WARN]`；Core 零 LLM 依赖；
- 修改类 proposal patch 队列（`proposals.py`）：`propose` 入队字段级 patch（目标不被触碰）、`proposals` 列队、merge/reject 统一分发（先 patch 队列后新增类），merge 经 update 应用（version++ / change_log）；validate 新增 `[PROPOSAL-WARN]`（积压 / 目标缺失）；评审结论：不复用 compiler review（粒度不匹配），独立小模块；
- 删除拟人范式残留：focus / overview / wander 全链路（handlers / cli / tools / mcp / backend 路由）、`compute_retrieval_probability`、validate decay check；
- intensity / stability 全链路移除：models 4 字段、create / index / orphans / cli / tools / mcp / importer / compiler / transient / backend 请求模型与序列化清扫；skeletonize 评分改名 weight（`--min-intensity` 与 `@intensity` 为仅存的两处 deprecated 别名）；MCP propose_memory 现代化为 `create --propose` 委托；
- shim 处置：`context_pack.py` 删除，importer 全部指向 `build`；
- 附带修复：backend `/api/resolve` 从"regex 解析渲染文本"改为直接消费结构化管线（阶段 B 潜在债，test_api 捕获）；
- 文档同步：CLAUDE.md / guide / prd / architecture（A/B/C 全部标记完成，过时现状注记刷新）/ pitfalls（decay 条目移除）/ rules/python.md。

**Acceptance evidence:**

- `pytest tests/unit tests/test_api.py -q` → `197 passed`；`integration_test.py` → `21/21 passed`
- `grep -rn "intensity" src/ backend/ --include="*.py"` → 仅 2 处 deprecated 别名（4 行）；stability 引用清零
- CLI 冒烟：`test` 导出题集 JSON；`propose → proposals → merge` 全链路（patch 应用、version++、队列清空）；`focus` 报 invalid choice
- examples 生成文件提交前恢复，残留测试垃圾清理

**Deferred:**

- MCP / toolkit 工具面对齐（build/search/expand_source/create/propose 最小集）→ post-convergence backlog
- Operator UI 对齐（wander 面板已 404、proposed 队列展示）→ post-convergence backlog
- skeletonize deprecated 别名按计划在下一版本移除

---

## 2026-06-10 — 阶段 B：读路径收敛

**Status:** Accepted and merged.

**Merge commit:** `b778abd`（branch `sprint/phase-b-read-path`，5 commits：`2c38526` / `e2386bd` / `9f0e9a4` / `110ccf1` / `e6cef18`）

**Delivered:**

- `build.py`：统一装配管线（DAG 工具 + ContextPack builder + renderers 单一实现）；`context_pack.py` 变 re-export shim，`resolve.py` 变薄别名（管线 + plain-markdown，错误映射为 `Error:` 字符串）；
- 两遍式 trim：第一遍按角色优先级分配预算（target > required > recommended > related，级内 tie-break 被依赖数 → access_count），target/required/recommended 最低 summary，related 可 skipped；第二遍按拓扑序渲染——阅读顺序与预算分配解耦；
- 装配副作用收敛为纯访问遥测：移除 maturity 自动升级、stability SInc 与 stale 衰减写入（architecture §5.1 惰性元数据契约）；
- `codememory build` 命令落地（默认 xml-markdown），`handle_build` 为主 handler，`handle_context_pack` 委托之；
- search 词法排序：分词 + 字段加权（id=4/summary=3/tags=2/body=1）+ OR 语义 + score 排序，零新依赖；
- 行为修正：`--budget 0` 从"视为无限"改为真实零预算（全员降级 summary）；
- 文档同步：guide §0、CLAUDE.md（对照/速查/文件树）、prd §4.2 实现状态、architecture §2/§6 阶段标记。

**Acceptance evidence:**

- `pytest tests/unit -q` → `184 passed`（新增 search 排序 5 + 管线 8 个金测试；7 个旧格式断言测试按契约迁移）
- `tests/integration_test.py` → `24/24 passed`（解析器迁移到统一渲染格式）
- CLI 冒烟：`build --format plain-markdown` ≡ `resolve`、`build` ≡ `context-pack`（剔除时间戳行后 diff 为空）；多 token 排序符合预期
- examples 生成文件提交前已恢复（pitfalls 纪律）

**Deferred:**

- 修改类 proposal patch 队列、intensity 移除、legacy 命令删除、test 契约 → 阶段 C
- resolve / context_pack shim 的去留 → 阶段 C 处置

---

## 2026-06-10 — 阶段 A：写入纪律

**Status:** Accepted and merged.

**Merge commit:** `ae30ee8`（branch `sprint/phase-a-write-discipline`，4 commits：`e1408cc` / `546b3db` / `1ad9129` / `067a943`）

**Delivered:**

- `create --propose` 产出 `status: proposed` 的 atom；
- `merge <id>` / `reject <id>`：proposed → active / archived，写审计日志，非 proposed 目标报错退出；
- 过滤语义：search 默认仅返回 active/draft（显式 `--status` 可见任意状态）；resolve 与 context-pack 跳过 proposed/archived/superseded 节点并出 notice，拒绝非可装配 target 并给出 merge 指引；共享契约常量 `NON_ASSEMBLABLE_STATUSES`（models.py）；
- validate 新增 `[PROPOSED-WARN]`（proposed 积压 >14 天）与 `[STATUS-WARN]`（active atom 引用非可装配节点）；
- protected 与 intensity 解耦：仅 owner 手动设置，`create --intensity 8` 不再自动加锁；
- `update --source-ref / --source-ref-summary`：asset 绑定的 CLI 写入路径（按 artifact_id 幂等，经 context-pack 渲染）；
- 文档同步：agent-memory-guide §0/§5/§6、CLAUDE.md 概念对照与 CLI 速查。

**Acceptance evidence:**

- `PYTHONPATH=src python -m pytest tests/unit -q` → `171 passed`（新增 18 个写入纪律测试，零回归）
- `PYTHONPATH=src python tests/integration_test.py` → `24/24 passed`
- SPRINT 合同 7 步 CLI 冒烟逐步执行，行为全部符合契约
- examples 生成文件按 pitfalls 规则恢复（`ccc05ab`）

**Deferred:**

- 修改类 proposal patch 队列 → 阶段 C
- `build` 动词收敛、两遍式 trim、search 词法排序 → 阶段 B

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
