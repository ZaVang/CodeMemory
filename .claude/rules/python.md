---
description: Python coding standards — applies to all .py files in this project
paths:
  - "**/*.py"
---

# Python 开发规范

## 技术栈

- Python 3.13+，核心依赖：`pyyaml>=6.0`、`pydantic>=2.0`
- 核心实现：`src/codememory/` package（16 个模块）
- 命令处理：`handlers.py` 统一业务逻辑，`cli.py`（薄 argparse 壳，< 200 行）和 `tools.py`（Sandbox handler 委托）各司其职

## 代码组织

- handlers.py 是唯一的业务逻辑入口——新增命令只改它
- cli.py 只做 argparse 解析 + delegate 给 handler
- tools.py 只做 async wrapper + delegate 给 handler
- 所有公共函数类型注解覆盖
- 函数命名：动词开头（`handle_create`, `compute_body_hash`, `build_dag`）

## 数据模型

- 模块间 API 边界用 Pydantic v2 BaseModel（`models.py`）
- `MemoryEntry`：单条记忆的全部字段
- `IndexData`：index.json 的内存表示（`memories: dict[str, MemoryEntry]`）
- 序列化走 `model_dump(mode="json")`
- 禁止 Pydantic v1 API（`.dict()`, `class Config`, `schema()`）
- 禁止裸 `dict` 作为模块间 API 边界
- 搜索函数返回 `dict` 列表（兼容旧调用者），handler 层需处理 `getattr` / `.get()` 双兼容

## 日志

- 系统日志走 `logging` 模块：`logging.warning()` / `logging.error()` / `logging.info()`
- 用户可见正文走 `print()`（stdout）
- CLI 全局参数 `--verbose`（INFO+）/ `--quiet`（ERROR+）
- 默认级别 WARNING

## 文件格式

- 记忆文件 = YAML frontmatter（`---` 分隔） + Markdown body
- frontmatter 修改不触发 stale：body hash 基于 body 文本计算
- 编码统一 UTF-8

## 禁止事项

- 禁止硬编码文件路径（通过 `--root` 参数或 `CODEMEMORY_ROOT` 环境变量）
- 禁止在 resolve 输出中混入 debug 信息（debug 走 stderr/logging）
- 禁止不声明理由新增第三方依赖
- 禁止修改 `src/harnesslib/` 或 `src/llm_gateway/` 的内部逻辑
