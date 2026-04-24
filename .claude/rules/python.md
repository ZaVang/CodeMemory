---
description: Python coding standards — applies to all .py files in this project
paths:
  - "**/*.py"
---

# Python 开发规范

## 技术栈

- Python 3.13+，唯一外部依赖 `pyyaml`
- 核心实现：单文件 `bin/codememory.py`
- 原型阶段：无 async、无 Pydantic、无 LLM 调用

## 代码组织

- 单文件原则：所有 CLI 逻辑在 `bin/codememory.py`，保持 500 行以内
- 函数命名：动词开头（`parse_frontmatter`, `compute_body_hash`, `build_dag`）
- 所有公共函数类型注解覆盖
- 相关功能按注释分区（`# Core Utilities`, `# Index Management`, `# Commands`）

## 接口约定

- 函数间传递原生 Python dict/list，不使用 Pydantic（原型阶段简化依赖）
- 错误输出到 `sys.stderr`，正常输出到 `sys.stdout`
- 异常仅在系统边界处理（文件读取、YAML 解析）

## 文件格式

- 记忆文件 = YAML frontmatter（`---` 分隔） + Markdown body
- frontmatter 修改不触发 stale：body hash 基于 body 文本计算，修改 frontmatter 后 hash 不变
- 编码统一 UTF-8

## 禁止事项

- 禁止引入 `pyyaml` 之外的第三方依赖
- 禁止硬编码文件路径（通过 `--root` 参数或脚本路径推导）
- 禁止在 resolve 输出中混入 debug 信息（debug 走 stderr）

## 日志

- 原型阶段用 `print()` 输出，不引入 `logging` 模块
- 错误信息用 `print(f"...", file=sys.stderr)`
- 进入 Phase 2（精确 tokenizer、版本历史）后切换到 `logging`
