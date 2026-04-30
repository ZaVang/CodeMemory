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
