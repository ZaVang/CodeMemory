# Memory-as-Code 文档重建 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按已批准的设计 spec（`docs/superpowers/specs/2026-06-10-memory-as-code-prd-rebuild-design.md`）重写 `docs/prd.md` 与 `docs/agent-memory-guide.md`，同步 `.claude/CLAUDE.md` 术语，并给 `docs/architecture.md` / `docs/plan/FUTURE.md` 加过渡提示。**不动任何代码。**

**Architecture:** 纯文档变更。三份文档的完整最终文本已内嵌在本计划中（执行者直接写入，不需要再创作）；每个任务以 grep 验证 + git commit 收尾。文档中引用的所有 CLI 命令均已对照 `src/codememory/cli.py` 核实为真实存在的命令。

**Tech Stack:** Markdown、git、grep、pytest（仅作"未动代码"的回归证明）。

**重要背景（执行者必读）：**
- 设计 spec 是本计划的唯一上游：`docs/superpowers/specs/2026-06-10-memory-as-code-prd-rebuild-design.md`。
- 当前 CLI 事实（已核实，文档内容依赖这些事实，不得"修正"成想象中的命令）：
  - 装配命令是 `codememory resolve <id>` 和 `codememory context-pack <id>`（带连字符）；尚无 `build` 命令。
  - `create` 不支持声明 imports / summary / body——生成的模板 summary 是 `"TODO: fill in summary"`；真实流程是 create → update 两步。
  - `update --status` 的合法值是 `active|archived|superseded|draft`，**没有 `proposed`**（proposal 未实装）。
  - `source_refs` 字段目前没有 CLI 写入路径（仅 compiler/skeletonize 生成）。
  - `protected` 由 `create --intensity 8` 间接触发，没有独立 flag。
  - `focus` / `overview` / `wander` / `snapshot` 命令存在（概念已砍，命令待收敛）。
- 范围外（明确不做）：修改任何 `src/`、`tests/`、`backend/`、`frontend/` 代码；重写 `docs/architecture.md` 正文（只加 banner）；更新 `.claude/rules/python.md`（它有陈旧的"16 个模块"表述，留给架构阶段一并处理）。

---

### Task 1: 重写 docs/prd.md

**Files:**
- Modify: `docs/prd.md`（整文件替换）

- [ ] **Step 1: 用以下完整内容覆盖 `docs/prd.md`**

````markdown
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
````

- [ ] **Step 2: 验证结构与术语隔离**

```bash
grep -n "^## " docs/prd.md
```
预期输出 10 行：8 个正文章节（1-8）+ 附录 A + 附录 B。

```bash
grep -n "intensity" docs/prd.md
```
预期：仅附录 A 的"intensity 1-10"一行。

```bash
grep -n "ContextPack\|Source Artifact" docs/prd.md
```
预期：仅 header 的"前身"行 + 附录 A 表格行（共 4 处左右，全部位于这两个位置）。

```bash
grep -n "Work Layer\|Companion\|wander\|认知操作" docs/prd.md
```
预期：仅附录 A 表格行。

- [ ] **Step 3: Commit**

```bash
git add docs/prd.md
git commit -m "docs: rebuild prd.md around memory-as-code axiom"
```

---

### Task 2: 重写 docs/agent-memory-guide.md

**Files:**
- Modify: `docs/agent-memory-guide.md`（整文件替换）

- [ ] **Step 1: 用以下完整内容覆盖 `docs/agent-memory-guide.md`**

````markdown
# Agent Memory Guide — 记忆库贡献规范

> 你在向一个**代码式记忆库**提交变更。请像读一个仓库的 CONTRIBUTING.md 一样读本文。
> 概念定义见 `docs/prd.md`；本文只讲"怎么写"。

---

## 0. 概念 ↔ 当前命令对照

概念名是 PRD 语言；命令名是当前 CLI 现实（动词收敛前以本表为准）：

| 概念 | 当前命令 |
|---|---|
| build（装配） | `codememory resolve <id> [--depth required\|recommended\|full] [--budget N]`；结构化输出用 `codememory context-pack <id> [--format json\|markdown\|xml-markdown]` |
| check（校验） | `codememory validate` |
| search（检索） | `codememory search --query <q> [--tags t1 t2]` |
| asset（登记/查看/展开） | `codememory source add <uri> [--id ID] [--summary "..."]` / `source list` / `source get <id>` / `source check` / `source expand <id> [--max-chars N]` |
| 新增 atom | `codememory create --id <id> [--schema s] [--tags "a,b"]`，然后立即 `update` 填入真实内容（见第 7 节） |
| 修改 atom | `codememory update <id> --change-note "..."`（高风险，见第 6 节） |
| proposal | 未实装；过渡做法见第 6 节 |

---

## 1. 写入门槛：什么值得记

两个问题，过不了就不要写：

1. **三个月后还重要吗？** 一次性查询结果、临时待办——不记。
2. **丢了会导致错误决策吗？** 会——必须记，且把"为什么"一起记下来。

代码类比：不是每行调试 print 都值得提交；值得提交的是会被再次调用的函数。

---

## 2. 记成什么：目录与 schema

id 的第一段就是目录。**目录区分"种类"，tags 区分"主题"**：

| 目录 | 用途 | 示例 ID |
|------|------|---------|
| `user/facts/` | 外部事实、背景知识 | `user/facts/vite-proxy-behavior` |
| `user/observations/` | 观察到的现象（当时未必知道原因） | `user/observations/ci-flaky-on-windows` |
| `user/preferences/` | 偏好、习惯、个人约束 | `user/preferences/no-new-deps` |
| `user/decisions/` | 具体决策（适用 `schemas/decision` 时带 `--schema`） | `user/decisions/2026-06-pin-python-313` |
| `user/principles/` | 长期原则、判断框架 | `user/principles/docs-first` |
| `user/processes/` | 流程、检查清单、排障步骤 | `user/processes/release-checklist` |
| `user/contexts/` | 给 agent 的上下文入口 | `user/contexts/codememory-dev` |
| `user/snapshots/` | snapshot 固化的推理链 | `user/snapshots/2026-06-10-缓存层分析` |
| `api/` | API 文档等外部结构化知识 | `api/quantexpr/sharpe` |
| `schemas/` | 结构契约（仅 schema 类型） | `schemas/decision` |

规则：

1. 不确定种类时默认 `user/facts/`；
2. 不要在目录里按主题建子文件夹——主题交叉用 tags 表达；
3. schema 只使用已有的，agent 不自行创建 schema。

---

## 3. summary：签名 + docstring

build 超预算时你的 atom 会被裁剪到只剩 summary——所以 summary 必须**独立可读、包含关键结论**。

好例子：

- `"2026-06 决定 Python 固定 3.13：tree-sitter 轮子在 3.14 缺 Windows 版"`
- `"Windows 编码问题排查：先查 PowerShell UTF-16，再查 locale，最后查 autocrlf"`

坏例子：

- `"TODO: fill in summary"`——这是 create 模板的占位符，留着它等于提交了空函数
- `"关于 Python 版本的一些讨论"`——无结论
- `"排障笔记"`——无信息量

---

## 4. imports：依赖判据

判断标准不是"相关吗"，而是"**不先读它，能正确理解我吗**"。

- **required**：不读必误解。决策 ← 它依据的约束；上下文入口 ← 核心组成记忆。
- **recommended**：读了更好懂，不读不误解。决策 ← 背景分析。
- **related**：同主题但无理解依赖。同领域的另一次讨论。

反模式：

- 全标 required（= 全没标）；
- 用 imports 表达"出处"——出处是 asset 引用的职责，不是依赖。

---

## 5. asset：长材料的正确姿势

长文档、会议记录、设计稿、PDF、代码文件——**登记为 asset，不要塞进 atom body**。

```bash
codememory source add docs/rfc-001.md --id src/rfc-001-cache --summary "RFC-001: 缓存层设计"
```

然后写一个轻量 atom 做语义索引：summary 说清"它是什么、什么时候该读"。

过渡限制：`source_refs` 字段目前没有 CLI 写入路径，请在 atom 的 body 中明确写出 asset id（如"原文见 asset `src/rfc-001-cache`，用 `codememory source expand src/rfc-001-cache` 展开"）。CLI 支持落地后本节将更新。

需要原文时按需 `source expand`，不要默认展开全文。

---

## 6. 直写还是提案（分级写入纪律）

| 你要做的事 | 等级 | 动作 |
|---|---|---|
| 新增 atom，不改任何已有文件（可声明自己的 imports） | 低风险 | 直接 create + update 填内容，写后 validate |
| 修改**已有** atom 的 body 或 imports | 高风险 | 走 proposal |
| 涉及 protected atom 的任何变更 | 高风险 | 走 proposal |

**proposal 的过渡做法**（`status: proposed` 实装前）：高风险变更**不要直接 update**。在会话中向 owner 说明：要改哪个 atom、改成什么、为什么；获得明确同意后再执行 update，并在 `--change-note` 里写清理由。proposal 机制落地后，本节将更新为 propose 命令用法。

**protected 的设置**：由 owner 拍板，agent 不自行创建 protected atom。当你认为某条记忆需要保护（核心原则、硬约束），向 owner 建议。

---

## 7. 完整场景示例

### 场景 A：记录一次架构决策（低风险，直写）

> 对话：「以后这个项目的文档主干只留 canonical，历史探索都进 reference/。」

判断：长期决策（三个月后仍约束行为）→ 记；新增 atom、依赖已有原则 → 直写。

```bash
codememory create --id user/decisions/2026-06-docs-canonical-only \
  --schema schemas/decision --tags "decision,docs"

codememory update user/decisions/2026-06-docs-canonical-only \
  --change-note "初始内容：记录文档主干决策" \
  --summary "2026-06 起 docs/ 主干只留 canonical 文档，历史探索移入 docs/reference/" \
  --body "决策：docs/ 根目录只保留长期指导文档。理由：两代世界观共存导致漂移。" \
  --import-required user/principles/docs-first

codememory validate
```

注意：create 只生成模板（summary 是 TODO 占位符），**必须立即用 update 填入真实内容**。

### 场景 B：沉淀一个排障流程（低风险，直写）

> 对话：「这次 Windows CI 又是编码问题，把排查套路记下来。」

判断：可复用流程 → `user/processes/`；无前置依赖 → 直写，无 imports。

```bash
codememory create --id user/processes/windows-encoding-triage --tags "process,windows,debugging"

codememory update user/processes/windows-encoding-triage \
  --change-note "初始内容：Windows 编码排查流程" \
  --summary "Windows 编码问题排查：先查 PowerShell 默认 UTF-16，再查 Python locale，最后查 git autocrlf" \
  --body "1. PowerShell Out-File 默认 UTF-16，写文件加 -Encoding utf8；2. 检查 PYTHONIOENCODING；3. 检查 .gitattributes 的 eol 设置。"

codememory validate
```

### 场景 C：登记一份设计文档（asset + 索引 atom）

> 对话：「这份 30 页的缓存层 RFC 以后会反复用到。」

判断：长文档 → asset，绝不塞进 atom body；另建轻量索引 atom。

```bash
codememory source add docs/rfc-001.md --id src/rfc-001-cache --summary "RFC-001: 缓存层设计"

codememory create --id user/contexts/cache-layer --tags "architecture,cache"

codememory update user/contexts/cache-layer \
  --change-note "初始内容：缓存层上下文入口" \
  --summary "缓存层上下文入口；动缓存实现前必读 RFC-001" \
  --body "原文见 asset \`src/rfc-001-cache\`（codememory source expand src/rfc-001-cache）。核心结论：写穿透 + 5 分钟 TTL。"

codememory validate
```

### 场景 D：修正一条已有记忆（高风险，走 proposal 过渡做法）

> 对话：「上次记的'Python 固定 3.13'，现在 3.14 轮子齐了，可以解除。」

判断：修改已有 decision atom → 高风险。先向 owner 说明变更与理由，**获得明确同意后**：

```bash
codememory update user/decisions/2026-06-pin-python-313 \
  --change-note "3.14 Windows 轮子已齐，解除版本钉死" \
  --status archived

codememory validate
```

---

## 8. 常见错误速查

| 错误 | 正确做法 |
|------|----------|
| 把多个事实塞一个 atom | 一个 atom 一个语义单元，像一个函数只做一件事 |
| 长文档塞进 atom body | 登记 asset，atom 只做语义索引 |
| 全部依赖标 required | 按"不读会不会误解"分级 |
| 用 imports 表达出处 | 出处写 asset 引用（body 中注明 asset id） |
| create 后不 update，留着 TODO summary | create 只是模板，必须立即 update 填真实 summary/body |
| 未经 owner 同意 update 已有 atom | 高风险变更先说明、再获同意（proposal 过渡做法） |
| update 不写 change-note | `--change-note` 必填，它是 log 的原料 |
| 给记忆打重要性分（`--intensity`） | 概念已废除，不要传该参数；重要性由被依赖数表达，保护语义找 owner 标 protected |
| 写完不跑 validate | 任何写入后 `codememory validate` 守门 |
````

- [ ] **Step 2: 验证术语与命令真实性**

```bash
grep -n "proposed\|propose" docs/agent-memory-guide.md
```
预期：仅出现在第 0 节对照表"未实装"行与第 6 节过渡做法段。

```bash
grep -n "intensity" docs/agent-memory-guide.md
```
预期：仅第 8 节"给记忆打重要性分"一行。

```bash
grep -n "codememory build\|codememory propose\|codememory test\|codememory check " docs/agent-memory-guide.md
```
预期：无匹配（guide 中所有命令必须真实存在）。

- [ ] **Step 3: Commit**

```bash
git add docs/agent-memory-guide.md
git commit -m "docs: rewrite agent-memory-guide as repo contribution guide"
```

---

### Task 3: 同步 .claude/CLAUDE.md

**Files:**
- Modify: `.claude/CLAUDE.md`（整文件替换）

- [ ] **Step 1: 用以下完整内容覆盖 `.claude/CLAUDE.md`**

````markdown
# CodeMemory — memory as code

> **公理**：记忆按代码的方式组织——原子化、显式依赖、按需装配。一个记忆库就是一个仓库，agent 是它的运行时。

概念模型与产品边界见 `docs/prd.md`（canonical）；agent 写记忆的规范见 `docs/agent-memory-guide.md`；本文件是本仓库开发者（含 agent）的工程速查。

## 文件架构

```
CodeMemory/
├── src/
│   ├── harnesslib/              # 通用 Agent 编排（跨项目复用，上游维护）
│   ├── llm_gateway/             # 多 provider LLM 接入（跨项目复用，上游维护）
│   └── codememory/              # 记忆管理核心
│       ├── __init__.py          # Public API
│       ├── core.py              # frontmatter 解析, body hash, logging 配置
│       ├── models.py            # Pydantic v2 数据模型
│       ├── handlers.py          # 统一命令处理（cli + tools + REST 共享）
│       ├── index.py             # Index 加载/保存/reindex
│       ├── resolve.py           # DAG + 拓扑排序 + token 裁剪（build 的底层）
│       ├── context_pack.py      # 结构化装配产物（build 的结构化输出）
│       ├── sources.py           # asset 登记/校验/展开（CLI 命令组 source）
│       ├── validate.py          # check：循环/断链/schema/stale
│       ├── create.py            # atom 模板生成
│       ├── update.py            # 版本递增 + change_log
│       ├── search.py            # 入口检索
│       ├── orphans.py           # 不可达 atom 发现
│       ├── changelog.py         # 单条记忆变更历史
│       ├── log.py               # 全局审计日志
│       ├── diff.py              # 自上次快照以来的变更
│       ├── suggest_deps.py      # 依赖推断辅助
│       ├── transient.py         # 会话级推理链（REPL 草稿）
│       ├── snapshot.py          # 推理链持久化
│       ├── import_cmd.py        # 冷启动文本导入
│       ├── skeletonize/         # Markdown/代码骨架化导入
│       ├── compiler/            # importer：corpus → 提案 → review → materialize
│       ├── integrations.py      # OpenAI/Anthropic/Gemini toolkit 适配
│       ├── mcp_server.py        # MCP adapter
│       ├── cli.py               # 薄 argparse 壳
│       └── tools.py             # harnesslib Sandbox 工具注册
├── backend/                     # REST adapter（FastAPI）
├── frontend/                    # Operator UI adapter（Vite）
├── bin/                         # codememory CLI wrapper / dev 一键启动
├── examples/                    # 示例记忆库数据（独立于框架）
├── docs/                        # canonical 文档 + plan/ + reference/
├── tests/
└── .claude/
```

## 核心概念速览

三组 11 概念（完整定义见 `docs/prd.md` 第 4 章）：

- **静态结构**：repo（记忆库）、atom（记忆单元）、imports（依赖）、schema（结构契约）、asset（资产，不进依赖图）
- **动态操作**：build（装配）、check（校验）、search（入口检索）、test（黄金问题验证，未实现）
- **变更管理**：proposal（提案，未实现）、log（审计日志）

概念 ↔ 当前 CLI 对照：build = `resolve` / `context-pack`（待收敛）；check = `validate`；asset = `source` 命令组；proposal 未实装（过渡做法见 guide 第 6 节）。

## 关键设计决策

- 装配是 DAG 依赖解析 + 预算裁剪，不是向量检索；search 只做入口发现，不参与装配。
- asset（原始材料）不进依赖图；atom 不装长文档。
- 分级写入纪律：新增 atom 直写；修改已有 atom 或涉及 protected 走 proposal（实装前：会话内征得 owner 同意）。
- 遗忘是路径不可达问题，不是删除问题。系统只建议，不自动删除。
- 框架（`src/codememory/`）与数据（`CODEMEMORY_ROOT` 指向的记忆库）物理分离。
- reindex 自动行为（实现细节，不属于概念模型）：`summary_hash` 未变且 `access_count >= 2` → `cache_stable=true`；`ephemeral` 且 `access_count==0` → 自动归档。frontmatter 手动声明优先于自动推断。
- **功能筛选标准**：它在代码世界里的对应物是什么？映射得出来的可以做；映射不出来的拒绝或放 `docs/reference/`。

## 硬约束（不可违反）

### 1. Agent 视角：只用 Bash

**所有 Agent 可用的记忆操作必须通过 bash 命令完成。** Agent 不调用 Python API，不 import codememory，不直接读写记忆库的 .md 文件。

```bash
codememory search --query "缓存"          # 找入口
codememory resolve user/contexts/cache-layer --budget 2000   # 装配
codememory source expand src/rfc-001-cache --max-chars 2000  # 展开 asset
codememory validate                        # 校验
```

底层实现可用 Python（DAG、拓扑排序等），但 Agent 视角下只有 bash 子命令。

### 2. Python 数据模型：Pydantic v2

**所有 Python schema 类、配置模型、数据传递对象必须使用 Pydantic v2 实现。**

```python
from pydantic import BaseModel, Field

class MemoryEntry(BaseModel):
    type: str = Field(description="atom | schema")
    id: str
    summary: str

data = entry.model_dump(mode="json")
```

禁止事项：

- 禁止 Pydantic v1 API（`.dict()`, `class Config`, `schema()`）
- 禁止裸 `dict` 作为模块间 API 边界
- 禁止 `Optional[T]` 不设显式 default

## 代码规范

### 技术栈

- Python 3.13+，核心依赖：`pyyaml`、`pydantic>=2.0`；可选依赖 `tree-sitter`（`pip install codememory[code]`）
- codememory 自身不依赖 harnesslib 或 llm_gateway（只在 tools.py / integrations.py 适配）
- token 估算用 `len(text)` 近似

### 编码约定

- 所有公共函数类型注解覆盖
- 系统日志走 `logging`（WARNING+），用户可见正文走 `print()`（stdout）
- `--verbose` / `--quiet` 全局控制日志级别
- frontmatter 修改不触发 stale（基于 body hash）
- 命令处理委托给 `handlers.py`，cli.py 和 tools.py 只做薄壳

### 修改原则

- 最小变更：只改与任务直接相关的代码
- 不引入新依赖：除非有充分理由并在 plan 中说明
- 不碰 `src/harnesslib/` 和 `src/llm_gateway/` 内部实现（上游维护）
- 先验证再提交：改代码后运行 `validate` + `resolve` 确认

## CLI 命令速查

```bash
# 读路径
codememory search [--query q] [--tags t1 t2] [--type atom|schema] [--status s]
codememory resolve <id> [--depth required|recommended|full] [--budget N]
codememory context-pack <id> [--format xml-markdown|markdown|json] [--budget N] [--task-goal "..."]
codememory source expand <id> [--start N] [--end N] [--max-chars N]

# 写路径（纪律见 docs/agent-memory-guide.md 第 6 节）
codememory create --id <id> [--type atom|schema] [--schema s] [--tags "a,b"] [--dry-run]
codememory update <id> --change-note "..." [--summary "..."] [--body "..."] [--status s] [--import-required ...]
codememory source add <uri> [--id ID] [--kind markdown|code|text|pdf|url|external] [--summary "..."]

# 校验与维护
codememory reindex
codememory validate [-v|-q]
codememory orphans [--type t]
codememory changelog <id>
codememory log [--limit N]
codememory diff [--since "2 days ago"]
codememory suggest-deps <id> [--min-score N]
codememory source list | source get <id> | source check [id]

# 迁移（importer）
codememory import --file notes.txt --extract preferences
codememory skeletonize <file_or_dir> [--min-intensity N] [--dry-run] [--tags "a,b"]
codememory compile-md <corpus> [--review-id ID] [--namespace user/imports]
codememory materialize-review <review_id> [--accept-all]

# 兼容命令（概念已废除，命令待收敛，新用法勿依赖）
codememory focus / overview / wander / snapshot
```

## 测试规范

- 单元测试：`PYTHONPATH=src python -m pytest tests/unit/ -v`
- 集成测试：`PYTHONPATH=src python tests/integration_test.py`
- 手工验证：`validate` → `resolve` → check output
- 边界：循环依赖、断链、空记忆、超大/零预算
- 验证命令：
  ```bash
  codememory reindex && codememory validate
  codememory resolve user/investment/context --budget 500
  codememory skeletonize examples/ --dry-run
  ```

## 禁止事项

- 禁止 Agent 绕过 bash CLI 直接调用 Python API 或 import codememory
- 禁止在 Agent 工具定义中使用 Python 函数签名
- 禁止 new 第三方依赖而不在 plan 中说明理由
- 禁止修改 `src/harnesslib/` 或 `src/llm_gateway/` 内部逻辑
- 禁止引入在代码世界找不到对应物的新概念（先过 `docs/prd.md` 第 1 章的筛选标准）

## 开发环境

### 端口

| 服务 | 默认端口 | 启动命令 | 备注 |
|------|---------|---------|------|
| Backend (FastAPI) | 8000 | `python backend/server.py` | `--root` 参数或 `CODEMEMORY_ROOT` 指定记忆库 |
| Frontend (Vite) | 5300 | `cd frontend && npm run dev` | 端口被占用自动递增；proxy 固定指向 8000 |
| 一键启动 | — | `./bin/dev` | Backend + Frontend，Ctrl+C 停止 |

实际端口以启动时终端输出为准。验收脚本不应硬编码端口号。
````

- [ ] **Step 2: 验证硬约束保留与旧术语清除**

```bash
grep -n "Pydantic v2\|只用 Bash" .claude/CLAUDE.md
```
预期：两条硬约束标题都在。

```bash
grep -n "Layer 0\|触景生情\|认知接口\|记忆原子化协议\|instance\|composite" .claude/CLAUDE.md
```
预期：无匹配。

```bash
grep -n "wander" .claude/CLAUDE.md
```
预期：仅"兼容命令"一行。

```bash
grep -n "sources.py\|context_pack.py\|mcp_server.py\|compiler/" .claude/CLAUDE.md
```
预期：文件架构树中各出现一次（修复旧版文件清单缺失）。

- [ ] **Step 3: Commit**

```bash
git add .claude/CLAUDE.md
git commit -m "docs: sync CLAUDE.md to memory-as-code terminology"
```

---

### Task 4: 过渡 banner + 跨文档一致性 + 回归证明

**Files:**
- Modify: `docs/architecture.md`（仅在标题块后插入 banner）
- Modify: `docs/plan/FUTURE.md`（仅在标题块后插入注记）

- [ ] **Step 1: 在 `docs/architecture.md` 的 `# CodeMemory Architecture` 标题与原 blockquote 之间插入**

```markdown
> **状态提示（2026-06-10）**：PRD 已按 memory-as-code 公理重建（见 `docs/prd.md` 与
> `docs/superpowers/specs/2026-06-10-memory-as-code-prd-rebuild-design.md`）。
> 本文档尚未随之更新——术语冲突处以新 prd.md 为准；架构重建是下一阶段工作。
```

- [ ] **Step 2: 在 `docs/plan/FUTURE.md` 的标题块后插入**

```markdown
> **注（2026-06-10）**：以下 roadmap 优先级早于 memory-as-code PRD 重建。
> 选择下一个 sprint 前，按新 `docs/prd.md` 重新推导优先级（候选：proposal 状态、
> search 词法排序、build 动词收敛、test 最小实现）。
```

- [ ] **Step 3: 跨文档术语一致性检查**

```bash
grep -c "asset" docs/prd.md docs/agent-memory-guide.md .claude/CLAUDE.md
```
预期：三个文件计数均 > 0（概念名统一为 asset）。

```bash
grep -n "状态提示\|memory-as-code" docs/architecture.md docs/plan/FUTURE.md
```
预期：两个文件各命中 banner 行。

- [ ] **Step 4: 回归证明（未动代码）**

```bash
git diff --stat HEAD~3 -- src/ tests/ backend/ frontend/
```
预期：空输出（三次提交均未触碰代码）。

```bash
PYTHONPATH=src python -m pytest tests/unit -q
```
预期：全部通过（与重建前一致）。

- [ ] **Step 5: Commit**

```bash
git add docs/architecture.md docs/plan/FUTURE.md
git commit -m "docs: mark architecture and roadmap as pending memory-as-code rebuild"
```

---

## 计划自检记录

- **Spec 覆盖**：spec §3 公理（prd 第 1 章）、§4 概念模型含实现状态（prd 第 4 章）、§5 命名决策（prd 4.2/4.3 标注 + guide §0 对照表）、§6 核心循环（prd 第 5 章）、§7 对照表（prd 附录 A）、§8 大纲（prd 全文）、§9 大纲（guide 全文，9 节）、§10 成功标准（prd 第 7 章）、§11 非目标（prd 第 8 章）、§12 范围边界（CLAUDE.md 工程部分原样保留；不动代码；Task 4 回归证明）、§13 风险缓解（实现状态标注 + FUTURE.md 注记 + examples 不删除）。
- **命令真实性**：guide 与 CLAUDE.md 中所有命令均对照 `cli.py` 核实；不存在 `codememory build/propose/test` 的用法指示。
- **类型一致性**：三份文档使用同一组概念名（atom/asset/build/check/search/test/proposal/log/protected/owner）。
