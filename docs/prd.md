# CodeMemory PRD

> **公理**
> 记忆按代码的方式组织——原子化、显式依赖、按需装配。
> 一个记忆库就是一个仓库，agent 是它的运行时。

**最后更新**：2026-07-23
**状态**：canonical
**前身**：2026-05-19 版（Source Artifact / ContextPack 体系）。旧概念的去向见附录 A。

---

## 1. 公理与推论

CodeMemory 的全部设计从一条公理推导：**记忆像代码一样组织**。

三条推论：

1. **原子化**——一个 .md 文件 = 一个可独立引用的语义单元，像一个模块只做一件事；
2. **显式依赖**——"理解这条记忆需要先理解什么"通过 imports 声明，不靠语义相似度猜测；
3. **按需装配**——上下文是从入口解析依赖闭包、在预算内裁剪出的构建产物，不是检索结果的堆砌。

这三条推论约束的是 **canonical memory**。Personal Profile 中的每日 Capture 和月度 Incubator 文档分别对应 append-only source log 与 working tree；它们不是 atom，不进入 imports DAG，也不要求“一条记录一个文件”。只有提升后的 Canonical Atom 承担可装配的正式认识。

功能筛选标准（设计哲学）：**它在代码世界里的对应物是什么？**
映射得出来的可以进入产品；映射不出来的拒绝，或放入 `docs/reference/` 作为探索记录。

## 2. 背景与问题

长期使用多个 agent 的人，最常见的困境不是没有信息，而是：

- agent 之间无法共享已经形成的判断，每个新会话从零认识你和你的项目；
- 决策只留下结论，没有留下前提、来源和依赖——三个月后没人知道"为什么当时这么定"；
- 长文档存在，但无法稳定压缩成 agent 可直接消费的工作上下文；
- 现有记忆方案要么是手工维护的平面文档（必然漂移、腐烂），要么是向量检索（高召回，但拿到结论时拿不到理解它的前提）。
- 对个人使用者而言，若每次记录都必须分类、填写 frontmatter 或逐条审核 Agent 产物，捕获摩擦和维护负担会使系统失去持续使用价值；反过来，若 Agent 任意生成零碎文件，记忆库又会迅速膨胀和失真。

"拿到结论时同时拿到前提"是因果完整性问题，本质是依赖解析——代码世界用 import 声明和构建系统解决了几十年的问题。CodeMemory 把这套被验证过的机制移植到记忆上。

## 3. 主场景

**跨项目个人工作记忆，以及面向单一 owner 的 Personal Memory Profile。**

- 库独立于任何代码 repo，存单一 owner 的判断、决策、偏好、流程、项目上下文入口；
- 消费者是多个 agent（Claude Code、Codex、自建 harness、MCP client），跨本地/云端多环境；
- owner 是唯一 reviewer；agent 是主要写入者，受写入纪律约束（第 6 章）。
- Personal Profile 中，owner 通过低摩擦 Capture 记录工作、生活和想法；Agent 异步维护 Incubator Topic，并只在提升为 Canonical Atom 时请求 owner 确认。
- 程序仓库与个人实例严格分离：CodeMemory 提供协议、Core 和 adapters；MyMemory 一类外部仓库存放 owner 数据。

暂不服务：多人团队知识库、企业权限治理、面向大众的陪伴产品、通用向量数据库替代品。

## 4. 概念模型

Core 仍由三组共 11 个概念构成。Personal Profile 在这些概念之上定义 Capture 与 Incubator Topic 两类 profile 对象，不把它们伪装成 atom。**实现状态如实标注**——"已定义未实现"是路线图承诺，不是已交付能力。

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
| **build**（装配） | 构建/链接 + tree-shaking | 入口 atom → imports 闭包 → 拓扑排序 → 预算内裁剪（超预算按 target > required > recommended > related 降级为 summary）→ 结构化上下文 | 已实现（CLI 主命令 `build`；`resolve` / `context-pack` 为兼容别名） |
| **check**（校验） | 类型检查 + linter | 断链、循环、schema 违约、stale asset、孤儿 | 已实现（CLI 名 `validate`） |
| **search**（检索） | 符号搜索 / LSP | **只负责发现候选入口**；Canonical Atom 进入 build，Capture / Incubator Topic 走直接读取。词法、时间和标签是默认能力；语义检索只可用于 discovery | atom 词法排序、Personal typed discovery 与可选本地 semantic discovery 已实现 |
| **test**（验证） | 测试 / CI | 入口 atom 可附黄金问题：装配出的上下文应能让 agent 回答 X；eval harness 以同一模型对比 ContextPack、full-memory 与 no-memory，再由盲判 judge 评分 | 已实现（题集导出/report + 显式三臂 eval harness） |

### 4.3 变更管理（仓库怎么演化）

| 概念 | 代码对应物 | 定义 | 实现状态 |
|---|---|---|---|
| **proposal**（提案） | Pull Request | 高风险变更落为 `status: proposed`，不进默认 build，owner merge 后生效 | 已实现（新增类 = `status: proposed`；修改类 = patch 队列 `propose`/`merge`/`reject`） |
| **log**（日志） | git log | 每次变更的审计轨迹（change_note / log.md） | 已实现 |

### 4.4 Personal Profile 三层模型

| 层级 | 代码对应物 | 写入与修改纪律 | 检索与装配 |
|---|---|---|---|
| **Capture** | append-only source log record | 一条输入一个稳定 ID 和独立内容 hash；Agent 只追加，不自动改写或删除；owner 可明确清理 | 可按全文、时间、标签和 provenance 发现并按 ID 读取；不进 build |
| **Incubator Topic** | working tree 中的可演化模块草稿 | 月度文档内按稳定 topic ID 聚类；Agent 可自动补充、合并、纠正；未审阅不阻塞维护 | 可发现、直接读取、参与关联；不进 build |
| **Canonical Atom** | 已合并模块 | 一个文件一个语义单元；由 topic 提升时默认需要 owner 确认；后续高风险修改继续走 proposal | search 找入口后只通过 imports DAG build |

补充规则：

- owner 明确说“新建正式 idea”或等价自然语言时，该指令本身就是本次提升确认；
- Incubator Topic 可以长期未审阅、继续参与检索和关联，不是待办队列；
- 集中审阅必须支持批量提升、合并和删除，不能退化为逐条 proposal 清单；
- Agent 推断可以自动写入 Incubator，但不得无确认提升为 Canonical Atom；
- 原始 Capture 是证据；Incubator 是低风险衍生工作区；Canonical Atom 是少量、长期维护的正式认识。

## 5. 核心循环

### 5.1 两条读路径——发现与装配分离

```text
Path A：canonical
任务 → search 发现 Canonical Atom
     → build：解析 imports 闭包，预算内裁剪
     → 需要原文细节时按 provenance / source_refs 显式展开

Path B：personal discovery
任务 → 按全文 / 时间 / 标签搜索 Capture 与 Incubator Topic
     → 按稳定 ID 读取命中记录或主题段落
     → Agent 主动阅读、比较和综合
     → 若需正式上下文，另选 Canonical Atom 走 Path A
```

Personal Memory Phase 2 提供显式启用的本地语义候选索引：模型必须已存在于 ignored `private_local`，加载时禁止下载和网络 fallback，派生索引也只存于 `private_local`。外部 embedding 保持关闭且当前不受支持。任何语义命中都只能返回 typed 候选入口，不得直接成为 canonical build 的装配节点。

### 5.1.1 Personal owner workspace

本地 Operator UI 可以通过服务端持有的 allowlist registry 打开外部 Personal Profile。请求只携带精确 dataset alias，绝对 root 永不进入 request 或公开 dataset metadata。该工作区只提供：

- 完整且 hash 有效的 Capture 浏览；
- Topic revision、内嵌 Claim、origin / claim_status / provenance 浏览；
- 仅由 authored timestamp 与显式关系组成的 idea timeline；
- 一次 owner 明确确认的 promote / merge / delete 批量审阅。

它不是任意文件浏览器或完整 Markdown 编辑器，也不提供 maintenance、Git delivery、semantic vector、registry 编辑、认证或远程托管。外部实例在 Web server 启动时不自动 reindex 或写入。

### 5.2 写路径——agent 沉淀

```text
owner 输入 → Capture 立即 append + fsync，返回稳定 ID
          → 不等待分类、维护、Git 或网络

Agent 维护 → 读取全部未消费 Capture
          → 自动更新 / 合并 Incubator Topic
          → 写明 origin、derived_from；独立推断写 claim block + claim_status
          → 不自动提升 canonical

topic 提升 → owner 明确指令或集中审阅确认
          → 新 Canonical Atom
          → check 守门

已有 atom 修改 / protected 变更 → proposal → owner merge / reject
```

### 5.3 Personal Profile 维护循环

```text
scan captures → 计算所有未被 applied run 消费的 Capture（包含 missed-run catch-up）
              → 生成幂等 changeset
              → apply：更新 incubator / 索引 / provenance
              → sensitive scan
              → commit（同一 run 不重复提交）
              → push（失败留在本地，下次只重试未完成阶段）
              → 简短通知
```

maintenance run 的状态与日志只存放在 `.codememory/`，不得写入 journal 正文。Capture 落盘成功不依赖后续任何阶段；整理、commit 或 push 失败都不能造成原始记录丢失或重复消费。

原有 canonical 维护循环继续保留：`check` 检查 stale / 断链 / schema，`orphans` 发现不可达 atom，`test` 验证黄金问题。

### 5.3.1 周期回顾

月度/年度回顾分为两层：

1. Core 按 Profile timezone 和显式 `monthly + YYYY-MM` / `yearly + YYYY` 冻结确定性 evidence bundle；只收录有效 Capture、期内 Topic/Claim revision、必要的期前 baseline、显式关系和当前可装配 canonical provenance。
2. Personal Memory Skill 在 bundle 上进行跨主题阅读、事实/综合/推断/不确定性区分，并可通过既有 maintenance changeset 更新 Incubator。

回顾默认是临时综合回答，不产生文件。只有 owner 明确要求保存时才在 `paths.reviews` 下写入每期最多一个 Markdown；它不是 canonical Atom，不进入 imports/build。周期回顾不会隐式运行 maintenance、Git delivery、semantic discovery 或模型 provider。

### 5.4 导入路径——原文、候选与 canonical 分离

```text
Markdown corpus → 登记 Source Artifacts（稳定 URI-derived ID + hash）
                → 每份文档生成一个轻量 anchor proposal
                → 默认：每个非空段落生成一个带精确 locator 的 derived proposal
                → 显式 LLM 模式：从带 paragraph ID 的原文提炼较少的 semantic proposals
                → review 选择需要 materialize 的候选
                → 写入 status: proposed 的 atom 文件
                → owner merge 后才进入 canonical graph
```

确定性 importer 只做可复现的结构转换，不声称已经完成语义提炼，也不自动发明 imports。可选 LLM proposer 必须由 owner 显式提供 gateway 配置和模型后才启用；它只提出候选与依赖建议，不能跳过 review / owner merge。Source 文本会发送到该显式配置的模型，但不启用 tools / Web，也不发送 gateway 配置内容。原文保持不变，anchor 与 derived 都通过 `source_refs` 回指 asset；`source_refs` 永不进入 imports DAG。

## 6. 写入纪律

| 等级 | 判据 | 路径 |
|---|---|---|
| 低风险 | 新增 atom（可声明自己的 imports），不修改任何已有文件 | 直写，写后 check |
| 高风险 | 修改已有 atom 的正文或 imports；或变更涉及 protected atom | proposal，owner merge 后生效 |

Personal Profile 对此作更严格覆盖：

| 操作 | 默认权限 |
|---|---|
| append Capture | 自动执行 |
| 新建、补充、聚类、合并 Incubator Topic | 自动执行，完整记录 provenance |
| Agent 新建 Canonical Atom | 必须由 owner 确认提升；默认 proposed |
| owner 明确要求“新建正式 idea” | 该指令视为确认，可直接创建 active atom并记录确认来源 |
| 修改已有 atom / imports、删除或修改 protected 内容 | proposal / owner 确认 |
| owner 集中审阅 incubator | 可批量提升、合并、删除 |

**protected 的语义**：标记"动它必须走 proposal"的 atom（核心原则、硬约束类记忆）。它是写入纪律的判据，由 owner 拍板设置，不与任何重要性评分挂钩。

**check 守门**：任何写入后运行 check；断链、循环、schema 违约即报，不得带病合入。

## 7. 成功标准

**产品侧：**

- 一个全新 agent 通过 search → build 重建某项目的关键上下文，并通过该入口的黄金问题测试；
- 高风险变更 100% 经过 proposal（可由 check 验证）；
- 任何重要结论可追溯：经 imports 到前提，经 asset 引用到原文，经 log 到变更历史。
- owner 可不填表单地追加记录；Capture 即使维护、commit 或 push 失败也不丢失；
- 大量日常输入只产生每日 journal 与月度 incubator，不按想法数量生成 Markdown 文件；
- Incubator 可长期自动演化并参与检索，而 Canonical Atom 的新增仍由 owner 确认；
- 可按时间、标签、主题和显式关系回看想法演化，Agent 推断不会伪装成 owner 原话；
- missed-run catch-up、重复维护、重复 commit 和 push 重试均幂等。

**工程侧：**

- 所有 adapter（CLI / MCP / REST / SDK）调用同一 core handler；
- MCP 与 Toolkit 共享同一 agent-tool catalog / dispatcher：普通实例只暴露 build、search、expand_source、create、propose；Personal Profile 只追加已定义的 capture/read/maintenance/review 扩展；
- agent 的 modification proposal 只能写 patch queue，不得用伪 proposal 直接修改 canonical Atom；Personal Profile 的 agent create 永远先落为 proposed；
- Operator UI 以 Build 为唯一装配主路径，分开显示 proposed Atom 与 modification patch 两条 owner review 队列，并只读呈现 golden questions；
- Personal Operator workspace 只对 allowlisted Personal dataset 出现；公开 payload 不含 root/private-local/Git/semantic/maintenance 私有状态，批量审阅复用同一 Core handler；
- prd / architecture / CLAUDE.md 三处术语一致；
- check 全绿是任何 merge 的前置条件。

### 7.1 Eval harness 产品信号

Eval harness 是 `test` 的显式 provider-backed runner，不改变 build 或 golden-question 的 Core 契约。每个带非空 `expect` 的问题在冻结输入上运行三条互相独立的答题路径：

1. **ContextPack**：入口经 canonical imports DAG 和指定 budget/depth 装配；
2. **full-memory**：当前 index 中所有可装配 Atom/Schema 的 summary + authored body，按 ID 稳定排序；
3. **no-memory**：不给答题模型任何 memory context。

三条路径使用同一 answer model、prompt 和解码参数；answer model 永远看不到 `expect`。judge 只看到 question、expect 和 candidate answer，不看到 arm 或 context。full-memory 不包含 frontmatter 中的 golden questions，避免标准答案泄漏。

首版把成功标准变成以下可审计数字：

- 三个 arm 各自的 eligible-question pass rate；
- ContextPack 相对 full-memory 的 pass-rate delta / retention；
- ContextPack 与 full-memory 相对 no-memory 的 uplift；
- ContextPack 相对 full-memory 的 context chars、估算 tokens 和实际 answer input-token savings；
- 每题 verdict、短理由、provider/model、usage 和 latency。

执行必须由 owner/CI 显式提供 provider config、answer model 与 judge model。默认命令、Core import、MCP、Agent tools 和 Web 均不触发 provider。报告只保留复核需要的 answer / expect / verdict 与安全调用 metadata；不保存 context、prompt、config 路径、credential、raw response 或 raw thinking。

## 8. 非目标

1. 语义向量检索作为装配机制（search 只做词法入口发现）；
2. 多人协作与权限系统；
3. 拟人记忆、遗忘、陪伴体验（相关探索在 `docs/reference/`）；
4. 把长文档塞进 atom body（那是 asset 的职责）；
5. LLM 直写高风险路径；
6. 图的分支管理（proposal 是状态，不是分支）。
7. 把 Capture 或 Incubator Topic 自动塞入 canonical build；
8. Phase 1 引入语义向量索引，或默认调用外部 embedding 服务；
9. 完整笔记编辑器、插件生态、每条记录强制原子化；
10. 自动删除或无痕改写 owner 原始 Capture；
11. 把 private GitHub remote 当作正文加密；Git 历史中的敏感内容不能因工作树删除而视为已清除。

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
| Personal Profile | 面向单一 owner 的低摩擦捕获与异步维护实例规范 |
| Capture | journal 中带稳定 ID 与独立内容 hash 的 append-only 原始记录 |
| Incubator Topic | 月度 incubator 文档中的段落级、可演化衍生主题，不进入 build |
| Canonical Atom | 经 owner 确认提升、可通过 imports DAG 装配的正式认识 |
| origin | 内容来源类别：human_explicit / agent_synthesis / agent_inference；混合来源 Topic 可为 mixed |
| claim | Topic 内带稳定 claim_id 的段落级独立主张；不单独创建 Markdown 文件 |
| claim_status | 具体 claim 或单一主张型 Atom 的认识状态：unassessed / supported / contested / refuted；不属于整个 Topic，不代替生命周期 status |
| maintenance run | 一次可恢复、可重试、幂等的整理—扫描—commit—push 批次 |
