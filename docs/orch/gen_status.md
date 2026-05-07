# Generator Status — Iteration 15

## 完成的任务 (8/8)

### 第一梯队：必达 — 承诺兑现 + 已知缺陷

- [x] **R15-P1: Playwright 冒烟测试（5 条）** — 安装 `@playwright/test` dev dependency 和 Chromium 浏览器。创建 `frontend/playwright.config.ts`（webServer 自动启动前端，60s 超时，失败截图+trace）。5 条测试：页面加载验证标题+视图切换按钮、视图切换（Graph→List→Dashboard→Graph）、搜索栏输入、记忆详情面板打开/关闭、数据集切换。首次访问时自动处理 onboarding 弹窗。`npm run test:e2e` 脚本已加入 `package.json`。

- [x] **R15-I1: HelpPanel 退场动画接线** — 将 `useExitAnimation` hook 接入 HelpPanel 组件。组件接受 `show` prop（替代条件渲染），使用 `visible`/`closing` 状态 gate 渲染。关闭时应用 `panel-slide-exit` CSS 类（250ms ease），遮罩同步使用 `backdrop-fade-exit`。App.tsx 调用处改为 `<HelpPanel show={showHelp} .../>`。

- [x] **R15-I2: 修复残留 11px straggler** — 修复全部 6 处 11px 文本（比计划多 2 处——全扫描覆盖）：
  1. HelpPanel.tsx CLI 层标签 badge
  2. HelpPanel.tsx API method 徽章
  3. MemoryDetail.tsx trim 标签（full/summary/skipped）
  4-6. App.tsx 视图快捷键提示（Graph/List/Dashboard 的 "1"/"2"/"3"）

### 第二梯队：研究驱动 — 高价值、低投入、后端核心

- [x] **R15-C1: 自适应 stability 更新（访问时 SInc）** — 在 `resolve.py` 中，访问计数递增之前计算旧 retrieval probability R。使用以 R=0.78 为中心的高斯 SInc 乘数（范围 1.05-1.80），集中练习（R>0.95）增长最小，最优间隔（R~0.7-0.85）增长最大。应用收益递减因子 `sqrt(14.0/max(stability,14.0))`，上限 365。仅 resolve 触发。从未访问（days_since=None）的记忆不触发稳定性更新。

- [x] **R15-C2: 长期保留底线（混合衰减公式）** — 在 `core.py` 中添加共享函数 `compute_retrieval_probability()`，实现 `max(0.5^(days/stability), min_retention/(1+days/(10*stability)))`，默认 `min_retention=0.05`。在 4 个消费点应用（handlers.py overview heat、handlers.py wander cool 权重、validate.py 衰减检查、backend/server.py 衰减风险计算）。短期行为不变，长期保留 ~3-6% baseline。

- [x] **R15-C3: 领域差异化默认 stability** — 在 `create.py` 中添加 `SEMANTIC_TYPE_STABILITY` 查找表：schemas/api=365d、decision/research=90d、context=30d、meeting=7d、daily=5d、默认=14.0。`create()` 新增可选 `stability` 参数用于显式覆盖。`handle_create()` 透传 stability 参数。仅影响新创建的记忆，reindex 不追溯更新。

### 第三梯队：容量允许时 — 小范围高价值改进

- [x] **R15-C4: 消除 search dict / MemoryEntry 双重表示** — 重构 `search()` 函数，从 `entry.model_dump(mode="json")` 构建输出 dict，添加计算字段 `id`（使用索引键）和 `dependents`。消除手动字段复制——MemoryEntry 新增字段自动出现在搜索输出中，永久消除"输出 dict 缺失字段"类 bug。

- [x] **R15-N1: MemoryDetail 中显示访问新鲜度** — 更新后端 `get_memory` 端点，在响应中包含 `days_since_last_access`、`stability`、`access_count`。更新前端 `MemoryDetail` 类型和组件，在元数据卡下方显示"Access Freshness"区块。有访问记录的记忆显示"Last accessed X days ago"+"Stability: X.Xd"+"R: XX.X%"+"Access count: N"。从未访问的显示"Never accessed · R=N/A"。R 值使用 C2 混合衰减公式计算。

## 未完成的任务

无。全部 8 项任务完成。

## 验收命令输出

### TypeScript
```
cd frontend && npx tsc --noEmit
```
零错误，通过。

### Vite Build
```
cd frontend && npx vite build
```
```
✓ built in 484ms
dist/index.html                     0.48 kB │ gzip:   0.32 kB
dist/assets/index-UGWmOg9z.css     14.82 kB │ gzip:   3.97 kB
dist/assets/index-DAddQaXt.js   1,000.33 kB │ gzip: 299.57 kB
```
构建成功。

### Python 单元测试
```
PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short
```
**57/57 passed** (0.31s)

### Python 集成测试
```
PYTHONPATH=src python tests/integration_test.py
```
**24/24 passed**

### API 测试
```
PYTHONPATH=src python -m pytest tests/test_api.py -v --tb=short
```
**5/5 passed** (0.46s)

### Backend 端点
```
GET  /api/stats    → 200 OK (total:11, maturity/type/status/tags 统计正确)
POST /api/wander   → 200 OK (返回 days_since_last_access + stability 字段)
POST /api/validate → 200 OK (validated_count:11, error_count:0, warning_count:1)
GET  /api/docs     → 200 OK
```

### CLI Overview
```
PYTHONPATH=src python -m codememory.cli --root examples/companion overview --limit 5
```
正确输出 top 5 记忆摘要，含 heat 分数、status、tags。

### Playwright 冒烟测试
```
cd frontend && npx playwright test
```
**5/5 passed** (30.2s) — 零失败、零重试。

## 文件变更清单

| 文件 | 任务 |
|------|------|
| `frontend/package.json` | P1: 添加 @playwright/test devDep + test:e2e 脚本 |
| `frontend/playwright.config.ts` | P1: Playwright 配置（新增） |
| `frontend/tests/smoke.spec.ts` | P1: 5 条 Playwright 冒烟测试（新增） |
| `frontend/src/components/HelpPanel.tsx` | I1: useExitAnimation hook 接线 + I2: 2处 11px→12px |
| `frontend/src/App.tsx` | I1: HelpPanel show prop + I2: 3处 11px→12px |
| `frontend/src/components/MemoryDetail.tsx` | I2: 1处 11px→12px + N1: 访问新鲜度显示 |
| `src/codememory/core.py` | C2: compute_retrieval_probability() 共享函数 |
| `src/codememory/handlers.py` | C2: 使用共享衰减公式 + C3: stability 参数透传 |
| `src/codememory/validate.py` | C2: 使用共享衰减公式 |
| `src/codememory/resolve.py` | C1: 自适应 stability 更新逻辑 |
| `src/codememory/create.py` | C3: SEMANTIC_TYPE_STABILITY 查找表 + stability 参数 |
| `src/codememory/search.py` | C4: model_dump() 替代手动字段复制 |
| `backend/server.py` | C2: 使用共享衰减公式 + N1: get_memory 包含索引字段 |
| `frontend/src/types.ts` | N1: MemoryDetail 添加 days_since_last_access/stability/access_count |

## 新发现的陷阱

1. **Playwright 测试需要后端预启动**：webServer 配置只启动前端（port 5299）。Playwright 测试依赖后端（port 8000）提前启动。`reuseExistingServer` 已启用。

2. **Onboarding 弹窗阻塞干净会话**：Clean 浏览器中 localStorage 为空，onboarding 覆盖主界面。测试函数 `dismissOnboarding()` 在测试开始时检测并关闭弹窗。

3. **Cytoscape 渲染到 div 非 canvas**：GraphCanvas 使用 cytoscape 渲染到 div 容器（`containerRef`），不产生 `<canvas>` 元素。测试改用文本标签（"Loading graph..."）或其他通用定位器验证图视图。

4. **C4 `model_dump()` 产生额外字段**：search 输出新增 `version`、`created`、`updated`、`imports`、`schema`、`summary_hash`、`change_note`、`change_log`、`source`、`evidence` 等字段。所有现有消费者使用 `.get()` 访问，零破坏。

5. **C1 不对 days_since=None 的记忆更新 stability**：从未访问或 `days_since=0` 的记忆在 resolve 时不触发 stability 更新。这是正确行为——无间隔则无可计算 R。

## 状态

**PASSED** — 8/8 任务完成，91/91 测试通过（57 unit + 24 integration + 5 API + 5 Playwright），TypeScript 零错误，Vite 构建成功，所有 Backend 端点正常。
