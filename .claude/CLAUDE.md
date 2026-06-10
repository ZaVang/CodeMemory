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
│       ├── build.py             # 统一装配管线：DAG/拓扑/两遍式裁剪/渲染
│       ├── resolve.py           # build 的 plain-markdown 薄别名（兼容）
│       ├── context_pack.py      # 兼容 shim（re-export build）
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
- **变更管理**：proposal（提案，新增类已实装）、log（审计日志）

概念 ↔ 当前 CLI 对照：build = `build`（主命令；`resolve` / `context-pack` 为同管线别名）；check = `validate`；asset = `source` 命令组；proposal 新增类 = `create --propose` + `merge` / `reject`，修改类未实装（过渡做法见 guide 第 6 节）。

## 关键设计决策

- 装配是 DAG 依赖解析 + 预算裁剪，不是向量检索；search 只做入口发现，不参与装配。
- asset（原始材料）不进依赖图；atom 不装长文档。
- 分级写入纪律：新增 atom 直写（没把握用 `create --propose`，owner merge/reject）；修改已有 atom 或涉及 protected 走 proposal（修改类实装前：会话内征得 owner 同意）。proposed/archived/superseded 不进默认 build 与 search。
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
codememory build <id> [--depth required|recommended|full] [--budget N] [--format xml-markdown|markdown|plain-markdown|json]
codememory resolve <id> [--depth ...] [--budget N]        # build 的 plain-markdown 别名
codememory context-pack <id> [--format ...] [--budget N] [--task-goal "..."]   # build 的别名
codememory source expand <id> [--start N] [--end N] [--max-chars N]

# 写路径（纪律见 docs/agent-memory-guide.md 第 6 节）
codememory create --id <id> [--type atom|schema] [--schema s] [--tags "a,b"] [--propose] [--dry-run]
codememory update <id> --change-note "..." [--summary "..."] [--body "..."] [--status s] [--import-required ...] [--source-ref <artifact_id>]
codememory merge <id> | reject <id>        # proposed → active / archived（owner 审阅）
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
