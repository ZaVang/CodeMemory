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
