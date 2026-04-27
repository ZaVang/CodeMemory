# Sprint 5 — 集成与发布

> **起始日期**：2026-04-27
> **前置条件**：Sprint 4 完成（Layer 0 五个认知操作全部就绪）
> **目标**：新开发者 10 分钟跑通 demo；codememory 可被一行代码集成到任意 Agent 项目

---

## 一、现状评估

| 项目 | 状态 |
|------|------|
| README.md | 存在但过时（引用 `bin/codememory.py`，应改为 `python -m codememory.cli` / `pip install -e .`） |
| INTEGRATION.md | 不存在 |
| example_agent.py | 不存在 |
| integrations package | 不存在（无 `CodememoryToolkit`） |
| harnesslib docstrings | `harness.py`、`sandbox.py`、`event.py` 有少量注释，无 README |
| llm_gateway docstrings | `bridge.py`、`router.py` 有 docstring，但无独立的 README |

---

## 二、Sprint Backlog

### 任务 1：INTEGRATION.md — 集成指南 ✅

**产出一份让新开发者在 10 分钟内跑通 demo 的集成文档。**

| # | 子任务 | 说明 |
|---|--------|------|
| 1.1 | 快速开始 | pip install 方式、最小配置、一条命令验证安装 |
| 1.2 | 记忆库配置 | `--root` 参数、`CODEMEMORY_ROOT` 环境变量、`.codememory/index.json` 结构说明 |
| 1.3 | CLI 使用 | 8 个命令速查（create/resolve/reindex/validate/search/orphans/wander/snapshot）+ Layer 0 接口（overview/focus） |
| 1.4 | Sandbox 集成 | 如何注册 codememory tools 到 harresslib Sandbox：`await register_all(sandbox)` → 9 个 tool |
| 1.5 | 自定义 overview 模板 | `overview --format inject` 输出如何嵌入 system prompt |
| 1.6 | llm_gateway 配置 | `llm_gateway/config.yaml` 格式、API key 设置、model 选择 |

**产出**：`INTEGRATION.md`

**验收**：
```bash
test -f INTEGRATION.md && echo "OK" || echo "FAIL"
grep -c "^## " INTEGRATION.md  # 至少 5 个标题
```

---

### 任务 2：README.md 更新 ✅

**更新 README.md 以反映当前架构（`src/codememory/` package + `pip install -e .`）。**

| # | 子任务 | 说明 |
|---|--------|------|
| 2.1 | 快速开始更新 | `python bin/codememory.py` → `pip install -e . && codememory --root examples/investment reindex` |
| 2.2 | 架构图更新 | 引用 `src/codememory/` 包结构，标注四层架构 |
| 2.3 | CLI 命令速查 | 更新为当前 10 个命令 |
| 2.4 | Python API 速查 | `from codememory import resolve, create, search` |

**产出**：更新的 `README.md`

**验收**：
```bash
# 快速开始命令可运行
pip install -e . 2>&1 | tail -1
codememory --root examples/investment reindex && codememory --root examples/investment validate
```

---

### 任务 3：example_agent.py — 最小 Agent 示例 ✅

**一个 ~150 行的 Python 脚本，展示 codememory × harnesslib × llm_gateway 完整闭环。**

| # | 子任务 | 说明 |
|---|--------|------|
| 3.1 | 初始化 | 配置 codememory root + llm_gateway model + 注册 tools 到 Sandbox |
| 3.2 | 对话循环 | 模拟用户提问 → Agent 调用 search → 发现缺失 → create 新记忆 → resolve 验证 → 输出答案 |
| 3.3 | 自包含 | 不依赖外部 API key（使用 mock LLM 或跳过 LLM 调用，直接展示 tool 调用流程） |
| 3.4 | 可运行 | `PYTHONPATH=src python examples/example_agent.py` 可执行并输出完整对话日志 |

**产出**：`examples/example_agent.py`

**验收**：
```bash
PYTHONPATH=src python examples/example_agent.py 2>&1 | head -30
# 应输出模拟对话流程：search → create → resolve → 回答
```

---

### 任务 4：integrations 模块 — CodememoryToolkit ✅

**新增 `src/codememory/integrations.py`，提供一行代码注册到各类 Agent 框架。**

| # | 子任务 | 说明 |
|---|--------|------|
| 4.1 | `CodememoryToolkit` class | 封装 codememory root 配置 + 9 个 tool 的注册逻辑 |
| 4.2 | `register_to_sandbox(sandbox)` | 一行代码注册全部 codememory tools：`CodememoryToolkit(root="...").register_to_sandbox(sandbox)` |
| 4.3 | `get_tools_for_openai()` | 导出 OpenAI function calling 格式的 tool list（`[{"type": "function", "function": {...}}]`），AI 平台可直接消费 |
| 4.4 | `__init__.py` 导出 | `from codememory.integrations import CodememoryToolkit` |

**产出**：`src/codememory/integrations.py`，修改 `src/codememory/__init__.py`

**验收**：
```bash
# 模块可导入
PYTHONPATH=src python -c "from codememory.integrations import CodememoryToolkit; print('OK')"

# OpenAI 格式导出
PYTHONPATH=src python -c "
from codememory.integrations import CodememoryToolkit
tk = CodememoryToolkit(root='examples/investment')
tools = tk.get_tools_for_openai()
assert len(tools) == 9
assert tools[0]['type'] == 'function'
print(f'OK: {len(tools)} tools in OpenAI format')
"

# Sandbox 注册
PYTHONPATH=src python -c "
import asyncio
from harnesslib.sandbox import Sandbox
from codememory.integrations import CodememoryToolkit
async def t():
    s = Sandbox()
    tk = CodememoryToolkit(root='examples/investment')
    await tk.register_to_sandbox(s)
    names = [d.name for d in s.list_tools()]
    assert len(names) == 9
    print(f'OK: {names}')
asyncio.run(t())
"
```

---

### 任务 5：harnesslib + llm_gateway 关键 API 文档 ✅

**为两个通用组件补全 docstring 和模块级文档，确保独立可用。**

| # | 子任务 | 说明 |
|---|--------|------|
| 5.1 | harnesslib 模块 docstring | `__init__.py` 补充 Harness/Sandbox/Session 三个核心类的用途说明 + 最小示例 |
| 5.2 | llm_gateway 模块 docstring | `__init__.py` 补充 LLMBridge/Router 用途说明 + 最小示例 |
| 5.3 | Sandbox 关键方法 docstring | `sandbox.py` 的 `register()`/`execute()`/`list_tools()` 补充参数和返回值说明 |
| 5.4 | LLMBridge 关键方法 docstring | `bridge.py` 的 `chat()`/`chat_with_tools()` 补充参数和返回值说明 |

**产出**：修改 `src/harnesslib/__init__.py`、`src/llm_gateway/__init__.py`、`src/harnesslib/sandbox.py`、`src/llm_gateway/bridge.py`

**验收**：
```bash
# harnesslib 文档可查看
PYTHONPATH=src python -c "import harnesslib; help(harnesslib)" 2>&1 | head -20
PYTHONPATH=src python -c "import llm_gateway; help(llm_gateway)" 2>&1 | head -20
```

---

### 任务 6：全场景闭环测试 ✅

**模拟一个完整用户故事：用户分享偏好 → Agent 创建记忆 → 下次对话自动加载。**

| # | 验证项 | 说明 |
|---|--------|------|
| 6.1 | 场景 A：创建 + 检索 | create 一条 atom（偏好），search 能找到 |
| 6.2 | 场景 B：resolve 上下文 | resolve 一个含依赖的 composite，拓扑顺序正确 |
| 6.3 | 场景 C：update + stale | update body → overview 显示 stale → update summary → stale 消失 |
| 6.4 | 场景 D：wander 发现冷记忆 | wander 返回低 access_count 记忆 + 邻居 |
| 6.5 | 场景 E：snapshot 持久化 | TransientDAG → snapshot → composite .md 可被 resolve |
| 6.6 | 清理 | 所有测试记忆删除，reindex 回到 12 条 |

**产出**：测试脚本 `tests/integration_test.py`（自动执行上述 5 个场景）

**验收**：
```bash
PYTHONPATH=src python tests/integration_test.py
# 应输出 5 个场景全部 PASS
```

---

### 任务 7：回归验证 + 清理 ✅

**确保 Sprint 5 变更不破坏已有能力。**

| # | 验证项 |
|---|--------|
| 7.1 | 模块可导入（含 integrations） |
| 7.2 | `pip install -e .` 后 codememory CLI 全局可用 |
| 7.3 | reindex + validate 0 errors |
| 7.4 | resolve context 7 节点拓扑正确 |
| 7.5 | overview/focus/wander/orphans/snapshot 全部可用 |
| 7.6 | Sprint 1-4 验收命令不退化 |
| 7.7 | 清理集成测试文件 |

---

## 三、文件变更总览

```
新增：
  INTEGRATION.md                        # 集成指南
  examples/example_agent.py             # 最小 Agent 示例
  src/codememory/integrations.py        # CodememoryToolkit
  tests/integration_test.py             # 闭环测试

修改：
  README.md                             # 快速开始 + 架构图更新
  src/codememory/__init__.py            # 导出 CodememoryToolkit
  src/harnesslib/__init__.py            # 模块 docstring
  src/llm_gateway/__init__.py           # 模块 docstring
  src/harnesslib/sandbox.py             # 关键方法 docstring
  src/llm_gateway/bridge.py             # 关键方法 docstring

不修改（Sprint 1-4 完成的模块）：
  src/codememory/{core,create,update,index,resolve,validate,search,orphans,transient,snapshot,cli,tools}.py
```

---

## 四、验收命令汇总

```bash
# ── 模块导入 ──
PYTHONPATH=src python -c "from codememory import resolve, create, update, search, validate, reindex; from codememory.integrations import CodememoryToolkit; print('OK')"

# ── INTEGRATION.md 存在 ──
test -f INTEGRATION.md && echo "OK" || echo "FAIL"
grep -c "^## " INTEGRATION.md

# ── README 快速开始可运行 ──
pip install -e . 2>&1 | tail -1
codememory --root examples/investment reindex && codememory --root examples/investment validate

# ── example_agent.py 可运行 ──
PYTHONPATH=src python examples/example_agent.py 2>&1 | head -30

# ── CodememoryToolkit ──
PYTHONPATH=src python -c "
from codememory.integrations import CodememoryToolkit
tk = CodememoryToolkit(root='examples/investment')
tools = tk.get_tools_for_openai()
assert len(tools) == 9
print(f'OK: {len(tools)} tools in OpenAI format')
"

# ── harnesslib + llm_gateway 文档 ──
PYTHONPATH=src python -c "import harnesslib; help(harnesslib)" 2>&1 | head -5
PYTHONPATH=src python -c "import llm_gateway; help(llm_gateway)" 2>&1 | head -5

# ── 闭环集成测试 ──
PYTHONPATH=src python tests/integration_test.py

# ── 回归 ──
codememory --root examples/investment reindex
codememory --root examples/investment validate
codememory --root examples/investment resolve user/investment/context
codememory --root examples/investment orphans
codememory --root examples/investment wander --inject
codememory --root examples/investment overview
codememory --root examples/investment focus user/investment/risk-tolerance --level summary
```

---

## 五、风险

| 风险 | 缓解 |
|------|------|
| example_agent.py 依赖外部 LLM API | 使用 mock LLM handler，只验证 tool 调用流程，不依赖真实 API |
| integrations.py 与 tools.py 功能重叠 | integrations.py 是外观层（facade），内部委托 tools.py 的已有 handler，不重写逻辑 |
| harnesslib/llm_gateway 内部 API 不稳定 | 只补 docstring，不修改实现代码 |
| `pip install -e .` 引入未声明依赖 | pyproject.toml 的 dependencies 已梳理过，只新增确认已有依赖 |

---

## 六、完成定义

1. `INTEGRATION.md` ≥ 5 个标题，覆盖快速开始、CLI、Sandbox 集成、overview 模板、llm_gateway 配置
2. `README.md` 反映当前 `pip install -e .` + `src/codememory/` 架构
3. `example_agent.py`~150 行，`PYTHONPATH=src python examples/example_agent.py` 可直接运行
4. `from codememory.integrations import CodememoryToolkit` 可用，`get_tools_for_openai()` 返回 9 个 tool
5. harnesslib + llm_gateway 关键 API 有 docstring，`help()` 可查看
6. `tests/integration_test.py` 覆盖 5 个场景，全部 PASS
7. Sprint 1-4 回归全部通过
