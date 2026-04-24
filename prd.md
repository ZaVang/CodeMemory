# 记忆原子化协议 PRD

> 一个完整的 AI 记忆子系统——定义记忆的格式、存储、检索、加载和生命周期管理。
> 核心理念：**记忆加载是依赖解析问题，不是搜索问题。**

**创建日期**：2026-04-22  
**最后更新**：2026-04-24  
**状态**：设计收敛，待原型验证  
**同步策略**：Git Repo

---

## 一、背景与动机

### 1.1 核心问题

多 AI 环境工作（Claude Code / Antigravity / Coze）时，项目记忆割裂，无法跨环境共享上下文。

**当前记忆系统的局限**：

| 方案 | 问题 |
|------|------|
| 文档级记忆 | 粒度太粗，无法精细引用 |
| RAG | 基于语义相似度检索，无法保证因果完整性 |
| 知识图谱 | 结构好但 LLM 难以原生操作 |

### 1.2 核心洞察

传统 RAG 检索到的 chunks 之间没有依赖关系——可能捞到"2月买了半导体"但捞不到"为什么买"的前置判断。

**本协议的核心差异**：给记忆赋予代码的依赖图语义。每段记忆声明自己的前置依赖，加载时按拓扑排序组装，确保 LLM 收到的上下文是因果完整的。

### 1.3 设计哲学

1. **关系视角 > 数据视角**：不是"知识放这，项目放那"，而是"你的东西放 `user/`，我的东西放 `self/`"
2. **依赖解析 > 语义搜索**：记忆加载像 `webpack bundle`，不像 `vector search`
3. **Markdown 为母语**：LLM 原生读写，跨平台零配置
4. **抽象字段 > 具体字段**：base fields 不出现"地点""人物"等具体字段，领域字段由 schema 定义

---

## 二、系统架构：三层设计

```
┌──────────────────────────────────────────┐
│  Layer 3: Harness Integration            │
│  Agent 如何使用记忆系统（bash CLI）         │
├──────────────────────────────────────────┤
│  Layer 2: Operations & Retrieval         │
│  resolve / search / deps / create        │
│  index.json / 依赖解析 / 生命周期管理      │
├──────────────────────────────────────────┤
│  Layer 1: Memory Format Spec             │
│  Markdown + YAML Frontmatter             │
│  Base Fields / 四种原语 / 三级依赖         │
└──────────────────────────────────────────┘
```

- **Layer 1** 单独可用（手动管理记忆文件）
- **Layer 1+2** 配合 bash 脚本 = 功能完整的系统
- **Layer 1+2+3** = Agent 全自动集成

---

## 三、Layer 1：记忆格式规范

### 3.1 文件格式：Markdown + YAML Frontmatter

| 要求 | 满足情况 |
|------|----------|
| LLM 可直接读写 | ✅ Markdown 是 LLM 的母语 |
| 结构化元数据 | ✅ Frontmatter 是标准 YAML，支持完整层级嵌套 |
| 可编程解析 | ✅ 任何语言都有 YAML 解析库 |
| 跨平台零配置 | ✅ 纯文本，任何 AI 平台直接读 |
| 版本控制友好 | ✅ Git diff 完美支持 |
| 人类可读可编辑 | ✅ 任何编辑器打开就能看懂 |

### 3.2 Base Fields（通用字段）

设计原则：**足够抽象，适用于任何形式的记忆。**

```yaml
---
# ══════ Identity ══════
type: atom | composite | schema | instance
id: user/investment/semiconductor-thesis     # 路径式唯一 ID

# ══════ Core ══════
summary: "AI存储+AI制造双核心驱动，2026最确定产业趋势"

# ══════ Lifecycle ══════
status: active           # active | archived | superseded | deprecated
created: 2026-04-22
updated: 2026-04-22
version: 1

# ══════ Classification ══════
tags: [investment, thesis]

# ══════ Provenance ══════
source:
  platform: antigravity
  created_by: user

# ══════ Integrity ══════
summary_hash: a3f2e1d    # 正文内容的短 hash，检测 summary 过期
---
```

#### 字段规范

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | enum | ✅ | atom / composite / schema / instance |
| `id` | string | ✅ | 路径式 ID，与文件路径对应 |
| `summary` | string | ✅ | LLM 生成的一句话摘要——记忆的 docstring |
| `status` | enum | ✅ | active / archived / superseded / deprecated |
| `created` | date | ✅ | 创建时间 |
| `updated` | date | ✅ | 最后更新时间 |
| `version` | int | ✅ | 版本号，更新时递增 |
| `tags` | string[] | ✅ | 分类标签 |
| `source.platform` | enum | ❌ | 来源平台 |
| `source.created_by` | enum | ❌ | user / ai |
| `summary_hash` | string | ❌ | `hash(body markdown, 不含 frontmatter)`。body 改了 hash 就变，frontmatter 修正不触发 stale |

#### 可选扩展字段

| 字段 | 适用类型 | 说明 |
|------|----------|------|
| `imports` | composite, instance | 三级依赖声明 |
| `schema` | instance | 指向所用模板 |
| `purpose` | composite | 使用场景描述 |
| `change_note` | 所有（更新时） | 本次更新的原因 |
| `supersedes` | 所有（替代时） | 被替代记忆的 ID |
| `fields` | schema | 领域字段定义列表 |

#### `summary` 字段的核心作用

`summary` 是整个系统最重要的 base field：

| 角色 | 说明 |
|------|------|
| 记忆的 docstring | 一句话概括这段记忆 |
| 索引搜索内容 | index.json 中的可搜索字段 |
| Token 紧张时的替代品 | 预算不够时加载 summary 代替全文 |
| 快速预览 | 浏览记忆列表时显示 |

**Summary 生成规则**：
- 由 LLM 在创建/更新记忆时自动生成
- 用户可手动修改确认
- 当正文 hash 与 `summary_hash` 不匹配时，系统提示重新生成

### 3.3 四种记忆原语

| 原语 | 代码类比 | 含义 | 有依赖 |
|------|----------|------|--------|
| **Atom** | `const` | 不可再分的原子事实 | ❌ |
| **Composite** | `function` | 组合多个记忆的打包清单 | ✅ |
| **Schema** | `class/type` | 某类记忆的结构模板 | ❌ |
| **Instance** | `new Obj()` | 遵循 Schema 的具体记忆 | ✅ |

#### Atom（原子事实）

最小单元，不依赖其他记忆。判断标准：能被独立引用且引用时仍有独立意义。

```markdown
---
type: atom
id: user/investment/semiconductor-thesis
summary: "AI存储+AI制造双核心驱动，2026最确定产业趋势"
status: active
created: 2026-04-22
updated: 2026-04-22
version: 1
tags: [investment, thesis]
source:
  platform: claude-code
  created_by: user
summary_hash: a3f2e1d
---

# 半导体投资主线

AI 存储需求爆发 + AI 制造国产替代，形成双核心驱动。
这是 2026 年最确定的产业趋势之一。
```

#### Schema（记忆模板）

定义某类记忆的领域字段。字段类型限于基础类型（string / float / date / bool / enum）。

```markdown
---
type: schema
id: schemas/decision
summary: "决策类记忆的结构模板，包含 what/why/when/confidence/outcome"
status: active
created: 2026-04-22
updated: 2026-04-22
version: 1
tags: [meta, template]
fields:
  - name: what
    type: string
    required: true
  - name: why
    type: string
    required: true
  - name: when
    type: date
    required: true
  - name: confidence
    type: float
    required: true
  - name: outcome
    type: string
    required: false
---

# Decision Schema

所有"决策类"记忆应遵循此结构。
```

#### Instance（记忆实例）

遵循 Schema，包含 base fields + 领域字段 + 依赖。

```markdown
---
type: instance
schema: schemas/decision
id: user/investment/february-buy
summary: "2月重仓半导体ETF，基于AI存储爆发+国产替代判断，置信度0.8"
status: active
created: 2026-02-15
updated: 2026-04-22
version: 2
tags: [investment, decision]
source:
  platform: antigravity
  created_by: user
summary_hash: b7c9d4e

what: "重仓半导体ETF（512480）"
why: "AI存储爆发 + 国产替代加速"
when: 2026-02-15
confidence: 0.8
outcome: "截至4月涨15%"

imports:
  required:
    - id: user/investment/semiconductor-thesis
    - id: user/investment/risk-tolerance
      pin: v1
      reason: "决策基于当时的风险偏好"
  recommended:
    - user/investment/market-env-2026Q1
  related:
    - user/investment/historical-cycles
---

# 2月重仓半导体决策

基于半导体主线判断，结合个人风险偏好，决定将仓位的 40% 配置到半导体 ETF。

## 决策过程
...

## 后续追踪
- 2026-03-01: 涨了5%
- 2026-04-15: 涨了15%
```

#### Composite（组合视图）

打包清单，声明"理解 X 话题需要加载哪些记忆"。支持嵌套。

```markdown
---
type: composite
id: user/investment/context
summary: "投资决策的完整上下文包"
status: active
created: 2026-04-22
updated: 2026-04-22
version: 1
tags: [investment, context]
purpose: "讨论投资话题时加载的完整上下文"

imports:
  required:
    - user/investment/semiconductor-thesis
    - user/investment/risk-tolerance
    - user/investment/february-buy
    - user/investment/current-holdings
  recommended:
    - user/investment/market-env-2026Q1
  related:
    - user/investment/historical-cycles
---

# 投资决策上下文

本组合提供完整的投资决策背景。
```

### 3.4 三级依赖

```yaml
imports:
  required: []      # 缺了会误解本记忆，始终加载
  recommended: []   # 锦上添花，token 够就加载
  related: []       # 扩展阅读，主动探索时加载
```

版本锁定（仅 required 可用）：

```yaml
imports:
  required:
    - id: user/investment/risk-tolerance
      pin: v1
      reason: "决策基于当时的风险偏好"
```

---

## 四、设计约束

协议级硬性规则：

| # | 规则 | 原因 |
|---|------|------|
| R1 | **禁止循环引用** | Import 是有方向的因果关系。循环说明建模粒度需调整——应合并为一个 atom 或放在同一个 composite 中作为 sibling |
| R2 | **`pin` 只允许用于 required** | recommended/related 默认跟随最新版本，pin 旧版本会造成认知不一致 |
| R3 | **每个文件只包含一个记忆** | 一个 .md 文件 = 一个记忆单元，ID 与文件路径一一对应 |
| R4 | **summary 必填** | 它是索引、预览、降级加载的基础 |
| R5 | **`self/` 仅 AI 可写** | 初期靠规范约束，不做强制实现 |
| R6 | **Schema 字段类型限于基础类型** | string / float / date / bool / enum。引用关系统一走 imports |
| R7 | **被 pin 的记忆不可物理删除** | 只能标记 archived/deprecated，保护 downstream 依赖 |

**R1 的执行层区分**：

| 场景 | 行为 | 说明 |
|------|------|------|
| `codememory validate` | 警告 + 列出循环 ID + 修复建议 | Lint 层面：不应该存在 |
| `codememory resolve` | 跳过循环节点 + 警告 + 继续加载其余 | Runtime 层面：容错，不因一条循环记忆导致整个 resolve 失败 |

---

## 五、Layer 2：操作与检索

### 5.1 代码式操作映射

| 代码操作 | 记忆等价 | 命令 |
|----------|----------|------|
| `import x from y` | 按路径加载 | `codememory resolve <id>` |
| `grep -r "keyword"` | 文本搜索 | `codememory search --query "半导体"` |
| IDE autocomplete | 结构化浏览 | `codememory search --tags invest --type atom` |
| `git log --since` | 时间查询 | `codememory search --since 2026-03` |
| Find References | 反向依赖 | `codememory rdeps <id>` |
| Go to Definition | 正向依赖 | `codememory deps <id>` |

### 5.2 index.json

只存元数据，不存全文。**每次 create/update 操作自动更新**，`reindex` 保留作为修复工具。

```json
{
  "version": 1,
  "updated": "2026-04-24T10:00:00+08:00",
  "memories": {
    "user/investment/semiconductor-thesis": {
      "type": "atom",
      "summary": "AI存储+AI制造双核心驱动",
      "status": "active",
      "tags": ["investment", "thesis"],
      "created": "2026-04-22",
      "updated": "2026-04-22",
      "version": 1,
      "path": "user/investment/semiconductor-thesis.md",
      "imports": { "required": [], "recommended": [], "related": [] }
    },
    "user/investment/february-buy": {
      "type": "instance",
      "schema": "schemas/decision",
      "summary": "重仓半导体ETF，基于AI存储爆发判断",
      "status": "active",
      "tags": ["investment", "decision"],
      "created": "2026-02-15",
      "updated": "2026-04-22",
      "version": 2,
      "path": "user/investment/february-buy.md",
      "imports": {
        "required": [
          "user/investment/semiconductor-thesis",
          "user/investment/risk-tolerance"
        ],
        "recommended": ["user/investment/market-env-2026Q1"],
        "related": ["user/investment/historical-cycles"]
      }
    }
  }
}
```

**搜索策略**：基于 summary + tags，覆盖 80% 场景。全文搜索暂不实现，预留钩子。

### 5.3 CLI（Bash）

```bash
# ═══ 检索 ═══
codememory resolve <id> [--depth required|recommended|full] [--budget <tokens>]
codememory search --query <text> [--tags <t>] [--type <t>] [--since <date>] [--status active]
codememory deps <id>             # 正向依赖
codememory rdeps <id>            # 反向依赖
codememory list [--type <t>] [--tags <t>] [--status active]

# ═══ 写入 ═══
codememory create --type <type> --id <id> [--schema <schema-id>]
codememory update <id> [--change-note "reason"]

# ═══ 维护 ═══
codememory reindex               # 重建 index.json（修复工具）
codememory validate              # 循环依赖 + schema 合规 + 断链检查
codememory graph <id>            # 可视化依赖树
codememory stale                 # 列出 summary_hash 不匹配的记忆
```

**演进路线**：初期 bash + `yq`/`jq`，核心逻辑复杂后封装为 Python/Go 二进制。

### 5.4 Resolve 算法

```python
def resolve(memory_id, budget_tokens, depth="required"):
    # 1. 从 index.json 构建依赖 DAG
    graph = build_dag(memory_id, depth)
    
    # 2. 循环引用检测（Runtime 容错：跳过循环节点，继续加载其余）
    if has_cycle(graph):
        cycle_ids = find_cycle_participants(graph)
        warn(f"Circular dependency detected, skipping: {cycle_ids}")
        graph = remove_nodes(graph, cycle_ids)  # 移除循环节点，不中断
    
    # 3. 拓扑排序（前置知识在前）
    ordered = topological_sort(graph)
    
    # 4. 版本解析（pin 只出现在 required 中）
    resolved = resolve_versions(ordered)
    
    # 5. Token 预算裁剪
    result, used = [], 0
    for mid in resolved:
        m = load_file(mid)
        t = count_tokens(m)
        if used + t <= budget_tokens:
            result.append(m)
            used += t
        elif is_required(mid, graph):
            result.append(load_summary_only(mid))  # 降级加载 summary
            used += count_tokens(summary)
    
    return result, used
```

---

## 六、记忆生命周期

### 6.1 状态流转

```
                  更新内容
         ┌──────────────────┐
         v                  │
  ──► [active] ────────► [active v2] ────► [active v3]
         │                                     │
         │ 新版本替代                            │ 不再需要
         v                                     v
    [superseded]                          [deprecated]
         │                                     │
         v                                     v
    [archived]                            [archived]
```

### 6.2 更新机制（三层）

| 层级 | 机制 | 场景 |
|------|------|------|
| 原地编辑 | 修改文件，version++，加 change_note | 事实修正、补充信息 |
| Git 历史 | 自动追溯 | 任何时候回看"当时写了什么" |
| 依赖锁定 | `pin: v1`（仅 required） | 确保引用方不受更新影响 |

### 6.3 Summary 过期检测

当正文被编辑但 summary 未更新时，`summary_hash` 不匹配：

```bash
codememory stale
# STALE  user/investment/risk-tolerance  (body changed, summary_hash mismatch)
```

---

## 七、目录结构

```
CodeMemory/                              # Git Repo
├── user/                                # 用户的记忆（用户+AI 可读写）
│   ├── projects/
│   ├── investment/
│   │   ├── semiconductor-thesis.md      # atom
│   │   ├── risk-tolerance.md            # atom
│   │   ├── february-buy.md              # instance
│   │   ├── current-holdings.md          # composite
│   │   └── context.md                   # composite（顶层包）
│   ├── ideas/
│   └── reminders/
├── self/                                # AI 的记忆（仅 AI 可写，用户可读）
│   ├── thoughts/
│   ├── opinions/
│   └── emotions/
├── schemas/                             # 记忆模板
│   ├── decision.md
│   ├── project.md
│   └── idea.md
├── .codememory/
│   ├── config.yaml                      # 全局配置
│   └── index.json                       # 记忆索引缓存
├── bin/
│   └── codememory                       # bash CLI 入口
└── README.md
```

**权限模型**：
- `user/`：用户和 AI 均可读写
- `self/`：**仅 AI 可写**，用户可读
- `schemas/`：用户和 AI 均可读写

---

## 八、Layer 3：Harness 集成

### 8.1 混合 Runtime

| 环境 | Resolve 方式 |
|------|-------------|
| 有 Harness（Antigravity, Claude Code） | Harness 解析 frontmatter，递归 resolve，注入上下文 |
| 无 Harness（手动） | 用 `codememory resolve` 脚本生成合并文本，粘贴给任何 AI |

### 8.2 Resolve 输出

```bash
$ codememory resolve user/investment/context --depth recommended --budget 2000

# === 已解析的上下文 (1250 tokens) ===

## [1/6] semiconductor-thesis (atom)
AI 存储需求爆发 + AI 制造国产替代...

## [2/6] risk-tolerance (atom, v2)
中风险偏好，可承受 15% 回撤...

## [3/6] february-buy (instance, decision)
重仓半导体ETF，基于AI存储爆发+国产替代...
...
```

输出可直接粘贴给任何 AI，不需要对方理解记忆协议。

---

## 九、已决策事项

| 问题 | 决策 | 理由 |
|------|------|------|
| 系统定位 | 完整 memory 子系统（三层） | 格式+操作+集成缺一不可 |
| 文件格式 | Markdown + YAML Frontmatter | LLM 母语，跨平台，可编程 |
| ID 格式 | 路径式 `user/investment/xxx` | 像 import 路径 |
| 字段设计 | 抽象 base fields + schema 领域字段 | summary 是核心 |
| 记忆状态 | `status: active/archived/superseded/deprecated` | 多版本生命周期管理 |
| Summary 生成 | LLM 自动生成 + 用户可手动确认 | 配合 summary_hash 过期检测 |
| 索引机制 | index.json，每次写入自动更新 | reindex 保留作修复工具 |
| 全文搜索 | 暂不实现，留钩子 | summary + tags 先覆盖 80% |
| 实现语言 | Bash CLI（初期） | 所有 harness 可调用 |
| 依赖层级 | required / recommended / related | 三级 |
| Pin 约束 | 仅 required 可 pin | 避免认知不一致 |
| 循环引用 | 禁止，validate 友好提示 | 循环说明建模粒度需调整 |
| 继承 | 暂不实现，保留 | 避免过度工程化 |
| Schema 引用类型 | 暂不支持 `reference` 类型 | 引用统一走 imports |
| 被 pin 记忆 | 不可物理删除，只可 archive | 保护 downstream 依赖 |
| 同步策略 | Git Repo | 天然版本控制 |
| self/ 权限 | 仅 AI 可写，初期靠规范 | 不做强制实现 |

---

## 十、未来扩展

| 问题 | 优先级 | 备注 |
|------|--------|------|
| 跨库引用 `@namespace` | 低 | 预留 `@public/xxx` 语法 |
| Schema `reference` 字段类型 | 中 | 让字段值指向其他记忆 ID |
| 记忆销毁/遗忘 | 中 | 隐私场景需彻底删除 |
| Schema 迁移 | 中 | Schema 增加 required 字段后的合规检查 |
| 多语言记忆 | 低 | 可选 `lang` 字段 |
| 并发写入冲突 | 低 | 多 agent 协写需锁或合并 |
| CLI 演进 | 中 | bash → Python/Go 二进制 |
| 继承 / 链式关系 | 低 | 发现具体场景后再实现 |

---

## 十一、下一步

### Phase 1：原型验证（核心闭环）

必须跑通的端到端流程：**create → resolve → 人工验证上下文质量**

| 步骤 | 交付物 | 说明 |
|------|--------|------|
| 1. 创建目录结构 | `user/` `self/` `schemas/` `.codememory/` `bin/` | 按第七节目录规范 |
| 2. 创建样例记忆 | 3-5 个 atom + 1 schema + 1 instance + 1 composite | 用真实投资场景，不用占位符 |
| 3. 实现 `codememory create` | 生成模板文件 + 自动更新 index.json | 避免手写 frontmatter 出错 |
| 4. 实现 `codememory resolve` | frontmatter 解析 → DAG → 拓扑排序 → token 裁剪 | 核心算法 |
| 5. 实现 `codememory reindex` | 扫描所有 .md 重建 index.json | 修复工具 |
| 6. 实现 `codememory validate` | 循环检测 + 断链检查 | 基础完整性保障 |
| 7. 验证 | 用 resolve 输出注入 Antigravity 对话 | 测试跨会话记忆加载效果 |

### Phase 2：完善与跨平台

| 步骤 | 说明 |
|------|------|
| `codememory search` | summary + tags 搜索 |
| `codememory deps` / `rdeps` | 正向/反向依赖查询 |
| `codememory stale` / `graph` | summary 过期检测 / 依赖可视化 |
| 跨平台验证 | 把 resolve 输出粘贴给不同 AI，验证一致性 |
| `codememory update` | version++ / change_note / summary_hash 更新 |
