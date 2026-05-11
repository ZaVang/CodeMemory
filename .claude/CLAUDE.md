# CodeMemory — 记忆原子化协议

将 AI 记忆拆分为可依赖解析的原子单元。核心理念：**记忆加载是依赖解析问题，不是搜索问题。**

## 文件架构

```
CodeMemory/
├── src/
│   ├── harnesslib/              # 通用 Agent 编排（跨项目复用）
│   ├── llm_gateway/             # 多 provider LLM 接入（跨项目复用）
│   └── codememory/              # 记忆管理（本项目核心，Phase 2A 从 bin/ 提取）
│       ├── __init__.py          # Public API
│       ├── core.py              # frontmatter 解析, body hash, logging 配置
│       ├── models.py            # Pydantic v2 数据模型
│       ├── handlers.py          # 统一命令处理（cli + tools 共享）
│       ├── index.py             # Index 加载/保存/reindex
│       ├── resolve.py           # DAG + 拓扑排序 + token 裁剪 + stale/pin 提醒
│       ├── validate.py          # 循环检测 + 断链 + schema 合规 + 衰减建议
│       ├── create.py            # 记忆模板生成
│       ├── update.py            # 版本递增 + change_log + summary_hash 重算
│       ├── search.py            # 检索（tags/query/type/status）
│       ├── orphans.py           # 孤立记忆发现
│       ├── changelog.py         # 变更历史查看
│       ├── transient.py         # TransientDAG 会话级推理链
│       ├── snapshot.py          # 瞬态持久化
│       ├── log.py                # 全局追加审计日志
│       ├── import_cmd.py         # 冷启动文本导入
│       ├── suggest_deps.py       # 自动依赖推断（三层过滤 + 双向）
│       ├── skeletonize/          # 结构化批量导入（Markdown 骨架化）
│       │   ├── __init__.py
│       │   ├── common.py         # intensity 解析 + 文本工具
│       │   ├── markdown.py       # 节拆分 + 骨架化
│       │   └── code.py           # 代码骨架化（Python/JS/TS，Tree-sitter）
│       ├── integrations.py      # CodememoryToolkit（OpenAI/Anthropic/Gemini）
│       ├── cli.py               # 薄 argparse 壳（< 200 行）
│       └── tools.py             # harnesslib Sandbox 工具注册
├── bin/
│   ├── codememory               # bash wrapper → python -m codememory.cli
│   └── codememory.ps1
├── examples/                    # 示例记忆数据（不是框架的一部分）
│   └── investment/
├── docs/
├── tests/
├── pyproject.toml
└── .claude/
```

## 核心概念

### 两种记忆原语

| 类型 | 含义 |
|------|------|
| **atom** | 通用记忆——角色通过 `imports`、`schema`、`tags`、目录表达 |
| **schema** | 元模板——定义记忆结构，atom 通过 `schema` 字段引用 |

所有记忆统一为 `atom`，旧概念 `instance`（有 schema 的决策）和 `composite`（依赖其他记忆的组合包）现在都是带 `schema` 和/或 `imports` 的 atom。reindex 自动映射旧 type 值。

### Layer 0 认知接口

Agent 与记忆系统之间的接口层，实现五个认知基础操作（稳定如 CPU 指令集）：

| 认知行为 | 命令 | 说明 |
|----------|------|------|
| **扫视** | `codememory overview` | 会话启动自动注入 top 5 相关记忆摘要到 system prompt |
| **注视** | `codememory focus <id> --level full\|summary` | 动态切换特定记忆的分辨率 |
| **残留** | 瞬态 DAG + `codememory snapshot` | 会话推理链在内存中，snapshot 持久化 |
| **重构** | `codememory resolve <id> --depth ... --budget ...` | DAG 拓扑拼装 + token 裁剪输出 |
| **触景生情** | `codememory wander` / 联想搜索 | 随机或关联激活冷记忆 |

### 关键设计决策

- 记忆加载是 DAG 解析问题，不是 vector search
- 每个 .md 文件 = 一个记忆单元（YAML frontmatter + Markdown body）
- 依赖通过 frontmatter 的 `imports` 显式声明，不靠语义相似度猜测
- Token 预算裁剪：超预算时 required 节点降级为 summary
- 遗忘是路径不可达问题，不是删除问题。系统只建议，不自动删除。
- 框架（`src/codememory/`）与数据（`examples/`）物理分离

---

## 硬约束（不可违反）

### 1. Agent 视角：只用 Bash

**所有 Agent 可用的记忆操作必须通过 bash 命令完成。** Agent 不调用 Python API，不 import codememory，不直接读写 .md 文件。

```bash
# Agent 看到的接口——全部是 bash 命令
codememory overview --tags "investment"     # 扫视
codememory resolve user/investment/context  # 重构
codememory focus risk-tolerance --level full # 注视
codememory wander                          # 触景生情
codememory snapshot "session-001"          # 残留持久化
```

底层实现可用 Python（处理 DAG、拓扑排序等复杂逻辑），但 Agent 视角下只有 bash 子命令。这遵循 Claude Code 的模式：`file edit` 和 `bash` 是接口，内部实现不限语言。

### 2. Python 数据模型：Pydantic v2

**所有 Python schema 类、配置模型、数据传递对象必须使用 Pydantic v2 实现。**

```python
from pydantic import BaseModel, Field

class MemoryEntry(BaseModel):
    type: str = Field(description="atom | schema")
    id: str
    summary: str
    # ...

# 序列化统一用
data = entry.model_dump(mode="json")
```

禁止事项：
- 禁止使用 Pydantic v1 API（`.dict()`, `class Config`, `schema()`）
- 禁止用裸 `dict` 作为模块间 API 边界（改用 BaseModel）
- 禁止在 Pydantic model 中使用 `Optional[T]` 不设 default=None（Pydantic v2 要求显式 default）

---

## 代码规范

### 技术栈
- Python 3.13+，核心依赖：`pyyaml`、`pydantic>=2.0`；可选依赖 `tree-sitter`（代码骨架化需要 `pip install codememory[code]`）
- codememory 自身不依赖 harnesslib 或 llm_gateway（只在 tools.py 和 integrations.py 中适配接口）
- token 估算用 `len(text)` 近似

### 编码约定
- 所有公共函数类型注解覆盖
- 系统日志走 `logging`（WARNING+），用户可见正文走 `print()`（stdout）
- `--verbose` / `--quiet` 全局控制日志级别
- frontmatter 修改不触发 stale（基于 body hash）
- 命令处理委托给 `handlers.py`，cli.py 和 tools.py 只做薄壳

### 修改原则
- 最小变更：只改与任务直接相关的代码
- 不引入新依赖：除非有充分理由
- 不碰 `src/harnesslib/` 和 `src/llm_gateway/` 的内部实现（它们是独立组件，在其他仓库维护）
- 先验证再提交：改代码后运行 `validate` + `resolve` 确认

---

## CLI 命令速查

```bash
# 创建 / 更新
codememory create --id user/ideas/my-thesis [--intensity N] [--dry-run] [--tags "a,b"] [--schema <id>]
codememory create --type schema --id schemas/my-template
codememory update <id> --change-note "explanation" [--body "..."] [--summary "..."] [--status archived]

# 索引 / 验证 / 检索
codememory reindex
codememory validate [-v|-q]
codememory search [--query <q>] [--tags <t>] [--type <t>] [--status <s>] [--maturity proven] [--semantic-type decision] [--has-imports] [--has-schema]

# 分析 / 日志
codememory orphans [--type <t>] [--min-intensity <n>]
codememory changelog <id>
codememory log [--limit N]

# 导入
codememory import --file notes.txt --extract preferences
codememory import --stdin --extract decisions
codememory skeletonize <file_or_dir> [--min-intensity N] [--dry-run] [--tags "a,b"]

# 依赖推断
codememory suggest-deps <id> [--min-score N] [--forward-only] [--retroactive-only]

# Layer 0 认知工具
codememory overview [--tags <t>] [--format inject] [--with-recall] [--min-maturity verified]
codememory focus <id> --level full|summary [--content "..."] [--resolve]
codememory wander [--mode cool|random] [--inject]
codememory resolve <id> [--depth required|recommended|full] [--budget N] [--focus decision]
codememory snapshot <id> [--target <id> | --from-dag <json_file>]
```

## 测试规范

- 单元测试：`PYTHONPATH=src python -m pytest tests/unit/ -v` — 108 个测试覆盖 resolve/validate/create/update/skeletonize/边界
- 集成测试：`PYTHONPATH=src python tests/integration_test.py` — 24 个断言覆盖全部场景
- 手工验证：`validate` → `resolve` → `check output`
- 边界测试：循环依赖、断链、空记忆、超大/零预算
- 验证命令：
  ```bash
  codememory reindex && codememory validate
  codememory resolve user/investment/context
  codememory resolve user/investment/context --budget 500
  # skeletonize 验证
  codememory skeletonize examples/ --dry-run
  codememory skeletonize <dir> --min-intensity 5 --tags "imported"
  ```

## 禁止事项

- 禁止 Agent 绕过 bash CLI 直接调用 Python API 或 import codememory
- 禁止在 Agent 工具定义中使用 Python 函数签名（Agent 只能看到 bash 命令描述）
- 禁止 new 第三方依赖而不在 plan 中说明理由
- 禁止修改 `src/harnesslib/` 或 `src/llm_gateway/` 的内部逻辑（它们在上游仓库维护）

## 开发环境

### 端口

| 服务 | 默认端口 | 启动命令 | 备注 |
|------|---------|---------|------|
| Backend (FastAPI) | 8000 | `python backend/server.py` | 可通过 `--root` 参数或 `CODEMEMORY_ROOT` 环境变量指定记忆数据目录 |
| Frontend (Vite) | 5300 | `cd frontend && npm run dev` | 若端口被占用，Vite 会自动递增到 5301、5302 等；proxy 配置固定指向 backend `localhost:8000` |
| **一键启动** | — | `./bin/dev` | 同时启动 Backend + Frontend，Ctrl+C 停止全部 |

实际端口以启动时终端输出为准。验收脚本不应硬编码端口号——优先读 `vite.config.ts` 中的 `server.port` 或启动日志。
