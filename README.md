# CodeMemory

**memory as code** —— 记忆按代码的方式组织：原子化、显式依赖、按需装配。

一个记忆库就是一个仓库，agent 是它的运行时。记忆装配是依赖解析问题，不是搜索问题：CodeMemory 用显式依赖图（DAG）+ 预算化构建替代语义相似度检索，保证交给 agent 的上下文因果完整、可追溯。

## 快速开始

```bash
# 安装（Markdown 导入可用）
pip install -e .

# 安装代码骨架化支持（Python/JS/TS 文件导入需要）
pip install -e ".[code]"

# 重建索引
codememory --root examples/investment reindex

# 验证完整性（断链 / 循环 / schema / stale asset / 提案积压）
codememory --root examples/investment validate

# 找入口（词法排序检索）
codememory --root examples/investment search --query "半导体 持仓"

# 装配上下文（DAG 闭包 + 两遍式预算裁剪）
codememory --root examples/investment build user/investment/context --budget 2000
```

设置 `CODEMEMORY_ROOT` 环境变量可省略 `--root`：

```bash
export CODEMEMORY_ROOT=examples/investment
codememory reindex && codememory validate
```

## 启动完整应用

CodeMemory 提供本地 Operator UI（Graph / List / Dashboard / Review / Build / Golden Questions）。

```bash
cd frontend && npm install && cd ..
python bin/codememory.py dev
```

Windows / PowerShell 也可以直接使用根目录启动脚本：

```powershell
.\start.ps1
```

默认地址：

| 界面 | 地址 |
|------|------|
| 前端 UI（Graph + Dashboard） | http://127.0.0.1:5300 |
| Backend API | http://127.0.0.1:8000 |
| Swagger 文档 | http://127.0.0.1:8000/docs |

### Backend

```bash
# 直接启动（默认 dataset = investment）
python backend/server.py

# 指定默认数据集
CODEMEMORY_DEFAULT_DATASET=software-architecture python backend/server.py

# 指定端口
BACKEND_PORT=8010 python backend/server.py

# 或通过 uvicorn
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000
```

Backend 启动后访问 http://localhost:8000/docs 查看 Swagger API 文档。

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite 开发服务器默认监听 `127.0.0.1:5300`，并将 `/api` 代理到本地 FastAPI `8000` 端口。

## 核心概念

三组共 11 个概念（完整定义见 [docs/prd.md](docs/prd.md) 第 4 章）：

| 组 | 概念 | 代码对应物 |
|----|------|-----------|
| **静态结构** | repo（记忆库）、atom（记忆单元）、imports（依赖）、schema（结构契约）、asset（资产，不进依赖图） | git 仓库、模块、import 语句、接口、repo 里的 data/ |
| **动态操作** | build（装配）、check（校验）、search（入口检索）、test（黄金问题验证） | 构建 + tree-shaking、类型检查、符号搜索、测试/CI |
| **变更管理** | proposal（提案）、log（审计日志） | Pull Request、git log |

每个 atom 是一个 Markdown 文件（YAML frontmatter = 接口，body = 实现），通过 `imports` 显式声明依赖。写入有分级纪律：新增直写，没把握走 `create --propose`，修改已有 atom 走 `propose` patch 队列，owner 统一 `merge` / `reject`。

## 架构

三层结构（契约级定义见 [docs/architecture.md](docs/architecture.md)）：

| 层 | 组件 | 职责 |
|----|------|------|
| **Adapters** | `cli.py` / `evaluation/` / `tools.py` / `mcp_server.py` / `integrations.py` / `backend/` / `frontend/` | 参数/传输/呈现；显式 eval runner 只编排既有 build/test 契约 |
| **Core** | `build.py`（统一管线）、`models.py`、`search.py`、`validate.py`、`proposals.py`、`test_contract.py` 等 | 表示、装配、校验、变更管理 |
| **Importer** | `import_cmd.py` / `skeletonize/` / `compiler/` | 外部材料 → asset + atom proposals（一律经 review 晋升） |

agent 不在系统内——agent 是消费 build 产物、按写入纪律提交变更的运行时，永远经 adapter 调用。`harnesslib/` 与 `llm_gateway/` 是跨项目复用的可选编排层（上游维护）。

```
CodeMemory/
├── src/
│   ├── codememory/              # 记忆管理核心（结构详见 .claude/CLAUDE.md 文件架构）
│   │   └── evaluation/          # 显式三臂 eval runner；provider adapter 惰性加载
│   ├── harnesslib/              # 通用 Agent 编排（跨项目复用）
│   └── llm_gateway/             # 多 provider LLM 接入（跨项目复用）
├── backend/                     # REST adapter（FastAPI）
├── frontend/                    # Operator UI adapter（Vite）
├── examples/                    # 示例记忆库数据（独立于框架）
├── tests/                       # 单元 / API / 集成测试
└── docs/                        # canonical 文档 + plan/ + reference/
```

## CLI 命令速查

```bash
# 写路径（纪律见 docs/agent-memory-guide.md）
codememory create --id user/decisions/buy --schema schemas/decision --tags "investment" [--propose]
codememory update <id> --change-note "..." [--body ...] [--summary ...] [--import-required ...] [--source-ref <artifact_id>]
codememory propose <id> --reason "..." [--summary ...] [--body ...]   # 修改类提案入队
codememory proposals                                                  # 待审队列
codememory merge <id|proposal_id> | reject <id|proposal_id>           # owner 审阅

# 读路径
codememory search [--query <q>] [--tags <t>] [--type <t>] [--status <s>] [--has-imports] [--has-schema]
codememory build <id> [--depth required|recommended|full] [--budget N] [--format xml-markdown|markdown|plain-markdown|json]
codememory resolve <id> [...]        # build 的 plain-markdown 别名
codememory context-pack <id> [...]   # build 的别名
codememory source add <uri> [--id ID] [--summary "..."] | source list | source expand <id>

# 验证与维护
codememory reindex
codememory validate
codememory test <entry> [--budget N]                        # 导出黄金问题 + 装配上下文
codememory test report <entry> --results results.json      # 回写判分结果
codememory eval <entry> --llm-config gateway.yaml --answer-model smart --judge-model smart [--budget N] [--output report.json]
codememory orphans [--type <t>]
codememory changelog <id> | log [--limit N] | diff [--since "2 days ago"]
codememory suggest-deps <id> [--min-score N]

# 迁移（importer）—— 高质量导入用 agent 提炼范式（docs/agent-memory-guide.md 第 9 节）
codememory import --file notes.txt --extract preferences,decisions
codememory skeletonize <file_or_dir> [--min-weight N] [--dry-run] [--tags "a,b"]
codememory compile-md <corpus_dir> [--review-id <id>] [--namespace <ns>]
codememory materialize-review <review_id> [--accept-all]

# 辅助工具（REPL 草稿）
codememory snapshot <id> [--target <id>] [--budget N] [--from-dag <file>]
```

## Python API 速查

```python
from codememory import (
    # Memory operations
    create, update, resolve, search, validate, reindex,
    # Pipeline
    build_context_pack, render_context_pack, ContextPack,
    # Inspection
    find_orphans,
    # Transient reasoning
    TransientDAG, TransientNode,
    # Index
    load_index, save_index,
    # Core utilities
    parse_frontmatter, compute_body_hash, get_root_dir,
    # Integration
    CodememoryToolkit,
)

# One-line Agent integration
from codememory.integrations import CodememoryToolkit
toolkit = CodememoryToolkit(root="examples/investment")
tools = toolkit.get_tools_for_openai()  # standard root: exact 5-tool agent surface
```

Toolkit 与 MCP 共用同一 root-bound catalog：普通实例提供 `build_memory`、`search_memories`、`expand_source`、`create_memory`、`propose_memory`；Personal Profile 只追加 capture/read/maintenance/review 扩展。所有 schema 都不接受调用方传入 `root`，修改类 `propose_memory` 只写 proposal queue。

## 文档

- [产品需求](docs/prd.md) -- memory-as-code 公理、11 概念模型、写入纪律、非目标
- [架构设计](docs/architecture.md) -- 契约级参考：三层结构、数据契约、管线契约、收敛路径（已完成）
- [Agent 记忆指南](docs/agent-memory-guide.md) -- 记忆库贡献规范（agent 的 CONTRIBUTING.md）
- [项目结构](docs/project_structure.md) -- 当前文件职责与新代码落点
- [集成指南](docs/INTEGRATION.md) -- CLI / Python / MCP / Toolkit / REST 接入
- [用户指南](docs/USER_GUIDE.md) -- 日常使用、Personal Profile、维护和迁移
- [Roadmap / Sprint](docs/plan/FUTURE.md) -- 长期 backlog；当前任务见 [SPRINT](docs/plan/SPRINT.md)
- [Reference: Companion Mode](docs/reference/companion-mode.md) -- 历史探索，不代表 v1 方向

## 许可证

MIT -- 详见 [LICENSE](LICENSE)
