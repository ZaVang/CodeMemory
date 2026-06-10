# CodeMemory PRD

> **公理**
> 记忆按代码的方式组织——原子化、显式依赖、按需装配。
> 一个记忆库就是一个仓库，agent 是它的运行时。

**最后更新**：2026-06-10
**状态**：canonical
**前身**：2026-05-19 版（Source Artifact / ContextPack 体系）。旧概念的去向见附录 A。

---

## 1. 公理与推论

CodeMemory 的全部设计从一条公理推导：**记忆像代码一样组织**。

三条推论：

1. **原子化**——一个 .md 文件 = 一个可独立引用的语义单元，像一个模块只做一件事；
2. **显式依赖**——"理解这条记忆需要先理解什么"通过 imports 声明，不靠语义相似度猜测；
3. **按需装配**——上下文是从入口解析依赖闭包、在预算内裁剪出的构建产物，不是检索结果的堆砌。

功能筛选标准（设计哲学）：**它在代码世界里的对应物是什么？**
映射得出来的可以进入产品；映射不出来的拒绝，或放入 `docs/reference/` 作为探索记录。

## 2. 背景与问题

长期使用多个 agent 的人，最常见的困境不是没有信息，而是：

- agent 之间无法共享已经形成的判断，每个新会话从零认识你和你的项目；
- 决策只留下结论，没有留下前提、来源和依赖——三个月后没人知道"为什么当时这么定"；
- 长文档存在，但无法稳定压缩成 agent 可直接消费的工作上下文；
- 现有记忆方案要么是手工维护的平面文档（必然漂移、腐烂），要么是向量检索（高召回，但拿到结论时拿不到理解它的前提）。

"拿到结论时同时拿到前提"是因果完整性问题，本质是依赖解析——代码世界用 import 声明和构建系统解决了几十年的问题。CodeMemory 把这套被验证过的机制移植到记忆上。

## 3. 主场景

**跨项目个人工作记忆。**

- 库独立于任何代码 repo，存单一 owner 的判断、决策、偏好、流程、项目上下文入口；
- 消费者是多个 agent（Claude Code、Codex、自建 harness、MCP client），跨本地/云端多环境；
- owner 是唯一 reviewer；agent 是主要写入者，受写入纪律约束（第 6 章）。

暂不服务：多人团队知识库、企业权限治理、面向大众的陪伴产品、通用向量数据库替代品。

## 4. 概念模型

三组共 11 个概念。**实现状态如实标注**——"已定义未实现"是路线图承诺，不是已交付能力。

### 4.1 静态结构（仓库里有什么）

| 概念 | 代码对应物 | 定义 | 实现状态 |
|---|---|---|---|
| **repo**（记忆库） | git 仓库 | 一个目录树 = 一个库；`.codememory/` 存索引、日志、元数据，相当于 `.git/` | 已实现 |
| **atom**（记忆单元） | 模块/函数 | 一个 .md 文件；frontmatter = 接口（id/summary/imports/schema/tags），body = 实现；summary 是签名 + docstring——裁剪后只剩它，必须独立可读 | 已实现 |
| **imports**（依赖） | import 语句 | "理解此记忆需先理解什么"；required / recommended / related 三级 | 已实现 |
| **schema**（结构契约） | 接口/类型定义 | 某类 atom 的字段约定，check 时校验 | 已实现 |
| **asset**（资产） | repo 里的 data/、vendored 文件 | 原始材料（长文档/会议记录/PDF/代码文件）：登记路径+hash+摘要，可被 atom 引用、按需展开；**不是 atom，不进依赖图** | 已实现（CLI 命令组现名 `source`） |

### 4.2 动态操作（对仓库做什么）

| 概念 | 代码对应物 | 定义 | 实现状态 |
|---|---|---|---|
| **build**（装配） | 构建/链接 + tree-shaking | 入口 atom → imports 闭包 → 拓扑排序 → 预算内裁剪（超预算按 target > required > recommended > related 降级为 summary）→ 结构化上下文 | 已实现（CLI 现名 `resolve` / `context-pack`，待收敛为单一动词） |
| **check**（校验） | 类型检查 + linter | 断链、循环、schema 违约、stale asset、孤儿 | 已实现（CLI 名 `validate`） |
| **search**（检索） | 符号搜索 / LSP | **只负责找入口**；找到后一切走 build。词法排序，不做语义装配 | 部分实现（现为子串匹配，词法排序待实现） |
| **test**（验证） | 测试 / CI | 入口 atom 可附黄金问题：装配出的上下文应能让 agent 回答 X；最小形态 = 题集 + LLM judge | 未实现（概念已定型） |

### 4.3 变更管理（仓库怎么演化）

| 概念 | 代码对应物 | 定义 | 实现状态 |
|---|---|---|---|
| **proposal**（提案） | Pull Request | 高风险变更落为 `status: proposed`，不进默认 build，owner merge 后生效 | 未实现（概念已定型；过渡做法见 agent-memory-guide 第 6 节） |
| **log**（日志） | git log | 每次变更的审计轨迹（change_note / log.md） | 已实现 |

## 5. 核心循环

### 5.1 读路径——agent 接活

```text
任务 → search 找入口（检索只到这一步）
     → build：解析依赖闭包，预算内裁剪
     → 需要原文细节时 asset 按需展开（不默认塞全文）
     → 带着上下文干活
```

### 5.2 写路径——agent 沉淀

```text
会话中形成新判断
     → 按 guide 判断：值不值得记 / 记成什么 / 依赖谁
     → 低风险：新增 atom（可声明自己的 imports），不修改任何已有文件 → 直写
     → 高风险：修改已有 atom（正文或 imports）、或涉及 protected atom → proposal
     → owner 异步 review → merge / reject / edit
     → 任何写入后 check 守门
```

### 5.3 维护循环——owner 周期性

```text
check    → stale asset（原文 hash 变了）→ 复核受影响 atom
orphans  → 不可达 atom → 归档或重新挂依赖
test     → 黄金问题回归 → 装配质量没有退化
```

## 6. 写入纪律

| 等级 | 判据 | 路径 |
|---|---|---|
| 低风险 | 新增 atom（可声明自己的 imports），不修改任何已有文件 | 直写，写后 check |
| 高风险 | 修改已有 atom 的正文或 imports；或变更涉及 protected atom | proposal，owner merge 后生效 |

**protected 的语义**：标记"动它必须走 proposal"的 atom（核心原则、硬约束类记忆）。它是写入纪律的判据，由 owner 拍板设置，不与任何重要性评分挂钩。

**check 守门**：任何写入后运行 check；断链、循环、schema 违约即报，不得带病合入。

## 7. 成功标准

**产品侧：**

- 一个全新 agent 通过 search → build 重建某项目的关键上下文，并通过该入口的黄金问题测试；
- 高风险变更 100% 经过 proposal（可由 check 验证）；
- 任何重要结论可追溯：经 imports 到前提，经 asset 引用到原文，经 log 到变更历史。

**工程侧：**

- 所有 adapter（CLI / MCP / REST / SDK）调用同一 core handler；
- prd / architecture / CLAUDE.md 三处术语一致；
- check 全绿是任何 merge 的前置条件。

## 8. 非目标

1. 语义向量检索作为装配机制（search 只做词法入口发现）；
2. 多人协作与权限系统；
3. 拟人记忆、遗忘、陪伴体验（相关探索在 `docs/reference/`）；
4. 把长文档塞进 atom body（那是 asset 的职责）；
5. LLM 直写高风险路径；
6. 图的分支管理（proposal 是状态，不是分支）。

## 附录 A：旧概念对照表（2026-05-19 体系 → 现行）

| 旧概念 | 去向 | 理由 |
|---|---|---|
| Source Artifact / Registry | → asset（保留实现，改名降重） | 概念正确但被包装成平行体系 |
| source_refs | → asset 引用（保留） | 语义不变 |
| ContextPack | → build 的产物（保留实现） | 不再作为独立概念 |
| resolve | → build 的兼容别名 | 双动词收敛 |
| Anchor Atom / Derived Atom | → guide 里的写法模式 | 不配专有名词 |
| Memory Compiler | → importer（迁移工具，保留） | = codemod；"自动结果默认是 proposal"纪律保留 |
| intensity 1-10 | → 砍 | 重要性由图结构（被依赖数）表达 |
| Work Layer / Companion Layer | → 砍 | 场景已锚定；目录约定进 guide；companion 文档留 docs/reference/ |
| overview / focus / wander | → 砍；focus 能力并入 build 参数 | 拟人范式残留，被 search/build/expand 覆盖 |
| TransientDAG / snapshot | → 保留为辅助工具（REPL 草稿） | 非核心概念 |
| maturity / cache_stable / heat | → 实现细节，移出概念层 | 不进 PRD |
| disclosure L0-L3 | → 不作为独立概念 | 是 build 预算 + asset 按需展开的自然结果 |

## 附录 B：术语表

| 术语 | 定义 |
|---|---|
| repo / 记忆库 | 一个目录树形态的记忆仓库，`.codememory/` 为其元数据目录 |
| atom | 可独立引用的最小语义记忆单元，一个 .md 文件 |
| imports | atom 之间的理解性依赖声明（required/recommended/related） |
| schema | atom 的结构契约 |
| asset | 原始材料的登记引用（路径+hash+摘要），不进依赖图 |
| build | 从入口 atom 装配上下文的操作及其产物 |
| check | 静态校验：断链/循环/schema/stale/孤儿 |
| search | 入口发现：词法检索 atom |
| test | 行为验证：黄金问题 + 判分 |
| proposal | 高风险变更的待审状态 |
| log | 变更审计轨迹 |
| protected | "修改必须走 proposal"的 atom 标记，由 owner 设置 |
| owner | 库的唯一所有者与 reviewer |
