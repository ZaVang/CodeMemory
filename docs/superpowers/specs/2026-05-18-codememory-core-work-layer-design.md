# CodeMemory Core / Work Layer Product Design

**Date**: 2026-05-18
**Status**: Approved design direction
**Owner**: CodeMemory

---

## 1. Problem

CodeMemory 最早的吸引力来自“让 agent 的记忆更像人”。
但在当前阶段，项目最有价值、也最常被使用的形态，不应首先是陪伴产品，而应是：

> **一个人可以在多个 agent、多个环境中共享的可靠工作记忆底座。**

原始 idea 与现实需求之间的张力在于：

- 陪伴模式需要自然、选择性、会遗忘的记忆；
- 工作场景需要准确、可追溯、尽量不丢失的记忆。

把两者强行揉进同一个默认模型，会让底层既不够可靠，也不够拟人。

---

## 2. Decision

采用三层产品模型：

1. **CodeMemory Core**
   负责稳定底层能力：格式、模型、依赖图、resolve、版本、生命周期、索引、校验、审计。

2. **Layer Profiles**
   负责场景策略：目录、schema、写入门槛、召回策略、边语义、保留/遗忘规则。

3. **Adapters**
   负责接入：CLI、SDK、MCP、REST API、UI、harness。

4. **Memory Compiler**
   负责把既有资料编译为可审阅的 draft memory graph。

v1 的官方产品层定义为：

- **Work Layer first**
- **single owner first**
- **declarative profile first**
- **markdown migration first**

Companion Layer 被保留为未来正式 profile，而不是继续作为 Core 默认目标。

---

## 3. Why this shape

### 3.1 为什么不是“继续把所有能力都塞进 Core”

因为“可靠工作记忆”与“陪伴记忆”对同一能力的解释经常相反：

- 访问少的记忆，在工作里可能仍然必须保留；
- 访问少的记忆，在陪伴里也许正是“自然遗忘”的一部分；
- 工作召回优先完整；
- 陪伴召回优先时机和分寸。

如果 Core 直接内建某种 recall / forgetting 哲学，它就不再是 substrate，而是一个偷偷带偏见的产品。

### 3.2 为什么 Work Layer 先于 Companion Layer

- 它最能解决当前真实问题；
- 它的正确性要求最严格，能反向磨稳 Core；
- 它可测试、可验证、可集成；
- 它不会阻止未来继续做“更像人”的东西，反而让那件事建立在更稳的地基上。

### 3.3 为什么是 declarative profile

用户选择了 B：让 layer 以声明式 profile 定义，而不是把 layer 做成一堆分叉逻辑。
这样做有三个好处：

1. 语义可读；
2. 扩展更稳；
3. future layers 不会反复复制 Core。

---

## 4. Canonical Product Definition

### 4.1 Core

Core 拥有：

- 文件格式；
- `atom` / `schema`；
- ID 与版本；
- 生命周期；
- `imports`；
- DAG resolve；
- index / validate / audit；
- 通用访问观测信号。

Core 不拥有：

- 某个场景里“什么值得记”；
- 某种拟人化召回风格；
- 遗忘、wander、salience 的默认产品含义。

### 4.2 Work Layer

Work Layer 服务一个 owner 的长期工作记忆，重点覆盖：

- facts
- decisions
- constraints
- processes
- contexts
- learnings

它的默认原则：

- 写入谨慎；
- 召回可靠；
- 保留优先；
- 审计友好；
- 跨 agent 一致。

### 4.3 Companion Layer

Companion Layer 未来再定义：

- 更低的写入门槛；
- 更松散的联想边；
- 对时机、情绪、亲密度的召回权重；
- 会遗忘、会模糊、会克制的行为；
- 更严格的隐私与同意规则。

---

## 5. Architecture consequences

### 5.1 Data model

正式模型收敛为：

- `atom`
- `schema`

早期文档中的 `instance` 与 `composite` 被视为 atom 的不同角色，而不是独立类型。

### 5.2 Layer boundary

Layer 需要至少声明：

- directories
- default schemas
- edge semantics
- write policy
- recall policy
- retention / forgetting policy
- validation rules

### 5.3 Adapter boundary

CLI、API、MCP、SDK、UI 应共享同一套 core service，而不是复制逻辑。

### 5.4 Memory construction boundary

LLM 负责从非结构化源材料中提议：

- atoms
- schemas
- summaries
- candidate imports
- duplicates / conflicts

但这些提议默认只进入 draft / proposal 状态。
Core 必须保留 provenance，并在 materialize 前执行校验。
用户体验上，这应更像“审阅一组变更”，而不是“黑箱导入”。

---

## 6. Migration as first wedge

Work Layer 的首个增长入口不是“要求用户从今天开始按新格式写”，而是：

> **把用户现有的 Markdown 知识库迁移成 agent 可继续工作的 memory graph。**

默认迁移流：

```text
markdown corpus
  ↓
preserve originals
  ↓
compiler proposes draft graph
  ↓
review like a PR
  ↓
approve / reject / merge / edit
  ↓
materialize canonical memories
```

核心原则：

- preserve originals
- promote drafts
- review before canon
- trace every memory to source
- start useful, become cleaner

---

## 7. Documentation consequences

本设计生效后，canonical docs 应调整为：

1. `docs/prd.md`
   改写为新的产品定义；

2. `docs/architecture.md`
   改写为 Core / Layer / Adapter 正式边界；

3. `docs/agent-memory-guide.md`
   后续收敛为 Work Layer 使用指南；

4. `docs/companion-mode.md`
   保留为未来 Companion Layer 的探索文档，不再代表 v1 默认行为。

---

## 8. Non-goals

本轮设计不解决：

- 团队协作；
- 企业知识治理；
- Companion Layer 的最终产品细节；
- 全量实现重构；
- 任何代码级迁移方案。

这些将在文档稳定后进入单独的整改清单与实施计划。

---

## 9. Success criteria

本设计成立的标志：

1. 团队可以用一句话说清 CodeMemory v1 是什么；
2. Work Layer 与 Companion Layer 的边界被正式拆开；
3. Core 不再被拟人化目标牵着走；
4. 用户可以从现有 Markdown corpus 迁移进入系统，而不是被迫从零开始；
5. 后续代码 review 能以新的架构边界为准绳；
6. 新增未来 layer 时，不必推翻底层。

---

## 10. Final product sentence

> **CodeMemory v1 is a reliable work-memory substrate for one owner across many agents and environments; human-like memory behavior belongs to future layer profiles, not to the core substrate itself.**
