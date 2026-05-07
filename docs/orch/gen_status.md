# Generator Status — Iteration 13

## 完成的任务 (11/11)

### 第一梯队：审美完成
- [x] **R13-A1**: 退场动画接线 — 创建 `useExitAnimation` 通用 hook，接线 MemoryDetail/Settings/MemoryForm 三个组件面板+遮罩，关闭时播放 `panel-slide-exit`/`backdrop-fade-exit` CSS 动画再卸载 DOM。Escape 键触发的关闭同样播放退场。覆盖 7 处入口。
- [x] **R13-A2**: 修复残余 sub-12px 字号 — Badges.tsx 默认 fontSize 11→12；SearchBar.tsx "includes fuzzy matches" 9→11px、match quality badge 9→11px。
- [x] **R13-A3**: 搜索下拉框 fade-in 动画 — CSS `dropdownFadeIn` 动画（150ms ease + translateY），SearchBar 挂载 `search-dropdown-enter` class。

### 第二梯队：发现路径缩短
- [x] **R13-D1**: 搜索结果添加 "Resolve →" 动作 — SearchBar 每条结果旁显示按钮；App.tsx 处理关闭下拉框→切换到 Graph→100ms 延迟触发 resolve。
- [x] **R13-D2**: 视图切换按钮添加快捷键提示 — Graph/List/Dashboard 按钮内嵌 "1"/"2"/"3" 小号提示（10px, 55% opacity）。
- [x] **R13-D3**: Resolve 加载状态 — MemoryDetail 新增 `isResolving` prop，resolve 运行期间展示 shimmer 骨架动画。

### 第三梯队：衰减模型统一
- [x] **R13-M1**: 统一 overview/wander/validate 衰减模型 — 三套逻辑统一为 `0.5^(days/stability)` 公式。
- [x] **R13-M2**: 排除循环参与者从 dependents 计数 — overview heat 计算时预计算 required-imports 循环，将其 dependents 计为 0。
- [x] **R13-M3**: index 预计算 days_since_last_access — MemoryEntry 新增 int 字段，reindex 时计算，resolve 后设为 0，概述中用该字段替代 datetime.fromisoformat。
- [x] **R13-M4**: 添加 stability 字段（默认 14.0）— MemoryEntry 新增 `stability: float = 14.0`，heat 公式使用 stability 替代硬编码 14.0。

### 第四梯队：基础设施
- [x] **R13-I1**: 启用 OpenAPI /docs 端点 — /docs 和 /openapi.json 加入数据集中间件豁免列表，HTTP 200 可访问。

## 验收命令输出

### TypeScript 类型检查
```
npx tsc --noEmit
(无错误，通过)
```

### Frontend 构建
```
npx vite build
✓ built in 339ms
dist/index.html                   0.48 kB
dist/assets/index-DzG4uodV.css   14.80 kB
dist/assets/index-DuTcM8Z4.js   997.06 kB
```

### Python 单元测试 (57/57)
```
PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short
============================= 57 passed in 0.30s ==============================
```

### Python 集成测试 (24/24)
```
PYTHONPATH=src python tests/integration_test.py
Results: 24/24 passed
All tests PASSED
```

### API 测试 (5/5)
```
PYTHONPATH=src python -m pytest tests/test_api.py -v --tb=short
============================== 5 passed in 0.46s ==============================
```

### Backend 端点回归
```
GET  /api/stats    → 200 OK (JSON stats with total/maturity/tags)
POST /api/wander   → 200 OK (cold memory with id/summary/access_count)
POST /api/validate → 200 OK (validated_count: 11, error_count: 0, warning_count: 1)
GET  /docs         → 200 OK (Swagger UI accessible)
```

### Index 字段验证
```
Keys present: [..., days_since_last_access, ..., stability, ...]
Has stability: True, value: 14.0, type: float
Has days_since_last_access: True, value: 0, type: int
```

### Overview 热力计算
```
user/investment/risk-tolerance     atom  heat:31  [active]  [investment, preference]
user/investment/semiconductor-thesis atom heat:31  [active]  [investment, thesis]
user/facts/nvidia-earnings         atom  heat:21  [active]  [investment, fact, ...]
user/facts/soxl-composition        atom  heat:21  [active]  [investment, fact, etf]
user/investment/february-buy       atom  heat:20  [active]  [investment, decision]
```

## 文件变更清单

| 文件 | 任务 |
|------|------|
| `frontend/src/useExitAnimation.ts` (新) | R13-A1 通用退场动画 hook |
| `frontend/src/components/Badges.tsx` | R13-A2 fontSize 提升 |
| `frontend/src/components/SearchBar.tsx` | R13-A2/A3/D1 字号修复+动画+Resolve按钮 |
| `frontend/src/components/MemoryDetail.tsx` | R13-A1 退场动画 + R13-D3 加载骨架 |
| `frontend/src/components/Settings.tsx` | R13-A1 退场动画 |
| `frontend/src/components/MemoryForm.tsx` | R13-A1 退场动画 + show prop |
| `frontend/src/App.tsx` | R13-D1/D2/D3/A1 搜索 Resolve/快捷键提示/加载状态/始终渲染 |
| `frontend/src/index.css` | R13-A3 搜索下拉动画 |
| `src/codememory/models.py` | R13-M3 days_since_last_access + R13-M4 stability |
| `src/codememory/index.py` | R13-M3 reindex 时计算 days_since_last_access |
| `src/codememory/resolve.py` | R13-M3 resolve 后 days_since = 0 |
| `src/codememory/handlers.py` | R13-M1/M2/M3/M4 统一衰减+循环排除+预计算+stability |
| `src/codememory/validate.py` | R13-M1 统一 _check_decay 衰减公式 |
| `backend/server.py` | R13-I1 /docs /openapi.json 豁免中间件 |

## 新发现的陷阱
无。

## 状态
**PASSED** — 11/11 任务完成，86/86 测试通过（57 unit + 24 integration + 5 API），零回归，TypeScript 类型检查通过，Vite 构建成功，所有 Backend 端点正常。
