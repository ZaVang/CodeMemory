# CodeMemory -- Product Evolution Audit Report

**Date:** 2026-05-07
**Reviewer:** Product Evolution Reviewer (Product Strategy)
**Build:** Post-Round 14 (62119d8), following Round 14 completion
**Previous score:** 7.8/10 (post-Round 13)
**Round 14 eval:** 7/8 PASS, 1 INTENTIONALLY DEFERRED (N3)
**Datasets available:** companion (11), investment (10), software-architecture (11), quant_operators (62)
**Methodology:** Full source code review (handlers.py C1 fix, models.py C2 guards, server.py C3 API exposure, search.py output extension, Dashboard.tsx N1 + I1 wiring, App.tsx N2 context menu), live API testing (6 endpoints verified, /docs 200, decay fields confirmed in all responses), competitive intelligence update (Mem0 April 2026 algorithm, Zep/Graphiti MCP server, paradigm-memory 28 tools, Letta Code), code-quality verification (86/86 tests pass, TypeScript zero errors, Vite build 338ms).

---

## Executive Summary

**Product Evolution Maturity Score: 8.3 / 10** (up from 7.8, +0.5)

Round 14 is the build where CodeMemory stopped pretending. For three rounds, the unified decay model (`0.5^(days/stability)`) was a theoretical promise -- the code was written, the tests passed, the fields were populated, but the formula was never actually activated in the overview path. Round 14 fixed that. The flagship R13 feature now works on all three consumption paths (overview, wander, validate). This is the difference between "the feature exists in source code" and "the feature exists in the user experience."

The +0.5 score increase reflects four substantive improvements:

| Area | Pre-R14 | Post-R14 | Impact |
|------|---------|----------|--------|
| **Decay correctness** | Formula broken in overview path (C1 bug) | Formula active on all 3 paths | Correctness: silent failure -> verified working |
| **Stability safety** | `stability=0` crashed with ZeroDivisionError | Guarded by Pydantic validator + runtime clamps | Reliability: crash-prone -> crash-proof |
| **Polish completion** | 3 of 6 close points had exit animations; 7 elements sub-12px | All 6 close points animate; all fonts >=11px | Polish: incomplete -> complete |
| **Decay visibility** | Decay model invisible (pure backend) | API exposes stability/decay fields; Dashboard shows decay risk | Infrastructure: invisible -> API-accessible |

The score didn't move higher because the three structural gaps that block external adoption remain untouched: full-text body search (the single biggest functional gap vs every competitor), zero frontend test coverage (the highest-risk technical debt), and READ-ONLY MCP tools (the agentic loop is half-closed). These were correctly deferred in the Round 14 negotiation and remain the product's glass ceiling.

**Ready to show to early users?** For developer early adopters who understand the explicit-DAG model -- yes, conditionally. The core loop works correctly, the UI is polished, the API is documented, and the unique differentiators (DAG resolve + time decay) are operational. For non-developer knowledge workers -- no. The missing full-text body search means their first search will fail to find content in memory bodies, and the lack of any onboarding experience means the "aha moment" is still buried behind manual exploration.

---

## Phase 1: Core Completeness -- What Round 14 Delivered

### 1.1 Round 14 Task Verification (Eval Confirmed)

| Task | Status | Evidence |
|------|--------|----------|
| **C1: Fix overview decay pipeline bug** | PASS | `handlers.py:256` reads from `MemoryEntry` (not search dict). `search.py:85-86` outputs `days_since_last_access` + `stability`. Heat values confirmed different from old formula. |
| **C2: Add stability boundary guards** | PASS | `models.py:78`: `stability: float = Field(default=14.0, gt=0.0)`. `models.py:111-122`: `@field_validator` rejects <=0, clamps <0.1. Runtime `max(stability, 0.1)` safety clamps in overview + wander. |
| **C3: Expose decay fields in API** | PASS | `/api/memories`: all 4 decay fields present. `/api/stats`: `decay_risk` array present. `/api/search`: `days_since_last_access` + `stability`. `/api/wander`: same. `types.ts`: `DecayRiskEntry` synced. |
| **I1: Wire modal exit animations** | PASS | `Dashboard.tsx` imports `useExitAnimation`, applies to wander/validate states. `Modal()` accepts `closing` prop, applies `modal-fade-exit` / `backdrop-fade-exit` CSS classes. Archive modal wired in `App.tsx`. |
| **I2: Fix all sub-12px fonts** | PASS | Zero `fontSize: 9` or `fontSize: 10` in DOM UI text. All 7 documented violations fixed. All interactive elements >=12px. |
| **N1: Dashboard decay risk** | PASS | `Dashboard.tsx:455-521`: Decay Risk `SectionCard` reads `stats.decay_risk`, shows count + top 3 IDs with R values + "N more at risk" overflow. |
| **N2: Graph Resolve context menu** | PASS | `App.tsx:465`: `handleResolveFromContext` callback. `App.tsx:1326`: `<ContextMenuItem label="Resolve">` in graph node right-click menu. |
| **N3: Remove List local filter bar** | DEFERRED | Intentionally skipped per plan. |

### 1.2 The C1 Bug: A Post-Mortem

The C1 bug is worth memorializing because it reveals a pattern that threatens future correctness. Here is what happened:

1. **R13** introduced `days_since_last_access` as a precomputed field on `MemoryEntry` objects in `index.json`.
2. `handle_overview()` reads memory data from the search result dict (a lightweight dict returned by `search()`), NOT from the `MemoryEntry` Pydantic model.
3. `search()` builds its output dict by manually copying fields one-by-one (search.py lines 73-86). In R13, `days_since_last_access` was not in the copy list.
4. `handle_overview()` at line 258 attempted `r.get("days_since_last_access")` from the search dict -- which always returned `None`.
5. When `days_since_last_access` is `None`, the overview heat formula falls through to `access * 0.1` (the old pre-R13 formula).
6. The 86 tests passed because they validate against the **old** formula output, which matched the **broken** code path. This is a test-validates-broken-code failure, not a test-coverage gap.

**Root cause:** Two different data representations of the same memory -- `MemoryEntry` (Pydantic model, index.json) and search result dict (hand-rolled dict) -- diverged silently. The handler read from the wrong one.

**The C1 fix is architecturally correct:**
- `handlers.py` now reads `days_since_last_access` from `entry.days_since_last_access` (the `MemoryEntry` object fetched from `index.memories`), not from the search dict.
- `search.py` now also includes both `days_since_last_access` and `stability` in its output dict -- closing the gap for future consumers.
- This is a belt-and-suspenders fix: the handler no longer depends on search dict completeness, and the search dict is now complete anyway.

**Lesson for future rounds:** Any new field added to `MemoryEntry` must be propagated to three places: (1) `models.py` field definition, (2) `search.py` output dict, (3) `server.py` API response shape. A Pydantic-to-dict auto-serializer for search results would eliminate this class of bug entirely.

### 1.3 The C2 Stability Guards: Crash-Proofing

The C2 guards protect against three failure modes:

| Failure | Pre-R14 | Post-R14 |
|---------|---------|----------|
| `stability=0` | `ZeroDivisionError` crash in `0.5^(days/0)` | Pydantic validator rejects `<=0` with clear error |
| `stability < 0` | `decay > 1.0` (memory "strengthens" over time -- nonsense) | Pydantic validator rejects negative values |
| `stability < 0.1` (dangerously low) | Decay races to near-zero in hours | Pydantic validator clamps to 0.1 minimum (2.4h half-life); runtime `max(stability, 0.1)` double-guard |
| `days_since_last_access=None` | Treated as `0` (no decay) in all three consumers | Unified: `None` falls through to `access * 0.1` (no-decay path); behavior identical but now **documented and intentional** |

The Pydantic `@field_validator("stability", mode="before")` at line 111-122 of `models.py` is the correct defense-in-depth pattern. The runtime `max(stability, 0.1)` clamps in `handlers.py` (lines 257, 346) provide a second safety net for data that bypasses Pydantic validation (e.g., manually constructed objects).

### 1.4 The Core Loop -- Post-Round 14 Assessment

The product interaction loop remains:

```
Search/Graph Browse -> Inspect Memory -> Resolve Dependencies -> Edit/Maintain -> Validate
```

Round 14 tightened two additional joints beyond Round 13:

| Joint | Pre-R14 | Post-R14 |
|-------|---------|----------|
| **Graph -> Resolve** | No path. Had to switch to Search/List to resolve. | Right-click node -> "Resolve" context menu. |
| **Dashboard -> Awareness** | Passive stats only (maturity, status, type counts). | Decay Risk section shows memories approaching the R < 0.1 threshold. |
| **Modal Close** | Wander/Validate/Archive snapped away instantly. | All modals fade+scale out over 250ms with backdrop fade. |
| **Font readability** | 7 elements below 12px, including 9px reference text. | All text >= 11px; all interactive elements >= 12px. |

The core loop **works correctly end-to-end for the first time**. The decay formula that powers overview heat, wander cool-mode selection, and validate decay detection is now the same formula across all three paths. A user who resolves a memory, then views the overview dashboard, then runs wander, will see consistent decay behavior -- the same memory won't be "hot" in overview but "cold" in wander.

### 1.5 The Missing Table-Stakes Features (Unchanged from Prior Audit)

These remain the structural gaps preventing CodeMemory from reaching feature parity:

| Feature | Status | Competitor Standard |
|---------|--------|---------------------|
| Full-text body search | Missing | Mem0, Zep, paradigm, Obsidian, Notion -- all support |
| Multi-select / batch ops | Missing | Notion, Obsidian standard |
| Multi-level undo | Single-level | Every editor since 1984 |
| Graph keyboard navigation | Missing | Cytoscape native, not wired |
| Tabbed/multi-pane view | Missing | Obsidian, Notion, Logseq standard |
| Pin/bookmark memories | Missing | Every knowledge tool |
| Mobile responsive design | Missing | Standard in 2026 |
| Frontend tests | 0 tests | Any production UI |
| Semantic/embedding search | Missing | Mem0, Zep, paradigm standard |
| Entity extraction / linking | Missing | Mem0, Zep standard |
| Write-capable MCP tools | Snapshot only (1 of 5) | Mem0 (9 tools), paradigm (28 tools) |
| Onboarding / first-run experience | Missing | Standard in 2026 |

**Assessment:** The functional core is solid. The polish is complete. The correctness is verified. But the product still cannot perform the single most common user action -- "search for a word in a memory's body" -- which every competitor handles trivially. This is now the product's most acute functional gap and the primary blocker to external user adoption.

---

## Phase 2: Competitive Gap Analysis

### 2.1 The 2026 AI Memory Landscape (Updated)

The landscape has shifted significantly since the prior audit. Three developments matter:

**1. Mem0's April 2026 Algorithm (v2.0/v3.0) raises the bar dramatically:**
- 91.6% LoCoMo, 93.4% LongMemEval -- both up 20+ points from their prior algorithm
- Single-pass ADD-only extraction with ~7K tokens per operation
- Entity linking, multi-signal retrieval (semantic + BM25 + entity), temporal reasoning at 93%
- 9 MCP tools via `mcp.mem0.ai` cloud server, lifecycle hooks for Claude Code/Cursor/Codex
- CLI v0.2.2 (add, search, list, get, update, delete, import, entity management)
- Skill Graph for in-context coding agent documentation
- The gap between Mem0's "dump text, it figures out what to store" and CodeMemory's "manually create structured .md files" has **widened**.

**2. Zep/Graphiti now has a first-class MCP server (Thoughtworks Trial, April 2026):**
- Bi-temporal edges with 4 timestamps per relationship
- MCP server for Claude/Cursor -- making temporal KG memory accessible to any agent
- FalkorDB integration for multi-agent isolation
- 63.8% LongMemEval (independent benchmark)
- The bi-temporal model ("what was Alice's address before she moved in October?") is something CodeMemory cannot express natively.

**3. paradigm-memory continues to expand its tool surface:**
- 28 MCP tools (vs CodeMemory's 5), covering full CRUD + maintenance + audit + snapshot diff/restore
- Desktop app (Tauri + React + react-flow) with nodal graph visualization
- Consolidation/dream pass for auto-dedup and staleness detection
- Local embeddings (ONNX/WASM) with no cloud dependency
- Every mutation audited with actor + reason + diff

**4. Letta (formerly MemGPT) -- the OS-for-memory approach:**
- Treats LLM context window like virtual memory (RAM/disk/cold storage tiers)
- Agents self-edit their own memory -- no passive extraction pipeline
- Letta Code (March 2026): memory-first coding agent with defragmentation and reflection
- Task delegation to specialized subagents with project-specific memory
- ~83.2% LoCoMo
- The key insight: Letta's agents decide what to remember, not a pipeline. This is philosophically opposite to CodeMemory's explicit-imports model but practically similar in ambition: deterministic, agent-controlled memory.

### 2.2 Updated Competitive Positioning

```
                    Deterministic │
                    Dependency     │  CodeMemory  ← unique position
                    Resolution    │     ●
                                  │
                    Explicit      │  CodeMemory  Letta ●
                    Structure     │     ●          paradigm ●
                                  │
                    Probabilistic │       Mem0 ●
                    Similarity    │              ● Zep/Graphiti
                                  │
                                  │
                    Cloud ──────────────────────────── Local
                                  │
                    Mem0 ●        │     ● CodeMemory
                    Zep  ●        │     ● paradigm-memory
                    Letta ●       │
```

CodeMemory's niche -- deterministic dependency resolution for AI memory, local-first, file-based -- remains unique. But three competitors now occupy adjacent territory that was empty 6 months ago:

- **Letta** (deteministic + agent-controlled) has moved closer to CodeMemory's "explicit structure" axis by giving agents full control over what goes into memory.
- **paradigm-memory** has expanded its MCP tool surface to 28 tools, making it the most complete read/write/audit memory MCP server.
- **Mem0** has raised the accuracy bar to >90% on major benchmarks, making the argument for probabilistic memory harder to dismiss on quality grounds.

### 2.3 Missing "Must-Have" Features -- Updated Competitor Matrix

| Feature | Mem0 | Zep | paradigm | Letta | CodeMemory | Priority |
|---------|------|-----|----------|-------|------------|----------|
| Full-text body search | Yes | Yes | Yes | Yes | **No** | CRITICAL |
| Semantic/embedding search | Yes | Yes | Yes (local) | Yes | **No** | HIGH |
| Entity extraction + linking | Yes | Yes | Partial | Yes | **No** | MEDIUM |
| Write-capable MCP tools | Yes (9) | Yes | Yes (28) | Yes | **Snapshot only** | HIGH |
| Self-editing memory | Yes | No | Partial | Yes (core) | **No** | MEDIUM |
| Multi-level undo | N/A | N/A | Yes (snapshot) | N/A | **No** | MEDIUM |
| Auto-consolidation/dedup | Yes | Partial | Yes (dream) | Yes | **No** | LOW |
| Managed cloud hosting | Yes | Yes | No | Yes | **No** | LOW (by design) |
| Desktop app | No | No | Yes (Tauri) | Yes (ADE) | **No** | LOW |
| Frontend tests | Yes | Yes | Unknown | Yes | **No** | HIGH |
| Temporal fact tracking | No | Yes (core) | No | No | **No** | LOW |
| Onboarding/first-run | Yes | Partial | No | Partial | **No** | MEDIUM |

### 2.4 The Competitive Moat -- Three Risks

**Risk 1: The "explicit imports" moat is also a wall.** CodeMemory's core differentiator -- deterministic recall through explicit imports -- requires users to manually declare dependencies between memories. Every competitor that uses auto-extraction (Mem0, Zep, paradigm) can ingest unstructured text and infer relationships. CodeMemory cannot. The question is not whether explicit > implicit (it is, for correctness) but whether the market of users willing to do explicit memory engineering is large enough to sustain the product.

**Mitigation:** The `suggest_deps.py` module already exists CLI-only. Surfacing it in the MemoryForm UI (auto-complete import suggestions as the user types) would bridge the gap between "manual only" and "AI-assisted manual." This is proposed as Recommendation I4 below.

**Risk 2: Mem0's benchmark numbers are becoming impossible to ignore.** 91.6% LoCoMo and 93.4% LongMemEval mean Mem0 correctly recalls the right memory in the right context >90% of the time. The "probabilistic = unreliable" argument weakens when probabilistic hits 93%. CodeMemory's "deterministic = 100% accurate" argument remains true for structured recall but applies only to memories with explicit imports. CodeMemory cannot claim high recall on unstructured content.

**Mitigation:** This is not a feature gap to fix but a positioning decision. CodeMemory should lean harder into the use cases where deterministic recall matters most: investment decisions with audit trails, software architecture decisions with rationale chains, compliance-sensitive workflows where "the AI hallucinated a connection" is unacceptable. Full-text body search (C1 in recommendations) would close the unstructured-content recall gap enough to make the product defensible.

**Risk 3: paradigm-memory's 28 MCP tools make CodeMemory's 5-tool MCP server look thin.** Agents that connect to paradigm-memory can read, write, update, delete, move, audit, snapshot, diff, restore, dream, doctor, warm, and self-update. CodeMemory's agents can: resolve, overview, wander, focus, and snapshot. The gap is not just tool count -- it's the closed vs open agentic loop. CodeMemory's agents can READ context but cannot CONTRIBUTE to the knowledge base.

**Mitigation:** Write-capable MCP tools (`propose_create`, `propose_update`, `propose_imports`) would close the loop. This is Recommendation I1 below and should be the centerpiece of the MCP-focused round (suggested R16).

---

## Phase 3: Feature Depth -- Where Can We Go Deeper?

### 3.1 The Decay Model: From Invisible to API-Visible

Round 14 transforms the decay model from pure backend infrastructure into API-accessible data. The `/api/stats` endpoint now returns `decay_risk` -- an array of memories with R < 0.1, sorted by decay multiplier. The `/api/memories` endpoint now returns `stability` and `days_since_last_access` for every memory. The `/api/search` and `/api/wander` endpoints include the same fields.

This is not user-visible depth (the Dashboard N1 section is minimal -- count + top 3 IDs) -- but it is the **necessary infrastructure for all future decay features**. The next step is making it user-controllable:

- **Per-memory stability slider** in MemoryForm/MemoryDetail (Recommendation I2)
- **Decay column in List view** with color-coded recency (Recommendation I3)
- **Full "Cooling Memories" Dashboard section** with sortable list (Recommendation I5)
- **Per-tag stability defaults** ("investment" = 30d, "facts" = 7d) (long-term F2)
- **FSRS-lite stability updates** on resolve/focus access (long-term F3)

The `stability` field is now guarded, exposed, and computed correctly. It is a door waiting to be walked through.

### 3.2 Feature Depth Scores -- Updated

| Feature | R13 Score | R14 Score | Delta | Notes |
|---------|----------|----------|-------|-------|
| **Resolve** | 8.5/10 | **9.0/10** | +0.5 | Graph context menu adds second discovery path. Resolve-from-graph completes the triad (search + list + graph all lead to resolve). |
| **Overview (heat)** | 8/10 | **8.5/10** | +0.5 | Decay formula now actually works (C1). Heat values reflect real access decay for the first time. |
| **Wander** | 6.5/10 | **7.0/10** | +0.5 | Now uses correct decay formula; cool mode genuinely surfaces cooled memories. Exit animation added. |
| **Focus** | 4/10 | **4/10** | 0 | Unchanged. Still a binary full/summary toggle. |
| **Snapshot** | 6/10 | **6/10** | 0 | Unchanged. |
| **Search** | 4.5/10 | **4.5/10** | 0 | Unchanged. Body text search still missing. Resolve button now 12px (readable). |
| **Validate** | 7/10 | **7.5/10** | +0.5 | Decay detection now uses the correct, working formula. Exit animation added. |
| **Graph** | 6/10 | **7.0/10** | +1.0 | Resolve context menu is the single biggest graph UX improvement since initial Cytoscape integration. |
| **List** | 5.5/10 | **5.5/10** | 0 | Unchanged. |
| **Dashboard** | 4/10 | **5.0/10** | +1.0 | Decay Risk section (N1) transforms Dashboard from passive stats to active awareness. First time decay data is user-visible. |

**Weighted average: 6.4/10 (up from 6.0).** Four of ten features deepened measurably. Graph and Dashboard each gained a full point from single, high-impact additions. Resolve, Overview, Wander, and Validate each gained 0.5 from correctness (C1) and polish (I1) improvements.

### 3.3 The Personalization Frontier (Unchanged Opportunities)

The three personalization features identified in the prior audit remain equally feasible, now with the decay pipeline verified correct:

**A. Per-Memory Decay Curves** -- stability slider + "Decay" column in List view. Now that the API exposes stability and days_since_last_access, the frontend can consume this data directly.

**B. "Since You Last Visited" Context Injection** -- when resolving a long-untouched memory, inject a summary of what changed in its dependency chain. CodeMemory uniquely tracks both structure (DAG) and time (decay).

**C. Memory Health Dashboard** -- a 0-100 score from: cycle count, stale ratio, broken links, avg days since access, decay distribution. Now feasible because all decay data is API-accessible.

---

## Phase 4: Differentiation -- Strengthening the Moat

### 4.1 The Core Differentiator: Sharpened

CodeMemory's unique value proposition post-Round 14:

**"Correctly working deterministic dependency resolution for AI memory, with time-decay activation management exposed via API, and a native MCP protocol server with cognitive-primitive tools."**

The three-legged stool:

| Leg | R13 Status | R14 Status | Competitor comparison |
|-----|-----------|-----------|----------------------|
| **DAG (explicit imports)** | Working | Working (unchanged) | Mem0/Zep: probabilistic. paradigm: tree+activation. CodeMemory: deterministic DAG topo sort. |
| **MCP (5 cognitive primitives)** | 4 readOnly + 1 write | 4 readOnly + 1 write (unchanged) | Mem0: 9 tools (utility). paradigm: 28 tools (utility). CodeMemory: 5 tools aligned with cognitive model. |
| **Time decay (unified)** | Formula defined but broken in overview | **Formula correct and verified on all 3 paths** | Mem0: ADD-only. Zep: temporal facts. CodeMemory: activation decay (recency-weighted recall). |

The decay leg is now load-bearing. The C1 fix means CodeMemory is the only AI memory product with a **correctly implemented, internally consistent, cross-cutting time-decay activation model**. This is a legitimate technical moat -- building a unified decay model that works identically across overview, wander, and validate is architecturally non-trivial and no competitor has attempted it.

### 4.2 Three Strategic Bets (Updated)

#### Bet 1: Expose the Decay Model as a User-Visible Feature (Progress: 20%)

Round 14 completed the API exposure (C3) and the minimal Dashboard widget (N1). This is ~20% of the journey to making decay a user-visible differentiator. The remaining 80%:

- Per-memory stability slider in MemoryForm/MemoryDetail
- "Decay" column in List view with color coding
- Full "Cooling Memories" Dashboard section with sortable list
- Decay curve sparkline showing `0.5^(days/stability)` over time
- "Days since last access" display in MemoryDetail panel

**Next step:** R15 should make decay **controllable** (stability slider) and **sortable** (Decay column). This transforms the decay model from API infrastructure to user-facing feature.

#### Bet 2: Close the MCP Write Gap (Progress: 0%)

CodeMemory's MCP server is unchanged from Round 13: 4 readOnly tools + 1 write (snapshot). An agent can recall context but cannot contribute to the knowledge base. This is the single biggest integration gap.

**Next step:** Adding `propose_create_memory` and `propose_update_memory` MCP tools (with `propose_*` staging pattern for safety) would close the agentic loop. Suggested as the centerpiece of an MCP-focused round (R16).

#### Bet 3: Ship the "Aha Moment" as a One-Click Demo (Progress: 0%)

The "Demo Resolve" button proposed in the prior audit (Recommendation I3) remains unbuilt. With the graph Resolve context menu (N2) and Resolve-from-search (R13-D1), users now have two discovery paths to the Resolve flow. But neither is a one-click "here's what this product does" experience.

**Next step:** A 3-node demo dataset (Observation -> Analysis -> Decision) with a "Try Resolve" button on the Dashboard that auto-executes the full flow. Cost: ~50 lines + 3 .md files. This delivers the aha moment for new users and can be built in a single afternoon.

### 4.3 What NOT to Build (Unchanged)

CodeMemory should continue to consciously NOT compete on:

- **Entity extraction / NLP pipeline** -- Mem0 and Zep have multi-year head starts. CodeMemory's explicit model is the differentiator.
- **Collaborative editing / WebSocket sync** -- Notion-level infrastructure. Git-based collaboration is more aligned with developer users.
- **Mobile app** -- File-based architecture doesn't map to mobile.
- **Plugin ecosystem** -- Obsidian's 1,000+ plugins is not a target. Simplicity is the product.

---

## Technical Health

### 5.1 Architecture Assessment

```
Frontend (React 19 + TypeScript 6 + Vite 8, port 5299)
    |  REST API (fetch)
    v
Backend (FastAPI, port 8000)
    |  Python import
    v
Core (src/codememory/, 20 modules)
    |  File I/O
    v
Datasets (examples/*/, .md files + index.json)

MCP Server (JSON-RPC over stdio, separate process)
    |  Python import (same handlers.py functions)
    v
Core (src/codememory/)
```

**Round 14 architecture changes:**
- `models.py`: +1 `@field_validator` for stability (15 lines)
- `search.py`: +2 fields in output dict (2 lines)
- `handlers.py`: ~8 lines changed (C1 fix: read from entry, not dict; C2 runtime clamp)
- `server.py`: +4 fields in `/api/memories` response, +`decay_risk` in `/api/stats` (~20 lines)
- `Dashboard.tsx`: +65 lines (N1 decay risk section + I1 modal exit animations)
- `App.tsx`: +5 lines (N2 resolve context menu + I1 archive exit animation)
- `types.ts`: +4 fields on `MemorySummary`, +`DecayRiskEntry` interface, +`decay_risk?` on `StatsResponse`

**Assessment:** Clean, minimal, targeted changes. Zero architecture violations. The handler delegation pattern (server.py -> handlers.py, mcp_server.py -> handlers.py) remains intact. No new files were created. No dependencies were added.

### 5.2 Technical Debt -- Updated

| Item | R13 Status | R14 Status | Trend |
|------|-----------|-----------|-------|
| CSS-in-JS everywhere | Medium friction | Medium friction | UNCHANGED |
| No frontend tests | 0 tests | 0 tests | UNCHANGED -- Playwright deferred to R15 |
| Tailwind installed, unused | Low waste | Low waste | UNCHANGED |
| OpenAPI /docs unexposed | FIXED | FIXED | Maintained |
| No TypeScript strict mode | Medium risk | Medium risk | UNCHANGED |
| No CI pipeline | Medium risk | Medium risk | UNCHANGED |
| Single-level undo | User-facing gap | User-facing gap | UNCHANGED |
| Search-result dict / MemoryEntry duality | **Bug-causing** | **Mitigated** (belt+suspenders) | IMPROVED -- but root cause (two data representations) persists |

**New item from R14: Search result dict / MemoryEntry duality.** The C1 bug was caused by the existence of two different data structures representing the same memory. The fix adds the missing fields to the search dict (belt) AND makes the handler read from MemoryEntry directly (suspenders). But the fundamental design risk remains: any future field added to MemoryEntry must be manually propagated to the search dict and the API response shape. A single-source-of-truth approach (Pydantic model -> serialized output via `model_dump`) would eliminate this risk permanently.

### 5.3 Test Health

| Suite | Count | R13 | R14 | Delta |
|-------|-------|-----|-----|-------|
| Unit tests | 57 | 57/57 PASS (0.27s) | 57/57 PASS (0.33s) | UNCHANGED |
| Integration tests | 24 | 24/24 PASS | 24/24 PASS | UNCHANGED |
| API tests | 5 | 5/5 PASS (0.43s) | 5/5 PASS (0.44s) | UNCHANGED |
| TypeScript | -- | 0 errors | 0 errors | UNCHANGED |
| Vite build | -- | Built (365ms) | Built (338ms) | IMPROVED (7% faster) |
| **Total** | **86** | **86/86 PASS** | **86/86 PASS** | **UNCHANGED** |

**Assessment:** 100% pass rate, zero regressions, zero new tests. The C1 bug was a test-design failure (tests validated broken formula output), not a coverage gap. A new test that validates overview heat values change when `days_since_last_access` changes would permanently close this gap.

**Critical gap unchanged:** Zero frontend tests. 15 TSX components, 1 hook, and the entire user-facing surface have no automated test coverage. The Playwright constraint (promised for R15 first task) is now three rounds overdue (deferred R12, R13, R14). This is not a sustainable pattern.

### 5.4 Dependency Health

Unchanged from prior audit. Python: pyyaml, pydantic v2, jinja2, python-dotenv. Frontend: React 19, TypeScript 6, Vite 8, cytoscape 3.33, dagre 0.8, react-markdown 10. Zero AI/ML dependencies. Zero transitive vulnerabilities. Python 3.13+ requirement acceptable for developer tools. Supply chain risk: minimal.

---

## Prioritized Recommendations

### Critical (Fix Before Any External User Sees This)

| # | Recommendation | Rationale | Effort | Status |
|---|---------------|-----------|--------|--------|
| **C1** | **Add full-text body search** | The single biggest functional gap vs every competitor. Search matches ID, summary, tags only. A 500-word memory body is invisible to search. This is the #1 blocker to external user adoption. Wire into frontend search bar with result highlighting. | Medium (2-3 days) | DEFERRED (search sprint) |
| **C2** | **Add Playwright smoke tests** | Zero frontend test coverage across 15 TSX components. 5 tests (app loads, graph renders, node click, search, CRUD cycle) would catch ~80% of regressions. Now 3 rounds deferred. **Must be R15's first task.** | Small (1 day) | **COMMITTED for R15** |
| **C3** | **Eliminate search dict / MemoryEntry duality** | The C1 bug was caused by two data representations diverging. Refactor `search()` to build output from `MemoryEntry.model_dump()` instead of manual field copying, or refactor consumers to use MemoryEntry objects directly. This eliminates the entire class of "field missing from output dict" bugs. | Small (~30 lines) | **NEW -- suggested for R15** |

### Important (Build Before Seeking Early Adopters)

| # | Recommendation | Rationale | Effort |
|---|---------------|-----------|--------|
| **I1** | **Add write-capable MCP tools** | 4 of 5 MCP tools are readOnly. Agents recall but cannot contribute. Add `propose_create_memory`, `propose_update_memory`, `propose_imports` as MCP tools with staging pattern for safety. Closes the agentic loop. This is Mem0's and paradigm's #1 differentiator over CodeMemory. | Medium (~150 LOC) |
| **I2** | **Per-memory stability UI** | The `stability` field exists, is guarded, and is API-exposed -- but users cannot control it. Add a slider in MemoryForm/MemoryDetail. This is the single highest-impact user-facing feature from the decay model investment. | Small (~40 lines) |
| **I3** | **Decay column in List view** | Expose `days_since_last_access` and `stability` as sortable columns in the List view with color coding (warm for recent, cool for old). Gives users visibility into their memory access patterns. | Small (~20 lines) |
| **I4** | **Auto-complete import suggestions in MemoryForm** | `suggest_deps.py` exists CLI-only. Surface it as auto-complete suggestions when typing import IDs in the MemoryForm UI. Reduces manual linking friction and bridges the "explicit imports" wall. | Medium (~80 lines) |
| **I5** | **Full "Cooling Memories" Dashboard section** | Expand N1's minimal decay risk widget into a sortable list of all at-risk memories with decay values, access counts, and last-access dates. Clickable to open MemoryDetail. | Small (~50 lines) |
| **I6** | **Multi-level undo stack** | Single-level undo is unacceptable for any product positioning. Push operations onto a 20-deep stack, expose via Ctrl+Z / Ctrl+Shift+Z. The undo data model exists; this is wiring. | Small (rearchitecture of undo state) |

### Nice-to-Have (Build After Early Adopter Feedback)

| # | Recommendation | Rationale | Effort |
|---|---------------|-----------|--------|
| **N1** | **"Demo Resolve" button on Dashboard** | One-click demo: switch to 3-node demo dataset, auto-resolve Decision node, show animation, return. Delivers the aha moment in one click. ~50 lines + 3 .md files. | Small |
| **N2** | **Graph keyboard navigation** | Arrow keys to traverse nodes, Enter to open detail, Escape to close. Cytoscape supports natively; needs event binding. | Small |
| **N3** | **Version diff viewer** | Backend stores full change_log. Frontend shows only version number. Add "View changes" showing side-by-side diff. | Medium |
| **N4** | **"Since your last visit" context injection** | When resolving a long-untouched memory, inject summary of what changed in its dependency chain. Uniquely feasible because CodeMemory tracks both DAG and time. | Medium |
| **N5** | **Memory health score Dashboard** | A 0-100 number from cycle count, stale ratio, broken links, avg days since access, decay distribution. Gamifies knowledge maintenance. | Medium |
| **N6** | **Semantic/embedding search** | Vector similarity as complement to deterministic DAG resolve. Use local embeddings (ONNX/WASM) to keep zero-cloud promise. | Large |
| **N7** | **Git integration guide + GitHub Action** | Documented workflow for version-controlling .md datasets. GitHub Action that runs validate on push. "Memory as code" story for developers. | Small |

### Feature Ideas (Long-Term Strategic Assets)

| # | Idea | Why It Matters |
|---|------|---------------|
| **F1** | **Incremental resolve** | Only re-resolve changed dependencies. Reduces token cost for repeated resolves. Unique to explicit dependency model. |
| **F2** | **Per-tag stability defaults** | Tag-level stability ("investment"=30d, "facts"=7d). New memories inherit from tags. |
| **F3** | **FSRS-lite stability updates** | Update stability on resolve/focus access. Makes decay adaptive -- memories you use stay fresh longer. |
| **F4** | **DAG-aware editing sidebar** | Show upstream deps and downstream dependents while editing. Warn on semantic breakage. The core product insight, surfaced where it matters. |
| **F5** | **"Memory as code" CI pipeline** | GitHub Action + pre-commit hook running validate/reindex. Reject PRs with cycles or broken links. Developer adoption wedge. |
| **F6** | **Temporal fact modeling** | `valid_from`/`valid_to` on imports or body sections. "NVIDIA's P/E was 45 in Q4 2025" as a temporal fact. Unique differentiator vs Zep's bi-temporal edges. |

---

## Summary: The Path to v1.0

CodeMemory has crossed an important threshold. The engine is correct (C1 bug fixed, all decay paths verified). The design is complete (all modals animate, all fonts readable). The API is documented and decay-aware. The test suite is stable at 86/86 with zero regressions. The architecture is clean with no Round 14 violations.

Three deliverables separate the product from v1.0 readiness:

1. **Full-text body search** -- the last missing table-stakes feature. Without it, any external user's first search will fail to find their content. This is the single highest-priority functional gap and must be the centerpiece of the search-focused sprint.

2. **Frontend test coverage** -- 15 components at zero coverage. The Playwright commitment (5 smoke tests) has been deferred for three consecutive rounds. It must be R15's first commit before any new feature code lands.

3. **The agentic loop closure** -- 4 of 5 MCP tools are readOnly. CodeMemory cannot be a full agent memory partner until agents can write back. Write-capable MCP tools (with `propose_*` staging) would close this gap and match the minimum standard set by Mem0 and paradigm-memory.

The product's identity question from the prior audit remains unresolved but is becoming clearer: **CodeMemory is a developer tool for structured, auditable, explicit knowledge management.** The DAG model, CLI interface, MCP server, token budget controls, file-based architecture, and Git compatibility all point in this direction. The warm-neutral design and serif typography suggest broader ambitions, but the feature set has converged on developer power-users. This is not a problem -- developer tools are a large and profitable market (GitHub, Linear, Obsidian, VS Code). But the team should consciously embrace this identity rather than straddling two audiences.

**Round 15 recommendation:** Playwright tests first, then full-text body search. R16: MCP write tools + per-memory stability UI. R17: onboarding + demo resolution. This sequence closes the glass ceiling in priority order: safety net (tests), functional completeness (body search), agentic integration (MCP writes), user control (stability UI), user acquisition (onboarding).

---

*Audit completed 2026-05-07. Next review: post-Round 15.*
