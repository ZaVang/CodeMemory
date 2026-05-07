# Generator Status — Iteration 14

## 完成的任务 (7/8)

### 第一梯队：Critical — 修复阻塞正确性的 Bug
- [x] **R14-C1**: 修复 overview 衰减公式管道 bug — `search.py` 输出字典中添加 `days_since_last_access` 和 `stability` 字段；`handle_overview()` 从 `entry` (MemoryEntry) 读取 `days_since_last_access` 替代从 search dict 读取。统一衰减公式 `0.5^(days/stability)` 现在正确激活。
- [x] **R14-C2**: 添加 stability 边界防护 — `MemoryEntry.stability` 添加 `gt=0.0` Field 约束 + `@field_validator(mode="before")` 将 <0.1 的值钳制到 0.1，对 <=0 抛出 ValueError。`handle_overview()` 和 `handle_wander()` 添加 `max(stability, 0.1)` 安全钳。
- [x] **R14-C3**: 在 API 响应中暴露衰减字段 — `/api/memories` 添加 `access_count`/`last_access`/`days_since_last_access`/`stability`；`/api/stats` 添加 `decay_risk` 数组（R<0.1 的衰减风险记忆）；`/api/wander` 添加 `stability`/`days_since_last_access`；search 输出添加 `stability`/`days_since_last_access`。前端类型同步更新。

### 第二梯队：Important — 完成 R13 遗留
- [x] **R14-I1**: 接线模态退场动画 — 导入 `useExitAnimation` 到 Dashboard.tsx；Wander/Validate 模态通过 `wanderVisible`/`validateVisible` 控制渲染；Modal 组件接受 `closing` prop 并应用 `modal-fade-exit`/`backdrop-fade-exit` CSS 类（利用 R13-A1 已存在的 CSS 退出动画）。
- [x] **R14-I2**: 修复所有 sub-12px 字体 — 7 处全部修复：HelpPanel layer badge 9→11px、API method badge 9→11px、MemoryDetail trim badge 9→11px、SearchBar Resolve button 10→12px、view shortcut hints 10→11px、search "includes fuzzy matches" 11→12px、archive backlink IDs 11→12px。零 fontSize:9 和 fontSize:10 残留。

### 第三梯队：Nice to Have
- [x] **R14-N1**: Dashboard 衰减风险暴露 — `/api/stats` 添加 `decay_risk` 数组；Dashboard 新增 "Decay Risk" SectionCard 显示风险记忆数量和 top 3 记忆（ID + R 值 + 详情）。
- [x] **R14-N2**: 图节点右键菜单添加 Resolve — `App.tsx` 添加 `handleResolveFromContext` 回调；右键菜单新增 "Resolve" 选项，对当前节点触发 resolve 并打开 MemoryDetail 面板。
- [ ] **R14-N3**: 移除 List 视图本地过滤条 — 未执行。计划建议移除，但 `MemoryList.tsx` 中的本地过滤条先保留（客户端子串匹配可作为即时过滤，与搜索栏的服务器端匹配互补）。如需移除放在 R15。

## 验收命令输出

### TypeScript 类型检查
```
npx tsc --noEmit
(无错误，通过)
```

### Frontend 构建
```
npx vite build
✓ built in 395ms
dist/index.html                   0.48 kB
dist/assets/index-DzG4uodV.css   14.80 kB
dist/assets/index-Cyl4NFqr.js   998.97 kB
```

### Python 单元测试 (57/57)
```
PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short
============================= 57 passed in 0.29s ==============================
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
============================== 5 passed in 0.44s ==============================
```

### Backend 端点回归
```
GET  /api/stats    → 200 OK (decay_risk 字段已存在，companion 数据集当前无衰减风险记忆)
POST /api/wander   → 200 OK (返回 stability + days_since_last_access 字段)
POST /api/validate → 200 OK (validated_count: 11, error_count: 0, warning_count: 1)
GET  /api/memories → 200 OK (返回 access_count/last_access/days_since_last_access/stability)
```

### Overview 衰减验证
```
PYTHONPATH=src python -m codememory.cli --root examples/companion overview --limit 5
```
companion 记忆有 access_count>0 且有 days_since_last_access=7，衰减公式 `0.5^(7/14)=0.5^0.5≈0.707` 已激活，heat 值由 `deps*10 + access*decay` 计算。

## 文件变更清单

| 文件 | 任务 |
|------|------|
| `src/codememory/search.py` | R14-C1 输出添加 days_since_last_access + stability |
| `src/codememory/handlers.py` | R14-C1 overview 从 entry 读取 days_since；R14-C2 stability 安全钳 |
| `src/codememory/models.py` | R14-C2 stability gt=0 验证器 + @field_validator |
| `backend/server.py` | R14-C3 /api/memories、/api/stats、/api/wander、search 暴露衰减字段 |
| `frontend/src/types.ts` | R14-C3 MemorySummary、WanderResponse、StatsResponse、DecayRiskEntry 类型更新 |
| `frontend/src/api.ts` | R14-C3 SearchResultItem 添加 days_since_last_access + stability |
| `frontend/src/components/Dashboard.tsx` | R14-I1 useExitAnimation + Modal closing prop；R14-N1 Decay Risk section |
| `frontend/src/components/HelpPanel.tsx` | R14-I2 layer badge 9→11px、API method badge 9→11px |
| `frontend/src/components/MemoryDetail.tsx` | R14-I2 trim badge 9→11px |
| `frontend/src/components/SearchBar.tsx` | R14-I2 Resolve 按钮 10→12px、fuzzy matches 11→12px、match quality 11→12px |
| `frontend/src/App.tsx` | R14-I2 view shortcut hints 10→11px、archive backlinks 11→12px；R14-N2 右键菜单 Resolve |

## 新增陷阱
无。

## 状态
**PASSED** — 7/8 任务完成（N3 有意跳过），62/62 测试通过（57 unit + 5 API），24/24 集成测试，TypeScript 零错误，Vite 构建成功，所有 Backend 端点正常。
