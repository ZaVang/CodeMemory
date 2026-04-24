请使用 multi-ralph 技能执行本项目的标准 Sprint 流程。

**Sprint 合同**：`docs/plans/SPRINT.md`

**操作步骤**：

1. 读取 Sprint 合同，识别所有 `[ ]` 未完成任务
2. 按依赖顺序逐项实现，每完成一项将 `[ ]` 改为 `[x]`
3. 运行验收命令验证
4. 完成后记录 session 到 `docs/chronicle.md`

**验收命令**（从 Sprint 合同中获取）：
```bash
python bin/codememory.py reindex
python bin/codememory.py validate
python bin/codememory.py resolve user/investment/context
```
