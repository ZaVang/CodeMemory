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
| R13-M3: 预计算 days_since_last_access | [x] | **PASS** | `models.py:64`: `days_since_last_access: int \| None`。`index.py:122-130`: reindex 时计算 `(now - last_access).days`，无访问记录则 None。`resolve.py:320`: resolve 后设为 0。overview heat 循环用 `entry.days_since_last_access` 替代 `datetime.fromisoformat`。 |
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
CODEMEMORY_ROOT=examples/investment PYTHONPATH=src python -m codememory.cli overview
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
