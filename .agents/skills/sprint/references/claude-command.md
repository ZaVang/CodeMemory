请使用 ralph-loop 插件执行本项目的标准 Sprint 流程。

**操作步骤**：
使用以下参数调用 `/ralph-loop:ralph-loop` plugin：

```
读取 docs/plans/SPRINT.md，逐项实现功能清单，运行验收命令直到全部通过，每次迭代结束前更新 SPRINT.md 任务状态，完成后追加 docs/chronicle.md 记录并向 docs/plans/pitfalls.md 追加新条目 --max-iterations 2 --completion-promise 'SPRINT COMPLETE'
```

**上下文**（自动注入）：
- Sprint 合同：docs/plans/SPRINT.md（当前未完成的 [ ] 任务）
- 陷阱知识库：docs/plans/pitfalls.md（实现前请阅读相关条目）