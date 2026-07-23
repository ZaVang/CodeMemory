# CodeMemory Sprint History

This file records accepted sprint outcomes. Current work belongs in `docs/plan/SPRINT.md`; long-term backlog belongs in `docs/plan/FUTURE.md`.

---

## 2026-07-23 — Operator UI Alignment: Build, Review Queue, and Golden Questions

**Status:** Accepted by owner.

**Delivered:**

- Added a primary structured `/api/build` REST path, kept compatibility endpoints on the same Core pipeline, and moved `/api/search` to Core delegation with REST-only field mapping.
- Added typed proposed-Atom and patch-proposal review queues with explicit kind-specific merge/reject actions and bounded failure behavior.
- Added read-only golden-question TestBundle display, complete one-call create/update semantics, and clear non-buildable status handling.
- Reworked the React operator UI around Build and Review workflows while preserving graph, list, dashboard, dataset switching, themes, keyboard behavior, validation, and reindex flows.
- Removed active intensity, stability, decay, wander, and touch behavior from frontend contracts and replaced graph sizing with bounded canonical metadata.
- Restricted every UI request to an existing dataset alias, rejected absolute/traversal/unknown roots, added resolved containment as a final defense, and reset request-scoped ContextVar state after each request.
- Updated PRD, architecture, README, USER_GUIDE, project structure, roadmap, UI help/onboarding copy, and API/frontend regression coverage.

**Acceptance evidence:**

- Owner independently rechecked dataset alias containment and Core search delegation; the former absolute-path header escape now returns 400 and creates neither external memory nor index files.
- `tests/test_api.py` → `30 passed`
- `tests/unit/test_create_update.py` → `14 passed`
- `python -m pytest tests/unit tests/test_api.py -q` → `271 passed` with one existing warning
- Personal Profile suite → `42 passed`
- `python tests/integration_test.py` → `21/21 passed`
- `python tests/integration_personal.py` → `15/15 passed`
- Frontend build and lint passed; Playwright smoke → `6 passed`
- `git diff --check` → passed; generated example test differences restored

**Deferred:**

- Personal Memory Web instance registry, Capture/Incubator browsing, provenance timeline, and batch Topic review.
- Importer/compiler review-set UI and LLM proposer configuration.
- Golden-question execution/evaluation harness, Web/PDF ingestion, semantic discovery, external embeddings, and production authentication.

---

## 2026-07-22 — Adapter Alignment: Shared MCP / Toolkit Agent Surface

**Status:** Accepted by owner.

**Delivered:**

- Added one provider-neutral, root-bound agent-tool catalog and dispatcher shared mechanically by MCP, Sandbox/Toolkit, OpenAI, Anthropic, and Gemini exports.
- Defined the exact five-tool standard surface (`build_memory`, `search_memories`, `expand_source`, `create_memory`, `propose_memory`) and the exact six-tool Personal Profile extension for capture/read/maintenance/review.
- Added complete one-write agent creation, forced proposed status for Personal Profile agent-created Atoms, and modification proposals that preserve target bytes until owner merge.
- Removed legacy direct-update/import/validation/snapshot/log tools from agent surfaces while retaining trusted owner CLI/Core operations.
- Required explicit MCP root binding, ignored caller-forged root values, preserved bounded JSON-RPC errors, and kept source expansion payloads consistent across adapters.
- Closed the final owner-review blocker by centralizing strict slash-delimited ID validation and resolved root containment across create/propose/update/merge/reject/promotion paths; dot segments, empty segments, backslashes, drive paths, and absolute paths are rejected while valid nested Chinese IDs remain supported.
- Updated PRD, architecture, integration guidance, README, project structure, roadmap, sprint pitfalls, and regression/integration coverage.

**Acceptance evidence:**

- Owner independently reproduced `../other/escape`, backslash traversal, absolute drive, root-absolute, dot-segment, and whitespace-segment rejection; confirmed valid nested Chinese creation remains inside the bound root and both external escape artifacts were removed.
- Focused path/adapter/proposal/promotion suite → `63 passed` with one existing Pydantic deprecation warning
- `python -m pytest tests/unit tests/test_api.py -q` → `248 passed` with one existing warning
- Personal Profile suite → `42 passed`
- `python tests/integration_test.py` → `21/21 passed`
- `python tests/integration_personal.py` → `15 passed, 0 failed`
- `git diff --check` → passed; generated example test differences restored

**Deferred:**

- Importer/compiler tools in MCP or Toolkit and owner-only administration tools.
- Operator UI alignment, eval harness, Web/PDF ingestion, and Personal Memory semantic discovery.

---

## 2026-07-22 — Importer v2B: Optional LLM Semantic Proposer

**Status:** Accepted by owner.

**Delivered:**

- Added an explicitly enabled `compile-md --proposer llm` path requiring both gateway config and model arguments; deterministic v2A remains the default and loads no provider dependency.
- Added a provider-neutral semantic proposer with fixed untrusted-source instructions, typed structured output, bounded existing-Atom inventory, stable proposal/path ownership, paragraph-level provenance validation, and controlled same-document/existing-Atom imports.
- Added a lazy `llm_gateway` adapter with low-temperature bounded generation and no tools/Web; review metadata stores safe per-call provider/model/token usage that can be losslessly aggregated, without config paths/content, credentials, prompts, or raw thinking.
- Added semantic review idempotency: identical `review_id` source/options retries make no second model call and preserve registry/review bytes and decisions; changed inputs conflict before model invocation or mutation.
- Added whole-batch semantic materialization preflight for exact source paragraph/range provenance, safe/non-existing paths, resolvable imports, and same-batch cycle freedom; any failure writes zero files.
- Preserved the canonical gate: even tampered active proposals materialize as `status: proposed`, and default search/build excludes them until owner merge.
- Updated PRD, architecture, roadmap, guides, project structure, optional dependency packaging, and fake-bridge regression coverage without any live provider/network requirement.

**Acceptance evidence:**

- Owner independently reproduced explicit-only activation, pre-call digest conflicts, lazy gateway loading, bad-provenance and unknown-import rejection, valid same-document import resolution, no-call retry byte stability, same-batch cycle zero-write, forced-proposed materialization, and default search exclusion with no actionable findings.
- Importer/LLM focused suite → `37 passed`
- `python -m pytest tests/unit tests/test_api.py -q` → `217 passed`
- Personal Profile suite → `38 passed`
- `python tests/integration_test.py` → `21/21 passed`
- `python tests/integration_personal.py` → `15 passed, 0 failed`
- Core import boundary → `core import ok`, `llm_gateway` not loaded
- `git diff --check` → passed; generated example test differences restored

**Deferred:**

- MCP/toolkit importer surface and Operator UI review workflows.
- Web/PDF/non-Markdown ingestion, cross-document semantic deduplication, and Personal Memory semantic discovery.

---

## 2026-07-22 — Importer v2A: Deterministic Source-Aware Markdown Compiler

**Status:** Accepted by owner.

**Delivered:**

- Upgraded `compile-md` to register each Markdown document as a stable URI-derived Source Artifact before generating its review set; unchanged upserts do not rewrite registry state.
- Added one compact anchor proposal per document and one deterministic derived proposal per non-empty paragraph, with artifact reference, stable paragraph ID, content hash, heading context, and exact line range.
- Kept review acceptance separate from canonical acceptance: compiler v2 materialization requires registered `source_refs` and always writes `status: proposed`, so default search/build excludes the result until owner merge.
- Added same-review idempotency that preserves decisions and file bytes, rejects conflicting `review_id` reuse before registry/review mutation, and allows a new review to update the same artifact ID/hash.
- Kept the deterministic path free of generated imports and all LLM/provider dependencies; source documents remain byte-identical through compile and materialize.
- Updated PRD, architecture, integration/user guides, agent import guidance, project structure, CLI help, and regression coverage.

**Acceptance evidence:**

- Owner independently cross-validated CRLF input, repeated heading/body text, stable source IDs, paragraph locators, same-review idempotency, conflict rejection, artifact hash refresh, and proposed search/build exclusion with no actionable findings.
- `python -m pytest tests/unit/test_memory_compiler.py tests/unit/test_sources.py -q` → `23 passed`
- `python -m pytest tests/unit tests/test_api.py -q` → `203 passed`
- Personal Profile suite → `38 passed`
- `python tests/integration_test.py` → `21/21 passed`
- `python tests/integration_personal.py` → `15 passed, 0 failed`
- optional provider dependency grep → no matches (exit code 1 as expected)
- `git diff --check` → passed; generated example test differences restored

**Deferred:**

- Optional LLM proposer for semantic extraction, classification, deduplication, and imports suggestions; it must remain in the Importer layer and only emit reviewable proposals.
- MCP/toolkit importer surface, Operator UI review, Web/PDF/non-Markdown ingestion, and Personal Memory semantic discovery.

---

## 2026-07-22 — Personal Memory Phase 1B

**Status:** Accepted by owner.

**Delivered:**

- Added the repository Personal Memory Skill with low-friction record-only behavior, explicit interview-mode gating, active reading, Topic synthesis, paragraph provenance, inline Claim handling, and owner-facing batch review discipline.
- Added a single-active-run maintenance ledger, stable input digest, missed-run catch-up, pending changesets with before/after hashes, idempotent Topic upsert, and interrupted-apply recovery.
- Added monthly Incubator Topic maintenance with stable Topic/revision/Claim IDs, `origin: mixed`, paragraph-level Capture ID/hash provenance, and typed inline Claim search/read without separate Claim files.
- Added owner-gated canonical promotion: Agent-created Atoms default to proposed, explicit owner confirmation activates them, and batch review supports promote/merge/delete while preserving provenance.
- Added optional Git delivery with Profile path allowlisting, staged-diff fixed-pattern and high-entropy scanning, single-run `scan_blocked` recovery, unique `CodeMemory-Run` commit trailers, and same-commit push retry.
- Added CLI and root-bound Toolkit maintenance/status/resume/review adapters, Automation invocation/notification contracts, documentation, and disposable integration coverage.
- Closed four final owner-review findings: public resume now retries `scan_passed` delivery and reconstructs commits from trailers; high-entropy values are blocked without disclosure; NUL-delimited Git parsing supports Chinese paths; self-merge is rejected before mutation.

**Acceptance evidence:**

- Owner independently reproduced all four focused failure windows and accepted Phase 1B with no remaining actionable findings.
- `python -m pytest tests/unit tests/test_api.py -q` → `197 passed`
- Personal Profile suite → `38 passed`
- `python tests/integration_personal.py` → `15 passed, 0 failed`
- existing `python tests/integration_test.py` → `21/21 passed`
- enabled external embedding search → no matches
- `git diff --check` → passed; generated example test differences restored

**Deferred:**

- Personal Memory Phase 2 local semantic discovery and explicitly enabled external embeddings.
- Personal Memory Web UI and arbitrary external-instance browsing.

---

## 2026-07-22 — Personal Memory Phase 1A

**Status:** Accepted by owner.

**Delivered:**

- Added a Personal Profile contract and non-overwriting initialization for ordinary directories, Git repositories without remotes, and fully configured Git repositories; Git delivery remains optional and disabled by default.
- Added append-only Capture storage with stable `cap_<ULID>` IDs, payload-only SHA-256, instance locking, flush + fsync, and complete-block parsing.
- Added typed indexing and lexical discovery across Capture, Incubator Topic, and Canonical Atom, with stable-ID `read` for non-canonical objects and imports-DAG `build` for Atoms only.
- Preserved inline claim blocks inside Topics without prematurely adding claim indexing, maintenance, promotion, Web, semantic discovery, or Git delivery.
- Bound toolkit and MCP adapters to explicit instance roots and exposed the Phase 1A capture/search/read/build surface.
- Closed four owner-review findings: validate now reports malformed Captures; hash-invalid Captures are excluded from scan/index/read; MCP has no writable example fallback; and custom `paths.private_local` drives ignore/tracked validation.

**Acceptance evidence:**

- Owner independently reproduced all four focused fixes and accepted Phase 1A.
- `python -m pytest tests/unit tests/test_api.py -q` → `197 passed`
- Personal Profile suite → `17 passed`
- `python tests/integration_personal.py` → `10 passed, 0 failed`
- existing `python tests/integration_test.py` → `21/21 passed`
- hard-coded production MyMemory path and enabled external embedding searches → no matches
- `git diff --check` → passed; generated example test differences restored

**Deferred / gate state:**

- Phase 1B remains closed pending a separate explicit owner authorization.
- Codex Skill, maintenance, Git delivery, promotion, Web, and semantic discovery were not started.

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
