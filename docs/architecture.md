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
create → 生成 .md 文件（带 frontmatter 模板）→ 自动追加 log.md
    ↓
reindex → 扫描所有 .md → 解析 frontmatter → 写入 index.json
    ↓
resolve → 读取 index.json → 构建 DAG → 拓扑排序 → token 裁剪 → 输出
    ↓                        → maturity 自动升降（draft→verified→proven）
    ↓                        → 追加 log.md（maturity 升级记录）
validate → 循环检测 + 断链检查 + schema 合规 + maturity 复核建议
```

日志流（全局追加）：

```
create/update/snapshot → append_log() → .codememory/log.md（只追加不修改）
maturity auto-upgrade  → append_log() → .codememory/log.md
codememory log         → show_log()   → 时间线审计
```

## 四、目录布局

```
CodeMemory/
├── src/codememory/               # 记忆引擎（17 模块）
│   ├── core.py                   #   frontmatter 解析, body hash, logging
│   ├── models.py                 #   Pydantic v2 数据模型
│   ├── handlers.py               #   统一命令处理（cli + tools 共享）
│   ├── index.py                  #   Index 加载/保存/reindex
│   ├── resolve.py                #   DAG + 拓扑排序 + token 裁剪 + maturity
│   ├── validate.py               #   循环/断链/schema/衰减/maturity 复核
│   ├── create.py / update.py     #   记忆 CRUD + log 集成
│   ├── search.py / orphans.py    #   检索 + 孤立发现
│   ├── log.py                    #   全局追加日志
│   ├── import_cmd.py             #   冷启动文本导入
│   ├── cli.py / tools.py         #   薄壳接口层
│   └── integrations.py           #   OpenAI/Anthropic/Gemini 工具适配
├── docs/
├── examples/                     # 示例记忆数据（与框架分离）
│   └── investment/
├── tests/
│   └── unit/                     # 57 个单元测试
├── pyproject.toml
└── .claude/
```

记忆数据目录（可任意路径）：

```
<memory-root>/
├── user/                         # 个人记忆
│   ├── preferences/              #   偏好、习惯、约束
│   └── {domain}/                 #   按领域（investment, ideas...）
├── team/                         # 团队约定（可选，Git 共享）
├── tech/                         # 技术知识（可选，跨项目共享）
├── biz/                          # 业务知识（可选，按领域）
├── schemas/                      # Schema 定义
└── .codememory/
    ├── index.json                # DAG 索引
    └── log.md                    # 全局追加审计日志
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
      "path": "user/investment/semiconductor-thesis.md",
      "maturity": "proven",
      "evidence": {
        "contributors": ["agent"],
        "sessions": ["#a3f8c2"],
        "verified_in": [
          {"session": "#c5f0e2", "date": "2026-04-28"}
        ]
      }
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

### Focus 参数

| focus | 行为 |
|-------|------|
| `decision` | 标记为 decision 的节点全文输出，其余降级为 summary |
| `pitfall` | 标记为 pitfall 的节点全文输出，其余降级为 summary |
| 逗号分隔 | `decision,pitfall` 交叉过滤 |

### Maturity 自动升降

```
resolve 时自动检查（LLM 零负担）：
  access_count >= 3              → draft → verified
  access_count >= 10 + dependents > 0 → verified → proven
  update --status superseded     → maturity = superseded

validate 时复核（仅建议，不降级）：
  proven + 12 个月无 resolve     → 建议复核
```

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
tags: ["investment", "thesis", "decision"]
maturity: draft | verified | proven     # 使用验证级别（自动升降）
intensity: 5                            # 1-10，>=8 自动 protected
evidence:                               # 溯源信息（自动维护）
  contributors: ["agent"]
  sessions: ["#a3f8c2"]
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
| maturity 过期 | `validate` 建议复核（不自动降级） |

## 九、新增功能（Phase 4）

- **Maturity 自动升降**：resolve 根据 access_count + dependents 自动升级 maturity；LLM 零负担
- **全局审计日志**：`.codememory/log.md` 全局追加，`codememory log` 时间线查看
- **Evidence 溯源**：create 时自动记录 session；maturity 升级时追加 verified_in
- **semantic_type**：通过 tags 标记知识类型（model/decision/guideline/pitfall/process），`search --semantic-type` 过滤
- **resolve --focus**：按语义类型过滤节点输出分辨率，保持因果链完整
- **冷启动 import**：从文本提取初始记忆，maturity=draft 安全阀

## 十、已知限制

- Token 估算用 `len(text)` 代替真实 tokenizer
- 版本锁定（`pin: v1`）未实现，始终加载当前文件
- 循环检测只在 validate/resolve 时运行，不在 create 时阻止
- maturity 升级是会话内的（基于 index 内存数据），reindex 后从 YAML frontmatter 恢复默认值
