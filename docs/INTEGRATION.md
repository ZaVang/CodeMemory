# CodeMemory Integration Guide

> **Terminology note (2026-06-10):** This guide predates the memory-as-code rebuild.
> Conceptual terms (Source Artifact / ContextPack / disclosure, etc.) are superseded by
> the new model in `docs/prd.md` and `docs/architecture.md` (mapping table in prd
> Appendix A). Some CLI examples below are stale after the convergence phases
> (focus/overview/wander and --intensity were removed; build is the primary verb) —
> trust `.claude/CLAUDE.md` CLI quick-reference over this file until the scheduled rewrite
> (see `docs/plan/FUTURE.md`).

This guide gets you from zero to a working codememory integration in **under 10 minutes**.

## Quick Start

```bash
# 1. Install from source
git clone <repo-url> && cd CodeMemory
pip install -e .

# 2. Verify installation
codememory --root examples/investment reindex
codememory --root examples/investment validate
# Expected: "0 errors, 0 warnings"

# 3. Try a resolve
codememory --root examples/investment resolve user/investment/context
# Expected: assembled context with dependencies in topological order
```

## Markdown Migration: Memory Compiler

CodeMemory can migrate an existing Markdown corpus without rewriting the source files. `compile-md` first registers every document as a Source Artifact, then creates a PR-style review set with one anchor candidate per document and one derived candidate per non-empty paragraph. Accepted review items materialize as `status: proposed` atom files; owner merge is still required before they become canonical.

```bash
# 1. Compile existing Markdown into a review set
codememory --root examples/work compile-md ./docs --review-id docs-import --tags "work,migration"

# 2. Inspect the review JSON
cat examples/work/.codememory/reviews/docs-import.json

# 3. Materialize every proposal for a first-pass migration
codememory --root examples/work materialize-review docs-import --accept-all

# 4. Validate the resulting memory graph
codememory --root examples/work validate
```

Compiler guarantees:

- Original Markdown files are not modified.
- Source Artifact IDs are derived from resolved URIs and remain stable when content changes; repeating an unchanged compile does not rewrite registry state.
- Generated memories start as `maturity: draft` and `status: proposed`.
- Every generated memory carries `source_refs`; derived candidates also store paragraph ID/hash and exact line provenance.
- The deterministic path emits no imports suggestions and has no LLM/provider dependency.
- The review JSON can be edited before materialization.
- Existing memory files are not overwritten.

### Optional semantic proposer

Deterministic compilation remains the default. An integration may explicitly opt into the Importer-only semantic proposer by supplying all three LLM arguments:

```bash
pip install -e ".[llm]"
codememory --root examples/work compile-md ./docs \
  --review-id docs-semantic \
  --proposer llm \
  --llm-config ./llm_gateway/config.yaml \
  --llm-model smart
```

This opt-in sends the source paragraph bodies to the configured model. The adapter requests typed structured output with a fixed untrusted-source system instruction, no tools, and bounded output. It never places the gateway config path/body, credentials, raw response, or model thinking in the review metadata. The provider-neutral compiler validates cited paragraph IDs and restricts imports to same-document drafts or the bounded existing-Atom inventory supplied in that call.

LLM mode creates one deterministic anchor per document plus the validated semantic proposals; it does not also create paragraph-copy derived proposals. Same `review_id` + identical source/options is a no-call retry that preserves decisions. Any changed source, namespace, tags, requested model, or config fingerprint conflicts before a model call; use a new review ID to refresh the stable Source Artifact. Materialization preflights the complete accepted semantic batch and writes nothing if a source ref, path, overwrite, import target, or same-batch cycle is invalid. Every resulting atom is still forced to `status: proposed`.

### Compiler Architecture

The migration path is intentionally split into small modules so each stage can be tested independently:

| Stage | Module | Responsibility |
|---|---|---|
| Source manifest | `codememory.compiler.ingest` | Discover Markdown files, skip `.codememory`, compute SHA-256, and never mutate source files. |
| Segmentation | `codememory.compiler.segment` | Preserve heading context, split non-empty paragraphs, and attach exact line provenance. |
| Proposal graph | `codememory.compiler.propose` | Idempotently register assets and generate deterministic anchor/derived proposals with `source_refs`. |
| Semantic proposer | `codememory.compiler.llm_proposer` | Build safe prompts, validate typed semantic drafts/provenance/imports, and generate CodeMemory-owned IDs and proposals. |
| Optional gateway | `codememory.compiler.gateway_adapter` | Lazily adapt explicit `llm_gateway` config/model selection; never loads on the deterministic path. |
| Review persistence | `codememory.compiler.review` | Store/load `.codememory/reviews/{review_id}.json`; identical retries preserve decisions and conflicting reuse is rejected. |
| Materialization | `codememory.compiler.materialize` | Write only accepted candidates as proposed atom files; semantic batches preflight atomically before writes. |

Operational rule of thumb: `compile-md` never edits the source corpus, but it does update the memory root's Source Artifact registry and review JSON. Inspect/edit that review, run `materialize-review` for selected candidates, validate, then use the normal owner merge path to activate them.

## Memory Library Configuration

### The `--root` parameter

All codememory operations target a **memory root directory** -- a folder containing `.md` memory files organised under `user/`, `self/`, and `schemas/` subdirectories.

```bash
codememory --root /path/to/memory/data <command>
```

### `CODEMEMORY_ROOT` environment variable

To avoid passing `--root` on every invocation:

```bash
export CODEMEMORY_ROOT=/path/to/memory/data
codememory reindex   # --root is now optional
```

On Windows (PowerShell):

```powershell
$env:CODEMEMORY_ROOT = "D:\memories"
```

### `.codememory/index.json` structure

The index is a JSON file auto-generated by `reindex`. It lives at `<root>/.codememory/index.json`:

```json
{
  "memories": {
    "user/investment/context": {
      "type": "atom",
      "path": "user/investment/context.md",
      "summary": "...",
      "tags": ["investment"],
      "status": "active",
      "intensity": 8,
      "access_count": 3,
      "dependents": 4,
      "imports": {
        "required": ["user/investment/risk-tolerance"],
        "recommended": ["self/analysis/style"]
      }
    }
  },
  "last_reindexed": "2026-04-27T12:00:00"
}
```

Rebuild the index any time you add, remove, or edit `.md` files:

```bash
codememory reindex
```

## CLI Command Reference

### create — 创建新记忆

```bash
codememory create --id user/ideas/my-thesis --tags "research,ai"
codememory create --id user/decisions/buy-1 --schema schemas/decision --tags "investment"
codememory create --type schema --id schemas/my-template
codememory create --id user/notes/draft --intensity 9 --dry-run
```

**做什么**：生成一个带 YAML frontmatter 模板的 `.md` 文件，并自动更新 `index.json`。

**关键参数**：
- `--type`：atom（默认）| schema（元模板）
- `--schema`：声明依附的 schema ID（可选）
- `--intensity`：1-10，>=8 自动标记 `protected: true`（永不衰减）
- `--dry-run`：预览 frontmatter + body 但不写文件
- `--tags`：逗号分隔，如 `"investment,thesis"`

**输出示例**：
```
Created memory at examples/investment/user/ideas/my-thesis.md
Updating index...
Reindexed 13 memories successfully.
```

---

### update — 更新记忆（含版本控制）

```bash
codememory update user/ideas/my-thesis --change-note "根据 Q2 数据修改" --body "新正文..."
codememory update user/investment/risk-tolerance --status archived --change-note "不再适用"
```

**做什么**：修改记忆的 body/summary/status/imports，自动递增 `version`，追加 `change_log`，重算 `summary_hash`。

**关键参数**：
- `--change-note`（必填）：说明改了什么、为什么改
- `--body`：新正文内容
- `--summary`：新摘要（注意：不传 --summary 但传 --body 时，hash 不变 → 触发 stale 检测）
- `--status`：active | archived | superseded | draft

**输出示例**：
```
Updated user/investment/risk-tolerance to version 3
Updating index...
Reindexed 12 memories successfully.
```

---

### reindex — 重建索引

```bash
codememory reindex
```

**做什么**：扫描 `<root>/user/`、`<root>/self/`、`<root>/schemas/` 下所有 `.md` 文件，提取 frontmatter 元数据写入 `.codememory/index.json`。**保留**已有 `access_count` 和 `last_access`（不重置）。

**何时需要**：手动增删 `.md` 文件后、index.json 损坏时。

**输出示例**：
```
Reindexed 12 memories successfully.
```

---

### validate — 完整性校验 + 衰减建议

```bash
codememory validate
codememory validate -v     # 详细模式（含 INFO）
codememory validate -q     # 静默模式（仅 ERROR）
```

**做什么**：检查四项：

| 检查项 | 说明 | 严重程度 |
|--------|------|----------|
| 断链检测 | A 的 imports 引用了不存在的 B | ERROR |
| schema 合规 | 有 schema 字段时缺少 schema 要求的必填字段 | ERROR |
| 循环依赖 | A → B → A 形成环 | WARNING |
| 衰减建议 | 孤立 + 冷记忆（access_count=0 + 无引用 + intensity<8） | DECAY-WARN |

**输出示例**：
```
Running CodeMemory Validation...

[DECAY-WARN] user/ideas/test has low access (access_count=0), no recent
access, and is not referenced by any other memory. Consider re-linking
or archiving this memory.

Validation complete. 12 memories checked.
Errors: 0, Warnings: 4
```

**如何解读**：
- `Errors: 0` — 依赖图健康，可以放心用
- `Warnings: N` — 有 N 条衰减建议，需要人工判断是否要归档或重新关联
- 出现 ERROR 时 exit code = 1（CI 可据此失败）

---

### resolve — DAG 拓扑拼装上下文

```bash
codememory resolve user/investment/context
codememory resolve user/investment/context --depth full --budget 2000
```

**做什么**：从目标记忆出发，递归加载其 `imports` 依赖，按拓扑排序（被依赖的在前）输出完整上下文。超预算时降级非核心节点为 summary。

**关键参数**：
- `--depth`：required（默认，只含 required imports）| recommended | full（含 related）
- `--budget N`：token（字符）上限，触发降级策略
- `--focus <type>`：按语义类型过滤（如 `decision`、`pitfall`），匹配的节点保持正文，不匹配的降级为 summary

**降级顺序**：required=full > recommended=full > required=summary > recommended=summary > related=full

**输出末尾的 `## Notices` 节**：resolve 过程中发现的数据质量问题：
- `[NOTICE] summary may be stale for <id>` — body 被改了但 summary_hash 未更新
- `[NOTICE] pinned version v1 of <id> is behind current version v3` — 引用了旧版本

---

### context-pack — 结构化 agent handoff 上下文包

```bash
codememory context-pack user/investment/context
codememory context-pack user/investment/context --format json --budget 2000
codememory context-pack user/investment/context --format markdown --task-goal "Review this project before coding"
```

**做什么**：生成可直接交给 agent / harness 的结构化上下文包。Core contract 是 `ContextPack` JSON/Pydantic 对象；XML / Markdown 只是 renderer。

**支持格式**：
- `xml-markdown`（默认）：XML tags 标定边界，正文用 Markdown/CDATA，适合直接复制给 LLM agent。
- `json`：机器传输格式，适合 SDK、API、MCP、workflow runtime。
- `markdown` / `plain-markdown`：人类可读 handoff。

**REST API**：

```http
POST /api/context-pack
X-Codememory-Dataset: investment

{
  "id": "user/investment/context",
  "depth": "recommended",
  "budget": 2000,
  "format": "xml-markdown",
  "task_goal": "Use this as agent handoff context."
}
```

响应包含：

- `pack`：结构化 ContextPack；
- `rendered`：按 `format` 渲染后的字符串；
- `target` / `format`：便于 adapter 直接路由。

---

### search — 检索记忆

```bash
codememory search --query "risk" --tags "investment" --type atom --status active
```

**做什么**：按条件过滤记忆，按 `(被引用数, access_count)` 降序排列。

**关键参数**：
- `--query`/`-q`：summary 子串匹配（大小写不敏感）
- `--tags`/`-t`：AND 逻辑
- `--type`/`-T`：atom | schema
- `--status`/`-s`：active | archived | superseded | draft
- `--maturity`：过滤 maturity 级别（draft | verified | proven）
- `--semantic-type`：按语义类型过滤（model | decision | guideline | pitfall | process）
- `--has-imports`：只显示有 imports 的记忆
- `--has-schema`：只显示有 schema 引用的记忆

**输出列含义**：`id  type  deps:被引用数  [tags]`，下面一行是 summary。

---

### orphans — 孤立记忆发现

```bash
codememory orphans
codememory orphans --type atom --min-intensity 5
```

**做什么**：列出所有入度为 0（没有任何其他记忆 imports 它）的记忆。高 intensity 标注 `[protected]`，低 intensity 标注 `[decay-risk]`。

**输出示例**：
```
user/ideas/sprint2-test   atom    intensity: 5  last_access: None  [decay-risk]
schemas/decision          schema  intensity: 5  last_access: -     [protected]
```

---

### overview — 透明感知摘要

```bash
codememory overview
codememory overview --tags "investment" --limit 5 --format inject --with-recall
```

**做什么**：输出 top N 最相关（高 heat）的记忆摘要。Agent 会话启动时注入 system prompt 用。

**heat 公式**：`heat = dependents * 10 + access_count`

**输出格式**：
- `default`：表格风格，含 `[active]`/`[stale]` 状态标签
- `inject`：紧凑单行，可直接粘贴到 system prompt
- `--with-recall`：末尾追加一行 `[recall]`（随机触景生情一条冷记忆）

---

### focus — 分辨率切换

```bash
codememory focus user/investment/risk-tolerance --level summary   # zoom-out
codememory focus user/investment/risk-tolerance --level full      # zoom-in
codememory focus some-id --content "body text" --summary "sum" --level full  # 免磁盘
```

**做什么**：对指定记忆切换 full（全文）/ summary（摘要）分辨率。`--content` 模式下不读磁盘，直接对传入内容切换。

---

### wander — 触景生情（随机漫步）

```bash
codememory wander
codememory wander --mode cool --inject
```

**做什么**：随机选一条记忆展示。`--mode cool`（默认）偏向冷记忆（低 access_count 权重更高），模拟"触景生情"。

**权重公式（cool 模式）**：`weight = 1 / (access_count + 1)`，排除 protected 记忆。

**`--inject` 格式**：`[recall] <id> — <summary>（tags: t1,t2）`，单行可直接注入 system prompt。

---

### changelog — 变更历史

```bash
codememory changelog user/investment/risk-tolerance
```

**做什么**：展示该记忆的 `change_log` 历史，按时间倒序。

**输出示例**：
```
# Change Log for user/investment/risk-tolerance

v3 (2026-04-27): 根据 Q2 数据调整风险偏好
v2 (2026-04-24): Sprint 2 测试 update 命令
v1 (2026-03-15): 初始版本 — 从 v1 激进调整为中高
```

---

### snapshot — 瞬态持久化

```bash
codememory snapshot "session-001"
codememory snapshot "my-snap" --target user/investment/context  # 自动 DAG
codememory snapshot "from-dag" --from-dag /tmp/dag.json         # TransientDAG
```

**做什么**：将会话推理链（或指定记忆的依赖上下文）导出为持久化的 `.md` 文件，落盘到 `user/snapshots/{date}-{id}.md`。

---

### log — 全局审计日志

```bash
codememory log
codememory log --limit 10
```

**做什么**：查看 `.codememory/log.md` 最近 N 条操作记录（create/update/snapshot/maturity 升级）。全局追加日志，按时间倒序输出。

**何时使用**：想知道"这个知识库最近发生了什么变化"——不需要翻几十个 `.md` 的 change_log，一条命令看时间线。

---

### import — 冷启动导入

```bash
codememory import --file chat-log.txt --extract preferences
echo "用户偏好长期持有..." | codememory import --stdin --extract decisions
```

**做什么**：从非结构化文本中提取初始记忆，生成 maturity=draft 的 `.md` 文件。所有 import 产物都是 draft 级别——必须经过后续 resolve 验证才能升级到 verified。

**关键参数**：
- `--file <path>`：从文件读取
- `--stdin`：从 stdin 读取
- `--extract <types>`：提取类型（preferences | decisions | facts），逗号分隔

**安全阀**：import 产物 maturity=draft，未被引用的 draft 会被衰减建议标记。不会因自动提取产生不可逆转的噪声。

---

### suggest-deps — 自动依赖推断

```bash
codememory suggest-deps user/investment/new-decision
codememory suggest-deps user/investment/new-decision --min-score 5
codememory suggest-deps user/investment/new-decision --forward-only
codememory suggest-deps user/investment/new-decision --retroactive-only
```

**做什么**：基于三层过滤算法（标签交集 ×3 + Schema 模式 ×5 + dependents），为指定记忆推荐候选依赖列表。输出分为两部分：

- **正向推断**："新记忆该 import 谁"——按 required/recommended/related 分类
- **反向推断**："谁该 import 新记忆"——检测已有记忆中缺少同领域依赖的"孤立的果"

**关键参数**：
- `--min-score N`：只输出得分 >= N 的候选（默认 3）
- `--forward-only`：只做正向推断
- `--retroactive-only`：只做反向推断
- 默认 dry-run，不修改任何文件

**何时使用**：创建新记忆后，不确定该声明哪些 imports 时。suggest-deps 不引入向量/embedding，零新依赖。

---

### Full command list

| 命令 | 一句话 |
|------|--------|
| `create` | 创建记忆文件 + 更新索引 |
| `update` | 版本递增 + change_log + hash 重算 |
| `resolve` | DAG 拓扑拼装上下文 + stale/pin 提醒 |
| `reindex` | 从 .md 文件重建 index.json |
| `validate` | 断链/schema/循环/衰减 四项检查 |
| `search` | 按 query/tags/type/status 检索 |
| `orphans` | 列出入度为 0 的孤立记忆 |
| `wander` | 随机漫步（偏置冷记忆） |
| `snapshot` | 瞬态 → 持久化 atom .md |
| `overview` | top N 摘要（heat 排序 + stale 检测） |
| `focus` | 单个记忆 full/summary 分辨率切换 |
| `changelog` | 查看变更历史 |
| `log` | 全局审计日志（时间线） |
| `import` | 从文本提取初始记忆（draft） |
| `suggest-deps` | 自动推断候选依赖（正向+反向） |
| `source add/list/get/check` | 管理 Source Artifact Registry |
| `source expand` | 显式展开 Source Artifact，返回结构化 JSON |

### Source expansion

`source_refs` 默认只作为 provenance 出现在 ContextPack 中；需要原文时，调用 explicit expansion：

```powershell
codememory source expand src/design-md --max-chars 2000
```

REST adapter:

```text
GET /api/sources/expand?artifact_id=src/design-md&max_chars=2000
```

返回 `SourceExpansion` JSON，包含 artifact id、kind、uri/path、registry hash、current hash、status、content、range 和 message。missing/stale/unsupported 都是结构化状态。

## Sandbox Integration

Register the root-appropriate CodeMemory agent surface into a `harnesslib.Sandbox` with one call. A standard root gets exactly five tools; a Personal Profile gets those five plus six Personal extensions. Toolkit and MCP consume the same catalog and dispatcher. Exported schemas omit `root`, and a caller-supplied root cannot redirect execution.

```python
import asyncio
from harnesslib.sandbox import Sandbox
from codememory.integrations import CodememoryToolkit

async def main():
    sandbox = Sandbox()
    toolkit = CodememoryToolkit(root="examples/investment")

    # One-line registration
    await toolkit.register_to_sandbox(sandbox)

    # A standard root exposes exactly 5 tools, bound to examples/investment
    for tool_def in sandbox.list_tools():
        print(f"  {tool_def.name}: {tool_def.description}")

    # Execute a tool via the sandbox
    result = await sandbox.execute("search_memories", {
        "query": "risk",
    })
    print(result)

asyncio.run(main())
```

### Standard root tools

| Tool | Contract |
|---|---|
| `build_memory` | Assemble canonical Atom context through the explicit imports DAG. |
| `search_memories` | Lexical discovery; a Personal root also returns Capture/Topic routes. |
| `expand_source` | Explicit structured Source Artifact expansion with fresh/stale/missing state. |
| `create_memory` | Create a complete summary/body/imports Atom in one write; standard roots may request active or proposed. |
| `propose_memory` | Queue a modification patch against an existing Atom; target bytes do not change before owner merge. |

### Personal Profile extension

| Tool | Contract |
|---|---|
| `capture_memory` | Append one immutable Capture. |
| `read_memory` | Read Capture/Topic/Claim content by stable ID. |
| `maintenance_status` | Inspect the active run and unconsumed valid Captures. |
| `maintain_memory` | Apply one provenance-rich Topic changeset idempotently. |
| `resume_memory_maintenance` | Resume the same pending or scan-blocked run/delivery. |
| `review_personal_memory` | Apply an owner-provided promote/merge/delete batch. |

Initialize a Personal instance with `codememory init <path> --profile personal`. Its agent `create_memory` is always forced to `status: proposed`, even if a caller submits `propose: false`; only the trusted owner CLI confirmation path can create an active canonical Atom directly. `capture_memory` never performs maintenance, Git delivery, semantic indexing, or Web work. A maintenance changeset uses `{"topics": [...]}` where every paragraph/claim carries `derived_from` entries containing both `capture_id` and `content_hash`.

MCP is process-bound through a required explicit `CODEMEMORY_ROOT` and has no example fallback. `tools/list` selects the same standard/Personal profile as Toolkit, and `tools/call` uses the same shared dispatcher. Historical agent aliases such as `resolve_context`, `update_memory`, `propose_update`, `snapshot`, `validate_memories`, and `import_memories` are no longer exported; their trusted CLI/Core operations remain available where applicable.

Automation contract: inspect status first; call `maintain_memory` only when there is no active run; call `resume_memory_maintenance` for an existing pending or blocked run. Treat `scan_blocked` as a safety event, never as a review queue item. Retry a failed push through resume and do not submit another changeset.

### OpenAI format export

For platforms that consume the OpenAI function-calling schema directly:

```python
from codememory.integrations import CodememoryToolkit

toolkit = CodememoryToolkit(root="examples/investment")
tools = toolkit.get_tools_for_openai()

# tools is a list of {"type": "function", "function": {...}} dicts
# Ready to pass to OpenAI chat completions, Anthropic Messages API, etc.

import openai
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What are my investment risks?"}],
    tools=tools,
)
```

## Custom Overview Templates

The `overview` command supports two output formats:

### `default` format (human-readable)

```bash
$ codememory overview --limit 3
user/investment/context                     atom       heat: 43 [active]  [investment, user-profile]
    Complete investment decision-making context and constraints
user/investment/risk-tolerance              atom       heat: 15 [active]  [investment, risk]
    Risk tolerance profile: moderate-aggressive, max single position 25%
user/investment/big-tech-thesis             atom       heat:  8 [active]  [investment, thesis]
    Big tech AI infrastructure thesis
```

### `inject` format (system prompt embedding)

```bash
$ codememory overview --format inject --limit 3
[user/investment/context](atom, heat:43, active)[investment, user-profile] Complete investment decision-making context and constraints
[user/investment/risk-tolerance](atom, heat:15, active)[investment, risk] Risk tolerance profile: moderate-aggressive...
[user/investment/big-tech-thesis](atom, heat:8, active)[investment, thesis] Big tech AI infrastructure thesis
```

Use the `inject` format to embed a memory summary directly into your Agent's system prompt:

```python
import subprocess

def get_memory_context() -> str:
    result = subprocess.run(
        ["codememory", "overview", "--format", "inject", "--limit", "5"],
        capture_output=True, text=True, env={"CODEMEMORY_ROOT": "examples/investment"}
    )
    return result.stdout.strip()

system_prompt = f"""You are an investment advisor.

## Relevant memories
{get_memory_context()}

Use these memories to ground your advice."""
```

### With recall

Append a randomly-selected low-activity memory for serendipitous recall:

```bash
codememory overview --with-recall --format inject
```

## LLM Gateway Configuration

The `llm_gateway` package provides a unified multi-provider LLM interface used by the Agent harness.

### Config file format

Create `llm_gateway/config.yaml` (or any path):

```yaml
default_model: fast
skills_dir: skills/

retry:
  max_attempts: 3
  base_delay_seconds: 1
  max_delay_seconds: 30

models:
  fast:
    provider: openai
    model: gpt-4o
    api_keys: ["${OPENAI_API_KEY}"]
    temperature: 0.7
    max_tokens: 32000
    fallback_models: ["gemini_flash"]

  gemini_flash:
    provider: google
    model: gemini-2.0-flash
    api_keys: ["${GEMINI_API_KEY}"]
    temperature: 0.3
    max_tokens: 32000

  smart:
    provider: anthropic
    model: claude-sonnet-4-20250514
    api_keys: ["${ANTHROPIC_API_KEY}"]
    temperature: 0.5
    max_tokens: 64000
```

### API key setup

Environment variables are referenced with `${VAR}` syntax and resolved at load time. Set them before running:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."
```

### Minimal usage

```python
from llm_gateway import LLMBridge, ChatParameters

bridge = LLMBridge.from_config("llm_gateway/config.yaml")

response = await bridge.chat(
    model="fast",
    messages=[{"role": "user", "content": "Hello!"}],
    params=ChatParameters(temperature=0.5, max_tokens=1000),
)
print(response.content)
```

### Structured output

```python
from pydantic import BaseModel

class Sentiment(BaseModel):
    label: str       # "positive" | "negative" | "neutral"
    confidence: float

response = await bridge.chat(
    model="fast",
    messages=[{"role": "user", "content": "Analyze: 'This product is amazing!'"}],
    response_model=Sentiment,
)
print(response.parsed.label)       # "positive"
print(response.parsed.confidence)  # 0.95
```

### Tool use loop

```python
from llm_gateway.tools import FetchURLTool, ReadFileTool

response = await bridge.chat(
    model="smart",
    messages=[{"role": "user", "content": "Summarize https://example.com/api-docs"}],
    tools=[FetchURLTool(), ReadFileTool()],
)
# The bridge automatically enters an agentic loop: call -> execute tools -> call again
```

---

## Putting It All Together

The recommended integration pattern for an Agent application:

```python
import asyncio
from harnesslib.sandbox import Sandbox
from harnesslib.harness import Harness
from codememory.integrations import CodememoryToolkit
from llm_gateway import LLMBridge, ChatParameters

async def main():
    # 1. Set up memory
    toolkit = CodememoryToolkit(root="examples/investment")

    # 2. Set up LLM gateway
    bridge = LLMBridge.from_config("llm_gateway/config.yaml")

    # 3. Set up sandbox with memory tools
    sandbox = Sandbox()
    await toolkit.register_to_sandbox(sandbox)

    # 4. Create harness
    harness = Harness(sandbox=sandbox, bridge=bridge)

    # 5. Run agent loop
    await harness.run("What's my investment risk profile?")

asyncio.run(main())
```

For a complete working example, see [`examples/example_agent.py`](../examples/example_agent.py).
