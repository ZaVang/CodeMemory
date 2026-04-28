# CodeMemory 与外部团队知识库方案的互操作

本文档说明 CodeMemory 与外部团队知识库方案（五层存储、五种知识类型、三级成熟度、16 阶段工作流）之间的关系、差异和适配方式。

---

## 一、核心差异定位

| 维度 | 外部方案 | CodeMemory |
|------|---------|------------|
| 目标场景 | 公司内团队项目知识沉淀 | 个人 Agent 记忆管理（companion/助手场景） |
| 核心问题 | "6 个月后换同事接手项目，知识不丢" | "3 小时对话中 Agent 保持因果连贯" |
| 验证方式 | 多人共识（consensus） | 自我一致性（coherence） |
| 加载方式 | 三级索引（图书馆检索模型） | DAG 编译（模块导入模型） |
| 冲突处理 | maintainer 裁决 | update + change_log 演化（想法变了） |

---

## 二、目录层级映射

外部方案的五层目录可直接映射到 CodeMemory 的目录约定：

| 外部方案 | CodeMemory | 场景 |
|---------|-----------|------|
| Layer 0-P 个人偏好 | `user/preferences/` | 纯本地，不共享 |
| Layer 0-T 团队约定 | `team/conventions/` | 团队级，Git 共享 |
| Layer 1 技术知识 | `tech/wiki/` | 跨项目共享 |
| Layer 2 业务知识 | `biz/{domain}/` | 按领域 |
| Layer 3 项目知识 | 项目级 `<root>/` | 随项目走 |

**适配方式：** 目录结构直接对应，不需要改任何代码。CodeMemory 的 DAG 不关心目录层级——只跟 `id` 和 `imports` 打交道。

---

## 三、知识类型映射

外部方案的五种知识类型（MECE 原则）与 CodeMemory 的语义分类：

| 外部方案类型 | CodeMemory semantic_type | 对应原语 |
|-------------|-------------------------|---------|
| model（实体定义） | `model` | atom |
| decision（技术选型） | `decision` | instance（依附 schemas/decision） |
| guideline（推荐/禁止） | `guideline` | atom 或 composite |
| pitfall（已知风险） | `pitfall` | atom |
| process（流程状态机） | `process` | atom 或 composite |

**适配方式：** CodeMemory 通过 tags 实现 semantic_type（`tags: ["decision", "architecture"]`），不新增 frontmatter 字段。`search --semantic-type decision` 按类型过滤，`resolve --focus pitfall` 按类型过滤节点输出。

---

## 四、成熟度映射

外部方案的三级成熟度与 CodeMemory 的 maturity 字段：

| 外部方案 | CodeMemory | 升级方式 |
|---------|-----------|---------|
| draft（新提取，单一来源） | draft | create 默认值 |
| verified（单项目验证） | verified | resolve ≥ 3 次自动升级 |
| proven（多项目验证） | proven | resolve ≥ 10 次 + dependents > 0 |

**差异：**

1. **验证主体不同** — 外部方案靠"多少人/多少项目验证"，CodeMemory 靠"多少次会话使用 + 被多少记忆引用"。后者适配个人场景（没有多人验证的条件）。

2. **衰减逻辑不同** — 外部方案用**时间驱动**（12 个月无引用 → 降级），CodeMemory 用**可达性驱动**（无引用 + 低 heat → 建议，不删）。CodeMemory 刻意不做自动降级——"12 个月没被引用"不代表过时，可能只是领域不常讨论。

3. **共同点** — 两者都要求 maturity 升级依赖使用证据（不是作者自评），且都有安全阀（外部方案的 draft 回滚 vs CodeMemory 的 decay 建议）。

---

## 五、工作流对比

外部方案的 16 阶段状态机工作流 vs CodeMemory 的认知循环：

| 外部方案阶段 | CodeMemory 对应 | 差异 |
|-------------|----------------|------|
| INIT：git pull 拉取最新知识 | overview 会话启动注入 | 同为"继承前人知识" |
| 执行中：按阶段按需查询 | resolve + focus | 同为"按需加载" |
| ARCHIVE：@archiverAgent 自动提取 | snapshot 手动持久化 | **核心差异**：自动 vs 手动 |

**差异分析：**
- 外部方案用专门 Agent 自动从产物中提取知识——覆盖率高，但可能存噪声
- CodeMemory 的 snapshot 靠 Agent 主动判断——质量高，但可能遗漏
- 互补方式：自动提取做初筛（所有产物先 draft），手动 snapshot 做精选（高 intensity）

---

## 六、可直接借鉴的设计

以下是 CodeMemory 从外部方案中吸收的设计，均已在 Phase 4 实现：

| 设计 | 外部方案 | CodeMemory 实现 |
|------|---------|---------------|
| 全局审计日志 | log.md 只追加不修改 | `.codememory/log.md` + `codememory log` |
| 成熟度自动升级 | draft→verified→proven | resolve 自动升降，LLM 零负担 |
| 溯源证据链 | evidence.contributors[] | evidence 字段（contributors + sessions + verified_in） |
| 按类型查询 | 五类知识 MECE | `--semantic-type` + `--focus` |
| 冷启动导入 | /flow-import 管道 | `import --stdin --extract` |

---

## 七、有意不采纳的设计

| 设计 | 原因 |
|------|------|
| 多人角色系统（maintainer/contributor/reader） | 个人 Agent 场景无多人协作需求 |
| 自动时间衰减（12 个月无引用自动降级） | 冷门但正确的知识不该降级；CodeMemory 用可达性判断 |
| 内容矛盾自动检测 + maintainer 裁决 | 个人场景的矛盾是"想法变了"不是"两人冲突"；update + change_log 已覆盖 |
| 16 阶段状态机工作流 | CodeMemory 是记忆引擎，不做工作流编排（那是 harnesslib 的职责） |
| 三级索引（全景目录 → 分类清单 → 完整条目） | CodeMemory 用 overview（扫视）+ resolve（编译因果闭包）替代；resolve 是 DAG 编译不是搜索 |
| Git 作为共识机制载体 | 个人场景不需要区块链式共识 |

---

## 八、总结

外部方案解决的是**"知识在团队中如何被沉淀、验证、共享"**——这是治理层问题。CodeMemory 解决的是**"知识如何被 AI 正确加载、保持因果完整"**——这是引擎层问题。

两者不是竞争关系。外部方案的五层目录和语义分类可以直接在 CodeMemory 上运行——目录结构对应，semantic_type 通过 tags 实现。反过来，CodeMemory 的 DAG 编译和认知接口是对方没有的能力——它们的 resolve 本质仍是"搜索"，无法构建因果闭包。

一个完整的企业级方案应该是：**CodeMemory 的 DAG 编译引擎 + 外部方案的五层治理模型 + 16 阶段工作流中的自动 ARCHIVE 提取。**
