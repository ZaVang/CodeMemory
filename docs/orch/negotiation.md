# Negotiation — Round 17

**Date:** 2026-05-07
**Context:** Two audit inputs assessed:
- Product Experience Reviewer (post-R16): 7.2/10. Functionality 6.5/10 (down from 8.5 due to dataset regression). Aesthetic Taste 8.0/10.
- Evolution Strategy Reviewer (post-R16): 7.5/10 (+1.0 from R15). Engine 9.5/10, product experience 6/10.

**Round position:** Defect-fix round. Round 16 was the final Product-Loop investment cycle round. Round 17 is a consolidation round focused exclusively on regressions and technical debt accumulated during the R16 delivery sprint.

**Planning constraint:** Tasks are limited to defect fixes and technical debt elimination. No new features, no competitive gap work, no architecture migration. Strategy: fix what broke, nothing more.

---

## 一、产品体验官建议（Product Audit Report — 7.2/10）

### Critical Recommendations

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| CR1 | 修复 dataset 默认值自强化回归——`/api/datasets` 端点返回服务端真实默认值，不受请求 header 污染；前端移除硬编码 `_currentDataset = 'companion'` | **ACCEPT — R17-CR1** | 两段式回归。根因：前端 `api.ts` 硬编码初始值为 companion + 后端中间件在豁免路径上仍从 header 写 ContextVar + `/api/datasets` handler 从已污染的 ContextVar 读取 current 字段。影响：每个浏览器会话初始化到错误的数据集（companion 而非 investment）。进化策略师估算修复约 30 分钟。最高优先级——本轮第一顺位。 |
| CR2 | `/api/datasets` 的 `current` 字段应使用服务端配置（`DEFAULT_DATASET`），而不是从 per-request ContextVar 读取 | **ACCEPT — 合并入 R17-CR1** | CR1 和 CR2 是同一条因果链的两个环节。'current' 字段的语义是"服务端的实际当前数据集是什么"，不是"客户端认为当前是什么"。修复 CR1 自然覆盖 CR2。 |

### Important Recommendations

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| I1 | 恢复 investment 为首次访问的默认数据集 | **ACCEPT — CR1 的自然结果** | 修复 CR1 后，服务端 `DEFAULT_DATASET=investment` 自然生效。不需要额外工作。不单独建任务。 |
| I2 | 丰富 companion 数据集依赖——至少 3-4 条显式 imports | **DEFER** | 有价值——companion 的依赖稀疏使得 DAG 展示效果不好（82% stale、极少边）。但数据集回归修复后，investment 将成为默认数据集，此问题的紧迫性自然下降。同时本轮定位为纯修复轮，不修改示例数据。留待未来 Sprint。 |
| I3 | 引导流程应感知当前数据集——onboarding copy 应提及正在展示的数据集 | **DEFER** | 有意义——提到"你正在浏览 investment 决策数据集（10 条关于市场分析、风险承受和投资组合决策的互连记忆）"比当前泛型文案更强。但这是内容改进而非缺陷修复。留待未来 Sprint。 |
| I4 | 搜索结果中区分精确匹配和模糊匹配——添加分组分隔或"精确"/"相关"分组 | **DEFER** | 体验改进。当前搜索已有 match_quality 指示器，只是缺少明确的分组视觉。非缺陷。留待未来 Sprint。 |

### Nice-to-have Recommendations

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| N1 | Legend 目录点击高亮——点击 legend 中的目录名应在图上高亮该目录所有节点 | **DEFER** | 体验增强。约 30 分钟的非破坏性前端改动。但本轮容量已分配给 CR1（回归修复）和展示修复（UX1/UX2）。留待未来 Sprint。 |
| N2 | Dashboard stale ID 可点击——原为纯文本，改为跳转到 MemoryDetail 的链接 | **DEFER** | 体验改进。约 15 分钟。非缺陷——当前行为是设计如此而非 bug。留待未来 Sprint。 |
| N3 | 图节点 hover tooltip 丰富——添加 R-probability 和 dependent count | **DEFER** | 约 20 分钟。留待未来 Sprint。 |
| N4 | 暗色模式图节点填充可见性——DIRECTORY_TINTS_DARK 值过暗，提升 5-10% 亮度 | **DEFER** | 约 15 分钟的调色工作。需要跨亮色/暗色模式验证不破坏现有设计。留待未来 Sprint。 |
| N5 | 响应式工具栏——15+ 元素的 header 在 <1200px 视口下溢出 | **DEFER** | 约 1-2 天的响应式适配。当前目标用户使用大屏桌面，不紧急。留待未来 Sprint。 |
| N6 | 无障碍——全大写覆写设置选项 | **DEFER** | 设计决策而非缺陷。留待未来 Sprint。 |

### Feature Ideas (from Phase 3)

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| F1 | Review Queue（复习队列——闪卡式 stale 记忆复习工作流） | **DEFER** | 约 1.5 天。有吸引力的功能（利用已有 touch API 和 R-probability 排序），但本轮定位为纯修复轮。留待未来 Sprint。 |
| F2 | Dataset Comparison View（跨数据集拓扑和成熟度对比） | **DEFER** | 约 2-3 天。需新建视图和跨数据集查询逻辑。留待未来 Sprint。 |
| F3 | Memory Timeline（时间线——衰减曲线、创建日期、最后访问可视化） | **DEFER** | 约 2-3 天。需图表库或 canvas 渲染。留待未来 Sprint。 |
| F4 | Dependency Health Score（结构重要性权重，critical-path 检测） | **DEFER** | 约 0.5-1 天。计算在已有数据上完成，仅需展示层。留待未来 Sprint。 |
| F5 | Export-as-Context（一键 LLM system prompt 注入） | **DEFER** | 约 1 天。Resolve 已产出结构化输出，格式化步骤简单。留待未来 Sprint。 |

### 执行摘要中直接提及的展示问题

| 问题 | 决策 | 理由 |
|------|------|------|
| 图节点标签 11px 仍太小——Legend 中可读但图 canvas 上节点标签在 11px 下难以辨认 | **ACCEPT — R17-UX1** | R15 的 sub-12px 修复针对交互元素，图节点标签落在此保护线之外。约 15 分钟。 |
| List 视图缺少水平 padding——内容紧贴边缘 | **ACCEPT — R17-UX2** | R16 期间遗留的展示回归。约 10 分钟。 |
| SearchBar Resolve 按钮无 tooltip（R16-P2 的交付可能未在实时环境中正确渲染） | **ACCEPT — R17-G1** | 需现场验证 tooltip 在实时环境中是否可见。R16-P2 验收通过证明源码存在，若实时不可见则根因是 CSS/条件渲染/叠层问题。 |

---

## 二、进化策略师建议（Evolution Audit Report — 7.5/10）

### CRITICAL

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| CR1 | 修复 Dataset 默认值回归——约 30 分钟 | **ACCEPT — R17-CR1** | 与体验官 CR1 为同一问题。本轮第一顺位。 |

其余 CRITICAL 建议（C1 批量导入 UI ~3 天, C2 MemoryForm imports 自动补全 ~1 天, C3 AI 辅助创建 ~2 天）均为大型功能项目，已在 R16 协商中明确延期至未来 Sprint。本轮作为纯修复轮不重新评估。

### IMPORTANT

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| I1 | Review Queue——从被动衰减告警到主动闪卡式复习机制 | **DEFER** | 已在上方体验官 Feature Ideas 中回应。约 1.5 天。留待未来 Sprint。 |
| I2 | 图-搜索联动——搜索结果高亮图上对应节点 | **DEFER** | 约 0.5 天。留待未来 Sprint。 |
| I3 | Markdown 预览——MemoryForm 中实时渲染 body 预览 | **DEFER** | 约 0.5 天。留待未来 Sprint。 |
| I4 | "Proposed" 审核队列——为 MCP proposed 记忆提供人工审核界面 | **DEFER** | 约 1 天。R16-M1 完成了工具端，审核界面是自然的下一步。但本轮不启动新功能。留待未来 Sprint。 |
| I5 | App.tsx 状态管理重构——Zustand 或 Context API 分离状态 | **DEFER** | 约 2 天。架构改进，非缺陷。留待未来 Sprint。 |
| I6 | Dashboard stale ID 可点击 | **DEFER** | 与体验官 N2 重复。留待未来 Sprint。 |
| I7 | Legend 点击高亮 | **DEFER** | 与体验官 N1 重复。留待未来 Sprint。 |
| I8 | Export-as-Context 按钮 | **DEFER** | 与体验官 F5 重复。留待未来 Sprint。 |

### Technical Health

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| TH5 | Dataset 默认值回归 | **ACCEPT — R17-CR1** | 已纳入。 |
| TH1 | App.tsx God Object | **DEFER** | 与 I5 重复。留待未来 Sprint。 |
| TH2 | 文件索引瓶颈——>1000 节点时 index.json 和全文搜索成为瓶颈 | **DEFER** | 约 4 天的 SQLite 迁移。当前 <200 条记忆，未触及瓶颈。留待未来 Sprint。 |
| TH3 | CSS 架构——70% CSS 为内联样式 | **DEFER** | 约 3 天渐进迁移。当前 12 个组件可管理。留待未来 Sprint。 |
| TH4 | 前端组件测试覆盖 | **DEFER** | 约 2 天 React Testing Library 覆盖。留待未来 Sprint。 |

---

## 三、Eval 报告发现的问题（Round 16 Eval）

| # | 发现 | 决策 | 理由 |
|---|------|------|------|
| 8.1 | `stability_source` 未在 API 响应中暴露——前端检查此字段但永不可见 | **ACCEPT — R17-G2** | 序列化缺口（非逻辑缺口）。后端 SInc 豁免正确执行，仅前端 "(manual)" 标签缺失。修复方式：在 API 响应序列化中包含此字段。约 15 分钟。 |
| 8.2 | Playwright 测试需要后端单独运行——CI 就绪缺口 | **DEFER** | 环境配置问题，非代码缺陷。当前文档可说明运行要求。留待未来 Sprint。 |
| 8.3 | FastAPI `on_event` 废弃警告——迁移至 lifespan | **ACCEPT — R17-T1** | 每次启动触发 `DeprecationWarning`。长期累积开发摩擦。约 15 分钟。 |

---

## 四、本轮接受/延期/拒绝统计

| 类别 | 数量 |
|------|------|
| **ACCEPT（本轮执行）** | 6 个任务（CR1、UX1、UX2、G1、G2、T1） |
| **DEFER（未来 Sprint）** | 29 个建议/提案 |
| **DECLINE（拒绝）** | 0 |

---

## 五、策略说明

**本轮不启动任何新功能的原因：**

1. **CR1 数据集回归的严重性。** 这是 R16-A1 APIRouter 拆分的直接后遗症——不是 demo 瑕疵，而是每个浏览器会话都初始化到错误状态的 production bug。修复 CR1 是任何进一步工作的前置条件。

2. **R16 投资循环已完成。** Rounds 12-16 交付了衰减模型正确性、全文搜索、可写 MCP 工具和 APIRouter 拆分——共 16/16 任务零回归、91/91 测试通过。这是一个强大的技术基座。在启动下一个投资循环（Sprint 17-20：冷启动 + AI Copilot）之前，需要一轮整顿来清除遗留的灰尘。

3. **体验官评分下降（8.6/10 → 7.2/10）的信号。** 功能评分从 8.5 下降到 6.5，直接归因于数据集回归——一个本应被发现的 bug。这表明测试覆盖不足——Playwright 测试当前 4/5 pass，且都针对 companion 数据集运行。修复 CR1 后，应为 investment 数据集添加 regression test。

4. **进化策略师的技术健康提醒。** 7.5/10 的评分中 engine 9.5/10、product experience 6/10 的结构值得注意——产品体验的短板主要来自"没有导入 UI"和"没有 AI 辅助创建"两个规划性决策（R16 协商中明确延期），而非本轮可修复的 bug。这意味着当前修复轮的产出将解决 9.5/10 engine 上的最后瑕疵，而不改变 6/10 product experience——后者需要下一个投资循环来解决。
