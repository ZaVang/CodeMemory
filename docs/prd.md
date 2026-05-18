# CodeMemory PRD

> **Product thesis**
> CodeMemory v1 不再试图成为“更像人的记忆系统”；它首先要成为**单 owner、多 agent、多环境共享的可靠工作记忆底座**。
> “更像人”的体验，不属于底层 Core，而应由未来的 Layer Profile 在明确场景中实现。

**最后更新**：2026-05-18
**状态**：新版产品定义
**版本**：v1 / Work Layer first

---

## 1. 背景

当一个人同时使用多个 agent、多个 harness、多个工作环境时，真正昂贵的不是“没有信息”，而是：

- agent 之间无法共享已经形成的判断；
- 同一个项目在不同环境里反复丢失上下文；
- 决策只留下结论，没有留下形成结论所依赖的前提；
- 记忆虽然存在，却无法被可靠、可解释、可复用地重新装配。

传统 RAG 更擅长“尽可能找回相关内容”，却不天然保证：

1. **因果完整性**：拿到结论时，也拿到理解它所需的前提；
2. **跨环境一致性**：不同 agent 读到同一份可复现上下文；
3. **可审计性**：知道一条记忆从何而来、为何被更新、是否已经过期；
4. **可集成性**：在 CLI、API、MCP、SDK、harness 中都用同一套语义。

CodeMemory 的机会，不是去模拟人的全部记忆，而是把“工作中最需要可靠的那部分记忆”做成一个通用 substrate。

---

## 2. 核心判断

### 2.1 可靠 memory substrate 与陪伴模式不是同一个产品

| 维度 | Reliable Memory Substrate | Companion Mode |
|------|---------------------------|----------------|
| 首要目标 | 准确、可追溯、可复用 | 连续感、亲密感、自然感 |
| 记忆门槛 | 高：值得长期保留才写入 | 低：细碎体验也可能重要 |
| 召回原则 | 充分、稳定、可解释 | 适时、克制、像人 |
| 遗忘观 | 工作上常常要“不要忘” | 陪伴中“会忘”本身是人格的一部分 |
| 典型风险 | 漏掉关键依赖导致错误 | 过度精确反而显得机械 |

这两者共享一部分底层能力，但产品目标相反。
因此，CodeMemory 采用：

```
Layer Profiles  =  场景策略
CodeMemory Core =  底层记忆逻辑
Adapters        =  接入方式
```

### 2.2 v1 的正式产品定义

> **CodeMemory v1 = 单 owner、多 agent、多环境共享的可靠工作记忆底座。**

它首先服务于一个人：

- 在多个 agent 之间切换；
- 在多个项目、仓库、工作台之间切换；
- 希望长期保留判断、约束、流程、决策、上下文；
- 希望不同系统调用同一份工作记忆，而不是各自形成孤岛。

### 2.3 为什么先做 Work Layer

原始灵感来自“更拟人的记忆”，但最先值得落地、也最能形成长期价值的，是 **Work Layer**：

- 它能立刻改善真实工作流；
- 它对正确性、复用性、集成性要求最高，能倒逼 Core 设计变稳；
- 它的成功标准清楚，可被测试；
- 它未来仍然能托住 Companion Layer，而不是与之竞争。

---

## 3. 产品模型

### 3.1 CodeMemory Core

Core 是不带人格和场景偏好的底层协议，负责：

- 记忆文件格式；
- `atom` / `schema` 数据模型；
- ID、版本、生命周期、来源、哈希；
- `imports` 依赖图与 resolve；
- 索引、校验、更新、审计；
- 面向 adapter 的稳定操作接口。

Core 的目标不是“像人”，而是**正确、可复现、可移植**。

### 3.2 Layer Profiles

Layer 不是新的数据库，而是一组**声明式策略**，用于解释同一个 Core：

- 该记什么；
- 目录如何分层；
- 默认 schema 是什么；
- `required / recommended / related` 在该场景下分别意味着什么；
- 写入门槛、召回策略、生命周期、遗忘/保留策略如何定义；
- 哪些校验在该场景下是强约束。

v1 首个官方 profile：

#### Work Layer

面向一个人的长期工作记忆：

- 项目事实；
- 设计决策；
- 约束条件；
- 流程与操作手册；
- 领域知识；
- 当前上下文入口；
- 跨 agent 共享的长期判断。

未来 profile：

#### Companion Layer

面向陪伴体验：

- 更低写入门槛；
- 更强的情境联想；
- 对“何时想起”比“想起多少”更敏感；
- 允许遗忘、模糊、情感权重和隐私边界成为一等规则。

Companion Layer 是 **未来场景层**，不是 v1 Core 的成功条件。

### 3.3 Memory Compiler

Memory Compiler 是 CodeMemory 的**生成入口**，负责把现实世界里已经存在的知识资产转成可审阅的 memory graph。

它不是新的 Layer，也不是新的存储引擎，而是一条横向能力：

```text
Source Corpus
  ↓
LLM-assisted compilation
  ↓
Draft memory graph
  ↓
Review
  ↓
Canonical memory graph
```

v1 首要支持的输入源是 **Markdown corpus**：

- 现有项目文档；
- ADR；
- 设计说明；
- 运行手册；
- 长期笔记；
- 其他 `.md` 知识库。

Memory Compiler 的职责：

- 保留原始来源与 provenance；
- 从文档中提议 atoms、schemas、summaries、candidate imports；
- 发现重复、冲突、潜在上下文包；
- 先生成 `draft` / proposal，而不是直接改写 canonical memory；
- 让用户像审 PR 一样 approve / reject / merge / edit；
- 通过校验后再 materialize 为正式记忆。

**关键原则**：
LLM 负责理解和提案；Core 负责约束和保真。
CodeMemory 不要求用户抛弃旧知识库，而是帮助用户把旧知识库编译成 agent 可持续使用的工作记忆。

### 3.4 Adapters

Adapters 负责把同一套 Core / Layer 能力接到不同入口：

- CLI
- Python SDK
- MCP Server
- Harness / Sandbox tools
- REST API
- Web UI

Adapter 不应偷偷引入新的记忆语义；它们只负责暴露能力，不负责定义产品哲学。

---

## 4. 目标用户

### 4.1 Primary User

一个 owner：

- 长期使用多个 AI agent；
- 在多个项目和工具链之间来回切换；
- 需要把“工作中已经想清楚的东西”变成可复用资产；
- 不希望每个 agent 都重新认识自己和自己的项目。

### 4.2 暂不优先的用户

- 多人协作团队知识库；
- 面向大众消费者的陪伴型聊天产品；
- 需要重型文档搜索平台的大型企业知识管理场景。

这些都可能是后续扩展，但不应在 v1 中扭曲 Core。

---

## 5. v1 目标

### 5.1 产品目标

1. **让一个人的工作记忆跨 agent 连续存在。**
2. **让记忆召回具备因果完整性，而不是只靠语义相似度。**
3. **让写入、更新、引用、失效都可追踪。**
4. **让用户能把既有 Markdown 知识库低风险迁移进来。**
5. **让任意主流 agent 框架可以低摩擦接入。**
6. **让未来 Companion Layer 可以建立在 Core 之上，而不污染 Core。**

### 5.2 用户可感知结果

用户应能感受到：

- agent 不再反复问已经回答过的问题；
- 不同环境里的 agent 能接上同一段工作上下文；
- 重要决策能带着“为什么”一起被重新拿起；
- 自己不需要从零开始重写旧知识库，就能开始使用 CodeMemory；
- 自己过去形成的知识不再散落成一堆无法重用的聊天残片。

---

## 6. 非目标

v1 明确**不**做：

1. 模拟完整的人类记忆；
2. 以陪伴感作为第一成功指标；
3. 把所有原始材料都塞进系统并寄望自动提炼真理；
4. 替代全文搜索、向量库、知识库系统；
5. 解决多人协作、权限治理、组织级知识管理；
6. 让 Core 内建某一种具体“人格化策略”。

---

## 7. 首次迁移体验

对新用户而言，Work Layer 的第一增长楔子不是“从今天开始按新协议写记忆”，而是：

> **把你现有散落的 Markdown 文档，编译成 agent 真能继续使用的工作记忆图。**

### 7.1 默认迁移流

```text
选择 Markdown corpus
  ↓
保留原文与 provenance
  ↓
Compiler 生成 draft atoms / schemas / candidate imports
  ↓
展示 review set
  ↓
用户 approve / reject / merge / edit
  ↓
materialize 为 canonical Work Layer memory
```

### 7.2 产品承诺

1. **Preserve originals**：原始文档不被静默改写；
2. **Promote drafts**：自动结果先是 proposal，不是事实本体；
3. **Review before canon**：正式记忆进入 Core 前，必须经过审阅或明确的晋升规则；
4. **Trace every memory**：每条迁移记忆都能回到源文档；
5. **Start useful, become cleaner**：第一次迁移就能产生价值，后续再逐步清洁图谱。

---

## 8. Work Layer 的产品要求

### 8.1 记忆对象

Work Layer 至少需要稳定支持：

| 类别 | 例子 |
|------|------|
| Facts | 项目事实、系统约束、外部接口说明 |
| Decisions | 架构决策、取舍、结论与理由 |
| Constraints | 不可违反的偏好、边界、原则 |
| Processes | 运行手册、排障流程、发布步骤 |
| Contexts | 某个项目/主题的入口包 |
| Learnings | 复盘、踩坑、规律 |

### 8.2 质量要求

Work Layer 中的记忆应尽量满足：

- 可独立理解；
- 可被引用；
- 可被验证；
- 可被更新；
- 有明确生命周期；
- 有可解释的依赖关系。

### 8.3 召回要求

Work Layer 的召回不追求“像回忆一样自然”，而追求：

- **正确优先**；
- **依赖前置**；
- **预算可控**；
- **结果可解释**；
- **跨 adapter 一致**。

---

## 9. 成功标准

### 9.1 Product Success

在单 owner 场景下，CodeMemory v1 成功意味着：

1. 同一份 memory root 可被多个 agent / harness 重复使用；
2. 一个新 agent 能通过 resolve 重建关键工作上下文；
3. 重要结论不会脱离其必要前提被孤立召回；
4. 用户能审计“某个结论是怎么来的、什么时候被改过”；
5. 用户能把已有 Markdown corpus 迁移成可审阅的 memory graph；
6. 用户能把 CodeMemory 当成默认工作记忆层，而不是一次性实验。

### 9.2 Engineering Success

1. Core 语义稳定，不依赖某个 adapter；
2. Work Layer 通过 profile 定义，而非硬编码进 Core；
3. CLI / API / MCP / SDK 输出同一套概念；
4. 未来新增 Layer 不需要重写底层；
5. 当前实现中的 companion-like 策略可被逐步收敛到 layer，而不是继续扩散。

---

## 10. 产品原则

1. **Core neutral, layers opinionated.**
   底层中立，场景层有态度。

2. **Recall is reconstruction, not just retrieval.**
   召回是重构，不只是检索。

3. **Causal completeness beats semantic similarity.**
   对工作记忆而言，因果完整性优先于“看起来相关”。

4. **One owner first.**
   先把一个人的长期记忆做好，再谈团队协作。

5. **Human-like is a layer concern.**
   拟人不是 Core 的方向盘，而是未来 profile 的一种风格。

6. **Adapters should be thin.**
   入口越多，底层语义越要收敛。

7. **Import is a compiler, not a dump pipe.**
   迁移不是搬运，而是可审阅的结构化编译。

---

## 11. 术语

| 术语 | 定义 |
|------|------|
| Core | 不含场景偏好的底层记忆协议与引擎 |
| Layer Profile | 基于场景声明的一组目录、schema、策略、校验规则 |
| Work Layer | v1 官方 profile，服务单 owner 的长期工作记忆 |
| Companion Layer | 未来 profile，服务拟人陪伴体验 |
| Memory Compiler | 将现有资料编译为 draft memory graph 的生成链路 |
| Adapter | CLI / API / MCP / SDK / UI 等接入面 |
| Atom | 通用记忆单元 |
| Schema | 结构模板 |
| Imports | 显式依赖关系 |

---

## 12. 关键决策记录

| 问题 | 决策 |
|------|------|
| v1 首要产品是什么 | Reliable work memory substrate |
| 是否把陪伴模式做进 Core | 否，放到未来 Layer Profile |
| v1 面向谁 | 单 owner |
| v1 官方场景层 | Work Layer |
| Layer 如何表达 | 声明式 profile |
| Core 是否定义人格化行为 | 否 |
| 记忆主模型 | `atom` + `schema` |
| v1 首个迁移源 | Markdown corpus |
| 自动迁移是否直接写 canonical memory | 否，先生成 proposal / draft |
| 是否继续把“拟人化”当作总体口号 | 作为未来体验目标保留，但不再定义 v1 |

---

## 13. 后续文档策略

- `architecture.md`：定义 Core / Layer / Adapter 的正式边界；
- `agent-memory-guide.md`：后续应收敛为 Work Layer 的使用指南；
- `companion-mode.md`：保留为 Companion Layer 的探索文档，但不再代表 v1 默认行为；
- 旧的“四种原语”叙事与早期 Phase 1 文档，应逐步降级为历史材料或归档。
