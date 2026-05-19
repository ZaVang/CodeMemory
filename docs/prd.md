# CodeMemory PRD

> **Product thesis**
> CodeMemory v1 是一个面向单 owner、多 agent、多环境的 **reliable work-memory substrate**。
> 它不是默认拟人陪伴产品，也不是全文知识库或 RAG 搜索器；它的核心价值是把工作记忆整理成可追溯、可装配、可迁移、可被 agent harness 稳定调用的上下文资产。

**最后更新**：2026-05-19
**状态**：canonical / v1 Work Layer first

---

## 1. 背景

用户同时使用多个 agent、多个本地/云端 harness、多个项目环境时，最常见的问题不是“完全没有信息”，而是：

- agent 之间无法共享已经形成的判断；
- 项目上下文在不同环境里反复丢失；
- 决策只留下结论，没有留下前提、来源和依赖；
- 长文档虽然存在，但无法被稳定压缩成 agent 可消费的工作上下文；
- 旧的 Markdown / 笔记 / 设计文档迁移成本太高，导致用户不愿意切换到新系统。

RAG 在工作场景里仍然有价值：它能高召回地找回相关材料，弥补人的遗忘。但它不天然解决：

1. **因果完整性**：拿到结论时，也拿到理解它所需的前提；
2. **结构化迁移**：把既有文档变成可审阅的长期记忆图；
3. **上下文预算控制**：不是“召回越多越好”，而是按任务逐层披露；
4. **跨 adapter 一致性**：CLI、API、MCP、SDK、UI 调用同一套语义；
5. **可审计性**：知道某条记忆从何而来、为何存在、何时需要展开原文。

CodeMemory 的产品机会是：让工作中真正需要可靠保留的知识，成为 agent 可以稳定继承的 substrate。

---

## 2. 产品判断

### 2.1 v1 先做可靠工作记忆，不先做陪伴

可靠 memory substrate 与 companion mode 是两种不同产品目标：

| 维度 | Reliable Work Memory | Companion Mode |
|---|---|---|
| 首要目标 | 准确、可追溯、可复用 | 连续感、自然感、亲密感 |
| 写入门槛 | 高：有长期工作价值才进入 canonical graph | 低：细碎体验也可能重要 |
| 召回原则 | 依赖完整、预算可控、可解释 | 适时、克制、像人 |
| 遗忘观 | 工作中关键记忆默认不应丢失 | 遗忘、模糊、沉默本身可能是体验 |
| 主要风险 | 漏掉关键依赖导致错误 | 过度精确导致机械感 |

两者可以共享 Core，但不能共用同一套默认策略。v1 的正式方向是 **Work Layer first**；Companion Layer 作为未来 profile，不进入 v1 的成功条件。

### 2.2 Atomization 是语义原则，不是把所有文本切碎

CodeMemory 强调 atom，但 atom 不是“任意长文档都要强行拆成很多小文件”。

正式定义：

- **Atom**：可被独立引用的语义记忆，例如事实、决策、约束、流程、上下文入口；
- **Source Artifact**：原始或外部材料，例如长文档、设计稿、会议记录、代码文件、PDF、网页；
- **Anchor Atom**：指向某个 Source Artifact 的轻量语义索引卡；
- **Derived Atom**：从 Source Artifact 中提炼出的可执行事实、决策、约束或流程。

长文档不适合整体塞进 atom。正确模式是：

```text
Source Artifact  保留原文和 provenance
  ↓
Anchor Atom      说明它是什么、什么时候该读、有哪些 source_refs
  ↓
Derived Atoms    只提炼长期有用、可独立引用的语义记忆
```

---

## 3. 产品模型

CodeMemory v1 由四个核心部分组成：

```text
Source Artifacts  →  Atom Graph  →  ContextPack  →  Agent / Human Adapters
        ↑                ↑              ↑
        └────── Memory Compiler ────────┘
```

### 3.1 Source Artifact Registry

Source Artifact Registry 保存原始材料的稳定引用和摘要，不把原文伪装成 atom。

它需要记录：

- artifact id；
- 类型：markdown、code、pdf、url、text、external 等；
- 路径 / URI；
- hash / version；
- title / summary；
- `when_to_read`；
- sections / ranges / anchors；
- provenance；
- 状态：active / archived / missing / stale。

产品价值：

- 迁移旧文档时不破坏原文；
- agent 默认拿到摘要和 source ref，必要时再展开；
- 用户可以追溯每条记忆来源；
- 未来支持不同类型文件，而不污染 atom 模型。

### 3.2 Atom Graph

Atom Graph 是长期工作记忆的 canonical graph。

v1 只保留两个基础 memory type：

- `atom`：通用语义记忆；
- `schema`：结构模板。

Atom 通过 `imports.required / recommended / related` 表示记忆之间的依赖。Atom 通过 `source_refs` 追溯到 Source Artifact。

关键边界：

- `imports` 表示“理解这条记忆需要哪些其他记忆”；
- `source_refs` 表示“这条记忆来自或指向哪些原始材料”；
- Source Artifact 默认不进入 imports DAG，除非被显式展开。

### 3.3 ContextPack

ContextPack 是 v1 面向 agent handoff 的主输出，不只是把 resolve 文本拼起来。

它应该输出：

- 目标 memory；
- 依赖节点；
- 节点摘要和正文；
- source refs；
- disclosure level；
- budget 使用情况；
- stale / missing / cycle / budget notices；
- 可复制给 agent 的 XML-tagged Markdown / Markdown / JSON。

默认策略：

- 先给 agent `atom + summary + source_ref`；
- 不默认塞入长文档全文；
- 当任务需要时，通过 `expand_source` 获取 excerpt 或 full artifact；
- budget 不足时降级为 summary，而不是静默丢掉 required context。

### 3.4 Memory Compiler

Memory Compiler 是迁移入口。它把现有 Markdown / 文档资产转为可审阅的 CodeMemory 结构。

默认迁移流：

```text
选择 source corpus
  ↓
登记 Source Artifacts
  ↓
生成 Anchor Atoms
  ↓
提议 Derived Atoms / schemas / imports / source_refs
  ↓
review set
  ↓
用户 approve / reject / edit / merge
  ↓
materialize canonical Atom Graph
```

LLM 的角色是 proposer，不是 truth source。Core 和 review 流程负责约束、保真和晋升。

---

## 4. 目标用户

### 4.1 Primary User

一个长期使用 agent 的 owner：

- 同时使用 Codex、本地脚本、云端 agent、MCP client 或自定义 harness；
- 在多个项目之间切换；
- 希望项目事实、设计决策、约束、流程和上下文入口可长期复用；
- 不希望每个 agent 都重新认识自己、项目和历史判断；
- 已经有一批 Markdown / 文档 / 笔记，希望低成本迁移。

### 4.2 暂不优先

v1 不优先服务：

- 多人团队知识库；
- 面向大众消费者的陪伴聊天产品；
- 企业级权限治理；
- 重型全文检索平台；
- 通用向量数据库替代品。

---

## 5. 核心用户流程

### 5.1 迁移已有文档

用户选择一个 Markdown corpus，CodeMemory：

1. 保留原始文档为 Source Artifacts；
2. 为重要文档生成 Anchor Atoms；
3. 提议 Derived Atoms、schemas、imports 和 source_refs；
4. 生成 review set；
5. 用户审阅后 materialize。

成功体验：用户不需要重写旧知识库，也不会丢失原文 provenance。

### 5.2 给 agent 交接项目上下文

用户或 agent 选择一个入口 atom，CodeMemory：

1. 解析 imports DAG；
2. 生成 ContextPack；
3. 默认包含 atom 内容和 source refs；
4. 必要时再展开 source excerpt；
5. 输出可复制或可 tool-call 的结构化上下文。

成功体验：新 agent 能快速接上项目，不靠随机搜索。

### 5.3 维护长期工作记忆

用户可以：

- 创建 / 更新 atom；
- 声明 imports；
- 绑定 source_refs；
- 验证断链、循环、stale、schema 问题；
- 通过 UI 或 CLI 审阅 graph；
- 把 ContextPack 交给不同 agent 使用。

---

## 6. v1 Requirements

### P0 — 产品与架构契约

- PRD 和 Architecture 明确定义 Source Artifact / Atom / ContextPack 的边界；
- 文档主干只保留 canonical docs，历史探索进入 `docs/reference/`；
- 所有后续功能优先服务后端和 Core contract，前端只作为 adapter。

### P1 — Source Artifact Registry

- 支持登记 Markdown / text 文件；
- 保存 artifact metadata、hash、summary、sections、status；
- 支持 `source add / list / get / expand` 的 core API 与 CLI；
- 支持 source_refs 被 atom 和 ContextPack 引用；
- validate 能发现 missing / stale artifacts。

### P1 — ContextPack / Resolve v2

- ContextPack 成为 agent handoff 的 canonical output；
- resolve 作为兼容命令保留，但语义收敛到 ContextPack；
- 支持 `include_sources = none | anchor | excerpt | full`；
- 支持 `disclosure_level = 0 | 1 | 2 | 3`；
- 输出 XML-tagged Markdown、Markdown、JSON；
- 默认不展开全文 artifact。

### P1 — Migration Compiler v2

- 编译 Markdown corpus 时先登记 Source Artifacts；
- 自动生成 Anchor Atom proposals；
- 自动提议 Derived Atoms、schemas、imports、source_refs；
- review set 中明确 proposal 与 source 的关系；
- materialize 前必须可审阅、可验证。

### P2 — Agent Framework / Harness Integration

- 对外暴露稳定工具：`context_pack`、`expand_source`、`search`、`create/update`、`validate`；
- MCP / OpenAI function / Anthropic tool / CLI / Python SDK 复用同一 core handler；
- adapter 不重新实现 memory contract。

### P2 — Operator UI

- UI 支持查看 ContextPack；
- UI 支持查看 source_refs 和按需展开 source；
- UI 支持 migration review；
- UI 不定义新的 canonical semantics。

### P3 — Companion Layer

- 仅在 Core、Source Artifact、ContextPack 和 Work Layer 稳定后推进；
- 作为 Layer Profile 设计，不污染 v1 Core。

---

## 7. 非目标

v1 明确不做：

1. 模拟完整人类记忆；
2. 把陪伴感作为第一成功指标；
3. 把长文档直接塞进 atom body；
4. 用 RAG 替代 imports DAG 和 source_refs；
5. 直接把 LLM 迁移结果当 canonical truth；
6. 做企业级团队协作和权限系统；
7. 让 frontend 或 adapter 私自定义 memory contract。

---

## 8. 成功标准

### Product Success

- 一个新 agent 能通过 ContextPack 重建关键项目上下文；
- 用户能把已有 Markdown corpus 迁移成可审阅的 Source Artifact + Atom Graph；
- 重要结论能追溯到 source，并能按需展开原文；
- 不同 adapter 读取到同一套语义；
- 用户愿意把 CodeMemory 作为默认工作记忆层，而不是一次性导入工具。

### Engineering Success

- Core 不依赖 UI、backend 或某个 LLM provider；
- Source Artifact、Atom、ContextPack 有稳定数据契约；
- imports DAG 与 source_refs 清晰分离；
- ContextPack 输出在 CLI、REST、MCP、SDK 中一致；
- Memory Compiler 的自动结果默认是 proposal；
- 前端只做 operator UI，不成为业务逻辑来源。

---

## 9. 产品原则

1. **Atomization is semantic, not mechanical splitting.**
2. **Originals are preserved as artifacts, not disguised as atoms.**
3. **Recall is progressive disclosure, not maximal retrieval.**
4. **ContextPack is the handoff unit.**
5. **LLM proposes; Core constrains; user or policy promotes.**
6. **Backend/Core first; frontend follows contracts.**
7. **Companion is a future layer, not the v1 baseline.**

---

## 10. 术语

| 术语 | 定义 |
|---|---|
| Core | 不含产品人格的底层记忆协议与引擎 |
| Work Layer | v1 官方场景层，服务单 owner 的长期工作记忆 |
| Companion Layer | 未来场景层，服务拟人陪伴体验 |
| Atom | 可独立引用的语义记忆 |
| Schema | Atom 的结构模板 |
| Imports | Atom 与 Atom 之间的依赖边 |
| Source Artifact | 原始或外部材料的稳定引用与 metadata |
| Source Ref | Atom / ContextPack 指向 Source Artifact 的引用 |
| Anchor Atom | 指向 Source Artifact 的轻量语义索引卡 |
| Derived Atom | 从 Source Artifact 中提炼的长期语义记忆 |
| ContextPack | 面向 agent handoff 的结构化上下文包 |
| Memory Compiler | 把既有材料编译成 proposals / review set / canonical graph 的迁移链路 |

---

## 11. 文档策略

`docs/` 根目录只保留长期指导当前产品和工程判断的文档：

- `prd.md`
- `architecture.md`
- `project_structure.md`
- `INTEGRATION.md`
- `USER_GUIDE.md`
- `agent-memory-guide.md`

历史探索、审计报告和非 v1 默认方向放入 `docs/reference/`。它们可以解释 idea 来源，但不作为当前实现依据。
