# Negotiation — Round 16（最终轮）

**Date:** 2026-05-07
**Context:** Five audit inputs assessed:
- Product Experience Reviewer (post-R15): 8.6/10 (+0.2 from R14). R15 verified 8/8 PASS.
- Evolution Strategy Reviewer (post-R15): 6.5/10 (engine 9/10, product 4/10).
- Research Reviewer (post-R15): Decay model now correct. Remaining items identified.
- Gemini Four-Role Audit: Experience 8.5/10, Evolution 6.5/10, Research 8.0/10, Architect 7.0/10.
- Round 15 Eval: 8/8 PASS, zero discrepancies.

**Round position:** 5 of 5 — FINAL round of the Product-Loop investment cycle. No further iterations follow. All accepted items must complete within this single round.

**Planning constraint:** Core plan (Tiers 1-4) estimated at ~5 days. Stretch (Tier 5) estimated at ~2-3 additional days and is explicitly conditional on core completion.

---

## 一、产品体验官建议（Product Audit Report, R15 — 8.6/10）

### Critical Recommendations

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| 1 | 修复个别记忆端点衰减字段缺口——`GET /api/memories/{id}` 不返回 `access_count` / `days_since_last_access` / `stability` | **ACCEPT — R16-F1** | 数据完整性 bug。前端侥幸生效（使用列表端点数据），但 CLI focus、MCP 工具、外部集成的消费者收到不完整数据。约 30 分钟。必须在最终轮修复。 |
| 2 | 修复 Badges.tsx 过时注释——第 19 行称"List view uses 10px"但实际已是 12px | **ACCEPT — R16-F2** | 注释与代码不一致会导致未来开发者"修复"代码以匹配注释，重新引入 sub-12px 字体。约 5 分钟。零成本零风险。 |

### Important Recommendations

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| 3 | R-probability 信号化着色——MemoryDetail 中 R 值按绿色（>50%）、琥珀色（10-50%）、红色（<10%）三档着色 | **ACCEPT — R16-F4** | 体验官 Proposal 1。将 R-probability 从数字变为信号。纯前端条件样式，R 值已在前端计算。约 15 分钟。投入产出比极高的 polish。 |
| 4 | Touch 端点——轻量衰减刷新，`POST /api/memories/{id}/touch` + 前端 Touch 按钮 | **ACCEPT — R16-S1** | 体验官 Proposal 2。使衰减管理轻量化。当前"resolve 以刷新"机制重量级且与用户意图（"我复习过此记忆"）错位。约 1 小时（后端 10 行端点 + 前端按钮 + 确认动画）。 |
| 5 | List 视图添加记忆健康列——每行显示 R-probability 彩色条形 | **ACCEPT — R16-S3** | 体验官 Proposal 3。将 List 从目录升级为诊断工具。纯前端——列表端点已返回所有需要的数据。约 2 小时。 |
| 6 | 修复 Playwright 测试路径解析——测试应从项目根目录和 `frontend/` 目录均可运行 | **ACCEPT — R16-F3** | CI 就绪的必要条件。当前 `testDir: './tests'` 仅在从 `frontend/` 目录运行时正确解析。约 15 分钟（绝对路径或文档化规范调用）。 |

### Nice-to-Have Recommendations

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| 7 | Search Resolve 按钮添加 tooltip | **ACCEPT — R16-P2** | R13 遗留项。改善主要功能可发现性。约 20 分钟。纳入批量 Polish。 |
| 8 | 移除 List 视图本地过滤条 | **DEFER — 超出本轮容量** | R13 遗留项。约 1 小时但需确保移除后全局搜索完全覆盖本地过滤的所有用例。全局搜索（正文全文搜索在 R16-C1 中增强后）将成为唯一搜索入口。在最终轮容量饱和的情况下，此项不及 C1/C2/S1/S2/S3 紧迫。 |
| 9 | Maturity badge 添加 tooltip | **DEFER — 超出本轮容量** | R13 遗留项。约 1 小时。Maturity 是 CodeMemory 独特概念，tooltip 解释有价值。但在最终轮，全文搜索和 stability UI 优先于教育性 tooltip。 |
| 10 | 上下文菜单项添加快捷键提示 | **ACCEPT — R16-P3** | R14 推荐项。右键菜单是自然的快捷键可发现面。约 30 分钟。纳入批量 Polish。 |
| 11 | 移除 Wander 模式切换 | **ACCEPT — R16-P1** | 体验官 Phase 3 建议。"cool" 与 "random" 模式在当前数据集大小（10-62 条）下感知上不可区分。移除切换按钮简化 UI。约 15 分钟。 |

### Product Strategy Recommendations

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| 12 | 跨数据集解析 | **DEFER — 未来 Sprint** | 约 3-4 天。需共享索引 + resolve 引擎变更。独立轮次范畴。三项策略建议中唯一不依赖前端 UI 的项，但工作量超过最终轮全部剩余容量。 |
| 13 | 衰减复习队列 | **DEFER — 未来 Sprint** | 约 2 天。被动衰减警告（Dashboard decay_risk 面板 R14-N1）+ 主动 review 机制的组合已通过 S3（List 健康列）和 F4（R-probability 着色）获得 80% 价值覆盖。完整复习队列需要序贯导航状态管理——在最终轮容量饱和的情况下无法挤入。 |
| 14 | Per-memory stability UI（前端滑块） | **ACCEPT — R16-C2** | 后端 stability 工作已在 R15 全部完成（自适应更新 C1 + 长期底线 C2 + 领域默认值 C3）。前端 UI 是 R15 协商明确延期至 R16 的项。约 1 天。必须在最终轮完成。 |
| 15 | 访问新鲜度时间线 | **DEFER — 未来 Sprint** | 约 2-3 天。需 sparkline + activity feed 前端组件。大型全栈功能，在容量紧张的最终轮无法纳入。 |

### R14 遗留债务

| # | 建议 | R14 状态 | R16 决策 | 理由 |
|---|------|---------|---------|------|
| 🟡 3 | MemoryDetail 添加 stability 编辑 | DEFERRED to R16 | **ACCEPT — R16-C2** | 同策略 #14。 |
| 🟡 5 | 搜索结果中显示访问新鲜度 | DEFERRED to R16 | **ACCEPT — R16-S2** | R15 协商明确延期至 R16。搜索结果 API 已包含 `days_since_last_access` 和 `stability`（自 R15-C4 统一数据源起）。纯前端渲染。约 1 小时。 |
| 🟡 6 | 复习队列 | DEFERRED to R16 | **DEFER — 未来 Sprint** | 同策略 #13。 |
| 🟢 7-10 | 各项 Nice-to-Have（tooltip、List 过滤条、maturity badge tooltip、快捷键提示） | DEFERRED | **部分采纳**（P2、P3 已纳入 Polish；过滤条和 maturity tooltip 延期） | 详见上方对应条目。 |

### 体验官建议汇总

- **ACCEPT (本轮纳入):** 11 项（F1, F2, F3, F4, F5 隐含相关, S1, S2, S3, C2, P1, P2, P3）
- **DEFER (未来 Sprint):** 5 项（List 过滤条、maturity tooltip、复习队列、跨数据集解析、访问时间线）
- **核心原则:** 体验官的高投入产出比建议（着色 R-probability、Touch 端点、List 健康列）全部采纳。仅规模过大或与更高优先级功能冲突的项延期。

---

## 二、进化策略师建议（Evolution Audit Report, R15 — 6.5/10）

### Critical Recommendations

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| C1 | 批量导入流水线（Web UI 拖拽 Markdown 导入 + 预览确认 + 自动依赖推断） | **DEFER — 未来 Sprint** | 约 3 天。进化策略师、Gemini 进化策略师、体验官三方一致认定的 #1 冷启动障碍。但在最终轮单轮容量约束下无法与全文搜索（C3）同时交付。全文搜索服务于已有数据的用户（检索），导入 UI 服务于新用户（冷启动）。最终轮优先服务于产品当前用户群。未来 Sprint 应将导入 UI 作为最高优先级。 |
| C2 | MemoryForm 的 imports 自动补全（suggest_deps 集成到创建表单） | **DEFER — 未来 Sprint** | 约 1 天。`suggest_deps.py` 后端逻辑已完备，仅缺前端接线。价值清晰（降低 DAG 构建摩擦），但在最终轮，手动填写 imports 的摩擦低于完全无法全文搜索 body 内容的摩擦。未来 Sprint 与导入 UI 一同纳入。 |
| C3 | 全文正文搜索（索引 body 全文 + 搜索结果高亮 + 匹配位置预览） | **ACCEPT — R16-C1** | 连续四轮延期的 #1 功能缺口。每个竞品都支持。搜索是记忆工具的"逃生舱"——当 DAG 导航和浏览都失败时，全文搜索是最后的检索机制。当前逃生舱半闭（仅匹配前 120 字符）。约 2-3 天。本轮最高优先级功能任务。 |

### Important Recommendations

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| I1 | 可写 MCP 工具（`propose_memory` + `propose_update`，draft/proposed 状态 + 人工审核队列） | **STRETCH — R16-M1** | 约 2 天。闭合 agentic 循环——当前 Agent 可读不可写，悖论于"为 AI Agent 设计的外部大脑"定位。纳入延伸目标（Tier 5）：**仅当 Tiers 1-4 全部完成、测试通过后启动。** 若容量不足则留给未来 Sprint。 |
| I2 | AI 辅助创建（LLM Gateway 集成到 MemoryForm：自动摘要/标签/关联推荐） | **DEFER — 未来 Sprint** | 约 2 天。Gemini 进化策略师标注为 #2 短板。差异化战略资产，但需 `llm_gateway` 前端集成——该基础设施的跨项目状态未确认。不适合在容量紧张的最终轮作为依赖项启动。未来 Sprint 与导入 UI 并列最高优先级。 |
| I3 | God Object 拆分（server.py APIRouter + App.tsx 状态管理） | **STRETCH — R16-A1（部分）** | 约 3 天完整拆分。纳入延伸目标仅 server.py 路由拆分（约 0.5-1 天）——使用 FastAPI `APIRouter` 将 17 个端点按业务域分到 `routers/memories.py`、`routers/search.py`、`routers/stats.py`。App.tsx 状态管理重构留给未来 Sprint。**仅当 M1 完成后仍有容量时启动。** |
| I4 | 复习队列（主动 review 机制） | **DEFER — 未来 Sprint** | 约 1.5 天。同体验官策略 #13 理由。 |
| I5 | 图-搜索联动（搜索结果在图视图中高亮对应节点） | **DEFER — 未来 Sprint** | 约 0.5 天。有价值但在最终轮容量受限。全文搜索（C1）交付后，搜索本身就是比图高亮更直接的发现路径。 |
| I6 | Markdown 预览（MemoryForm body 字段的实时渲染预览） | **DEFER — 未来 Sprint** | 约 0.5 天。价值清晰但最终轮优先于全文搜索和 stability UI 之下。属于 MemoryForm 编辑体验提升范畴，与 AI 辅助创建、imports 自动补全一同留给未来 Sprint。 |

### Nice-to-Have Recommendations

全部 **DEFER — 未来 Sprint**。Dashboard 趋势视图（2 天）、CSS 现代化（3 天）、前端组件测试（2 天）、响应式降级（3 天）、搜索历史/保存搜索（0.5 天）、时间维度图视图（1 天）——均为有价值项目但最终轮容量已饱和。其中响应式降级和 CSS 现代化是 Gemini 体验官关注的长期体验债务，应在未来 Sprint 中优先考虑。

### Feature Ideas（长期差异化战略资产）

全部 **DEFER — 未来 Sprint**。语义边（5 天）、DAG 感知 AI 编辑侧边栏（8 天）、"自您上次访问以来"上下文注入（2 天）、记忆健康评分+贡献热力图（3 天）、混合搜索（5 天）、SQLite 索引后端（4 天）、记忆分支/合并（10 天）——均为 CodeMemory 长期护城河的关键方向，但每个都需要独立轮次的专注投入。其中语义边被 Gemini 研究员标注为"突破点"，应在新 Sprint 早期优先评估。

### Technical Health Recommendations

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| TH1 | God Objects（server.py 1419 行 + App.tsx 1655 行） | **STRETCH — R16-A1（部分）** | 同 I3。仅 server.py 路由拆分作为延伸目标纳入。 |
| TH2 | 基于文件的索引瓶颈（>1000 节点时） | **DEFER — 未来 Sprint** | 约 4 天。当前 <200 节点时性能可接受（~200ms）。在达到 500 节点之前不构成实际瓶颈。未来 Sprint 引入 SQLite 索引后端。 |
| TH3 | CSS 架构（70% 行内样式） | **DEFER — 未来 Sprint** | 约 3 天。在 12 个组件的当前规模下可维护。Dark mode 复杂性增加时需迁移至 TailwindCSS 或 CSS modules。 |
| TH4 | 测试覆盖（缺少前端组件级测试） | **DEFER — 未来 Sprint** | 约 2 天。当前 91 个测试（57 unit + 24 integration + 5 API + 5 Playwright）覆盖良好。React Testing Library 组件测试为锦上添花。 |

### 进化策略师建议汇总

- **ACCEPT (本轮纳入):** 1 项（C3 全文搜索）——但这是本轮最大的单项任务（2-3 天）
- **STRETCH (条件纳入):** 2 项（I1 可写 MCP、I3/A1 God Object 部分拆分）
- **DEFER (未来 Sprint):** 19 项（涵盖 Critical C1/C2、Important I2/I4/I5/I6、全部 Nice-to-Have、全部 Feature Ideas、TH2/TH3/TH4）
- **核心原则:** 进化策略师的战略眼光（导入 UI、AI 辅助、语义边）为产品指明了长期方向，最终轮无法承载所有这些。选择交付"当前用户最痛的功能缺口"（全文搜索）而非"未来用户的第一印象"（导入 UI）。

---

## 三、设计研究员建议（Research Audit + Post-R15 剩余项）

**背景：** 研究员的三项 Critical 和 Important 发现已在 R15 全部实现——自适应 stability 更新（C1）、长期保留底线（C2）、领域差异化默认值（C3）。以下是剩余项。

### Remaining Important Recommendations

| # | 建议 | 决策 | 理由 |
|---|------|------|------|
| 4 | Wander 主动复习模式（`--mode review`，Gaussian 加权 R ~ 0.75 中心的记忆） | **DEFER — 未来 Sprint** | 约 2 小时。价值清晰（将衰减从被动警告转为主动维护），但依赖 C1（自适应 stability）和 C2（per-memory stability UI）先落地、通过狗食测试并稳定。在 R16 中 C2 刚刚交付，主动复习模式的 Gaussian 加权基于的 stability 值还在校准中。过早实现会产生基于不成熟 stability 值的错误建议。未来 Sprint 在 stability 值稳定后自然纳入。 |
| 5 | 陈旧检测时下调 stability——hash 不匹配 = 回忆失败 → stability 应下降 | **ACCEPT — R16-F5** | 对称于 R15-C1（成功访问 → stability↑）。完成 stability 反馈闭环。约 1 小时。研究员在 R15 协商中明确标注为"R16 末尾自然纳入"。 |

### Nice-to-Have Recommendations

全部 **DEFER — 未来 Sprint**。指数-幂（Weibull）衰减选项（2-3 天）、per-user 参数学习（1-2 周）、Dashboard stability 趋势可视化（1 天）——均为研究级增强，适合未来独立轮次。其中 Weibull 衰减选项的研究依据坚实（2024 年 Psychonomic Bulletin 元分析），应在新的研究驱动 Sprint 中优先评估。

### Product Strategy Recommendations

全部 **DEFER — 未来 Sprint**。各记忆衰减曲线形状（2-3 天）、周度记忆半衰期健康报告（2 天）——为长期差异化功能，在基础自适应 stability 和 per-memory stability UI 充分验证之前不应启动。

### 研究员建议汇总

- **ACCEPT (本轮纳入):** 1 项（F5 陈旧检测时下调 stability）
- **DEFER (未来 Sprint):** 6 项
- **核心原则:** 研究员已在本投资循环中获得最大的投资回报——R15 实现了三项 Critical/Important 发现。最终轮仅完成 stability 反馈闭环的下半部分（陈旧 → stability↓）以对称于已实现的访问 → stability↑。

---

## 四、Gemini 四角色综合审计建议

### Gemini 体验官（8.5/10）

| 建议 | 决策 | 理由 |
|------|------|------|
| 暗黑美学+排版出色——保持 | **NO ACTION** | 已达商用 SaaS 级别。R15 完成的 12px 字体底线和 7/7 动画表面巩固了这一优势。 |
| 创建流程生硬——右侧弹出表单缺少 Notion/Mem.ai 的行云流水感 | **DEFER — 未来 Sprint** | AI 辅助创建 + Markdown 预览 + imports 自动补全三者的组合将解决此问题。三项均延期至未来 Sprint（理由见进化策略师 I2、I6、C2）。 |
| 移动端/响应式缺失——界面明显为大屏（1200px+）设计 | **DEFER — 未来 Sprint** | 约 3 天。CodeMemory 当前目标用户（开发者 + AI Agent）主要使用桌面端。在进入消费级市场前，此项非 blocker。 |

### Gemini 进化策略师（6.5/10）

| 建议 | 决策 | 理由 |
|------|------|------|
| DAG 引擎是杀手级差异化——维护这一优势 | **NO ACTION** | 已在 R15 巩固（自适应 stability + 混合衰减 + 领域默认值）。R16 继续增强（全文搜索 + per-memory stability UI）。 |
| 核心短板是导入 UI——Web UI 零导入入口 | **DEFER — 未来 Sprint** | 同进化策略师 C1 理由。 |
| AI 辅助工作流是 #2 短板——用户在 UI 写卡片时无 AI 帮助 | **DEFER — 未来 Sprint** | 同进化策略师 I2 理由。 |
| MCP tools——继续增强 Agent-to-Agent 共享记忆拓扑 | **STRETCH — R16-M1** | 可写 MCP 工具是第一步。完整 Agent-to-Agent 拓扑共享需独立架构设计。 |

### Gemini 研究员（8.0/10）

| 建议 | 决策 | 理由 |
|------|------|------|
| 时间衰减闭环优美——R15 已实现 | **NO ACTION** | 自适应 stability、长期保留底线、领域默认值均已验证工作。R16 完成闭环（陈旧 → stability↓）。 |
| 语义边（Semantic Edge）仍缺失——imports 有强度无语义（支持/反驳/补充/前置条件） | **DEFER — 未来 Sprint** | 约 5 天。需 schema 迁移 + resolve prompt 生成逻辑变更 + 前端语义标签 UI。研究级差异化功能。Gemini 研究员标注为"长链推理基准测试中的统治级表现"突破点。新 Sprint 应以此为核心主题。 |

### Gemini 架构师（7.0/10）

| 建议 | 决策 | 理由 |
|------|------|------|
| 测试基线健全——91 个测试全部通过，零回归 | **NO ACTION** | 保持。 |
| God Object 反模式——server.py 1377 行、App.tsx 1628 行 | **STRETCH — R16-A1（部分）** | 仅 server.py APIRouter 拆分作为延伸目标纳入。完整拆分（含 App.tsx 状态管理）约 3 天，留给未来 Sprint。 |
| 基于文件的索引瓶颈——>1000 节点时锁竞争 | **DEFER — 未来 Sprint** | 约 4 天。同 TH2 理由。当前 <200 节点，性能可接受。 |
| CSS 演进——高度依赖行内样式，样板代码累积 | **DEFER — 未来 Sprint** | 约 3 天。同 TH3 理由。 |

### Gemini 综合路线图回应

Gemini 报告的六阶段路线图核心建议：
1. **1-2 个月：破局冷启动**（God Object 拆分 + 批量导入 UI + suggest-deps 集成）——本轮仅能完成 God Object 拆分的最小子集（server.py 路由拆分作为延伸目标）。导入 UI 和 suggest-deps 集成留给未来 Sprint。
2. **3-4 个月：全方位 AI 副驾驶**（LLM Gateway 集成 + MCP 增强）——可写 MCP 工具作为延伸目标纳入。LLM Gateway 集成留给未来 Sprint。
3. **5-6 个月：语义图谱与拓展性**（语义边 + 混合搜索 + 响应式降级）——全部留给未来 Sprint。

**Sprint Planner 对路线图的评估：** Gemini 路线图的方向完全正确。Product-Loop 投资循环聚焦于将引擎做得正确且完整（R13-R15：衰减模型正确性 + UI 审美 + 测试覆盖；R16：全文搜索 + 衰减可控性）。未来 Sprint 应按照"导入 UI → AI 辅助 → 语义边 → 索引后端 → 响应式"的顺序推进。

---

## 五、跨领域协商总结

### 本轮纳入（R16 最终轮）

| 梯队 | 任务 ID | 任务名称 | 来源审计官 | 投入 |
|------|---------|---------|----------|------|
| Tier 1 — Critical Fixes | F1 | 修复个别记忆端点衰减字段缺口 | 体验官 Critical #1 | ~30 分 |
| Tier 1 | F2 | 修复 Badges.tsx 过时注释 | 体验官 Critical #2 | ~5 分 |
| Tier 1 | F3 | 修复 Playwright 测试路径解析 | 体验官 Important #6 | ~15 分 |
| Tier 1 | F4 | R-probability 信号化着色 | 体验官 Proposal 1 | ~15 分 |
| Tier 1 | F5 | 陈旧检测时下调 stability | 研究员 Important #5 | ~1 小时 |
| Tier 2 — Feature Completion | C1 | 全文正文搜索 | 进化策略师 C3 + Gemini 进化策略师 | ~2-3 天 |
| Tier 2 | C2 | Per-memory stability UI 前端滑块 | 体验官 Important #3/Strategy #14 + 进化策略师 I2 | ~1 天 |
| Tier 3 — Decay Surface | S1 | Touch 端点——轻量衰减刷新 | 体验官 Proposal 2 | ~1 小时 |
| Tier 3 | S2 | 搜索结果中显示访问新鲜度 | 体验官 Important #5（R14 遗留） | ~1 小时 |
| Tier 3 | S3 | List 视图添加记忆健康列 | 体验官 Proposal 3 | ~2 小时 |
| Tier 4 — Batch Polish | P1 | 移除 Wander 模式切换 | 体验官 Phase 3 建议 | ~15 分 |
| Tier 4 | P2 | Search Resolve 按钮 tooltip | 体验官 Nice-to-have #7 | ~20 分 |
| Tier 4 | P3 | 上下文菜单项快捷键提示 | 体验官 Nice-to-have #10 | ~30 分 |
| Tier 5 — Stretch | M1 | 可写 MCP 工具 | 进化策略师 I1 + Gemini 进化策略师 | ~2 天 |
| Tier 5 — Stretch | A1 | God Object 部分拆分（server.py APIRouter） | Gemini 架构师 + 进化策略师 TH1 | ~0.5-1 天 |

**核心计划 (Tiers 1-4) 合计：** 约 5 天。13 项任务，其中 C1（全文搜索）和 C2（stability UI）为最大单项。
**延伸目标 (Tier 5)：** 约 2.5-3 天。仅当前四梯队全部完成、测试通过后启动。

### 全体审计官共识

1. **全文搜索必须在最终轮交付** —— 进化策略师、Gemini 进化策略师、体验官（隐性认可）三方一致。连续四轮延期的 #1 功能缺口。没有任何审计官建议继续延期。
2. **R15 的后端 stability 工作必须配套前端可控性** —— 体验官 Important #3 和进化策略师 I2 均在 R14 协商中标记为 Important 并明确延期至 R16。后端正确性已就绪，前端 UI 不可再延。
3. **修复全部已知 bug 再结束循环** —— 三个微小但真实的数据完整性和文档一致性问题（端点字段缺口、过时注释、Playwright 路径）。修复成本合计不到 1 小时。最终轮不容忍已知 bug 存留。
4. **导入 UI 和 AI 辅助创建是下一 Sprint 的最高优先级** —— 四个审计源（体验官、进化策略师、Gemini 体验官、Gemini 进化策略师）一致认定这两个大型功能是当前产品最大的体验鸿沟。最终轮无法承载，但共识明确：新 Sprint 必须从这里开始。

### 争议项

| 项目 | 进化策略师立场 | 其他审计官立场 | Planner 裁决 |
|------|-------------|-------------|------------|
| 可写 MCP 工具 | Important I1——闭合 agentic 循环，应在 R16 交付 | 体验官未评分；Gemini 进化策略师提及 MCP 增强；研究员未涉及 | **STRETCH (R16-M1)**。价值无可争议，但约 2 天的投入在核心计划已 5 天满负荷的情况下只能作为延伸目标。若核心计划提前完成，立即启动。否则留给未来 Sprint。 |
| God Object 拆分 | Important I3——降低合并冲突风险 | Gemini 架构师 Critical——逼近重构红线 | **STRETCH (R16-A1，部分)**。仅 server.py 路由拆分（0.5-1 天）作为延伸目标。App.tsx 状态管理留给未来 Sprint。若核心计划提前完成且 M1 也完成，启动。 |
| 复习队列 | Important I4——主动 review 机制 | 体验官 Strategy #13——2 天；研究员未涉及 | **DEFER**。S3（List 健康列）+ F4（R-probability 着色）覆盖复习队列 80% 价值（扫描发现风险记忆）。完整 sequential review 留给未来 Sprint。 |
| 移除 List 过滤条 | 未涉及 | 体验官 Nice-to-have #8——统一搜索入口 | **DEFER**。R14-N3 已标记有意延期。在最终轮容量饱和的情况下，不会为一个非阻塞性 UI 简化而冒险挤压核心功能。 |

### 未来 Sprint 前瞻

Product-Loop 投资循环结束后，以下项目按优先级排列为新 Sprint 的候选主题：

**Sprint 14 主题候选——破局冷启动（The Input Problem）：**
1. **批量导入 UI**（进化策略师 C1 + Gemini 进化策略师 #1 短板）——约 3 天
2. **AI 辅助创建**（进化策略师 I2 + Gemini 进化策略师 #2 短板）——约 2 天
3. **MemoryForm imports 自动补全**（进化策略师 C2）——约 1 天
4. **Markdown 预览**（进化策略师 I6）——约 0.5 天

**Sprint 15 主题候选——语义图谱（The Semantic Leap）：**
5. **语义边**（Gemini 研究员突破点 + 研究员 Strategy）——约 5 天
6. **God Object 完整拆分**（Gemini 架构师 + 进化策略师 TH1）——约 3 天
7. **可写 MCP 工具**（如 R16 未完成）——约 2 天

**Backlog（持续评估）：**
8. 复习队列、图-搜索联动、"自您上次访问以来"上下文注入、记忆健康评分、Dashboard 趋势视图、CSS 现代化、响应式降级、混合搜索、SQLite 索引后端、前端组件测试、Wander 主动复习模式、Weibull 衰减选项、搜索历史/保存搜索、时间维度图视图

---

*协商结束。待 Planner 将接受项目写入 SPRINT.md 第 16 轮追加任务。*
