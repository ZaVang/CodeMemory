# CodeMemory 后续路线图

> 从 Phase 1 原型 → 可嵌入任意 Agent 的通用记忆后端
>
> 设计哲学参见 [`docs/plans/IDEA.md`](IDEA.md)

---

## 零、系统全景：四层架构

CodeMemory 不是一个孤立工具——它和 `harnesslib`（编排）、`llm_gateway`（LLM 接入）组成完整的 Agent 后端栈。

### 四层关系

```
┌──────────────────────────────────────────────────┐
│          Layer 0：认知接口层（Agent 视角）           │
│  扫视 overview  │ 注视 focus  │ 残留 snapshot      │
│  重构 resolve   │ 触景生情 wander                  │
│  所有操作对 Agent 暴露为 bash 子命令                 │
├──────────────────────────────────────────────────┤
│            harnesslib（编排层）                     │
│  Harness: Effect 循环，yield 意图 → 基础设施执行     │
│  Sandbox: 工具注册/执行，所有工具统一 execute() 接口  │
│  Session: 追加写入事件流，系统唯一持久状态锚          │
│  Orchestration: 调度器，确保 session 被处理          │
├──────────────────────────────────────────────────┤
│            llm_gateway（LLM 接入层）                 │
│  LLMBridge: 统一入口，一行 chat() 调用任意模型       │
│  Router: API key 轮转 + 指数退避重试 + 动态 fallback │
│  CircuitBreaker: 熔断保护                           │
│  Skills: 加载 SKILL.md 注入 system prompt           │
│  Tools: BridgeTool 接口 + agentic tool loop         │
├──────────────────────────────────────────────────┤
│            codememory（记忆层）                      │
│  resolve: DAG → 拓扑排序 → token 裁剪 → 输出        │
│  create: 生成记忆模板 + 自动索引                     │
│  search: 按 tags/query/type/status 检索             │
│  validate: 循环检测 + 断链 + schema 合规             │
│  focus: 动态分辨率切换（zoom-in / zoom-out）         │
│  overview: 透明感知摘要，注入 system prompt          │
└──────────────────────────────────────────────────┘
```

### Layer 0 详解：五个认知基础操作

Layer 0 是 Agent 与记忆系统之间的**稳定接口**。它不定义实现，只定义 Agent 能"看见和操作"的认知原语。这些操作像 CPU 指令集一样保持稳定，后续版本只增不改。

| 认知行为 | 系统命令 | 触发方式 | 说明 |
|----------|----------|----------|------|
| **扫视** glance | `codememory overview --tags <t>` | 会话启动自动运行 | top 5 匹配记忆的 summary 注入 system prompt；Agent 不主动查就感知到 |
| **注视** focus | `codememory focus <id> --level full\|summary` | Agent 主动调用 | 对已加载 context 中某记忆动态 zoom-in/out，不重新 resolve |
| **残留** persist | 瞬态 DAG + `codememory snapshot <id>` | 会话中自动维护；snapshot 显式触发 | 会话推理链在内存中不落盘，snapshot 导出为 composite .md |
| **重构** reconstruct | `codememory resolve <id> --depth ... --budget ...` | Agent 主动调用 | DAG 拓扑拼装 + token 裁剪输出因果完整上下文 |
| **触景生情** recall | `codememory wander` / 联想搜索 | Agent 主动或系统偶尔自动 | 随机或关联激活一条冷记忆，模拟"气味触发回忆" |

### Agent 视角：只有 Bash

**Agent 不调用 Python API，不 import codememory，不直接读写 .md 文件。** Agent 视角下所有记忆操作都是 bash 子命令：

```bash
codememory overview --tags "investment"     # 扫视
codememory resolve user/investment/context  # 重构
codememory focus risk-tolerance --level full # 注视
codememory wander                          # 触景生情
codememory snapshot "session-001"          # 残留持久化
```

底层实现可以用 Python（处理 DAG、拓扑排序等复杂逻辑），但 Agent 只能通过 bash 调用。这与 Claude Code 的 `file edit` 和 `bash` 工具是同样的模式——壳是 bash，内部实现不限语言。

### 数据流：实现视角（Agent 一次对话的内部执行）

> Agent 只看到 Layer 0 的 bash 命令。下面的 harnesslib → llm_gateway → Sandbox → codememory 是实现细节，Agent 不感知。

```
User message
     │
     ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐
│ harnesslib  │────▶│ llm_gateway  │────▶│ OpenAI / Anthropic  │
│ Harness     │     │ LLMBridge    │     │ / Google            │
│ effect loop │◀────│ .chat()      │◀────│                     │
└──────┬──────┘     └──────────────┘     └─────────────────────┘
       │ yield ExecuteToolEffect
       ▼
┌─────────────┐
│ Sandbox     │
│ .execute()  │
├─────────────┤
│ 注册的工具：  │
│  create_memory    ← codememory
│  resolve_context  ← codememory
│  search_memory    ← codememory
│  focus_memory     ← codememory
│  update_memory    ← codememory
│  snapshot         ← codememory
│  ...              ← 项目自定义工具
└─────────────┘
```

### 关键：四层各自独立可替换

- **Layer 0** 是最稳定的接口层。它定义 Agent"能看见什么"，不定义下面怎么实现。换一套记忆后端，只要 bash 命令名不变，Agent 无感知。
- **harnesslib** 通用编排，不感知 LLM provider 也不感知记忆格式。换个项目照样用。
- **llm_gateway** 只做 LLM 接入，不关心上层是预测 pipeline 还是记忆系统。
- **codememory** 只做记忆管理，不关心 LLM 怎么调用、Agent 怎么编排。

四者唯一的交汇点：**Sandbox + bash CLI**。codememory 把自己的函数注册为 Sandbox 的 tool，同时每个 tool 有对应的 bash 命令。harnesslib 的 Effect 循环驱动 LLM ↔ tool 交替执行。

---

## 一、Phase 2A：框架化 + 数据分离（第 1 周）

> 前置条件：Phase 1 原型已跑通

### 当前问题

- `bin/codememory.py`（框架）与 `user/`、`self/`、`schemas/`（具体用户数据）混在一起
- 框架无法 `pip install`，换一个用户就要 fork 整个 repo
- `user/investment/` 是 demo 数据，占据项目根目录
- codememory 的函数无法被 harnesslib Sandbox 直接注册（耦合在 CLI 里）

### 目标目录结构

```
CodeMemory/                          # 平台 monorepo
├── src/
│   ├── harnesslib/                  # 通用 Agent 编排（跨项目复用）
│   │   ├── harness.py               #   Harness: Effect 循环
│   │   ├── sandbox.py               #   Sandbox: 工具注册/执行
│   │   ├── event.py                 #   Event + SessionBase
│   │   ├── orchestration.py         #   调度器
│   │   ├── _tracing.py              #   调用追踪
│   │   ├── resources.py             #   资源管理
│   │   └── prompt_engine.py         #   提示词引擎
│   ├── llm_gateway/                 # 多 provider LLM 接入（跨项目复用）
│   │   ├── bridge.py                #   LLMBridge: 统一入口
│   │   ├── config.py                #   YAML 配置加载
│   │   ├── models.py                #   Pydantic 数据模型
│   │   ├── router.py                #   重试 + fallback
│   │   ├── circuit_breaker.py       #   熔断器
│   │   ├── skills.py                #   Skill 加载器
│   │   ├── providers/               #   OpenAI / Anthropic / Google 适配器
│   │   └── tools/                   #   BridgeTool 接口
│   └── codememory/                  # 记忆管理（本项目核心）
│       ├── __init__.py              #   Public API
│       ├── core.py                  #   frontmatter 解析, body hash, token 估算
│       ├── index.py                 #   Index 加载/保存/reindex
│       ├── resolve.py               #   DAG 构建 + 拓扑排序 + token 裁剪
│       ├── validate.py              #   循环检测 + 断链 + schema 合规
│       ├── create.py                #   记忆模板生成
│       ├── search.py                #   检索（tags/query/type/status）
│       ├── cli.py                   #   薄 argparse 壳
│       └── tools.py                 #   harnesslib Sandbox 工具注册
├── examples/
│   └── investment/                  # Demo: 投资决策记忆库
│       ├── codememory.yaml          #   记忆库配置
│       ├── user/investment/         #   7 个示例记忆
│       └── schemas/decision.md
├── bin/
│   ├── codememory                   # bash wrapper
│   └── codememory.ps1
├── docs/
├── tests/
├── pyproject.toml
├── README.md
└── INTEGRATION.md
```

### Epic 0：架构重构

| # | 任务 | 产出 | 验证 |
|---|------|------|------|
| 0.1 | 从 `bin/codememory.py` 提取 `src/codememory/` package | 8 个模块（core/index/resolve/validate/create/search/cli/tools），每个 < 200 行 | `from codememory import resolve` 可导入 |
| 0.2 | `pyproject.toml` + 可编辑安装 | `pip install -e .` 后 `codememory` 命令全局可用 | `codememory --root /tmp/test-memories validate` |
| 0.3 | 记忆数据迁出框架根目录 | 现有 `user/` `self/` `schemas/` → `examples/investment/` 下 | 仓库根目录干净，无用户数据 |
| 0.4 | harnesslib + llm_gateway 路径规范化 | 保持在 `src/` 下，确认 import 路径一致；清理 `_agents/` 等残留 | `from harnesslib import Harness, Sandbox` 可导入 |
| 0.5 | codememory 注册为 harnesslib tool | `src/codememory/tools.py`：将 create/resolve/search/focus 封装为 Sandbox-compatible handler | harness 启动后 Agent 可通过 function calling 调用 codememory |
| 0.6 | 迁移现有测试场景 | `examples/investment/` 下独立运行 reindex → validate → resolve | 6 个 Phase 1 验证测试结果一致 |

### 0.5 的实现概要：tools.py

```python
# src/codememory/tools.py
from harnesslib.sandbox import ToolDefinition

CODEMEMORY_TOOLS = [
    ToolDefinition(
        name="create_memory",
        description="创建一条新记忆。type: atom|instance|composite",
        input_schema={...},
    ),
    ToolDefinition(
        name="resolve_context",
        description="解析记忆的完整上下文，按依赖顺序加载",
        input_schema={...},
    ),
    ToolDefinition(
        name="search_memory",
        description="按 tags/关键词/类型 搜索记忆",
        input_schema={...},
    ),
]

# 注册到 Sandbox
# sandbox.register(CODEMEMORY_TOOLS[0], handler=create_memory_handler)
```

### 重构后的三种使用方式

```bash
# 1. CLI（独立使用）
codememory --root ./my-memories resolve user/investment/context

# 2. Python API（脚本中使用）
from codememory import resolve
context = resolve("user/investment/context", root="./my-memories")

# 3. harnesslib tool（Agent 使用）
# Agent 在对话中直接调用 create_memory / resolve_context / search_memory
```

---

## 二、Phase 2B：Agent 自主维护记忆（第 1-2 周）

> 前置条件：Phase 2A 完成（codememory 可在 Sandbox 中注册）

### Epic 1：记忆创建与更新

| # | 任务 | 产出 | 验证 |
|---|------|------|------|
| 1.1 | `agent-memory-guide.md` — Agent 决策树 | 文档：何时创建 atom/composite/instance、如何声明依赖、如何评估 intensity、如何写 summary | 对照 3 个对话场景，Agent 选择正确原语 |
| 1.2 | `create` 增强 — intensity 字段 | `intensity` (1-10) 写入 frontmatter；≥ 8 标记 `protected: true` | 创建 intensity=9 的记忆，检查 protected |
| 1.3 | `create` 增强 — Agent 预览模式 | `--dry-run` 输出 frontmatter 预览，Agent 确认后再写入 | Agent 说"创建记忆"→ 预览 → 修改 summary → 确认 |
| 1.4 | `update` 命令 | 递增 version，强制 `change_note`，自动更新 `summary_hash` | 更新 risk-tolerance，version 正确递增 |
| 1.5 | 瞬态记忆 DAG | 内存 `TransientDAG`，会话推理链可 resolve 不落盘 | 建 3 个临时 atom，resolve 正常输出 |
| 1.6 | `snapshot` 命令 | 瞬态 DAG 导出为 composite .md，自动声明依赖 | snapshot → `user/snapshots/2026-04-24-001.md` |

### Agent 工具签名

```python
def create_memory(
    type: Literal["atom", "instance", "composite"],
    id: str,
    summary: str,
    intensity: int = 5,
    schema: str | None = None,
    imports: dict | None = None,
    tags: list[str] | None = None,
    dry_run: bool = False,
) -> MemoryCreated | FrontmatterPreview

def update_memory(
    id: str,
    change_note: str,
    body: str | None = None,
    summary: str | None = None,
    imports: dict | None = None,
    status: str | None = None,
) -> MemoryUpdated

def snapshot(
    id: str,
    summary: str,
    nodes: list[str],
) -> MemoryCreated
```

---

## 三、Phase 2C：智能检索与自然遗忘（第 2 周）

> 前置条件：Phase 2B 完成（需要 access_count 统计）

### Epic 2：检索与遗忘

| # | 任务 | 产出 | 验证 |
|---|------|------|------|
| 2.1 | `search` 命令增强 | `--query`（summary 模糊匹配）、`--tags`、`--type`、`--status`；按被依赖数 + access_count 降序 | 搜索"调仓"返回 context composite 在顶部 |
| 2.2 | access_count + 热度衰减 | index.json 记录 `access_count` + `last_access`；`list --sort-by heat` | 多次 resolve 后 count 增长，冷记忆排末位 |
| 2.3 | `orphans` 命令 | 列出所有入度为 0 的 atom，标注 intensity 和 last_access | 运行 orphans 显示从未被引用的旧想法 |
| 2.4 | `wander` 命令 | 随机选一个低 access_count 记忆，展示邻居依赖 | 执行 wander 返回冷记忆 + 关联记忆预览 |
| 2.5 | 衰减建议（validate 扩展） | 低 access_count + 低 intensity + 无入边 → warn | validate 输出针对特定记忆的衰减建议 |
| 2.6 | protected 机制 | intensity ≥ 8 → `protected: true`，所有衰减逻辑跳过 | 高强度记忆在 orphans 列表中无衰减警告 |

### 遗忘规则

```
if intensity >= 8:         → skip    （"车祸"级记忆，永不衰减）
elif access_count > 0 and last_access within 30d: → skip
elif in_degree > 0:        → skip    （被引用中）
else:                      → warn "建议重新关联"
```

系统只建议，不自动删除。遗忘由依赖图结构自然发生。

---

## 四、Phase 2D：Layer 0 认知接口层（第 2-3 周）

> 前置条件：Phase 2C 完成
>
> 设计理念：IDEA.md §2 "透明玻璃与雨水"、§5 "视觉残留与重构"、§6 "双焦距与分辨率层级"
>
> Layer 0 是 Agent 与记忆系统之间的稳定接口。实现后这五个认知操作像 CPU 指令集一样保持稳定，后续只增不改。

### Epic 3：五个认知基础操作

| # | 认知行为 | 任务 | 产出 | 验证 |
|---|----------|------|------|------|
| 3.1 | **扫视** glance | `overview` 命令 | 生成与当前对话 tags 匹配的 top 5 记忆的 summary + status + heat，嵌入 Agent system prompt | Agent 新会话直接说"我知道你的半导体主线判断"，无需调用 search |
| 3.2 | **注视** focus | `focus` 工具 | 对已加载 context 中某记忆 zoom-in（全文）/ zoom-out（summary），不重新 resolve | Agent："把 risk-tolerance 全文加载进来"→ 该记忆展开，其余保持 summary |
| 3.3 | **重构** reconstruct | 被动提醒 + 自动分辨率 | resolve 时检测 summary_hash 过期、pin 版本落后 → `[NOTICE]`；token 紧张时自动降级非 required 节点 | 改 body 不改 summary → 下次 resolve 输出 stale 提醒；budget=300 → 远景模式 |
| 3.4 | **残留** persist | 瞬态 DAG 维护 | 会话推理链在内存中维护为 `TransientDAG`，可被 resolve 引用但不落盘 | 对话中建 3 个临时 atom，resolve 正常输出，会话结束后消失 |
| 3.5 | **触景生情** recall | `wander` 自动触发 | 系统偶尔自动注入一条低 access_count 冷记忆到 Agent 的 system prompt 边缘 | Agent："说到这个我突然想起你之前提过…" |

---

## 五、Phase 2E：集成与发布（第 3 周）

> 前置条件：Phase 2D 完成

### Epic 4：对外接口

| # | 任务 | 产出 | 验证 |
|---|------|------|------|
| 4.1 | `INTEGRATION.md` | 完整集成指南：配置记忆库路径、注册工具到 Sandbox、自定义 overview 模板、llm_gateway 配置 | 新开发者按文档 10 分钟跑通 demo |
| 4.2 | 最小 Agent 示例 | 一个 `example_agent.py`（~150 行）：用 harnesslib + llm_gateway + codememory 跑完整闭环 | Agent 自主创建记忆 → resolve 上下文 → 回答用户问题 |
| 4.3 | OpenAI/LangChain tool 封装 | `CodememoryToolkit`，一行代码注册 create/search/resolve/focus | `from codememory.integrations import CodememoryToolkit` |
| 4.4 | 全场景闭环测试 | 模拟完整对话：用户提问 → Agent 查记忆 → 发现缺失 → 创建 → resolve 验证 → 追问 → search 关联 | 测试覆盖全部 4 个用户故事 |
| 4.5 | harnesslib + llm_gateway 文档补全 | 给两个通用组件补 README + docstring 示例，确保独立可用 | 在其他项目中 `from harnesslib import Harness` 可直接使用 |

---

## 六、时间线

```
Week 1 ─┬─ Phase 2A: 架构重构（Epic 0）
        └─ Phase 2B: Agent 自主维护（Epic 1 开始）

Week 2 ─┬─ Phase 2B: Agent 自主维护（Epic 1 完成）
        ├─ Phase 2C: 智能检索与遗忘（Epic 2）
        └─ Phase 2D: 透明接口（Epic 3 开始）

Week 3 ─┬─ Phase 2D: 透明接口（Epic 3 完成）
        └─ Phase 2E: 集成与发布（Epic 4）
```

---

## 七、完成定义

1. `pip install -e .` 可安装 codememory，`--root` 指向任意记忆数据目录
2. Layer 0 五个认知操作全部可用：`overview` / `focus` / `resolve` / `wander` / `snapshot` 作为 bash 命令
3. codememory 工具可通过 harnesslib Sandbox 注册，Agent 在对话中自主调用
4. `src/harnesslib/` + `src/llm_gateway/` + `src/codememory/` + Layer 0 bash CLI 四层各自独立
5. Agent 可自主创建/更新记忆，正确声明依赖与强度
6. 新会话中 Agent 无需调用工具即通过 overview 感知相关记忆，通过 focus 调整分辨率
7. 孤立记忆可被发现，系统提供衰减建议但不自动删除；高强度记忆受保护
8. `INTEGRATION.md` 让第三方开发者在 10 分钟内接入
9. `examples/investment/` 作为独立 demo 可一键体验

---

## 八、风险与缓解

| 风险 | 缓解 |
|------|------|
| 重构破坏现有功能 | Phase 1 的 6 个验证测试全部保留为回归测试 |
| harnesslib/llm_gateway 的 Deep Thought 残留假设混入 codememory | 三个 package 各自独立，codememory 不 import 另外两个（只在 tools.py 中适配接口） |
| Agent 自动创建记忆依赖声明不准确 | `agent-memory-guide.md` 给明确规则；`validate` 事后检查 |
| overview 注入使 system prompt 过长 | 限制 top 5，仅 summary + id；Agent 通过 focus 按需拉取全文 |
| 不同平台 tool 调用格式差异 | 先适配 OpenAI/Claude function calling；抽象 `BaseToolkit` |
| 瞬态记忆与持久记忆边界模糊 | 瞬态 DAG 严格限定当前会话，snapshot 需显式执行 |

---

## 九、与 IDEA.md 的映射

| IDEA.md 洞察 | 对应 Phase |
|--------------|-----------|
| §1 代码即因果模型 | Phase 2A（DAG 是框架核心数据结构） |
| §2 透明玻璃与雨水 | **Layer 0**（overview = 透明玻璃，focus = 雨水可见时的调焦） |
| §3 触景生情与不可达 | Phase 2C（orphans + wander = 人工触景）+ **Layer 0 触景生情** |
| §4 单词与车祸：记忆强度 | Phase 2B（intensity + protected） |
| §5 视觉残留与重构 | Phase 2B（瞬态 DAG）+ **Layer 0 残留（snapshot）** |
| §6 双焦距与分辨率层级 | **Layer 0**（focus 工具 + 自动分辨率切换） |
| §7 让环境适应 LLM | Phase 2A（bash CLI + Markdown + Python package） |
| §8 自组织记忆生态 | Phase 2C（遗忘由依赖图结构决定，不由系统裁决） |

---

## 十、Phase 3：工程化与打磨

> 前置条件：Phase 2E 完成
>
> Phase 2 实现了完整的记忆功能闭环。Phase 3 消灭已知技术债务，提升代码质量，为独立发布做准备。

### Phase 3A：代码质量（第 1 周）

| # | 任务 | 产出 | 验证 |
|---|------|------|------|
| 3A.1 | cli/tools handler 去重 | `src/codememory/handlers.py`：所有命令的共享 handler，cli 和 tools 都委托给它 | 新增命令只需写一份逻辑；cli.py 回到 150 行以内 |
| 3A.2 | Pydantic v2 数据模型 | `src/codememory/models.py`：`MemoryEntry`、`IndexData`、`ImportRef`、`ChangeLogEntry` 等 BaseModel | 序列化/反序列化走 `model_dump(mode="json")`，IDE 补全生效 |
| 3A.3 | print() → logging | 所有 `print(x, file=sys.stderr)` → `logging.warning()`/`logging.error()`；stdout 输出保留 `print()` | 可控制日志级别；resolve notice 走 stderr，正文走 stdout |

### Phase 3B：功能深化（第 1-2 周）

| # | 任务 | 产出 | 验证 |
|---|------|------|------|
| 3B.1 | 示例记忆 hash 修复 | 8 个样例文件 + index.json 中的 `summary_hash` 全部更新为真实值 | `overview` 无 `[stale]` 误报 |
| 3B.2 | `changelog` 命令 | `codememory changelog <id>` 输出该记忆的 change_log 历史（按时间倒序） | 查看 risk-tolerance 的版本变更轨迹 |
| 3B.3 | wander 加权概率 | 当前"最低 1/3 等概率"改为加权随机：`weight = 1 / (access_count + 1)`，冷记忆更容易被选中，但不完全排除热门记忆 | 多次 wander 结果多样性优于当前硬切 1/3 |
| 3B.4 | snapshot 统一 | `snapshot --target` 内部自动构建临时 DAG（委托 resolve 逻辑），消除与 `--from-dag` 的两条代码路径 | `snapshot <id>` 等价于 `snapshot <id> --target <id>`；snapshot.py 逻辑砍半 |
| 3B.5 | `--format json` | 所有 CLI 命令支持 `--format json`：`resolve --format json`、`search --format json`、`overview --format json` | 输出机器可读 JSON，程序化集成不依赖文本解析 |

### Phase 3C：测试体系（第 2 周）

| # | 任务 | 产出 | 验证 |
|---|------|------|------|
| 3C.1 | resolve.py 单元测试 | `tests/unit/test_resolve.py`：DAG 构建、拓扑排序、循环检测、token 裁剪 | 10+ 纯函数测试，不依赖文件系统 |
| 3C.2 | validate.py 单元测试 | `tests/unit/test_validate.py`：断链检测、schema 合规、衰减建议规则 | 覆盖 4 条衰减规则的边界 |
| 3C.3 | create/update 集成测试 | `tests/unit/test_create_update.py`：protected 自动标记、version 递增、summary_hash 计算 | 临时目录隔离，不污染 examples |
| 3C.4 | 边界测试 | 空记忆库、循环依赖、超大 budget、零 budget、缺失 imports | 所有边界不抛异常，输出合理错误信息 |

### Phase 3D：独立发布（第 3 周）

| # | 任务 | 产出 | 验证 |
|---|------|------|------|
| 3D.1 | harnesslib 独立 pip 包 | `src/harnesslib/` 有独立 `pyproject.toml`、`README.md`、CI 配置 | `pip install harnesslib` 可在其他项目使用 |
| 3D.2 | llm_gateway 独立 pip 包 | `src/llm_gateway/` 有独立 `pyproject.toml`、`README.md`、CI 配置 | `pip install llm-gateway` 可在其他项目使用 |
| 3D.3 | codememory 0.2.0 发布 | `pyproject.toml` 版本号、changelog、`pip install codememory` 可安装 | 新用户 `pip install codememory && codememory --root my-memories reindex` |
| 3D.4 | LangChain/Anthropic tool 适配 | `integrations.py` 追加 `get_tools_for_anthropic()`（tool_use 格式）、`get_tools_for_langchain()`（BaseTool 列表） | 三个主流 Agent 框架各一行代码集成 |

---

## Phase 3 与 IDEA.md 的映射

| IDEA.md 洞察 | 对应 Phase |
|--------------|-----------|
| §7 让环境适应 LLM | Phase 3A（handler 架构 + Pydantic + logging — 代码本身也更易被 LLM 理解和维护） |
| §8 自组织记忆生态 | Phase 3B（changelog 可见历史、snapshot 统一 — 系统行为更可解释、可调试） |
| — 工程基础 | Phase 3C（测试体系 — 所有后续迭代的安全网） |
| — 生态分发 | Phase 3D（独立发布 — codememory 从 monorepo 内组件变为独立可安装的 pip 包） |
