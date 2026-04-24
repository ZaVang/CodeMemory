# CodeMemory Phase 1：实施计划

> 核心闭环：**create → resolve → 验证上下文质量**

**创建日期**：2026-04-24  
**状态**：待执行  
**前置依赖**：Python 3.13 + pyyaml（已确认可用）

---

## 一、目录结构

```
CodeMemory/
├── bin/
│   ├── codememory.py       # Python CLI（核心实现）
│   ├── codememory           # bash wrapper
│   └── codememory.ps1       # PowerShell wrapper
├── user/
│   └── investment/
│       ├── semiconductor-thesis.md    # atom
│       ├── risk-tolerance.md          # atom
│       ├── position-semiconductor.md  # atom
│       ├── position-cash.md           # atom
│       ├── february-buy.md            # instance
│       ├── current-holdings.md        # composite
│       └── context.md                 # composite (top-level)
├── self/
│   └── thoughts/
├── schemas/
│   └── decision.md                    # schema
├── .codememory/
│   └── index.json
├── docs/
│   └── plans/
│       └── SPRINT.md                  # 本文件
├── prd.md
└── README.md
```

---

## 二、样例记忆文件（8 个）

基于投资决策场景，覆盖全部四种原语。

### 依赖图

```
context (composite)
├── [required] semiconductor-thesis (atom)
├── [required] risk-tolerance (atom)
├── [required] february-buy (instance → schemas/decision)
│   ├── [required] semiconductor-thesis (atom) ← 重复引用，resolve 去重
│   └── [required, pin:v1] risk-tolerance (atom)
└── [required] current-holdings (composite)
    ├── [required] position-semiconductor (atom)
    └── [required] position-cash (atom)
```

### 文件清单

| 文件 | 类型 | ID | 依赖 |
|------|------|-----|------|
| `schemas/decision.md` | schema | `schemas/decision` | 无 |
| `user/investment/semiconductor-thesis.md` | atom | `user/investment/semiconductor-thesis` | 无 |
| `user/investment/risk-tolerance.md` | atom | `user/investment/risk-tolerance` | 无 |
| `user/investment/position-semiconductor.md` | atom | `user/investment/position-semiconductor` | 无 |
| `user/investment/position-cash.md` | atom | `user/investment/position-cash` | 无 |
| `user/investment/february-buy.md` | instance | `user/investment/february-buy` | required: semiconductor-thesis, risk-tolerance(pin:v1) |
| `user/investment/current-holdings.md` | composite | `user/investment/current-holdings` | required: position-semiconductor, position-cash |
| `user/investment/context.md` | composite | `user/investment/context` | required: 上述全部 |

---

## 三、Python CLI：bin/codememory.py

单文件实现，唯一外部依赖 `pyyaml`。

### 核心函数

```python
def parse_frontmatter(filepath) -> (dict, str):
    """分离 YAML frontmatter 和 body。
    body = frontmatter '---' 结束后的全部 Markdown 文本（不含 frontmatter）。
    summary_hash 基于 body 计算，修改 frontmatter 不触发 stale。"""

def compute_body_hash(body: str) -> str:
    """sha256(body)[:7]"""

def estimate_tokens(text: str) -> int:
    """原型阶段：直接用 len(text) 作为 token 近似值。
    budget 参数的单位也是字符数。精确 tokenizer 留作 Phase 2。"""
```

### 四个子命令

| 命令 | 功能 | 说明 |
|------|------|------|
| `create --type <t> --id <id> [--schema <s>]` | 生成模板文件 + 自动更新 index.json | 避免手写 frontmatter 出错 |
| `resolve <id> [--depth] [--budget]` | DAG → 拓扑排序 → token 裁剪 → 输出 | 核心算法 |
| `reindex` | 扫描所有 .md 重建 index.json | 修复工具 |
| `validate` | 循环检测 + 断链 + schema 合规 | 完整性保障 |

### Resolve 算法流程

```
1. 从 index.json 读取目标记忆的 imports
2. 递归构建依赖 DAG（按 depth 过滤层级）
3. 检测循环引用 → 跳过循环节点 + warn（Runtime 容错）
4. 拓扑排序（Kahn's algorithm，前置知识在前）
5. 版本解析（处理 pin 锁定）
6. 按序加载文件全文
7. Token 预算裁剪（超预算的 required → 只输出 summary）
8. 输出合并后的上下文文本
```

### Schema 合规检查逻辑

```python
def check_schema_compliance(metadata, schemas):
    schema_id = metadata.get('schema')
    if not schema_id: return []
    schema = schemas.get(schema_id)
    if not schema: return [f"Schema '{schema_id}' not found"]
    return [f"Missing required field: {f['name']}"
            for f in schema.get('fields', [])
            if f.get('required') and f['name'] not in metadata]
```

### Shell Wrappers

**bin/codememory** (bash):
```bash
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python "$SCRIPT_DIR/codememory.py" "$@"
```

**bin/codememory.ps1** (PowerShell):
```powershell
python "$PSScriptRoot\codememory.py" @args
```

---

## 四、验证计划

### 自动化验证

| # | 测试 | 预期结果 |
|---|------|----------|
| 1 | `codememory.py reindex` | index.json 包含 8 个记忆条目 |
| 2 | `codememory.py validate` | 0 errors（无循环、无断链、schema 合规） |
| 3 | `codememory.py resolve user/investment/context --depth required` | 输出 6 个记忆，拓扑排序顺序正确 |
| 4 | `codememory.py resolve user/investment/context --budget 500` | token 裁剪，部分降级为 summary |
| 5 | `codememory.py resolve user/investment/february-buy` | 含 pin:v1 的 risk-tolerance |
| 6 | `codememory.py create --type atom --id user/ideas/test` | 生成模板文件 + index 自动更新 |

### 循环依赖边界测试

手工创建临时循环文件（A imports B, B imports A）：
- `validate` → 输出 warn + 列出参与循环的 ID + 修复建议
- `resolve` → 跳过循环节点 + warn + 继续加载其余节点
- 验证后删除临时文件

### 人工验证

将 `resolve user/investment/context` 的完整输出粘贴到新的 AI 对话中，询问"我为什么2月买了半导体？"——验证 LLM 能基于加载的因果上下文准确回答。

---

## 五、执行顺序

```
[ ] 1. 创建目录结构（user/ self/ schemas/ .codememory/ bin/ docs/）
[ ] 2. 创建 8 个样例记忆文件
[ ] 3. 实现 bin/codememory.py
    [ ] 3.1 frontmatter 解析 + body hash
    [ ] 3.2 create 子命令
    [ ] 3.3 reindex 子命令
    [ ] 3.4 resolve 子命令（DAG + 拓扑排序 + token 裁剪）
    [ ] 3.5 validate 子命令（循环检测 + 断链 + schema 合规）
    [ ] 3.6 CLI 入口（argparse）
[ ] 4. 创建 shell wrappers
[ ] 5. 运行验证计划
    [ ] 5.1 reindex → 检查 index.json
    [ ] 5.2 validate → 0 errors
    [ ] 5.3 resolve 各场景测试
    [ ] 5.4 循环依赖边界测试
    [ ] 5.5 create 测试
[ ] 6. 人工验证：resolve 输出 → 新 AI 对话测试
```
