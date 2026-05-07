# Sprint 13 — 管理面板

> **起始日期**：2026-04-29
> **前置条件**：Sprint 12 完成（交互式 Resolve + budget 滑块 + 拓扑动画）
> **目标**：在 UI 中完成记忆的增删改查 + 系统健康检查，打造完整管理工具

---

## 一、任务

### 任务 1：Backend 管理端点

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 1.1 | `POST /api/memories` | 创建新记忆（委托 `handle_create()`），返回创建后的记忆数据 | [x] |
| 1.2 | `PUT /api/memories/{id}` | 更新记忆（委托 `handle_update()`），支持修改 body/summary/tags/intensity/status | [x] |
| 1.3 | `GET /api/stats` | 返回统计数据：总数、maturity 分布（draft/verified/proven）、stale 数量、tag 频次 | [x] |
| 1.4 | `POST /api/wander` | 触发 wander，返回一条冷记忆（低访问次数 + 高 intensity 加权随机） | [x] |
| 1.5 | `POST /api/validate` | 运行 validate，返回诊断结果（循环/断链/schema 合规/maturity 建议） | [x] |

**产出**：5 个管理端点，通过 curl 可验证

---

### 任务 2：Dashboard 页面

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 2.1 | Dashboard 视图 | 统计卡片行（总记忆数、stale 数、proven 数）+ maturity 分布图 + tag 列表 | [x] |
| 2.2 | 视图切换 | 顶部导航切换 "Graph" / "Dashboard" 两个视图 | [x] |
| 2.3 | Stale 记忆高亮 | Dashboard 中高亮展示所有 stale 记忆，点击可跳转到详情 | [x] |
| 2.4 | Wander 按钮 | 点击随机召回一条冷记忆，弹窗展示其 summary + id | [x] |
| 2.5 | Validate 结果展示 | 运行 validate 后展示诊断结果列表（errors/warnings） | [x] |

**产出**：Dashboard 视图 + Graph 视图可切换

---

### 任务 3：记忆创建/编辑表单

| # | 子任务 | 说明 | 状态 |
|---|--------|------|------|
| 3.1 | 创建表单 | 滑出面板或弹窗中的表单：id、summary、tags、intensity、body（textarea） | [x] |
| 3.2 | 编辑表单 | 复用创建表单组件，预填现有数据，支持更新 body/summary/tags/intensity/status | [x] |
| 3.3 | 图节点右键菜单 | 右键节点 → "Edit" / "Delete" 选项，触发编辑表单或删除确认 | [x] |

**产出**：可通过 UI 创建和编辑记忆，图实时刷新

---

## 二、技术约束

- 所有 Backend 端点委托 `src/codememory/handlers.py`，不重复实现业务逻辑
- Dashboard 和 Graph 视图切换不销毁 cytoscape 实例（保持图状态）
- 创建/编辑表单使用 LuxCart 设计系统风格
- 表单验证：id 必填（创建时），intensity 范围 1-10
- 删除操作需要确认弹窗
- 不修改 `src/codememory/` 内部逻辑
- 不修改 `src/harnesslib/` 或 `src/llm_gateway/`

---

## 三、验收命令汇总

```bash
# Backend 统计端点
curl http://localhost:8000/api/stats | python -m json.tool

# Backend wander
curl -X POST http://localhost:8000/api/wander | python -m json.tool

# Backend validate
curl -X POST http://localhost:8000/api/validate | python -m json.tool

# Backend 创建 + 清理
curl -X POST http://localhost:8000/api/memories \
  -H "Content-Type: application/json" \
  -d '{"id":"user/test/sprint13-test","summary":"Sprint 13 test memory","tags":["test"],"intensity":5,"body":"Test body content."}'
curl http://localhost:8000/api/memories/user/test/sprint13-test | python -m json.tool
curl -X PUT http://localhost:8000/api/memories/user/test/sprint13-test \
  -H "Content-Type: application/json" \
  -d '{"change_note":"update summary","summary":"Updated test summary"}'
# Clean up: manually delete the test file + reindex

# Frontend TypeScript 类型检查
cd frontend && npx tsc --noEmit

# Frontend 构建
cd frontend && npx vite build

# 全量回归
PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short
PYTHONPATH=src python tests/integration_test.py
```

---

## 四、完成定义

1. 5 个管理端点全部可用（create/update/stats/wander/validate）
2. Dashboard 视图展示统计卡片 + maturity 分布 + stale 列表
3. Graph / Dashboard 视图可切换
4. 可通过 UI 创建新记忆，创建后图自动刷新
5. 可通过 UI 编辑现有记忆（右键 → Edit）
6. Wander 按钮可召回冷记忆
7. Validate 结果可展示
8. TypeScript 零错误，前端可构建
9. 57+24 测试不退化

---

## 第 1 轮追加任务（基于体验官审计 — 2026-04-30）

### 第一梯队（关键缺陷 — 阻止发布）

- [x] PL1-1: 修复 Dashboard Stale 记忆检测逻辑
  - 目标：Dashboard 的 stale 记忆列表能正确显示那些 body hash 与 summary_hash 不匹配的记忆
  - 验收：人为制造一条 stale 记忆后，Dashboard 的 stale 列表中出现该记忆（含 ID），而非永远显示空列表

- [x] PL1-2: 为 POST /api/memories 添加 ID 格式校验
  - 目标：API 拒绝不含 "/" 分隔符或为空的 memory ID，与前端表单校验一致
  - 验收：curl 发送 `{"id":"badid"}` 返回 422 + 可读错误信息；`{"id":"user/test/ok"}` 正常创建

- [x] PL1-3: 为 server.py 添加 `__main__` 入口块
  - 目标：用户按 Sprint 文档执行 `python backend/server.py` 即可启动后端，无需自行拼接 uvicorn 命令行
  - 验收：执行 `python backend/server.py` 后服务在 localhost:8000 可用

### 第二梯队（重要改进 — 必须随后完成）

- [x] PL1-4: 向 /api/stats 响应中添加 stale_ids 字段
  - 目标：用户不仅能看到 stale_count 聚合数字，还能知道具体哪些记忆是 stale 的
  - 验收：当存在 stale 记忆时，/api/stats 返回 `stale_ids: ["user/ideas/a", "user/facts/b"]` 且列表完整

- [x] PL1-5: 统一 Archive/Delete 术语
  - 目标：在所有 UI 位置（右键菜单、编辑表单、确认弹窗）统一使用 "Archive" 一词，明确其可逆含义
  - 验收：右键菜单中出现 "Archive" 选项（非 "Delete"）；按钮颜色不误导为不可逆操作；确认弹窗说明 archive 后仍可通过取消 archive 恢复

- [x] PL1-6: 实现跨视图数据刷新
  - 目标：在 Graph 视图中创建/编辑/归档记忆后，切换到 Dashboard 时自动显示最新数据
  - 验收：在 Graph 视图创建一条记忆 → 切换到 Dashboard → 总记忆数和 tag 分布已更新，无需手动刷新浏览器

- [x] PL1-7: 添加空状态引导
  - 目标：零记忆或零依赖时显示清晰的 Call-To-Action，引导用户迈出第一步
  - 验收：删除所有记忆后页面显示 "No memories yet. Create your first memory to get started." 及创建按钮；有记忆但无 imports 边时显示对应提示

- [x] PL1-8: Budget 滑块无效果时提供视觉反馈
  - 目标：当 budget 变化未改变 resolve 结果（所有节点均已包含）时，以非侵入方式告知用户
  - 验收：在 10 节点数据集上拖动 budget 滑块（200-5000），不再出现无意义的 "Resolving..." 动画，而是显示 "All N nodes fit within budget" 提示

- [x] PL1-9: 在创建/编辑表单中暴露 imports 字段
  - 目标：用户可通过 UI 为记忆添加依赖边，而非必须使用 CLI
  - 验收：表单中可输入逗号分隔的 import IDs，每条带强度选择器（required/recommended/related）；提交后新记忆的 resolve 结果包含其 imports 链

### 第三梯队（锦上添花 — 本轮至少完成一项）

- [x] PL1-10: 替换默认占位 body 文本
  - 目标：消除用户误提交占位文本记忆导致索引污染的风险
  - 验收：新建记忆的 body 字段为空白或含结构化提示模板，不再出现 "Write content here..." 等无意义文本；提交空 body 的记忆也按最小有效记忆处理

## 第 2 轮追加任务（基于体验官审计 — 2026-04-30）

### 第一梯队（重要 UI 缺陷 — 本轮必须完成）

- [x] PL2-1: 前端正确展示 API 校验错误详情
  - 目标：前端的 API 错误处理能从 FastAPI 响应体中提取 detail 字段，用户看到的是 "Memory ID must contain at least one '/' separator" 而非 "API error: 422 Unprocessable Entity"
  - 验收：提交一个无效 ID（无 "/" 分隔符），前端表单错误栏显示人类可读的校验信息而非 HTTP 状态码文本

- [x] PL2-2: 修复 Legend 目录颜色键使其与 GraphCanvas 一致
  - 目标：Legend 组件使用的目录颜色键与 GraphCanvas 实际渲染逻辑使用的键完全对齐，当节点落入未映射目录时的默认颜色也有图例说明
  - 验收：检查 Legend 中的每个颜色条目，与 GraphCanvas 中对应目录节点的实际渲染颜色逐项比对一致；图例包含默认颜色（#57534E）的含义说明

- [x] PL2-3: 使 MemoryDetail 面板中的 imports 依赖可点击导航
  - 目标：MemoryDetail 面板中显示的每个 import 依赖 ID 都是可点击链接，点击后关闭当前详情并打开该依赖的详情面板
  - 验收：打开一条有 imports 的记忆详情，点击其中一个依赖 ID，详情面板切换为该依赖记忆的信息

- [x] PL2-4: 为 /api/validate 响应添加 validated_count 字段
  - 目标：validate 响应中包含 `validated_count` 字段指示实际扫描了多少条记忆，前端结果模态展示此数字
  - 验收：curl POST /api/validate 返回 `validated_count: 10`（或与实际记忆数一致）；前端 validate 结果弹窗显示 "N 条记忆已检查"

- [x] PL2-5: 移除 MaturityBadge 中无法触达的 "stale" 样式条目
  - 目标：删除 MaturityBadge 组件中为不存在的 maturity 值 "stale" 定义的颜色样式，消除死代码
  - 验收：代码审查确认 MaturityBadge 样式映射中不再包含 "stale" 键；stale 状态仅通过 Dashboard 的 stale_ids 机制呈现

### 第二梯队（一致性改进 — 本轮尽量完成）

- [x] PL2-6: 统一 Archive 按钮颜色
  - 目标：上下文菜单的 Archive 确认按钮（灰色）与编辑表单的 Archive 按钮（红色边框）使用一致的视觉信号
  - 验收：表单中的 Archive 按钮改为与上下文菜单一致的灰色/非警示色系，两者视觉上传达同一语义

- [x] PL2-7: 统一端口文档
  - 目标：消除 CLAUDE.md、vite.config.ts 中端口号的不一致，使文档与代码中声明的端口完全对齐
  - 验收：检查 CLAUDE.md、vite.config.ts 和其他提及端口号的文档，端口号不再互相矛盾

- [x] PL2-8: 为上下文菜单添加 Escape 键关闭支持
  - 目标：按下 Escape 键可以关闭已打开的右键上下文菜单，与 MemoryDetail 和 MemoryForm 的 Escape 关闭行为一致
  - 验收：在图上右键打开上下文菜单，按 Escape 键菜单关闭；已关闭后按 Escape 不会产生副作用

### 第三梯队（体验增强 — 本轮视时间完成至少一项）

- [x] PL2-9: 在 Wander 界面暴露 cool/random 模式切换
  - 目标：用户可以在 UI 中选择 Wander 的探索模式（cool 冷记忆 / random 随机），而非仅支持后端默认模式
  - 验收：Wander 触发按钮旁（或弹窗内）有模式选择控件；选择不同模式后 Wander 返回行为有明显差异

- [x] PL2-10: 在 resolve 输出中突出展示 pinned 版本提示
  - 目标：resolve 返回的 pinned 版本过时通知（"[NOTICE] pinned version v1 of ... is behind current version v2"）在 MemoryDetail 面板的 Resolve 区域有醒目展示，而非埋在 raw text 末尾
  - 验收：resolve 一条含有 pinned 版本依赖的记忆后，版本落后通知出现在 Detail 面板的可见区域（非正文片段末尾）

## 第 3 轮追加任务（基于体验官审计 — 2026-04-30）

### 第一梯队（体验一致性与可用性 — 本轮必须完成）

- [x] PL3-1: 修复搜索栏占位文本截断
  - 目标：搜索输入框的 placeholder 文本完整显示，不再被输入框宽度裁剪
  - 验收：搜索栏占位文本完整显示 "Search by tag, directory, or keyword..."；在不同窗口宽度下不出现截断

- [x] PL3-2: 统一图节点字体为 Raleway
  - 目标：消除 GraphCanvas 中 Cytoscape 节点标签使用 Inter 的字体不一致，统一为 Raleway
  - 验收：图上所有节点标签使用 Raleway 字体；产品中不再出现 Inter 字体引用

- [x] PL3-3: 实现 Resolve 拓扑动画
  - 目标：Resolve 完成后节点按依赖拓扑顺序依次高亮（300ms/步金色脉冲），以动画展示 DAG 组装过程
  - 验收：点击 Resolve 后，节点从源到目标依次出现金色高亮动画；动画完成后所有节点显示 trim-level 样式

- [x] PL3-4: 上下文菜单 hover 添加过渡动画
  - 目标：右键菜单项在 hover 时有平滑的背景色过渡（而非瞬间切换）
  - 验收：鼠标划过菜单项时背景色在约 100ms 内平滑过渡；动画自然不突兀

- [x] PL3-5: 添加 Clear Resolve 按钮
  - 目标：用户可通过显式按钮重置 Resolve 状态（恢复节点透明度），无需关闭再打开详情面板
  - 验收：Resolve 区域标题旁出现 Clear 按钮；点击后所有节点恢复原始样式；详情面板无需关闭

- [x] PL3-6: 放宽 imports 依赖展示上限
  - 目标：MemoryDetail 面板中展示更多依赖项（当前限制 5 条），减少信息截断
  - 验收：展示全部 imports 依赖或至少 10 条；超出合理数量时提供展开/折叠切换

### 第二梯队（生命周期与操作改进 — 本轮尽量完成）

- [x] PL3-7: 在创建/编辑表单中暴露 maturity 字段
  - 目标：用户可在创建和编辑记忆时设置 maturity 值（draft/verified/proven/superseded），与 status 字段形成完整生命周期管理
  - 验收：创建和编辑表单中均出现 maturity 下拉选择器；新建记忆可指定 maturity；编辑可修改

- [x] PL3-8: 隐藏 Force 布局模式
  - 目标：将 Force 布局从主要布局选项降级，默认仅显示 Dagre 布局
  - 验收：Graph 视图默认布局为 Dagre；Force 布局不再作为平级选项出现在主界面；若保留则隐藏在 Advanced 折叠区域内

### 第三梯队（战略资产 — 本轮至少完成一项）

- [x] PL3-9: 创建英文示例数据集
  - 目标：提供一套英文记忆数据作为备选默认数据集（软件架构决策或产品设计理由等通用技术领域），使非中文评估者可体验产品的核心价值主张
  - 验收：存在可切换的英文示例数据集（8-12 条记忆，含 meaningful 依赖关系）；通过环境变量或配置标记可切换；英文数据集同样通过 validate 检查

## 第 4 轮追加任务（基于体验官 + 进化策略师审计 — 2026-04-30）

### 第一梯队（Critical 回归修复 + 竞争性短板 — 本轮必须完成）

- [x] R4-force-hide: 彻底移除 Force 布局按钮
  - 目标：Force 布局按钮不再出现在 Graph 视图头部（上一轮 PL3-8 的修复仅添加了代码注释，未真正隐藏 UI 元素——体验官现场审计时按钮仍可见）
  - 验收：Graph 视图头部仅显示 Dagre 布局（或仅一种布局时完全不显示布局切换控件）；Force 布局按钮不在 DOM 中渲染

- [x] R4-legend: 使 Legend 组件动态化
  - 目标：Legend 展示的目录-颜色映射来源于实际加载的数据集图数据，而非硬编码的投资目录（当前无论加载哪个数据集，Legend 始终显示 10 个中文投资目录——体验官证实 Round 3 曾称赞 Legend "truthful"，现在退化为误导性信息）
  - 验收：切换到不同数据集后 Legend 目录条目随之变化；Legend 仅显示实际包含节点的目录；对于不在已知颜色映射中的目录显示合理的回退颜色说明

- [x] R4-stale-fix: 修复英文数据集 body hash staleness
  - 目标：英文软件架构数据集 11 条记忆中所有 summary_hash 值与实际 body 内容一致，不再出现全量 stale 状态
  - 验收：在英文数据集上执行 reindex，Dashboard stale_count 为 0；resolve 输出中不再出现占位哈希导致的 stale 通知

- [x] R4-backlinks: 为 MemoryDetail 面板添加 "Referenced By"（被引用）区域
  - 目标：查看一条记忆时展示哪些其他记忆通过 imports 依赖了它（进化策略师认定的首要竞争性缺失——所有主要竞品均具备此功能，且入度数据已存在于图结构中）
  - 验收：MemoryDetail 面板中在 imports 区域下方（或对称位置）显示 "Referenced By" 区域，列出可点击的记忆 ID；无反向引用时显示对应空状态提示

### 第二梯队（重要功能缺口 — 本轮尽量完成）

- [x] R4-default-depth: 将 resolve 默认深度从 required 改为 recommended
  - 目标：让 Resolve 在默认情况下实际遍历依赖边，展示产品的核心价值主张（当前默认 depth=required 导致示例数据集的 resolve 从不遍历任何依赖——所有边都是 recommended 强度，用户看不到 DAG 解析的真正能力）
  - 验收：在 UI 中点击 Resolve（不做任何深度调整），对存在 recommended 依赖的记忆能遍历并展示其依赖链；后端 /api/resolve 端点默认行为同步变更

- [x] R4-backend-default: 使 Backend 支持数据集切换（不再硬编码 investment 目录）
  - 目标：用户无需重启后端或手动设置环境变量即可在不同数据集之间切换（当前 server.py 硬编码 examples/investment，英文数据集仅能通过 CODEMEMORY_ROOT 环境变量访问——体验官发现的三大关键问题之一）
  - 验收：Backend 提供数据集切换机制；英文数据集可通过正常启动流程访问；Dashboard 和 Graph 在切换后自动刷新

- [x] R4-reindex-ui: 为 Dashboard 添加 Reindex 按钮
  - 目标：用户可通过 UI 触发重建索引，无需使用 CLI（当前 reindex 为 CLI-only，创建/编辑/归档后图自动刷新但索引重建需手动执行命令）
  - 验收：Dashboard 可见 Reindex 按钮；点击后触发后端 reindex 并刷新所有面板数据；操作有加载状态反馈

- [x] R4-undo: 为记忆操作添加撤销能力
  - 目标：创建、编辑、归档操作后出现有时限的撤销提示，让用户可以回滚误操作（进化策略师认定这是 2026 年产品的基本期望——当前任何操作不可逆）
  - 验收：创建/编辑/归档操作后出现含 "Undo" 按钮的提示条；点击 Undo 能回滚操作；提示条在约 5 秒后自动消失

### 第三梯队（引导与体验 — 本轮至少完成一项）

- [x] R4-onboarding: 首次使用引导
  - 目标：新用户首次打开产品时看到结构化引导，了解 CodeMemory 的核心概念和操作方式（进化策略师指出当前用户看到 11 个彩色圆圈，完全不知道产品解决什么问题或如何使用）
  - 验收：首次访问时展示引导流程（通过浏览器存储检测）；引导至少覆盖 Graph 视图、Resolve 操作、创建记忆三个核心概念；引导可跳过且不重复出现；Help 按钮在引导期间有视觉提示

- [x] R4-search-ui: 在 UI 中暴露全文搜索能力
  - 目标：搜索栏支持跨记忆正文内容的搜索，并展示排名搜索结果列表（当前搜索仅做标签/ID/目录的子串匹配并高亮节点——CLI 的 `codememory search --query` 能力未在 UI 中暴露）
  - 验收：搜索时返回包含正文匹配的排名结果列表；结果展示记忆 ID、summary 及匹配片段预览；点击结果导航到对应记忆详情

## 第 5 轮追加任务（基于体验官 + 进化策略师审计 — 2026-05-06）

### 第一梯队（🔴 关键缺陷修复 — 本轮必须完成）

- [x] R5-backlinks-fix: 修复 backlinks 后端端点路由顺序
  - 目标：GET /api/memories/{id}/backlinks 端点可被正常访问，不再被通配路由拦截返回 404
  - 验收：curl 请求任意记忆的 backlinks 端点返回反向引用列表（或空列表），而非 "Memory '.../backlinks' not found in index" 错误
  - 来源：上轮遗留缺陷（R4 Eval + Round 5 体验官均报告 FAIL）+ 进化策略师 Critical

- [x] R5-helppanel-update: 更新 HelpPanel 文档以反映当前 UI 状态
  - 目标：HelpPanel 中不再包含已移除功能（Force 布局）的描述，Legend 颜色说明反映动态派生机制
  - 验收：HelpPanel 全文无 "Force" 布局相关内容；Legend 说明不出现硬编码的投资目录颜色；若 UI 指南部分无法维护则考虑替换为动态方案或链接到 Onboarding
  - 来源：体验官 Critical #2（stale documentation erodes trust）

### 第二梯队（🟡 高价值改进 — 本轮尽量完成）

- [x] R5-backend-pagination: 为 API 端点添加分页支持
  - 目标：/api/memories 和 /api/search 支持 offset/limit 参数，防止大数据集下性能退化
  - 验收：/api/memories?offset=0&limit=5 返回不超过 5 条结果并包含 total 计数；/api/search 支持 limit 参数；默认 limit 值合理
  - 来源：进化策略师 Critical #3（无分页将在 200+ 记忆时触发性能问题）

- [x] R5-memory-list-view: 添加记忆列表/表格浏览视图
  - 目标：用户可通过表格形式浏览、排序、过滤全部记忆，补充纯图视图的不足
  - 验收：导航栏新增 "List" 视图选项（Graph / List / Dashboard 三视图）；列表展示 ID、Summary、Type、Maturity、Tags、Status 列；支持按列排序和基本过滤
  - 来源：进化策略师 Critical #2（#1 竞争性缺失——所有主要竞品均具备）+ 体验官认可

- [x] R5-keyboard-shortcuts: 添加最小键盘快捷键集
  - 目标：常用操作可通过键盘完成，降低鼠标依赖
  - 验收：Ctrl+K 聚焦搜索栏；Ctrl+N 打开创建表单；Ctrl+Z 触发撤销；Escape 关闭面板/菜单（已有，确认不退化）；若存在快捷键覆盖层（? 键）则列出所有快捷键
  - 来源：进化策略师 Critical #6（power users will not adopt without these）+ 体验官 Nice-to-have #5

- [x] R5-unsaved-changes-warning: 添加未保存更改警告
  - 目标：关闭含未保存内容的编辑表单时弹出确认提示，防止数据丢失
  - 验收：在编辑表单中修改内容后点击遮罩/按 Escape/点 X 关闭时，弹出 "You have unsaved changes. Discard?" 确认对话框；未修改内容时正常关闭无提示
  - 来源：进化策略师 Critical #5（basic UX expectation that prevents data loss）

- [x] R5-template-create: 添加"从模板创建"功能
  - 目标：创建记忆时可选从已有 schema 生成预填模板（如 architectural-decision），降低结构化记忆的创建门槛
  - 验收：创建表单中提供模板选择器（列出所有 type=schema 的记忆）；选择模板后表单预填 schema 定义的结构化字段；仍可手动覆盖任何预填值
  - 来源：进化策略师 Critical #4（schema system exists but invisible in UI）

### 第三梯队（🟢 锦上添花 — 本轮至少完成一项）

- [x] R5-resolve-clear-animation: 添加 Clear Resolve 过渡动画
  - 目标：清除 Resolve 状态时节点从 trim 样式平滑过渡回正常样式，而非瞬间跳变
  - 验收：点击 Clear Resolve 后节点在约 300ms 内从 dimmed/shrunk/dashed 渐变回正常透明度/大小/边框
  - 来源：体验官 Important #3（polish，与拓扑动画的 300ms/step 风格一致）

- [x] R5-deduplicate-colors: 消除 DIRECTORY_COLORS 跨组件重复定义
  - 目标：目录颜色映射在一处集中定义，GraphCanvas 和 Legend 从同一来源引用
  - 验收：两个组件不再各自维护一份颜色映射副本；修改颜色定义只需改一处
  - 来源：进化策略师 Important（duplication causes visual drift）+ Planner 自主判断

- [x] R5-clickable-dashboard: 使 Dashboard 元素可交互导航
  - 目标：Dashboard 中的 tag 标签、maturity 柱状图、stale 记忆列表项可点击，导航到对应过滤视图
  - 验收：点击 Dashboard 中的 tag 后导航到过滤了该 tag 的列表或图视图；点击 stale 列表项导航到该记忆详情
  - 来源：进化策略师 Important（Dashboard should be a launchpad, not just a report）

- [x] R5-graph-node-tooltips: 添加图节点悬浮提示
  - 目标：鼠标悬浮图节点时显示其 summary，无需点击打开详情面板
  - 验收：悬浮节点 300ms 后出现 tooltip 显示记忆 summary；移开后 tooltip 消失
  - 来源：进化策略师 Important（reduces friction for graph exploration）

## 第 6 轮追加任务（基于体验官 + 进化策略师审计 — 2026-05-06）

### 第一梯队（🔴 Critical Bug 修复 — 本轮必须完成）

- [x] R6-B1: 修复 MemoryForm.tsx 中缺失的 `useRef` import
  - 目标：编辑记忆时不再因 `ReferenceError: useRef is not defined` 崩溃
  - 验收：`import { useState, useEffect, useCallback, useRef } from 'react'`；编辑操作正常完成；TypeScript 零错误
  - 来源：体验官 Critical #1（Runtime Crash — any edit operation throws）

- [x] R6-B3: 使 resolve 端点返回 HTTP 404 而非 200（目标记忆不存在时）
  - 目标：后端 `/api/resolve` 对不存在的记忆 ID 返回 HTTP 404，与 `GET /api/memories/{id}` 行为一致
  - 验收：`curl -s -o /dev/null -w "%{http_code}" -X POST .../api/resolve -d '{"id":"nonexistent/id",...}'` 返回 `404`；存在的 ID 仍返回 200
  - 来源：体验官 Critical #2（Silent failure — error buried in body, frontend shows empty success）

- [x] R6-B5: 空搜索查询在 Backend 入口短路返回
  - 目标：当 `query` 为空字符串或仅含空白时立即返回空结果，不扫描全部索引
  - 验收：`curl -X POST .../api/search -d '{"query":""}'` 立即返回 `{"results":[],"count":0,"total":0,...}`；非空查询行为不变
  - 来源：体验官 Critical #3（Wasted backend computation + semantic inconsistency）

- [x] R6-integration-tests: 修复 5 条失败的集成测试
  - 目标：`PYTHONPATH=src python tests/integration_test.py` 返回 24/24 passed（当前 5 条因 sandbox fixture 缺失而失败）
  - 验收：`integration_test.py` 输出 `24/24 passed`；57 条单元测试零退化；修复方案不依赖 harnesslib 环境
  - 来源：进化策略师 Critical #3（regression risk — no safety net for backend changes）

### 第二梯队（🟡 错误可见性 + 组件卫生 — 本轮尽量完成）

- [x] R6-B2: 移除 MemoryForm 中未使用的 `onSelectMemory` prop
  - 目标：从 Props 接口和解构中删除声明但从未引用的死 prop
  - 验收：TypeScript 零错误；MemoryForm 接口中无 `onSelectMemory`
  - 来源：体验官 High #7（Dead code misleads future readers）

- [x] R6-B4: 修复 0-count "draft" maturity 柱状图始终渲染的问题
  - 目标：移除 Dashboard.tsx 中对 draft 的特殊豁免（`if (count === 0 && key !== 'draft')`），所有 maturity 在 count 为 0 时均不渲染柱状条
  - 验收：当 draft 数量为 0 时不显示空 bar；非零时正常显示
  - 来源：体验官 High #8（Visual confusion — empty bar with 0 count）

- [x] R6-network-error-feedback: 添加用户可见的网络错误反馈
  - 目标：当 API 不可达时显示 toast 或 banner（而非仅 `console.error`）
  - 验收：断开后端后刷新页面或操作时出现可见的用户提示；恢复后提示消失或可关闭
  - 来源：体验官 High #4（Errors swallowed into console — user sees nothing）

- [x] R6-resolve-error-feedback: 在 UI 中展示 Resolve 错误信息
  - 目标：当 resolve 端点返回 404 或错误文本时，在 Resolve 面板中展示错误（而非静默显示空面板）
  - 验收：resolve 一条不存在的记忆后，面板中显示错误信息而非空白内容
  - 来源：体验官 High #5（B3 counterpart — backend fix alone doesn't help the user）

- [x] R6-consolidate-badges: 提取共享的 StatusBadge 和 MaturityBadge 组件
  - 目标：两个组件从单一共享文件导入，消除 MemoryDetail 和 MemoryList 中的重复定义
  - 验收：MemoryDetail 和 MemoryList 均从 `components/Badges.tsx`（或等效共享路径）导入；两处样式一致；重复代码已移除
  - 来源：体验官 High #6（Duplication causes visual drift between views）

### 第三梯队（🟢 战略功能 + 打磨 — 本轮至少完成一项）

- [x] R6-resolve-to-prompt: "Resolve to Prompt"——将解析上下文导出为格式化 LLM 系统提示
  - 目标：Resolve 面板新增"Generate Prompt"按钮，将已解析的所有节点按拓扑顺序格式化为 LLM 系统提示，含节点 trim level 标注和 token 计数，一键复制到剪贴板
  - 验收：点击按钮后剪贴板包含结构化 prompt（含 resolved context + token budget + 指令块）；token 计数与 budget slider 一致；存在 resolve 结果的记忆均可操作
  - 来源：进化策略师 Critical #4（#1 highest-ROI feature — bridges CodeMemory to AI ecosystem）

- [x] R6-ui-polish: CSS 字体回退 + Undo toast 打磨
  - 目标：(a) 在 `font-family` 链中添加系统字体回退（`Georgia, serif` / `system-ui, sans-serif`），防止 Google Fonts CDN 故障导致无字体；(b) 移除 undo toast 中的 "x" 关闭按钮（冗余于 5s 自动消失）；(c) 为 undo toast 添加 200ms fade-in + slide-up 入场动画
  - 验收：CSS 中 `font-family` 声明包含系统字体回退；undo toast 无 "x" 按钮；toast 出现时有可见的入场动画
  - 来源：体验官 Medium #10/#12/#13（polish items bundled into one task）

## 第 7 轮追加任务（基于体验官 + 进化策略师审计 — 2026-05-06）

### 第一梯队（🔴 Critical 修复 — 本轮必须完成）

- [ ] R7-N2: 消除 Pydantic 模型中 `id` 字段名对 Python `id()` 内置的遮蔽
  - 目标：将 `ResolveRequest` 和 `CreateMemoryRequest` 中的 `id` 字段重命名为 `memory_id`，通过 `Field(alias="id")` 保持 API wire format 不变，消除未来开发者使用 `vars(req)` 或 `hasattr` 时意外获取整数内存地址的风险
  - 验收：API 请求仍使用 `"id"` 键（curl 命令不变）；代码内部字段为 `memory_id`；`grep "id: str" backend/server.py` 在 Pydantic 模型中不再出现原样未别名化的 `id` 字段；TypeScript 零错误，前端构建通过
  - 来源：体验官 Critical N2

- [ ] R7-N1: 处理 quant_operators 数据集的 62 条无 imports 记忆
  - 目标：在数据集切换器中为 quant_operators 添加可见的免责声明说明该数据集为自动生成的 API 文档、不含手动策划的语义依赖；同时通过 `suggest-deps` 批量推断 imports 以恢复部分 DAG 连通性
  - 验收：切换到 quant_operators 数据集时，UI 显示该数据集为生成文档而非手动策划的说明；至少有部分记忆获得了推断的 imports 依赖（不再全部是单节点 DAG）；切换回其他数据集时声明不残留
  - 来源：体验官 High N1

### 第二梯队（🟡 竞争性短板 + 一致性 — 本轮尽量完成）

- [ ] R7-export: 添加记忆导出功能
  - 目标：用户可将全部记忆导出为 .zip 文件（含全部 .md 文件 + index.json）；图视图支持导出为 SVG 和 PNG
  - 验收：Dashboard 或设置中有 Export 按钮；点击后下载 .zip，解压后包含完整记忆文件与 index.json；图视图有导出 SVG/PNG 按钮，导出图片包含当前可见的图渲染结果（节点、边、Legend）；导出操作有加载状态反馈
  - 来源：进化策略师 Critical #1

- [ ] R7-dark-mode: 添加深色模式 / 主题支持
  - 目标：系统感知的亮色/深色主题切换，通过 `data-theme` 属性 + CSS 自定义属性覆盖实现完整的深色配色方案；在头部或设置中提供手动切换开关
  - 验收：切换后所有视图（Graph/List/Dashboard/Detail/Form/Modal/Onboarding）均有对应的深色配色；`prefers-color-scheme` 媒体查询正常工作；手动切换覆盖系统偏好并持久化；亮色模式视觉效果不退化
  - 来源：进化策略师 Critical #2

- [ ] R7-settings: 添加设置页面
  - 目标：提供用户可配置的默认值：默认数据集（启动时自动加载）、默认 resolve budget（slider 初始值）、主题选择（light/dark/system）；通过滑出面板或 gear 图标访问；设置持久化到 localStorage
  - 验收：用户可设置并持久化默认数据集（下次启动自动加载该数据集）；可设置默认 budget 值（resolve 面板初始值使用该默认而非硬编码值）；主题设置持久化并在启动时恢复；设置面板可通过 Escape 或点击遮罩关闭
  - 来源：进化策略师 Critical #3

- [ ] R7-semantic-search: 添加模糊文本搜索
  - 目标：后端搜索支持 trigram 模糊匹配（Python stdlib `difflib`），使搜索 "risk" 能匹配 "risk-tolerance"，搜索含拼写错误的关键词仍能有合理容错；精确匹配结果排在模糊匹配结果之前；前端显示匹配质量指示
  - 验收：搜索 "risk" 返回 `user/investment/risk-tolerance` 等匹配结果；搜索含拼写错误的关键词仍能有合理容错；精确匹配排在模糊匹配之前；前端结果展示区分精确匹配与模糊匹配（如 match_quality 标识）
  - 来源：进化策略师 Critical #4

- [ ] R7-N3: 修复搜索增强管道静默丢弃结果
  - 目标：当搜索结果的主体文件路径无法解析时，记录警告并返回不含 snippet 的结果，而非静默排除该结果
  - 验收：即使某些结果无 body 文件路径，搜索结果仍包含它们（snippet 字段为空或标注不可用）；后端日志中出现对应 WARNING；搜索结果计数与索引匹配数一致（不静默减少）
  - 来源：体验官 Medium N3

- [ ] R7-N5: 统一三视图空状态
  - 目标：Graph/List/Dashboard 三视图在无记忆或无匹配结果时使用一致的 EmptyState 组件，提供情境化的引导文案和操作建议
  - 验收：Graph 空状态显示引导（如 "No memories yet — Click + New to add your first memory"）及创建按钮；List 过滤后无结果时显示 "No matching memories — try clearing the filter" 及清除过滤的按钮；Dashboard 空状态显示欢迎信息及创建 CTA；三种空状态视觉风格（图标、排版、间距）一致
  - 来源：体验官 High N5

### 第三梯队（🟢 打磨 — 本轮至少完成一项）

- [ ] R7-prompt-metadata: 为生成的 LLM prompt 添加记忆元数据
  - 目标：Generate Prompt 输出中包含每条记忆的 maturity、status、tags，使 AI 能够根据记忆可信度（proven > verified > draft）和状态（active > archived）加权使用信息
  - 验收：生成的 prompt 中每条记忆节点包含 maturity 和 status 标注；指令块说明了如何解释 maturity/status 差异以加权信息；元数据不影响 prompt 的 token 预算计算
  - 来源：体验官建议（Phase 3 Product Imagination — Resolve-to-Prompt 改进）

- [ ] R7-wander-improve: 改进 Wander 体验
  - 目标：移除 Cool/Random 模式切换（默认使用 cool 行为——按反向访问次数加权）；添加"为什么是这条记忆？"的说明（显示访问次数、intensity、上次访问时间）；添加 Wander 价值主张的一行说明
  - 验收：Wander 按钮为单一操作（无模式选择 toggle）；弹窗中显示记忆被选中的原因（访问次数、intensity、上次访问时间）；Wander 界面包含一句话价值说明（如 "Surfaces a memory you haven't revisited recently"）；从 Wander 弹窗仍可点击导航到记忆详情
  - 来源：进化策略师建议（Wander simplification）

## 第 8 轮追加任务（基于体验官 + 进化策略师审计 — 2026-05-06）

### 第一梯队（🔴 Critical 修复 — 本轮必须完成）

- [x] R8-darkmode-graph: 修复深色模式图渲染
  - 目标：将 GraphCanvas.tsx 中 Cytoscape 样式表的所有硬编码 hex 颜色值替换为主题感知的颜色值。节点标签颜色、边线颜色（required/recommended/related）、schema 节点背景和边框、dimmed 节点颜色必须响应活动主题。主题切换时 cytoscape 实例须重新渲染更新后的颜色。
  - 验收：深色模式下所有图节点标签在深色背景上可见；三种强度的边线均可见；schema 节点使用适当的深色背景（非亮色 #faf9f5）；trimmed/dimmed 节点在深色模式下可区分；亮色/深色切换时图实时更新且无需页面刷新；亮色模式图渲染与当前状态视觉一致；系统主题变更（OS 或 DevTools）时图跟随更新
  - 来源：体验官 Critical（深色模式评分 5.5/10，图是产品主视图却被遗漏）+ R7 Eval 遗漏（code review 通过但未实测深色模式图渲染）

- [x] R8-css-border-migration: 迁移所有硬编码 border 颜色到 CSS 变量
  - 目标：将整个前端中所有硬编码的 border 颜色值替换为对应的 CSS 变量。映射关系：#E7E5E4 → var(--cm-border)，#D4D4D8 → var(--cm-border-cool)，#F5F5F4 → var(--cm-bg-subtle)，强调色边框（#B8860B/#CA8A04/#1E40AF）→ var(--cm-accent)。覆盖文件：App.tsx（header/view switcher/dataset select/context menu/archive modal/shortcuts modal 边框）、SearchBar.tsx（input 边框/results dropdown 边框）、Dashboard.tsx（Validate/Refresh/Reindex 按钮边框）、MemoryDetail.tsx（panel 边框/metadata card 边框/resolve 按钮边框）、Legend.tsx（容器边框/边线样式指示器边框）。共约 15 处。
  - 验收：任何 .tsx 组件中不存在硬编码 hex border 颜色值；所有 border 均使用 CSS 变量；深色模式下 border 渲染为深色适配色；亮色模式下 border 渲染与当前状态视觉一致；TypeScript 零错误，前端构建通过
  - 来源：体验官 High（约 40% 的 border 实例为硬编码，深色模式下产生视觉不一致）

### 第二梯队（🟡 高价值改进 — 本轮尽量完成）

- [x] R8-empty-state-cta: 完成 R7-N5 — 为 EmptyState 添加 CTA 按钮 + 统一 List 过滤空状态
  - 目标：三处修复：(a) Graph 视图 EmptyState 添加 `actions` prop 含 "+ New" 按钮；(b) Dashboard EmptyState 添加 `actions` prop 含 "Create Memory" 按钮；(c) 将 List 视图过滤后无结果时的内联 `<div>`（自定义 padding、无图标、不同排版）替换为共享 EmptyState 组件，含适当 icon/title/description 及 "Clear Filter" 操作按钮。
  - 验收：Graph 空状态含 "+ New" 按钮可打开创建表单；Dashboard 空状态含 "Create Memory" 按钮可打开创建表单；List 过滤空状态使用共享 EmptyState 组件（非自定义 div）；List 过滤空状态含 "Clear Filter" 操作按钮；三种空状态视觉风格（图标、排版、间距）一致；零记忆状态与零过滤结果状态通过文案/图标区分
  - 来源：R7 Eval PARTIAL PASS（组件存在但未传 actions prop；List 过滤空状态绕过共享组件）

- [x] R8-quant-disclaimer: 完成 R7-N1 — 添加 quant_operators 数据集说明
  - 目标：在 `currentDataset === 'quant_operators'` 时，于数据集切换器区域显示条件性说明信息。说明该数据集为自动生成的 API 文档、非手动策划，依赖图为算法推断而非人工语义链接。信息性而非警告性语气。切换到其他数据集时说明消失。
  - 验收：切换到 quant_operators 数据集时显示可见的 disclaimer 信息；信息说明该数据集为自动生成文档；语气为信息性（非 error/warning）；切换到其他数据集（investment/software-architecture/companion）时 disclaimer 移除；disclaimer 不干扰正常数据操作（搜索/resolve 等）
  - 来源：R7 Eval PARTIAL PASS（suggest-deps 成功推断 imports，但条件性数据集 disclaimer 从未实现）

- [x] R8-png-export-ui: 在 Graph 视图工具栏添加 PNG 导出按钮
  - 目标：在 Graph 视图工具栏添加可见的 "Export PNG"（或 "Save as PNG"）按钮。按钮触发 GraphCanvas.tsx 中已存在的 `handleExportPng` 函数（调用 `cy.png()`）。按钮样式与现有工具栏控件一致，渲染期间有短暂的加载反馈。
  - 验收：Graph 视图工具栏含可见的 "Export PNG" 按钮；点击按钮触发当前图视图的 PNG 下载；按钮与现有工具栏按钮样式一致；渲染期间有简短反馈（如按钮文字变为 "Rendering..."）
  - 来源：体验官 High #3（PNG 导出已实现但前端 UI 不可见——功能存在但无法使用）

- [x] R8-wander-dismiss: Wander 结果可不导航直接关闭/重试
  - 目标：在 Wander 弹窗中 "View Details" 按钮旁添加 "Wander Again" 次要操作按钮。点击后发起新的 wander 请求并更新弹窗内容。用户无需打开详情面板即可循环浏览冷记忆。
  - 验收：Wander 弹窗含次要操作按钮（"Wander Again"）；点击后发起新 wander 请求并更新弹窗内容；"View Details" 按钮保持原行为；弹窗仍可通过 X 按钮或 Escape 关闭
  - 来源：体验官 High #4（wander 仅有一个操作 "View in Graph"——用户无法跳过当前结果）

- [x] R8-search-match-quality: 为所有搜索结果一致展示匹配质量
  - 目标：为每条搜索结果添加始终可见（非条件性）的匹配质量指示器。精确匹配显示绿色 "exact" 标识/勾选；模糊匹配显示琥珀色分数标识（如 "~82%"）。指示器位于每条结果行右侧，位置统一。移除当前仅在有模糊结果时才显示质量指示的条件性行为。
  - 验收：每条搜索结果均显示匹配质量指示器（不依赖是否存在模糊结果）；精确匹配显示绿色指示器；模糊匹配显示琥珀色指示器 + 分数百分比；指示器在结果间位置一致；搜索结果渲染和点击导航行为无退化
  - 来源：体验官 Medium #5（当前 UI 不一致地显示匹配质量——仅在模糊结果存在时才显示匹配标识）

### 第三梯队（🟢 打磨 — 本轮至少完成一项）

- [x] R8-darkmode-shortcut: 添加深色模式切换键盘快捷键
  - 目标：添加 Ctrl+Shift+D 作为亮色/深色主题切换的键盘快捷键。切换为二元操作（light ↔ dark），system 模式通过 Settings 设置。在 Help 面板的快捷键覆盖层（? 键触发）中记录该快捷键。
  - 验收：Ctrl+Shift+D 切换亮色/深色主题；切换为二元操作（light ↔ dark）；快捷键记录在 Help 面板覆盖层中；现有快捷键（Ctrl+K/Ctrl+N/Ctrl+Z/?）继续工作；切换与 Settings 面板和 header 按钮使用相同的持久化机制
  - 来源：体验官 Medium #6（15 分钟打磨项，power user 预期行为）

- [x] R8-search-match-fields: 在搜索结果中显示匹配字段指示
  - 目标：为每条搜索结果展示哪些字段匹配了查询（如 "matched: id, summary" 或小型字段标签指示器）。使用后端 API 已返回的 `match_fields` 数组。以小型、微妙文字或标签形式呈现在结果摘要下方——不作为主导视觉元素。
  - 验收：每条搜索结果展示匹配了哪些字段；字段指示器为微妙样式（小文字或紧凑标签，非主导元素）；常见字段（id/summary/body/tag）使用人类可读标签；无 match_fields 数据的结果优雅降级；不破坏搜索布局或点击导航行为
  - 来源：体验官 Nice-to-have #7（API 已返回 match_fields 但前端从未展示）

- [x] R8-memorylist-empty: MemoryList 零过滤结果使用 EmptyState
  - 目标：将 MemoryList 文本过滤产生零结果时的空可滚动区域替换为共享 EmptyState 组件。EmptyState 显示合适的图标、"0 of N memories match your filter" 消息和 "Clear Filter" 操作按钮。零记忆状态也使用 EmptyState（已在用但需补充 actions prop）。
  - 验收：MemoryList 零过滤结果展示 EmptyState（非空可滚动 div）；EmptyState 含过滤相关的特定消息和 "Clear Filter" 按钮；MemoryList 零总记忆也使用 EmptyState；视觉风格与 Graph 和 Dashboard 空状态一致
  - 来源：体验官 Nice-to-have #9（最后一个视图特定的空状态不一致——MemoryList 未使用 EmptyState）

## 第 9 轮追加任务（基于体验官 + 进化策略师审计 — 2026-05-06）

> **背景**: 体验官 8.5/10（从 7.5 上升），仅剩 cosmetic issues。进化策略师 6.5/10（从 5.0 上升），发现 3 个 Critical 数据完整性 bug。
> **优先级**: 🔴 第一梯队 = 修复 3 个 Critical bug + MemoryList hex；🟡 第二梯队 = 高价值改进；🟢 第三梯队 = 至少一项 polish。

### 第一梯队（🔴 Critical 修复 — 本轮必须完成）

- [x] R9-B1: 修复 Memory ID lookup — GET /api/memories/{id} 对所有有效 ID 返回 404
  - 目标：修复 `GET /api/memories/{id}` 端点，使其能正确检索 index 中已存在的记忆。统一所有端点的 index 加载路径为单一方法，消除 `_load_index()`（raw dict）与 `load_index()`（Pydantic 模型）两种不兼容加载方式。确保 `{memory_id:path}` FastAPI 路由参数正确捕获并匹配含 `/` 分隔符的记忆 ID。
  - 验收：对所有 companion 数据集 10 条记忆，GET /api/memories/{id} 均返回 200；对所有 investment 数据集 10 条记忆，均返回 200；对所有 software-architecture 数据集 11 条记忆，均返回 200；GET /api/memories/{id}/backlinks 返回正确的反向引用数据（非空数组）；MemoryDetail 面板点击任意图节点正常打开；MemoryForm 编辑模式预填正确；GET /api/memories 分页列表无退化；后端 57+24 测试通过
  - 来源：进化策略师 Critical #1 + #5（产品看起来坏了——任何点击记忆的用户都看到 404）

- [x] R9-B2: 修复 Stale 检测 — 100% 误报率
  - 目标：修复 `_stale_check()`，使 `summary_hash` 比对正确匹配 body 内容哈希。定位并对齐 reindex 时（计算 `summary_hash` 并存储）与 check 时（对 `_parse_frontmatter()` 解析的 body 调用 `compute_body_hash()`）之间的 body 文本规范化差异——可能是尾部空白处理、编码规范化（utf-8 vs utf-8-sig）或 body 内容修剪差异。
  - 验收：companion 数据集（10 条）：reindex 后 stale_count = 0；investment 数据集（10 条）：reindex 后 stale_count = 0；software-architecture 数据集（11 条）：reindex 后 stale_count = 0；人为修改某条记忆 body 后 stale_count 正确增加到 1；reindex 后修改过的记忆 stale_count 恢复到 0；Dashboard stale 列表反映准确的 stale 状态；`_stale_check()` 对 Pydantic 模型和 raw dict 均返回正确结果
  - 来源：进化策略师 Critical #2（Dashboard 健康指标完全无意义——用户学会忽略警告）

- [x] R9-B3: 修复全局 MEMORY_ROOT 线程不安全
  - 目标：用 FastAPI 依赖注入或 `request.state` 替换模块级 global `MEMORY_ROOT` 变量。所有当前直接读取 `MEMORY_ROOT` 的函数（`_get_index_path()`、`_stale_check()`、`get_memory()`、文件路径构建等）必须通过依赖接收 root 路径。数据集切换端点必须通过依赖机制更新活跃数据集，而非修改共享全局变量。
  - 验收：server.py 中无 `global MEMORY_ROOT` 语句；所有函数通过参数传递或依赖注入接收 memory root 路径；两个并发请求访问不同数据集（如 graph 查 investment + stats 查 companion）返回正确且数据集一致的结果；POST /api/datasets/switch 正确更新活跃数据集；多个浏览器 tab 可独立查看不同数据集而互不污染；全部 16 个 API 端点重构后功能正常；后端 57+24 测试通过
  - 来源：进化策略师 Critical #4（并发访问下数据不一致——测试中已观测到）

- [x] R9-hex: 替换 MemoryList.tsx 中最后一个硬编码 hex
  - 目标：将 `MemoryList.tsx` 第 225 行的 `'#7C3AED'` 替换为 CSS 变量。该值（紫色）用于 schema 类型文字颜色。替换为 `'var(--cm-info)'`（因为 `--cm-info` 已在 index.css 两个主题中定义，紫色为现有 info 色），或添加专用 `--cm-schema` CSS 变量（亮色模式值 `#7C3AED`，深色模式变体 `#A78BFA` 或 `#C4B5FD`）。
  - 验收：MemoryList.tsx 第 225 行不再含 `'#7C3AED'` 硬编码字符串；schema 类型文字使用主题感知的 CSS 变量；亮色模式下 schema 文字颜色与当前状态视觉一致；深色模式下 schema 文字可见且颜色恰当；所有 .tsx 组件中无其他硬编码 hex 值（通过 grep `'#[0-9A-Fa-f]{6}'` 和 `"#[0-9A-Fa-f]{6}"` 确认）；TypeScript 零错误，前端构建通过
  - 来源：体验官 Critical（98.7% → 100% 迁移完成——5 分钟修复，整个 backlog 中 ROI 最高）

### 第二梯队（🟡 高价值改进 — 本轮尽量完成）

- [x] R9-darkmode-colors: 改进深色模式节点颜色区分度
  - 目标：用目录颜色到深色模式调色板映射替换 GraphCanvas.tsx 中统一的 `themeTint()` 变暗方式。每个目录颜色（如 preferences 的金色 `#B8860B`、feelings 的琥珀色 `#D97706`、beliefs 的绿色 `#166534`）应有更亮、更饱和的深色模式变体，保留颜色语义（如金色变为 `#D4A017` 亮金，而非 `#2E2C2A` 深灰）。深色调色板定义在 `colors.ts` 中与亮色调色板并列（单一真相来源）。`themeTint()` 函数应替换或扩展为对已知目录查色、仅对未知/回退颜色回退到统一变暗。
  - 验收：深色模式下不同目录节点颜色可视觉区分（非全部近似深灰）；每个目录颜色有可感知更亮更饱和的深色模式变体；深色调色板定义在 `colors.ts` 与亮色调色板并列；未知/回退颜色仍走安全变暗（统一方式兜底）；亮色模式节点颜色视觉不变；动态 Legend 在深色模式下正确显示深色颜色；主题切换（亮 ↔ 暗）更新图中节点颜色
  - 来源：体验官 High #2（深色模式最后一个有意义的审美缺口——目录视觉分类丢失）

- [x] R9-graph-viewport: 主题切换时保留图视口位置
  - 目标：在主题变更销毁 cytoscape 实例前存储当前视口状态（缩放级别 `cy.zoom()` 和平移位置 `cy.pan()`），在新实例初始化并完成布局后恢复。这需要读取销毁前的值，并在新实例 `layoutstop` 事件后调用 `cy.zoom(zoom)` 和 `cy.pan(pan)`。
  - 验收：切换主题（亮 ↔ 暗）保留当前缩放级别（误差在 0.01 内）；切换主题保留当前平移位置（x, y，误差在 5px 内）；切换后图以正确主题颜色重新渲染；切换前用户在查看某特定子图区域，切换后看到同一区域；图渲染、布局、交互无退化
  - 来源：体验官 High #3（主题切换丢失空间上下文——令人迷失方向）

- [x] R9-error-feedback: 为 CRUD 操作添加用户可见的错误反馈
  - 目标：为 create、update、reindex、validate 操作失败时添加用户可见的错误反馈。当前错误仅记录到 `console.error`——用户看不到任何提示。修复应复用已建立的网络错误 banner 模式（顶部红色横幅）或扩展现有 toast 系统覆盖操作失败。错误消息必须人类可读（非原始 HTTP 状态码文本）。
  - 验收：创建失败（如无效 ID 格式、后端错误）向用户显示可见错误信息；更新失败显示可见错误信息；reindex 失败（API 返回 500）在 Dashboard 中显示可见错误信息；validate 失败显示可见错误信息；错误消息人类可读（非 "API error: 422"）；错误消息使用已有主题错误 banner 模式（或等效一致机制）；错误 banner 合理超时后自动消失或可通过 X 关闭；成功操作不显示错误反馈
  - 来源：进化策略师 Important #8（静默失败侵蚀信任——仅 2 条错误反馈路径）

- [x] R9-tag-autocomplete: 在 MemoryForm 和 SearchBar 中添加标签自动补全
  - 目标：在创建/编辑表单或搜索栏中输入标签时，建议当前数据集 index 中已存在的标签。自动补全在输入框下方以下拉菜单形式显示匹配标签（前缀匹配或模糊匹配）。选择建议后插入该标签。标签列表应来源于当前数据集实际使用的标签（通过 `/api/stats` 获取或从记忆列表中提取）。
  - 验收：在标签输入框中输入文字显示当前数据集已有匹配标签的下拉菜单；选择建议将标签插入当前输入；建议随用户继续输入过滤（前缀匹配）；标签列表来源于当前数据集实际使用（非硬编码）；创建和编辑表单中均可用；搜索栏标签筛选器（如已暴露）或搜索输入本身可用；62 条 quant_operators 数据集上无性能退化
  - 来源：进化策略师 Important #6（标签不一致破坏过滤和搜索——无自动补全几乎不可能保持一致性）

- [x] R9-validate-drilldown: 使验证结果在 Dashboard 中可操作
  - 目标：Dashboard 的 validate 区域当前仅显示通过/失败计数（如 "0 errors, 0 warnings"）。后端 `/api/validate` 端点返回含具体消息、记忆 ID 和类型的结构化数组（errors 和 warnings）。在 Dashboard 中展示这些详情：显示每条 error/warning 消息，将每个问题关联到对应记忆 ID（可点击打开详情面板），按类型分组（如 "Circular dependency"、"Broken link"、"Maturity decay"）。
  - 验收：Dashboard validate 区域展示具体 error/warning 消息（非仅计数）；每条 error/warning 包含受影响的记忆 ID，可点击打开详情面板；错误和警告按类型分组并含类型标签；顶部仍可见通过/失败汇总；0 错误 0 警告时显示 "All checks passed" 消息；Reindex 按钮在扩展的 validate 展示旁仍正常工作
  - 来源：进化策略师 Nice-to-have #13（后端返回结构化数据——UI 仅显示 pass/fail 计数）

### 第三梯队（🟢 打磨 — 本轮至少完成一项）

- [x] R9-empty-search: 为搜索添加"无结果"状态
  - 目标：当搜索查询返回零结果时，在搜索下拉菜单中显示用户可见的提示，而非什么都不显示。提示应有用且可操作："No memories found matching 'xyz'. Try different keywords." 当前行为（下拉菜单根本不出现）让用户无法确定搜索是否崩溃、仍在加载或确实无结果。
  - 验收：输入匹配零条记忆的查询后搜索下拉菜单显示 "No memories found matching [query]"；提示包含可操作指引（"Try different keywords" 或等效文字）；下拉菜单出现（含提示）而非根本不出现；用户清除查询时下拉菜单正常消失；有结果时正常显示结果列表（无退化）；空结果消息使用恰当样式（非 error，信息性语气）
  - 来源：进化策略师 Nice-to-have #22（最明显的剩余空状态缺口——下拉菜单直接消失）

- [x] R9-loading-skeletons: 为 List 和 Dashboard 添加加载骨架屏
  - 目标：用骨架屏占位组件替换 List 视图和 Dashboard 数据加载期间的空白/闪烁状态。骨架屏应模拟实际内容的布局（如 List 的行状矩形、Dashboard stat card 的卡片状矩形），带微妙的脉冲/shimmer 动画。提供即时视觉反馈表示内容正在加载而非损坏。
  - 验收：List 视图在初始数据加载期间显示骨架行（匹配表格布局）；Dashboard 在初始数据加载期间显示骨架卡片（匹配 stat card 布局）；骨架有微妙的脉冲或 shimmer 动画；数据到达后骨架被实际内容替换；数据加载失败时骨架被适当错误状态替换（非一直挂起）；已有缓存/客户端数据时不出现骨架屏（即时过渡）
  - 来源：进化策略师 Nice-to-have #19（低投入高感知性能改进——空白闪烁被误读为损坏状态）

## 第 10 轮追加任务（基于体验官 + 进化策略师审计 — 2026-05-06）

> **背景**: 体验官 8.0/10，3 个 Critical bug 已确认修复，TDZ 扫描清洁，9/9 功能验证通过，仅剩 cosmetic issues。进化策略师 7.0/10（从 6.5 上升），3 个 Critical bug 已确认修复，MCP server 从 Feature Idea 升级为 Important #5，startup auto-reindex 缺失导致首次访问者看到 stale_count=10。
> **优先级**: 🔴 第一梯队 = MCP server（最高杠杆战略特性）+ startup auto-reindex；🟡 第二梯队 = 高价值改进；🟢 第三梯队 = 至少两项 polish。
> **TDZ 警告**: Generator 实现时必须严格遵守 "变量声明必须在引用之前" + "useCallback 必须在其 useEffect 之前定义" 的规则。

### 第一梯队（🔴 战略基础设施 — 本轮必须完成）

- [x] R10-MCP-server: 构建 MCP server，将 Layer 0 认知原语暴露为 MCP 工具
  - 目标：构建一个 MCP server，将 CodeMemory 的五个 Layer 0 认知原语——resolve、overview、wander、focus、snapshot——作为可调用的 MCP 工具暴露。server 包装现有的 `handlers.py` 函数（与 CLI 使用相同的代码路径），因此 resolve/overview/wander 的 DAG 遍历逻辑是共享的而非重复的。MCP 工具保留 CodeMemory 的独特差异化：确定性依赖解析（非概率相似度）、基于显式 `imports` 的 DAG 遍历、以及带 token 预算裁剪级别的上下文组装。server 通过 `pyproject.toml` entry point 安装，可作为标准 MCP server 在 Claude Code、Cursor、Windsurf 等工具中配置使用。
  - 验收：MCP server 注册工具 `resolve_memory`（id, depth, budget）、`overview`（tags, min_maturity）、`wander`（mode）、`focus`（id, level）、`snapshot`（id）；每个工具委托 CLI 使用的同一 `handlers.py` 函数（无逻辑重复）；server 可通过标准 MCP JSON 配置 `{"codememory": {"command": "python", "args": ["-m", "codememory.mcp_server"]}}`；`pyproject.toml` 在 `[project.scripts]` 下包含 `"mcp-server"` entry point；`resolve_memory` 返回带裁剪级别标注和 token 计数的拓扑排序上下文；`overview` 返回 top 5 相关记忆摘要供注入 AI system prompt；`wander` 返回一条冷记忆含 access_count 和 last_access；server 通过 `CODEMEMORY_ROOT` 环境变量获取数据集路径；现有 CLI 和后端 API 继续不变；后端 57+24 测试通过
  - 来源：进化策略师 Important #5（从 Feature Idea 升级——2026 年 5 月所有新出记忆系统都 MCP-first，CodeMemory 的 DAG 解析引擎架构优于竞品但缺少 MCP 集成）

- [x] R10-auto-reindex: 后端启动时自动执行 reindex
  - 目标：在后端启动或首次加载数据集时触发完整 reindex，使 `stale_count` 和 `summary_hash` 值从第一个请求开始就是准确的。当前行为——显示 `stale_count: 10` 直到用户手动点击 Reindex 按钮——是一个破坏性的第一印象。reindex 逻辑是正确的（Iteration 9 修复了哈希计算），但工作流要求一个不必要的手动步骤。
  - 验收：后端启动后自动在 `_load_index()` 之后运行 `reindex()`；服务器启动后首次 `GET /api/stats` 返回 `stale_count: 0`（对所有 4 个数据集，假设没有实际 stale 记忆）；Dashboard 中的手动 Reindex 按钮仍可工作（且在自动 reindex 后是幂等的）；数据集切换（`POST /api/datasets/switch`）也对新选择的数据集触发自动 reindex；启动时间对 62 条记忆的 quant_operators 数据集增加不超过 500ms；现有 API 行为无退化；后端 57+24 测试通过
  - 来源：进化策略师 Critical #1（当前 stale count 在用户手动点击 Reindex 前是错误的——这是每轮会话的坏第一印象）

### 第二梯队（🟡 高价值改进 — 本轮尽量完成）

- [x] R10-loading-skeletons: 为 Graph 和 List 视图添加加载骨架屏
  - 目标：将现有的骨架屏模式（DashboardSkeleton 带 shimmer 动画）扩展到 Graph 和 List 视图。Graph 骨架应在居中布局中显示占位节点圆圈和连接线，替换 Cytoscape 初始化前短暂出现的空白画布。List 骨架应显示匹配表格列布局（ID、Summary、Type、Maturity、Tags、Status）的骨架行，宽度有变化以显得真实。
  - 验收：Graph 视图在 Cytoscape 初始化期间显示居中骨架含占位节点圆圈和连接线；List 视图在初始数据加载期间显示骨架行匹配表格布局（ID/Summary/Type/Maturity/Tags/Status 列）；两个骨架均使用现有 `skeleton-shimmer` CSS 动画（1.5s ease-in-out 渐变滑动）；数据到达后骨架被实际内容替换；数据加载失败时骨架被适当错误状态替换（非一直挂起）；已有缓存数据时不出现骨架（即时过渡）；图渲染、列表排序、过滤、分页无退化
  - 来源：体验官 Medium #4（Graph 加载骨架） + 进化策略师 Nice-to-have #18（List 和 Graph 骨架——目前仅 Dashboard 有骨架）

- [x] R10-error-queue: 将单条错误 banner 替换为排队 toast 系统
  - 目标：将当前的单条操作错误 banner 替换为堆叠 toast 队列。当前 `showOperationError()` 设置单个 `operationError` 状态字符串——如果第二条错误在第一条自动消失（6 秒）之前触发，第一条错误会静默丢失。修复应允许多条错误消息堆叠（最新的在底部），每条独立可关闭，每条有自己的自动消失计时器。视觉模式应遵循现有 toast 惯例（滑入动画，位于右下角或右上角）。
  - 验收：多条同时发生的操作错误各显示为独立 toast（最新的在底部）；每条 toast 有自己独立的 6 秒自动消失计时器；每条 toast 可通过 X 按钮独立关闭；toast 有滑入 + 淡入入场动画（与现有 Undo toast 200ms 模式一致）；所有 toast 关闭后 DOM 中无残留 toast 容器；网络错误 banner（顶部红色条）与操作 toast 保持分离（服务不同目的）；App.tsx、Dashboard.tsx 及其他组件中现有的 `showOperationError()` 调用点继续与新排队系统兼容
  - 来源：体验官 High #1（如果两个操作快速连续失败，只有第二个错误被显示——消息队列或非替换式 toast 模式会更加健壮）

- [x] R10-search-filter-fix: 支持无查询字符串的标签/类型/状态/成熟度过滤
  - 目标：修复 `POST /api/search` 端点使其在 `query` 为空时不短路。当前 server.py 约第 1055 行在 query 为空或仅含空白时立即返回 `{"results": [], "count": 0}`。这破坏了如"显示所有标签为 'investment' 的记忆"或"显示所有 proven 记忆"的使用场景——用户必须输入一个无意义的查询字符来绕过短路。修复应允许标签、类型、状态和成熟度过滤独立于查询文本工作，并应支持组合多个过滤维度。
  - 验收：`POST /api/search` 使用 `{"tags": ["investment"]}`（无 query）返回所有带该标签的记忆；`{"maturity": "proven"}` 返回所有 proven 记忆；`{"status": "archived"}` 返回所有归档记忆；`{"type": "schema"}` 返回所有 schema 记忆；组合过滤有效 `{"tags": ["ai"], "maturity": "verified"}` 返回交集；无过滤的空查询仍返回空结果（对真正空请求行为不变）；现有搜索行为（query + 过滤组合）不变；分页仍对仅过滤查询有效（offset/limit）；后端 57+24 测试通过
  - 来源：进化策略师 Critical #3（用户应该能够浏览"所有标签为 investment 的记忆"或"所有 proven 记忆"而无需输入查询字符串）

- [x] R10-dark-tints-widen: 扩展深色模式目录色彩调色板以提高扫视区分度
  - 目标：扩展 `colors.ts` 中的 `DIRECTORY_TINTS_DARK` 调色板，使深色模式目录颜色跨越更宽的亮度范围（约 `#1A`–`#4A` 而非当前的 `#2D`–`#3D` 簇）。对关键目录略微增加饱和度，同时保持深色美学。目标是保留语义标识（金色表示偏好，绿色表示信念，紫色表示人物），同时使颜色无需细读标签即可扫视区分。
  - 验收：深色模式目录色彩至少跨越 `#15`–`#4A` 亮度范围（按大致亮度测量）；每个目录的深色色彩保留其语义标识（偏好的暖金色、信念的绿色、人物的紫色等）；相邻色调无需仔细检查即可视觉区分；亮色模式目录颜色不变；动态 Legend 正确显示扩展后的深色调色板；主题切换正确更新图节点颜色；TypeScript 零错误，前端构建通过
  - 来源：体验官 High #2（深色色彩在狭窄范围内——大多数在 #2D 到 #3D 之间——因此区分需要注意力。略大的差距将提高扫视性）

- [x] R10-require-dataset-header: 要求 X-Codememory-Dataset 请求头，缺失时返回 400
  - 目标：使 `X-Codememory-Dataset` 请求头对所有 API 请求变为必需。当前，无请求头的请求静默默认为 "investment" 数据集。这是一个正确性陷阱：忘记请求头的新 API 消费者会获得无错误提示的错误数据。修复应在请求头缺失或为空时返回 400 Bad Request 并附清晰的错误消息，并应在帮助面板和 API 响应中记录请求头要求。
  - 验收：无 `X-Codememory-Dataset` 请求头的 API 请求返回 HTTP 400，消息如 "X-Codememory-Dataset header is required. Available datasets: companion, investment, software-architecture, quant_operators"；`GET /api/datasets` 端点无需请求头仍可访问（它是发现机制）；`GET /` 根端点无需请求头仍可访问（服务发现）；前端 `api.ts` 已对每个请求发送该请求头（Iteration 9 添加）——无需前端更改；帮助面板记录请求头要求；带有效请求头的现有 API 行为不变；后端 57+24 测试通过
  - 来源：体验官 High #3（并行请求依赖请求头规范。如果新 API 消费者忘记请求头，请求会静默默认为 "investment"——更健壮的方式是要求请求头并在缺失时返回 400）

### 第三梯队（🟢 打磨 — 本轮至少完成两项）

- [x] R10-search-prefix-match: 将搜索栏标签自动补全统一为前缀匹配
  - 目标：将 SearchBar 的标签自动补全匹配方式从 `includes`（任意位置子串匹配）改为 `startsWith`（前缀匹配），与 MemoryForm 的自动补全行为一致。当前，SearchBar 显示任何包含查询字符串的标签（如输入 "a" 匹配 "habit"、"math"、"career"），而 MemoryForm 使用 `startsWith` 获得更可预测的结果。将两者统一为 `startsWith` 使搜索自动补全可预测且一致。
  - 验收：SearchBar 标签自动补全仅显示以输入查询开头的标签（前缀匹配）；MemoryForm 标签自动补全继续使用前缀匹配（不变）；两处自动补全行为现在一致；标签建议仍出现在输入框下方的下拉菜单中；键盘导航（ArrowDown/ArrowUp/Enter/Escape）继续有效；标签列表仍来源于 `fetchStats()`（当前数据集实际使用的标签）
  - 来源：体验官 Medium #5（搜索栏使用 `includes` 进行标签匹配——显示任何包含查询的标签——而表单使用 `startsWith`。`startsWith` 对搜索来说更可预测。将两者统一为 `startsWith`）

- [x] R10-api-smoke-tests: 添加最少 5 个 API 冒烟测试（FastAPI TestClient）
  - 目标：使用 FastAPI 的 `TestClient` 添加 5 个覆盖最常用端点的 API 级冒烟测试。测试应验证基本正确性：`GET /api/memories` 返回分页结果，`GET /api/memories/{id}` 返回特定记忆，`POST /api/search` 返回匹配结果，`POST /api/resolve` 返回 DAG 解析上下文，`GET /api/stats` 返回聚合统计。这些是冒烟测试——验证 API 端到端与真实数据一起工作，而非穷尽测试每个边界情况。
  - 验收：`tests/test_api.py` 存在，至少包含 5 个使用 FastAPI `TestClient` 的测试函数；Test 1：`GET /api/memories` 返回结构正确的分页结果；Test 2：`GET /api/memories/{id}` 返回包含所有预期字段的特定记忆；Test 3：`POST /api/search` 带查询返回带匹配元数据的排名结果；Test 4：`POST /api/resolve` 带有效 ID 返回拓扑排序上下文；Test 5：`GET /api/stats` 返回 total_count、stale_count、maturity 分布、标签频次；测试基于真实 examples/ 数据（非 mock）使用 companion 数据集；测试可通过 `PYTHONPATH=src python -m pytest tests/test_api.py -v` 运行；现有 57+24 测试继续通过
  - 来源：进化策略师 Critical #4（零 API 测试意味着回归风险随每次端点变更而增加——Iteration 9 的 3 个关键 bug 本可以被基本 API 集成测试捕获）

## 第 11 轮追加任务（基于体验官 + 进化策略师 + 研究员审计 — 2026-05-06）

> **背景**: 体验官 7.0/10，发现 2 个 Critical UX bug（数据集切换竞态、模态叠加）和多项重要摩擦。进化策略师 4.5/10，核心完整性缺口巨大（导入 UI、语义搜索、空状态缺失）但多数为大型功能。研究员报告侧重长线架构方向。R10 eval.md 显示 18/18 PASSED，无回归。
> **策略**: 本轮聚焦于高影响、低投入的缺陷修复和体验打磨。大型功能（导入 UI、语义搜索）纳入 backlog 规划但不在本轮实现。研究员建议中仅采纳一个低投入项（MCP 工具注解）。
> **优先级**: 🔴 第一梯队 = 2 个 Critical bug + 3 个 Important UX fix；🟡 第二梯队 = 4 个重要改进；🟢 第三梯队 = 至少 3 项 polish。

### 第一梯队（🔴 Critical Bug 修复 + 关键 UX — 本轮必须完成）

- [x] R11-B1: 修复数据集切换时 List 和 Dashboard 视图数据不更新的竞态问题
  - 目标：切换数据集后，List 和 Dashboard 视图能正确显示新数据集的数据，而非旧数据集的缓存数据
  - 验收：在 List 视图切换 dataset 后记忆数量和 ID 列表更新为新数据集的数据（如切换到 quant_operators 后显示 "62 of 62" 而非 "10 of 10"）；在 Dashboard 视图切换后统计数据更新；多次快速切换数据集不出现数据混乱；Graph 视图切换行为不退化

- [x] R11-B2: 防止模态叠加
  - 目标：打开 Wander 或 Validate 模态时，若已有另一模态打开则自动关闭前者，确保同时仅显示一个模态
  - 验收：先打开 Wander 模态，再点击 Validate 按钮，Wander 模态自动关闭后 Validate 模态出现；反之亦然；两个模态的关闭逻辑互不干扰

- [x] R11-UX1: 修复 Ctrl+K 键盘快捷键失效
  - 目标：Ctrl+K 快捷键能正确聚焦到搜索输入框
  - 验收：按下 Ctrl+K 后光标出现在搜索输入框中；Help 面板中 Ctrl+K 描述与实际行为一致

- [x] R11-UX2: 为 REINDEX 操作添加完成反馈
  - 目标：Reindex 完成后显示成功 toast 或可见提示，而非静默刷新数据
  - 验收：点击 Reindex 按钮后，在操作完成时出现成功提示（如 "Reindexed N memories" toast）；失败时出现错误提示；提示在合理时间内自动消失

- [x] R11-UX3: 使搜索过滤 Graph 视图节点
  - 目标：在搜索栏输入文字并提交后，Graph 视图中的节点能根据搜索结果高亮或过滤显示
  - 验收：输入搜索关键词后非匹配节点变暗（dimmed）或隐藏；匹配节点保持高亮可见；清除搜索后所有节点恢复；搜索结果列表与 Graph 节点高亮同步（如搜索下拉结果 hover 时对应节点高亮）

### 第二梯队（🟡 高价值改进 — 本轮尽量完成）

- [x] R11-UX4: 为 Graph 视图添加加载骨架屏
  - 目标：Cytoscape 初始化期间显示骨架屏（占位节点圆圈 + 连接线），而非空白画布
  - 验收：切换到 Graph 视图时在 Cytoscape 渲染前显示骨架屏（含 placeholder 节点和边）；骨架使用现有 shimmer 动画；数据到达后骨架替换为真实图内容；已有缓存时不显示骨架

- [x] R11-UX5: 表单校验失败时禁用 CREATE 按钮
  - 目标：提交空表单或校验失败后 CREATE 按钮变为不可点击状态，防止重复提交
  - 验收：提交空表单显示校验错误后，CREATE 按钮变为 disabled 状态；修正所有校验错误后按钮恢复可点击；已有编辑表单的 SAVE 按钮行为一致

- [x] R11-UX6: 为 List 视图截断的摘要列添加 hover tooltip
  - 目标：鼠标悬浮在 List 视图摘要列被截断的文本上时，显示完整摘要内容的 tooltip
  - 验收：悬浮含省略号的摘要单元格时出现 tooltip 显示完整文本；摘要未截断时不显示 tooltip；tooltip 在合理延迟后出现（~300ms）

- [x] R11-UX7: 改进关键操作的错误消息用户体验
  - 目标：为网络错误和 CRUD 操作失败添加"Retry"按钮和人类可读的错误措辞，替代原始 HTTP 状态码文本
  - 验收：网络错误 banner 上出现 "Retry" 按钮，点击后重试上次失败的操作；错误消息使用人类可读语言（如 "Unable to connect to server" 而非 "500 Internal Server Error"）；关键 CRUD 失败时提供可操作指引（如 "Try again" 或 "Check your input"）

### 第三梯队（🟢 打磨 — 本轮至少完成三项）

- [x] R11-P1: 移除 header 中的 "Stats, validation, and reindex apply to the selected dataset" 声明文字
  - 目标：将这行 10px 斜体声明从 header 移除，改为 dataset 下拉框自身的 tooltip
  - 验收：Header 中不再显示该声明文字；dataset 下拉框或其附近有简短 tooltip 说明 dataset 范围

- [x] R11-P2: 移除 Dashboard stale 区域中重复的 memId 显示
  - 目标：Dashboard stale 记忆列表中每条记忆的 ID 仅显示一次（作为可点击标题），移除重复的 monospace 副标题
  - 验收：每条 stale 记忆仅显示一个 clickable ID；不再出现同一 ID 显示两次的情况

- [x] R11-P3: 添加搜索"无结果"空状态反馈
  - 目标：搜索查询返回零结果时显示用户可见提示（如 "No memories found matching 'xyz' — try different keywords"），而非下拉菜单静默消失
  - 验收：输入无匹配结果的查询后搜索下拉菜单出现，显示 "No results" 提示含可操作建议；清除查询后提示消失；有结果时正常显示结果列表

- [x] R11-P4: 为 MCP server 工具添加读写注解
  - 目标：在 MCP server 工具定义中将 `resolve_memory`、`overview`、`wander`、`focus` 标记为只读，`snapshot` 标记为写入操作
  - 验收：MCP tools/list 响应中每个工具包含 `readOnlyHint` 或等效注解；现有 MCP 工具调用行为不变；现有后端 57+24 测试通过

## 第 12 轮追加任务（基于体验官 + 进化策略师 + 研究员审计 — 2026-05-07）

> **背景**: 体验官评分 7.0/10，两个 Critical bug（模态竞态、列表 tooltip）和多项重要摩擦。进化策略师评分 5.5/10（从 4.5 上升），Critical 建议均为大功能（AI 创建、导入 UI、设置扩展），Important 中有低投入项（确认对话框、面板标准化、快捷键系统）。研究员 Red 级建议中 R4（MCP 注解）与 R11-P4 重叠，R1（时间衰减激活）为 20 行公式变更。R11 eval 12/13 PASSED，仅 R11-P4（MCP readOnlyHint）未完成。
> **策略**: 本轮聚焦于修复已知缺陷 + 完成 R11-P4 + 采纳体验官 2 个 Critical + 4 个 Important fix + 进化策略师 2 个低投入 Important 建议 + 研究员 R1。大型功能（导入 UI、AI 创建、设置扩展）纳入 backlog 不在本轮实现。
> **优先级**: 🔴 第一梯队 = R11-P4 carry-over + 2 个 Critical bug + 1 个 Critical UX bug；🟡 第二梯队 = 4 个 Important 改进 + 1 个进化策略师 Important + 1 个研究员 Red；🟢 第三梯队 = 至少 4 项 polish。

### 第一梯队（🔴 Critical 修复 — 本轮必须完成）

- [x] R12-B1: 修复 Validate 模态在 Wander 关闭后偶发性打不开的异步竞态问题
  - 目标：Wander 模态关闭 + 触发 validate 请求后，Validate 模态始终能可靠打开，不受异步 fetch 生命周期影响
  - 验收：多次重复"打开 Wander → 关闭 → 点击 Validate"操作，Validate 模态每次都出现；反之亦然（Validate → Wander）；两个模态的 close/open 逻辑完全独立无相互干扰
  - 来源：体验官 Critical #1（R11-B2 修复引入的新竞态——setWanderOpen(false) 和 fetchValidate() 同步调用但 setValidateOpen(true) 依赖 fetch promise 解析）

- [x] R12-B2: 修复 List 视图 TruncatedCell tooltip 不显示（R11 回归）
  - 目标：List 视图截断的 Summary 列在 hover 时正确显示包含完整文本的 tooltip
  - 验收：含省略号的长文本单元格 hover 后出现 tooltip 显示完整内容；未截断的单元格不显示 tooltip；中文混合文本截断检测同样准确；tooltip 内容与单元格实际完整内容一致
  - 来源：体验官 Critical #2（父元素 `<td>` 的 `overflow: hidden` 阻止了 `scrollWidth > clientWidth` DOM 检测——R11-UX6 在特定条件下失效）

- [x] R12-B3: 清除用户修正输入后的表单校验错误
  - 目标：用户在表单中修正了触发校验错误的字段后，错误 banner 自动消失，无需等待下次提交
  - 验收：提交空表单后显示的 "ID is required" 错误在用户输入有效 ID 后自动消失；按钮状态（disabled/enabled）与错误存在状态一致；任何字段修正后对应错误消失；错误消失后恢复时无闪烁
  - 来源：体验官 Important #7（错误 banner persist 让用户困惑——认为错误仍在）

- [x] R12-B4: 完成 R11-P4 — MCP server 工具 readOnlyHint 注解（上轮遗留）
  - 目标：在 MCP server 的 5 个工具定义中添加 readOnlyHint 属性（resolve/overview/wander/focus 为只读，snapshot 为写入）
  - 验收：MCP tools/list 响应中每个工具包含 readOnlyHint 或等效注解；现有 MCP 工具调用行为不变；现有后端 57+24 测试通过
  - 来源：上轮遗留 + 进化策略师 I9 + 研究员 R4（三方一致认定）

### 第二梯队（🟡 高价值改进 — 本轮尽量完成）

- [x] R12-UX1: 提升全局最小交互字号从 10-11px 到 12-13px
  - 目标：所有按钮、标签、badge 和控制文字的最小字号提升至 12px；微标签（match quality badge、tag count）可保持 11px 但不低于此
  - 验收：所有视图（Graph/List/Dashboard/Detail/Form/Modal/Onboarding）中交互文字字号 >= 12px；微标签 >= 11px；布局不因字号增加而破损；深色模式同样适用；色彩和间距与现有设计系统一致
  - 来源：体验官 Important #3（"the single highest-impact aesthetic change available" — 10-11px 在高 DPI 屏幕下低于可读阈值）

- [x] R12-UX2: 为 Settings、Help、MemoryForm 面板和 Wander/Validate 模态添加入场/退场动画
  - 目标：所有滑出面板使用与 MemoryDetail 相同的动画模式（transform 平移 + 250ms ease）；所有模态使用 fade-in + scale 过渡
  - 验收：Settings 面板从右侧滑入（250ms ease）；Help 面板从右侧滑入；MemoryForm 面板从右侧滑入；Wander 模态 fade-in + scale 入场；Validate 模态同样入场动画；所有退场动画正确执行（无瞬间消失）；动画统一性——所有同类型面板/模态使用相同时长和缓动函数
  - 来源：体验官 Important #4 + #5（"the fact that Settings/Help/MemoryForm panels lack identical animations is an oversight"；"Motion is how digital products communicate materiality"）

- [x] R12-UX3: 为 Validate 模态添加 "Validate Again" 按钮
  - 目标：Validate 模态内提供重新运行 validate 的按钮，匹配 Wander 模态的 "Wander Again" 体验
  - 验收：Validate 模态内出现 "Validate Again" 按钮（或等效操作入口）；点击后重新运行 validate 并更新模态内容；按钮位置和样式与 Wander 的 "Wander Again" 一致；按钮在 validate 运行期间有加载态反馈
  - 来源：体验官 Important #6（"Wander has 'Wander Again' — this asymmetry is confusing"）

- [x] R12-UX4: 为归档操作添加确认对话框
  - 目标：点击归档按钮时弹出确认对话框；若被归档的记忆被其他记忆 imports 引用，额外显示警告告知会创建断链
  - 验收：归档操作触发确认对话框（"Are you sure?" + 说明归档操作可逆）；若记忆被 N 条其他记忆引用，对话框中显示 "N memories import this one. Archiving it will create broken links." 及引用者 ID 列表；确认后执行归档；取消则关闭对话框无操作；确认对话框样式与现有设计系统一致（Escape 可关闭）
  - 来源：进化策略师 C5（"Prevents data loss. Standard UX pattern absent from the product."）

- [x] R12-UX5: 为 overview 添加时间衰减激活计算
  - 目标：将 `overview` 的 heat 计算公式从 `deps * 10 + access` 替换为时间衰减逻辑，使 session-start 上下文注入更能反映记忆的"最近相关性"而非简单访问频次
  - 验收：最近常访问的记忆 heat 值高于很久以前高频访问的记忆；overview 输出排序按新公式正确排列；时间衰减逻辑对 zero-access 记忆（从未访问过）优雅降级；现有 overview 输出格式和字段不变；57+24 测试通过
  - 来源：研究员 R1（Red / High-Impact Low-Effort — "约 20 行公式变更，能显著改善 session-start 质量"）

### 第三梯队（🟢 打磨 — 本轮至少完成四项）

- [x] R12-P1: 替换 onboarding 文字图标为 SVG 几何图标
  - 目标：5 步 onboarding overlay 中的原始文字字符（"+"、"o"、">"、"~"、"checkmark"）替换为一致的 SVG 几何图标集
  - 验收：每步 onboarding icon 为 SVG 图形（圆形表示 graph、箭头表示 resolve、加号表示 create、对勾表示完成、星形表示欢迎）；图标风格一致（线描或实心，非混合）；图标颜色与 gold accent 协调
  - 来源：体验官 Nice-to-have #8（"the most visible design element in the first 30 seconds uses placeholder symbols"）

- [x] R12-P2: 统一三个视图的空状态组件
  - 目标：Graph、List、Dashboard 三个视图在零记忆和零过滤结果场景下使用统一的 EmptyState 组件，包含一致的图标、文案和操作按钮
  - 验收：Graph 空状态含统一 EmptyState + "Create Memory" 按钮；List 空状态含统一 EmptyState + 情境化消息；Dashboard 空状态含统一 EmptyState + "Create Memory" 按钮；所有空状态的视觉风格（图标、排版、间距）一致；零记忆 vs 零过滤结果通过不同文案/图标区分
  - 来源：体验官 Nice-to-have #9（"Three different empty state UIs for the same condition"）

- [x] R12-P3: 统一操作标签 —— "Create Memory" / "+ New" / "+ NEW" → 单一主操作标签
  - 目标：全应用中使用一致的主操作标签文字和视觉样式
  - 验收：创建记忆操作在所有位置使用统一的文案（如 "Create Memory" 或 "+ New"——选一统一）；"+ NEW" 按钮与视图切换器在视觉上可区分（主操作 vs 导航）；操作按钮颜色/样式一致传达"创建"语义
  - 来源：体验官 Nice-to-have #9 补充（"Four different labels for the same action"）

- [x] R12-P4: 添加视图切换键盘快捷键（1/2/3）
  - 目标：按 1/2/3 键可在 Graph/List/Dashboard 视图之间切换；Help 面板记录这些快捷键
  - 验收：按 "1" 切换到 Graph 视图；按 "2" 切换到 List 视图；按 "3" 切换到 Dashboard 视图；当搜索框或表单输入框聚焦时不触发视图切换；Help 面板中快捷键列表包含 1/2/3 的说明
  - 来源：体验官 Nice-to-have #12 + 进化策略师 I3（"No keyboard shortcut for view switching... natural"）

- [x] R12-P5: 为 List 视图表格行添加 hover 效果
  - 目标：List 视图表格行在鼠标悬浮时有微妙的背景色过渡
  - 验收：悬浮表行时背景色在 ~100ms 内平滑过渡到稍深的色值（亮色和深色模式均适用）；已选中的行（如有）与 hover 行视觉可区分；hover 效果与 Dashboard tag cloud 和 search results 的交互风格一致；行 hover 不影响列排序功能
  - 来源：体验官 Nice-to-have #13（"lacks the subtle background-color shift present in other views"）

- [x] R12-P6: 为 List 视图添加容器横向 padding
  - 目标：List 视图表格不再拉伸到容器边缘，获得与 Dashboard 一致的横向 padding
  - 验收：List 视图表格有可见的横向 padding（不贴边）；padding 值与 Dashboard 视图一致或视觉协调；表格内容不被 padding 裁切（columns 宽度自适应）；深色模式下 padding 区域颜色与背景一致
  - 来源：体验官 Phase 2.3（"the List view table stretches edge-to-edge... feels squeezed and spreadsheet-like"）

### Backlog（本轮不纳入，下轮评估）

以下建议由 Planner 审阅后记录为 backlog，待后续轮次根据优先级和容量评估纳入：

- **数据导入 UI**（进化策略师 C2）—— #1 冷启动障碍，但属大型功能，需独立轮次
- **AI 辅助创建**（进化策略师 C1）—— 差异化战略资产，但需依赖 llm_gateway 集成，属大型功能
- **设置面板扩展**（进化策略师 C3）—— 从 3 项扩展到 15-20 项，中等规模但本轮聚焦缺陷修复
- **交互式 Onboarding**（进化策略师 C4）—— 被动教程升级为交互式引导，中等规模
- **Suggest-Deps 在创建表单中**（进化策略师 I1）—— 高价值低投入，但本轮任务已满
- **命令面板 Ctrl+P**（进化策略师 I2）—— 桥接 CLI/UI，下轮评估
- **图结构过滤器**（进化策略师 I6）—— 按 type/status/maturity/directory 过滤图节点
- **草稿自动保存**（进化策略师 I5）—— localStorage 持久化，已多次提及
- **Markdown 预览**（体验官 Nice-to-have #14）—— 编辑体验改进
- **移除 List 本地过滤条**（体验官 Nice-to-have #10）—— 搜索接口统一
- **图节点右键菜单添加 Resolve**（体验官 Nice-to-have #11）—— 减少 "aha moment" 点击路径
- **imports 字段添加语义类型**（研究员 R2）—— 支持/反驳/扩展/替换/例证
- **预计算 in_degree / out_degree**（研究员 R3）—— 消除 O(n^2) 瓶颈
- **图 Minimap**（进化策略师 I10）—— Cytoscape 原生支持
- **Schema purple 和 info blue 暖化**（体验官 Nice-to-have #22）—— 调色板和谐调整
- **SVG 图标集**（体验官 Nice-to-have #21）—— 替换所有 Unicode/emoji 图标

---

## 第 13 轮追加任务

> **日期**：2026-05-07
> **上轮评估**：Round 12 — 15/15 PASS，零回归（86/86 测试），首次零 Critical 缺陷
> **主题**：产品品质打磨 — 完成未竟的审美项、缩短发现路径、统一衰减模型
> **筛选原则**：修复成本低（不超过 50 行变更）+ 用户感知价值高

### 第一梯队：审美完成

- [x] R13-A1: 退场动画接线
  - 目标：面板关闭和模态关闭时播放退场动画（slide-out / fade-out），而非立即从 DOM 消失；创建通用的动画包装机制，一次实现覆盖所有 7 个面板/模态入口
  - 验收：关闭 Settings 面板时可见 slide-out 动画（而非瞬间消失）；关闭 MemoryDetail 面板同理；关闭 Wander/Validate/Archive 模态时可见 fade-out + scale-down 动画；动画时长与入场一致（250ms ease）；退场动画播放期间不可与已关闭的组件交互；Escape 键触发的关闭同样播放退场动画
  - 来源：体验官 Important #1（"Entrance animations — IMPLEMENTED. Exit animations — NOT IMPLEMENTED. The CSS exists but is dead code."）

- [x] R13-A2: 修复残余 sub-12px 字号
  - 目标：详情面板 StatusBadge 和 MaturityBadge 的 fontSize 从 11px 提升到 12px（与 List 视图一致）；搜索栏 "fuzzy matches" 指示器从 9px 提升到 11px；搜索栏 match quality badge 从 9px 提升到 11px
  - 验收：MemoryDetail 面板中 StatusBadge 和 MaturityBadge 的渲染字号 >= 12px；SearchBar 下拉结果中 "includes fuzzy matches" 文字 >= 11px；SearchBar 下拉结果中 MATCH 标签（EXACT/FUZZY）>= 11px；深色模式下微标签可读；布局不破损
  - 来源：体验官 Important #2（"The remaining stragglers are concentrated in three specific areas... Each can be fixed with a single-line change."）

- [x] R13-A3: 搜索下拉框 fade-in 动画
  - 目标：全局搜索下拉框出现时播放 150ms fade-in 动画，与面板/模态动画语言一致
  - 验收：点击搜索框或输入文字时下拉框 fade-in（150ms ease）；动画模式与面板/模态入场一致（opacity 过渡）；深色模式适用
  - 来源：体验官 Nice-to-have #5（"A 150ms fade-in on the dropdown appearing, matching the modal/panel animation language."）

### 第二梯队：发现路径缩短

- [x] R13-D1: 搜索结果添加 "Resolve →" 动作
  - 目标：全局搜索下拉框中每条结果条目旁显示 "Resolve →" 链接或按钮；点击后关闭搜索下拉框、切换到 Graph 视图、自动对该记忆触发 resolve（使用默认 depth 和 budget）
  - 验收：每条搜索结果旁有可见的 "Resolve →" 按钮或链接；点击后搜索下拉框关闭；视图切换到 Graph 且图已挂载后 resolve 自动触发；resolve 结果在 MemoryDetail 面板或 resolve 区域中展示；如果已经在 Graph 视图则无需切换，直接触发 resolve；快捷键或键盘导航不冲突
  - 来源：体验官 Important #3（"Turns the aha moment from 4 clicks to 2 clicks from the most-used interface."）

- [x] R13-D2: 视图切换按钮添加快捷键提示
  - 目标：Graph/List/Dashboard 视图切换按钮标签旁显示对应小号快捷键提示（"1" / "2" / "3"），让用户自然发现快捷键
  - 验收：Graph 按钮旁有 "1" 提示（小号、上标或 muted 颜色）；List 按钮旁有 "2" 提示；Dashboard 按钮旁有 "3" 提示；提示在亮色和深色模式下均可读但不喧宾夺主；Help 面板中快捷键条目保持一致
  - 来源：体验官 Important #4（"Users discover the shortcuts organically rather than needing to press '?' or read the Help panel."）

- [x] R13-D3: Resolve 加载状态
  - 目标：点击 Resolve 按钮后，在 resolve 结果区域展示加载骨架或旋转指示器（而非 UI 冻结无反馈），直到 API 响应返回
  - 验收：点击 Resolve 后 resolve 结果区域立即出现加载骨架或 spinner；加载指示器在深色模式下可见；API 返回后加载指示器消失，结果正常显示；API 错误时加载指示器消失，错误信息展示（已有 error banner 行为不变）
  - 来源：进化策略师 Critical #C3（"Clicking Resolve freezes the UI for 1-3 seconds with zero user feedback. A loading spinner or skeleton... is table-stakes UX."）

### 第三梯队：衰减模型统一

- [x] R13-M1: 统一 overview/wander/validate 的衰减模型
  - 目标：用同一套连续衰减公式替换当前三套并行逻辑——overview 的 `0.5^(days/14)` 保持不变（作为标准公式）；wander(cool) 的权重从原始 `1/(access_count+1)` 改为基于衰减公式（低检索概率 = 高冷却权重）；validate 的 `_check_decay()` 从硬编码 30 天二元阈值改为连续可配置的检索概率阈值（如 R < 0.1 触发警告）
  - 验收：overview heat 评分行为不变（标准公式保持）；wander(cool) 现在对"很久以前被多次访问的记忆"给予合理的冷却权重（之前它们被错误地排除）；validate 衰减警告基于同一连续公式而非硬编码 30 天；57+24 测试无回归
  - 来源：研究员 High-Impact #1（"Three different decay models in one system. Replace the hard 30-day threshold... with the same formula used in overview."）

- [x] R13-M2: 排除循环参与者从 dependents 计数
  - 目标：在计算 heat 公式的结构性分量（"deps * 10"）时，跳过检测到的循环参与者——不可解析的循环不应贡献误导性的高 dependents 计数
  - 验收：3 节点循环 A→B→C→A 中每个节点的 dependents 有效计数为 0（循环成员被排除）；非循环的合法 imports 计数不受影响；无循环的正常 DAG 行为不变；57+24 测试无回归
  - 来源：研究员 High-Impact #2（"A 3-node cycle gives each node dependents=1... But these are structurally broken... Dependents count should exclude cycle participants."）

- [x] R13-M3: index 中预计算 days_since_last_access
  - 目标：在 MemoryEntry 索引中添加一个整数 `days_since_last_access` 字段；reindex 时计算一次；每次 access 时更新；在 overview heat 循环中用该整数字段替代 `datetime.fromisoformat`
  - 验收：index.json 中每条记忆条目包含 `days_since_last_access` 整数字段；overview heat 计算使用该预计算值而非实时解析 last_access 字符串；未被访问过的记忆有合理的默认值；57+24 测试无回归
  - 来源：研究员 High-Impact #3（"Avoids the most expensive operation in the overview O(n) loop — datetime.fromisoformat per memory."）

- [x] R13-M4: 添加 stability 字段（默认 14.0）
  - 目标：在 MemoryEntry 数据模型上新增 `stability: float = 14.0` 字段——per-memory half-life 天数；heat 公式从 `0.5^(days / 14.0)` 改为 `0.5^(days / stability)`；所有记忆初始值 14.0（向后兼容，行为不变）
  - 验收：MemoryEntry 模型包含 stability 字段，默认值 14.0；旧 index.json 中无 stability 字段的记忆加载后自动获取 14.0；reindex 后新生成的 index.json 包含 stability 字段；overview heat 公式使用 stability 替代硬编码 14.0；57+24 测试无回归
  - 来源：研究员 High-Impact #4（"This single field enables per-memory half-life without changing the core formula... Initially all 14.0."）

### 第四梯队：基础设施

- [x] R13-I1: 启用 OpenAPI /docs 端点
  - 目标：FastAPI 自带的交互式 Swagger UI 文档端点 `/docs` 当前未暴露——通过配置开启，为后端 API 提供自文档化的交互式文档
  - 验收：浏览器访问 `http://localhost:8000/docs` 返回 Swagger UI 页面；页面列出所有 API 端点及其参数和响应格式；"Try it out" 功能可用；`/docs` 的启用不影响现有端点行为；所有端点回归测试通过
  - 来源：进化策略师 Critical #C2（"FastAPI auto-generates interactive Swagger UI documentation... Enabling it costs zero code changes and immediately makes the API self-documenting."）

---

### 本轮延期项目（下轮评估）

- **全文正文搜索**（进化策略师 C1/C4）—— 最大功能缺口，需搜索管道变更 + 前端双向接线，留给搜索聚焦轮次
- **多级撤销栈**（进化策略师 I1）—— 组件状态管理重构，超出本轮单体任务上限
- **交互式 onboarding demo**（进化策略师 I5）—— 需内嵌可交互 Cytoscape 实例
- **版本 diff 查看器**（进化策略师 I2）—— 需新建前端组件 + diff 算法集成
- **图键盘导航**（进化策略师 I3）—— 需 Cytoscape 事件绑定 + focus 管理
- **Playwright 冒烟测试**（进化策略师 I6）—— 需新 dev 依赖，首次配置成本不可忽略
- **视图切换过渡**（体验官 Nice-to-have #6）—— 等 A1 退场动画机制稳定后复用
- **图节点 hover 微动画**（体验官 Nice-to-have #7）—— Canvas 动画模式与 DOM 不同
- **FSRS 完整稳定性更新**（研究员 High-Effort #6）—— 需 schema 迁移 + per-access 数学更新，依赖 M4 先落地
- **记忆层级可视化**（研究员 High-Effort #7）—— 前端 100+ 行 + 后端 30 行，依赖 FSRS 先落地

### 本轮拒绝项目（需架构变更或新依赖）

- **CSS 设计 token 系统**（进化策略师 I4）—— 覆盖 14 个组件的架构级重构
- **扩散激活引擎**（研究员 High-Effort #5）—— 需先明确上下文模型设计
- **移除 List 本地过滤条**（体验官 Nice-to-have #8）—— 需全局搜索接口功能扩展
- **Markdown 预览**（体验官 Nice-to-have #9）—— 需新建 UI 组件

### 长期 Backlog 新增

- 协作 resolve / WebSocket（全新基础设施）
- MCP 写入工具（新 MCP tool 设计 + 安全边界）
- VS Code 扩展（独立产品）
- 自动归档 + 精华蒸馏（依赖 LLM gateway）
- 周度记忆摘要（依赖 LLM gateway + 调度）
- 图原生存储后端（架构变更，Phase 3）
- 记忆编译器隐喻（定位/营销层）
- 多选 + 批量操作 / 保存过滤视图 / 快速捕获 API / Tabbed 检查 / 子图提取 / 快捷键速查表 / Git 集成指南（进化策略师 Nice-to-have N1-N7）
- DAG-Aware 编辑 / 记忆提醒 / 图 Diff / 设置面板扩展 / 命令面板（体验官 Feature Ideas #10-#14）
- 扩散激活 / 记忆层级可视化 / 降级成熟度路径 / memory compiler / episodic-to-semantic mining（研究员 #5-#10）


## 第 14 轮追加任务

> **日期**：2026-05-07
> **上轮评估**：Round 13 — 10/11 FULL PASS + 1 PARTIAL PASS (R13-A1 模态退场动画)，86/86 测试通过，零回归。但研究员发现 CRITICAL bug：统一衰减公式从未在 overview 路径中激活。
> **主题**：Bug 修复与完工 — 修复 Critical 数据管道 bug、完成 R13 遗留工作、添加安全防护
> **筛选原则**：核心指令："修复、完工、防护。不建新功能。"所有大型功能（Playwright 测试、FSRS 自适应稳定性、全文搜索、可写 MCP 工具）延期至 R15+。

### 第一梯队：Critical — 修复阻塞正确性的 Bug

- [x] R14-C1: 修复 overview 衰减公式管道 bug
  - 目标：`handle_overview()` 从 search 结果字典而非 MemoryEntry 对象读取 `days_since_last_access`——但 `search()` 不在输出中包含此字段。统一衰减公式 `0.5^(days/stability)` 从未在 overview 路径中激活——所有被访问过的记忆回退到 R13 之前的 `access * 0.1` 常量乘数。修复：确保 overview 从 MemoryEntry 对象读取数据；同时在 search 输出字典中添加 `days_since_last_access` 和 `stability` 字段以永久闭合该缺口。
  - 验收：对有非零 `days_since_last_access` 的记忆运行 `codememory overview`——热力值与 R13 eval 报告中记录的旧公式输出不同（衰减已激活）；search 命令输出包含 `days_since_last_access` 和 `stability` 字段；wander 和 validate 的衰减行为不变（它们未受影响，已从正确来源读取）；86/86 现有测试通过 + 新增 1 个测试验证衰减公式激活
  - 来源：研究员 Critical R-RED-1（"handle_overview() reads days_since_last_access from search result dict... decay formula never activates in the overview path... the eval heat values passed because they match the old formula, not the new formula."）

- [x] R14-C2: 添加 stability 边界防护
  - 目标：(a) `stability=0` 导致 `ZeroDivisionError` 崩溃——在 `MemoryEntry.stability` 上添加 Pydantic `@field_validator(gt=0)`（建议最小 0.1 天 = 2.4 小时）；(b) `stability<0` 产生 `decay>1.0` 无意义输出——由 gt=0 验证器拦截；(c) `days_since_last_access=None` 语义在 overview（意外回退到旧公式）和 wander（有意的最大冷却权重）之间不一致——在三个衰减消费点（overview、wander、validate）中定义明确的合约并统一 None 处理。本轮不改变行为——仅统一处理并文档化。
  - 验收：设置 `stability=0` 在 Pydantic 验证时被拒绝（不崩溃）；设置 `stability=-1` 被拒绝；`days_since_last_access=None` 的记忆在 overview、wander、validate 中收到一致的衰减处理；`stability=14.0`（默认）行为不变；86/86 现有测试通过
  - 来源：研究员 Critical R-RED-2 + R-RED-3（"stability=0 crash vector waiting for a user to set it... None vs 0 semantics diverge between overview and wander"）

- [x] R14-C3: 在 API 响应中暴露衰减字段
  - 目标：在 search 输出字典中添加 `stability` 和 `days_since_last_access` 字段；在 `/api/memories` 响应中扩展字段集合以包含 `access_count`、`last_access`、`days_since_last_access`、`stability`（当前硬编码为排除这些字段的 10 字段子集）；在 `/api/stats` 中添加 `decay_risk` 数组——`R < 0.1` 阈值的记忆列表（使用统一衰减公式）。R13 的衰减模型完全是服务器端且对前端/API 消费者不可见。
  - 验收：`/api/memories` 响应中每条记忆条目包含 `access_count`、`last_access`、`days_since_last_access`、`stability` 字段；`/api/stats` 响应包含 `decay_risk` 数组（记忆 ID + 衰减值）；search API 输出包含 `stability` 和 `days_since_last_access`；前端类型定义同步更新以匹配新的响应形状（无 TypeScript 错误）；现有 API 测试通过
  - 来源：体验官 Yellow #4 + 研究员 R-RED-4（"The decay model exists but is invisible... The /api/memories response shape is hard-coded to a 10-field subset"）

### 第二梯队：Important — 完成 R13 未竟的承诺

- [x] R14-I1: 接线模态退场动画
  - 目标：将 `useExitAnimation` hook 导入 Dashboard.tsx 的 `Modal()` 内联函数、App.tsx 中的 Archive 确认模态、以及 HelpPanel 组件。在关闭时应用 `modal-fade-exit` / `backdrop-fade-exit` CSS 类（已存在于 index.css 中，但目前为死代码——从未被任何组件引用）。`useExitAnimation` hook 已在 MemoryDetail/Settings/MemoryForm 三个面板上证明可用；Modal 函数需要重构以接收 closing 状态或内部集成 hook。
  - 验收：关闭 Wander 模态时可见 250ms fade-out + scale-down 退场动画（非立即 DOM 消失）；关闭 Validate 模态同理；关闭 Archive 确认模态同理；关闭 HelpPanel 时可见 slide-out 退场动画；遮罩背景与模态内容同步退场；Escape 键触发的关闭同样播放退场动画；退场动画播放期间不可与正在关闭的组件交互
  - 来源：体验官 Critical #1 + 进化策略师 C2 + EVAL R13-A1 PARTIAL PASS（"The CSS infrastructure is complete; only component wiring is missing. This is a half-day fix."）

- [x] R14-I2: 修复所有 sub-12px 字体（含 Search Resolve 按钮）
  - 目标：提升所有 7 处残留 sub-12px 元素：(1) HelpPanel 键帽标签 9px→11px；(2) HelpPanel 快捷键描述文本 9px→11px；(3) MemoryDetail "No additional context" 文本 9px→11px；(4) SearchBar Resolve 按钮 10px→12px + padding 1px 8px → 3px 12px；(5) 视图快捷键提示（"1"/"2"/"3"）10px→11px（装饰性，维持低显著性）；(6) SearchBar 搜索片段文本 11px→12px；(7) Undo toast 详情文本 11px→12px（等宽字体，可在视觉上保持较小）。R13-A2 在 EVAL 中被标记为 PASS，但体验官的逐像素审查发现了 7 个残留项——其中 3 个为 9px（不可读）。
  - 验收：UI 中无元素 `fontSize < 11px`（无 9px 或 10px 文本）；无交互元素（按钮、链接、可点击文本）`fontSize < 12px`；Search Resolve 按钮在 12px 且 padding 3px 12px 下可读且可点击；HelpPanel 快捷键参考表在正常观看距离下可读；深色模式适用；布局不破损；TypeScript 构建零错误
  - 来源：体验官 Critical #2 + #3（"The remaining stragglers at 9px... are worse than nothing — they suggest quality was checked in some files but not others. The Search Resolve button at 10px ships a new feature at a deprecated size."）

### 第三梯队：Nice to Have — 小范围高价值改进（容量允许）

- [x] R14-N1: 在 Dashboard 中暴露衰减风险
  - 目标：在 Dashboard 统计部分添加"衰减风险"卡片：显示 `R < 0.1`（低于衰减阈值）的记忆数量、距离阈值最近的 top 3 记忆（ID + 检索概率 R）。这是让 R13 衰减模型对用户可见的最小前端改动——仅展示数量，不需要图表或完整列表。复用现有统计卡片组件模式。
  - 验收：Dashboard 在现有统计卡片旁或下方显示衰减风险区域；显示有衰减风险的记忆数量（"3 memories at decay risk"）；列出距离阈值最近的 3 条记忆及其 R 值；数据来自 `/api/stats` 的 `decay_risk` 字段（R14-C3）；亮色和深色模式适用；加载状态适配（stats 加载时显示骨架）
  - 来源：进化策略师 I5 + 体验官 Proposal 1 最小可行版（"Top 5 memories closest to decay threshold... transforms Dashboard from passive stats to active knowledge maintenance."）

- [x] R14-N2: 图节点右键菜单添加 Resolve
  - 目标：在 GraphCanvas 图节点右键菜单中添加"Resolve"选项。点击后打开 MemoryDetail 面板并自动对该节点触发 resolve（使用默认 depth 和 budget）。图视图目前完全无 Resolve 流程路径——用户必须离开图视图切换到 List 或 Search 才能解析。
  - 验收：右键点击图节点时，右键菜单包含"Resolve"选项（与现有的"Edit"和"Delete"并列）；点击"Resolve"后 MemoryDetail 面板打开并显示该记忆的解析上下文；resolve 加载期间显示骨架动画（复用 R13-D3）；在 Graph 视图中保持上下文——不引起视图切换
  - 来源：体验官 Yellow #5（"The graph view has no path to the Resolve flow. A user looking at a node in the graph must navigate to List view or Search to resolve it."）

- [ ] R14-N3: 移除 List 视图本地过滤条
  - 目标：从 MemoryList.tsx 中移除重复的本地过滤 UI（按 type/status/maturity/tags/text query 过滤）。本地过滤条 80% 与全局 SearchBar 功能重叠但产生不同结果——客户端子串匹配 vs 服务器端模糊匹配。这种重复让用户困惑并占用约 40px 的垂直屏幕空间。
  - 验收：List 视图不再显示本地过滤条 UI；全局 SearchBar 仍可正常过滤记忆（通过后端搜索 API）；List 视图的垂直空间增加（无 40px 过滤条开销）；记忆列表正常显示未经过滤的全部记忆；移除不破坏列排序功能
  - 来源：体验官 Green #8（"Two filter UIs with overlapping behavior create user confusion about which one to use. The local filter gives different results than SearchBar."）

---

### 本轮延期项目（下轮评估）

- **全文正文搜索**（进化策略师 C1/C4）—— 最大功能缺口，需搜索管道变更 + 前端接线，留给搜索聚焦轮次
- **Playwright 冒烟测试**（进化策略师 C3）—— **约束性承诺：R15 首个任务，在任何新功能代码之前**。连续第三次延期（R12/R13/R14），若 R15 首日未交付应升级为 Critical blocker
- **FSRS 自适应稳定性更新**（研究员 R-GRN-1）—— 依赖 R14 C1-C2 先使衰减公式正确运行
- **可写 MCP 工具**（进化策略师 I1）—— 闭合 agentic 闭环，约 150 LOC，需安全边界设计
- **衰减热力图 Dashboard 完整版**（体验官 Proposal 1）—— 依赖 R14 C1+C3 先完成，R15 自然议程
- **交互式 onboarding / "Demo Resolve" 按钮**（进化策略师 I3）—— 约 50 LOC + 3 个 .md 文件，R15 评估
- **时间快照对比**（体验官 Proposal 3）—— 3-4 天，需新建前端组件 + diff 算法
- **图漫步模式**（体验官 Proposal 4）—— 3 天，大规模 D3/Cytoscape 动画工作
- **多级撤销栈**（进化策略师 I6）—— 跨组件状态管理重构
- **Per-memory 稳定性 UI**（进化策略师 I2）—— 衰减模型正确后的 R15 自然下一步
- **每种记忆类型的衰减曲线**（研究员 R-GRN-3）—— 研究级，需新字段 + 5 种数学函数
- **扩散激活引擎**（研究员 R-BOMB-1）—— 需上下文模型 + DAG 遍历，大型设计密集任务

### 本轮拒绝项目（修复轮次不引入新架构或依赖）

- **Playwright**（新 dev 依赖 ~200MB）—— 延期至 R15（约束性承诺）
- **CSS 设计 token 系统**（架构级重构，覆盖 14 个组件）
- **语义/嵌入搜索**（新管道，数月非数天）
- **图键盘导航**（Cytoscape 事件绑定 + focus 管理，涉及面广）
- **Markdown 预览**（需新建 UI 组件）

### 新增陷阱（本轮结束后追加至 pitfalls.md）

- **[R14-C1] 修复 overview 管道 bug 将改变热力值输出。** 对于任何有 `days_since_last_access > 0` 的记忆，修复后将产生不同于 R13 eval 报告中记录的热力值。这是预期行为——旧值是基于错误公式计算得出的。验证时需要将新热力值与手算的 `0.5^(days/stability)` 对比，而非与 R13 eval 对比。

- **[R14-I1] 内联 Modal 函数无法复用 useExitAnimation hook 详见 R13 审计。** Dashboard.tsx 中的 `Modal({ children, onClose })` 是本地纯函数组件——需要重构以接收 `closing` prop 或内部集成 `useExitAnimation`。参见 EVAL.md 第 8 节陷阱文档。

- **[R14-C2] stability 的 gt=0 验证器可能拒绝已有数据。** 如果任何现有数据集包含 `stability=0`（当前没有），Pydantic 验证器将在加载时拒绝。在添加验证器之前验证所有 4 个数据集（companion、investment、software-architecture、quant_operators）均具有 `stability=14.0`。

- **[R14-C3] /api/memories 响应形状变更需要前端类型同步。** 当前响应形状在 server.py 中硬编码为一个 10 字段子集。添加 4 个新字段需要同步更新前端 TypeScript 接口定义。遗漏此项将导致 TypeScript 类型错误。

### 长期 Backlog 新增（本轮审计中识别的新项目）

- **衰减即功能（Forgetting-as-feature）**：在 Dashboard 中展示"你即将遗忘的内容"——R 值接近衰减警告阈值（0.1-0.2）的记忆。"救援队列"将衰减模型从后端机制转化为主动 UX 功能。概念新颖性：无已知 PKM 工具将遗忘作为用户可见功能。（研究员 R-BOMB-2）
- **DAG 稳定性继承**：当记忆 A 导入记忆 B 时，A 部分继承 B 的稳定性。一个依赖稳定记忆的概念应比依赖易变记忆的概念更稳定。按导入强度加权。概念新颖性：使 DAG 拓扑影响衰减动态——CodeMemory 独有。（研究员 R-BOMB-3）
- **"自您上次访问以来"的上下文注入**：当解析一个 30 天未触碰的记忆时，注入摘要块显示依赖链中的变化。唯一可行，因为 CodeMemory 同时追踪结构（DAG）和时间（衰减）。（进化策略师 N3）
- **搜索衰减感知排名**：对搜索结果排序应用衰减乘数。最近访问的记忆在同等结构重要性下排名更高。约 15 LOC。（研究员 R-YLW-2）
- **领域校准稳定性预设**：在 create 期间基于标签/类型/maturity 建议稳定性值。投资事实 7-14 天，软件架构概念 30-60 天，量化操作员公式 60-180 天。约 50 LOC。（研究员 R-YLW-1 / Bomb 1）
- **Git 集成指南 + GitHub Action**：为开发者受众提供文档化的 .md 数据集版本控制工作流。在 push 时运行 validate 的 GitHub Action。"代码式记忆"叙事。（进化策略师 N3）


## 第 15 轮追加任务

> **日期**：2026-05-07
> **上轮评估**：Round 14 — 7/8 PASS + 1 项有意延期（N3）。衰减管道修复确认生效（C1），stability 边界防护就位（C2），API 衰减字段暴露（C3），模态退场动画接线（I1），sub-12px 字体修复（I2），Dashboard 衰减风险面板（N1），图右键 Resolve（N2）。86/86 测试通过，零回归。
> **主题**：完整性 & 打磨 & 自适应衰减 — 兑现 Playwright 承诺、消除最后已知 UI 缺陷、采纳研究员的高价值低投入发现
> **筛选原则**：本轮为投资循环倒数第二轮（4/5）。规则：(1) Playwright 必须作为首个任务——连续三轮延期已成本轮阻塞性约束；(2) 修复而非新建——消除最后两个已知 UI 缺陷；(3) 采纳研究员标记为 Critical 或 Important 且投入不超过 1 天的发现；(4) 为 R16（最终轮）保留大型功能（全文搜索、可写 MCP 工具）。

### 第一梯队：必达 — 承诺兑现 + 已知缺陷

- [x] R15-P1: Playwright 冒烟测试（5 条）
  - 目标：为前端添加 Playwright 端到端冒烟测试覆盖。5 条测试：app 加载并渲染、图 canvas 挂载并显示节点、点击图节点打开详情面板、搜索栏输入返回结果、创建-读取-更新-删除（CRUD）完整周期。这是 R12 首次承诺、R13 和 R14 连续延期的项目。必须作为 R15 首个任务——在任何功能代码之前交付。
  - 验收：`npx playwright test` 5 条测试全部通过；测试在 headless 和 headed 模式均可运行；测试之间独立（不依赖执行顺序）；测试产出包含失败截图；测试纳入 `package.json` 脚本（`test:e2e`）；Playwright 作为 devDependency 添加到 `package.json`；无 TypeScript 错误。
  - 来源：进化策略师 Critical #C2（"Playwright constraint... now three rounds overdue. This is not a sustainable pattern. Must be R15's first task."）

- [x] R15-I1: HelpPanel 退场动画接线
  - 目标：为 HelpPanel 添加关闭时的 `panel-slide-exit` 退场动画。当前 HelpPanel 使用硬编码 `panel-slide-enter` 且条件渲染绑定原始 `showHelp` 布尔值——关闭时 DOM 立即卸载，无动画。将 `useExitAnimation` hook 导入 HelpPanel（该 hook 已在 MemoryDetail、MemoryForm、Settings、Wander、Validate、Archive 共 6 个表面经过验证），gate 渲染于 `visible`/`closing` 状态，关闭时应用 `panel-slide-exit` CSS 类。这是 R13 第二轮报告缺口且 R14 再次报告——最后一个无动画 UI 表面。
  - 验收：关闭 HelpPanel 时可见 250ms slide-out 退场动画（非立即 DOM 消失）；遮罩背景同步退场（如适用）；动画时长与所有其他面板一致（250ms ease）；Escape 键触发的关闭同样播放退场动画；退场动画播放期间不可与正在关闭的 HelpPanel 交互；入场动画行为不变；TypeScript 构建零错误
  - 来源：体验官 Critical #1（"Last unanimated UI surface. Every other panel and modal has smooth exit. The code pattern exists. This is a fifth-round-straggler fix."）

- [x] R15-I2: 修复残留 11px straggler（4 处）
  - 目标：将最后 4 处 11px DOM 文本元素提升至 12px：(1) HelpPanel 键帽标签（line 337）；(2) HelpPanel 快捷键描述文本（line 405）；(3) MemoryDetail 空状态文本（line 630）；(4) App.tsx 视图快捷键提示（"1"/"2"/"3"，lines 678/699/720）。R14-I2 消除了所有 9px 和 10px 文本，但将 4 处元素留在 11px。其中 HelpPanel 是用户用来学习产品快捷键的参考表——11px 在参考上下文中仍然偏小。视图快捷键提示为装饰性文字但一致性要求 12px。
  - 验收：HelpPanel 中无元素 `fontSize < 12px`（键帽和快捷键描述均为 12px）；MemoryDetail 空状态文本 >= 12px；视图快捷键提示 >= 12px；HelpPanel 快捷键参考表在正常观看距离下完全可读（12px + 行间距合理）；深色模式下适用；表格布局不因字号提升而破损（列宽自适应）；TypeScript 构建零错误
  - 来源：体验官 Critical #2（"HelpPanel keycaps and shortcut descriptions... at 11px in a reference table the user is expected to read to learn the product still feels under-spec."）

### 第二梯队：研究驱动 — 高价值、低投入、后端核心

- [x] R15-C1: 自适应 stability 更新（访问时 SInc）
  - 目标：在 `resolve.py` 的访问追踪代码块中，于 `access_count` 递增之后添加 stability 更新步骤。实现简化版 SInc（Stability Increase）函数，灵感来自 FSRS v6：乘数在最优复习窗口（R ~ 0.7-0.85）处达到峰值，太早（R > 0.95，集中练习）时最小，太晚（R < 0.3，接近遗忘）时中等。乘数范围约 1.05-1.80。应用收益递减因子：`diminish = sqrt(14.0 / max(current_stability, 14.0))`，确保高 stability 时增长放缓。完全向后兼容——所有记忆从 stability=14.0 起步，通过使用自适应向上。不改变 `create` 或 `update` 路径；不影响未访问过的记忆。
  - 验收：首次 resolve 访问记忆时 stability 值增加（从 14.0 增长）；同一记忆多次 resolve（短时间内）产生的 stability 增长小于间隔较长的 resolve（集中练习 vs 间隔效应）；stability 增长在高值处收益递减（stability=365 的记忆增长远小于稳定性=14 的记忆）；`access_count=0` 或 `days_since=None`（从未访问）的记忆 stability 不改变；向后兼容——无 stability 字段的旧记忆在首次加载时自动获取 14.0；57+24 测试通过；仅 resolve 触发 stability 更新——overview、wander、validate 不触发
  - 来源：研究员 Critical #1（"This is the single most important architectural improvement identified by adjacent research. Both FSRS and SuperMemo have proven that adaptive stability outperforms static stability by 20-30% in real-world usage."）

- [x] R15-C2: 长期保留底线（混合衰减公式）
  - 目标：将纯指数衰减公式 `0.5^(days/stability)` 替换为混合公式，在保留短期排名行为的同时防止长期静默知识丢失。混合公式：`R_hybrid = max(0.5^(days/stability), 0.1 / (1 + days / (10 * stability)))`。在 R < 0.1 之前（~46 天默认），行为与纯指数衰减相同（精确到 0.1%）。之后，power-law 渐近线为所有记忆保留 ~3-6% 的检索底线，匹配 Bahrick"永久存储"发现——良好学习的语义知识保留基线可访问性。在三个消费点应用：overview heat（`handlers.py:263`）、wander cool 权重（`handlers.py:349`）、validate 衰减警告（`validate.py:103`）。
  - 验收：在 stability=14.0、days=90 处：当前 `0.5^(90/14) = 1.2%` → 混合后 `max(1.2%, 0.1/(1+90/140)) = max(1.2%, 6.1%) = 6.1%`（~5x 提升）；在 stability=14.0、days=14 处：`max(50%, 0.1/(1+14/140)) = 50%`（短期行为不变）；在 stability=14.0、days=46 处：`max(10.3%, 0.1/(1+46/140)) = max(10.3%, 9.9%) = 10.3%`（阈值处近乎不变）；衰减警告（R < 0.1 触发）行为不变——混合公式在该阈值处与纯指数相交；所有记忆的检索概率渐近线 > 0（无记忆有效达到零）；57+24 测试无回归
  - 来源：研究员 Critical #2（"The current model contradicts the cognitive reality that well-learned semantic knowledge persists for years... A knowledge management system should not silently lose reference material because it wasn't accessed in 90 days."）

- [x] R15-C3: 领域差异化默认 stability
  - 目标：基于 `semantic_type` 和 `schema` 在创建时设置合理的 stability 默认值，替换当前所有记忆统一的 `stability=14.0`。实现为创建时（`handlers.py:handle_create` 或 `create.py`）使用的 `{semantic_type: default_stability}` 查找表。建议映射：`schemas`=365d（模板为永久参考）、`api`=365d（API 文档为永久）、`decision`=90d（决策有中等生命周期）、`research`=90d（研究笔记有中等生命周期）、`context`=30d（上下文摘要为中期）、`meeting`=7d（会议笔记一周内衰减）、`daily`=5d（日记最短暂）。默认后备值 14.0 保持不变——仅当前端或 CLI 创建时传入了 `semantic_type` 才读取映射。通过 schema 引用创建的记忆继承其 schema 的 stability 默认值。用户始终可以通过 MemoryForm 或 update 命令覆盖默认值。
  - 验收：通过 `--semantic-type decision` 创建的记忆获得 `stability=90.0`（而非 14.0）；通过 `--semantic-type api` 创建的记忆获得 `stability=365.0`；无 `--semantic-type` 创建的记忆获得 `stability=14.0`（行为不变）；通过 `--schema schemas/my-template` 创建的记忆继承 schema 的 stability 默认值（365d）；通过 `--stability 30` 显式设置 stability 覆盖语义类型默认值（用户始终有最终决定权）；现有记忆 stability 值不因 reindex 而改变（仅影响新创建）；57+24 测试无回归
  - 来源：研究员 Important #3（"The simplest possible improvement — a lookup table that brings default behavior closer to cognitive reality. Zero algorithmic complexity. Eliminates the most common 'wrong default' scenario: API docs decaying after 46 days."）

### 第三梯队：容量允许时 — 小范围高价值改进

- [x] R15-C4: 消除 search dict / MemoryEntry 双重表示
  - 目标：将 `search()` 函数重构为从 `MemoryEntry.model_dump()` 构建其输出字典，而非手动逐字段复制。R14 C1 bug（overview 从 search dict 读取 `days_since_last_access`，但 search 从未输出该字段）的根本原因是同一记忆存在两种独立维护的数据表示。`model_dump()` 产生所有 MemoryEntry 字段的完整字典——任何添加到模型的未来字段自动出现在搜索结果中，无需手动传播。这是进化策略师标记为消除"未来字段缺失"整类 bug 所需的重构。
  - 验收：`search()` 返回与当前相同的数据形状（相同键、相同值、相同类型），以保证零消费者破坏；`search()` 输出现在包含 `MemoryEntry` 模型的所有字段（未来字段自动包含）；向 `MemoryEntry` 添加新字段后无需修改 `search.py`；所有现有搜索消费者（overview、wander、CLI search、API /api/search）行为不变；57+24 测试无回归
  - 来源：进化策略师 Critical #C3（"The C1 bug was caused by two data representations diverging. Refactor search() to build output from MemoryEntry.model_dump() instead of manual field copying."）

- [x] R15-N1: MemoryDetail 中显示访问新鲜度
  - 目标：在 MemoryDetail 面板头部区域（标题/标签附近）展示两条访问新鲜度信息：(1) "最后访问 X 天前"或"从未访问"；(2) 当前检索概率 R = XX%（基于当前 stability 和 days_since_last_access 的衰减公式输出）。数据已在 API 响应中（`days_since_last_access`、`stability` 字段，自 R14-C3 起），MemoryDetail 组件接收这些 props——仅需渲染。将访问新鲜度展示在摘要文本下方或成熟度/状态徽章旁，使用次要文本样式（12px、低突出度颜色），不主导详情视图。新创建或从未访问的记忆显示"从未访问 · R=N/A"。
  - 验收：查看有 > 0 次访问的记忆时 MemoryDetail 显示"最后访问 X 天前"和"R:XX.X%"；从未访问的记忆显示"从未访问 · R=N/A"；新鲜度值在 resolve 后更新（resolve 重置 last_access 为 now）；数值来自 API 响应中已有的字段（无新端点）；展示使用次要文本样式，不喧宾夺主；亮色和深色模式适用；布局不破损；TypeScript 构建零错误
  - 来源：体验官 Important #4（"The decay fields are in the API response. The MemoryDetail panel receives them as props. Rendering them is low-effort, high-visibility."）

---

### 本轮延期项目（下轮评估）

- **全文正文搜索**（进化策略师 C1）—— #1 功能缺口。需搜索管道变更 + 前端双向接线 + 结果高亮。保留给 R16 最终轮。
- **可写 MCP 工具**（进化策略师 I1）—— 闭合 agentic 循环。需安全边界设计（propose_* 暂存模式）。~150 LOC。保留给 R16 最终轮。
- **Per-memory stability UI（前端滑块）**（体验官 Important #3 + 进化策略师 I2）—— 后端 stability 工作已在 R15 完成（自适应更新 + 长期底线 + 领域默认值）。前端 UI 在 R16 跟进。
- **复习队列**（体验官 Important #6）—— 顺序修复流程，需新建前端组件。依赖 stability UI 到位。
- **List 视图衰减列**（进化策略师 I3）—— 外观层面，R16 评估。
- **完整 Cooling Memories Dashboard**（进化策略师 I5）—— 将 N1 扩展到完整可排序列表。R16 评估。
- **Wander 主动复习模式（`--mode review`）**（研究员 Important #4）—— 依赖 C1 自适应 stability 先落地并稳定。
- **Stability 陈旧下降**（研究员 Important #5）—— 对称于 C1。当 resolve 检测到 hash 不匹配时 stability 应下降。R16 末尾自然纳入。
- **多级撤销栈**（进化策略师 I6）—— 跨组件状态管理重构。中等投入。
- **MemoryForm 自动补全 imports 建议**（进化策略师 I4）—— `suggest_deps.py` 存在但仅 CLI。~80 LOC。
- **全文正文搜索衰减感知排名**（研究员 R-YLW-2）—— 依赖全文搜索先落地。
- **"自您上次访问以来"上下文注入**（进化策略师 N4）—— 需依赖链 diff 逻辑。
- **记忆健康评分 Dashboard**（进化策略师 N5）—— 中等投入，依赖多项衰减特性稳定。
- **图键盘导航**（进化策略师 N2）—— 需跨组件事件绑定。

### 本轮拒绝项目（需架构变更、新依赖或超出本轮容量）

- **全文正文搜索**—— 保留给 R16 最终轮，用作该轮中心功能
- **可写 MCP 工具**—— 保留给 R16 最终轮，用作该轮第二中心功能
- **跨数据集解析**（体验官 Strategy #11）—— 重大架构变更（3-4 天），需共享索引 + resolve 引擎变更。独立轮次范畴。
- **语义/嵌入搜索**（进化策略师 N6）—— 新管道（ONNX/WASM），数月非数天。长期战略资产。
- **交互式 onboarding / Demo Resolve 按钮**（进化策略师 N1）—— 低投入（~50 LOC + 3 个 .md 文件），但在最终轮应让位于全文搜索和可写 MCP 工具。
- **CSS 设计 token 系统**（进化策略师 I4 长期）—— 架构级重构，覆盖 14 个组件。
- **Markdown 预览**—— 需新建 UI 组件，体验官 Nice-to-have #14 连续三轮未采纳。
- **图漫步模式**（体验官 Strategy #13）—— 3 天，大规模 D3/Cytoscape 动画工作。
- **访问新鲜度时间线**（体验官 Strategy #12）—— 2-3 天，需 sparkline + activity feed。

### 新增陷阱（本轮结束后追加至 pitfalls.md）

- **[R15-C1] stability 值会因 resolve 访问而随时间增长。** 依赖于精确 stability 值（如 `== 14.0`）的测试将失败。验收应使用 `>=` 或检查 stability 的变化方向（新值 > 旧值）而非精确数值。`access_count` 不应用于推导 stability——stability 的增长率取决于上次访问时的检索概率 `R`，而非访问次数。

- **[R15-C1] 在未先 reindex 的情况下多次 resolve 同一记忆会给出不同的 stability 增长量。** 首次 resolve：R ~ 1.0（刚访问过）→ SInc 最小（~1.05）。等待 7-14 天后再次 resolve：R ~ 0.5-0.7 → SInc 峰值（~1.3-1.5）。这是预期行为，不是 bug——间隔效应使然。验收必须将间隔因素纳入计算，或使用允许范围而非精确断言。

- **[R15-C2] 混合衰减公式在 R < 0.1 时与纯指数产生不同结果。** 任何对纯指数衰减值的硬编码断言（如 `0.5^(90/14) = 0.0116`）在混合公式下将失败。长期（> 60 天）的 R 值预期将更高（保留底线 3-6%）。短期行为不变。验收应分别测试短期行为（days < 46，预期不变）和长期底线（days > 90，预期 > 0）。

- **[R15-C2] validate 衰减警告的 R < 0.1 阈值行为不变。** 混合公式在 R = 0.1 附近与纯指数相交——警告触发条件不变。但是，一旦 `decay_risk` 数组在 `/api/stats` 中暴露，其条目数量将因 memory 在混合公式下以不同速率穿越阈值而变化（长期 baseline 更高 → 跨越 0.1 阈值的 memory 更少）。

- **[R15-C3] 领域默认值仅影响新创建的记忆。** 运行 `reindex` 不会追溯更新现有记忆的 stability。验收应将创建时行为（新记忆获得映射后的 stability）与 reindex 时行为（现有 stability 值不变）分开测试。如果后续修改了查找表映射，已创建记忆的 stability 不受影响。

- **[R15-P1] Playwright 需要浏览器二进制文件。** `npx playwright install chromium` 下载 ~150MB。首次运行前需要网络连接。CI 环境可能需要额外的系统依赖（lib 库）。验收脚本应在运行测试前检查 Playwright 浏览器是否已安装。

- **[R15-C4] `model_dump()` 产生的字段多于旧的 hand-rolled dict。** 如果存在任何使用 `len(dict)` 或 `dict.keys()` 检查精确形状的消费者，将看到额外的键。对所有搜索消费者的现有断言使用 `.get()` 而不是精确 key 集合比较。

- **[R15-I1] HelpPanel 使用与 Modal 组件不同的退场 CSS 类。** Modal 使用 `modal-fade-exit` / `backdrop-fade-exit`；面板（如 MemoryDetail）使用 `panel-slide-exit`。HelpPanel 是面板，应使用 `panel-slide-exit`。如果误用模态退场类，动画效果将不匹配（fade+scale 而非 slide）。

### 长期 Backlog 新增（本轮审计中识别的新项目）

- **FSRS-lite 完整 stability 更新**（研究员 F3）—— R15-C1 的部分实现。完整 FSRS-6 需要 21 个 per-user 参数、power-law 遗忘曲线（w20 个性化）、和基于难度（D）的 stability 更新。R15 的简化 SInc 是第一步。
- **Per-memory 衰减曲线形状**（研究员 Strategy #9）—— 允许在 frontmatter 中设置 `decay_type`：`exponential`（当前）、`power_law`（R=S/(S+t)）、`exponential_power`（Weibull）、`permastore`（永久无衰减）。将"不同内容类型有不同遗忘曲线"的研究发现转化为产品功能。
- **DAG stability 继承**（研究员 R-BOMB-3）—— 当记忆 A imports 记忆 B 时，A 部分继承 B 的 stability。按 import 强度加权。使 DAG 拓扑影响衰减动态——CodeMemory 独有能力。
- **"衰减即功能"Dashboard**（研究员 R-BOMB-2）—— 在 Dashboard 中展示"你即将遗忘的内容"——R 值接近衰减警告阈值（0.1-0.2）的记忆。"救援队列"将衰减模型从后端机制升级为主动 UX 功能。无已知 PKM 工具将遗忘作为用户可见功能。
- **Per-tag stability 默认值**（进化策略师 F2）—— 标签级 stability（"investment"=30d，"facts"=7d）。新记忆从标签继承。比 semantic_type 映射（R15-C3）更细粒度但维护成本更高。
- **"代码式记忆"CI 流水线**（进化策略师 F5）—— GitHub Action + pre-commit hook 在 push 时运行 validate/reindex。拒绝含循环或断链的 PR。开发者采用楔子。
