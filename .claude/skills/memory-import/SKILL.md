---
name: memory-import
description: 把存量文档、笔记、聊天记录提炼导入 CodeMemory 记忆库（agent 即 importer）。Use when the user asks 导入记忆 / 导入文档 / 把这些笔记导入记忆库 / import memories / migrate notes into codememory, or points at existing material to be distilled into a memory repo.
---

# Memory Import — agent 即 importer

你现在是 CodeMemory 的导入器。**canonical 范式是 `docs/agent-memory-guide.md` 第 9 节**——先读它，本文件只是执行检查单。你的价值是提炼与取舍，不是搬运：机械切分交给 `compile-md` / `skeletonize` / `import`。

## 前置检查

1. 确认记忆库 root：`CODEMEMORY_ROOT` 环境变量或每条命令带 `--root <path>`；用户没说就先问清楚目标库。
2. `codememory reindex && codememory validate`——基线必须干净（已有 ERROR 先报告，不要在脏库上导入）。
3. 让用户指明材料范围（文件 / 目录 / 粘贴文本），并确认主题归属（影响目录与 tags）。

## 执行循环（guide §9 六步）

每批材料：

1. **盘点分类**：原文有长期价值 → asset + 提炼；只有结论有价值 → 仅提炼；过不了写入门槛两问 → 跳过并记录原因。
2. **登记 asset**：`codememory source add <path> --id src/<slug> --summary "..."`（原文不动）。
3. **提炼 atoms**：每条一个语义单元，目录按种类选（facts/decisions/preferences/processes/principles），**一律 `create --propose`**，随即 `update` 填真实 summary（独立可读含结论）与简短 body。
4. **声明关联**：`update <id> --change-note "..." --import-required <依赖>... --source-ref src/<slug>`。
5. **批次校验**：`codememory validate`——ERROR 当场修；proposed 引发的 STATUS-WARN 属预期，merge 后消失。
6. **交付审阅清单**（必须输出给用户）：

```
| # | proposed id | summary | 出处 | merge 顺序 |
（被依赖者排前；用户 merge 后建议建入口 atom + golden_questions 并跑 codememory test）
```

## 硬约束

- 不直写 active；不修改已有 atom（要改走 `propose`）；不动原文文件。
- 不绕过 CLI 直接写 .md（包括"帮忙补 frontmatter"）。
- 跳过的材料必须列在清单里，不允许静默丢弃。
