# CodeMemory Architecture

> **Architecture thesis**
> CodeMemory 的核心架构是：**Source Artifact Registry + Atom Graph + Progressive ContextPack + Thin Adapters**。
> Core 负责可靠表示和装配工作记忆；Layer 负责场景策略；Compiler 负责迁移；Adapters 负责接入。

**最后更新**：2026-05-19
**状态**：canonical / v1 Work Layer first

---

## 1. 架构决策

### 1.1 v1 Core 不追求“像人”

v1 的底层目标是可靠工作记忆，不是陪伴体验。拟人化记忆、遗忘、情绪权重、亲密度等能力可以在未来 Companion Layer 中定义，但不能污染 Core contract。

### 1.2 Atomization 是语义边界

Atom 是可独立引用的语义记忆，不是任意文本块。长文档、代码文件、设计稿、会议记录等原文应进入 Source Artifact Registry，再由 Anchor Atom 和 Derived Atoms 表达其可复用语义。

### 1.3 Source provenance 是一等能力

每条重要 atom 应能追溯到 source。Source 不只是 metadata 字段，而是可被登记、校验、展开和迁移的 artifact。

### 1.4 ContextPack 是 agent handoff 的主协议

`resolve` 的历史价值是把 imports DAG 拼成上下文；新的主协议是 ContextPack：它既包含 memory graph，也包含 source_refs、budget、disclosure level 和 notices。

---

## 2. 总体分层

```text
┌──────────────────────────────────────────────────────────────┐
│                        Layer Profiles                         │
│ Work Layer (v1): directories / schemas / recall / retention   │
│ Companion Layer (future): timing / affect / forgetting        │
├──────────────────────────────────────────────────────────────┤
│                         CodeMemory Core                        │
│ Atom Graph / Source Artifact Registry / ContextPack Builder   │
│ index / validate / lifecycle / audit / access primitives      │
├──────────────────────────────────────────────────────────────┤
│                       Memory Compiler                         │
│ ingest sources / propose anchors+atoms / review / materialize │
├──────────────────────────────────────────────────────────────┤
│                            Adapters                           │
│ CLI / Python SDK / MCP / REST API / UI / Harness tools         │
└──────────────────────────────────────────────────────────────┘
```

### 2.1 Core

Core 只定义跨场景稳定的机制：

- `atom` / `schema`；
- Source Artifact / Source Ref；
- imports DAG；
- index / validate / lifecycle / audit；
- ContextPack assembly；
- budget 与 progressive disclosure；
- adapter 共享 handlers。

Core 不决定“什么值得记”。这属于 Layer Profile。

### 2.2 Layer Profile

Layer Profile 是声明式策略层，定义：

- 目录和 namespace；
- 默认 schema；
- 写入门槛；
- imports 语义；
- 召回策略；
- lifecycle / retention；
- source 展开策略；
- UI 呈现偏好。

v1 官方 profile 是 Work Layer。Companion Layer 是未来 profile。

### 2.3 Memory Compiler

Compiler 负责把已有材料迁移成可审阅 memory graph。它调用 LLM 做 proposal，但不绕过 Core 校验和 review。

### 2.4 Adapters

Adapters 只暴露能力：

- CLI；
- Python SDK；
- MCP；
- REST API；
- Operator UI；
- agent harness tools。

Adapter 不应复制 Core 逻辑，也不应私自扩展 memory semantics。

---

## 3. Core 数据模型

### 3.1 Atom

Atom 是长期工作记忆的基本语义单元。它可以表示：

- 事实；
- 决策；
- 约束；
- 流程；
- 复盘；
- 上下文入口；
- 对 Source Artifact 的 anchor。

核心字段：

```yaml
type: atom
id: project/architecture/context
summary: Stable one-line meaning
status: active
created: 2026-05-19
updated: 2026-05-19
tags: [architecture, context]
schema: schemas/decision        # optional
imports:
  required: []
  recommended: []
  related: []
source_refs: []                 # planned canonical field
```

### 3.2 Schema

Schema 定义某类 atom 的结构，不是业务记忆本体。

```yaml
type: schema
id: schemas/decision
fields:
  - name: decision
    required: true
```

### 3.3 Source Artifact

Source Artifact 是原文或外部材料的 registry entry，不是 atom。

建议 contract：

```yaml
id: src/project-architecture-md
kind: markdown                  # markdown | code | text | pdf | url | external
uri: docs/architecture.md
sha256: "..."
title: CodeMemory Architecture
summary: Canonical architecture document
when_to_read: Read before changing core contracts.
sections:
  - id: progressive-disclosure
    title: Progressive Disclosure
    selector: "## 4. Progressive Disclosure"
status: active                  # active | archived | missing | stale
created: 2026-05-19
updated: 2026-05-19
metadata: {}
```

Storage recommendation:

```text
.codememory/
  index.json
  log.md
  sources/
    index.json
```

原始文件可以继续留在原路径；registry 只保存引用、hash、摘要和结构化 anchors。

### 3.4 Source Ref

Source Ref 是 atom 或 ContextPack 指向 artifact 的引用。

```yaml
source_refs:
  - artifact_id: src/project-architecture-md
    section_id: progressive-disclosure
    range: null
    summary: Progressive disclosure policy for context assembly.
    disclosure_hint: excerpt     # anchor | excerpt | full
```

关键边界：

| 关系 | 含义 | 是否进入 imports DAG |
|---|---|---|
| `imports.required` | 理解当前 atom 必须先理解的 atom | 是 |
| `imports.recommended` | 有助于理解的 atom | 是 |
| `imports.related` | 相关但非前提的 atom | 可选 |
| `source_refs` | provenance 或可展开原文 | 默认否 |

---

## 4. Progressive Memory Disclosure

Context assembly 不应该默认把所有可得文本塞进 prompt，而应按层展开。

| Level | 名称 | 内容 | 默认用途 |
|---|---|---|---|
| L0 | Index Card | id、summary、tags、status、heat | 搜索候选、列表、粗筛 |
| L1 | Atom / Anchor | atom summary、body、imports、source_refs | 默认 ContextPack |
| L2 | Focused Excerpt | source section、range、derived atoms | 任务需要原文细节 |
| L3 | Full Artifact | 完整原文 | 明确要求或预算允许 |

默认策略：

```text
context_pack(target, disclosure_level=1, include_sources="anchor")
```

只有在以下情况展开到 L2 / L3：

- 用户或 agent 明确请求；
- ContextPack notice 指出 source 需要展开；
- task_goal 与 source section 高度相关；
- budget 允许且 layer policy 允许。

---

## 5. Context Assembly

### 5.1 ContextPack Contract

ContextPack 是结构化对象，render 只是输出格式。

核心字段：

```yaml
format_version: context-pack/v1
target_id: user/project/context
task_goal: optional string
budget:
  requested: 3000
  estimated: 1800
disclosure:
  level: 1
  include_sources: anchor
nodes:
  - id: user/project/fact
    type: atom
    summary: ...
    body: ...
    source_refs: []
source_refs:
  - artifact_id: src/...
    disclosure_level: 1
notices:
  - severity: warning
    code: budget_exceeded
```

Render targets:

- XML-tagged Markdown；
- plain Markdown；
- JSON。

### 5.2 Resolve Compatibility

`resolve` 继续保留，但定位应下沉为兼容入口。

目标演进：

```text
resolve(id) ≈ render_context_pack(build_context_pack(id), format="plain-markdown")
```

这能避免 CLI、REST、MCP 各自维护不同拼装逻辑。

### 5.3 Source Expansion

Source expansion 应成为独立能力：

```text
expand_source(artifact_id, section_id=None, range=None, mode="excerpt")
```

它返回 excerpt / full artifact，并保留 hash、路径、selector 和 warning。

ContextPack 默认只引用 source；expand_source 按需补充 source body。

---

## 6. Memory Compiler v2

Compiler 的职责从“把 Markdown 切成 atom”升级为“把文档资产编译成 Source Artifact + Atom Graph proposals”。

```text
source corpus
  ↓
register Source Artifacts
  ↓
extract sections / anchors
  ↓
propose Anchor Atoms
  ↓
propose Derived Atoms / schemas / imports / source_refs
  ↓
dedupe + conflict detection
  ↓
review set
  ↓
materialize accepted proposals
```

硬约束：

1. 原始材料默认保留；
2. 自动输出默认是 proposal；
3. 每个 proposal 能追溯到 artifact；
4. materialize 前必须 validate；
5. LLM 不直接写 canonical truth。

---

## 7. Work Layer

Work Layer 是 v1 的默认场景策略。

默认原则：

- 写入谨慎；
- 保留关键事实、约束、决策和流程；
- imports 追求依赖完整；
- source_refs 追求可追溯；
- ContextPack 追求 agent 可直接使用；
- 过时信息应标记 stale，而不是静默删除。

建议目录：

```text
project/
  facts/
  decisions/
  constraints/
  processes/
  contexts/
  learnings/
schemas/
```

---

## 8. Adapter Contracts

所有 adapter 应共享同一组 core operations：

| Operation | 用途 |
|---|---|
| `create_memory` | 创建 atom/schema |
| `update_memory` | 更新 atom/schema |
| `search_memory` | 搜索候选 |
| `context_pack` | 生成 agent handoff context |
| `expand_source` | 按需展开 Source Artifact |
| `validate` | 校验 graph、schema、source_refs |
| `compile_markdown` | 生成 migration review set |
| `materialize_review` | 晋升 accepted proposals |

优先级：core handler → CLI / REST / MCP / SDK。禁止在 frontend 或 backend router 中重写核心算法。

---

## 9. 当前仓库映射

```text
src/codememory/              Core implementation
src/codememory/context_pack.py
                             Current ContextPack implementation; should evolve to source_refs/disclosure policy
src/codememory/resolve.py    Existing DAG resolver; should become ContextPack-compatible
src/codememory/compiler/     Current Markdown compiler; next step is Source Artifact aware compiler
backend/                     REST adapter
frontend/src/                Operator UI adapter
src/harnesslib/              Optional agent harness layer
src/llm_gateway/             Optional multi-provider LLM gateway
docs/                        Canonical docs only
docs/reference/              Historical idea sources and audits
```

Planned source registry code should live in Core, not backend:

```text
src/codememory/sources.py
# or
src/codememory/sources/
```

---

## 10. Implementation Priorities

### P0

- Freeze this architecture in `docs/prd.md` and `docs/architecture.md`;
- keep `docs/` root canonical;
- make Source Artifact / Atom / ContextPack terms consistent.

### P1

- Implement Source Artifact Registry;
- add source_refs to atom metadata and validation;
- update ContextPack to emit source_refs and disclosure policy;
- add `expand_source`;
- update compiler to produce Source Artifact + Anchor Atom + Derived Atom proposals.

### P2

- expose `context_pack` and `expand_source` through MCP / toolkit / REST;
- update UI for source_refs and migration review;
- improve frontend UX only after backend contract is stable.

### P3

- design Companion Layer as a separate profile.

---

## 11. Architecture Tests

Any new feature should pass these questions:

1. Does it belong to Core, Layer, Compiler, or Adapter?
2. Is it changing memory semantics, or only presentation?
3. Does it confuse imports with source_refs?
4. Does it preserve original source material?
5. Does it make ContextPack more stable for agents?
6. Can it run without frontend?
7. Can another adapter call the same handler?

If the answer is unclear, update architecture before code.
