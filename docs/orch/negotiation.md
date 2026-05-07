# Negotiation — Round 13

**Date:** 2026-05-07
**Context:** Three Reviewer reports (product-audit-report.md, evolution-audit-report.md, research-audit-report.md) assessed against Round 12 (15/15 PASS, zero regression, first zero-Critical audit).

---

## 体验官建议

### Important

#### 建议 1（体验官 Important #1）: Wire exit animations
- **决策**：接受
- **理由**：入场动画 CSS 已在 R12-UX2 中写完并正常运作，但 `panel-slide-exit` / `modal-fade-out` / `backdrop-fade-out` 三种退场 CSS class 从未被任何组件引用——实质上是死代码。体验官在 Phase 2.2 的详细分析已证明：关闭面板时 DOM 立即消失，退场 CSS 无 DOM 可动画。接入退场动画让入场动画有了"另一只靴子落地"的完成感——从 85% 完成推进到 100%。创建一套复用机制（延迟卸载直到 `animationend`）是低成本的解决方案，一次实现覆盖全部 7 个面板/模态入口。
- **本轮行动**：A1

#### 建议 2（体验官 Important #2）: Fix remaining sub-12px font sizes
- **决策**：接受
- **理由**：R12-UX1 将最小交互字号提升到了 12px，但体验官在 Phase 2.1 的代码审查中发现了 4 处遗漏——详情面板的 StatusBadge/MaturityBadge 缺少 fontSize 覆写（11px）、搜索栏 fuzzy matches 标签（9px）、搜索栏 match quality badge（9px）。4 行变更即可完成，没有布局风险。详情面板是最常被阅读的视图，它的徽章字号不应比列表视图的更小。图节点标签（11px Cytoscape）被体验官明确标记为"可辩护的例外"——Canvas 渲染有不同于 DOM 的可读性特征。
- **本轮行动**：A2

#### 建议 3（体验官 Important #3）: Add "Resolve" action to search result items
- **决策**：接受
- **理由**：这是本轮单一最高价值的发现路径改进。搜索是最常用的界面，Resolve 是最强大的功能——当前它们之间无任何连接。在搜索结果旁加一个"Resolve →"按钮，将 aha moment 从 4 次点击压缩到 2 次搜索加一次点击。体验官预估约 30 行变更，属于低投入。唯一需要关注的是跨组件回调——SearchBar 需要触发 Graph 视图切换和 resolve 调用，但 SearchBar 已经存在于顶层 App 控制下，数据流是可行的。
- **本轮行动**：D1

#### 建议 4（体验官 Important #4）: Display keyboard shortcut hints on view switcher buttons
- **决策**：接受
- **理由**：快捷键 1/2/3 已在 R12-P4 中实现，但完全没有可见提示——用户只能在 Help 面板中发现它们。在视图切换按钮标签旁添加小号 "1" / "2" / "3" 提示，让快捷键被自然发现而非需要文档搜索。体验官预估约 15 分钟变更——极低的投入产出比。
- **本轮行动**：D2

---

### Nice-to-have

#### 建议 5（体验官 Nice-to-have #5）: Search dropdown expand/collapse animation
- **决策**：接受
- **理由**：搜索下拉框当前"闪现"而无过渡，与面板/模态的 250ms 动画语言不一致。150ms fade-in 是约 3 行 CSS 的变更，且搜索下拉框已经是条件渲染组件——技术模式已有先例。低投入，完成"全应用动画一致"的最后一块拼图。
- **本轮行动**：A3

#### 建议 6（体验官 Nice-to-have #6）: View-switch transition
- **决策**：延期
- **理由**：视图切换时添加 150ms crossfade 确实是低成本的（约 15 行 CSS），但本轮的任务密度已经足够高。且视图切换过渡与退场动画（A1）共享相同的技术模式——等退场动画的复用机制稳定后，视图过渡可以沿用同一套方案，避免重复设计。下轮评估。
- **本轮行动**：N/A

#### 建议 7（体验官 Nice-to-have #7）: Graph node hover micro-animation
- **决策**：延期
- **理由**：Cytoscape 原生支持 `transition-property`，实现成本低。但图动画与退场动画（A1）和搜索下拉动画（A3）在技术模式上不同（Canvas vs DOM），不能复用本轮建立的动画模式。且图节点 hover 反馈的实际用户感知价值低于退场动画和搜索下拉——用户关闭面板的频率远高于 hover 图节点。下轮评估。
- **本轮行动**：N/A

#### 建议 8（体验官 Nice-to-have #8）: Remove List view local filter bar, consolidate into global SearchBar
- **决策**：延期
- **理由**：这是 R12 negotiation 中已接受概念但延期的项目，本轮继续延期。理由不变：移除本地过滤条需要先在全局搜索下拉中添加"Show all N results in List view"功能——这是搜索功能的扩展，不是简单的删除。搜索功能扩展应在一个聚焦搜索的独立轮次中处理（届时可同步解决全文正文搜索的缺口）。
- **本轮行动**：N/A

#### 建议 9（体验官 Nice-to-have #9）: Markdown preview in MemoryForm body
- **决策**：延期
- **理由**：需要新建 UI 组件（Markdown 渲染面板 + Edit/Preview 切换器），成本中等。属于独立的编辑体验改进轮次的范围，不应在本轮打磨轮次中混入。
- **本轮行动**：N/A

---

### Feature Ideas（建议 10-14）

- **DAG-Aware Editing** (建议 10) / **Memory Reminders** (建议 11) / **Graph Diff** (建议 12) / **Settings Panel Expansion** (建议 13) / **Command Palette** (建议 14) — 全部纳入长期 backlog。这些是 R12 审计中已记录的方向，本轮无新增信息改变其优先级。

---

## 进化策略师建议

### Critical

#### 建议 C1（进化策略师 Critical #C1）: Full-text body search
- **决策**：延期——计划在搜索聚焦轮次中处理
- **理由**：进化策略师将其标记为"the single biggest functional gap vs every competitor"。这个判断完全正确——CodeMemory 的搜索只覆盖 ID/summary/tags/metadata 而不覆盖 body 文本，确实是与 Obsidian/Notion/Mem.ai 的最大功能差距。但"Medium"effort 的估计过于乐观——body 搜索需要后端搜索管道变更（搜索循环中加载 body 文本、匹配算法扩展、性能考虑）、前端结果展示变更（body 匹配片段的高亮显示）、以及 API 响应格式的扩展。这不是本轮"不超过 50 行变更"的任务类型。适合在一个搜索聚焦轮次中与建议 C4（前端 body 搜索接线）、建议 8（List 过滤条整合）一并处理。
- **本轮行动**：N/A

#### 建议 C2（进化策略师 Critical #C2）: Enable OpenAPI /docs endpoint
- **决策**：接受
- **理由**：FastAPI 内建 Swagger UI，启用仅需引入 `from fastapi.openapi.docs import get_swagger_ui_html` 并添加一个路由——或者更简单地在 FastAPI app 初始化时设置 `docs_url="/docs"`（默认值）。零代码变更，纯配置打开。对于目标开发者用户，自文档化 API 是第一印象的关键组成部分。
- **本轮行动**：I1

#### 建议 C3（进化策略师 Critical #C3）: Add Resolve loading state
- **决策**：接受
- **理由**：点击 Resolve 后 UI 完全冻结 1-3 秒没有任何反馈——体验官和进化策略师都指出这是"任何人第一次使用的抱怨点"。在 Resolve 面板区域添加骨架加载器或旋转指示器是基础 UX 规范。成本低——Resolve 结果区域已有条件渲染逻辑，只需在等待状态时渲染加载组件。
- **本轮行动**：D3

#### 建议 C4（进化策略师 Critical #C4）: Add body text to frontend search
- **决策**：延期——与 C1 合并处理
- **理由**：本质上是 C1 的前端侧对应物。后端 body 搜索先落地，前端接线才能生效。纳入搜索聚焦轮次。
- **本轮行动**：N/A

---

### Important

#### 建议 I1（进化策略师 Important #I1）: Multi-level undo stack
- **决策**：延期
- **理由**：单级撤销栈确实是落后的 UX，但升级为多级撤销需要跨组件状态管理重构——当前撤销状态存储在 App.tsx 顶层，undo entry 仅保存最近一次操作。升级为栈（至少 20 深）需要改变 undo entry 的数据结构、Ctrl+Z 的遍历逻辑、以及 Undo toast 的层级展示。这个变更超出本轮"不超过 50 行"的单体任务上限。下轮评估。
- **本轮行动**：N/A

#### 建议 I2（进化策略师 Important #I2）: Version diff viewer
- **决策**：延期
- **理由**：后端已存储完整版本历史（change_log + version 递增），这是进化策略师指出的"数据在，功能不在"的典型场景。但 diff 查看器需要新建前端组件、diff 算法选择、MemoryDetail 面板扩展——成本中等。应在专门的编辑体验轮次中与 Markdown 预览（体验官 Nice-to-have #9）一并处理。
- **本轮行动**：N/A

#### 建议 I3（进化策略师 Important #I3）: Graph keyboard navigation
- **决策**：延期
- **理由**：箭头键导航图节点 + Enter 打开详情 + Escape 取消——这是交互式图的预期行为。但实现涉及 Cytoscape 事件绑定、focus 管理、与现有图交互（拖拽、缩放、点击）的冲突处理。超出本轮低投入边界。下轮评估。
- **本轮行动**：N/A

#### 建议 I4（进化策略师 Important #I4）: CSS design token system
- **决策**：拒绝本轮——纳入中期架构 backlog
- **理由**：进化策略师正确诊断了"inline styles everywhere"带来的维护摩擦——30+ CSS 自定义属性散落在 main.tsx 中，改变字体需要搜索 14 个组件文件。但提取设计 token 系统是一个架构级变更：需要定义 token 命名约定、迁移 14 个组件中的 inline styles、设置 linting 规则防止回退。这不是打磨轮次的任务，而是需要独立轮次的技术债清偿。本轮不做，但记录为中期优先处理项。
- **本轮行动**：N/A

#### 建议 I5（进化策略师 Important #I5）: Interactive onboarding demo
- **决策**：延期
- **理由**：在 onboarding 中嵌入一个 3 节点预建 DAG 让用户点击和 resolve——这是"让用户在第一分钟体验 aha moment"的优秀想法。但需要内嵌小型可交互 Cytoscape 实例，这超出了文本替换的范畴。成本中等，涉及 Cytoscape 容器管理（onboarding 是一个叠加层而非主视图）。下轮评估。
- **本轮行动**：N/A

#### 建议 I6（进化策略师 Important #I6）: Playwright smoke tests
- **决策**：延期
- **理由**：前端测试零覆盖是一个被三方 Reviewer 持续指出的结构性缺口。5 个 Playwright 冒烟测试（app 加载、图渲染、节点点击、搜索、CRUD 循环）能以最小投入捕获约 80% 的回归。但 Playwright 是一个新的 dev 依赖（约 200MB 安装），首次配置——浏览器二进制管理、测试运行器集成、CI 接线——成本不可忽略。本轮优先完成可直接写入代码的功能改进，Playwright 在下轮作为独立基础设施任务处理。
- **本轮行动**：N/A

---

### Nice-to-have（建议 N1-N7）

- **N1**（Multi-select in List）/ **N2**（Saved filters）/ **N3**（Git integration guide + GitHub Action）/ **N4**（Quick-capture API）/ **N5**（Tabbed memory inspection）/ **N6**（Graph subgraph extraction）/ **N7**（Keyboard shortcut cheat sheet overlay） — 全部纳入长期 backlog。其中 N3（Git 集成指南）和 N7（快捷键速查表）成本低但战略价值高，建议下轮优先评估。

---

### Feature Ideas（建议 F1-F6）

- **F1**（Collaborative resolve via WebSocket）/ **F2**（Memory health score）/ **F3**（DAG-aware editing sidebar）/ **F4**（Scheduled re-engagement）/ **F5**（VS Code extension）/ **F6**（MCP write tools） — 全部纳入长期研究 backlog。这些是差异化战略资产，但都属于需要独立轮次的大型功能。

---

## 研究员建议

### High-Impact, Low-Effort

#### 建议 R-H1（研究员 High-Impact #1）: Unify decay models across overview, wander, and validate
- **决策**：接受
- **理由**：研究员 Phase 3.1 的诊断精确指出了概念断层——三套并行的衰减逻辑在一个系统中运行，且产生矛盾的行为。overview 用 `0.5^(days/14)`（连续指数衰减），wander(cool) 用原始 `access_count` 权重（完全忽略时间衰减），validate 的 `_check_decay()` 用硬编码 30 天阈值（二元判断）。统一的代价是约 20 LOC 的变更——将 wander 的冷却权重和 validate 的衰减检测都切换到 overview 已有的连续衰减公式。不引入新概念，只是消除内部不一致。
- **本轮行动**：M1

#### 建议 R-H2（研究员 High-Impact #2）: Exclude cycle participants from dependents count
- **决策**：接受
- **理由**：当节点属于不可解析的循环时，它仍然从循环成员获得 dependents 计数——这些计数乘 10 后贡献给 heat 公式。结果：不可解析的记忆因为"被循环引用"而排名高。这是结构上错误的 heat 评分。修复只需在 dependents 计数循环中跳过检测到的循环成员——约 15 LOC。
- **本轮行动**：M2

#### 建议 R-H3（研究员 High-Impact #3）: Precompute days_since_last_access in the index
- **决策**：接受
- **理由**：`datetime.fromisoformat` 在 overview O(n) 循环中的每个记忆上调用是当前最昂贵的单次操作。将 `days_since_last_access` 预计算为整数存储在 IndexData 中——在 reindex 时计算一次，在 access 时更新。约 10 LOC，纯性能优化，零行为变更。
- **本轮行动**：M3

#### 建议 R-H4（研究员 High-Impact #4）: Add stability field to MemoryEntry (default 14.0)
- **决策**：接受
- **理由**：当前 14 天 half-life 对所有记忆一视同仁——一个快速变化的代码库记忆和一个缓慢演变的原则记忆以相同速率衰减。添加一个 `stability: float = 14.0` 字段到 MemoryEntry，在 heat 公式中将 `0.5^(days / 14.0)` 改为 `0.5^(days / stability)`。初始值 14.0 对所有记忆保持向后兼容——行为不变。本轮仅添加字段并埋入公式，不实现 FSRS 动态更新逻辑（那是需要 schema 迁移 + per-access 数学的大型变更）。本轮仅铺路。
- **本轮行动**：M4

---

### High-Impact, High-Effort

#### 建议 R-HE5（研究员 High-Effort #5）: Implement spreading activation from tag context
- **决策**：延期
- **理由**：扩散激活是 ACT-R 模型中 CodeMemory 最大缺失的组件——一个关于风险容忍度的记忆在用户处理风险分析时应自动"热起来"。这是强大的概念，但实现前需要明确设计决策：上下文是由 --tags 参数提供（简单）还是从 active resolve session 推断（复杂）？上下文应该衰减吗？扩散范围应该限制在图中的几跳？这些设计问题应该在实现前回答。本轮不做，但列为中期研究优先项。
- **本轮行动**：N/A

#### 建议 R-HE6（研究员 High-Effort #6）: Build FSRS-style per-memory stability updates
- **决策**：延期
- **理由**：FSRS DSR 模型（Difficulty-Stability-Retrievability）是经过实证的个性化衰减方案，比全局 14 天 half-life 更科学。但实现需要：schema 迁移（两个新 float 字段 + 版本兼容逻辑）、per-access 更新函数（FSRS-4.5 公式）、以及两轮验证确保稳定性收敛而非发散。这是本轮 M4（添加 stability 字段）之后的下一个自然步骤，但需要独立轮次。
- **本轮行动**：N/A（M4 是铺路项）

#### 建议 R-HE7（研究员 High-Effort #7）: Memory tier visualization (Hot/Warm/Cold/Frozen)
- **决策**：延期
- **理由**：研究员建议将 FSRS 计算结果映射为 Leitner 风格的直观层级——Hot (R>0.7) / Warm (0.3<R<=0.7) / Cold (0.1<R<=0.3) / Frozen (R<=0.1)。这是"数学严谨 + 用户直观"的优秀折中。但需要 FSRS 先落地（建议 R-HE6），然后前端需要为每种层级设计视觉处理——成本约 100 行前端 + 30 行后端。依赖链：M4 → R-HE6 → R-HE7。
- **本轮行动**：N/A

---

### Thought-Provoking（建议 8-10）

- **R-T8**（Memory Compiler metaphor）/ **R-T9**（Episodic-to-semantic mining）/ **R-T10**（Demotion path for maturity） — 8 和 9 是定位/营销层的概念重组和需要新架构的 TransientDAG 持久化——都不在本轮代码变更范围内。10（降级路径）与 M2（排除循环参与者）共享成熟度治理的关切，但降级需要新的生命周期状态机——比 M2 复杂得多。全部纳入长期研究。

---

### Wild Ideas（建议 11-12）

- **R-W11**（Auto-archiving with essence distillation）/ **R-W12**（Weekly Memory Digest） — 两个都依赖 LLM gateway 集成（精华蒸馏需要 LLM 生成 3 行摘要，周度摘要需要 LLM 生成报告）。llm_gateway 是一个存在于代码库但尚未与 codememory 核心深度集成的组件——这些功能是"当 AI 管道就绪后"的自然延伸，而非本轮的可行任务。

---

## Planner 自主识别的关注点

### 1. 退场动画的复用机制设计
A1（退场动画接线）是本轮唯一需要"设计"的任务——它需要创建一个复用机制来延迟组件卸载直到动画完成。这不是一个新问题：React 社区对此有成熟的解决方案（closing state + onAnimationEnd handler + 条件渲染延迟）。关键是这个机制需要足够通用以覆盖两种动画模式——panel-slide-exit（translateX）和 modal-fade-out（opacity + scale）。一次设计，7 处应用。

### 2. M1（统一衰减模型）的 wander 冷却语义
研究员指出 wander(cool) 当前使用 `1/(access_count+1)` 作为权重，完全忽略时间维度。用连续衰减公式替代后，wander 的语义从"最少访问的记忆"变为"最低检索概率的记忆"——这是一个更精确的"cool"定义。但需要确认：wander 有两种模式（cool / random），本次变更仅影响 cool 模式。

### 3. M4（stability 字段）的未来扩展路径
添加 stability 字段时需确保向后兼容——旧 index.json 中没有该字段的记忆在加载后应获取默认值 14.0。这是 Pydantic 的 `Field(default=14.0)` 自然处理的场景。同时，heat 公式中的 `days / 14.0` 硬编码需要替换为 `days / stability`——这个变更应在一处（handle_overview）完成，而非在多处复制。

### 4. D1（搜索 Resolve）的视图切换时机
D1 要求搜索结果中的"Resolve →"按钮触发三件事：关闭搜索下拉、切换到 Graph 视图、自动 resolve。关键约束：切换到 Graph 视图后 Cytoscape 实例需要已渲染（因为 resolve 的依赖链动画依赖图实例）。如果视图切换和 resolve 调用之间没有渲染间隙，动画可能丢失。Generator 应确保 resolve 操作在 Graph 视图挂载后触发。

### 5. 本轮不应触发 stale 记忆数据的修复
本轮任务（M3/M4）涉及 index 数据模型的微小扩展——不影响 .md 文件中的 body hash，因此不会触发 stale 检测。但 reindex 操作应作为验收步骤之一运行，确保新增字段在 index.json 中正确序列化/反序列化。

---

*Negotiation 结束。详细任务计划见 docs/orch/plan.md。*
