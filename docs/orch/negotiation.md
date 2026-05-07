# Negotiation — Round 14

**Date:** 2026-05-07
**Context:** Three Reviewer reports (product-audit-report.md, evolution-audit-report.md, research-audit-report.md) assessed against Round 13 (10/11 FULL PASS + 1 PARTIAL PASS, 86/86 tests, one CRITICAL bug discovered by Researcher).

---

## 产品体验官建议（Product Audit 7.9/10）

### Critical

#### 建议 1（体验官 Critical #1）: Wire modal exit animations to Wander/Validate/Archive modals and HelpPanel
**产品体验官判定 Round 13 为 PARTIALLY IMPLEMENTED — 3/6 个 UI 关闭点缺少退场动画。**
- **决策：** 接受 — 纳入 I1
- **理由：** `useExitAnimation` hook 已创建并证明可用于 3 个面板（MemoryDetail、Settings、MemoryForm）。CSS 退场类（`modal-fade-exit`、`backdrop-fade-exit`）存在于 index.css，但目前为死代码——从未被任何组件引用。Wander、Validate 和 Archive 模态在关闭时瞬间消失，与面板平滑的退出动画形成鲜明对比。修复是机械性的：将 `useExitAnimation` 集成到 Dashboard 的 `Modal()` 函数和 App.tsx 的 Archive 确认中。约 25 行。这是当前构建中最明显的单一抛光缺陷。
- **已解决挑战：** 体验官将其标记为"本次构建中最明显的单一抛光缺陷——每次模态关闭都提醒用户产品未完工。"进化策略师将相同的项目标记为 C2（"本轮必须修复"）。Eval 将 R13-A1 记录为 PARTIAL PASS。三个来源全部交汇于此项。

#### 建议 2（体验官 Critical #2）: Fix 9px font stragglers in HelpPanel and MemoryDetail
**产品体验官判定 R13-A2（Sub-12px Font Fix）为 INCOMPLETE — 7 个元素仍在 12px 以下。**
- **决策：** 接受 — 纳入 I2
- **理由：** HelpPanel 键盘快捷键参考表（2 处）为 9px。MemoryDetail 的"无额外上下文"文本为 9px。体验官："9px 文本在正常观看距离下确实不可读——比药瓶标签上的小写文字还小。"此外，Search Resolve 按钮以 10px 发布——正是 R13 承诺修复的字号。修复是低级替换——每处 1 行变更，无布局风险。
- **已解决挑战：** R13-A2 在 EVAL 中被标记为 PASS（仅检查了 Badges 和 SearchBar 微标签），但体验官的逐像素代码审查发现了 7 个残留项。Eval 的验收标准不够严格——"无残留 10px 以下交互文字"错误地排除了 9px 非交互文本（HelpPanel、MemoryDetail 空状态）。

#### 建议 3（体验官 Critical #3）: Bump Search Resolve button from 10px to 12px
- **决策：** 接受 — 纳入 I2（与建议 2 合并）
- **理由：** Search Resolve 按钮——R13 的旗舰新功能——以 `fontSize: 10` 发布。体验官："与它所代表的 R13 论题：'抛光轮次消除 sub-12px 字号' 矛盾。5 分钟修复。"将 fontSize 提升至 12 并将 padding 提升至 `3px 12px`。

### Important

#### 建议 4（体验官 Yellow #4）: Expose decay data to frontend API
- **决策：** 接受 — 纳入 C3
- **理由：** R13 的衰减模型完全是服务器端——`/api/memories` 端点目前硬编码了一个 10 字段子集，排除了 `access_count`、`last_access`、`days_since_last_access` 和 `stability`。前端仪表盘无法显示衰减信息、访问最近性，也无法实现"记忆健康"面板。在响应形状中添加这些字段的成本极低（约 10 行后端 + 类型定义同步）。这是将来任何衰减可视化功能的必要前提。

#### 建议 5（体验官 Yellow #5）: Add "Resolve" to graph node context menu
- **决策：** 接受 — 纳入 N2
- **理由：** 图视图目前无 Resolve 流程路径。查看图中某个节点的用户必须切换到 List 视图或使用 Search 才能解析它。在右键菜单中添加"Resolve"选项可在上下文需求点连接图视图与 Resolve 流程。约 15 行前端。

#### 建议 6（体验官 Yellow #6）: Heat-map maturity distribution in Dashboard
- **决策：** 延期至 R15
- **理由：** 视觉成熟度分布（色标柱状图）将"记忆健康"概念变得具体。但本轮优先级低于衰减风险暴露（N1）——N1 建立在 R13 模型之上并实现了体验官的"让衰减可见"指令，成本更低。成熟度可视化需要新的图表组件；衰减风险计数仅复用现有统计卡片模式。

### Nice to Have

#### 建议 7（体验官 Green #7）: Search Resolve button tooltip
- **决策：** 接受 — 纳入 N4
- **理由：** Resolve 按钮小且用途不直观。"Resolve"一词在没有上下文的情况下含义不明。悬停提示解释"解析 DAG 上下文"可在不改变布局的情况下提高可发现性。约 30 分钟。

#### 建议 8（体验官 Green #8）: Remove List view local filter bar
- **决策：** 接受 — 纳入 N3
- **理由：** List 视图的本地过滤条 80% 与全局 SearchBar 功能重叠，但产生不同结果（客户端子串匹配 vs 服务器端模糊匹配）。这种重复让用户困惑并占用屏幕空间。约 1 小时移除。

#### 建议 9（体验官 Green #9）: Fix 11px sub-12px stragglers
- **决策：** 纳入 I2（与建议 2 合并为综合字体修复）
- **理由：** 搜索片段（当前 11px）和撤销 toast 详情（11px）略微低于最小交互文本的可读性。与 9px 修复一起批量完成。

#### 建议 10（体验官 Green #10）: Add tooltip to maturity badges
- **决策：** 延期至 R15
- **理由：** 有价值——成熟度是 CodeMemory 独有的概念，用户需要帮助理解语义。但本轮优先完成安全/正确性（C1-C2）和完成未竟任务（I1-I2）。N1-N3 已经构成雄心勃勃的"附加"层；添加另一个工具提示组件将使 Generator 超出容量。

### 产品策略建议

#### 建议 11（体验官 Decay Heat Dashboard）: Proposal 1 — 完整衰减可视化
- **决策：** 延期至 R15-R16
- **理由：** 体验官将其标记为"尚未构建的最高单一影响力产品功能——将 CodeMemory 从笔记应用转变为记忆管理系统。"完全同意这是一种差异化功能。但需要 2-3 天，且需要 C1（Bug 修复）和 C3（API 暴露）作为前提。R14 交付前提条件；R15 构建仪表盘。

#### 建议 12（体验官 Temporal Snapshot Comparison）: Proposal 3 — 版本历史与差异视图
- **决策：** 延期至 R16+
- **理由：** 后端已存储完整版本历史（change_log），但查看器需要新前端组件 + 差异算法集成。3-4 天。独立的编辑体验轮次候选。

#### 建议 13（体验官 Graph Stroll Mode）: Proposal 4 — 动画依赖链游览
- **决策：** 延期至 R16+
- **理由：** "在空间上与 Wander 的时间召回等价——让图视图对不知道自己要找什么的用户变得可探索。"引人入胜的概念。需要 3 天的大规模 D3/Cytoscape 动画工作。独立轮次候选。

---

## 进化策略师建议（Evolution Audit 7.8/10）

### Critical

#### 建议 C1（进化策略师 Critical #C1）: Add full-text body search
- **决策：** 延期 — 与所有竞品相比最大的功能缺口，需独立搜索轮次
- **理由：** 进化策略师将其标记为"与每款竞品相比最重大的功能缺口"。完全正确——搜索仅匹配 ID、摘要、标签和元数据。一个包含 500 字 body 并讨论"半导体供应链"的记忆不会在搜索"供应链"时出现。但"中等"投入的估计过于乐观——Body 搜索需要后端搜索管道变更、前端结果高亮、以及性能考量。本轮"修复 + 完工"不是构建搜索管道基础设施的正确时机。规划搜索聚焦轮次（建议 R16）作为 R15 的自然后续——那是衰减模型变得用户可见后的时机。

#### 建议 C2（进化策略师 Critical #C2）: Complete modal exit animations
- **决策：** 接受 — 纳入 I1
- **理由：** 与体验官 Critical #1 交汇。进化策略师："3/6 个 UI 退出点已失效。修复：将 Dashboard `Modal()` 重构为使用 `useExitAnimation` 模式。约 25 行。"

#### 建议 C3（进化策略师 Critical #C3）: Add Playwright smoke tests (5 tests)
- **决策：** 延期至 R15 — 承诺为 R15 首个任务
- **理由：** 进化策略师正确诊断了最高风险的技术债务项："15 个 TSX 组件零自动化测试覆盖。每次 UI 回归在手动检查前都是无法检测的。"5 个 Playwright 冒烟测试（应用加载、图渲染、节点点击、搜索、CRUD 循环）将以最小成本捕获约 80% 的回归。但 Playwright 是一个新开发依赖（约 200MB），首次配置——浏览器二进制管理、测试运行器集成、CI 接线——成本不可忽略。**策略承诺：** 如果 R14 在没有追加范围的条件下成功交付 C1-C2 + I1-I2（高概率），Playwright 是 R15 的第一个和最高优先级任务——在引入任何新代码之前建立回归安全网。

### Important

#### 建议 I1（进化策略师 Important #I1）: Add write-capable MCP tools (create_memory, update_memory)
- **决策：** 延期至 R15-R16
- **理由：** 闭合 agentic 闭环：Agent 读取上下文（resolve），推理，行动，并将学习结果写回。这是 Mem0 核心价值主张"自编辑记忆"的等价物——但具有显式导入而非概率提取。是 CodeMemory 可建的最强差异化功能。但作为"M"（中型 = ~150 LOC + 安全设计）任务，超出了修复轮次的范围。在衰减模型稳定且用户可见后（R14-R15），MCP 写入在 R16 变得迫切。

#### 建议 I2（进化策略师 Important #I2）: Per-memory stability UI
- **决策：** 延期至 R15 — 在 C1 衰减 Bug 修复 + C3 API 暴露后，成为 R15 的自然高优先级项目
- **理由：** `stability` 字段（R13-M4）存在但不可见。MemoryForm/MemoryDetail 中的滑块 + List 视图中的"Decay"列将使衰减模型变得用户可见和用户可控。小型投入（约 40 行前端）。在 R14 使衰减计算**正确**运行后，R15 使衰减参数**可控**是逻辑的下一步。

#### 建议 I3（进化策略师 Important #I3）: "Demo Resolve" button on Dashboard
- **决策：** 延期至 R15
- **理由：** 一键演示——切换至 3 节点演示数据集，自动 resolve 决策节点，播放动画，返回原始数据集。巧妙且有差异化（约 50 行 + 3 个 .md 文件）。优先级低于修复实际搜索 Resolve 可发现性（工具提示 N4 是更轻量的权宜之计）和完成退出动画（I1）。

#### 建议 I4（进化策略师 Important #I4）: Full-text body search — frontend wiring
- **决策：** 延期 — 随 C1（后端 body 搜索）一起
- **理由：** 在后端 body 搜索落地后，前端接线是独立的但被阻塞。逻辑上包含在搜索聚焦轮次中。

#### 建议 I5（进化策略师 Important #I5）: Dashboard "Cooling Memories" section
- **决策：** 部分接受 — 纳入 N1（衰减风险暴露）作为轻量级替代
- **理由：** 显示距离衰减阈值（R < 0.1）最近的 top 5 记忆。使用已计算的 `days_since_last_access` 和 `stability`。N1 将其缩减为最低限度——仅显示**数量**而非完整列表——以适应修复轮次的容量约束。在 R15 中扩展为完整列表。

#### 建议 I6（进化策略师 Important #I6）: Multi-level undo stack
- **决策：** 延期至 R16+
- **理由：** 上一轮（R13）以相同理由延期，该理由仍然成立：完整的 Ctrl+Z/Ctrl+Shift+Z 接入需要跨组件状态管理重构。数据模型存在；布线是机械性的但范围很广。独立轮次候选。

### Nice to Have / Feature Ideas

- **N1-N7**（多选、保存的过滤器、Git 集成指南、快速捕获 API、标签页检查、子图提取、快捷键速查表覆盖层）— 全部保留在长期 backlog。其中，Git 集成指南（N3）和快捷键速查表覆盖层（N7）成本低、战略价值高，建议 R15 评估。
- **F1-F6**（WebSocket 协作 resolve、记忆健康评分、DAG 感知编辑、定时重新参与提醒、VS Code 扩展、MCP 写入工具）— 全部保留在长期研究 backlog。这些是差异化战略资产，均需独立轮次。

### 产品策略回应

#### 进化策略师的"先关缺口再深挖功能"策略
- **决策：** 完全接受并采纳为本轮指令
- **理由：** 进化策略师："先关缺口再深挖功能。全文搜索 + 模态退出动画 + Playwright 冒烟测试应是 R14 的要求。衰减模型个性化（per-memory stability UI、冷却记忆仪表盘）是 R15 的自然议程。"Planner 同意这一策略方向。R14 交付 C1（衰减 Bug 修复，开辟缺口）、C2（稳定性防护，开辟缺口）、I1（模态动画，开辟缺口）、C3（API 暴露，使 R15 衰减功能化成为可能）。R15 才是"深挖"——使衰减变得用户可见和可控。

---

## 设计研究员建议（Research Audit 6.5/10，已发现 CRITICAL Bug）

### Critical（阻塞正确性的 Bug）

#### 建议 R-RED-1（研究员 CRITICAL）: Fix overview data plumbing bug
- **决策：** 接受 — 纳入 C1，最高优先级
- **理由：** `handle_overview()` 第 258 行从 search 结果字典中读取 `days_since_last_access`。`search()` 函数（search.py 第 73-85 行）从未在输出中包含此字段。统一衰减公式 `0.5^(days/stability)` 从未在 overview 路径中激活。所有被访问过的记忆回退到 R13 之前的 `access * 0.1` 常量乘数。Eval 热力值（31、31、21、21、20）通过是因为它们匹配的是**旧公式**，而非新公式。对比：`handle_wander()` 正确地从 `entry.days_since_last_access`（第 345 行）读取并按设计工作。**这是 Round 14 的单一最高优先级任务——其余均为次要。**

#### 建议 R-RED-2（研究员 High Priority）: Add stability validation (guard against zero and negative)
- **决策：** 接受 — 纳入 C2
- **理由：** `stability=0` 导致 `0.5^(days/0)` → `ZeroDivisionError`——崩溃。`stability<0` 产生 `decay>1.0`——无意义（记忆随时间的推移"增强"）。需要 Pydantic `@field_validator(gt=0)`。研究员建议在 MemoryEntry 上设置 `stability > 0` 并设置最小 0.1 天（2.4 小时）作为实用下限。

#### 建议 R-RED-3（研究员 High Priority）: Resolve `days_since_last_access=None` semantics
- **决策：** 接受 — 纳入 C2
- **理由：** `None` 表示"从未被访问"；`0` 表示"刚刚访问过"。两者当前在所有三个消费点（overview、wander、validate）中产生相同的衰减值（1.0 — 无衰减）。但语义不同：对于从未访问的记忆，wander 应有最大冷却权重（已存有 bug——被 C1 修复所掩盖），而 overview 应给予少量非零访问奖励。定义明确的合约并将所有三个消费点更新为一致处理。至少，使行为明确并记录，而非意外。本轮不改变行为——仅统一处理。

#### 建议 R-RED-4（研究员 High Priority）: Include stability and decay fields in search result dict and API
- **决策：** 接受 — 纳入 C3（与体验官 Yellow #4 合并）
- **理由：** 研究员的搜索字典修复与体验官的 API 暴露请求趋同于同一个变更：使衰减字段对消费者可用。在 search 输出中添加 `stability` 和 `days_since_last_access`。同时考虑添加 `schema` 和 `imports`（或至少导入数量）——消费者越来越需要这些字段。

### Medium Priority

#### 建议 R-YLW-1（研究员 Medium）: Domain-calibrated stability presets (Bomb 1)
- **决策：** 延期至 R15-R16
- **理由：** 研究员提供了充分证据表明不同领域需要不同的半衰期：投资事实 7-14 天，软件架构概念 30-60 天，量化操作员程序性公式 60-180 天。作为 create 期间基于标签/类型的稳定性建议实现是正确的方法（约 50 LOC）。但在衰减**计算正确**（C1）之前调整默认值会混淆原因与效果。在 R14 中使公式正确；在 R15 中改进默认值。

#### 建议 R-YLW-2（研究员 Medium）: Add recency factor to search ranking
- **决策：** 延期至 R15
- **理由：** 对搜索结果排序应用衰减乘数（最近访问的记忆排名更高）使搜索具有时间感知能力。约 15 LOC 在 search.py 中。C1 修复后自然扩展。

#### 建议 R-YLW-3（研究员 Medium）: Decay-aware maturity upgrade requirements
- **决策：** 延期至 R15
- **理由：** 防止通过旧的、未经审查的记忆实现"成熟度膨胀"。需要最近的访问才能进行 draft→verified 升级。约 10 LOC 在 resolve.py 中。合理，但不如 C1-C2 迫切。

#### 建议 R-YLW-4（研究员 Medium）: Apply decay formula to `--with-recall` path
- **决策：** 延期至 R15 — 但受益于 C1 修复（如果 with-recall 路径与 overview 共享 code path）
- **理由：** `handle_overview()` 第 292-307 行对 with-recall 排序使用原始 `access_count`。C1 修复可能解决此问题（取决于是否共享衰减计算路径）。如果未解决，这是 R15 中约 5 LOC 的变更。

#### 建议 R-YLW-5（研究员 Medium）: Unify intensity-decay interaction
- **决策：** 延期至 R15 — 设计决策需讨论
- **理由：** 目前只有 `validate._check_decay` 豁免 `intensity >= 8` 的记忆免于衰减警告。Overview 和 wander 无论 intensity 如何都应用衰减。研究员提出了正确的问题：高 intensity 记忆应该获得稳定性乘数（`effective_stability = stability * (intensity / 5)`）吗？还是 intensity 只影响警告决策，不影响衰减计算？这是一个设计决策，不应急于在修复轮次中处理。

### Exploratory / Inspiration Bombs

- **R-GRN-1**（FSRS 自适应稳定性）/ **R-GRN-2**（协同记忆图）/ **R-GRN-3**（per-memory-type 衰减曲线）— 全部保留在长期研究 backlog。这些是研究员最高影响力的远期构想。R-GRN-1 是 R-YLW-1（领域校准预设）后逻辑上的下一步。R-GRN-2 和 R-GRN-3 是差异化长期战略资产，目前无已知竞品产品拥有。
- **R-BOMB-1 至 R-BOMB-4**（上下文感知激活、遗忘即功能、DAG 稳定性继承、Duolingo HLR 风格训练稳定性）— 保留在启发式 backlog。这些代表了研究员最具想象力的构想。R-BOMB-2（"遗忘即功能"——作为主动 UX 功能展示处于风险中的记忆）是 Round 14-15 衰减工作直接催生的最具说服力的产品概念。

### 研究员评分 6.5/10 — Planner 注解

研究员的 6.5/10 是三位 Reviewer 中的最低分，但不应被解读为悲观——这是一个严格但公正的评估。评分扣分源于：(a) 发现的 CRITICAL bug（如果公式未被激活则无法给予功能性评分），(b) 未防护的边界情况（如果稳定性=0 会导致崩溃，则不能认为模型完备），(c) 该设计止步于"统一模型"而未达到"差异化模型"（14.0 天稳定性均匀 + 单一指数曲线未充分利用研究文献中的证据）。研究员报告的真正价值不在分数而在发现：overview bug 是隐藏良好的，三位 Reviewer 中就他一人通过代码审查而非功能测试发现了它。没有这份审计报告，R14 将在 decay 公式已损坏数轮的情况下继续——所有三种衰减计算路径均回归，但仅对其中两种路径。

---

## Planner 自主关注的物品

### 1. C1（Bug 修复）是本轮压倒性的最高优先级
这不仅仅是另一个任务——它是 Round 13 全部衰减模型工作一直处于待机状态的原因。Planner 因此将 C1 标记为 Critical 而非 Important。在 C1 被修复和验证之前，本轮没有其他任务重要。所有 eval 的"PASS"标记均无效（它们验证的是旧公式）。修复是约 3 行但需要额外约 10 行的搜索输出字典扩展以永久闭合该缺口。还需要一个新的测试：验证当 `days_since_last_access` 变化时 overview 热力值变化。

### 2. 交接文件中的"退场动画接线 — 约 25 行"估计
这个估计适用于 I1 模态端。对于面板端，`useExitAnimation` 已经在 3 个组件中集成并工作正常。HelpPanel 需要相同处理。总 I1 工作量：将 `useExitAnimation` 集成到 Dashboard Modal 函数（~15 行）、Archive 确认模态（~5 行）、HelpPanel（~5 行）。

### 3. 搜索 Resolve 按钮字体（I2 的一部分）是本轮的一个哲学试金石
体验官："一个标志性 R13 功能以已弃用的字号发布，破坏了该轮次的论题。这是个具有讽刺意味的事实，让所有修复工作显得避重就轻。"这是**为什么该按钮的字体仍然显示 10px** 的真正问题——它是在构建机器上生成的吗？是预先存在的样式吗？是复制粘贴的吗？Planner 不探究原因，仅记录：修复它。I2 确保了搜索结果中不会再有功能元素显示 10px。

### 4. Round 14 的规模：约 80-100 行总计，分布在 6-8 个任务中
这比 Round 13 的约 150 行小（且 11 个任务 vs 本轮 8-9 个）。这是有意为之：修复轮次不应在修复的同时引入新复杂性。所有变更都是替换或添加——没有架构变更。唯一的结构性思考是 C2（None 语义一致性），这更像是文档记录而非代码变更。

### 5. Playwright 承诺：延期至 R15，但有约束力
Planner 承认拖延测试是不好的模式——这是 Playwright 连续第三次因"配置成本不可忽略"而被延期（R12 延期、R13 延期、R14 再次延期）。**此延期附带约束性承诺：** Playwright 冒烟测试是 Round 15 的第一个和最高优先级任务——在任何新功能代码之前。如果在首次 R15 提交时未交付，应提升为 Critical blocker。

---

*Negotiation 结束。详细任务计划见 docs/orch/plan.md。*
