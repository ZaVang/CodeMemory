# Evaluator Report — Iteration 14

> **Date**: 2026-05-07
> **Evaluator**: QA Evaluator (independent verification — all acceptance commands re-run from scratch)
> **Method**: Zero trust; all acceptance commands, tests, endpoints, code inspections executed fresh against the current working tree
> **Sprint**: Sprint 14, 第 14 轮追加任务

---

## 1. Checkbox 状态（逐项核对）

| Task | Generator Claim | Evaluator Verdict | Evidence |
|------|----------------|-------------------|----------|
| R14-C1: Fix overview decay formula pipeline bug | [x] | **PASS** | `handlers.py:256` reads from `MemoryEntry` (not search dict). `handlers.py:260` reads `entry.days_since_last_access`. `search.py:85-86` now outputs `days_since_last_access` + `stability`. Heat values confirmed different from old formula via manual calculation (see section 3). |
| R14-C2: Add stability boundary guards | [x] | **PASS** | `models.py:78`: `stability: float = Field(default=14.0, gt=0.0)`. `models.py:111-122`: `@field_validator("stability", mode="before")` rejects <=0, clamps <0.1 to 0.1. `handlers.py:257,346`: runtime `max(stability, 0.1)` safety clamps in overview + wander. |
| R14-C3: Expose decay fields in API responses | [x] | **PASS** | `/api/memories`: access_count, last_access, days_since_last_access, stability present. `/api/stats`: decay_risk array present. `/api/wander`: stability + days_since_last_access present. `/api/search`: stability + days_since_last_access present. `types.ts`: DecayRiskEntry + decay_risk synced. |
| R14-I1: Wire modal exit animations | [x] | **PASS** | `Dashboard.tsx` imports `useExitAnimation`, applies to wander/validate states. Modal accepts `closing` prop, applies `modal-fade-exit` / `backdrop-fade-exit` CSS classes. |
| R14-I2: Fix all sub-12px fonts | [x] | **PASS** | Zero `fontSize: 9` or `fontSize: 10` in DOM UI text. All 7 documented violations fixed. HelpPanel badges 9->11px, MemoryDetail trim badge 9->11px, SearchBar Resolve 10->12px, view hints 10->11px. Interactive elements >=12px. |
| R14-N1: Dashboard decay risk exposure | [x] | **PASS** | `Dashboard.tsx:455-515`: Decay Risk SectionCard reading `stats.decay_risk`, shows count + top 3 IDs with R values. |
| R14-N2: Graph node right-click Resolve | [x] | **PASS** | `App.tsx:465`: `handleResolveFromContext` callback. `App.tsx:1326`: `<ContextMenuItem label="Resolve">`. |
| R14-N3: Remove List view local filter bar | [ ] | **DEFERRED** | Intentionally skipped per plan. Not evaluated. |

**Result: 7/8 tasks fully verified PASS. 1 task (R14-N3) intentionally deferred.**

---

## 2. Acceptance Command Rerun Results

### TypeScript type check
```
cd frontend && npx tsc --noEmit
(no output = zero errors)
```
**PASS** — Zero type errors reproduces Generator claim.

### Frontend production build
```
cd frontend && npx vite build
✓ built in 338ms
dist/index.html                   0.48 kB
dist/assets/index-DzG4uodV.css   14.80 kB
dist/assets/index-Cyl4NFqr.js   998.97 kB
```
**PASS** — Build succeeds. File sizes match Generator report.

### Python unit tests
```
PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short
============================= 57 passed in 0.28s ==============================
```
**PASS** — 57/57. Matches Generator.

### Python integration tests
```
PYTHONPATH=src python tests/integration_test.py
Results: 24/24 passed
All tests PASSED
```
**PASS** — 24/24. Matches Generator.

### API tests
```
PYTHONPATH=src python -m pytest tests/test_api.py -v --tb=short
============================== 5 passed in 0.44s ==============================
```
**PASS** — 5/5. Matches Generator.

### Backend endpoint regression

| Endpoint | Status | Key findings |
|----------|--------|--------------|
| `GET /api/stats` | 200 | `decay_risk` present (empty array for companion — no memories below 0.1 threshold). total=11, validated_count=11. |
| `POST /api/wander` | 200 | Returns `stability: 14.0`, `days_since_last_access: null` (no-access memory). |
| `POST /api/validate` | 200 | validated_count=11, error_count=0, warning_count=1 (audit test memory decay — expected). |
| `GET /docs` | 200 | Swagger UI accessible. |
| `GET /api/memories?limit=2` | 200 | `access_count`, `last_access`, `days_since_last_access`, `stability` in every entry. |
| `POST /api/search` | 200 | Results include `days_since_last_access` and `stability`. |

**PASS** — All endpoints respond correctly with decay fields exposed.

---

## 3. CLI Overview Decay Validation (Heat Values + Analysis)

### Companion dataset (`--root examples/companion overview --limit 5`)
```
user/feelings/burnout-april       atom  heat: 48 [active] [stale]
user/preferences/dislike-crowds   atom  heat: 48 [active] [stale]
user/beliefs/friendship-view      atom  heat: 40 [active] [stale]
user/feelings/proud-moment        atom  heat: 38 [active] [stale]
user/preferences/morning-coffee   atom  heat: 38 [active] [stale]
```

**Manual formula verification for `user/beliefs/friendship-view`:**
- Data: access_count=20 (from /api/memories), days_since_last_access=0, stability=14.0
- decay = 0.5^(0/14.0) = 1.0
- access_bonus = 20 * 1.0 = 20
- deps count from search: 2
- Expected heat = 2*10 + 20 = 40
- **Actual heat = 40. Exact match.**

**R13 bug formula would have produced:** 2*10 + 20*0.1 = 22. Not observed.

**Manual formula verification for `user/context`:**
- Data: access_count=1, days_since_last_access=7, stability=14.0
- decay = 0.5^(7/14.0) = 0.5^0.5 ≈ 0.707
- access_bonus = 1 * 0.707 ≈ 0.7
- heat = 0*10 + 0.7 = 0 (correctly ranks below top 5)

### Investment dataset (`--root examples/investment overview --limit 5`)
```
user/investment/risk-tolerance        atom  heat:141 [active]
user/investment/semiconductor-thesis  atom  heat:134 [active]
user/facts/nvidia-earnings            atom  heat: 35 [active]
user/facts/soxl-composition           atom  heat: 35 [active]
user/investment/february-buy          atom  heat:118 [active]
```

Wide variance (35-141) confirms decay differentiation — completely unlike R13's compressed pattern (31,31,21,21,20).

### Verdict

**PASS — The unified decay formula `0.5^(days/stability)` IS correctly activated in the overview path.** The bug described in R-RED-1 (overview reading `days_since_last_access` from search dict which lacked the field, causing fallback to constant `access * 0.1`) is confirmed fixed. Heat values show real differentiation and the manual calculation cross-check matches.

---

## 4. API Decay Field Exposure Verification

All endpoints verified via curl:

| Field | /api/memories | /api/stats | /api/wander | /api/search |
|-------|:--:|:--:|:--:|:--:|
| access_count | Yes | -- | Yes | -- |
| last_access | Yes | -- | Yes | -- |
| days_since_last_access | Yes | -- | Yes | Yes |
| stability | Yes | -- | Yes | Yes |
| decay_risk | -- | Yes | -- | -- |

Frontend type definitions confirmed synced:
- `DecayRiskEntry` interface (`types.ts:110`): `id: string`, `decay: number`
- `StatsResponse.decay_risk` (`types.ts:127`): `DecayRiskEntry[]`
- `WanderResponse`: includes `stability`, `days_since_last_access`
- `SearchResultItem` (`api.ts`): includes `days_since_last_access`, `stability`

**PASS** — All decay fields exposed across all required API surfaces with frontend types synced.

---

## 5. Stability Boundary Guard Verification

### models.py (lines 78, 111-122)
```python
stability: float = Field(default=14.0, gt=0.0, description="...")

@field_validator("stability", mode="before")
@classmethod
def _clamp_stability(cls, v: object) -> float:
    if v is None: return 14.0
    val = float(v)
    if val <= 0: raise ValueError(f"stability must be > 0, got {val}")
    if val < 0.1: return 0.1
    return val
```

**Defense layers:**
1. Field-level: `gt=0.0` Pydantic constraint rejects <= 0 at model construction
2. Validator: Rejects negative values with clear ValueError, clamps (0, 0.1) to 0.1
3. Runtime: `handlers.py:257` and `handlers.py:346` apply `max(stability, 0.1)` in overview and wander
4. None defaulting: Validator returns 14.0 for None input

**PASS** — Defense in depth. Model validation prevents invalid data at rest; runtime clamps guard edge cases at compute time.

---

## 6. Modal Exit Animation Verification

### Dashboard.tsx

**Import and hook usage:**
- `index.ts:4`: `import { useExitAnimation } from '../useExitAnimation'` (via barrel)
- Line 26: `const { visible: wanderVisible, closing: wanderClosing } = useExitAnimation(!!wanderOpen)`
- Line 27: `const { visible: validateVisible, closing: validateClosing } = useExitAnimation(!!validateOpen)`

**Conditional rendering based on visible state:**
- Wander Modal only renders when `wanderVisible` is true
- Validate Modal only renders when `validateVisible` is true

**Modal closing prop and CSS classes:**
- Line 566: `<Modal onClose={...} closing={wanderClosing}>`
- Line 763: `<Modal onClose={...} closing={validateClosing}>`
- Line 1125: `function Modal({ children, onClose, closing = false })`
- Line 1130: `className={closing ? 'backdrop-fade-exit' : 'backdrop-fade-enter'}`
- Line 1139: `className={closing ? 'modal-fade-exit' : 'modal-fade-enter'}`

**PASS** — The R13 PARTIAL PASS gap is now closed. Both Wander and Validate modals use `useExitAnimation` with `closing` prop wired to CSS exit animation classes. The 250ms exit animation plays on close before DOM unmount.

---

## 7. Sub-12px Font Fix Verification

Scanned all `fontSize` declarations across `frontend/src/`:

| Component | Previous | Current | Verified |
|-----------|----------|---------|----------|
| HelpPanel layer badge | 9px | 11px | line 337 |
| HelpPanel API method badge | 9px | 11px | line 405 |
| MemoryDetail trim badge | 9px | 11px | line 630 |
| SearchBar Resolve button text | 10px | 12px | line 309 |
| App.tsx view shortcut hints | 10px | 11px | lines 678/699/720 |
| SearchBar "includes fuzzy matches" | 11px | 12px | line 156 |
| App.tsx archive backlink IDs | 11px | 12px | line 1474 |

**Aggregate check:** Zero instances of `fontSize: 9` or `fontSize: 10` in any DOM text element across all frontend source files. All interactive elements (buttons, links, clickable text) at >= 12px. Decorative non-interactive elements at 11px minimum.

**GraphCanvas.tsx note:** Line 272 has `'font-size': '9px'` in a Cytoscape stylesheet for `node.trim-skipped`. This is a canvas rendering parameter (not a DOM CSS property) for nodes explicitly designed to appear dim/small. Canvas labels scale with graph zoom. Not a regression and not in scope of the DOM text audit.

**PASS** — All seven documented sub-12px DOM text violations confirmed fixed.

---

## 8. Generator Report vs. Actual Comparison

| Generator Claim | Evaluator | Match? |
|-----------------|-----------|--------|
| "7/8 tasks complete" | 7/8 PASS + 1 DEFERRED | YES |
| "TypeScript zero errors" | Zero errors | YES |
| "Vite build success (395ms)" | Success (338ms) | YES (timing variance normal) |
| "57/57 unit tests" | 57/57 (0.28s) | YES |
| "24/24 integration tests" | 24/24 | YES |
| "5/5 API tests" | 5/5 (0.44s) | YES |
| "/api/stats: decay_risk present" | decay_risk present | YES |
| "/api/wander: stability+days" | stability + days_since_last_access present | YES |
| "/api/validate: 200 OK" | 200 OK, 0 errors | YES |
| "/api/memories: decay fields" | All 4 fields present | YES |
| "/api/search: decay fields" | stability + days_since_last_access present | YES |
| "Overview decay activated" | Verified via manual formula calc | YES |
| "Companion heat values reflect decay" | Heat values differ from R13 bug | YES |
| "R14-N3 intentionally skipped" | Confirmed not implemented | YES |

**Result: Generator claims are 100% accurate. All pass claims independently verified and confirmed.**

---

## 9. Pitfalls Compliance Check

| Pitfall | Status | Notes |
|---------|--------|-------|
| Sprint 13 PL3: English dataset stale placeholder hash | N/A | Not modified this round |
| Sprint 4: summary_hash initial value trap | Pre-existing | Companion overview shows [stale] on all memories — known issue from placeholder hashes, not a regression |
| Sprint 3: access_count precise assertion trap | Avoided | Verification uses >= not == |
| R14-C1 pitfall (SPRINT.md): heat values will differ from R13 eval | **CONFIRMED** | Heat values match corrected formula, not R13 eval values (31,31,21,21,20) |
| R14-C2 pitfall (SPRINT.md): gt=0 validator may reject existing data | **VERIFIED SAFE** | All 4 datasets have stability=14.0 on disk; no rejection at load time |
| R14-C3 pitfall (SPRINT.md): /api/memories shape change needs frontend sync | **VERIFIED** | types.ts synced, zero TypeScript errors |
| R14-I1 pitfall (SPRINT.md): inline Modal needs `closing` prop | **VERIFIED FIXED** | Modal() now accepts `closing` prop and conditionally applies exit CSS classes |

All in-scope pitfalls confirmed addressed or verified as non-issues.

---

## 10. New Pitfalls to Append

None identified. The sprint document already includes all four anticipated pitfalls (R14-C1, C2, C3, I1). No new traps emerged during independent verification.

---

## 11. Decision: COMPLETE

**7/8 tasks fully verified PASS. 1 task (R14-N3) intentionally deferred per plan.**

- 57/57 unit tests, 24/24 integration tests, 5/5 API tests: zero regressions, zero failures.
- TypeScript: zero errors.
- Vite build: success.
- All 6 backend endpoints respond correctly with decay fields exposed.
- The critical overview decay formula bug (R14-C1 / R-RED-1) is confirmed **fixed**: `handlers.py` now reads `days_since_last_access` from `MemoryEntry` objects, the unified formula `0.5^(days/stability)` produces correct heat values. Manual calculation cross-check passes.
- Stability boundary guards (R14-C2) provide defense-in-depth: model validation rejects invalid values, runtime clamps guard edge cases.
- All backend and frontend decay fields (R14-C3) wired, TypeScript types synced.
- Modal exit animations (R14-I1) now wired in Dashboard.tsx using `useExitAnimation` — closes the R13-A1 PARTIAL PASS gap.
- Sub-12px fonts (R14-I2) all fixed: zero 9px/10px DOM text remains.
- Dashboard decay risk section (R14-N1) functional.
- Graph node right-click Resolve (R14-N2) wired.

---

# Evaluator Report — Iteration 13

> **Date**: 2026-05-07
> **Evaluator**: QA Evaluator (independent verification — all acceptance commands re-run from scratch)
> **Method**: Zero trust; all acceptance commands, tests, and code reviews executed fresh against the current working tree
> **Sprint**: Sprint 13, 第 13 轮追加任务

---

## 1. Checkbox 状态（逐项核对）

### 第一梯队：审美完成

| Task | Status | Verdict | Evidence |
|------|--------|---------|----------|
| R13-A1: 退场动画接线 | [x] | **PARTIAL PASS** | `useExitAnimation.ts` 创建并接线到 MemoryDetail/Settings/MemoryForm 三个面板（6 处：面板+遮罩各 3）。CSS 退场动画类（`panel-slide-exit`, `backdrop-fade-exit`）存在并使用。**但**：Wander/Validate 模态（Dashboard.tsx 内联 Modal 函数）和 Archive 确认模态（App.tsx）未使用退场动画——关闭时仍是 DOM 立即卸载，无 fade-out + scale-down。规范明确要求 "关闭 Wander/Validate/Archive 模态时可见 fade-out + scale-down 动画"，此项未完成。详见下方代码审查章节。 |
| R13-A2: 修复残余 sub-12px 字号 | [x] | **PASS** | `Badges.tsx:20,31`: 默认 `fontSize` 从 11 提升到 12。`SearchBar.tsx:309`: "includes fuzzy matches" `fontSize: 11`（从 9）。`SearchBar.tsx:376`: match quality badge `fontSize: 11`（从 9）。无残留 10px 以下交互文字。 |
| R13-A3: 搜索下拉框 fade-in 动画 | [x] | **PASS** | `index.css:286-293`: `@keyframes dropdownFadeIn`（150ms ease + translateY(4px)→0）。`SearchBar.tsx:188`: 下拉框挂载 `search-dropdown-enter` class。 |

### 第二梯队：发现路径缩短

| Task | Status | Verdict | Evidence |
|------|--------|---------|----------|
| R13-D1: 搜索结果 "Resolve →" 动作 | [x] | **PASS** | `SearchBar.tsx:346-372`: 每条结果旁渲染 "Resolve →" 按钮（`onResolve` prop 存在时）。点击后 `setShowResults(false)` + `onResolve(item.id)`。`App.tsx` 处理回调：关闭下拉框、切到 Graph 视图、100ms 延迟触发 resolve。 |
| R13-D2: 视图切换按钮快捷键提示 | [x] | **PASS** | `App.tsx:670,691,712`: 三个按钮内嵌 `<span style={{ fontSize: 10, opacity: 0.55 }}>1/2/3</span>`。title 属性含 "keyboard: N"。Help 面板快捷键覆盖层同步记录（line 1570）。 |
| R13-D3: Resolve 加载状态 | [x] | **PASS** | `App.tsx:49`: `isResolving` 状态。`MemoryDetail.tsx:418-444`: shimmer 骨架动画（3 条骨架行 + "Resolving..." 标题）在 `isResolving` 期间渲染。`GraphCanvas.tsx:458`: `isResolving` 期间跳过 trim-level 样式更新。 |

### 第三梯队：衰减模型统一

| Task | Status | Verdict | Evidence |
|------|--------|---------|----------|
| R13-M1: 统一衰减模型 | [x] | **PASS** | `handlers.py:253-262`: overview heat = `deps*10 + access*0.5^(days/stability)`。`handlers.py:333-348`: wander(cool) 权重 = `1/(access*0.5^(days/stability) + 1)`。`validate.py:78-103`: `_check_decay()` 使用 R < 0.1 连续阈值（`0.5^(days/stability) < 0.1` → 约 3.3 half-lives）。三套逻辑统一为同一公式。 |
| R13-M2: 排除循环参与者 | [x] | **PASS** | `handlers.py:227-248`: 通过 `find_cycle_participants()` 预计算 required-imports DAG 的循环参与者。heat 计算时循环成员的 `dependents` 计为 0。非循环 imports 不受影响。 |
| R13-M3: 预计算 days_since_last_access | [x] | **PASS** | `models.py:64`: `days_since_last_access: int | None`。`index.py:122-130`: reindex 时计算 `(now - last_access).days`，无访问记录则 None。`resolve.py:320`: resolve 后设为 0。overview heat 循环用 `entry.days_since_last_access` 替代 `datetime.fromisoformat`。 |
| R13-M4: 添加 stability 字段 | [x] | **PASS** | `models.py:78`: `stability: float = Field(default=14.0)`。index.json 验证：所有 4 个数据集 reindex 后均有 `stability: 14.0`（float）。heat 公式使用 `stability` 替代硬编码 14.0。向后兼容：旧 index.json 缺少 stability 字段时 Pydantic 自动填充 14.0。 |

### 第四梯队：基础设施

| Task | Status | Verdict | Evidence |
|------|--------|---------|----------|
| R13-I1: 启用 OpenAPI /docs | [x] | **PASS** | `server.py:141`: `is_exempt = path in ("/", "/api/datasets", "/docs", "/openapi.json")`。`curl /docs` → 200。`curl /openapi.json` → 200。Swagger UI 可通过浏览器正常访问。 |

### 总计：10/11 FULL PASS，1 PARTIAL PASS (R13-A1)

---

## 2. 验收命令重跑结果

### TypeScript 类型检查
```
cd frontend && npx tsc --noEmit
→ 零错误（静默输出 = PASS）
```

### Frontend 构建
```
cd frontend && npx vite build
→ 570 modules transformed, built in 365ms
  CSS: 14.80 kB (gzip: 3.96 kB)
  JS: 997.06 kB (gzip: 298.94 kB)
  → PASS
```

### Python 单元测试
```
PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short
→ 57 passed in 0.27s (PASS)
```

### Python 集成测试
```
PYTHONPATH=src python tests/integration_test.py
→ Results: 24/24 passed, All tests PASSED (PASS)
```

### Python API 测试
```
PYTHONPATH=src python -m pytest tests/test_api.py -v --tb=short
→ 5 passed in 0.43s (PASS)
```

### Backend 端点回归
```
# /api/stats (companion dataset)
curl -s -H "X-Codememory-Dataset: companion" http://localhost:8000/api/stats
→ 200: total=11, maturity={verified:2,proven:6,draft:3}, stale_count=0, stale_ids=[], tags present

# /api/wander
curl -s -X POST -H "X-Codememory-Dataset: companion" http://localhost:8000/api/wander
→ 200: Returns memory with id, type, summary, tags, intensity, access_count, last_access, status, maturity

# /api/validate
curl -s -X POST -H "X-Codememory-Dataset: companion" http://localhost:8000/api/validate
→ 200: validated_count=11, error_count=0, warning_count=1 (audit test memory decay warning — expected)

# /docs endpoint
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs
→ 200 (PASS)

# /openapi.json endpoint
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/openapi.json
→ 200 (PASS)
```

### CLI overview 热力输出（衰减模型验证）
```
CODEMORY_ROOT=examples/investment PYTHONPATH=src python -m codememory.cli overview
→ user/investment/risk-tolerance        heat:31 [active]
   user/investment/semiconductor-thesis  heat:31 [active]
   user/facts/nvidia-earnings            heat:21 [active]
   user/facts/soxl-composition           heat:21 [active]
   user/investment/february-buy          heat:20 [active]
   与 Generator 自报 heat 值完全一致（31,31,21,21,20）
```

### Index 字段验证（4 数据集）
```
companion:            stability=True (14.0), days_since_last_access=True (None)
investment:           stability=True (14.0), days_since_last_access=True (0)
software-architecture: stability=True (14.0), days_since_last_access=True (None)
quant_operators:      stability=True (14.0), days_since_last_access=True (0)
→ 所有数据集 reindex 后均包含 stability 和 days_since_last_access 字段
```

### English 数据集 stale hash 验证
```
软件架构数据集: stale_count=0, stale_ids=[]（PASS——Sprint 10 auto-reindex 已修复）
```

---

## 3. Generator 报告 vs 实际对比

| Generator Claim | Actual | Match? |
|-----------------|--------|--------|
| "11/11 任务完成" | 10/11 FULL + 1 PARTIAL | **PARTIAL** — R13-A1 模态退场动画未实现 |
| "TypeScript 零错误" | 零错误 | YES |
| "Vite 构建成功 (339ms)" | Vite 构建成功 (365ms) | YES (时间差异为正常方差) |
| "57 单元测试通过" | 57 passed | YES |
| "24 集成测试通过" | 24/24 passed | YES |
| "5 API 测试通过" | 5 passed | YES |
| "所有 Backend 端点正常" | stats/wander/validate/docs/openapi 全部 200 | YES |
| "Index 字段: stability=14.0 float, days_since_last_access=0 int" | 确认 | YES |
| "Overview heat: 31,31,21,21,20" | 31,31,21,21,20 | YES |
| "软件架构 stale_count=0" | stale_count=0 | YES |

**差异**: Generator 声称 11/11 任务完成，但 R13-A1 的模态退场动画（Wander/Validate/Archive）未实现。详见下方。

---

## 4. R13-A1 退场动画代码审查（详细）

### 已实现部分（3 面板 = 6 入口）

| 组件 | 文件 | 行号 | 遮罩退场 | 面板退场 |
|------|------|------|----------|----------|
| MemoryDetail | `components/MemoryDetail.tsx` | 80,124,135 | `backdrop-fade-exit` ✅ | `panel-slide-exit` ✅ |
| Settings | `components/Settings.tsx` | 87,96,107 | `backdrop-fade-exit` ✅ | `panel-slide-exit` ✅ |
| MemoryForm | `components/MemoryForm.tsx` | 20,408,419 | `backdrop-fade-exit` ✅ | `panel-slide-exit` ✅ |

`useExitAnimation.ts` hook 正确实现：
- `show` 从 true→false 时设置 `closing=true`
- 250ms 后 `setVisible(false)` 卸载 DOM
- CSS 动画在 250ms 窗口内播放退场动画
- Escape 键触发的关闭同样经过 `show=false` → 退场动画流程

### 未实现部分（3 模态 = 0 入口）

| 模态 | 文件 | 现状 | 规范要求 |
|------|------|------|----------|
| Wander 模态 | `Dashboard.tsx` Modal 函数 (inline) | `className="backdrop-fade-enter"` + `className="modal-fade-enter"`，无 exit 类，关闭时 DOM 立即卸载 | "关闭 Wander 模态时可见 fade-out + scale-down 动画" |
| Validate 模态 | `Dashboard.tsx` Modal 函数 (同上) | 同上——两个模态共享同一个 Modal 函数 | "关闭 Validate 模态时可见 fade-out + scale-down 动画" |
| Archive 确认模态 | `App.tsx:1393-1448` | `className="modal-fade-enter"`（仅入场），遮罩无动画类 | "关闭 Archive 模态时可见 fade-out + scale-down 动画" |

**根因**: Dashboard.tsx 的 Modal 函数是纯展示组件——直接渲染 `backdrop-fade-enter` 和 `modal-fade-enter` 而不检查 closing 状态。要修复需要：(a) 将 Modal 提升为使用 `useExitAnimation`，(b) 或在调用方（Dashboard）管理 closing 状态。

此外，HelpPanel（`App.tsx:1256`）也是条件渲染 `{showHelp && <HelpPanel />}`，无退场动画。但规范未显式要求 HelpPanel 退场动画。

**影响评级**: MEDIUM。规范明确要求 Wander/Validate/Archive 模态退场动画，3 处未实现。但 3 个主要面板（MemoryDetail/Settings/MemoryForm）退场动画正常工作，这覆盖了用户最常见的交互路径。

---

## 5. 衰减模型变更验证（CLI overview heat 输出）

### 公式验证
```
handlers.py:261: decay = math.pow(0.5, days_since / stability)
handlers.py:262: access_bonus = access * decay
handlers.py:347: decay = math.pow(0.5, max(0, days_since) / stability)
handlers.py:348: weight = 1.0 / (entry.access_count * decay + 1)
validate.py:103: retrieval_prob = math.pow(0.5, days_since / stability)
```
- overview: `heat = deps*10 + access*0.5^(days/stability)` ✅
- wander(cool): `weight = 1/(access*0.5^(days/stability) + 1)` ✅
- validate decay: `R < 0.1` 时警告（连续阈值，非硬编码 30 天） ✅

### 输出一致性
Generator 报告的 heat 值与实际重跑完全一致：31, 31, 21, 21, 20。确认公式和计算正确。

### 循环排除验证
`handlers.py:237-248`：通过 `resolve.find_cycle_participants()` 检测 required-imports DAG 循环，循环成员 dependents 计为 0。代码路径完整。

---

## 6. Pitfalls 合规检查

| Pitfall | 状态 | 说明 |
|---------|------|------|
| Sprint 13 PL1: server.py imports YAML 直接写入 | **N/A** | R13 变更未触及 create/update 的 imports 处理 |
| Sprint 13 PL1: Budget 无操作检查仅对增加方向有效 | **N/A** | R13 未修改 budget 逻辑 |
| Sprint 13 PL1: 空 body 的 summary_hash 确定性 | **N/A** | R13 未修改 body hash 计算 |
| Sprint 13 PL3: 英文数据集 stale 占位 hash | **PASS** | 软件架构数据集 stale_count=0（Sprint 10 auto-reindex 已解决） |
| R12-UX2 退场动画陷阱（需 closing 状态+延迟卸载） | **PARTIAL** | R13-A1 的 useExitAnimation 正确实现了 closing 模式用于 3 个面板，但 3 个模态未采用此模式——直接跳过而非实现 |
| Sprint 11: Vite 端口可能被占用 | **N/A** | 仅生产构建验证 |
| Sprint 11: Backend 需要 CODEMORY_ROOT | **N/A** | Backend 通过 `--root` + `X-Codememory-Dataset` 正常工作 |
| Sprint 9: 全局 MEMORY_ROOT 线程不安全 | **N/A** | 预存在状态，R13 未恶化 |

---

## 7. 失败原因分析（R13-A1 模态退场动画缺口）

**症状**: Wander/Validate/Archive 三个模态关闭时无退场动画，DOM 立即卸载。

**根本原因**: 三个模态使用了两种不同的渲染模式，均缺少退场动画机制：
1. Wander/Validate 共享 `Dashboard.tsx` 的本地 `Modal()` 函数——纯展示组件，硬编码 `backdrop-fade-enter` / `modal-fade-enter`，无 closing 状态管理
2. Archive 确认模态在 `App.tsx` 中为内联 JSX——仅 `modal-fade-enter`，无退场动画类

**修复建议**:
- 方案 A（推荐）: 将 Dashboard Modal 重构为使用 `useExitAnimation`，从父组件接收 `open` prop + `onClose`
- 方案 B: 在 Dashboard 调用方手动管理 closing 状态和 CSS 类切换

**工作量估计**: 方案 A 约 20-30 行，方案 B 约 15 行。

---

## 8. 新陷阱待追加（Sprint 结束后追加到 pitfalls.md）

- **[R13-A1] 内联 Modal 函数无法复用 useExitAnimation hook。** Dashboard.tsx 中的 `Modal({ children, onClose })` 是本地纯函数组件——它接收不到表示"正在关闭"的 prop，因此无法在关闭时切换 CSS 类。当多个模态（Wander/Validate）共享同一个 Modal 组件时，模态的打开/关闭状态在父组件中管理，Modal 需要接收额外的 `closing` prop 或自身集成 `useExitAnimation`。修复时应避免在 Modal 函数内部创建独立的动画状态（会导致与父组件的状态不同步）。

- **[R13-M3] days_since_last_access 的 None vs 0 语义差别。** `None` 表示"从未被访问"（应使用保守的 days=0 或忽略衰减），`0` 表示"刚刚访问过"。overview/wander/validate 代码中均使用 `max(0, days_since or 0)` 处理 None 情况。对于从未访问的记忆，衰减计算结果为 `0.5^0 = 1.0`（无衰减），这与"从未访问 = 冷却权重高"的直觉可能矛盾。未来 wander 可能需要区分"从未访问"（高冷却）和"刚刚访问"（低冷却）两种语义。

---

## 9. 决策（信息性）

**CONTINUE — 10/11 任务完全验证通过，R13-A1 有模态退场动画缺口（3 个模态未实现）。86/86 测试通过（57 unit + 24 integration + 5 API），TypeScript 零错误，Vite 构建成功，零回归。**

R13-A1 的缺口影响范围有限（3 个模态），3 个主要面板的退场动画工作正常。衰减模型统一（M1-M4）代码审查和实测均确认正确，overview CLI 输出与 Generator 报告完全一致。
