# CodeMemory

**记忆原子化协议** -- 将 AI 记忆拆分为可依赖解析的原子单元。

记忆加载是依赖解析问题，不是搜索问题。CodeMemory 用显式依赖图（DAG）替代语义相似度检索，保证加载的上下文因果完整。

## 快速开始

```bash
# 安装
pip install -e .

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

## 核心概念

记忆被拆分为四种**原语**：

| 类型 | 说明 | 可被引用 | 有 imports |
|------|------|---------|-----------|
| **atom** | 不可再分的原子事实 | 是 | 否 |
| **instance** | 依附 schema 的决策/事件 | 是 | 是（required） |
| **composite** | 组合其他记忆的上下文包 | 是 | 是（required/recommended/related） |
| **schema** | 定义 instance 结构的元模板 | 是（instance 通过 schema 引用） | 否 |

每个记忆是一个 Markdown 文件（YAML frontmatter + body），通过 `imports` 显式声明依赖关系。记忆加载是 DAG 解析问题，不是 vector search。

## 架构

```
CodeMemory/
├── src/
│   ├── codememory/              # 记忆管理核心（本项目）
│   │   ├── __init__.py          # Public API
│   │   ├── core.py              # frontmatter 解析, body hash
│   │   ├── index.py             # Index 加载/保存/reindex
│   │   ├── resolve.py           # DAG + 拓扑排序 + token 裁剪
│   │   ├── validate.py          # 循环检测 + 断链 + schema 合规
│   │   ├── create.py            # 记忆模板生成
│   │   ├── update.py            # 版本控制 + change tracking
│   │   ├── search.py            # 检索
│   │   ├── orphans.py           # 孤立记忆检测
│   │   ├── transient.py         # 瞬态 DAG（会话内推理链）
│   │   ├── snapshot.py          # TransientDAG → persistent .md
│   │   ├── integrations.py      # CodememoryToolkit（一行注册）
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
│   └── integration_test.py      # 5 场景闭环集成测试
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
codememory create --type atom --id user/ideas/my-thesis --tags "ai"
codememory update <id> --change-note "..." [--body ...] [--summary ...] [--status ...]

# 检索
codememory resolve <id> [--depth required|recommended|full] [--budget N]
codememory search [--query <q>] [--tags <t>] [--type <t>] [--status <s>]

# 维护
codememory reindex
codememory validate
codememory orphans [--type <t>] [--min-intensity N]

# Layer 0 认知操作
codememory overview [--tags <t>] [--limit N] [--format default|inject] [--with-recall]
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

- [集成指南](INTEGRATION.md) -- 10 分钟上手集成
- [架构设计](docs/architecture.md)
- [已知陷阱](docs/plans/pitfalls.md)

## 许可证

MIT -- 详见 [LICENSE](LICENSE)
