# CodeMemory Architecture

> **Architecture thesis**
> CodeMemory 的正式架构不再是“一个带若干拟人特性的记忆工具”，而是：
> **中立的 Core + 声明式 Layer Profiles + Memory Compiler + 多种 Adapters**。

**最后更新**：2026-05-18
**适用版本**：v1 / Work Layer first

---

## 1. 设计原则

1. **Core neutral, layers opinionated**
   Core 只定义稳定机制；Layer 负责场景判断。

2. **Dependency resolution before semantic retrieval**
   对工作记忆而言，先保证依赖完整，再谈搜索丰富。

3. **One memory model, many products**
   同一底层可以支撑 Work Layer，也可以支撑未来 Companion Layer。

4. **Thin adapters**
   CLI、API、MCP、SDK、UI 都只暴露能力，不私自扩展语义。

5. **Migration by compilation**
   迁移不是搬运旧文件，而是把既有资料编译成可审阅、可追溯的 draft memory graph。

6. **Portability by construction**
   纯文本、可审计、可移植、可版本控制，是架构默认值。

---

## 2. 总体分层

```text
┌──────────────────────────────────────────────────────────────┐
│                        Layer Profiles                         │
│   Work Layer (v1)        Companion Layer (future)        ...  │
│   policies / schemas / directories / recall / validation      │
├──────────────────────────────────────────────────────────────┤
│                         CodeMemory Core                        │
│ format / ids / atom+schema / imports DAG / resolve / lifecycle │
│ versioning / validation / index / audit / access primitives    │
├──────────────────────────────────────────────────────────────┤
│                       Memory Compiler                         │
│ ingest / segment / propose / dedupe / review / materialize     │
├──────────────────────────────────────────────────────────────┤
│                            Adapters                           │
│      CLI       Python SDK       MCP       REST API       UI    │
└──────────────────────────────────────────────────────────────┘
```

### 2.1 Core

Core 是跨场景稳定不变的部分：

- Markdown + YAML frontmatter 文件格式；
- `atom` 与 `schema` 两种基础类型；
- 路径式 ID；
- 状态、版本、来源、哈希；
- `imports.required / recommended / related`；
- DAG 构建、循环检测、拓扑排序、预算裁剪；
- 索引、校验、更新、审计；
- 访问统计等通用观测信号。

### 2.2 Layer Profile

Layer Profile 是对 Core 的声明式解释层。它定义：

- 命名空间与目录约定；
- 默认 schema；
- 允许的边语义；
- 写入门槛；
- 召回策略；
- 生命周期和保留/遗忘策略；
- 校验增强规则；
- UI 呈现偏好。

**重点**：Layer 不是新的存储引擎，而是策略表。
不同 layer 可以共享 Core，却表现为不同产品。

### 2.3 Memory Compiler

Memory Compiler 是把**既有资料**转成 CodeMemory graph 的生成链路。
它横跨 Layer 与 Core，但不改变两者边界：

- Layer 决定什么样的记忆值得被提议；
- LLM 负责理解原始材料并生成 proposal；
- Core 负责校验、版本化、落盘和保真。

默认迁移流：

```text
source corpus
  ↓
ingest
  ↓
segment
  ↓
llm propose atoms / schemas / imports
  ↓
dedupe + conflict detection
  ↓
review set
  ↓
materialize canonical memories
```

v1 首个正式支持的 source corpus 是 Markdown。

### 2.4 Adapters

Adapters 负责让外部系统调用同一套语义：

- CLI：本地脚本与手工操作；
- Python SDK：程序内嵌；
- MCP：agent 工具调用；
- REST API：Web 后端；
- UI：人类浏览与维护；
- Harness / Sandbox：agent runtime 集成。

Adapter 必须遵守：

1. 不复制业务语义；
2. 不偷偷改变 layer 规则；
3. 同名操作在不同 adapter 下应保持一致输入输出契约。

---

## 3. Core 数据模型

### 3.1 Memory Types

#### `atom`

通用记忆单元。
事实、决策、流程、上下文包、复盘，默认都用 `atom` 表示。

#### `schema`

结构模板。
定义某类 atom 所需字段，但自身不是业务记忆。

> 早期文档中的 `instance` 与 `composite`，在当前正式模型中都应视为 **atom 的角色差异**，而不是独立类型：
>
> - 带 `schema` 的 atom = 旧语义里的 instance；
> - 带 `imports`、用于打包上下文的 atom = 旧语义里的 composite。

### 3.2 Core Fields

Core 负责理解的基础字段包括：

- `type`
- `id`
- `summary`
- `status`
- `created`
- `updated`
- `version`
- `tags`
- `source`
- `summary_hash`
- `schema`
- `imports`

扩展字段允许由 Layer 使用，但只有被 Core 声明支持的字段，才具有跨 adapter 的稳定语义。

### 3.3 Imports

```yaml
imports:
  required: []
  recommended: []
  related: []
```

Core 只保证：

- 三种边的存储；
- resolve 时的加载优先级；
- required 的强约束行为；
- 循环与断链的校验。

Layer 才负责解释：

- 某类场景里什么算 required；
- related 是“主题相关”还是“情感联想”；
- 是否允许更弱、更强或更特殊的边规则。

---

## 4. Layer Profile 规范

Layer Profile 采用声明式定义，概念上类似：

```yaml
id: work
title: Work Layer

namespaces:
  - work
  - schemas

directories:
  facts: "稳定事实"
  decisions: "决策与理由"
  constraints: "长期约束"
  processes: "流程与手册"
  contexts: "主题入口"
  learnings: "复盘与经验"

edge_semantics:
  required: "缺少它会误解当前记忆"
  recommended: "有助于理解，但不是前提"
  related: "同域相关，可用于探索"

defaults:
  write_threshold: "durable_work_value"
  recall_mode: "deterministic"
  retention_policy: "preserve_unless_explicitly_archived"

validation:
  require_summary: true
  require_change_note_on_update: true
  forbid_cycle: true
```

### 4.1 Work Layer

Work Layer 的默认姿态：

- **写入更谨慎**：只保留有长期工作价值的东西；
- **召回更可靠**：优先完整、稳定、可解释；
- **保留更强**：对重要判断与约束默认不轻易遗忘；
- **结构更明确**：鼓励 schema、依赖、状态、审计。

### 4.2 Companion Layer

Companion Layer 的默认姿态将明显不同：

- 写入门槛更低；
- 允许更松散的联想边；
- 时间、情绪、亲密度可能参与召回；
- “没有被想起”本身也可以是策略的一部分；
- 隐私、同意、敏感度会更靠前。

这说明 Companion 不是 Core 的一组“小功能”，而是一个正式的 Layer Profile。

---

## 5. 数据流

### 5.1 写入流

```text
request
  ↓
adapter normalize
  ↓
layer policy check
  ↓
core create/update
  ↓
validate + index refresh + audit
  ↓
result
```

职责划分：

- Adapter：把外部请求变成标准调用；
- Layer：判断“该不该这样记”；
- Core：保证“写进去后是正确且一致的”。

### 5.2 召回流

```text
query / target id
  ↓
adapter normalize
  ↓
layer recall policy
  ↓
core resolve / search
  ↓
ordered context bundle
  ↓
adapter render
```

Work Layer 的典型召回路径：

1. 找到目标 memory / context；
2. 按 `imports` 构建 DAG；
3. 拓扑排序；
4. 按预算进行全文 / summary 降级；
5. 输出可解释、顺序稳定的上下文。

### 5.3 迁移流

```text
markdown corpus
  ↓
source preservation
  ↓
compiler segmentation
  ↓
llm proposals
  ↓
layer policy review
  ↓
core validation
  ↓
review UI / CLI
  ↓
canonical graph
```

迁移流的硬约束：

1. 原始文档默认保留，不被静默重写；
2. 自动生成结果默认是 draft / proposal；
3. 每条正式记忆都能追溯到 source；
4. dedupe、conflict、断链、循环必须在 materialize 前暴露；
5. “编译成功”不等于“已经成为 canonical truth”。

---

## 6. Core 与 Layer 的边界

| 能力 | Core | Layer |
|------|------|-------|
| 文件格式 | ✅ | |
| atom / schema | ✅ | |
| ID / version / lifecycle | ✅ | |
| imports DAG | ✅ | |
| resolve 算法 | ✅ | |
| index / validate | ✅ | |
| access_count 等原始信号 | ✅ | |
| 哪些目录是官方约定 | | ✅ |
| 什么值得记 | | ✅ |
| 什么算高优先级召回 | | ✅ |
| 遗忘 / wander / salience 的语义 | | ✅ |
| 某种产品体验是否“像人” | | ✅ |
| 原始资料的保留、provenance、proposal 协议 | ✅ | ✅ |

一个重要推论是：
**Core 可以提供观测信号，但不应替任何产品决定这些信号意味着什么。**

例如：

- `last_access`、`access_count` 可以是 Core 信号；
- “冷记忆是否应该被唤起”是 Layer 策略；
- “多久没被访问就算该忘”更是 Layer 策略。

---

## 7. 当前仓库映射

```text
src/codememory/   →  当前主要承载 Core，也混入了少量尚未分离的策略
backend/          →  REST Adapter
frontend/src/     →  Operator UI Adapter
import_cmd.py / skeletonize / suggest_deps
                  →  当前已经出现的 compiler 零件，但还不是完整 Memory Compiler
docs/agent-memory-guide.md
                  →  目前最接近 Work Layer 使用指南的文档
docs/companion-mode.md
                  →  未来 Companion Layer 的探索文档
```

### 7.1 当前实现中的架构漂移

现有代码已经接近新架构，但还存在一些“层没有分干净”的迹象：

1. `wander`、`stability`、部分 decay 语义更像 layer policy，却已经进入 core vocabulary；
2. 某些文档仍混用旧的四原语叙事；
3. 部分 adapter 重新实现了 core 逻辑，增加了契约漂移风险；
4. 当前 Work / Companion 的目录和语义还没有被正式 profile 化。
5. 现有 `import`、`skeletonize`、`suggest-deps` 仍是分散工具，尚未形成统一的 proposal / review / materialize 流程。

这些不是推翻现有实现的理由，而是下一阶段重构时最值得优先收敛的边界。

---

## 8. 接入架构

### 8.1 目标

CodeMemory 应可以无缝接入主流 agent 框架和 harness 系统。
决定可接入性的，不是“有没有很多胶水代码”，而是是否具备：

- 稳定的操作语义；
- 纯文本且可携带的数据格式；
- 明确的工具接口；
- 可在不同 runtime 中复用的 resolve / validate / update 行为。

### 8.2 官方接入面

| 接入面 | 适用场景 |
|--------|----------|
| CLI | shell agent、脚本、手动调试 |
| Python SDK | 自定义 agent / app 内嵌 |
| MCP | 支持 MCP 的 agent runtime |
| Sandbox / Toolkit | harnesslib 等工具注册体系 |
| REST API | Web UI 与外部系统 |

### 8.3 架构要求

1. Core 必须可在无 UI、无后端的情况下独立运行；
2. MCP / SDK / REST 应调用同一业务逻辑；
3. Layer 选择应显式可见，而非散落在 adapter 代码里；
4. 默认 profile 应可被替换，但不能破坏 core contracts。

---

## 9. 未来演进

### 9.1 近期

- 把 Work Layer 的目录、schema、召回、写入规则 profile 化；
- 把 companion-like 策略从 Core 中剥离到未来 profile；
- 把现有导入相关能力收敛成正式 Memory Compiler；
- 先完成 Markdown corpus → draft graph → review → materialize 闭环；
- 统一 backend / frontend / MCP / SDK 的契约；
- 让文档、代码、测试围绕同一套正式模型收敛。

### 9.2 中期

- Companion Layer；
- Research Layer / Project Layer 等更多 profile；
- 更正式的 profile schema 与加载机制；
- 跨 memory root 引用与迁移工具。

### 9.3 暂不优先

- 多 owner 协作；
- 组织权限；
- 企业级知识治理；
- 把 Core 变成重型检索平台。

---

## 10. 架构判准

如果未来某个功能拿不准该放哪里，可用这句判断：

> **如果它改变的是“记忆本身怎么被可靠表示和处理”，它属于 Core；
> 如果它改变的是“在某个场景里什么值得记、如何被想起”，它属于 Layer。**
