# CodeMemory

**记忆原子化协议** -- 将 AI 记忆拆分为可依赖解析的原子单元。

记忆加载是依赖解析问题，不是搜索问题。CodeMemory 用显式依赖图（DAG）替代语义相似度检索，保证加载的上下文因果完整。

## 快速开始

```bash
# 安装（Markdown 导入可用）
pip install -e .

# 安装代码骨架化支持（Python/JS/TS 文件导入需要）
pip install -e ".[code]"

# 重建索引
codememory --root examples/investment reindex

# 验证完整性
codememory --root examples/investment validate

# 加载投资决策上下文（DAG 拓扑拼装）
codememory --root examples/investment resolve user/investment/context

# 查看记忆概览
codememory --root examples/investment overview --limit 5
```

设置 `CODEMEMORY_ROOT` 环境变量可省略 `--root`：

```bash
export CODEMEMORY_ROOT=examples/investment
codememory reindex && codememory validate
```

## 启动完整应用

CodeMemory 提供 Web 管理面板（Graph 视图 + Dashboard + CRUD 表单）。

### Backend

```bash
# 直接启动（默认 root = examples/investment）
python backend/server.py

# 指定记忆数据集
CODEMEMORY_ROOT=examples/all python backend/server.py

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

Vite 默认监听 5173 端口；端口被占用时自动选择下一个可用端口（关注终端输出中的实际 URL）。

### 访问地址

| 界面 | 地址 |
|------|------|
| 前端 UI（Graph + Dashboard） | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger 文档 | http://localhost:8000/docs |

## 核心概念

记忆有两种**原语**：

| 类型 | 说明 |
|------|------|
| **atom** | 通用记忆——角色通过 `imports`、`schema`、`tags`、目录表达，不靠 type 区分 |
| **schema** | 元模板——定义记忆结构（如决策模板、会议模板），atom 通过 `schema` 字段引用 |

每个记忆是一个 Markdown 文件（YAML frontmatter + body），通过 `imports` 显式声明依赖关系。记忆加载是 DAG 解析问题，不是 vector search。

## 架构

```
CodeMemory/
├── src/
│   ├── codememory/              # 记忆管理核心（本项目）
│   │   ├── __init__.py          # Public API
│   │   ├── core.py              # frontmatter 解析, body hash, logging
│   │   ├── models.py            # Pydantic v2 数据模型
│   │   ├── handlers.py          # 统一命令处理（cli + tools 共享）
│   │   ├── index.py             # Index 加载/保存/reindex
│   │   ├── resolve.py           # DAG + 拓扑排序 + token 裁剪
│   │   ├── validate.py          # 循环检测 + 断链 + schema 合规 + 衰减建议
│   │   ├── create.py            # 记忆模板生成
│   │   ├── update.py            # 版本控制 + change tracking
│   │   ├── search.py            # 检索
│   │   ├── orphans.py           # 孤立记忆检测
│   │   ├── changelog.py         # 变更历史查看
│   │   ├── transient.py         # 瞬态 DAG（会话内推理链）
│   │   ├── snapshot.py          # TransientDAG -> persistent .md
│   │   ├── log.py                # 全局追加审计日志
│   │   ├── import_cmd.py         # 冷启动文本导入
│   │   ├── suggest_deps.py       # 自动依赖推断（三层过滤）
│   │   ├── skeletonize/          # 结构化批量导入
│   │   │   ├── common.py         # intensity 解析 + 文本工具
│   │   │   ├── markdown.py       # Markdown 节拆分 + 骨架化
│   │   │   └── code.py           # 代码骨架化（Python/JS/TS，Tree-sitter）
│   │   ├── integrations.py      # CodememoryToolkit（OpenAI/Anthropic/Gemini）
│   │   ├── cli.py               # argparse CLI 壳
│   │   └── tools.py             # Sandbox tool 注册
│   ├── harnesslib/              # 通用 Agent 编排（跨项目复用）
│   │   ├── harness.py           # Agent 主循环
│   │   ├── sandbox.py           # 工具执行环境
│   │   └── event.py             # 事件总线
│   └── llm_gateway/             # 多 provider LLM 接入（跨项目复用）
│       ├── bridge.py            # LLMBridge 统一入口
│       ├── router.py            # 重试/fallback/负载均衡
│       ├── models.py            # Pydantic 数据模型
│       ├── providers/           # Provider 适配器
│       └── tools.py             # 内置工具（文件读取等）
├── examples/
│   ├── investment/              # 示例：投资决策记忆库（12 条记忆）
│   └── example_agent.py         # 最小 Agent 示例（mock LLM）
├── tests/
│   ├── unit/                     # 108 个单元测试
│   └── integration_test.py      # 24 个集成测试
├── docs/
├── pyproject.toml
└── INTEGRATION.md               # 集成指南（10 分钟上手）
```

### 四层架构

| 层 | 组件 | 职责 |
|----|------|------|
| **Agent 应用** | `example_agent.py`, your app | 业务逻辑 + 对话循环 |
| **集成外观** | `CodememoryToolkit` | 一行代码注册全部记忆工具 |
| **记忆引擎** | `codememory` package | DAG 解析, 拓扑拼装, stale 检测 |
| **编排 + LLM** | `harnesslib` + `llm_gateway` | Agent 循环, 多 provider, 重试/fallback |

## CLI 命令速查

```bash
# 记忆生命周期
codememory create --id user/ideas/my-thesis --tags "ai"         # 默认 type=atom
codememory create --type schema --id schemas/my-template --tags "template"
codememory create --id user/decisions/buy --schema schemas/decision --tags "investment"
codememory update <id> --change-note "..." [--body ...] [--summary ...] [--status ...]

# 检索
codememory resolve <id> [--depth required|recommended|full] [--budget N] [--focus decision]
codememory search [--query <q>] [--tags <t>] [--type <t>] [--status <s>] [--maturity proven] [--semantic-type decision]
codememory search --has-imports          # 有依赖的记忆
codememory search --has-schema           # 有 schema 引用的记忆

# 维护
codememory reindex
codememory validate
codememory orphans [--type <t>] [--min-intensity N]
codememory changelog <id>
codememory log [--limit N]

# 导入
codememory import --file notes.txt --extract preferences,decisions
codememory import --stdin --extract facts
codememory skeletonize <file_or_dir> [--min-intensity N] [--dry-run] [--tags "a,b"]

# 依赖推断
codememory suggest-deps <id> [--min-score N] [--forward-only] [--retroactive-only]

# Layer 0 认知操作
codememory overview [--tags <t>] [--limit N] [--format default|inject] [--with-recall] [--min-maturity verified]
codememory focus <id> --level full|summary [--resolve] [--content ...]
codememory wander [--mode cool|random] [--inject]
codememory snapshot <id> [--target <id>] [--budget N] [--from-dag <file>]
```

## Python API 速查

```python
from codememory import (
    # Memory operations
    create, update, resolve, search, validate, reindex,
    # Inspection
    find_orphans,
    # Transient reasoning
    TransientDAG, TransientNode,
    # Index
    load_index, save_index,
    # Skeletonize
    skeletonize_markdown, Section,
    # Core utilities
    parse_frontmatter, compute_body_hash, get_root_dir,
    # Integration
    CodememoryToolkit,
)

# One-line Agent integration
from codememory.integrations import CodememoryToolkit
toolkit = CodememoryToolkit(root="examples/investment")
tools = toolkit.get_tools_for_openai()  # -> OpenAI format tool list
```

## 文档

- [集成指南](docs/INTEGRATION.md) -- 10 分钟上手集成
- [Layer 0 认知接口原理](docs/layer0-cognitive-interface.md) -- 五个认知操作为什么这样设计
- [Agent 记忆指南](docs/agent-memory-guide.md) -- 对话中自主维护记忆的决策树
- [架构设计](docs/architecture.md)
- [与团队知识库方案互操作](docs/interop-with-team-knowledge.md) -- 五层目录、语义分类、成熟度对照
- [已知陷阱](docs/plans/pitfalls.md)

## 许可证

MIT -- 详见 [LICENSE](LICENSE)
