# Negotiation -- Iteration 12

**Date:** 2026-05-07

## 对本轮 Reviewer 报告的逐条回应

---

### 体验官建议

#### 建议 1（体验官 Critical #1）: 修复 Validate 模态在 Wander 关闭后偶发性打不开的异步竞态
- **决策**：接受
- **理由**：这是 R11-B2 修复引入的新 bug——`setWanderOpen(false)` + `fetchValidate()` 同步调用但 `setValidateOpen(true)` 依赖 promise 解析，导致竞态。体验官在 headless page-state extraction 中复现了此问题。这是核心交互（Dashboard 两个主操作按钮）的阻断性缺陷。
- **本轮行动**：R12-B1

#### 建议 2（体验官 Critical #2）: 修复 List 视图 TruncatedCell tooltip 不显示（R11 回归）
- **决策**：接受
- **理由**：R11-UX6 在理想条件下通过了验收，但父元素 `<td>` 的 `overflow: hidden` 使 `scrollWidth > clientWidth` DOM 检测永远为 false——tooltip 在所有场景下均不显示。中文摘要被截断后用户无法查看完整内容。这是 R11 的回归 bug。
- **本轮行动**：R12-B2

#### 建议 3（体验官 Important #3）: 提升全局最小交互字号从 10-11px 到 12-13px
- **决策**：接受
- **理由**：体验官将此标记为"the single highest-impact aesthetic change available"。10px 文字在 4K 显示器上约 2mm 高——低于可读阈值。全应用约 15+ 处使用 10-11px 字号。这是一个 CSS 变更，影响面广但每处改动简单。深色模式同样受益。
- **本轮行动**：R12-UX1

#### 建议 4（体验官 Important #4）: 为 Settings、Help、MemoryForm 面板添加滑入动画
- **决策**：接受
- **理由**：MemoryDetail 已有 250ms ease slide-in 动画——这证明了技术可行性。Settings、Help、MemoryForm 三个面板同为右侧滑出组件但缺少动画是"一个疏忽"。体验官明确指出："Motion is how digital products communicate materiality." 对于定位 premium 的产品，动画缺失直接削弱感知质量。
- **本轮行动**：R12-UX2（与建议 5 合并实施）

#### 建议 5（体验官 Important #5）: 为 Wander 和 Validate 模态添加入场动画
- **决策**：接受
- **理由**：模态"出现"而非"到达"——150ms fade-in + scale(0.98->1) 是约 5 行 CSS 的改动。与建议 4 合并为 R12-UX2，统一处理所有面板和模态的入场/退场动画。
- **本轮行动**：R12-UX2（与建议 4 合并实施）

#### 建议 6（体验官 Important #6）: 为 Validate 模态添加 "Validate Again" 按钮
- **决策**：接受
- **理由**：Wander 有 "Wander Again"，Validate 没有——这是明显的交互不对称。添加一个 re-run 按钮约 10 分钟改动，但消除了"怎么重新验证？关了再打开？"的困惑。
- **本轮行动**：R12-UX3

#### 建议 7（体验官 Important #7）: 清除用户修正输入后的表单校验错误
- **决策**：接受并升级为 Critical
- **理由**：错误 banner 在用户修正输入后 persist——这是混淆性 UX bug。用户看到错误消息 + 启用的按钮同时存在，不知道该相信自己还是相信系统。这是表单可用性的基本预期，应排在 Tier 1。
- **本轮行动**：R12-B3

#### 建议 8（体验官 Nice-to-have #8）: 替换 onboarding 文字图标为 SVG 图标
- **决策**：接受
- **理由**：Onboarding 是产品的第一印象。"+"、"o"、">"、"~" 等原始字符在 Cormorant Garamond 字体中看起来不协调（serif 字体 + 抽象符号 = 视觉矛盾）。替换为简单 SVG 几何图形是低投入、高感知价值的改进。
- **本轮行动**：R12-P1

#### 建议 9（体验官 Nice-to-have #9）: 统一空状态组件 + 统一操作标签
- **决策**：接受
- **理由**：三个视图的空状态使用不同组件，操作标签在四个位置各不相同（"Create Memory" / "+ New" / "+ NEW" / "Create"）。这是基本一致性缺陷。拆分两个任务：R12-P2 统一空状态组件，R12-P3 统一操作标签。
- **本轮行动**：R12-P2 + R12-P3

#### 建议 10（体验官 Nice-to-have #10）: 移除 List 视图的本地过滤条
- **决策**：接受概念，延后
- **理由**：List 视图的本地过滤条与全局 SearchBar 功能重叠，确实造成"两个搜索"的困惑。但移除它需要同时添加"Show all N results in List view"功能到全局搜索下拉——这是搜索功能的重构，并非简单的删除。且全局搜索需要支持"无 query 的纯过滤"（已在 R10-search-filter-fix 中实现）。纳入下轮 backlog。
- **本轮行动**：N/A

#### 建议 11（体验官 Nice-to-have #11）: 为图节点右键菜单添加 "Resolve" 选项
- **决策**：接受概念，延后
- **理由**：减少 "aha moment" 点击路径从 4 步到 3 步（右击 → Resolve 而非 点击 → 面板 → Resolve 按钮）。但 "默认 resolve on node click" 是更深的结构性改动（影响所有用户的交互模式），不应作为右键菜单的一个选项单独处理。建议在更大的"aha moment 优化"轮次中统一考虑。
- **本轮行动**：N/A

#### 建议 12（体验官 Nice-to-have #12）: 添加视图切换键盘快捷键（1/2/3）
- **决策**：接受
- **理由**：2 个现有快捷键（Escape, Ctrl+K）对于一个专业工具远远不够。1/2/3 是自然的视图切换映射，在输入框聚焦时豁免即可避免冲突。Help 面板已有快捷键部分——只需添加条目。约 30 分钟改动。
- **本轮行动**：R12-P4

#### 建议 13（体验官 Nice-to-have #13）: 为 List 视图表格行添加 hover 效果
- **决策**：接受
- **理由**：Dashboard tag cloud 和 search results 已有 hover 效果——List 表格行没有，体验不一致。添加 `tr:hover` background-color 过渡是约 5 行 CSS。
- **本轮行动**：R12-P5

#### 建议 14（体验官 Nice-to-have #14）: Markdown 预览在 MemoryForm body textarea 中
- **决策**：接受概念，延后
- **理由**：编辑-保存-查看的循环确实低效。但 split-pane 或 toggle 预览需要中等规模的 UI 变更——不是本轮 polish 级任务。纳入 backlog。
- **本轮行动**：N/A

#### 建议 15（体验官 Feature Idea）: DAG-Aware Editing
- **决策**：接受，纳入长期 backlog
- **理由**：这是体验官 Phase 3 #1 的"if only"功能——在编辑表单中展示"4 memories depend on this"是 CodeMemory 独特能力的自然延伸。但需要新的 UI 组件和后端数据查询，属中型功能。
- **本轮行动**：N/A

#### 建议 16（体验官 Feature Idea）: Memory Reminders（定时复查提醒）
- **决策**：接受，纳入长期 backlog
- **理由**：体验官 Phase 3 #2 的建议——解决知识管理工具的 retention 问题。需要 memory model 扩展（`review_cadence` 字段）、Dashboard 新区域、可能的浏览器通知。属大型功能。
- **本轮行动**：N/A

#### 建议 17（体验官 Feature Idea）: Graph Diff（版本间 DAG 变化可视化）
- **决策**：接受，纳入长期 backlog
- **理由**：体验官 Phase 3 #3 的建议——"版本历史 + 可视化 = 时间机器"。这是 CodeMemory 独有的能力（竞品无 DAG 基础），但实现复杂度高（需要版本间图拓扑比较、diff 可视化）。
- **本轮行动**：N/A

#### 建议 18-22（体验官 Feature Ideas #18-#22）: Default Resolve on click、Resolve from search、review_cadence field、SVG icon set、color warm-ification
- **决策**：接受，全部纳入长期 backlog
- **理由**：这些都是有价值的长期方向。其中 SVG 图标集（#21）和颜色暖化（#22）可在后续 polish 轮次中分批实现。
- **本轮行动**：N/A

#### 体验官 Phase 2.3 隐含建议: List 视图横向 padding
- **决策**：接受
- **理由**：List 表格 edge-to-edge 与 Dashboard 32px padding 形成视觉不一致。简单的容器 padding 变更，约 5 行 CSS。
- **本轮行动**：R12-P6

---

### 进化策略师建议

#### 建议 C1（进化策略师 Critical #1）: AI 辅助记忆工作流
- **决策**：接受，纳入 backlog（Sprint 14-15）
- **理由**：这是进化策略师认定的"single most impactful action this sprint"——利用 `llm_gateway/` 在创建表单中集成 LLM：自动生成摘要、建议 imports、"rephrase" 按钮。这确实是 2026 年知识工具的基本预期，且 CodeMemory 的 DAG 结构能让 AI 建议更精准。但这是一个中型偏大功能（需要 llm_gateway 集成 + 前端 UI + 后端端点），自行消化一整轮。本轮聚焦于缺陷修复和低投入改进，AI 创建应在专门的轮次中实现。
- **本轮行动**：N/A

#### 建议 C2（进化策略师 Critical #2）: 数据导入 UI
- **决策**：接受，纳入 backlog（Sprint 14）
- **理由**：#1 冷启动障碍——没有人会通过表单手动创建 100+ 条记忆。但这是一个大型功能：文件上传、拖放区域、文本粘贴解析、批量导入 API、进度反馈。需要独立轮次。
- **本轮行动**：N/A

#### 建议 C3（进化策略师 Critical #3）: 设置面板扩展（从 3 项到 15-20 项）
- **决策**：部分接受——纳入 backlog，但降低优先级
- **理由**：当前 3 项设置确显单薄。但 15-20 项的扩展意味着需要定义 12-17 个新设置项、对应的 UI 控件、存储和恢复逻辑——这是中等偏大的功能。相比之下，用户体验更紧迫的问题是现有的 3 项设置能正常工作（它们能），而模态竞态和 tooltip 回归是每天折磨用户的 bug。设置面板扩展应在核心交互稳定后实施。
- **本轮行动**：N/A

#### 建议 C4（进化策略师 Critical #4）: 交互式 Onboarding
- **决策**：接受概念，延后
- **理由**：当前 5 步被动教程比完全无 onboarding 好得多（R4-onboarding 添加的）。升级为交互式教程（等待用户实际操作）是优秀的长期方向，但属中等规模改动（需要跨多个组件的引导状态管理 + 操作检测逻辑）。在本轮有 2 个 Critical bug 的前提下不应并行。
- **本轮行动**：N/A

#### 建议 C5（进化策略师 Critical #5）: 确认对话框 + 破坏性操作安全
- **决策**：接受
- **理由**：这是进化策略师 Critical 中唯一的"Low" effort 项——归档确认对话框 + 被引用警告。防止数据丢失是产品的基本安全预期。MemoryDetail 已有 backlinks 数据可用。约 30 分钟改动。
- **本轮行动**：R12-UX4

#### 建议 I1（进化策略师 Important #1）: Suggest-Deps 在创建/编辑表单中
- **决策**：接受，纳入 backlog
- **理由**：`suggest-deps` CLI 已存在，暴露到 UI 是低投入（Low-Medium）高价值改进——用户体验官也同意导入手动连线是最大摩擦点。但本轮 Tier 2 已满（5 项任务），下轮优先采纳。
- **本轮行动**：N/A

#### 建议 I2（进化策略师 Important #2）: 命令面板（Ctrl+P）
- **决策**：接受，纳入 backlog
- **理由**：桥接 CLI/UI 的创新功能，对 power user 极有价值。但需要新 UI 组件 + 命令解析 + 所有 API 端点的命令映射。中等投入。下轮评估。
- **本轮行动**：N/A

#### 建议 I3（进化策略师 Important #3）: 键盘快捷键系统
- **决策**：部分接受
- **理由**：完整的快捷键系统（Ctrl+N/Ctrl+Shift+N/Ctrl+R/Ctrl+1-3/Ctrl+,/Ctrl+/）需要在整个应用中注册和处理快捷键——中等范围。本轮采纳其中最低投入且与体验官建议重叠的部分：视图切换快捷键 1/2/3（已在 R12-P4 中）。完整的快捷键系统延后到专门轮次。
- **本轮行动**：R12-P4（部分实现——视图切换快捷键）

#### 建议 I4（进化策略师 Important #4）: 记忆内容模板（非仅 Schema）
- **决策**：接受概念，纳入 backlog
- **理由**：R5-template-create 已有 schema 选择器。扩展为内容模板（Meeting Notes、Project Decision 等含预填 body 的模板）是自然的下一步，但属中等功能（需要模板定义、存储、选择 UI）。下轮评估。
- **本轮行动**：N/A

#### 建议 I5（进化策略师 Important #5）: 草稿自动保存
- **决策**：接受，纳入 backlog
- **理由**：localStorage 持久化 + `beforeunload` 警告。R5-unsaved-changes-warning 已防止意外关闭丢失数据——草稿自动保存是合乎逻辑的下一步。但本轮表单已有 R12-B3（错误清除）变更，避免冲突。下轮采纳。
- **本轮行动**：N/A

#### 建议 I6（进化策略师 Important #6）: 图结构过滤器
- **决策**：接受，纳入 backlog
- **理由**：按 type/status/maturity/directory 过滤图节点——使图可探索而不只是可观看。quant_operators（62 节点）的导航压力证实了此需求。但需要新的 UI 控件 + Cytoscape 过滤逻辑，中等规模。
- **本轮行动**：N/A

#### 建议 I7（进化策略师 Important #7）: 批量操作
- **决策**：接受，纳入 backlog
- **理由**：Shift+Click multi-select + 批量 tag/archive/maturity change + 批量 PATCH API。对于管理 50+ 记忆的用户至关重要。但属中大型功能，需独立轮次。
- **本轮行动**：N/A

#### 建议 I8（进化策略师 Important #8）: 标准化面板组件（提取共享 SlideoutPanel）
- **决策**：接受概念，本轮部分采纳
- **理由**：MemoryDetail/Settings/Help/MemoryForm/Onboarding 5 个面板各有不同的实现方式——déjà vu 实现和细微的行为差异。提取共享组件是正确方向。在本轮中，R12-UX2 将为所有面板添加统一动画——这是走向标准化的第一步。完整的组件提取延后。
- **本轮行动**：R12-UX2（部分实现——统一动画是标准化的第一步）

#### 建议 I9（进化策略师 Important #9）: MCP Server readOnlyHint 注解
- **决策**：接受（与 R11-P4 和研究员 R4 重叠）
- **理由**：这是三个 Reviewer 唯一一致认定的未完成项。进化策略师标记为 Important + Low effort，研究员标记为 Red / High-Impact Low-Effort，体验官虽未直接提及但 eval.md 明确标为 FAIL。三方一致——最高优先级。
- **本轮行动**：R12-B4

#### 建议 I10（进化策略师 Important #10）: 图 Minimap
- **决策**：接受，纳入 backlog
- **理由**：Cytoscape 原生支持 minimap——添加成本低。对 quant_operators（62 节点）的导航压力有实际缓解作用。但本轮有更紧迫的 UX bug，下轮采纳。
- **本轮行动**：N/A

#### 建议 N1-N10（进化策略师 Nice-to-have）: Markdown 预览、高级搜索语法、图分析、记忆 diff、导出增强、保存视图、响应式布局、服务端分页、搜索历史、Wander 历史
- **决策**：接受，全部纳入 backlog
- **理由**：这些是值得做的长期功能。其中响应式布局（N7）和高级搜索语法（N2）具有较高的战略价值，建议后续轮次优先考虑。
- **本轮行动**：N/A

#### 建议 F1-F7（进化策略师 Feature Ideas）: AI Co-Pilot、记忆 diff 时间线、交互式 thesis 发布、环境记忆发现、Agent-to-Agent 记忆基础设施、语音笔记到记忆图、Obsidian 兼容桥
- **决策**：接受概念，全部纳入长期研究 backlog
- **理由**：这些是高区分度的创新方向。其中 AI Co-Pilot（F1）和 Agent-to-Agent 基础设施（F5）与 CodeMemory 的 DAG 差异化定位高度契合，值得在核心完整性达标后优先投入。Obsidian 兼容桥（F7）在技术上可行（两者共享 .md + YAML 基础），有明确的用户获取价值。
- **本轮行动**：N/A

---

### 研究员建议

#### 建议 R1（研究员 Red / High-Impact Low-Effort）: 时间衰减激活替代静态 heat
- **决策**：接受
- **理由**：约 20 行的 `handle_overview` 公式变更——利用已有的 `access_count` 和 `last_access` 数据，无新依赖。将 session-start 上下文注入从"访问最多的记忆"改为"最近最相关的记忆"能显著改善 Agent 体验。这是研究员报告中与体验官 Immediate 优先级交集最大的项。
- **本轮行动**：R12-UX5

#### 建议 R2（研究员 Red / High-Impact Low-Effort）: imports 添加可选 `semantic` 字段
- **决策**：接受概念，纳入 backlog
- **理由**：支持/反驳/扩展/替换/例证——给依赖关系添加语义维度是 powerful 的想法，与进化策略师的 DAG 深化方向一致。约 50 行改动（models.py + resolve.py + handlers.py），改动面集中在后端。但本轮 Tier 2 已满，且涉及 Pydantic 模型变更（需谨慎测试）。下轮优先采纳。
- **本轮行动**：N/A

#### 建议 R3（研究员 Red / High-Impact Low-Effort）: 预计算 in_degree / out_degree
- **决策**：接受概念，纳入 backlog
- **理由**：在 reindex 时计算并存储度数字段，消除搜索/overview/validate 中的 O(n^2) 扫描。代码改动小（约 30 行），但在 10-62 条记忆的当前规模下性能增益不可感知。应在数据规模增长前（预计 200+ 记忆时）实施。下轮评估。
- **本轮行动**：N/A

#### 建议 R4（研究员 Red / High-Impact Low-Effort）: MCP 工具注解
- **决策**：接受（与 R11-P4 和进化策略师 I9 重叠）
- **理由**：三方一致认定——最高优先级。已在 R12-B4 中。
- **本轮行动**：R12-B4

#### 建议 Y1-Y3（研究员 Yellow / High-Impact High-Effort）: 边优先记忆模型、内容寻址记忆身份、层级化记忆 tier
- **决策**：接受概念，纳入长期研究
- **理由**：这些都是架构级的方向——Y1（边优先模型）和 Y2（Merkle DAG）打破了"一切皆是 Markdown 文件"的纯粹性，需要设计文档和充分讨论。Y3（tier 分类）与进化策略师的"环境记忆发现"方向有共鸣。但这些不应在产品迭代轮次中实现——它们在 Research 轨道上。
- **本轮行动**：N/A

#### 建议 G1-G4（研究员 Green / Thought-Provoking）: 信念修正框架、记忆网络分析、多 Agent 冲突解决、链接健康仪表盘
- **决策**：接受概念，纳入长期研究
- **理由**：G4（链接健康仪表盘——统一展示死链/stale/衰减/孤儿）是其中最接近产品的方向，可与进化策略师的"图分析仪表盘"（N3）结合考虑。G1-G3 需要 Y1/Y2 作为前提，应在基础设施到位后评估。
- **本轮行动**：N/A

#### 建议 B1-B3（研究员 Blue / Wild Ideas）: 记忆编译器、记忆光谱学、记忆作为叙事
- **决策**：接受概念，纳入研究 reference
- **理由**：B1（预计算上下文包——"编译时" DAG 解析）在概念上与进化策略师的"索引缓存"方向互补，值得做一次技术 spike。B2（认知功能分析）和 B3（叙事检索）是 provocative 的想法，为产品长期愿景提供养分，但离当前产品阶段较远。
- **本轮行动**：N/A

---

## 本轮 Planner 自主发现的改进方向（不在 Reviewer 报告中的）

### 1. 归档确认需后端 dependency count 数据
R12-UX4（归档确认对话框）需要知道"被归档记忆被多少其他记忆 imports"才能显示警告。MemoryDetail 的 backlinks 数据已在前端可用，但归档操作发生在不同位置（右键菜单、表单 Archive 按钮）。Planner 提醒：Generator 需要确保归档确认对话框能获取到被引用数据——无论是复用已有 backlinks API 还是在确认触发时拉取。

### 2. R12-UX1（字号提升）与现有布局的交互
10-11px → 12-13px 是约 20% 的字号提升。在 view switcher 按钮行（4px gap）、header 区域、badge 标签等紧凑元素中，这可能导致文字溢出或换行。Generator 实施后应进行以下场景的视觉检查：4 个视图切换按钮并排、header 搜索栏 + dataset 下拉 + 视图切换的并排布局、Dashboard stat card label + 数字的组合。

### 3. R12-UX2（面板动画）的退场处理
React 的 conditional rendering 模式使退场动画难以实现——状态变为 false 后组件立即从 DOM 移除，animation 无法播放。Generator 需要决定技术策略：是延迟卸载（在动画完成后才移除组件）、使用 CSS animation + `animationend` 事件、还是采用退出动画的替代方案。这是一个已知的前端挑战，不是新问题——MemoryDetail 面板已有 slide-in 动画，Generator 可参考其实现方式处理退场。

### 4. R12-UX5（时间衰减）的 zero-access 降级
研究员 R1 提案中的公式 `ln(1 + sum(1 / sqrt(days_since_access + 1)))` 对从未访问过的记忆（`last_access` 为空或 never）需要一个合理的降级值。建议：若从未访问过，将 `days_since_access` 设为一个较大的默认值（如 365 天），使该记忆获得一个低但非零的衰减值——它仍可因 `deps * 2` 的依赖项获得合理的 heat，但不会因除零错误而崩溃。

### 5. Onboarding 图标设计约束（R12-P1）
Planner 提醒：SVG 图标需与现有 LuxCart 设计系统协调——使用 gold accent 色（`#B8860B`）、2px stroke width（匹配 app 的 sharp 美学）、Raleway 的几何感。避免 rounded / playful 风格——CodeMemory 的视觉性格是"private library meets data lab"，图标应传达 precision 而非 playfulness。
