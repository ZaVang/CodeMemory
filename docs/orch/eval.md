# Evaluator Report — Iteration 11

> **Date**: 2026-05-07
> **Evaluator**: QA Evaluator (independent verification — all acceptance commands re-run from scratch)
> **Method**: Zero trust; all acceptance commands, tests, and code reviews executed fresh against the current working tree

---

## 1. Acceptance Commands (Re-run from Scratch)

| # | Command | Result | Details |
|---|---------|--------|---------|
| 1 | `curl -s -H "X-Codememory-Dataset: companion" http://localhost:8000/api/stats \| python -m json.tool` | **PASS** | total: 10, stale_count: 0, maturity/stats/tags all present |
| 2 | `curl -s -X POST -H "X-Codememory-Dataset: companion" http://localhost:8000/api/wander \| python -m json.tool` | **PASS** | Returns memory with id, summary, tags, intensity, access_count, last_access |
| 3 | `curl -s -X POST -H "X-Codememory-Dataset: companion" http://localhost:8000/api/validate \| python -m json.tool` | **PASS** | validated_count: 10, error_count: 0, warning_count: 0 |
| 4 | `cd frontend && npx tsc --noEmit` | **PASS** | Zero TypeScript errors |
| 5 | `cd frontend && npx vite build` | **PASS** | Built in 377ms (569 modules, CSS 13.85 kB, JS 989.76 kB) |
| 6 | `PYTHONPATH=src python -m pytest tests/unit/ -v --tb=short` | **PASS** | 57/57 passed in 0.32s |
| 7 | `PYTHONPATH=src python tests/integration_test.py` | **PASS** | 24/24 passed |
| 8 | `PYTHONPATH=src python -m pytest tests/test_api.py -v --tb=short` | **PASS** | 5/5 passed in 0.46s |

**8/8 acceptance commands pass. Zero regressions across 57+24+5 = 86 total tests.**

---

## 2. Checkbox Status (Per-Task Verdict)

### Tier 1 — Critical Bug Fix + Key UX

| Task | Status | Verdict | Evidence |
|------|--------|---------|----------|
| R11-B1: Dataset switching race condition | [x] | **PASS** | `App.tsx:266-283`: `handleSwitchDataset` calls `switchDataset(name)` (backend), then `setCurrentDataset(name)` + `setRefreshTrigger(...)` (triggering Dashboard/List reload). Dataset is set in API layer via `useEffect` at line 252-256 before any child component fetches. Dashboard and List both react to `refreshTrigger` prop for data reload. |
| R11-B2: Modal stacking prevention | [x] | **PASS** | `Dashboard.tsx:46` (Wander handler calls `setValidateOpen(false)`) and `Dashboard.tsx:58` (Validate handler calls `setWanderOpen(false)`). Both handlers close the other's modal before opening their own. |
| R11-UX1: Fix Ctrl+K keyboard shortcut | [x] | **PASS** | `App.tsx:524-535`: Ctrl+K handler focuses `document.getElementById('global-search-input')`. Handles dashboard mode by switching to graph view first (50ms setTimeout). Respects input focus state. |
| R11-UX2: Reindex feedback toast | [x] | **PASS** | `Dashboard.tsx:68-87`: `handleReindex` sets `reindexMessage` state with "Reindexed N memories" (success) or "Reindex failed: ..." (failure). Auto-dismiss timers (4s success, 6s failure). Toast rendered at lines 110-143 with color-coded styling and manual X dismiss. |
| R11-UX3: Search filtering Graph nodes | [x] | **PASS** | `GraphCanvas.tsx:379-405`: Cytoscape `useEffect` watches `searchText`. Adds `highlighted` class to matching nodes, `dimmed` class to non-matching. Clear search restores all. Styles at lines 225-233 define `dimmed` (opacity 0.15) and `highlighted` (opacity 1) selectors. |

### Tier 2 — High-Value Improvements

| Task | Status | Verdict | Evidence |
|------|--------|---------|----------|
| R11-UX4: Graph loading skeleton | [x] | **PASS** | `GraphCanvas.tsx:531` (conditional rendering) and lines 616-690: `GraphSkeleton` component with 10 placeholder circles in DAG arrangement, connecting SVG edge lines with `edge-shimmer` gradient, plus `skeleton-shimmer` animation on nodes. |
| R11-UX5: Disable CREATE on validation failure | [x] | **PASS** | `MemoryForm.tsx:864`: CREATE/SAVE button `disabled` prop is true when `(saving \|\| loading \|\| (error !== null && (error === 'ID is required' \|\| error.startsWith('ID must contain') \|\| error.startsWith('Intensity must be'))))`. `clearValidationError` (lines 198-205) re-enables on input change. |
| R11-UX6: List summary hover tooltip | [x] | **PASS** | `MemoryList.tsx:337-355`: `TruncatedCell` component uses `useRef` on `<span>`, checks `scrollWidth > clientWidth`, sets `title` attribute only when truncated. |
| R11-UX7: Improved error messages + Retry | [x] | **PASS** | `api.ts:30-40`: `_humanReadableError()` maps status codes to human-readable messages ("Bad request — check your input and try again", "Validation failed — check your input and try again", etc.). `App.tsx:148-152`: `handleRetryNetwork` increments `refreshTrigger` to reload all data. `App.tsx:963-1020`: Network error banner shows human-readable error + "Retry" button + manual X dismiss. |

### Tier 3 — Polish

| Task | Status | Verdict | Evidence |
|------|--------|---------|----------|
| R11-P1: Remove header declaration text | [x] | **PASS** | `App.tsx:701`: Old 10px italic text removed, replaced with `title="Stats, validation, and reindex apply to the selected dataset"` attribute on the dataset `<select>` element. Comment at line 728 confirms: `Dataset disclaimer moved to tooltip on the select element (R11-P1)`. |
| R11-P2: Remove duplicate memId in Dashboard stale | [x] | **PASS** | `Dashboard.tsx:393-441`: Stale section shows each memId exactly once — a single styled div with the ID (lines 411-420) and a "stale" badge (lines 422-435). No duplicate monospace subtitle. |
| R11-P3: Search "no results" empty state | [x] | **PASS** | `SearchBar.tsx:258-285`: When `hasSearched && results.length === 0`, shows "No memories found matching \<query\>" with actionable advice "Try broadening your search or using different keywords." |
| R11-P4: MCP tool read/write annotations | [ ] | **FAIL** | `src/codememory/mcp_server.py`: The `TOOLS` list (lines 55-187) contains 5 tools. None of them have a `readOnlyHint` or `read_only` property. Verified with programmatic check: `has_readOnlyHint: false` for all 5 tools. |

---

## 3. Summary

| Tier | Total | Passed | Failed |
|------|-------|--------|--------|
| Tier 1 (Critical + UX) | 5 | 5 | 0 |
| Tier 2 (High-Value) | 4 | 4 | 0 |
| Tier 3 (Polish) | 4 | 3 | 1 |
| **Total** | **13** | **12** | **1** |

---

## 4. Generator Code Review vs Actual Comparison

### Files Changed (Reported by Generator)
- `frontend/src/App.tsx` — modal stacking, Ctrl+K, Reindex feedback, header text removal
- `frontend/src/api.ts` — human-readable error messages
- `frontend/src/components/Dashboard.tsx` — Reindex toast, modal stacking, stale display fix
- `frontend/src/components/MemoryForm.tsx` — validation-based button disable
- `frontend/src/components/MemoryList.tsx` — list skeleton, truncated cell tooltip

### Files Changed (Actually Observed)
In addition to the above, the following files also contain Iteration 11 changes:
- `frontend/src/components/GraphCanvas.tsx` — search filtering (R11-UX3), graph loading skeleton (R11-UX4)
- `frontend/src/components/SearchBar.tsx` — search "no results" empty state (R11-P3)

### Unchanged Files (Where Changes Were Expected)
- `src/codememory/mcp_server.py` — SHOULD have been modified for R11-P4 but no changes made

---

## 5. Pitfalls Compliance Check

Existing pitfalls reviewed against the Generator's changes:

| Pitfall | Status | Notes |
|---------|--------|-------|
| Budget no-op check only for increase direction (Sprint 13 PL1) | **N/A** | Not related to any R11 task |
| Async operation race conditions (Iteration 11 plan) | **PASS** | R11-B1 correctly sequences `switchDataset` → `setCurrentDataset` → `setRefreshTrigger`. The API layer's `_currentDataset` is set before any data-fetching effect can fire. |
| Sprint 11: Vite port may be taken | **N/A** | Dev server not started for this evaluation; build is port-independent |
| Sprint 11: Tailwind v4 uses CSS @theme | **N/A** | No Tailwind config changes in this iteration |
| Sprint 11: Backend needs CODEMORY_ROOT | **PASS** | Backend running correctly with the `--root` startup parameter |

### No new pitfalls identified from code review.

---

## 6. Failure Analysis

### R11-P4: MCP tool read/write annotations — NOT IMPLEMENTED

**What was expected**: The MCP server's `TOOLS` list should include `readOnlyHint` (or equivalent property) for each tool. `resolve_memory`, `overview`, `wander`, `focus` should be annotated as read-only; `snapshot` as write.

**What was found**: The `TOOLS` list in `mcp_server.py` (lines 55-187) has 5 tools defined, none with `readOnlyHint`. A Python inspection confirms `has_readOnlyHint: false` for all 5 tools.

**Fix direction**: Add `"readOnlyHint": true` to the 4 read-only tools and `"readOnlyHint": false` to `snapshot`. This is a ~10-line change in `mcp_server.py` — 5 additions to the tool definition dicts.

**Impact**: Low. The MCP specification's `readOnlyHint` is advisory — MCP clients work fine without it. However, the annotation is useful for clients to display tool safety information to users. This is the only remaining task from the Iteration 11 sprint.

---

## 7. New Pitfall Candidates

None identified. All code changes are straightforward and don't introduce subtle patterns that future Generators might trip over.

---

## 8. Decision (Informational, does not terminate loop)

**COMPLETE — 12/13 tasks verified, zero regressions, 86/86 tests passing.**

The single outstanding task (R11-P4, MCP tool read/write annotations) is a 10-line documentation-level change in `mcp_server.py` that has no effect on existing functionality or any other component. It can be picked up as a trivial addition in Iteration 12 or completed as a quick follow-up fix.
