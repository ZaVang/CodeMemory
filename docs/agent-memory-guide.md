# Agent Memory Guide — 记忆库贡献规范

> 你在向一个**代码式记忆库**提交变更。请像读一个仓库的 CONTRIBUTING.md 一样读本文。
> 概念定义见 `docs/prd.md`；本文只讲"怎么写"。

---

## 0. 概念 ↔ 当前命令对照

概念名是 PRD 语言；Agent 使用 root-bound tool，owner 的可信本地操作使用 CLI：

| 概念 | 当前命令 |
|---|---|
| build（装配） | `codememory build <id> [--depth required\|recommended\|full] [--budget N] [--format xml-markdown\|markdown\|plain-markdown\|json]`（主命令）；`resolve` / `context-pack` 是同一管线的兼容别名 |
| check（校验） | `codememory validate` |
| search（检索） | `codememory search --query <q> [--tags t1 t2]` |
| asset（登记/查看/展开） | `codememory source add <uri> [--id ID] [--summary "..."]` / `source list` / `source get <id>` / `source check` / `source expand <id> [--max-chars N]` |
| Agent 新增 atom | `create_memory` 一次提交完整 `id + summary + body + tags + imports`；普通 root 可选 active/proposed，Personal Profile 强制 proposed |
| Agent 修改 atom | `propose_memory` 只写 patch queue，不修改 target bytes（高风险，见第 6 节） |
| proposal（新增类） | `create_memory` 传 `propose: true`；owner 用 `codememory merge <id>` / `reject <id>` 处理 |
| proposal（修改类） | `propose_memory` 或可信 CLI `codememory propose <id> --reason "..." [--summary ...] [--body ...]` 入队；owner `merge <proposal_id>` / `reject <proposal_id>` |
| test（验证） | `codememory test <entry>` 导出题集+上下文 JSON；答完 `codememory test report <entry> --results <file>` |
| Agent 给已有 atom 绑定 asset | `propose_memory` 传 `source_ref`；owner merge 后经 canonical update 生效 |
| 批量导入存量材料 | agent 提炼范式见第 9 节；机械切分用 `compile-md` / `skeletonize` / `import` |

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

长文档、会议记录、设计稿、PDF、代码文件——**登记为 asset，不要塞进 atom body**。登记是可信 owner/operator 操作，不在标准 Agent tool surface：

```bash
codememory source add docs/rfc-001.md --id src/rfc-001-cache --summary "RFC-001: 缓存层设计"
```

然后写一个轻量 atom 做语义索引：summary 说清"它是什么、什么时候该读"。

artifact 已登记后，Agent 给已有 atom 增加结构化绑定也属于修改，必须提案：

```json
{
  "tool": "propose_memory",
  "input": {
    "id": "user/contexts/cache-layer",
    "reason": "绑定已登记的 RFC-001 source artifact",
    "source_ref": "src/rfc-001-cache"
  }
}
```

owner merge patch 后，同一 artifact 的重复绑定会被自动跳过。在 body 中顺带写明 asset id 与展开命令仍是好实践（agent 阅读时可直接行动）。

需要原文时按需 `source expand`，不要默认展开全文。

---

## 6. 直写还是提案（分级写入纪律）

| 你要做的事 | 等级 | 动作 |
|---|---|---|
| 新增 atom，不改任何已有文件（可声明自己的 imports） | 低风险 | `create_memory` 一次提交完整内容，写后 validate |
| 修改**已有** atom 的 body 或 imports | 高风险 | 走 proposal |
| 涉及 protected atom 的任何变更 | 高风险 | 走 proposal |

**新增类 proposal（已实装）**：对要新增的内容没把握、或内容涉及 protected 邻域时，调用 `create_memory` 并传 `propose: true`。产出的 atom 是 `status: proposed`——默认 search 不可见、build 不装配，owner 审阅后 `codememory merge <id>`（进入 canonical）或 `codememory reject <id>`（归档）。

**修改类 proposal（已实装）**：修改**已有** atom 的高风险变更**不要直接 update**。用 `codememory propose <id> --reason "..."` 把字段级 patch 入队（支持 --summary / --body / --import-* / --source-ref），目标 atom 不被触碰；owner 审阅后 `merge <proposal_id>`（经 update 应用，version++、change_log 留痕）或 `reject <proposal_id>`。

可信 owner CLI 的 `create` 仍是模板命令，owner 可以随后直接 `update`；这不是 Agent 写入路径。Agent 不模拟这个两步流程，必须调用 `create_memory` 完整创建。所有 Agent tool payload 都不包含 `root`，实例由 adapter 预先绑定。

**protected 的设置**：由 owner 拍板，agent 不自行创建 protected atom。当你认为某条记忆需要保护（核心原则、硬约束），向 owner 建议。

---

## 7. 完整场景示例

### 场景 A：记录一次架构决策（低风险，直写）

> 对话：「以后这个项目的文档主干只留 canonical，历史探索都进 reference/。」

判断：长期决策（三个月后仍约束行为）→ 记；新增 atom、依赖已有原则 → 直写。

```json
{
  "tool": "create_memory",
  "input": {
    "id": "user/decisions/2026-06-docs-canonical-only",
    "summary": "2026-06 起 docs/ 主干只留 canonical 文档，历史探索移入 docs/reference/",
    "body": "决策：docs/ 根目录只保留长期指导文档。理由：两代世界观共存导致漂移。",
    "tags": ["decision", "docs"],
    "import_required": ["user/principles/docs-first"],
    "propose": false
  }
}
```

owner/Automation 随后运行：

```bash
codememory validate
```

注意：Agent 的 `create_memory` 必须一次提供真实 summary/body；不能先创建 TODO 模板再直接改写。

### 场景 B：沉淀一个排障流程（低风险，直写）

> 对话：「这次 Windows CI 又是编码问题，把排查套路记下来。」

判断：可复用流程 → `user/processes/`；无前置依赖 → 直写，无 imports。

```json
{
  "tool": "create_memory",
  "input": {
    "id": "user/processes/windows-encoding-triage",
    "summary": "Windows 编码问题排查：先查 PowerShell 默认 UTF-16，再查 Python locale，最后查 git autocrlf",
    "body": "1. PowerShell Out-File 默认 UTF-16，写文件加 -Encoding utf8；2. 检查 PYTHONIOENCODING；3. 检查 .gitattributes 的 eol 设置。",
    "tags": ["process", "windows", "debugging"],
    "propose": false
  }
}
```

```bash
codememory validate
```

### 场景 C：登记一份设计文档（asset + 索引 atom）

> 对话：「这份 30 页的缓存层 RFC 以后会反复用到。」

判断：长文档 → asset，绝不塞进 atom body；另建轻量索引 atom。

owner 先登记 asset：

```bash
codememory source add docs/rfc-001.md --id src/rfc-001-cache --summary "RFC-001: 缓存层设计"
```

Agent 一次创建完整索引 atom；因为还需绑定 source_ref，先保持 proposed：

```json
{
  "tool": "create_memory",
  "input": {
    "id": "user/contexts/cache-layer",
    "summary": "缓存层上下文入口；动缓存实现前必读 RFC-001",
    "body": "原文见 asset src/rfc-001-cache（按需 expand）。核心结论：写穿透 + 5 分钟 TTL。",
    "tags": ["architecture", "cache"],
    "propose": true
  }
}
```

再用 `propose_memory` 提交 `source_ref: src/rfc-001-cache` patch。owner 先 merge patch、再 merge proposed Atom，最后运行 `codememory validate`。不要用 direct update 补绑定。

### 场景 D：修正一条已有记忆（高风险，走修改类 proposal）

> 对话：「上次记的'Python 固定 3.13'理由过时了；把结论改成升级前先核对 Windows wheel。」

判断：修改已有 decision atom → 高风险。Agent 只提交 patch，不等待确认后绕过队列：

```bash
codememory propose user/decisions/2026-06-pin-python-313 \
  --reason "3.14 Windows wheels 已可用，原固定版本理由过时" \
  --summary "Python 升级前先核对 tree-sitter 等关键依赖的 Windows wheels" \
  --body "版本不再永久固定为 3.13。每次升级前必须先验证关键原生依赖在 Windows 上有可用 wheel。"

codememory proposals
```

owner 审阅后执行 `codememory merge <proposal_id>` 或 `reject <proposal_id>`。`status` 不属于当前 modification patch 支持字段；归档等 status-only lifecycle 操作由 owner 直接处理，Agent 不执行，也不能用 direct update 绕过该限制。

---

## 8. 常见错误速查

| 错误 | 正确做法 |
|------|----------|
| 把多个事实塞一个 atom | 一个 atom 一个语义单元，像一个函数只做一件事 |
| 长文档塞进 atom body | 登记 asset，atom 只做语义索引 |
| 全部依赖标 required | 按"不读会不会误解"分级 |
| 用 imports 表达出处 | 出处写 asset 引用（body 中注明 asset id） |
| Agent 先 create TODO 再 update | 使用 `create_memory` 一次提交完整 summary/body/imports |
| 直接 update 已有 atom | 高风险变更走 `propose` 入队，owner `merge` 后生效 |
| Agent 用 owner CLI update 补字段 | 新增内容一次完整 create；已有内容走 proposal |
| 给记忆打重要性分 | intensity 已整体移除（参数不存在）；重要性由被依赖数表达，保护语义找 owner 标 protected |
| 写完不跑 validate | 任何写入后 `codememory validate` 守门 |

---

## 9. 导入工作流：agent 即 importer

存量文档、笔记、聊天记录的高质量导入靠 **agent 提炼**，不靠机械切分。机械路径（`compile-md` 登记 asset 并生成 anchor + paragraph-derived proposals、`import` 按段落切、`skeletonize` 骨架化）只适合结构本来就规整、内容本来就一段一条的材料；其余情况按本节流程走——你的价值是**判断与取舍**，不是搬运。

### 六步流程（每批材料）

**第 0 步 · 盘点分类**。每份材料三选一：

- 原文有长期参考价值（设计稿 / RFC / 规范）→ 走 asset 登记 + 提炼；
- 只有结论有价值（聊天记录、会议速记、草稿）→ 只提炼，不登记 asset；
- 过不了第 1 节的写入门槛两问 → 跳过，在审阅清单里注明跳过原因。

**第 1 步 · 登记 asset**（如适用，由 owner/operator 执行）：

```bash
codememory source add <path> --id src/<slug> --summary "一句话说明它是什么"
```

原文留在原地，不动、不删、不改。

**第 2 步 · 提炼 atoms**。通读材料，找出"可独立引用的语义单元"——事实、决策、约束、流程、原则。纪律：

- 每条过第 1 节的两问（三个月后还重要吗？丢了会导致错误决策吗？）——**宁缺毋滥**；
- 一个 atom 一个语义单元（第 8 节反模式）；
- 目录按第 2 节的种类表选，**直接进正确目录**（`user/facts/`、`user/decisions/`……），不要堆进 `user/imports/`；
- **一律用 `create_memory` 且 `propose: true`**：批量导入是典型的“没把握”场景；每条一次提交完整 summary、简短 body、tags 与 imports，全部落为 proposed 走审。

**第 3 步 · 声明关联**：

- imports：按第 4 节判据指向库里已有 atom 或**同批** atom；
- 出处：body 不抄原文，只写结论。若必须绑定结构化 `source_ref`，用 `propose_memory` 提交 patch，由 owner merge；需要批量原子化 provenance 时优先走 `compile-md`。

**第 4 步 · 批次校验**：`codememory validate`。

- `[ERROR]` 断链：当场修（通常是 imports 拼错 id）；
- 同批 proposed 互相引用**不产生告警**（实测）；若出现 `[STATUS-WARN]`，说明库里**已有的 active atom** 引用了你新导入的 proposed——属预期，owner merge 后消失，不要为了消警告而直写 active。

**第 5 步 · 交付审阅清单**。给 owner 一张表：每条 proposed 的 id、一句话 summary、出处 asset；并给出**建议的 merge 顺序——被依赖者先 merge**（build 会跳过 proposed 节点，依赖链需要自底向上激活）。owner 用 `codememory merge <id>` / `reject <id>` 逐条或批量处理。

**第 6 步 · 收尾**（owner merge 后）。用 `create_memory` 一次创建完整上下文入口 atom（`user/contexts/<主题>`，imports.required 指向核心条目）；没把握时仍设 `propose: true`。owner 可为它补充 2-3 个 `golden_questions`，然后：

```bash
codememory test user/contexts/<主题>     # 自答题集，验证导入质量
codememory test report user/contexts/<主题> --results results.json
```

### 导入反模式速查

| 错误 | 正确做法 |
|------|----------|
| 每段原文一条 atom | 那是 compile-md 的机械行为；agent 的价值是提炼与取舍 |
| 批量导入直写 active | `create_memory` 一律传 `propose: true`，owner 审后 merge |
| atom body 抄原文 | 原文在 asset；atom 只写结论 + source_ref |
| 全部塞进 user/imports/ | 按种类直接进正确目录，imports 目录是机械导入器的着陆区 |
| 乱序 merge | 被依赖者先 merge，否则入口 build 暂时缺节点 |
| 跳过第 6 步 | 没有入口和黄金问题的导入批次，三个月后没人找得到 |
