# Round 13 任务计划 — 产品品质打磨

**生成日期：** 2026-05-07
**上轮评估：** Round 12 — 15/15 PASS，零回归（86/86 测试通过），首次零 Critical 缺陷
**本轮主题：** 完成未竟的打磨 + 统一衰减模型 + 消除概念断层

---

## 一、本轮聚焦

Round 12 是产品历史上最成功的打磨轮次。本轮不做大型功能、不改架构、不加依赖。目标是**用最小代价消除 Reviewer 三份报告交集的断层——把"85% 完成"的事情推进到 100%，把三套并行的衰减模型统一为一套，让产品在审美一致性和概念自洽性上达到可展示的标准。**

本轮任务按两个原则筛选：
1. **修复成本低**（不超过 50 行变更，不牵涉架构改动）
2. **用户感知价值高**（直接影响第一印象、日常操作流、或概念一致性）

---

## 二、任务清单

### 第一梯队：审美完成（完成 R12 未竟的打磨）

| # | 任务 | 说明 | 成本 | 来源 |
|---|------|------|------|------|
| A1 | 退场动画接线 | 入场动画 CSS 已写完，但 `panel-slide-exit` / `modal-fade-out` / `backdrop-fade-out` 从未被组件引用——退场动画是死代码。创建一套复用机制让关闭动作触发退场动画后再卸载 DOM。 | 低 | 体验官 Important #1 |
| A2 | 修复残余 sub-12px 字号 | 三处：详情面板徽章（StatusBadge/MaturityBadge 缺少 fontSize 覆写）、搜索栏微标签（fuzzy matches 9px、match quality badge 9px）。 | 极低 | 体验官 Important #2 |
| A3 | 搜索下拉框动画 | 搜索下拉框出现时添加 fade-in 动画（150ms），与面板/模态动画语言一致。 | 极低 | 体验官 Nice-to-have #5 |

### 第二梯队：发现路径缩短（让"aha moment"触手可及）

| # | 任务 | 说明 | 成本 | 来源 |
|---|------|------|------|------|
| D1 | 搜索结果添加"Resolve"动作 | 全局搜索下拉框中每条结果旁添加"Resolve →"按钮。点击后关闭搜索、切换到 Graph 视图、自动触发 resolve。将 aha moment 从 4 次点击缩短为 2 次。 | 低 | 体验官 Important #3 |
| D2 | 视图切换按钮添加快捷键提示 | Graph/List/Dashboard 按钮标签旁显示小号 "1"/"2"/"3" 提示，让用户自然发现快捷键。 | 极低 | 体验官 Important #4 |
| D3 | Resolve 加载状态 | 点击 Resolve 后 UI 冻结 1-3 秒无反馈。在 resolve 结果区域添加加载骨架或旋转指示器。 | 低 | 进化策略师 Critical #C3 |

### 第三梯队：衰减模型统一（消除概念断层）

| # | 任务 | 说明 | 成本 | 来源 |
|---|------|------|------|------|
| M1 | 统一 overview/wander/validate 的衰减模型 | 当前三套并行逻辑：overview 用 `0.5^(days/14)`，wander 用原始 access_count，validate 用 30 天硬阈值。统一为同一套连续衰减公式。 | 低 | 研究员 High-Impact #1 |
| M2 | 排除循环参与者从 dependents 计数 | 当节点属于不可解析的循环时，其 dependents 计数被纳入 heat 公式，产出误导性热力评分。在计算 dependents 时跳过循环成员。 | 极低 | 研究员 High-Impact #2 |
| M3 | index 中预计算 days_since_last_access | 将 `datetime.fromisoformat` 从 overview O(n) 热循环中移除，改为在索引中存储整数天数差。 | 极低 | 研究员 High-Impact #3 |
| M4 | 添加 stability 字段（默认 14.0） | 在 MemoryEntry 上新增可选的 per-memory half-life 字段。初始值 14.0 保持向后兼容——行为不变。为未来 per-memory 衰减铺路。 | 极低 | 研究员 High-Impact #4 |

### 第四梯队：基础设施

| # | 任务 | 说明 | 成本 | 来源 |
|---|------|------|------|------|
| I1 | 启用 OpenAPI /docs 端点 | FastAPI 自动生成的交互式 API 文档当前未暴露。开启为开发者提供自文档化 API。零代码变更，纯配置打开。 | 极低 | 进化策略师 Critical #C2 |

---

## 三、明确延期或拒绝的项目

### 延期到下轮评估

| 项目 | 理由 |
|------|------|
| **全文正文搜索**（进化策略师 C1/C4） | 最大的功能缺口，但涉及搜索管道变更 + 前端双向接线。成本中等，非"低投入"范畴。留给搜索聚焦轮次。 |
| **多级撤销栈**（进化策略师 I1） | 涉及跨组件状态管理重构和 Ctrl+Z 全局快捷键注册。超出本轮单体任务上限。 |
| **交互式 onboarding demo**（进化策略师 I5） | 需内嵌可交互 Cytoscape 实例。成本中等。 |
| **版本 diff 查看器**（进化策略师 I2） | 需新建前端组件、diff 算法集成。成本中等。 |
| **图键盘导航**（进化策略师 I3） | 需 Cytoscape 事件绑定 + focus 管理。涉及面广。 |
| **Playwright 冒烟测试**（进化策略师 I6） | 需要新的 dev 依赖（Playwright ~200MB），首次配置成本不可忽略。 |
| **视图切换过渡**（体验官 Nice-to-have #6） | 低投入但可复用 A1 的动画模式——等退场动画机制稳定后再做。 |
| **图节点 hover 微动画**（体验官 Nice-to-have #7） | Canvas 动画模式与 DOM 动画不同，不能复用本轮建立的机制。 |
| **FSRS 完整稳定性更新**（研究员 High-Effort #6） | 需要 schema 迁移 + per-access 数学更新。依赖 M4 先落地。 |
| **记忆层级可视化**（研究员 High-Effort #7） | 前端 100+ 行 + 后端 30 行，依赖 FSRS 先落地。 |

### 拒绝本轮（需要架构变更或新依赖）

| 项目 | 理由 |
|------|------|
| **CSS 设计 token 系统**（进化策略师 I4） | 覆盖 14 个组件的架构级重构——不是打磨任务。 |
| **扩散激活引擎**（研究员 High-Effort #5） | 需要先明确上下文模型设计，非本轮可完成。 |
| **移除 List 本地过滤条**（体验官 Nice-to-have #8） | 需要全局搜索接口功能扩展，涉及搜索重构。 |
| **Markdown 预览**（体验官 Nice-to-have #9） | 需要新建 UI 组件，成本中等。 |

### 长期留在 Backlog（大型功能，架构变更，或需新依赖）

- 协作 resolve / WebSocket（全新基础设施）
- MCP 写入工具（新 MCP tool 设计 + 安全边界）
- VS Code 扩展（独立产品）
- 自动归档 + 精华蒸馏（依赖 LLM gateway）
- 周度记忆摘要（依赖 LLM gateway + 调度）
- 图原生存储后端（架构变更，Phase 3）
- 记忆编译器隐喻（定位/营销层，非代码任务）

---

## 四、验收标准摘要

| 梯队 | 核心验证 |
|------|---------|
| 第一梯队 | 关闭任意面板/模态可见退场动画（非立即消失）；详情面板徽章字号 >= 12px；搜索栏微标签 >= 11px；搜索下拉框有 150ms fade-in |
| 第二梯队 | 搜索结果条目旁有 "Resolve →" 按钮——点击后切换到 Graph 并自动 resolve；视图切换按钮旁有 1/2/3 提示；Resolve 运行期间有可见加载反馈 |
| 第三梯队 | overview、wander(cool)、validate 使用同一衰减公式；循环成员不被计入 dependents 计数；index.json 包含 precomputed days_since 字段；MemoryEntry 有 stability 字段（所有记忆默认 14.0） |
| 第四梯队 | `/docs` 返回交互式 Swagger 页面 |

---

## 五、不做什么

- 不改架构、不加新依赖
- 不碰 CLI、MCP 服务端、harnesslib、llm_gateway
- 不做前端测试框架搭建（本轮不带 Playwright）
- 不引入新的设计概念（FSRS 全套、扩散激活、层级等——仅铺字段不改变行为）
- 不做任何需要超过 50 行变更的单体任务

---

## 六、相关陷阱（从 pitfalls.md 筛选）

- **[R12-UX2] 入场 CSS 可复用，退场需 closing 状态 + onAnimationEnd 延迟卸载** —— A1 的核心技术挑战。React conditional rendering 模式不支持退出动画——组件在状态变为 false 时立即卸载。通用解决方案：维护一个 closing 状态 flags，在关闭时先设置 closing=true 应用退场 CSS class，animationend 事件触发后再真正卸载。一次实现，7 处应用。

- **[R12-UX5] handlers.py 中两处 datetime import** —— M1/M3 涉及 handlers.py 的变更时需注意：模块级 `from datetime import datetime, timezone` (line 15) 和函数作用域 `from datetime import datetime as _dt` (line 440)。批量替换相关代码时避免破坏函数作用域缩进。

- **M4（stability 字段）的向后兼容** —— 旧 index.json 中没有 stability 字段的记忆在 Pydantic 加载后应自动获取默认值 14.0。Pydantic v2 的 `Field(default=14.0)` 自然处理此场景。需验证 reindex 后旧记忆的 stability 字段正确写入 index.json。

- **D1（搜索 Resolve）的视图切换时机** —— Resolve 操作依赖 Cytoscape 图实例已挂载。如果从非 Graph 视图触发 resolve，需先完成视图切换并确保图实例可用后再调用 resolve。视图切换和 resolve 调用之间需要渲染间隙。

- **本轮不触发 stale** —— M3/M4 涉及 index 数据模型扩展，不影响 .md 文件 body hash，不会触发 stale 检测。但 reindex 应作为验收步骤运行。

---

*计划结束。详细回应见 docs/orch/negotiation.md。*
