# Sprint 14 — Memory Compiler Markdown Migration

> **起始日期**：2026-05-18  
> **来源计划**：`docs/superpowers/plans/2026-05-18-memory-compiler-markdown-migration.md`  
> **目标**：实现 Core/CLI 级 Markdown Memory Compiler，把现有 Markdown 语料安全迁移为可审查、可溯源、可物化的 CodeMemory 原子记忆。

---

## 一、范围与原则

本轮只交付第一条可工作的编译闭环：

```text
Markdown corpus → preserved source manifest → draft proposal graph → review JSON → materialized atom files
```

### 明确包含

- 扫描 Markdown 文件或目录，生成 source manifest，并保留原始文件 SHA-256 与相对路径。
- 按 Markdown heading 切分 source segment，并记录行号、heading、segment id 等 provenance。
- 生成 deterministic draft proposal graph，不依赖 live LLM 调用。
- 保存/加载 review set JSON，允许人工在物化前审查与修改 proposal decision。
- 仅将 accepted proposal 写入 canonical atom `.md` 文件，并刷新索引。
- 暴露 `compile-md` 与 `materialize-review` CLI 命令。
- 更新包导出、打包发现规则与集成文档。

### 明确不包含

- 不做 Web UI review surface。
- 不接入 live LLM extraction backend。
- 不自动覆盖已存在的 canonical memory 文件。
- 不修改源 Markdown 语料。

---

## 二、任务拆分

### 任务 1：Compiler Models 与 Review Set 序列化

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 1.1 | 新建 `tests/unit/test_memory_compiler.py` 基础测试 | 覆盖 `SourceDoc`、`SourceSegment`、`MemoryProposal`、`ReviewSet` 默认值与 JSON round-trip | [x] |
| 1.2 | 新建 `src/codememory/compiler/__init__.py` | 暴露 compiler package 的初始 public API | [x] |
| 1.3 | 新建 `src/codememory/compiler/models.py` | 定义 source/proposal/review/materialize Pydantic v2 模型 | [x] |
| 1.4 | 新建 `src/codememory/compiler/review.py` | 实现 `.codememory/reviews/{review_id}.json` 保存/加载与 proposal decision helpers | [x] |
| 1.5 | 单测验证并提交 | `test_review_set_round_trip` 通过；提交 `feat: add memory compiler review models` | [x] |

**验收命令**：

```bash
python -m pytest -q tests/unit/test_memory_compiler.py::test_review_set_round_trip
```

---

### 任务 2：Markdown Corpus Ingestion 与 Segmentation

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 2.1 | 添加 ingestion/segmentation 失败测试 | 覆盖只读取 `.md`、跳过 `.codememory`、不修改源文件、heading/line provenance | [x] |
| 2.2 | 新建 `src/codememory/compiler/ingest.py` | 实现 `scan_markdown_corpus()`，支持单文件/目录扫描、排序、SHA-256、字符数统计 | [x] |
| 2.3 | 新建 `src/codememory/compiler/segment.py` | 基于现有 `codememory.skeletonize.markdown.split_sections()` 切分段落并记录行号 | [x] |
| 2.4 | 单测验证并提交 | ingestion 与 segmentation 单测通过；提交 `feat: scan and segment markdown corpus` | [x] |

**验收命令**：

```bash
python -m pytest -q \
  tests/unit/test_memory_compiler.py::test_scan_markdown_corpus_preserves_sources_and_ignores_codememory \
  tests/unit/test_memory_compiler.py::test_segment_markdown_doc_tracks_headings_and_lines
```

---

### 任务 3：Deterministic Draft Proposal 生成

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 3.1 | 添加 proposal 生成失败测试 | 覆盖 review/source/segment/proposal 数量、provenance、默认 `draft/pending`、tag 注入 | [x] |
| 3.2 | 覆盖 duplicate memory id 场景 | 相同 heading 生成唯一 memory id，追加 `-2` 等后缀 | [x] |
| 3.3 | 新建 `src/codememory/compiler/propose.py` | 实现 `proposal_from_segment()` 与 `compile_markdown_corpus()` | [x] |
| 3.4 | 更新 compiler package exports | 从 `codememory.compiler` 导出 `compile_markdown_corpus`、`proposal_from_segment` | [x] |
| 3.5 | 单测验证并提交 | proposal 相关单测通过；提交 `feat: generate markdown memory proposals` | [x] |

**验收命令**：

```bash
python -m pytest -q \
  tests/unit/test_memory_compiler.py::test_compile_markdown_corpus_generates_draft_proposals_with_provenance \
  tests/unit/test_memory_compiler.py::test_compile_markdown_corpus_disambiguates_duplicate_memory_ids
```

---

### 任务 4：Accepted Proposal 物化为 Canonical Atom

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 4.1 | 添加 materialization 失败测试 | 覆盖只写 accepted proposal、跳过 rejected proposal、写入 frontmatter、刷新 index | [x] |
| 4.2 | 新建 `src/codememory/compiler/materialize.py` | 实现 frontmatter 构造、文件写入、已存在文件保护、`reindex()` | [x] |
| 4.3 | 更新 compiler package exports | 导出 `materialize_review_set` | [x] |
| 4.4 | 单测验证并提交 | materialization 单测通过；提交 `feat: materialize memory compiler proposals` | [x] |

**验收命令**：

```bash
python -m pytest -q tests/unit/test_memory_compiler.py::test_materialize_review_set_writes_only_accepted_proposals_and_reindexes
```

---

### 任务 5：CLI Handler 层接入

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 5.1 | 添加 handler 失败测试 | 覆盖 `handle_compile_md()` 保存 review set、`handle_materialize_review(..., accept_all=True)` 写入索引 | [x] |
| 5.2 | 修改 `src/codememory/handlers.py` imports | 引入 compiler propose/review/materialize helpers | [x] |
| 5.3 | 实现 `handle_compile_md()` | 支持 source、review_id、tags、namespace，返回 sources/segments/proposals 摘要 | [x] |
| 5.4 | 实现 `handle_materialize_review()` | 支持加载 review、`accept_all` 批量接受、物化、错误摘要 | [x] |
| 5.5 | 单测验证并提交 | handler 单测通过；提交 `feat: add memory compiler handlers` | [x] |

**验收命令**：

```bash
python -m pytest -q \
  tests/unit/test_memory_compiler.py::test_handle_compile_md_saves_review_set \
  tests/unit/test_memory_compiler.py::test_handle_materialize_review_accept_all
```

---

### 任务 6：CLI Commands 接入

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 6.1 | 添加 CLI parser/dispatch 失败测试 | 通过 `codememory.cli.main()` 跑通 compile + materialize | [x] |
| 6.2 | 修改 `src/codememory/cli.py` imports | 引入 `handle_compile_md` 与 `handle_materialize_review` | [x] |
| 6.3 | 添加 `compile-md` subcommand | 参数：`source`、`--review-id`、`--tags`、`--namespace` | [x] |
| 6.4 | 添加 `materialize-review` subcommand | 参数：`review_id`、`--accept-all` | [x] |
| 6.5 | 添加 dispatch branches | 调用 handler 并打印返回摘要 | [x] |
| 6.6 | 单测验证并提交 | CLI 单测通过；提交 `feat: add memory compiler cli commands` | [x] |

**验收命令**：

```bash
python -m pytest -q tests/unit/test_memory_compiler.py::test_cli_compile_md_and_materialize_review
```

---

### 任务 7：Public API 导出与 Package Discovery 修复

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 7.1 | 修改 `src/codememory/__init__.py` | 从 package root 导出 compiler models/functions | [x] |
| 7.2 | 修改 `pyproject.toml` | 将 setuptools 配置改为 `find`，确保 `codememory.*` subpackages 被打包 | [x] |
| 7.3 | import smoke test 并提交 | 验证 `from codememory import compile_markdown_corpus, materialize_review_set`；提交 `chore: export compiler APIs and package submodules` | [x] |

**验收命令**：

```bash
python - <<'PY'
from codememory import compile_markdown_corpus, materialize_review_set
from codememory.compiler import ReviewSet
print(compile_markdown_corpus.__name__)
print(materialize_review_set.__name__)
print(ReviewSet.__name__)
PY
```

---

### 任务 8：集成文档更新

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 8.1 | 修改 `docs/INTEGRATION.md` | 在 Quick Start 后加入 Markdown Migration: Memory Compiler 使用流程 | [x] |
| 8.2 | 记录 compiler guarantees | 明确源文件不修改、proposal 默认 draft、source provenance、review JSON 可编辑、不覆盖现有 atom | [x] |
| 8.3 | Markdown fenced block 检查并提交 | 确认 fenced block 数量成对；提交 `docs: document markdown memory compiler migration` | [x] |

**验收命令**：

```bash
python - <<'PY'
from pathlib import Path
text = Path("docs/INTEGRATION.md").read_text(encoding="utf-8")
assert "## Markdown Migration: Memory Compiler" in text
assert text.count(chr(96) * 3) % 2 == 0
print("docs ok")
PY
```

---

### 任务 9：Full Verification 与手动迁移冒烟

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 9.1 | 跑 focused compiler tests | `tests/unit/test_memory_compiler.py` 全部通过 | [x] |
| 9.2 | 跑 core unit/API tests | `tests/unit tests/test_api.py` 全部通过 | [ ] |
| 9.3 | 跑 standalone integration script | `tests/integration_test.py` 通过 | [x] |
| 9.4 | 跑手动 migration smoke test | 临时 Markdown corpus → review set → materialize → validate，期望 0 errors | [x] |
| 9.5 | 检查 git diff/status | 确认只包含本轮预期文件；如验证暴露问题则补修并回归 | [x] |

**验收命令**：

```bash
python -m pytest -q tests/unit/test_memory_compiler.py
python -m pytest -q tests/unit tests/test_api.py
python tests/integration_test.py

TMPDIR="$(mktemp -d)"
mkdir -p "$TMPDIR/docs"
cat > "$TMPDIR/docs/architecture.md" <<'MD'
# Architecture

Core plus Work Layer.

## Migration

Markdown compiler creates proposals.
MD
PYTHONPATH=src python -m codememory.cli --root "$TMPDIR/memory" compile-md "$TMPDIR/docs" --review-id smoke --tags smoke
PYTHONPATH=src python -m codememory.cli --root "$TMPDIR/memory" materialize-review smoke --accept-all
PYTHONPATH=src python -m codememory.cli --root "$TMPDIR/memory" validate
git diff --stat HEAD
git status --short
```

---

## 三、完成定义

1. 新增 `codememory.compiler` package，包含 models/ingest/segment/propose/review/materialize 六个核心模块。
2. `compile-md` 可以从 Markdown 文件或目录生成 review JSON，且不修改源 Markdown。
3. Review JSON 中每个 proposal 都保留 `source.original_file`、`source.original_sha256`、`source.segment_id` 与行号信息。
4. Generated proposal 默认 `maturity: draft`、`decision: pending`，并带有 `compiled`、`markdown` tag。
5. `materialize-review` 只写入 accepted proposal；`--accept-all` 可用于首次批量迁移。
6. 物化出的 atom 文件包含 canonical frontmatter、source provenance、summary hash，并可被 index/validate 识别。
7. 已存在 atom 文件不会被覆盖，错误会进入 materialization result/output。
8. Public API 与 package discovery 支持安装后导入 `codememory.compiler`。
9. `docs/INTEGRATION.md` 包含完整 Markdown migration CLI 流程。
10. Focused compiler tests、core tests、integration script、manual smoke test 均通过。

---

## 四、实施顺序建议

1. **先建立数据契约**：任务 1 必须先完成，后续模块都依赖 models/review serialization。
2. **再建立只读 source pipeline**：任务 2 确保 compiler 对源 Markdown 是 non-destructive。
3. **再生成可审查 proposal**：任务 3 是 migration 的核心价值点，必须优先保证 deterministic 与 provenance。
4. **再接入物化写盘**：任务 4 才开始写 canonical atom，务必保留 no-overwrite 保护。
5. **最后接入 UX 面**：任务 5-8 依次接入 handler、CLI、public API、文档。
6. **每个任务独立提交**：按原计划中的 commit message 分 8 个小提交，最后任务 9 只在修复验证问题时提交补丁。

---

## 五、当前实现状态（2026-05-18）

- Core/CLI Markdown Memory Compiler 已实现并提交：`codememory.compiler` 包、handlers、CLI、package exports、review JSON、accepted-only materialization、integration docs、focused tests 均已落地。
- Focused compiler tests 已通过：`python -m pytest -q tests/unit/test_memory_compiler.py`。
- Manual migration smoke 已通过：临时 Markdown corpus → `compile-md` → `materialize-review --accept-all` → `validate`，结果为 0 errors。
- `tests/unit tests/test_api.py` 的 full check 当前受环境依赖影响：`tests/test_api.py` 需要 `httpx`；部分既有 skeletonize code tests 需要 optional tree-sitter language packages。
- Frontend 审查发现 `npm run build` 原先存在 TypeScript 阻断问题，本轮已修复；`npm run lint` 仍有 React Hooks/React Refresh 规则层面的结构性问题，详见 `docs/orch/frontend-audit-report.md`。
