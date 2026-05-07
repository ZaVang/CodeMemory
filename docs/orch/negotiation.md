# Negotiation — Round 18

**Date:** 2026-05-07
**Context:** Two audit inputs assessed:
- Product Experience Reviewer (post-R17): 8.5/10. Functionality 8.5/10 (up from 6.5), Aesthetic Taste 8.5/10 (up from 8.0), Product Imagination 7.0/10 (unchanged). Zero Critical defects for the first time.
- Evolution Strategy Reviewer (post-R16, dated 2026-05-07): 7.5/10. Engine 9.5/10, product experience 6/10. The two structural fractures (no import UI, no AI-assisted creation) remain unresolved by explicit negotiation choice.

**Round position:** Polish round. Round 17 was a defect-fix consolidation round. Round 18 is the penultimate round (2/3 of the final product cycle), focused exclusively on small-scope high-value polish items — closing the remaining Nice-to-have gaps identified in the product audit. No new features, no competitive gap work, no architecture migration.

**Planning constraint:** All tasks must be completable in minutes to hours (not days). The final round (Round 19) will carry the large features (import UI, AI-assisted creation, imports autocomplete).

---

## 一、产品体验官建议（Product Audit Report — 8.5/10）

### Important Recommendations

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| I1 | 将 `user/investment` 添加到预定义目录颜色调色板——当前在 Legend 中显示为 "(auto)" 并使用 fallback 循环颜色 | **ACCEPT — R18-P1** | 默认数据集的 primary directory 不应显示为 fallback。约 15 分钟的调色板扩展。三处同步添加（DIRECTORY_COLORS + DIRECTORY_TINTS + DIRECTORY_TINTS_DARK）。颜色选择：deep teal（#0F766E），传达"分析/决策"语义，不与已有色冲突。 |
| I2 | Onboarding 应感知当前数据集——overlay 文案应提及正在展示的数据集 | **ACCEPT — R18-P2** | 新用户首次看到 onboarding 时，背后的图是 investment 还是 companion 提供完全不同的上下文。动态注入数据集名称和描述到 overlay 文案中。约 30 分钟的前端改动（读取 `/api/datasets` 响应 + 文案模板化）。 |
| I3 | 替换或丰富 companion 数据集——82% stale、极少依赖边 | **ACCEPT (保守方案) — R18-P7** | 完全替换 companion（新建 domain-relevant 数据集如 startup-decisions）属于大型内容工作，约需 1-2 天，不适合本轮。采用保守方案：为现有 companion 记忆添加 4-5 条显式跨记忆 imports，使图边数从 ~3 增加到至少 7 条。纯数据工作，不涉及代码修改。验证：`validate` 通过（无循环依赖）。 |
| I4 | Trim-node 字体 9px/8px 违反 12px 可访问性下限——用 opacity 降级替代 | **ACCEPT — R18-P5** | Trim-node 的小字体是有意的视觉退化信号，但字体缩小到不可读程度违背了产品自设的 12px 标准。保持 12px 字体 + opacity 降级（trim-summary: 0.65 + italic, trim-skipped: 0.4 + line-through）同时传达层级语义和保持可读性。约 20 分钟。 |

### Nice-to-have Recommendations

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| N1 | Legend 目录点击高亮——点击 Legend 目录名在图 canvas 上高亮该目录节点 | **ACCEPT — R18-P4** | 跨 R16-R17 多次建议。利用 cytoscape 已有 API（`cy.batch()` 批量样式更新）。约 30 分钟。在 62 节点 quant_operators 上需验证响应时间 < 100ms。 |
| N2 | Dashboard stale IDs 可点击——当前纯文本，改为跳转到 MemoryDetail 的链接 | **ACCEPT — R18-P3** | 自 R15 起多次建议但持续延期。约 15 分钟的非破坏性前端改动。每轮都说"下次一定"——这次真的做。 |
| N3 | 图节点 hover tooltip 丰富——追加 R-probability 和 dependent count | **ACCEPT — R18-P6** | R-probability 和 dependent count 已存在于 API/图数据中，tooltip 展示是纯前端渲染。约 20 分钟。需先确认 cytoscape node data 中是否已注入这些字段——若未注入则需扩展 GraphCanvas 数据传递。 |
| N4 | 暗色模式图节点填充可见性——DIRECTORY_TINTS_DARK 值过暗 | **DEFER** | 涉及跨亮/暗模式的颜色调优，需逐色验证。本轮已包含 P1（目录颜色新增），颜色调优应在统一轮次完成。留待最终轮。 |
| N5 | 响应式工具栏——15+ 元素 header 在 <1200px 视口下溢出 | **DEFER** | 约 1-2 天的响应式适配工作。当前目标用户（开发者 + Agent）使用大屏桌面。留待最终轮。 |
| N6 | 无障碍——全大写覆写设置选项 | **DEFER** | 设计决策，非缺陷。LuxCart 的全大写 + tight letter-spacing 是设计语言特征，toggle 开关属于功能添加而非打磨。 |

### Feature Proposals (from Phase 3)

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| Proposal 1 | Review Queue（复习队列——闪卡式 stale 记忆复习） | **DEFER** | 约 1.5 天。后端 touch API 和 R-probability 排序已就绪，前端工作量为主。属于"功能添加"而非"打磨"。留待最终轮。 |
| Proposal 2 | Dataset Comparison View（跨数据集拓扑对比） | **DEFER** | 约 2-3 天。需新建视图和跨数据集查询逻辑。属于大型功能。 |
| Proposal 3 | Memory Timeline（衰减曲线时间线） | **DEFER** | 约 2-3 天。需图表库或 canvas 渲染。 |
| Proposal 4 | Dependency Health Score（结构重要性权重） | **DEFER** | 约 0.5-1 天。计算在已有数据上完成，展示层未开发。 |
| Proposal 5 | Export-as-Context（一键 LLM system prompt 注入） | **ACCEPT — R18-P8** | 这是所有 Phase 3/4 提案中 effort-to-differentiation 比率最高的项目。进化策略师估算约 1 天，但核心逻辑（`buildPromptContent()`）已在 Resolve 中完成——剩余工作是格式化输出 + 剪贴板集成 + UI 按钮。约 1 天的前端改动。作为产品核心差异化能力的"最后一公里"，即使在本轮中属于较大项目也值得纳入。 |

---

## 二、进化策略师建议（Evolution Audit Report — 7.5/10，post-R16）

### CRITICAL

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| C1 | Bulk Import Pipeline（Web UI 拖拽导入）~3 天 | **DEFER — 最终轮** | 这是进化策略师认定的#1 结构性缺口。后端 import API 已存在，前端导入 UI 完全缺失。约 3 天的工作量，必须在最终轮交付。本轮不做——但 P8（Export-as-Context）完成输入-输出闭环的另一端（输出）。 |
| C2 | MemoryForm Imports 自动补全 ~1 天 | **DEFER — 最终轮** | suggest_deps.py 后端逻辑完整，前端 MemoryForm imports 字段无自动补全。约 1 天。 |
| C3 | AI-Assisted Creation（LLM Gateway 集成）~2 天 | **DEFER — 最终轮** | 进化策略师认定的#2 结构性缺口。这是"AI 记忆系统为 AI Agent 设计但人类创建记忆时无 AI 辅助"的认知 dissonance 核心。2 天。 |

### IMPORTANT

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| I1 | Review Queue | **DEFER** | 与体验官 Proposal 1 重复。留待最终轮。 |
| I2 | 图-搜索联动（搜索结果高亮图节点） | **DEFER** | 约 0.5 天。属于交互增强。留待最终轮。 |
| I3 | Markdown 预览（MemoryForm body 渲染） | **DEFER** | 约 0.5 天。留待最终轮。 |
| I4 | "Proposed" 审核队列 | **DEFER** | R16-M1 完成了 MCP 工具端的 propose，UI 审核界面是自然下一步。约 1 天。留待最终轮。 |
| I5 | App.tsx 状态管理重构 | **DEFER** | 约 2 天。架构改进。留待最终轮。 |
| I6 | Dashboard stale ID 可点击 | **ACCEPT — R18-P3** | 与体验官 N2 合并。本轮执行。 |
| I7 | Legend 点击高亮 | **ACCEPT — R18-P4** | 与体验官 N1 合并。本轮执行。 |
| I8 | Export-as-Context 按钮 | **ACCEPT — R18-P8** | 与体验官 Proposal 5 合并。本轮执行。 |

### Technical Health

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| TH1 | App.tsx God Object（1667 行） | **DEFER** | 与 I5 重复。留待最终轮。 |
| TH2 | 文件索引瓶颈（>1000 节点时 index.json 成为瓶颈） | **DEFER** | 约 4 天的 SQLite 迁移。当前 <200 节点，远未触及瓶颈。 |
| TH3 | CSS 架构（70% 内联样式） | **DEFER** | 约 3 天渐进迁移。当前 12 个组件可管理。 |
| TH4 | 前端组件测试覆盖 | **DEFER** | 约 2 天 React Testing Library。留待最终轮。 |

### NICE-TO-HAVE

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| N9 | Companion 数据集依赖丰富——添加显式 imports | **ACCEPT — R18-P7** | 与体验官 I3 保守方案合并。本轮执行。 |

---

## 三、Eval 报告（Round 17 — 6/6 PASS）

Round 17 Eval 确认所有 6 个任务均通过独立验证（86/86 测试零回归）。无遗留问题需在本轮修复。Eval 报告未提出新的改进建议——仅确认 Generator 自报与独立验证完全一致。

---

## 四、本轮接受/延期统计

| 类别 | 数量 |
|------|------|
| **ACCEPT（本轮执行）** | 8 个任务（P1-P8） |
| **DEFER（最终轮 Round 19）** | 23 个建议/提案 |
| **DECLINE（拒绝）** | 0 |

### ACCEPT 清单

| 任务 | 来源 | 预估耗时 | 类型 |
|------|------|---------|------|
| R18-P1 | 体验官 I1 | ~15 min | 调色板扩展 |
| R18-P2 | 体验官 I2 | ~30 min | 文案动态化 |
| R18-P3 | 体验官 N2 + 进化 I6 | ~15 min | 交互链接化 |
| R18-P4 | 体验官 N1 + 进化 I7 | ~30 min | 图交互增强 |
| R18-P5 | 体验官 I4 | ~20 min | 可访问性修复 |
| R18-P6 | 体验官 N3 | ~20 min | Tooltip 丰富 |
| R18-P7 | 体验官 I3 + 进化 N9 | ~30 min | 数据质量 |
| R18-P8 | 体验官 Proposal 5 + 进化 DF5/I8 | ~1 day | 差异化资产 |
| **合计** | | **~1.5 天** | |

### DEFER 去向（最终轮 Round 19 候选）

以下项目明确延期至 Round 19（最终轮），按优先级排列：

**第一顺位（竞争缺口，必须在最终轮交付）：**
- Import UI（拖拽 Markdown 导入 + 预览确认 + 自动 suggest-deps）—— 进化 C1, ~3 天
- AI-Assisted Creation（LLM Gateway 集成到 MemoryForm）—— 进化 C3, ~2 天
- Imports 自动补全（suggest_deps 集成到 MemoryForm）—— 进化 C2, ~1 天

**第二顺位（功能深化，提升产品完整性）：**
- Review Queue（闪卡式 stale 记忆复习）—— 体验官 Proposal 1 + 进化 I1, ~1.5 天
- "Proposed" 审核队列（MCP proposed 记忆的 UI 审核界面）—— 进化 I4, ~1 天
- Markdown 预览（MemoryForm body 实时渲染）—— 进化 I3, ~0.5 天
- 图-搜索联动（搜索结果高亮图节点）—— 进化 I2, ~0.5 天

**第三顺位（技术健康，可在产品稳定后处理）：**
- App.tsx 状态管理重构 —— 进化 I5/TH1, ~2 天
- 暗色模式图节点填充可见性 —— 体验官 N4, ~15 min
- 响应式工具栏 —— 体验官 N5, ~1-2 天
- CSS 现代化 —— 进化 TH3, ~3 天
- 前端组件测试 —— 进化 TH4, ~2 天

**第四顺位（战略资产，长期差异化）：**
- Semantic Edges —— 进化 F1, ~5 天
- DAG-Aware AI Editing Sidebar —— 进化 F2, ~8 天
- Dataset Comparison View —— 体验官 Proposal 2, ~2-3 天
- Memory Timeline —— 体验官 Proposal 3, ~2-3 天
- Dependency Health Score —— 体验官 Proposal 4, ~0.5-1 天
- "Since You Last Visited" Context Summary —— 进化 F3, ~2 天
- Hybrid Search —— 进化 F5, ~5 天
- SQLite Index Backend —— 进化 F6, ~4 天

---

## 五、策略说明

**本轮为什么全是小项目：**

1. **体验官首次给出零 Critical 缺陷。** 8.5/10 的评分意味着产品没有阻塞性问题。剩余 10 个 Nice-to-have 建议中的大部分都可以在本轮关闭——使最终轮专注于大型功能交付。

2. **倒数第二轮的定位。** 在 3 轮产品循环（R17 整顿 → R18 打磨 → R19 功能冲刺）中，R18 的角色是"清理桌面"——关闭所有剩余的纸割伤（paper cuts），确保 R19 交付大型功能时产品基座是 polished 的。

3. **打磨对产品感知的影响。** 目录颜色 fallback、onboarding 上下文缺失、trim-node 字体不可读——这些单个都是微小问题，但累积起来传达"未完成"的信号。在本轮关闭它们，使产品在最终轮前达到"看起来完成了"的状态。

4. **P8 的例外理由。** Export-as-Context 是本轮唯一的"准功能"项目（~1 天），纳入理由是它的 differentiation-to-effort 比率在所有提案中最高。Resolve 是 CodeMemory 的核心差异化能力，但用户无法方便地将 Resolve 输出注入 LLM —— 这是"最后一公里"问题。完成这个闭环使产品的核心价值主张对一个关键使用场景（Agent 上下文注入）完整可用。

**最终轮（Round 19）的前瞻：**

如果本轮 8 个任务全部交付，最终轮的桌面将只有大型功能：Import UI（3 天）、AI-Assisted Creation（2 天）、Imports 自动补全（1 天）作为必达项，Review Queue 和 "Proposed" 审核队列作为二级目标。不再有纸割伤需要处理。

**本轮排除大型功能的原因：**

Import UI（进化 C1）和 AI-Assisted Creation（进化 C3）合计约 5 天工作量。它们需要在本轮集中精力设计交互流程和数据流——如果在打磨轮中分散注意力到大型功能，两者都会做不好。最终轮可以专注于这两个大型项目，不受纸割伤干扰。
