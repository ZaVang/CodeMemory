# Round 18 任务计划 — 打磨

**生成日期：** 2026-05-07
**上轮评估：** Round 17 — 6/6 PASS，86/86 测试通过，零回归。Dataset 默认值回归已修复、UX 展示修复完成、stability_source 已序列化、lifespan 迁移完成。
**本轮主题：** 打磨 —— 体验官首次给出零 Critical 缺陷（8.5/10）。剩余问题全部为 Nice-to-have 打磨项。本轮是倒数第二轮（产品循环 2/3），聚焦小范围高价值打磨，为最终轮收尾做准备。
**本轮定位：** 纯打磨轮。不引入新功能、不启动大型项目、不碰架构迁移。所有任务均为体验官审计报告中明确列出的 Nice-to-have 项目，每个任务耗时均以分钟计。

---

## 一、本轮聚焦

Round 17 修复了最后一条 Critical 缺陷（dataset 默认值回归），体验官首次将评分从 "有 Critical 缺陷" 提升至 8.5/10 "零 Critical"。剩余的改进建议集中在三个方向：

1. **目录颜色不完整。** 默认数据集 `user/investment` 目录不在 LuxCart 预定义调色板中，在 Legend 中显示为 "(auto)" 并使用 fallback 循环颜色——作为默认数据集的 primary directory，这削弱了 curated 感。修复方式：在 `colors.ts` 的 `DIRECTORY_COLORS`/`DIRECTORY_TINTS`/`DIRECTORY_TINTS_DARK` 中为 `user/investment` 添加条目。

2. **引导流程不感知数据集。** Onboarding overlay 文案泛化（"Your memory is a dependency graph"），未提及当前展示的数据集。investment 数据集（金融决策）与 companion 数据集（个人日记）的预期完全不同——上下文缺失会让新用户困惑"我在看什么"。修复方式：Onboarding 组件读取当前数据集名称和描述，动态注入到 overlay 文案中。

3. **交互打磨缺口。** Dashboard stale IDs 不可点击（纯文本）、Legend 目录不可交互（不能点击高亮图上节点）、trim-node 字体 9px/8px 违反 12px 可访问性下限（有意的视觉退化信号但可用 opacity 替代）、图节点 hover tooltip 可丰富（添加 R-probability 和 dependent count）。

本轮策略：**仅做小范围高价值打磨。** 不接受新功能提案、不碰 competitive gap、不启动架构迁移。所有任务均可在一小时内完成。

---

## 二、任务拆解

### 第一梯队：目录颜色 + 引导感知（必达，约 45 分钟合计）

| # | 任务 | 为何纳入 | 审计来源 |
|---|------|---------|---------|
| **P1** | 将 `user/investment` 添加到预定义目录颜色调色板 | 默认数据集 investment 的 primary directory `user/investment` 是用户第一眼看到的目录。当前在 Legend 中标记为 "(auto)" 并使用 fallback 循环颜色——作为产品门面，这削弱了 curated 感。添加一个语义上合适的颜色（如 deep teal 或 navy，关联"决策/分析"语义），使默认数据集的门面目录不再显示为 fallback。需在 `DIRECTORY_COLORS`、`DIRECTORY_TINTS`、`DIRECTORY_TINTS_DARK` 三处同步添加。 | 体验官 I1（Important） |
| **P2** | 使 Onboarding 感知当前数据集 | Onboarding overlay 当前文案泛化，不告知用户正在浏览的数据集。应在 overlay 中动态注入当前数据集名称和简短描述（从 `/api/datasets` 响应获取）。例如："You are viewing the **investment** dataset — 10 interconnected memories about financial decisions, market analysis, and risk assessment." 这为 onboarding 提供上下文锚点，帮助用户理解"我在看什么"。 | 体验官 I2（Important） |
| **P3** | Dashboard stale IDs 可点击导航 | Dashboard 的 stale 记忆列表当前显示纯文本 ID。将其变为可点击链接，点击后导航到 MemoryDetail 面板。这是约 15 分钟的非破坏性前端改动，自 R15 起多次被评审者建议但持续延期。 | 体验官 N2（Nice-to-have）、进化策略师 I6 |

### 第二梯队：交互打磨（应达，约 1 小时合计）

| # | 任务 | 为何纳入 | 审计来源 |
|---|------|---------|---------|
| **P4** | Legend 目录点击高亮 | 点击 Legend 中的目录名应在图 canvas 上高亮该目录的所有节点（提高透明度 + 边框加亮），再次点击恢复。这是跨多轮审计（R16-R17）持续建议的交互增强，利用 cytoscape 已有的节点选择/样式 API。 | 体验官 N1（Nice-to-have）、进化策略师 I7 |
| **P5** | 替换 trim-node 子 12px 字体为 opacity 降级 | trim-summary（9px）和 trim-skipped（8px）节点标签低于产品的 12px 可访问性下限。虽然这是有意的视觉退化信号（在 Resolve 模式下传递 budget 裁剪语义），但字体缩小到不可读程度违背了产品自身的可访问性标准。替代方案：保持 12px 字体，使用 opacity 降级（trim-summary: 0.65, trim-skipped: 0.4）来传达层级信号，同时保持可读性。 | 体验官 I4（Important） |
| **P6** | 图节点 hover tooltip 丰富 | 当前图节点 hover tooltip 仅显示 summary。在 tooltip 中追加 R-probability（检索概率，三色信号）和 dependent count（出度/被依赖数）。这两个字段均已存在于图数据和 API 响应中，tooltip 渲染是纯展示层的工作。 | 体验官 N3（Nice-to-have） |

### 第三梯队：数据质量 + 差异化资产（视时间完成，约 1 小时合计）

| # | 任务 | 为何纳入 | 审计来源 |
|---|------|---------|---------|
| **P7** | 丰富 companion 数据集：添加 4-5 条跨记忆 imports | companion 数据集（11 条个人记忆）有 82% 的 stale 率和极少依赖边（约 3 条），在任何用户切换到此数据集时都无法展示 DAG 能力。在不完全替换数据集的前提下（替换属于大型内容工作），为现有记忆添加 4-5 条显式 `imports` 跨引用（如 `friendship-philosophy` 引用 `burnout-reflection` 作为 recommended），使图展示至少 7-8 条边。这是纯数据工作，不涉及代码修改。 | 体验官 I3（Important）、进化策略师 N9 |
| **P8** | Export-as-Context 按钮：一键 LLM system prompt 注入 | Resolve 功能已产出 token-budgeted、拓扑排序的 markdown 输出。但用户无法方便地将此输出注入 LLM system prompt。在 Resolve 结果区域添加 "Copy as Context" 按钮：格式化输出为 `<codememory_context>` 标签包裹，包含 maturity weighting 指导和 status awareness，复制到剪贴板。这是所有 Phase 3/4 提案中 effort-to-differentiation 比率最高的项目（进化策略师估算约 1 天，但核心逻辑已在 `buildPromptContent()` 中完成）。 | 体验官 Proposal 5、进化策略师 DF5/I8 |

---

## 三、本轮排除项目（不接受、不实现、不讨论）

本轮定位为纯打磨轮（产品循环 2/3）。以下项目明确排除，留待最终轮（Round 19）：

- **大型功能**（Import UI ~3 天、AI 辅助创建 ~2 天、Imports 自动补全 ~1 天、Review Queue ~1.5 天）—— 属于"竞争差距"和"核心功能缺口"，需要在最终轮集中交付
- **架构迁移**（App.tsx 状态管理重构、CSS 现代化、SQLite 索引后端）—— 属于技术健康项，非用户可见改进
- **"Proposed" 审核队列** —— 属于 MCP 工具链的 UI 配套，约 1 天工作量
- **Markdown 预览**（MemoryForm 中的 body 实时渲染）—— 属于表单深度改进
- **暗色模式图节点填充可见性** —— 体验官 N4。涉及跨亮/暗模式的颜色调优，本轮已包含 P1 目录颜色修改，颜色调优应在统一轮次完成而非分散
- **响应式工具栏** —— 体验官 N5。约 1-2 天，属于大型前端适配
- **无障碍设置选项** —— 体验官 N6。设计决策，非缺陷
- **图-搜索联动**（搜索结果高亮图节点）—— 属于交互增强，留待最终轮
- **companion 数据集完全替换** —— 体验官 I3 的激进方案。本轮采用 P7 的保守方案（丰富 imports）；完全替换（如新建 startup-decisions 数据集）属于大型内容工作

---

## 四、验收概要

本轮共计 8 个任务。核心验收标准：

### P1 — 目录颜色
1. `user/investment` 目录在图 canvas 上使用预定义颜色（非 fallback 循环色）
2. Legend 中 `user/investment` 不再标记为 "(auto)"
3. 亮色和暗色模式下颜色均可区分
4. 其他数据集（companion、software-architecture、quant_operators）的颜色不受影响

### P2 — 引导感知
1. Onboarding overlay 文案包含当前数据集名称
2. 切换到不同数据集后重新触发 onboarding 时文案随之更新
3. 无数据集（空状态）时文案优雅降级
4. 首次访问（investment 默认）显示 investment 相关描述

### P3 — Dashboard 交互
1. Dashboard stale 记忆列表中的 ID 可点击
2. 点击后导航到对应 MemoryDetail
3. 亮色/暗色模式下链接样式一致

### P4 — Legend 交互
1. 点击 Legend 目录名高亮该目录所有节点（其他节点 dim）
2. 再次点击恢复全部节点正常状态
3. 点击另一个目录时切换高亮（不叠加）
4. 高亮状态在视图切换后清除

### P5 — Trim-node 可访问性
1. trim-summary 节点标签 >= 12px，使用 opacity 降低视觉权重
2. trim-skipped 节点标签 >= 12px，使用更低 opacity
3. Resolve 模式以外的节点不受影响
4. 视觉上 trim-summary < trim-skipped 的层级关系保持

### P6 — Tooltip 丰富
1. 图节点 hover tooltip 显示 R-probability（含三色信号）
2. 图节点 hover tooltip 显示 dependent count（被依赖数）
3. 无 R-probability 数据时优雅隐藏（不显示 "undefined"）

### P7 — Companion 数据
1. companion 数据集的图边数从 ~3 增加到至少 7
2. 新添加的 imports 具有合理的语义关联（非随机连接）
3. validate 通过（无循环依赖、无断链）
4. investment 默认数据集行为不变

### P8 — Export-as-Context
1. Resolve 结果区域出现 "Copy as Context" 按钮
2. 点击后将格式化输出复制到剪贴板
3. 复制后提供视觉反馈（checkmark 动画或 toast）
4. 输出格式包含 `<codememory_context>` 标签和 maturity weighting 指导

### 全量回归
1. `cd frontend && npx tsc --noEmit` — 零错误
2. `cd frontend && npx vite build` — 构建成功
3. `PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short` — 57/57
4. `PYTHONPATH=src python tests/integration_test.py` — 24/24
5. `PYTHONPATH=src python -m pytest tests/test_api.py -v --tb=short` — 5/5
6. 全部 86 测试无回归

---

## 五、陷阱提示

- **[P1] 颜色语义一致性。** `user/investment` 作为金融/决策类目录，颜色应区别于已有语义色（facts=charcoal, observations=gray, preferences=gold, decisions=red）。避免使用纯绿色（已被 `user/beliefs` 占用）或纯紫色（已被 `user/people` 占用）。建议使用深青色（deep teal, #0F766E 附近）传达"分析/理性"语义。同时须在亮色 tint、暗色 tint 两处定义，确保暗色模式下不过暗（参考 `DIRECTORY_TINTS_DARK` 的 #15-#4A 亮度范围）。

- **[P2] Onboarding 数据来源时序。** Onboarding 组件渲染时 `/api/datasets` 可能尚未完成。需处理加载态（显示占位文案）、空数据集状态（显示通用引导文案）、以及数据集切换后 onboarding 文案的更新时机（onboarding 是首次访问一次性展示，切换数据集后是否重新触发需明确策略——建议仅在首次展示时注入数据集上下文，不因后续切换而重新弹出）。

- **[P3] 点击导航与当前视图的交互。** Dashboard stale ID 点击后导航到 MemoryDetail（滑出面板）。需确认 MemoryDetail 在 Dashboard 视图下正确渲染（已在 Graph 视图下工作，Dashboard 下使用相同的 App 级状态管理）。

- **[P4] Cytoscape 批量样式更新性能。** 高亮/取消高亮涉及遍历所有节点修改样式。在 62 节点的 quant_operators 数据集上需验证操作响应时间 < 100ms。使用 `cy.batch()` 包裹样式更新以避免多次重绘。

- **[P5] Trim 样式语义保留。** 将 9px/8px 改为 12px 后，trim-summary 和 trim-skipped 之间的视觉层级需要通过 opacity 差值传达。建议 trim-summary: opacity 0.65 + font-style italic, trim-skipped: opacity 0.4 + line-through decoration。这保留了"内容被裁剪"的语义，同时不牺牲可读性。

- **[P6] Tooltip 数据可用性。** R-probability 和 dependent count 需从图数据或 API 响应中获取。确认当前 cytoscape node data 中是否已包含这些字段——如果 GraphCanvas 构建 cytoscape elements 时未注入，需先扩展数据传递路径。

- **[P7] Import 添加不引入循环依赖。** 在 companion 记忆中手动添加 imports 后，必须运行 `codememory validate` 确认无循环依赖。companion 记忆的目录结构分散（7 个目录 for 11 条记忆），跨目录 imports 需验证 ID 拼写完全匹配。

- **[P8] 剪贴板 API 兼容性。** `navigator.clipboard.writeText()` 在 localhost 以外的 HTTP 上下文中需要安全上下文（HTTPS）。开发环境（localhost）天然支持，但需确认 Playwright 测试环境中剪贴板 API 可用。备选方案：fallback 到 `document.execCommand('copy')` 或使用 textarea 选择复制。
