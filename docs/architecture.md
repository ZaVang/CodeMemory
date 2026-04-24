# CodeMemory 系统架构

## 一、设计理念

CodeMemory 的核心洞察：**AI 记忆加载的本质是依赖解析，不是语义搜索。**

传统 RAG 检索到的 chunks 之间没有依赖关系 — 可能捞到"2月买了半导体"但捞不到"为什么买"的前置判断。CodeMemory 通过显式依赖图（DAG）解决这个问题。

## 二、记忆原语

### Atom（原子）
- 不可再分的单一事实
- 无 `imports`，不被其他记忆污染
- 例：投资主线判断、风险偏好、持仓明细

### Instance（实例）
- 依附某个 `schema` 的具体决策或事件
- 有 `imports.required`（决策依赖的前置知识）
- 例："2月买入半导体ETF"决策，依赖 `semiconductor-thesis` + `risk-tolerance`

### Composite（组合）
- 将多个记忆打包为可一键加载的上下文
- 有 `imports.required/recommended/related`
- 例："投资决策完整上下文" = 主线 + 风险 + 历史决策 + 当前持仓

### Schema（模板）
- 定义 instance 的元结构
- 本身不是用户记忆，是 type 约束
- 例："决策模板"要求 instance 必须有 what/why/when/confidence 字段

## 三、数据流

```
create → 生成 .md 文件（带 frontmatter 模板）
    ↓
reindex → 扫描所有 .md → 解析 frontmatter → 写入 index.json
    ↓
resolve → 读取 index.json → 构建 DAG → 拓扑排序 → token 裁剪 → 输出
    ↓
validate → 循环检测 + 断链检查 + schema 合规验证
```

## 四、目录布局

```
CodeMemory/
├── bin/codememory.py           # CLI 入口（单文件，<500 行）
├── user/                       # 用户记忆
│   └── {domain}/               # 主题域（investment, ideas, work...）
│       └── {memory-name}.md    # 记忆文件
├── self/                       # AI 内部记忆
│   └── thoughts/               # 思考记录
├── schemas/                    # Schema 定义
│   └── {schema-name}.md        # Schema 文件（type=schema）
├── .codememory/
│   └── index.json              # 自动生成索引
└── docs/
    ├── architecture.md         # 本文件
    └── plans/
```

## 五、index.json 结构

```json
{
  "version": 1,
  "updated": "2026-04-24T14:22:37",
  "memories": {
    "user/investment/semiconductor-thesis": {
      "type": "atom",
      "summary": "AI存储+AI制造双核心驱动",
      "status": "active",
      "tags": ["investment", "thesis"],
      "created": "2026-02-10",
      "updated": "2026-04-24",
      "version": 1,
      "path": "user/investment/semiconductor-thesis.md"
    }
  }
}
```

## 六、Resolve 算法

```
1. 从 index.json 读取目标记忆的 imports
2. 递归构建依赖 DAG（按 depth 过滤：required/recommended/full）
3. 循环检测（DFS 三色标记） → 跳过循环节点 + warn
4. 拓扑排序（Kahn's algorithm） → 前置知识在前
5. 版本解析（pin 锁定，原型阶段未实现）
6. 按序加载文件全文
7. Token 预算裁剪：
   - 正文 fits → 输出正文
   - 正文 exceeds, is required → 输出 summary
   - 正文 exceeds, not required → 跳过
8. 输出合并后的上下文文本
```

### Depth 参数

| depth | 行为 |
|-------|------|
| `required` | 只追踪 `imports.required` |
| `recommended` | required + `imports.recommended` |
| `full` | required + recommended + `imports.related` |

## 七、Frontmatter 规范

每个记忆文件以 YAML frontmatter 开头：

```yaml
---
type: atom | instance | composite | schema
id: "user/investment/my-thesis"        # 全局唯一 ID
summary: "一句话摘要"                    # 用于 token 裁剪降级
status: active | archived | draft
created: "2026-01-15"
updated: "2026-04-24"
version: 1
tags: ["investment", "thesis"]
schema: "schemas/decision"              # instance 必须指定
imports:                                # composite / instance 必须
  required:
    - user/investment/semiconductor-thesis
    - id: user/investment/risk-tolerance
      pin: v1                           # 可选：锁定版本
      reason: "决策基于当时的激进偏好"
  recommended: []
  related: []
---
```

### 关键规则

- `summary` 在 token 裁剪时替代 body 输出
- `imports.required` 中 `pin: v1` 锁定历史版本（原型阶段未实现）
- Schema 合规：instance 必须包含其 schema 定义的所有 required 字段
- Body hash 基于 Markdown body 计算（不含 frontmatter），修改 frontmatter 不触发 stale

## 八、错误处理

| 场景 | 行为 |
|------|------|
| 循环依赖 | `validate` warn + `resolve` 跳过循环节点继续加载 |
| 断链（import 不存在的 ID） | `validate` error |
| Schema 字段缺失 | `validate` error |
| 目标记忆不存在 | `resolve` 报错退出 |
| 零预算 | 全部 required 节点降级为 summary |

## 九、已知限制（原型阶段）

- Token 估算用 `len(text)` 代替真实 tokenizer
- 版本锁定（`pin: v1`）未实现，始终加载当前文件
- 无自动版本历史管理
- 循环检测只在 validate/resolve 时运行，不在 create 时阻止
