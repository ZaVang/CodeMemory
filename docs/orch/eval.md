# Evaluator Report — Iteration 17

**Date**: 2026-05-07
**Evaluator**: Independent QA (non-Generator)
**Theme**: 整顿 (Consolidation) — 6/6 tasks, 86/86 tests, zero regressions

---

## Checkbox 状态

All 6 tasks verified as `[x]` in `docs/plans/SPRINT.md`:

| Task | Description | Status | Verified |
|------|-------------|--------|----------|
| R17-CR1 | Fix dataset default self-reinforcement regression | [x] | PASS |
| R17-UX1 | Graph node label font-size 11px -> 12px | [x] | PASS |
| R17-UX2 | List view horizontal padding restore | [x] | PASS |
| R17-G1 | Confirm SearchBar Resolve tooltip | [x] | PASS |
| R17-G2 | Expose stability_source in API responses | [x] | PASS |
| R17-T1 | FastAPI on_event -> lifespan migration | [x] | PASS |

---

## 验收命令重跑结果 (Independent)

### TypeScript Compilation
```
cd frontend && npx tsc --noEmit
```
**PASS** — Zero errors.

### Vite Build
```
cd frontend && npx vite build
```
**PASS** — Built in 326ms. Output: index.html 0.48 kB, CSS 14.82 kB, JS 1,005.01 kB.

### Python Unit Tests
```
PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short
```
**PASS** — 57/57 passed (0.28s).

### Python Integration Tests
```
PYTHONPATH=src python tests/integration_test.py
```
**PASS** — 24/24 passed.

### API Tests
```
PYTHONPATH=src python -m pytest tests/test_api.py -v --tb=short
```
**PASS** — 5/5 passed (0.41s).

**Total executable tests: 86/86 (57 unit + 24 integration + 5 API)** — zero regressions.

---

## Dataset 默认值验证 (Live Server)

Backend started on port 8722, verified with curl:

| Test Case | Expected | Actual | Result |
|-----------|----------|--------|--------|
| No header | `current: investment` | `current: investment` | PASS |
| X-Codememory-Dataset: companion | `current: investment` | `current: investment` | PASS |
| X-Codememory-Dataset: nonexistent | `current: investment` | `current: investment` | PASS |

All three cases return `"current": "investment"` — the server's true default, not influenced by any client header. The self-reinforcement regression is definitively fixed.

Root cause fixes verified in source:
- `backend/routers/stats.py:140`: Uses `DEFAULT_DATASET` constant directly, not `current_dataset.get()`
- `backend/server.py:81-85`: Middleware skips ContextVar write on exempt paths (`if not is_exempt:`)
- `frontend/src/api.ts:11`: `_currentDataset` initializes to `''` (empty string), not `'companion'`

---

## Lifespan 迁移验证

### Source Code Audit
- `backend/server.py:17`: `from contextlib import asynccontextmanager` — imported
- `backend/server.py:45-46`: `@asynccontextmanager` + `async def lifespan(app: FastAPI)` — defined
- `backend/server.py:64`: `FastAPI(..., lifespan=lifespan)` — wired into app creation
- `backend/server.py`: Zero occurrences of `@app.on_event("startup")` (only in comments on lines 8, 39)

### Runtime DeprecationWarning Check
```
PYTHONPATH=src CODEMEMORY_ROOT=examples/investment python -c "
import warnings; warnings.simplefilter('error');
import importlib; import backend.server;
print('SUCCESS: No DeprecationWarning on import')
"
```
**PASS** — No DeprecationWarning raised.

---

## Source-Level Verification of Remaining Tasks

### R17-UX1: Graph Node Font-Size
- `frontend/src/components/GraphCanvas.tsx:158`: `'font-size': '12px'` — confirmed 12px
- No remaining `'font-size': '11px'` in the file.

### R17-UX2: List View Padding
- `frontend/src/components/MemoryList.tsx`: 4 locations now use `32px` horizontal padding:
  - Line 149: `padding: '16px 32px'` (filter bar)
  - Line 195: `padding: '0 32px'` (table wrapper)
  - Line 351: `padding: '12px 32px'` (pagination bar)
  - Lines 469, 475: `padding: '16px 32px'` / `padding: '0 32px'` (skeleton variants)
- No remaining `24px` horizontal padding in the file.

### R17-G1: SearchBar Resolve Tooltip
- `frontend/src/components/SearchBar.tsx:381`: `title={`Resolve this memory's dependency graph into a structured context`}` — confirmed present
- This is a native HTML `title` attribute on the button element, which browsers render as a tooltip regardless of CSS overlay/z-index context.

### R17-G2: stability_source in API Responses
- `backend/routers/memories.py`: 6 locations append `stability_source` field
  - Line 78: `GET /api/memories` list
  - Line 157: `GET /api/memories/{id}` detail
  - Line 247: `POST /api/memories` create response
  - Line 331: `PUT /api/memories/{id}` update response
  - Line 373: `POST /api/memories/{id}/touch` response
- `backend/routers/search.py`: 2 locations append `stability_source` field
  - Line 317: search index path
  - Line 340: search full-text path
- Live verification: `GET /api/memories?limit=2` and `POST /api/search` both return `stability_source` field.

---

## Generator 报告 vs 实际对比

| Metric | Generator Report | Independent Verification | Match? |
|--------|-----------------|--------------------------|--------|
| TypeScript errors | 0 | 0 | YES |
| Vite build | success | success (326ms) | YES |
| Unit tests | 57/57 | 57/57 | YES |
| Integration tests | 24/24 | 24/24 | YES |
| API tests | 5/5 | 5/5 | YES |
| Dataset no-header | investment | investment | YES |
| Dataset companion header | investment (not polluted) | investment (not polluted) | YES |
| Dataset nonexistent header | not tested | investment (not polluted) | YES (bonus) |
| DeprecationWarning | none | none | YES |
| stability_source in responses | present | present | YES |
| on_event removed | yes | yes (only in comments) | YES |
| GraphCanvas font-size | 12px | 12px | YES |
| MemoryList padding | 32px | 32px (4 locations) | YES |
| SearchBar tooltip title | present | present (line 381) | YES |

**Verdict**: Generator report is fully accurate. No discrepancies found.

---

## 决策：COMPLETE

All 6 Round 17 tasks are independently verified as complete:
- 6/6 checkboxes verified
- 86/86 executable tests pass with zero regressions
- Dataset default value regression is confirmed fixed at all three levels (frontend init, middleware exempt guard, endpoint constant)
- Lifespan migration is complete with no DeprecationWarning
- stability_source is serialized across all 6 API response paths
- UX fixes (font-size 12px, padding 32px) confirmed in source
- SearchBar Resolve tooltip confirmed in source

**No blocking issues. No regressions. Generator's self-report matches independent verification exactly.**
