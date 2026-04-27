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

## [Sprint 2] 验收命令执行顺序
snapshot 验收脚本创建的 composite 会引用瞬态节点 ID（如 `s/x`, `s/y`），这些 ID 不在 index.json 中。如果在 snapshot 测试后立即运行 `validate`，会触发断链警告（预期行为，非 bug）。验收时应先跑 snapshot 测试，再跑 validate 回归。或者 snapshot 测试后用 `reindex` 重建索引再 `validate`。

## [Sprint 2] Sandbox 工具数量文档滞后
SPRINT.md 列出的验收命令期望 6 个 Sandbox tools，但 Sprint 2 新增了 `snapshot` tool，实际为 7 个。验收脚本中的 `assert len(names) == 6` 应更新为 `== 7`。后续 Sprint 新增 tool 时需同步更新文档中的数量预期。

## [Sprint 2] 验收脚本中的硬编码日期
snapshot 验收脚本使用 `datetime.now()` 动态生成文件名日期，导致文件名中的日期为运行日期而非固定值。验收脚本中的 `Path('...2026-04-24-...')` 断言会在不同日期运行失败。应使用 `datetime.now().strftime('%Y-%m-%d')` 动态构造路径，或在验收脚本中明确标注日期为变量。

## [Sprint 3] 验收命令与清理命令同步
Task 验收命令中 `create` 创建的测试记忆（如 `protected-orphan`、`cold-idea`、`never-forget`），必须在清理命令中有对应的 `rm -f`。写 SPRINT.md 时确保每个 `create` 都有对应的清理项，避免测试文件残留污染 index。

## [Sprint 3] access_count 精确断言陷阱
`resolve` 每次运行都会递增所有 full-text 节点的 access_count。验收脚本若使用 `assert ctx['access_count'] >= 1`（>=）而非精确值，则无论 resolve 运行多少次都能通过。不要用 `==` 断言 access_count 的具体数值——它会在多次验证中漂移。

## [Sprint 3] Sandbox tool 数量持续增长
当前 9 个 Sandbox tools：resolve_context, create_memory, search_memories, validate_memories, focus_memory, overview, update_memory, snapshot, find_orphans。每次 Sprint 新增 tool 时需同步更新所有文档和验收脚本中的数量断言。

## [Sprint 4] summary_hash 初始值陷阱
`create` 命令生成模板时 body 为 "Write content here..."，此时 `summary_hash` 已基于该模板 body 计算。用户填写实际内容后如果不通过 `update` 更新 summary_hash，新记忆会立即被 overview stale 检测标记为 `[stale]`。create 时应提示用户"填写内容后请运行 update 命令更新 summary_hash"。Sprint 1-3 的旧记忆文件中 summary_hash 为 "placeholder" 或与实际 body 不匹配，需要用 update 命令批量修复。

## [Sprint 4] access_count 累积导致验收不可重复
多次验证运行中 access_count 持续递增，使得 overview heat score、search 排序结果不可重复。验收脚本不应断言精确的 heat 数值或排序位置，而应验证 heat 字段存在（`heat:N` 格式）和排序的逻辑一致性（被引更多的排在前面）。

## [Sprint 5] example_agent.py 自动清理不完整
example_agent.py 在运行结束时删除自己创建的测试记忆文件，但未执行 `reindex`。这意味着 index.json 中会残留已删除记忆的引用，直到下次 reindex 才清除。如果 example_agent.py 用于 demo 展示，应在清理逻辑末尾添加 `reindex` 调用，使 index 恢复到运行前状态。

## [Sprint 5] INTEGRATION.md 与 README.md 内容重叠
两份文档都包含"快速开始"章节。维护时应以 README.md 为入口（精简版，面向首次访问者），INTEGRATION.md 为深度集成指南（详细版，面向需要嵌入 Agent 项目的开发者）。避免在两个文件中维护重复的安装步骤。
