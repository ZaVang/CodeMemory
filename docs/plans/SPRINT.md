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
