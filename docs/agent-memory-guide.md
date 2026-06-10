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
