# Negotiation — Round 19（最终轮）

**Date:** 2026-05-07
**Context:** Three audit inputs assessed:
- Product Experience Reviewer (post-R18): **9.0/10**. Functionality 9.5/10, Aesthetic Taste 9.0/10, Product Imagination 8.0/10. Zero Critical defects. 8 of 9 R17 recommendations resolved (89%).
- Evolution Strategy Reviewer (post-R16, dated 2026-05-07): 7.5/10. Engine 9.5/10, product experience 6/10. The two structural fractures (no import UI, no AI-assisted creation) remain unresolved by explicit negotiation choice.
- Eval Report (Round 18): 8/8 PASS, 86/86 tests, zero regressions.

**Round position:** FINAL round (3/3 of the product cycle). Lightweight hygiene and cleanup. All tasks are completable in minutes to hours.

**Key context shift:** R18 achieved the first 9.0/10 product score. With zero Critical defects and the product's narrative arc complete (onboarding -> exploration -> Resolve -> Copy as Context -> agent integration), the marginal value of large features (Import UI 3 days, AI-assisted creation 2 days) has sharply decreased. These were previously positioned as "must deliver in final round" but the product's experience score trajectory (6.5 -> 7.0 -> 7.5 -> 8.0 -> 8.5 -> 9.0) shows the existing polish strategy is working. A lightweight final round that closes the remaining gaps is more valuable than a crunch to deliver large features that won't change the product score at this level.

---

## 一、产品体验官建议（Product Audit Report — 9.0/10）

### Important Recommendations

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| I1 | Review Queue — "Memories That Need You." Flashcard-style stale memory review workflow. | **DEFER — 未来 Sprint** | 约 1.5 天。R18 已交付 Dashboard 衰减风险面板 + List 健康列 + Touch 按钮 + R-probability 着色——这些提供了约 80% 的复习队列价值（扫描发现风险记忆 + 一键刷新）。完整的 sequential review workflow 留给独立 Sprint。 |
| I2 | Onboarding Resolve Call-to-Action — 添加交互式 Resolve 演示步骤 | **ACCEPT — R19-C2** | 低投入（~20 分钟）。这是 R18 audit 唯一的 Important 未关闭建议。在 onboarding 中展示真实 resolve 结果（而非仅文字描述）能在 10 秒内证明产品核心价值。优雅降级路径确保后端不可达时不影响 onboarding 体验。 |

### Nice-to-have Recommendations

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| N1 | 暗色模式图节点填充可见性 | **ACCEPT — R19-C1** | R17 唯一未关闭建议（89% 关闭率 → 目标 100%）。~15 分钟的颜色值调整。两轮迭代均标记为 defer，最终轮收尾是合适的时机。 |
| N2 | "Copy as Context" 发现性 — Help 面板 + SearchBar 入口 | **ACCEPT — R19-C4（前半）** | ~15 分钟。R18 交付的差异化功能缺少发现途径。Help 面板添加条目是最小成本的发现性提升。 |
| N3 | Keyboard shortcut for Copy as Context | **ACCEPT — R19-C4（后半）** | ~15 分钟。与 N2 合并为一个任务——两个高度相关的发现性改进。 |
| N4 | Export as Context for multiple targets | **DEFER — 未来 Sprint** | 约 2 天。需 resolve 引擎变更（merge DAG）+ 新 UI 流程。单目标导出已满足 MVP。 |
| N5 | Clipboard fallback for HTTP contexts | **ACCEPT — R19-C5** | ~15 分钟。一道部署防线——确保 Copy as Context 在所有部署场景（HTTP/HTTPS/localhost）下工作。 |
| N6 | Responsive toolbar for narrow viewports | **DEFER — 未来 Sprint** | 约 1-2 天。当前目标用户（桌面开发者）不受影响。 |

### R17 遗留建议

| # | 建议 | 状态 | R19 决策 |
|---|------|------|---------|
| N4 | 暗色模式图节点填充可见性 | 仅剩未关闭的 R17 建议 | **ACCEPT — R19-C1** |

---

## 二、进化策略师建议（Evolution Audit Report — 7.5/10，post-R16）

### CRITICAL（此前延期至最终轮——现在重新评估）

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| C1 | Bulk Import Pipeline（Web UI 拖拽导入）~3 天 | **DEFER — 未来 Sprint** | 产品已达 9.0/10 评分。导入 UI 是锦上添花而非雪中送炭——它在产品评分 6-7 时是竞争性短板，但在 9.0 时是增量功能。留给独立 Sprint。 |
| C2 | MemoryForm Imports 自动补全 ~1 天 | **DEFER — 未来 Sprint** | 同上。留给独立 Sprint。 |
| C3 | AI-Assisted Creation（LLM Gateway 集成）~2 天 | **DEFER — 未来 Sprint** | 进化策略师认定的 #2 结构性缺口。同上逻辑——9.0/10 评分降低了紧迫性。 |

### IMPORTANT

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| I1 | Review Queue | **DEFER** | 与体验官 I1 重复。留给未来 Sprint。 |
| I2-I8 | 图-搜索联动、Markdown 预览、Proposed 审核队列、App.tsx 拆分、Dashboard stale clickable、Legend highlight、Export-as-Context | **全部 DEFER 或已由 R18 完成** | 已由 R18-P3/P4/P8 覆盖多个项。其余留给未来 Sprint。 |

### Technical Health

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| TH1-TH4 | God Object 拆分、SQLite 后端、CSS 架构、组件测试 | **DEFER — 未来 Sprint** | 技术健康项。1-2 人团队下当前架构可管理。 |

---

## 三、Eval 报告（Round 18 — 8/8 PASS）

Round 18 Eval 确认全部 8 个任务通过独立验证（86/86 测试零回归）。无遗留问题需在本轮修复。Eval 报告未提出新的改进建议。唯一的 discrepancies（companion validate 1 pre-existing warning）与 R18-P7 无关。

---

## 四、本轮接受/延期统计

| 类别 | 数量 |
|------|------|
| **ACCEPT（本轮执行）** | 5 个任务（C1-C5） |
| **DEFER（未来 Sprint）** | ~25 个建议/提案 |
| **DECLINE（拒绝）** | 0 |

### ACCEPT 清单

| 任务 | 来源 | 预估耗时 | 类型 |
|------|------|---------|------|
| R19-C1 | 体验官 R17 N4 + R18 N1 | ~15 min | 颜色值调整 |
| R19-C2 | 体验官 R18 I2 | ~20 min | Onboarding 增强 |
| R19-C3 | 多轮 Eval 卫生建议 | ~20 min | CI/构建卫生 |
| R19-C4 | 体验官 R18 N2 + N3 | ~30 min | 发现性 + 快捷键 |
| R19-C5 | 体验官 R18 N5 | ~15 min | 部署健壮性 |
| **合计** | | **~1.5 小时** | |

### DEFER 去向（未来 Sprint）

以下此前明确延期至 Round 19 的项目**不再纳入本轮**，留给未来独立 Sprint：

**大型功能（此前承诺在最终轮交付——现在重新评估）：**
- Import UI（拖拽 Markdown 导入 + 预览确认 + 自动 suggest-deps）—— 进化 C1, ~3 天
- AI-Assisted Creation（LLM Gateway 集成到 MemoryForm）—— 进化 C3, ~2 天
- Imports 自动补全（suggest_deps 集成到 MemoryForm）—— 进化 C2, ~1 天
- Review Queue（闪卡式 stale 记忆复习）—— 体验官 Proposal 1 + 进化 I1, ~1.5 天
- "Proposed" 审核队列 —— 进化 I4, ~1 天

**功能深化：**
- Markdown 预览 —— 进化 I3, ~0.5 天
- 图-搜索联动 —— 进化 I2, ~0.5 天
- Dataset Comparison View —— 体验官 Proposal 2, ~2-3 天
- Memory Timeline —— 体验官 Proposal 3, ~2-3 天
- Dependency Health Score —— 体验官 Proposal 4, ~0.5-1 天
- 复合目标 Export-as-Context —— 体验官 N4, ~2 天

**技术健康：**
- App.tsx 状态管理重构 —— 进化 I5/TH1, ~2 天
- 响应式工具栏 —— 体验官 N6, ~1-2 天
- CSS 现代化 —— 进化 TH3, ~3 天
- 前端组件测试 —— 进化 TH4, ~2 天
- SQLite 索引后端 —— 进化 F6, ~4 天

---

## 五、策略说明

**为什么大型功能在本轮被移除：**

1. **产品评分轨迹证明现有策略有效。** 从 R15 的 7.0 到 R18 的 9.0，产品评分稳步上升——每一轮打磨都带来了可感知的品质提升。大型功能（Import UI、AI 辅助创建）在产品评分 6-7 时是竞争性短板，但在 9.0 时，它们对评分的边际提升远低于对 polish gap 的修补。

2. **9.0/10 改变了"必须交付"的定义。** 当产品体验为 9.0 且零 Critical 缺陷时，"必须交付"的不再是竞争性功能缺口——而是让已接近完美的产品在每一处细节上都经得起检查。这 5 个任务恰好完成这个目标。

3. **大型功能需要独立 Sprint 而非尾随追加。** Import UI（3 天）和 AI 辅助创建（2 天）都有显著的设计和交互复杂度。将它们塞进一个"轻量收尾轮"会导致两者都做不好——它们应该在独立的、聚焦的 Sprint 中交付。

4. **"Copy as Context" 是产品循环的完美收官。** R18-P8 已经交付了产品差异化能力的"最后一公里"——将 DAG 解析结果转化为 LLM 可用的上下文。本轮的 C4 和 C5 只是确保这个闭环在所有场景下都健壮可用。

**本轮 5 个任务的设计逻辑：**

- C1 + C2 = 关闭最后 2 个未关闭的高信号审计建议 → R17 建议关闭率从 89% 提升至 100%
- C3 = 确保 CI 流水线健壮——产品进入维护模式前的必要步骤
- C4 + C5 = 确保 R18 的差异化功能在所有部署场景下都可发现、可访问

**5 个任务全部可在 1.5 小时内完成。这是 CodeMemory 产品循环的最终轻量收尾。**
