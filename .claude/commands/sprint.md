请使用 sprint 流程执行当前 CodeMemory Sprint。

**Sprint 合同**：`docs/plan/SPRINT.md`

**操作步骤**：

1. 读取 `docs/plan/FUTURE.md`、Sprint 合同与 `docs/plan/pitfalls.md`
2. 识别所有 `[ ]` 未完成任务，按依赖顺序逐项实现
3. 每完成一项将 `[ ]` 改为 `[x]`
4. 运行 Sprint 合同中列出的验收命令
5. owner 接受后才在 `docs/plan/HISTORY.md` 写入 accepted，并标记 `SPRINT COMPLETE`

基础验收示例（以 Sprint 合同为准）：

```bash
python -m codememory.cli --root examples/investment reindex
python -m codememory.cli --root examples/investment validate
python -m codememory.cli --root examples/investment build user/investment/context
```
