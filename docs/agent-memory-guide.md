# Agent Memory Guide — 记忆操作决策树

在对话中自主创建和维护记忆时，按以下决策树选择正确的参数和依赖强度。

---

## 原语选择规则

CodeMemory 有两种记忆类型：

### atom — 通用记忆

**所有非模板记忆都是 atom。** 角色通过 `imports`、`schema`、`tags`、目录来表达，不靠 type 字段区分。

**何时使用：** 任何需要记住的知识、偏好、决策、事件、事实、上下文包——全部用 atom。

- 用户的偏好或习惯："用户偏好长期持有"
- 一个外部知识点："VIX 指数是恐慌指数"
- 一个约束条件："不使用杠杆"
- 一次具体的买入/卖出决策（有 schema 时带上 `--schema` 参数）
- 将多个关联记忆打包的上下文入口（用 `imports` 引用被包含的记忆）

**有 schema 的 atom：** 当一个记忆需要依附某个结构模板（如 `schemas/decision`），使用 `--schema` 参数声明。这和旧版的 `instance` 概念对应，但现在类型统一为 atom。

```
codememory create --id user/investment/new-decision --schema schemas/decision --tags "investment,decision"
```

**有 imports 的 atom：** 当一个记忆需要引用其他记忆作为依赖（如上下文包引用其组成部分），使用 `--import-*` 参数声明。这和旧版的 `composite` 概念对应，但现在类型统一为 atom。

### schema — 元模板

**何时使用：** 定义某类记忆的结构。schema 本身不是记忆数据，而是记忆的"类型定义"。

- `schemas/decision`：定义一次决策需要记录哪些字段（日期、标的、金额、理由、结果）
- `schemas/meeting`：定义一次会议记录的结构

**注意：** schema 只由系统或高级用户创建，Agent 通常不自行创建 schema，而是使用已有的。

---

## 目录约定

`id` 的第一段就是目录。创建 atom 时，按以下约定选择目录：

| 目录 | 用途 | 示例 ID |
|------|------|---------|
| `user/facts/` | 外部事实、背景知识（不因用户而变） | `user/facts/nvidia-earnings` |
| `user/observations/` | 观察到的现象、事件（当时可能不知道原因） | `user/observations/soxl-drop-march` |
| `user/preferences/` | 偏好、约束、习惯（关于用户的） | `user/preferences/no-leverage` |
| `user/decisions/` | 具体的决策/行动（有 schema 时带上 `--schema`） | `user/decisions/february-buy` |
| `user/feelings/` | 情绪状态、心理觉察（陪伴模式） | `user/feelings/burnout-april` |
| `user/people/` | 用户生活中的重要人物（陪伴模式） | `user/people/best-friend-li` |
| `user/beliefs/` | 价值观、人生观、投资主线判断 | `user/beliefs/semiconductor-thesis` |
| `user/moments/` | 具体的生活事件、经历（陪伴模式） | `user/moments/rainy-sunday` |
| `user/snapshots/` | snapshot 命令固化的推理链 | `user/snapshots/2026-04-28-止盈分析` |
| `api/` | API 文档等外部结构化知识 | `api/quantexpr/sharpe` |
| `schemas/` | 模板定义（仅 schema 类型） | `schemas/decision` |

**规则：**
1. **目录区分"种类"** — 这是什么东西（事实？观察？偏好？决策？）
2. **tags 区分"主题"** — 这跟什么有关（`["semiconductor"]`、`["investment"]`）
3. **不要在目录里按主题再分子文件夹** — 一个 fact 可能同时涉及半导体和市场，放 `user/facts/semiconductor/` 还是 `user/facts/market/`？tags 天然支持交叉，目录不支持
4. **不确定时默认 `user/facts/`** — 最通用的种类
5. **陪伴模式用 `feelings/``people/``beliefs/``moments/`** — 见 `companion-mode.md`

---

## 依赖声明规则

`imports` 有三种强度，从强到弱：

### required — 强依赖

**规则：** 理解 B 必须先读 A，则 A 是 B 的 required 依赖。

- 记忆对其 schema 的引用 → required
- 上下文包对其核心组成记忆的引用 → required
- 决策记忆引用其依据的约束条件 → required

**效果：** resolve 时 required 节点一定被加载；token 超预算时降级为 summary 而非丢弃。

### recommended — 推荐依赖

**规则：** 读了 A 能更好理解 B，但不读也不影响核心理解。

- 决策记忆引用相关的市场分析报告
- 某个知识点引用其背景知识

**效果：** `--depth recommended` 时被加载；仅 `--depth required` 时被跳过。

### related — 弱关联

**规则：** A 和 B 有关联但无理解上的依赖。

- 同行业的另一只股票讨论
- 同一话题下不同时间的讨论

**效果：** 仅 `--depth full` 时被加载。

---

## intensity 评估规则

intensity 是 1-10 的整数，表示记忆的持久重要性。

| 区间 | 等级 | 含义 | 典型场景 |
|------|------|------|----------|
| 1-3 | 临时 | 会话结束后可遗忘 | 暂时性的待办事项、一次性查询结果 |
| 4-6 | 常规 | 值得保留但不关键 | 一般性偏好、日常讨论记录 |
| 7-9 | 重要 | 关键判断或核心约束 | 投资策略调整、风险偏好变更、重大决策 |
| 10 | 永久 | 终生不忘的原则 | 价值观声明、"绝不"类型的硬约束 |

**注意：** intensity >= 8 时，系统自动标记 `protected: true`，防止被意外修改或删除。

### 评估技巧

- 问自己："三个月后，这个信息还重要吗？" → 不重要的给 1-3
- 问自己："如果这个信息丢失，会导致错误决策吗？" → 会的话给 7+
- 不要给所有记忆都打 7+：如果一切都很重要，就什么都不重要了

---

## summary 写作规则

summary 是记忆的"名片"，在 token 裁剪时替代正文。必须独立可理解。

### 规则

1. **一句话概括核心内容**，不超过 80 字
2. **独立可理解**：不依赖正文即可知道这个记忆在说什么
3. **包含关键数值和结论**：如果是决策记忆，包含"做了什么 + 为什么"
4. **使用第一人称或第三人称一致**：用户偏好用"用户偏好..."，事实用陈述句

### 好例子

- `"中高风险偏好，可承受30%回撤，投资周期6-12个月"`
- `"2026年2月购入SOXL 200股，基于半导体上行周期判断"`
- `"用户明确偏好不碰加密货币，因不熟悉该领域"`

### 差例子

- `"TODO: fill in summary"` — 没有信息量
- `"关于投资的一些想法"` — 太模糊，不知道具体内容
- `"风险偏好"` — 缺少具体参数

---

## 完整对话场景示例

### 场景 A：用户分享偏好

**对话：**
> 用户：我比较喜欢分散投资，单只股票不超过总仓位的 20%。
> Agent：明白了，我把这个偏好记录下来。

**Agent 的决策过程：**

1. **选择类型：** 这是单个偏好/约束 → **atom**（无 schema，无 imports）
2. **评估 intensity：** 这是投资约束，可能影响未来决策 → **7**（重要）
3. **依赖声明：** 不依赖其他记忆 → 无 imports
4. **summary：** "用户偏好分散投资，单只股票仓位不超过20%"

**生成的 frontmatter：**
```yaml
type: atom
id: user/preferences/position-limit
summary: "用户偏好分散投资，单只股票仓位不超过20%"
intensity: 7
protected: true
tags: [investment, preference, risk-management]
```

---

### 场景 B：做出重大决策

**对话：**
> 用户：我今天把 SOXL 全卖了。AI 芯片需求增速放缓，加上仓位太重，每晚睡不好。
> Agent：这是一个重要的决策。我记录一下，并关联到你之前的持仓和投资主线。

**Agent 的决策过程：**

1. **选择类型：** 这是一个具体决策事件，需要记录标的、时间、理由 → **atom**，使用 `--schema schemas/decision`
2. **评估 intensity：** 重大调仓决策 → **8**
3. **依赖声明：**
   - `required`：`user/investment/semiconductor-thesis`（主线判断）、`user/investment/current-holdings`（此前的持仓记录）、`user/preferences/position-limit`（偏好约束）
   - `recommended`：`user/investment/risk-tolerance`（风险偏好作为背景）
4. **summary：** "2026年4月27日清仓SOXL，因AI需求放缓且仓位过重影响睡眠"

**生成的 frontmatter：**
```yaml
type: atom
id: user/investment/april-sell-soxl
schema: schemas/decision
summary: "2026年4月27日清仓SOXL，因AI需求放缓且仓位过重影响睡眠"
intensity: 8
protected: true
tags: [investment, decision, sell]
imports:
  required:
    - user/investment/semiconductor-thesis
    - user/investment/current-holdings
    - user/preferences/position-limit
  recommended:
    - user/investment/risk-tolerance
  related: []
```

---

### 场景 C：日常信息记录

**对话：**
> 用户：对了，下周有个新能源行业的线上分享会，我可能会参加。
> Agent：好的，我记一下这个信息。

**Agent 的决策过程：**

1. **选择类型：** 这是一个暂时性的待办/事件信息 → **atom**
2. **评估 intensity：** 下周的事，结束后可能不再重要 → **2**（临时信息）
3. **依赖声明：** 与现有投资记忆无直接关联 → 无 imports
4. **summary：** "下周有新能源行业线上分享会，用户可能参加"

**生成的 frontmatter：**
```yaml
type: atom
id: user/observations/new-energy-webinar
summary: "下周有新能源行业线上分享会，用户可能参加"
intensity: 2
tags: [event, new-energy]
```

---

## 常见错误速查

| 错误 | 正确做法 |
|------|----------|
| 把所有偏好放一个 atom | 拆成多个 atom，每个只表达一个事实 |
| 有 schema 依赖但忘记声明 schema | 使用 `--schema` 参数声明 |
| 上下文包自己写很长的 body | 上下文包的 body 应简短，内容在被引用的记忆中 |
| 把所有依赖都标 required | 区分 required / recommended / related |
| 所有记忆 intensity=5 | 根据重要性差异化评分 |
| summary 写 "TODO" | 必须写一句话摘要 |
| 忘记填 change_note 就 update | update 时必须用 `--change-note` 说明改动原因 |
