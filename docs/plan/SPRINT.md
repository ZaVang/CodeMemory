# CodeMemory Current Sprint

> **Status:** Active — **阶段 C：清理与 test**
> **依据：** `docs/architecture.md` §3.3（修改类 proposal）、§3.4（test 契约）、§6（验收信号）、附录（删除清单）。
> 实现若需偏离本合同或 architecture.md 契约：先改文档（经 owner 确认），再写代码。

---

## Sprint Goal

代码与概念模型的最后对齐：test 契约落地、修改类 proposal patch 队列落地、intensity/decay 机制全链路移除、拟人范式残留命令删除、shim 处置。完成后 `grep intensity src/` 仅剩 deprecated 别名。

---

## Scope（交付项）

### 1. test 契约（architecture §3.4，新模块 `test_contract.py`）

- frontmatter 新增可选 `golden_questions`（list of `{q, expect?}`）；
- `codememory test <entry> [--depth] [--budget]`：输出 `{format_version, entry, context, questions}` JSON；题集为空 → 退出码 0 + notice；
- `codememory test report <entry> --results <file>`：校验 `{q, answer, pass}` 列表格式后写入 log（`test_report` 条目）；
- check 新增 golden_questions 格式校验（非 list / 缺 q 字段 → warning）；
- Core 零 LLM 依赖：runner 是 agent / CI。

### 2. 修改类 proposal patch 队列（architecture §3.3）

- **复用评审结论（架构 §2.1 要求的前置评审，已完成）**：不复用 compiler review——它是"批量导入审阅集"粒度（corpus → ReviewSet → materialize），与单条修改提案的生命周期不匹配，强行复用会造出第三种机制。patch 队列独立实现。
- 存储：`.codememory/proposals/<seq>-<target-slug>.json`，字段 `{proposal_id, target_id, patch:{summary?, body?, import_required?, import_recommended?, import_related?, source_ref?}, reason, created_by, created_at}`；
- `codememory propose <target-id> --reason "..." [--summary ...] [--body ...] [--import-required ...] [--source-ref ...]`：写入队列，不动目标 atom；
- `codememory proposals`：列出待审队列；
- `merge` / `reject` 扩展：参数先按 proposal_id 查队列——merge = 经 update() 应用 patch（version++ / change_log 复用）+ 删除队列文件 + log；reject = 删除队列文件 + log；查不到再按 memory id 走新增类路径（阶段 A 行为不变）；
- check 新增：patch 队列积压提醒（超 14 天）、target 不存在的 proposal 报 warning。

### 3. 删除拟人范式残留（architecture 附录删除清单）

- 删 `handle_focus` / `handle_overview` / `handle_wander` 及 cli / tools.py / mcp_server.py / backend 路由绑定；
- 删 `core.compute_retrieval_probability`；
- 涉及 legacy 命令的测试断言迁移或删除（integration_test / test_api / test_source_refs）；
- snapshot.py / transient.py 保留（REPL 草稿辅助工具）。

### 4. intensity / stability 全链路移除

- models.py 删 4 字段：`intensity`、`stability`、`stability_source`、`days_since_last_access`（含校验器）；
- create.py：删 `--intensity` / stability 默认逻辑（`SEMANTIC_TYPE_STABILITY`）；orphans：删 `--min-intensity`；
- validate.py：删 decay check（`DECAY-WARN` 消失）；
- index / import_cmd / snapshot / transient / compiler（proposal 模型与 materialize）/ tools / mcp 的 intensity 引用清扫；
- skeletonize：内部评分改名 weight；CLI `--min-intensity` 改名 `--min-weight`，**旧名保留为 deprecated 别名一个版本**（架构附录）；config yaml 同时接受新旧键名（旧键 deprecated）；
- access_count / last_access / cache_stable / lifecycle / maturity / evidence 保留（架构 §3.1）。

### 5. shim 处置 + 文档同步（合同内完成）

- 删除 `context_pack.py` shim：`__init__.py` 与测试 import 迁移到 `codememory.build`；`resolve.py` 保留（承载 resolve 别名函数）；
- 文档：CLAUDE.md（文件树 / CLI 速查 / 概念对照：test 与 proposal 修改类已实装）、guide（§0 对照、§6 修改类提案命令用法替换过渡做法、§8 错误表）、prd §4.2/§4.3 实现状态、architecture §2/§6 阶段标记、pitfalls（decay 条目移除）、`.claude/rules/python.md`（模块清单与陈旧表述，架构 spec §11 预约的更新）。

---

## Out of Scope

- MCP / toolkit 新工具暴露（post-convergence backlog）；
- Operator UI 对齐（post-convergence backlog）；
- USER_GUIDE / INTEGRATION / project_structure 全量重写（post-convergence backlog）。

---

## Acceptance Signals（对应 architecture.md §6 阶段 C）

1. `grep -r "intensity" src/codememory/ --include="*.py"` 仅剩 skeletonize deprecated 别名处（含注释）；
2. `codememory test <entry>` 输出题集 + 装配上下文 JSON；空题集退出码 0；
3. `codememory propose` → `proposals` → `merge` 全链路可用：patch 应用后 version++、change_log 留痕、队列清空；
4. focus / overview / wander 命令与 handler 不复存在；`compute_retrieval_probability` 不复存在；
5. models.py 无 4 个删除字段；validate 无 DECAY-WARN；
6. 全套单测 + 集成 + test_api 在断言迁移后全绿。

---

## Verification Commands

```bash
PYTHONPATH=src python -m pytest tests/unit -q
PYTHONPATH=src python -m pytest tests/test_api.py -q
PYTHONPATH=src python tests/integration_test.py
grep -rn "intensity" src/codememory/ --include="*.py"   # 仅 deprecated 别名
# CLI 冒烟：
codememory test <entry>                                  # 输出题集 JSON
codememory propose <id> --reason "..." --summary "..."   # 入队
codememory proposals && codememory merge <proposal_id>   # 应用
codememory focus <id>                                    # 报"无此命令"
```

---

## Constraints

- TDD：新能力（test / patch 队列）先写失败测试；删除类变更以"全套测试迁移后绿色"为准；
- 业务逻辑只进 handlers.py / 核心模块；cli.py、tools.py 薄壳；
- 禁止新增第三方依赖；不碰 `src/harnesslib/`、`src/llm_gateway/`；
- 提交前恢复 examples 生成文件（pitfalls）；
- examples 数据若含 intensity frontmatter：保留不动（旧字段在 frontmatter 中变为惰性未知键，extra=allow 兼容），不强制迁移数据。

---

## References

- `docs/architecture.md` §3.3 / §3.4 / §4.4 / §6 / 附录
- `docs/plan/HISTORY.md` 阶段 A / B 记录
- `docs/plan/pitfalls.md`
