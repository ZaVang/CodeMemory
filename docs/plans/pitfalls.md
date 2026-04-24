# Pitfalls

## TypeError: Object of type date is not JSON serializable
In `codememory.py`, when saving the index to `index.json`, the YAML parser parsed `2026-04-24` as a Python `datetime.date` object. The standard `json.dump` does not know how to serialize `datetime.date`. Fix: custom `DateEncoder` that extends `json.JSONEncoder`.

## [Sprint 1] python-frontmatter 与 pyyaml 版本冲突
`python-frontmatter` 包强制依赖 `PyYAML==5.1`，而 codememory 使用 `pyyaml>=6.0`，两者无法共存。如果 llm_gateway 或其他组件需要解析 Markdown frontmatter，应使用手动 `---` 分隔符解析（`content.split('---', 2)`），不引入额外的 `frontmatter` 包。codememory 的 `core.py` 已有完整实现。

## [Sprint 1] async register_all() 需要 await
`codememory.tools.register_all(sandbox)` 内部使用了 `await sandbox.register(...)`，调用方必须 `await register_all(sandbox)`。如果忘记 `await`，不会报语法错误（Python 会静默返回 coroutine 对象），导致后续 `sandbox.list_tools()` 返回空列表。

## [Sprint 1] Sandbox handler 返回格式约定
codememory 的 Sandbox handler 返回 `{"result": str}`（序列化后的结果文本），而非结构化 dict。验收脚本不能假设返回 `{"nodes": [...]}` 等内部结构。测试时应使用 `result.get('result', '')` 并检查文本内容。

## [Sprint 1] 数据迁移后务必删除源目录
将记忆数据从框架根目录迁移到 `examples/` 后，必须显式执行 `rm -rf user/ self/ schemas/` 删除源目录。Generator 可能只完成文件复制但跳过清理步骤。验收时必须用 `ls user/ 2>/dev/null && echo FAIL || echo OK` 显式检查。
