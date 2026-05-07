# Negotiation — Round 15

**Date:** 2026-05-07
**Context:** Three Reviewer reports (product-audit-report.md 8.4/10, evolution-audit-report.md 8.3/10, research-audit-report.md 6.5/10) assessed against Round 14 (7/8 PASS, 1 deferred, decay pipeline confirmed working, 86/86 tests, zero regressions).
**Round position:** 4 of 5 investment-loop rounds. Round 16 is the final round and reserved for full-text body search + write-capable MCP tools.

---

## 产品体验官建议（Product Audit 8.4/10）

### Critical

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| 1 | HelpPanel 退场动画接线 | **ACCEPT — R15 Tier 1** | R13 遗留。最后一个无动画 UI 表面。`useExitAnimation` + CSS 模式已存在。纯接线工作，30 分钟。 |
| 2 | 残留 11px straggler 提升至 12px（4 处） | **ACCEPT — R15 Tier 1** | HelpPanel 键帽和快捷键说明在参考表中只有 11px——用户用来学习产品的地方。MemoryDetail 空状态文本和视图快捷键提示同理。20 分钟。 |

### Important

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| 3 | MemoryDetail 添加 stability 编辑（滑块） | **PARTIAL ACCEPT** | 后端 stability 工作已在 R15 完成（自适应更新 C1 + 长期底线 C2 + 领域默认值 C3）。前端滑块 UI 延期至 R16——后端正确性先于前端可控性。 |
| 4 | MemoryDetail 显示访问新鲜度 | **ACCEPT — R15 Tier 3** | "X 天前最后访问"和 R 概率数据已在 API 响应中。渲染它们投入低、可见性高。如容量允许则纳入。 |
| 5 | 搜索结果中显示访问新鲜度 | **DEFER — R16** | 每个搜索结果行增加一项元数据是简单前端变更，但 R15 Tier 3 已满。R16 与全文搜索一同纳入。 |
| 6 | 复习队列（顺序修复流程） | **DEFER — R16** | 将衰减风险从被动监控转为主动管理。需新建前端组件 + 顺序导航状态管理。中等投入。 |

### Nice-to-Have

全部 **DEFER — R16+**. 这些项（Search Resolve 工具提示、移除 List 过滤条、maturity badge 工具提示、右键菜单快捷键提示）均为低投入外观改进，但 R15 容量已满。各项均不超过 1 小时，可在 R16 末尾作为批量 polish 纳入。

### Product Strategy

全部 **DEFER**。跨数据集解析（3-4 天）、访问新鲜度时间线（2-3 天）、图漫步模式（3 天）均为大型功能，属于独立轮次范畴，非倒数第二轮修复轮。

---

## 进化策略师建议（Evolution Audit 8.3/10）

### Critical

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| C1 | 全文正文搜索 | **DEFER — R16** | #1 功能缺口。每个竞品都支持。需搜索管道变更（正文内容索引）+ 前端双向接线 + 结果高亮。中型功能（2-3 天）。刻意保留给最终轮。 |
| C2 | Playwright 冒烟测试 | **ACCEPT — R15 Tier 1（首个任务）** | 连续三轮延期（R12/R13/R14）。15 个组件零前端测试覆盖。5 条冒烟测试捕获约 80% 回归。**必须为 R15 首个任务——在任何功能代码之前交付。** |
| C3 | 消除 search dict / MemoryEntry 双重表示 | **ACCEPT — R15 Tier 3** | R14 C1 bug 根因。将 `search()` 重构为从 `MemoryEntry.model_dump()` 构建输出，消除手动字段复制。永久消除整个类别的 bug。约 30 行。如容量允许则纳入。 |

### Important

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| I1 | 可写 MCP 工具 | **DEFER — R16** | 5 个 MCP 工具中 4 个 readOnly。Agent 可读不可写。闭合 agentic 循环。需安全边界设计（propose_* 暂存模式）。~150 LOC。刻意保留给最终轮。 |
| I2 | Per-memory stability UI | **PARTIAL ACCEPT** | 后端 stability 工作已在 R15 完成（C1 自适应更新 + C2 长期底线 + C3 领域默认值）。前端 UI 延期至 R16——先正确，再可控。 |
| I3 | List 视图衰减列 | **DEFER — R16** | 外观层面。在 List 视图中将 `days_since_last_access` 和 `stability` 作为可排序列展示，配颜色编码。R16 与全文搜索一同评估。 |
| I4 | MemoryForm 自动补全 imports 建议 | **DEFER** | `suggest_deps.py` 存在但仅 CLI。前端集成需异步补全端点 + UI 组件。中等投入（~80 LOC）。非 R15 或 R16 优先项。 |
| I5 | 完整 Cooling Memories Dashboard | **DEFER — R16** | 将 N1 的最小衰减风险卡片扩展为全部有风险记忆的可排序列表。外观层面，中等投入。 |
| I6 | 多级撤销栈 | **DEFER** | 跨组件状态管理重构。中等投入。不及全文搜索或可写 MCP 工具紧迫。 |

### Nice-to-Have

全部 **DEFER**。"Demo Resolve"按钮、图键盘导航、版本 diff 查看器、"自您上次访问以来"上下文注入、记忆健康评分、语义搜索、Git 集成指南——均为有价值项目但在最终轮优先考虑全文搜索和可写 MCP 工具的约束下无法挤入。

### Feature Ideas

全部 **DEFER**。增量解析、per-tag stability 默认值、FSRS-lite stability 更新（部分被 R15 C1 解决）、DAG 感知编辑侧边栏、"代码式记忆"CI 流水线、时间事实建模——均为长期战略资产，非当前投资循环范围。

---

## 设计研究员建议（Research Audit 6.5/10）

### Critical

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| 1 | 自适应 stability 更新（访问时） | **ACCEPT — R15 Tier 2** | 研究员发现的最重要架构改进。FSRS v6 和 SuperMemo SM-19 均证明自适应 stability 优于静态 stability 20-30%。CodeMemory 拥有正确的原语（`stability` 字段、`days_since_last_access`、`access_count`、resolve 管道）但静态使用。修改 `resolve.py` 在成功访问时更新 stability，SInc 在 R ~ 0.7-0.85 处达到峰值，高 stability 时收益递减。完全向后兼容——所有记忆从 14.0 起步，通过使用自适应。约 1 天。 |
| 2 | 长期保留底线（混合衰减） | **ACCEPT — R15 Tier 2** | 纯指数衰减在 90 天时给出 1.2%、180 天后实际为零——参考知识不应静默消失。混合公式在保留短期排名（< 60 天行为不变）的同时确保所有记忆的最低检索概率。匹配 Bahrick"永久存储"发现：良好学习的语义知识保留基线可访问性。向后兼容 R < 0.1 警告阈值。约 1 小时。 |

### Important

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| 3 | 领域差异化默认 stability | **ACCEPT — R15 Tier 2** | 最简单可行的改进。`semantic_type` → stability 查找表。零算法复杂度。消除最常见错误默认场景：API 文档在 46 天衰减。约 30 分钟。 |
| 4 | Wander 主动复习模式（`--mode review`） | **DEFER — R16** | 价值清晰（将衰减从被动警告转为主动维护），但依赖 C1 自适应 stability 先落地且稳定。一旦 stability 值开始自适应，Gaussian 加权（R ~ 0.75 中心）复习选择变得有意义。 |
| 5 | 陈旧检测时 stability 下降 | **DEFER — R16** | 价值清晰（陈旧 = 回忆失败 = stability 应下降），但需先让自适应 stability 增加方向稳定。对称地，当 resolve 检测到 hash 不匹配时稳定性应下降。约 1 小时——R16 末尾自然纳入。 |

### Nice-to-Have

全部 **DEFER**。Weibull（指数-幂）衰减选项、per-user 参数学习、Dashboard stability 趋势可视化——均为研究级增强，适合未来独立轮次。当前回合聚焦于研究者标记为 Critical 和 Important 的高投入产出比项目。

### Product Strategy

全部 **DEFER**。各记忆衰减曲线形状、周度记忆半衰期健康报告——为长期差异化功能，在基础自适应 stability 验证之前不应启动。

---

## 跨领域协商总结

### 本轮纳入（R15）

| 梯队 | 任务 | 来源审计官 | 投入 |
|------|------|----------|------|
| Tier 1 | P1: Playwright 冒烟测试（5 条） | 进化策略师 C2 | ~1 天 |
| Tier 1 | I1: HelpPanel 退场动画 | 体验官 Critical #1 | ~30 分 |
| Tier 1 | I2: 修复残留 11px straggler（4 处） | 体验官 Critical #2 | ~20 分 |
| Tier 2 | C1: 自适应 stability 更新（访问时） | 研究员 Critical #1 | ~1 天 |
| Tier 2 | C2: 长期保留底线（混合衰减） | 研究员 Critical #2 | ~1 小时 |
| Tier 2 | C3: 领域差异化默认 stability | 研究员 Important #3 | ~30 分 |
| Tier 3 | C4: 消除 search dict/MemoryEntry 双重表示 | 进化策略师 C3 | ~1 小时 |
| Tier 3 | N1: MemoryDetail 访问新鲜度展示 | 体验官 Important #4 | ~1 小时 |

**总计：** 约 3-4 天。Tier 1+2 强制性任务约 2.5-3 天。

### 全体审计官同意的原则

1. **Playwright 必须先于任何功能代码** —— 进化策略师坚持，体验官和研究员未反对。三轮延期后已成为可信度问题。
2. **全文搜索和可写 MCP 工具必须去 R16** —— 三个审计官均认为这两项是关键功能。Sprint Planner 判定每项需专门实现窗口，挤入 R15 会挤占研究员的高价值低投入发现并使最终轮空心化。
3. **研究员的发现不可再延期** —— 指数衰减在 90 天实际删除知识的发现是研究审计的核心结论。即使体验官和进化策略师未标记为 Critical，三项研究驱动任务合计约 1.5 天，是本轮能产生最大长期回报的投资。
4. **前端 stability UI 在 R15 为时尚早** —— 体验官和进化策略师均建议 per-memory stability 滑块。Sprint Planner 判定后端稳定性工作（自适应更新 + 长期底线 + 领域默认值）必须先落地并在 R16 前端 UI 构建前通过狗食测试。

### 争议项

| 项目 | 体验官 | 进化策略师 | 研究员 | Planner 裁决 |
|------|--------|----------|--------|-------------|
| 全文正文搜索 | 未评分 | Critical C1 | 未涉及 | **DEFER 至 R16**。各审计官均认为关键，但需专门窗口。 |
| 消除 search dict 双重表示 | 未涉及 | Critical C3 | 未涉及（但发现了根因 bug） | **ACCEPT Tier 3**。如可能则修复根因而非仅症状。 |
| 复习队列 | Important #6 | 未涉及 | 未涉及 | **DEFER 至 R16**。有价值但依赖 stability UI 先到位。 |
| 领域差异化默认值 | 未评分 | 未涉及 | Important #3 | **ACCEPT Tier 2**。研究员发现的核心错误默认问题最便宜的修复。 |

### R16 前瞻

R16（最终轮）的自然组成：
- **全文正文搜索** —— 进化策略师 C1，体验官和研究员同步认可
- **可写 MCP 工具** —— 进化策略师 I1，闭合 agentic 循环
- **前端 stability UI** —— 体验官 Important #3 + 进化策略师 I2 的前端部分
- **剩余 Nice-to-Have** —— 本轮和三份审计的所有延期外观改进的批量 polish

---

*协商结束。待 Planner 将接受项目写入 SPRINT.md。*
