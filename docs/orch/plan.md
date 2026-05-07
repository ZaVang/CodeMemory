# Round 14 任务计划 — Bug Fix & Polish Completion

**生成日期：** 2026-05-07
**上轮评估：** Round 13 — 10/11 FULL PASS + 1 PARTIAL PASS，86/86 测试通过，零回归。但研究员发现 CRITICAL bug: 统一衰减公式从未在 overview 路径中激活。
**本轮主题：** 修复致命 bug + 完成 R13 遗留工作 + 添加安全防护。不做大型功能、不添新依赖。

---

## 一、本轮聚焦

Round 13 的 eval 结果看似优秀（10/11 PASS），但研究员的深度代码审查揭示了一个 CRITICAL bug：`handle_overview()` 从搜索结果字典中读取 `days_since_last_access`，而 `search()` 函数从未在输出中包含此字段。结果：R13 的旗舰功能——统一衰减公式 `0.5^(days/stability)`——在 overview 路径中从未被激活。所有被访问过的记忆回退到 R13 之前的 `access * 0.1` 常量乘数。86 个测试通过是因为它们验证的是旧公式的输出，而非新公式。

同时，体验官确认三项 R13 承诺仍未完成：模态退场动画（Wander/Validate/Archive）、9px 字体残留（HelpPanel 2 处 + MemoryDetail 1 处）、Search Resolve 按钮以 10px 字号发布。进化策略师建议"先关缺口再深挖功能"。

**本轮核心指令：修复、完成、防护。不建新功能。**

---

## 二、任务清单

### 第一梯队：Critical — 修复阻塞正确性的 Bug

| # | 任务 | 说明 | 成本 | 来源 |
|---|------|------|------|------|
| **C1** | 修复 overview 衰减公式管道 bug | `handle_overview()` 从 search 结果字典而非 MemoryEntry 对象读取 `days_since_last_access`——但 `search()` 不在输出中包含此字段。统一衰减公式 `0.5^(days/stability)` 从未在 overview 路径中激活。所有被访问过的记忆回退到正确的 R13 之前的 `access * 0.1`。修复：确保 overview 从 MemoryEntry 对象读取数据；同步在 search 输出字典中添加 `days_since_last_access` 和 `stability`。 | 极低（~3 行） | 研究员 Critical（R-RED-1） |
| **C2** | 添加 stability 边界防护 | 三个未防护的边界情况：(a) `stability=0` 导致 `ZeroDivisionError` 崩溃，(b) `stability<0` 产生 `decay>1.0`（无意义——记忆随时间的推移"增强"），(c) `days_since_last_access=None` 在 overview（意外回退到旧公式）和 wander（有意的最大冷却权重）之间语义不一致。修复：对 `stability` 添加 Pydantic 验证器（`gt=0`，建议最低 0.1）；在所有三个消费点（overview、wander、validate）中统一 `None` 语义。 | 低（~8 行） | 研究员 Critical（R-RED-2, R-RED-3） |
| **C3** | 在 API 响应中暴露衰减字段 | 在 search 输出字典中添加 `stability` 和 `days_since_last_access`。在 `/api/memories` 响应中添加 `access_count`、`last_access`、`days_since_last_access`、`stability`。在 `/api/stats` 中添加 `decay_risk` 数组（R < 0.1 的记忆）。衰减模型完全不可见——仅存在于后端。不暴露这些字段，任何"记忆健康"功能都无法构建。 | 低（~15 行） | 体验官（Yellow #4）、研究员（R-RED-4） |

### 第二梯队：Important — 完成 R13 未竟的承诺

| # | 任务 | 说明 | 成本 | 来源 |
|---|------|------|------|------|
| **I1** | 接线模态退场动画 | 将 `useExitAnimation` 导入 Dashboard Modal 函数和 App.tsx 中的 Archive 确认模态。在关闭时应用 `modal-fade-exit` / `backdrop-fade-exit` CSS 类。也接入 HelpPanel。 | 低（~25 行） | 体验官 Critical #1、进化策略师 C2 |
| **I2** | 修复所有 sub-12px 字体 | 提升：HelpPanel 键帽（9px→11px）、HelpPanel 描述（9px→11px）、MemoryDetail 空文本（9px→11px）、Search Resolve 按钮（10px→12px）、视图快捷键提示（10px→11px）、搜索片段（11px→12px）、撤销 toast 详情（11px→12px）。 | 极低（~7 行） | 体验官 Critical #2、#3 |

### 第三梯队：Nice to Have — 小范围高价值改进（容量允许）

| # | 任务 | 说明 | 成本 | 来源 |
|---|------|------|------|------|
| **N1** | 在 Dashboard 中暴露衰减风险 | 在 Dashboard 统计中添加"衰减风险"部分：R < 0.1 的记忆数量，距离阈值最近的 top 3 记忆。这是让衰减模型变得可见的最小前端改动。 | 低（~30 行） | 体验官 Proposal 1、进化策略师 I5 |
| **N2** | 图节点右键菜单添加 Resolve | 在图节点右键菜单中添加"Resolve"选项，打开 MemoryDetail 面板并附带已解析的上下文。图视图目前无 Resolve 路径。 | 低（~15 行） | 体验官 Yellow #5 |
| **N3** | 移除 List 视图本地过滤条 | 移除 MemoryList.tsx 中重复的过滤 UI。本地过滤条 80% 与全局 SearchBar 功能重叠，但产生不同结果（客户端子串匹配 vs 服务器端模糊匹配）。 | 极低（~1 小时） | 体验官 Green #8 |

---

## 三、明确延期至 Round 15+ 的项目

| 项目 | 理由 |
|------|------|
| **全文正文搜索**（进化策略师 C1/C4） | 与所有竞品相比最大的功能缺口。需要搜索管道变更 + 前端接线。需要独立搜索轮次（3-5 天）。由产品审查员和进化策略师双方延期。 |
| **Playwright 冒烟测试（5 个测试）** | 进化策略师标记为 C3 纳入本轮，但新增开发依赖 + 配置 Playwright + 编写 5 个测试超出修复/完工轮次的范围。需独立基础设施轮次或作为 R15 首个任务。 |
| **FSRS 自适应稳定性（per-memory SInc）** | 高研究价值，但需要 resolve/focus 中的新更新逻辑（约 60 LOC）+ 行为变更。稳定性字段已存在；自适应更新应在基础管道验证正确后进行。 |
| **可写 MCP 工具（create_memory, update_memory）** | 闭合 agentic 闭环（对 Mem0 的重大差异化优势）。需要 MCP 工具设计 + 安全边界（propose_* 暂存模式）。约 150 LOC。中等投入。 |
| **衰减热力图 Dashboard（完整可视化）** | 产品审查员 Proposal 1 — 未构建的最高影响力产品功能。需要 2-3 天。需先完成 C1（Bug 修复）和 C3（API 暴露）作为前提。 |
| **时间快照对比 / 图漫步模式** | 产品审查员 Proposal 3、4 — 各需 3+ 天。大型新前端组件需独立轮次。 |
| **多级撤销栈** | 数据模型存在，但完整的 Ctrl+Z/Ctrl+Shift+Z 接入需要跨组件状态管理重构。 |
| **交互式 onboarding / "Demo Resolve" 按钮** | 进化策略师 I3 — 巧妙低成本（约 50 LOC），但优先级低于修复实际 Resolve 可发现性问题（N1/N2）和完成退出动画（I1）。 |
| **每种记忆类型的衰减曲线（Bomb 4）** | 研究级。需要新 `decay_curve` 字段 + 5 种数学函数 + 自动建议逻辑。对修复轮次太具推测性。 |
| **扩散激活引擎（Bomb 5）** | 需要上下文模型 + 标签 IDF 计算 + 用于激活传播的 DAG 遍历。大型、重设计。 |
| **语义/嵌入搜索** | 需要新管道（向量数据库或 ONNX 本地嵌入）。数月，非数天。 |
| **CSS 设计 token 系统** | 覆盖 14 个组件的架构级重构。 |
| **图键盘导航** | Cytoscape 事件绑定 + focus 管理交互。 |

---

## 四、验收标准摘要

| 梯队 | 核心验证 |
|------|---------|
| **第一梯队（Critical）** | 对有非零 `days_since_last_access` 的记忆运行 `codememory overview`——热力值与旧公式不同（衰减激活）；`stability=0` 被拒绝（不崩溃）；`days_since_last_access=None` 在 overview/wander/validate 中表现一致；`/api/memories` 包含 `stability`、`days_since_last_access`；`/api/stats` 包含 `decay_risk` |
| **第二梯队（Important）** | 关闭 Wander 模态显示 fade-out + scale-down 动画；关闭 Validate 相同；关闭 Archive 确认相同；HelpPanel 滑出；无元素 `fontSize < 11px`（UI 中无小于 11px 的文本）；无交互元素 `fontSize < 12px` |
| **第三梯队（Nice to Have）** | Dashboard 显示衰减风险计数 + top 3 有风险记忆；图节点右键菜单包含"Resolve"；List 视图无重复过滤条 |
| **全局回归** | 86/86 测试通过（57 单元 + 24 集成 + 5 API）；TypeScript 零错误；Vite 构建成功；4 个数据集可 reindex |

---

## 五、不做什么

- 不建新功能（本轮的职责是修复和完工）
- 不添加新依赖（Playwright 延期至 R15）
- 不改架构、不碰 harnesslib、llm_gateway
- 不碰 CLI、MCP 服务端（除非 C1/C2 修复涉及共享 handlers.py 代码）
- 不做任何需要架构级设计的新概念（FSRS 自适应、扩散激活、每种类型的衰减曲线）

---

## 六、相关陷阱（来自本轮审计）

- **[R13-A1] 内联 Modal 函数无法复用 useExitAnimation hook。** Dashboard.tsx 中的 `Modal({ children, onClose })` 是本地纯函数组件——它无法接收表示"正在关闭"的 prop，因此无法在关闭时切换 CSS 类。当多个模态（Wander/Validate）共享同一个 Modal 组件时，模态的打开/关闭状态在父组件中管理，Modal 需要接收额外的 `closing` prop 或自身集成 `useExitAnimation`。

- **[R13-M3] days_since_last_access 的 None vs 0 语义区别。** `None` 表示"从未被访问"（应使用保守的 days=0 或忽略衰减），`0` 表示"刚刚访问过"。当前代码使用 `max(0, days_since or 0)` 处理 None——两者都产生相同结果。未来可能需要区分"从未访问"（高冷却）和"刚刚访问"（低冷却）。本轮（C2）应统一处理但不改变行为。

- **[R13-I1] /docs 中间件豁免创建新的绕过路径。** 数据集头部中间件现在豁免 `/docs` 和 `/openapi.json` 从 `X-Codememory-Dataset` 要求。任何未来不需要数据集的端点必须显式添加到豁免列表——一个手动维护点。

- **[R13-M1 新] 修复 C1 将改变 overview 热力值。** 对于任何有 `days_since_last_access > 0` 的记忆，修复管道 bug 将在 overview 中产生不同的热力值。这是正确行为——旧值完全是错误的。（对于 `days_since_last_access=0` 或 `None` 的记忆，行为不变。）

---

## 七、对 Generator 的说明

1. **C1 是本轮最高优先级的单一任务。** 其余均为次要。先修复 C1，验证，再继续。
2. 研究员为 C1 提供了精确代码位置：`handlers.py` 第 258 行和 `search.py` 第 73-85 行。详见研究审计报告 Phase 3.1 的根本原因分析。
3. C2 的 stability `gt=0` 验证器应使用合理的下限（建议 0.1 天 = 2.4 小时）——不允许零或负稳定性。
4. 本轮不授权新依赖。Playwright 延期至 R15。
5. 进化策略师明确建议"先关缺口再深挖功能"——不要让范围蔓延导致本打算作为修复轮次的回合变成大型新功能构建。修复、完工、防护。这是指令。
