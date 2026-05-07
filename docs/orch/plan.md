# Round 16 任务计划 — Closure

**生成日期：** 2026-05-07
**上轮评估：** Round 15 — 8/8 PASS，零回归（86/86 测试 + 5/5 Playwright + TypeScript 零错误 + Vite 构建成功）。
**本轮主题：** 闭环 —— 交付两个最长延期功能、完成衰减管理表面、修复所有已知 bug、清缴最多 polish 债务。
**本轮定位：** 投资循环 5/5 —— 最终轮。本轮之后无后续迭代。所有任务必须在本轮内完成。

---

## 一、本轮聚焦

Round 16 是 Product-Loop 投资循环的最后一轮。所有四个审计源一致认定本轮应聚焦于：

1. **交付全文正文搜索** —— 连续延期 R12/R13/R14/R15 四轮的 #1 功能缺口。每个竞品都支持。进化策略师、体验官、Gemini 进化策略师、Gemini 研究员全部标注为关键缺失。本轮必须交付。
2. **完成衰减管理表面** —— R15 完成了衰减模型的正确性（自适应 stability、长期保留底线、领域默认值）。R16 必须使其对用户可控：per-memory stability UI 滑块、Touch 轻量刷新、陈旧检测时的 stability 下调。
3. **修复所有已知 bug** —— 个别端点数据缺口、过时注释、Playwright 路径问题、R-probability 缺乏信号化着色。
4. **清缴最多 polish 债务** —— 多轮延期的 tooltip、Wander 模式切换移除、上下文菜单快捷键提示等项目。

刻意排除本轮的大型项目（留给未来 Sprint）：导入 UI、AI 辅助创建、语义边扩展、God Object 完整拆分、跨数据集解析。

---

## 二、任务拆解

### 第一梯队：关键修复（必达，< 3 小时合计）

| # | 任务 | 为何纳入 | 审计来源 |
|---|------|---------|---------|
| **F1** | 修复个别记忆端点衰减字段缺口 | `GET /api/memories/{id}` 不返回 `access_count` / `days_since_last_access` / `stability`，尽管 `server.py:407-414` 代码意图添加。前端侥幸生效（使用的是列表端点数据），但 CLI focus、MCP 工具、外部集成的消费者会收到不完整数据。数据完整性 bug。约 30 分钟。 | 体验官 Critical #1（R15 报告） |
| **F2** | 修复 Badges.tsx 过时注释 | `Badges.tsx:19` 注释称"List view uses 10px"，但实际代码和 List 视图均为 12px。注释与代码不一致会导致未来开发者"修复"代码以匹配注释，重新引入 sub-12px 字体。约 5 分钟。 | 体验官 Critical #2（R15 报告） |
| **F3** | 修复 Playwright 测试路径解析 | 测试从 `frontend/` 目录运行正确（5/5 pass），但从项目根目录运行时 `test.describe()` 报错。`playwright.config.ts` 使用相对路径 `testDir: './tests'` 仅从 `frontend/` 解析。阻碍 CI 流水线自动化。约 15 分钟。 | 体验官 Important #6（R15 报告） |
| **F4** | R-probability 信号化着色 | MemoryDetail 的 Access Freshness 区域将 R-probability 显示为纯数字。用户需自行判断 6.3% 是好是坏。应基于三档着色：绿色（>50%，健康）、琥珀色（10-50%，适中）、红色（<10%，风险）。使用已有 CSS 颜色变量 `--cm-success` / `--cm-warning` / `--cm-error`。纯前端条件样式，R 值已在前端计算。约 15 分钟。 | 体验官 Proposal 1（R15 报告） |
| **F5** | 陈旧检测时下调 stability | 当 `resolve` 检测到 summary_hash 不匹配（陈旧提醒），应将 stability 下调作为"回忆失败"信号。对称于 R15-C1 的"成功访问时上调 stability"。完成 stability 反馈闭环：成功回忆 → stability↑，检测陈旧 → stability↓。约 1 小时。 | 研究员 Important #5（审计报告）+ R15 协商明确延期至 R16 |

### 第二梯队：长期延期功能（必达，约 3-4 天）

| # | 任务 | 为何纳入 | 审计来源 |
|---|------|---------|---------|
| **C1** | 全文正文搜索 | 连续四轮延期（R12/R13/R14/R15）的 #1 功能缺口。当前搜索仅匹配 ID、summary、tags 和 body 前 120 字符。用户若只记得正文中的关键概念但忘了 ID 或摘要措辞，无法找到记忆。搜索是记忆工具的"逃生舱"——当前逃生舱半闭。需搜索管道重构（索引 body 全文）+ 前端搜索结果高亮 + 匹配位置预览。约 2-3 天。 | 进化策略师 C3（最新报告）+ 体验官未评分但认可 + Gemini 进化策略师 C4 |
| **C2** | Per-memory stability UI（前端滑块） | R15 完成了所有后端 stability 工作：自适应更新（C1）、长期保留底线（C2）、领域差异化默认值（C3）。但用户无法手动调整 stability——所有交互都通过 resolve/reindex 自动触发。前端滑块使高级用户可以按记忆类型微调半衰期。R14 协商中体验官 Important #3 和进化策略师 I2 均标记为 Important。约 1 天。 | 体验官 Important #3（R14）+ 进化策略师 I2（R14）+ R15 协商明确延期至 R16 |

### 第三梯队：衰减管理轻量化（应达，约 5 小时）

| # | 任务 | 为何纳入 | 审计来源 |
|---|------|---------|---------|
| **S1** | Touch 端点——轻量衰减刷新 | 当前唯一刷新记忆衰减时钟（更新 `last_access`）的方式是运行 Resolve——但 Resolve 是重量级操作（加载完整 DAG、渲染图节点）。用户只想标记"我已复习此记忆"时不应需要加载依赖图。新增 `POST /api/memories/{id}/touch`：更新 `last_access` 为现在 + 重新计算 stability，无需触发 DAG 解析。前端在 MemoryDetail 的 Access Freshness 区域添加"Touch"按钮，点击后显示短暂确认动画（对勾脉冲），"X days ago" 变为 "just now"。约 1 小时。 | 体验官 Proposal 2（R15 报告） |
| **S2** | 搜索结果中显示访问新鲜度 | R14 协商将此项（Important #5）延期至 R16。搜索结果的每条条目旁显示 `days_since_last_access` 和 R-probability（使用与 MemoryDetail 相同的信号化着色）。数据已在搜索 API 响应中（自 R15-C4 统一数据源起）。纯前端渲染。约 1 小时。 | 体验官 Important #5（R14）+ R15 协商 "search result access recency" |
| **S3** | List 视图添加记忆健康列 | List 视图是产品的"一览"界面。当前展示丰富元数据（ID、summary、type、maturity、status、tags）但无衰减信息。新增紧凑的"Health"列：每个记忆行显示彩色水平条形（绿色/琥珀色/红色对应 R-probability 三档），点击健康指示器打开该记忆的 MemoryDetail 并自动展开 Access Freshness 区域。列表端点已返回所有需要的数据。纯前端。约 2 小时。 | 体验官 Proposal 3（R15 报告） |

### 第四梯队：批量 Polish（容量允许时，约 2 小时）

| # | 任务 | 为何纳入 | 审计来源 |
|---|------|---------|---------|
| **P1** | 移除 Wander 模式切换 | Wander 模态的 "cool" vs "random" 模式切换在当前数据集大小（10-62 条）下产生感知上相同的结果。仅数据量 200+ 时才可区分。移除切换按钮，默认使用 "cool" 模式（更有用）。约 15 分钟。 | 体验官 Phase 3 建议（R15 报告） |
| **P2** | Search Resolve 按钮添加 tooltip | R13 遗留项。搜索结果的 "Resolve →" 按钮缺少 tooltip 解释功能（"Resolve this memory's dependency graph"）。改善主要功能的可发现性。约 20 分钟。 | 体验官 Nice-to-have #7（R14 遗留） |
| **P3** | 上下文菜单项添加快捷键提示 | R14 推荐项。图节点右键菜单（Edit / Delete / Resolve）自然适合展示键盘快捷键（如 "Ctrl+E" / "Delete" / "Ctrl+R"），作为快捷键可发现面。当前仅展示纯文本标签。约 30 分钟。 | 体验官 Nice-to-have #10（R14 遗留） |

### 第五梯队：延伸目标（仅当前四梯队提前完成时）

| # | 任务 | 为何纳入 | 审计来源 |
|---|------|---------|---------|
| **M1** | 可写 MCP 工具（propose_memory + propose_update） | 5 个 MCP 工具中 4 个标记为 `readOnly`。Agent 可读不可写——对于一个定位为"AI Agent 外部大脑"的系统构成悖论。实现 `propose_memory` 和 `propose_update` 工具：写入 `maturity: draft` + `status: proposed`，需人工审核。闭合 agentic 循环。约 2 天。**仅在 C1+C2+S1+S2+S3 全部完成且测试通过后启动。** | 进化策略师 I1（最新报告）+ Gemini 进化策略师 |
| **A1** | God Object 部分拆分——server.py APIRouter | `server.py` 达 1419 行，17 个端点全在一个文件。按业务域拆分为 `routers/memories.py`、`routers/search.py`、`routers/stats.py` 等使用 FastAPI `APIRouter`。仅做后端路由拆分（不碰 App.tsx），降低合并冲突风险并为未来团队扩展铺路。约 0.5-1 天。**仅在 M1 完成后仍有容量时启动。** | Gemini 架构师 + 进化策略师 TH1 |

---

## 三、排除项（本轮不纳入）

| 功能 | 排除理由 |
|------|---------|
| **导入 UI（拖拽 Markdown 批量导入）** | 约 3 天。大型全栈功能。本轮已被全文搜索 + stability UI 占满容量。留给未来 Sprint。虽然 Gemini 进化策略师标注为"冷启动障碍"且体验官和进化策略师均列为 Critical（C1），但在最终轮单轮内无法与全文搜索同时交付。 |
| **AI 辅助创建（LLM Gateway 集成到 MemoryForm）** | 约 2 天。需 `llm_gateway` 前端集成。差异化战略资产，但依赖尚未就绪的跨项目基础设施。留给未来 Sprint。 |
| **语义边（semantic_type on imports）** | 约 5 天。需 schema 迁移 + resolve prompt 生成逻辑变更。研究级差异化功能，不适合在容量紧张的最终轮启动。Gemini 研究员标注为核心突破点，但属于长期战略投资。 |
| **复习队列（Review Queue）** | 约 1.5-2 天。中型功能，但在最终轮容量已被 C1+C2+S1+S2+S3 填满的情况下无法挤入。衰减风险已在 Dashboard decay_risk 面板中被动暴露（R14-N1），S3 的 List 健康列提供扫描能力——两者结合覆盖了复习队列 80% 的价值。 |
| **跨数据集解析** | 约 3-4 天。需共享索引 + resolve 引擎变更。独立轮次范畴。 |
| **Markdown 预览（MemoryForm 中）** | 约 0.5 天。价值清晰但在最终轮优先于全文搜索和 stability UI 之下。 |
| **完整 God Object 拆分（含 App.tsx 状态管理）** | 约 3 天。仅 server.py 路由拆分（A1）作为延伸目标纳入。完整拆分留给未来 Sprint。 |
| **图-搜索联动（搜索结果在图视图中高亮）** | 约 0.5 天。有价值但在最终轮容量受限。全文搜索（C1）交付后，搜索本身就是比图高亮更直接的发现路径。 |

---

## 四、成功标准

### 第一梯队（不可协商）
1. `GET /api/memories/{id}` 返回 `access_count`、`days_since_last_access`、`stability` 字段——与列表端点行为一致
2. `Badges.tsx` 注释与实际代码一致——提及 12px 而非 10px
3. `npx playwright test` 从项目根目录和 `frontend/` 目录均可运行，5/5 通过
4. MemoryDetail 中 R-probability 值基于 R > 50%、10-50%、< 10% 三档着色（绿/琥珀/红）
5. `resolve` 检测到 summary_hash 不匹配时下调 stability——完成反馈闭环

### 第二梯队（预期达成）
6. 全局搜索返回匹配 body 全文的结果——不限于前 120 字符或仅 ID/summary/tags 匹配
7. 搜索结果高亮 body 中的匹配词；显示匹配片段及位置
8. MemoryDetail（或 MemoryForm）中存在 per-memory stability 滑块——用户可手动调整半衰期天数

### 第三梯队（期望达成）
9. `POST /api/memories/{id}/touch` 端点存在并更新 `last_access`、重算 `stability`
10. MemoryDetail 中存在 "Touch" 按钮——点击后显示确认动画，"Last accessed" 变为 "just now"
11. 搜索结果条目显示 `days_since_last_access` 和信号化着色的 R-probability
12. List 视图存在 "Health" 列——每行显示彩色 R-probability 条形

### 第四梯队（容量允许时达成）
13. Wander 模态无 "cool" / "random" 模式切换按钮——简化为单一 "Wander" 按钮
14. 搜索结果的 "Resolve →" 按钮有 tooltip 解释功能
15. 图节点右键菜单项显示键盘快捷键提示

### 延伸目标（仅当前四梯队完成后）
16. 2 个新 MCP 工具（`propose_memory`、`propose_update`）存在、可被发现、以 draft/proposed 状态写入
17. `server.py` 拆分为 3+ 个 APIRouter 模块——每个模块对应一个业务域

### 回归关卡（全部梯队共用）
- 57/57 单元测试通过
- 24/24 集成测试通过
- 5/5 API 测试通过
- 5/5 Playwright 测试通过
- TypeScript 零错误
- Vite 构建成功
- 所有 17+ 个后端端点正常响应

---

## 五、风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 全文搜索实现复杂度超预期（正文索引 + 多文件读取性能） | 中 | 高——阻塞本轮最大功能 | 如全文遍历不可行，退回到"body 全文纳入搜索 token 但不做复杂索引"方案。优先保证功能正确性，性能优化后续。 |
| 全文搜索 + stability UI 合计 3-4 天已接近单轮容量上限 | 中 | 高——可能挤占 S1/S2/S3 和 Polish | C1 和 C2 为刚性任务。如时间紧张，S2（搜索结果访问新鲜度）和 S3（List 健康列）可降级为仅 UI 不交互（无点击跳转）。Polish（P1-P3）和延伸目标（M1、A1）最先被裁减。 |
| stability 滑块变更被 resolve 的自适应更新覆盖 | 低 | 中——用户困惑 | 显式手动设置的 stability 应标记（添加 `stability_source: "manual"` 字段），resolve 的自适应更新仅应用于 `stability_source != "manual"` 的记忆。或采用更简单方案：滑块设置的是"基础 stability"，自适应更新在此基础上叠加。 |
| Touch 端点与 resolve 的 `last_access` 更新冲突 | 低 | 低 | Touch 和 Resolve 都更新 `last_access` 为 now。两者无冲突——都是合理的"访问"语义。Touch 仅跳过了 DAG 解析。 |
| 可写 MCP 工具的安全边界设计复杂（propose → review → approve 流程） | 中 | 高——如超出延伸时间则放弃 | 延伸目标明确标记为"仅当前四梯队完成后"。如未启动则不在本轮交付范围。 |

---

*计划结束。进入协商环节。*
