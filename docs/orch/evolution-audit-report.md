# CodeMemory -- Product Evolution Audit Report

**Date:** 2026-05-07
**Reviewer:** Product Evolution Reviewer (Product Strategy)
**Build:** Post-Round 13 (8da78d8), entering Round 14
**Previous score:** 7.5/10 (post-Round 12)
**Round 13 eval:** 10/11 FULL PASS, 1 PARTIAL PASS (modal exit animations)
**Datasets available:** companion (11), investment (10), software-architecture (11), quant_operators (62)
**Methodology:** Full source code review (frontend 15 TSX components + 1 new hook, backend server.py, handlers.py, models.py, index.py, validate.py, resolve.py), live API testing (13 endpoints, /docs, /openapi.json), frontend service verification on localhost:5318, competitive intelligence analysis of Mem0, Zep/Graphiti, LangMem, Letta/MemGPT, paradigm-memory, and SuperLocalMemory.

---

## Executive Summary

**Product Evolution Maturity Score: 7.8 / 10** (up from 7.5)

Round 13 is a quiet but structurally significant milestone. Eleven targeted tasks advanced CodeMemory on four fronts simultaneously: aesthetic completion (exit animations on 3 panels, font stragglers fixed, search dropdown animation), discovery path (Resolve from search, shortcut hints, loading skeleton), conceptual coherence (three decay models unified into one formula, stability field laid as foundation for per-memory half-life curves), and developer infrastructure (OpenAPI /docs enabled).

The headline achievement is NOT the features themselves -- it is that three independent Reviewer reports converged on the same conceptual gaps, and all three were addressed in a single sprint without architectural damage. The exit animation hook (`useExitAnimation.ts`) is a clean, reusable pattern. The decay model unification (R13-M1 through M4) eliminates a silent correctness issue that no user would notice but every power user would eventually suffer from: three different "what should I remember?" answers from three different code paths.

The partial pass on modal exit animations (Wander/Validate/Archive) is a cosmetic gap -- 3 panels animate correctly, 3 modals don't. The fix is mechanical and should land in Round 14's first wave.

**Why 7.8 (up +0.3 from 7.5):**

The +0.3 reflects genuine progress in three areas that were scored as gaps in the prior audit: Resolve loading state (previously "UI freezes 1-3 seconds" -- now shimmer skeleton), OpenAPI /docs (previously "unexposed" -- now live), and search dropdown polish (previously "appears instantly" -- now 150ms fade-in with translateY). The decay model unification is architecturally important but not user-visible, so it doesn't move the aesthetic or functional scores directly.

The score didn't move more because the two biggest structural gaps from the prior audit remain untouched: full-text body search (the single biggest functional gap vs every competitor) and the lack of frontend tests (zero Playwright/Jest coverage). These were explicitly deferred in the negotiation -- correctly, as they exceed the "under 50 lines" threshold for a polish sprint -- but the product cannot cross 8.5/10 without them.

---

## Phase 1: Core Completeness -- What Remains for the Core Loop to Close?

### 1.1 Round 13 Progress: What Was Completed

| Gap (from prior audit) | Round 13 Status | Detail |
|------------------------|-----------------|--------|
| Exit animation dead code (R12-UX2) | **PARTIAL** (3/6) | `useExitAnimation` hook created and wired to MemoryDetail, Settings, MemoryForm panels + backdrop. Wander, Validate, Archive modals still lack exit animation. |
| Sub-12px font stragglers (R12-UX1) | **DONE** | Badges.tsx default 11->12px; SearchBar fuzzy matches 9->11px; match quality badge 9->11px. Detail panel badges now 12px (was 11px). |
| Search dropdown instant-appear | **DONE** | `dropdownFadeIn` keyframe (150ms ease + translateY 4px->0), applied to result list container. |
| No Resolve from search (Feature Idea #19) | **DONE** | "Resolve ->" button per search result. Click: close dropdown, switch to Graph view, 100ms delay, trigger resolve. |
| No shortcut hints on view buttons (R12-P4) | **DONE** | "1"/"2"/"3" hints at 10px/55% opacity on Graph/List/Dashboard buttons. Help panel also updated. |
| Resolve UI freeze (Critical #C3) | **DONE** | `isResolving` state in App.tsx; MemoryDetail shows "Resolving..." header + 3-line shimmer skeleton during resolve. GraphCanvas skips trim-level style updates during resolve. |
| Three parallel decay models | **DONE** | Overview, wander(cool), and validate all use `0.5^(days/stability)`. Cycle participants excluded from dependents heat. `days_since_last_access` precomputed in index. `stability` field (default 14.0) on MemoryEntry. |
| OpenAPI /docs unexposed (Critical #C2) | **DONE** | `/docs` and `/openapi.json` added to middleware exemption list. Swagger UI accessible at `http://localhost:8000/docs`. 13 endpoints documented. |

### 1.2 The Core Loop -- Post-Round 13 Assessment

The product interaction loop remains:

```
Search/Graph Browse -> Inspect Memory -> Resolve Dependencies -> Edit/Maintain -> Validate
```

Round 13 tightened three joints in this chain:

| Joint | Before R13 | After R13 |
|-------|-----------|-----------|
| **Search -> Resolve** | 4 clicks (search result -> close search -> graph -> resolve button) | 2 clicks (search -> "Resolve ->" button) |
| **Resolve -> Feedback** | UI freezes silently for 1-3 seconds | Shimmer skeleton with "Resolving..." header |
| **Panel Close** | Panel vanishes instantly (entrance animated, exit dead) | 3 of 6 panels now fade/slide out over 250ms |

The core loop **works**. A user can search for a memory, resolve its dependency chain in two clicks, see loading feedback, and close panels with exit animations. The remaining gaps are:

1. **Body text search (Critical):** Search still only matches ID, summary, tags, and metadata. A memory titled "NVIDIA Analysis" with a 500-word body about "semiconductor supply chain" won't appear when searching "supply chain." This is the single biggest functional gap and was correctly deferred to a search-focused sprint.

2. **Modal exit animations (Partial):** Wander, Validate, and Archive modals still vanish instantly. Users who primarily interact through Dashboard modals will never see an exit animation. The fix requires refactoring the `Modal()` inline function in Dashboard.tsx to use `useExitAnimation`.

3. **Graph keyboard navigation (Deferred):** Arrow-key node traversal remains missing. Power users who prefer keyboard-only operation are locked out of the graph view.

4. **Multi-level undo (Deferred):** Single-level undo feels jarringly primitive in 2026. Two consecutive edits where the second was a mistake cannot be reversed.

### 1.3 The Missing Table-Stakes Features (Unchanged from Prior Audit)

These remain the structural gaps preventing CodeMemory from reaching feature parity with any competitor:

| Feature | Round 12 Status | Round 13 Status | Competitor Standard |
|---------|----------------|-----------------|---------------------|
| Full-text body search | Missing | Missing | Mem0, Zep, Obsidian, Notion, paradigm-memory -- all support |
| Multi-select / batch ops | Missing | Missing | Notion, Obsidian standard |
| Multi-level undo | Single-level | Single-level | Every editor since 1984 |
| Graph keyboard navigation | Missing | Missing | Cytoscape native, not wired |
| Tabbed/multi-pane view | Missing | Missing | Obsidian, Notion, Logseq standard |
| Drag-and-drop tag assignment | Missing | Missing | Notion, Obsidian standard |
| Pin/bookmark memories | Missing | Missing | Every knowledge tool |
| Mobile responsive design | Missing | Missing | Standard in 2026 |
| Frontend tests | 0 tests | 0 tests | Any production UI |
| Semantic/embedding search | Missing | Missing | Mem0, Zep, paradigm-memory standard |
| Entity extraction / linking | Missing | Missing | Mem0, Zep/Graphiti standard |

**Assessment:** CodeMemory's functional completeness is sufficient for its current audience (the builder team) but would fail any external evaluator's first 5 minutes. The gaps are concentrated in Search (body text, semantic) and Editing (multi-select, multi-undo, keyboard nav) -- the two features users touch most.

---

## Phase 2: Competitive Gap Analysis

### 2.1 The 2026 AI Memory Landscape

Three distinct architectural approaches have emerged in the AI agent memory space:

| Architecture | System | Approach | Funding/Stars | Key Metric |
|-------------|--------|----------|---------------|------------|
| **Vector + Graph Hybrid** | Mem0 | Semantic + graph + KV store | $24M, 48K stars | 91.6% LoCoMo (new algo) |
| **Temporal Knowledge Graph** | Zep/Graphiti | Bi-temporal entity-relation edges | 24K stars | 63.8% LongMemEval |
| **Cognitive Map** | paradigm-memory | Tree + activation propagation | Apache 2.0 | 28 MCP tools |
| **DAG Dependency Resolution** | **CodeMemory** | Explicit imports + topo sort + time decay | N/A | **Zero-ambiguity recall** |

### 2.2 Competitor Deep Dives

#### Mem0 (mem0ai/mem0) -- The Market Leader

**What they have that CodeMemory doesn't:**
- **Self-editing memory**: ADD-only extraction pipeline that consolidates and deduplicates. No conflicting memories.
- **Entity extraction + linking**: Automatically extracts entities (people, projects, dates) and links them across memories.
- **Multi-signal retrieval**: Semantic (vector) + BM25 (keyword) + entity matching in parallel, fused by scoring.
- **Graph memory (Pro tier)**: Neo4j/Memgraph/Kuzu backend for multi-hop queries ("What projects has Alice worked on with Bob?").
- **Managed cloud hosting**: Free tier -> $19/mo -> $249/mo Pro. SOC2, HIPAA compliance path.
- **LangGraph/CrewAI/AutoGen integrations**: Embedded in the major agent frameworks.
- **9 MCP tools**: Including lifecycle hooks and cloud MCP server.
- **91.6% LoCoMo, 93.4% LongMemEval** on their newest algorithm (self-reported).

**Where CodeMemory wins:**
- **Deterministic recall**: Mem0 relies on vector similarity = probabilistic. CodeMemory's `imports` DAG is fully deterministic. You get exactly what you asked for, not what was semantically nearby.
- **Local-first, zero cloud**: Mem0's core operates cloud-side; self-hosting is possible but not the happy path.
- **Explicit dependency model**: Mem0 infers relationships probabilistically. CodeMemory requires explicit `imports` -- fewer false positives, no "AI hallucinated a connection."
- **Token budget control**: CodeMemory's `--budget N` + depth modes (required/recommended/full) give developers precise control over context window usage. Mem0 has no equivalent.
- **Time decay as first-class concept**: Mem0's ADD-only model accumulates indefinitely; CodeMemory's decay formula naturally cools unused memories.

**The gap that matters most:** Mem0's self-editing memory means a user can dump unstructured text and the system figures out what to store. CodeMemory requires users to manually create structured .md files with frontmatter. For developer power-users, this is acceptable (prefer explicit over implicit). For non-developer knowledge workers, this is a non-starter.

#### Zep/Graphiti (getzep/graphiti) -- The Temporal Specialist

**What they have that CodeMemory doesn't:**
- **Bi-temporal edges**: Every relationship carries `valid_from`, `valid_to`, `created_at`, `invalid_at`. Can answer "What was Alice's address before she moved in October?"
- **Episode subgraph**: Raw conversation/event data preserved for provenance and audit.
- **Community subgraph**: High-level abstractions grouping related entities.
- **Hybrid retrieval**: Semantic + BM25 + graph traversal in parallel, sub-second latency.
- **Multiple graph backends**: Neo4j, FalkorDB, Kuzu, Amazon Neptune.
- **Multi-LLM support**: OpenAI, Azure, Google Gemini, Anthropic, Groq, Ollama (local).
- **63.8% LongMemEval** vs Mem0's 49.0% on temporal tasks (independent benchmark).

**Where CodeMemory wins:**
- **Explicit dependency model** (again): Zep's graphs are auto-extracted from text -- same probabilistic noise problem as Mem0.
- **File-based architecture**: Zep requires running a graph database. CodeMemory's .md files + index.json can be version-controlled with Git.
- **MCP server**: Zep has MCP but CodeMemory's 5 cognitive primitives (overview, focus, resolve, wander, snapshot) form a more structured cognitive interface than Zep's generic graph query tools.
- **Warm-neutral design**: Zep is a developer tool with developer aesthetics. CodeMemory's crafted visual identity is a legitimate competitive advantage for knowledge-worker adoption.

**The gap that matters most:** Zep's temporal reasoning is architecturally superior. CodeMemory's `days_since_last_access` tracks when you accessed a memory, but Zep tracks when facts were true. "NVIDIA's P/E was 45 in Q4 2025" is a temporal fact that CodeMemory cannot natively model -- it's just text in a body. A `valid_from`/`valid_to` concept on imports or body sections would be structurally additive.

#### paradigm-memory (infinition/paradigm-memory) -- The Closest Conceptual Competitor

**What they have that CodeMemory doesn't:**
- **28 MCP tools**: vs CodeMemory's 5. Includes mutations (write, update, delete, move), review/audit tools, snapshot diff/restore, import/export, and maintenance (doctor, stats, warm).
- **Activation propagation**: Three-level gating (open >=0.75, latent >=0.45, ignored <0.25) based on hybrid scoring (FTS BM25 + lexical + parent activation + importance + confidence + substring boost).
- **Consolidation/dream pass**: Detects duplicates, stale items, overloaded nodes, and orphans automatically.
- **Forensic audit log**: Every mutation records actor + reason + diff.
- **Multi-workspace pooling**: One process serves N projects via `workspace` parameter.
- **Desktop app**: Tauri + React + react-flow with nodal graph visualization.
- **Local embeddings**: ONNX/WASM (`Xenova/all-MiniLM-L6-v2`, 90MB) or optional Ollama.
- **Auto-snapshots**: Before every destructive operation.
- **Apache 2.0 license**, fully free, zero cloud.

**Where CodeMemory wins:**
- **DAG dependency resolution**: paradigm-memory's tree + activation is NOT a dependency graph -- it's a hierarchical topic tree with relevance propagation. CodeMemory's `imports` DAG + topological sort produces a deterministic, ordered resolve output. paradigm-memory cannot answer "show me everything that led to this decision, in causal order."
- **Explicit over inferred**: paradigm-memory auto-organizes based on content similarity. CodeMemory requires explicit imports -- again, fewer false positives.
- **MCP protocol compliance**: CodeMemory's `readOnlyHint` annotations are correct and complete. paradigm-memory's 28 tools don't consistently declare read/write semantics.
- **Token budget**: CodeMemory has `--budget N` + depth modes + trim levels. paradigm-memory's context packs don't expose explicit budget control.

**The gap that matters most:** paradigm-memory's tool surface is 5.6x larger (28 vs 5 tools) and covers the full CRUD cycle + maintenance + audit. CodeMemory's MCP server is read-oriented (4 readOnly, 1 write via snapshot). Agents can read from but cannot write to CodeMemory's memory system. Adding `create_memory` and `update_memory` as MCP tools would close the most important integration gap.

### 2.3 Competitive Landscape Summary

```
                    Deterministic │
                    Dependency     │  CodeMemory  ← unique position
                    Resolution    │     ●
                                  │
                    Explicit      │  CodeMemory     paradigm-memory
                    Structure     │     ●               ●
                                  │
                    Probabilistic │       Mem0 ●
                    Similarity    │              ● Zep/Graphiti
                                  │
                                  │
                    Cloud ──────────────────────────── Local
                                  │
                    Mem0 ●        │     ● CodeMemory
                    Zep  ●        │     ● paradigm-memory
```

CodeMemory occupies a unique niche -- deterministic dependency resolution for AI memory, local-first, file-based -- that no competitor fills. But this niche has walls: it requires users who are willing to manually structure their knowledge with explicit imports, and it lacks the automated extraction, entity linking, and consolidation that make Mem0 and Zep accessible to non-developers.

### 2.4 Missing "Must-Have" Features Across All Competitors

These features are now table stakes for any AI memory product:

| Feature | Mem0 | Zep | paradigm | CodeMemory | Priority |
|---------|------|-----|----------|------------|----------|
| Full-text body search | Yes | Yes | Yes | **No** | CRITICAL |
| Semantic/embedding search | Yes | Yes | Yes (local) | **No** | HIGH |
| Entity extraction + linking | Yes | Yes | Partial | **No** | MEDIUM |
| Write-capable MCP tools | Yes | Yes | Yes | **No** (except snapshot) | HIGH |
| Multi-level undo | N/A | N/A | Yes (snapshot) | **No** | MEDIUM |
| Auto-consolidation/dedup | Yes | Partial | Yes (dream pass) | **No** | LOW |
| Managed cloud hosting | Yes | Yes | No | **No** | LOW (by design) |
| Desktop app | No | No | Yes (Tauri) | **No** | LOW |
| Frontend tests | Yes | Yes | Unknown | **No** | HIGH |

---

## Phase 3: Feature Depth -- Where Can We Go Deeper?

### 3.1 The stability Field: A Door Opening

R13-M4's `stability: float = 14.0` on every MemoryEntry is the most strategically significant change in Round 13 -- not for what it does today (backward-compatible default; all memories have identical 14-day half-life), but for what it enables tomorrow.

**Current state:** `stability` is a passive, uniform constant. Every memory decays at the same rate: `0.5^(days/14)`. A one-line fact about NVIDIA earnings decays identically to a deeply-researched investment thesis.

**What stability unlocks per-memory:**
- **Spaced repetition (FSRS-lite):** Increase stability each time a memory is accessed via `resolve` or `focus`. Memories you use stay fresh longer. Memories you ignore cool faster.
- **Intensity-weighted stability:** High-intensity memories (8-10) could have longer half-lives (21-28 days). Low-intensity memories (1-3) could have shorter half-lives (7-10 days). This mirrors human memory: important things fade slower.
- **Maturity-gated stability:** `proven` memories decay at 21 days, `draft` at 7 days. The system naturally prioritizes proven knowledge.
- **Schema-directed stability:** `schema` type memories (templates) could have infinite stability (never decayed) since they define structure, not content.

The formula is already uniform across overview/wander/validate. Changing `stability` per-memory is a parameter change, not an architecture change. This is low-hanging personalization fruit.

### 3.2 days_since_last_access: Personalization Primitive

R13-M3's `days_since_last_access` integer is another strategic door-opener. Today it's used only for heat calculation. Tomorrow it enables:

- **"Last accessed N days ago" display** in MemoryDetail panel -- gives users visibility into their own memory usage patterns.
- **"Due for review" Dashboard section** -- memories where `days_since_last_access > stability` sort to the top with a warning icon. This transforms the Dashboard from a passive stats display into an active knowledge maintenance tool.
- **Access frequency trend** -- track the last 5 access timestamps to compute access velocity. "Is this memory being used more or less over time?" Surfaces shifting relevance before decay detection catches it.
- **"Since your last visit" resolve augmentation** -- when resolving a memory, highlight which dependencies have been accessed more recently than the memory itself (potential "context you have but haven't connected").

### 3.3 Feature Depth Scores -- Updated

| Feature | R12 Score | R13 Score | Delta | Can Go Deeper? |
|---------|----------|----------|-------|----------------|
| **Resolve** | 8/10 | **8.5/10** | +0.5 | Resolve-from-search shortens path; loading state removes friction. Next: incremental resolve (only changed deps), cycle-aware partial resolution. |
| **Overview (heat)** | 7/10 | **8/10** | +1.0 | Decay model unified; cycle participants excluded; days precomputed. Next: per-memory stability curves, user feedback loop ("this was useful"). |
| **Wander** | 5/10 | **6.5/10** | +1.5 | Now uses same decay formula as overview. Cool wander genuinely surfaces cooled memories. Next: spaced-repetition scheduling, serendipity streaks. |
| **Focus** | 4/10 | **4/10** | 0 | Unchanged. Still a summary/full binary toggle. Next: progressive disclosure (3+ levels), inline editing from focus, context-aware related suggestions. |
| **Snapshot** | 6/10 | **6/10** | 0 | Unchanged. Next: snapshot diff/comparison, auto-snapshot triggers. |
| **Search** | 3/10 | **4.5/10** | +1.5 | Resolve button + dropdown animation add quality. Next: full-text body search (the 3->6 jump), semantic search, saved searches. |
| **Validate** | 6/10 | **7/10** | +1.0 | Decay detection now uses continuous formula (R < 0.1 threshold), not hardcoded 30 days. Next: auto-fix suggestions, pre-commit hooks. |
| **Graph** | 6/10 | **6/10** | 0 | Unchanged. Resolve loading state integrated. Next: keyboard navigation, subgraph extraction, Hover micro-animations. |
| **List** | 5/10 | **5.5/10** | +0.5 | Badge fonts now 12px in list. Next: column customization, multi-select, batch ops. |
| **Dashboard** | 4/10 | **4/10** | 0 | Unchanged. Next: activity timeline, memory health score, "due for review" section. |

**Weighted average: 6.0/10 (up from 5.5).** Three of ten features deepened measurably. Seven features are at the same depth as Round 12. The decay model work deepens Overview, Wander, and Validate simultaneously -- a force multiplier from a single code change.

### 3.4 The Personalization Frontier

Three features that the `stability` + `days_since_last_access` pairing opens:

**A. Per-Memory Decay Curves Dashboard.** A Settings-like panel where power users can adjust stability per-memory or per-tag. "Investment theses: 30-day half-life. Market facts: 7-day half-life." This makes the decay model visible and controllable -- transforming it from an invisible algorithm to a user-controlled feature.

**B. "Since You Last Visited" Context Injection.** When a user resolves a memory they haven't touched in 30 days, inject a summary block: "Since your last visit to this dependency chain: 3 memories updated, 2 new dependencies added, 1 memory cooled below threshold." This is the "Recap" feature from social media but for personal knowledge -- and uniquely feasible because CodeMemory tracks both structure (DAG) and time (decay).

**C. Memory Health Dashboard.** A 0-100 score computed from: cycle count, stale ratio, broken links, average days since access, decay rate distribution, dependency depth distribution. Gamifies knowledge maintenance. "Your knowledge base health is 72. Resolve 3 stale memories and validate to reach 85." This was F2 in the prior audit and gains feasibility now that the decay model is unified and the data is precomputed.

---

## Phase 4: Differentiation -- Strengthening the Moat

### 4.1 The Core Differentiator: DAG + MCP + Time Decay

CodeMemory's unique value proposition has sharpened since Round 12:

**"Deterministic dependency resolution for AI memory, with time-decay activation management, exposed as a native MCP protocol server."**

This is now a three-legged stool:

| Leg | What it means | Competitor comparison |
|-----|---------------|----------------------|
| **DAG (explicit imports)** | Memory loading is dependency resolution, not vector search | Mem0/Zep: probabilistic. paradigm: tree+activation. CodeMemory: deterministic DAG topo sort. |
| **MCP (native protocol)** | 5 cognitive primitives as agent tools | Mem0: 9 MCP tools (utility). Zep: MCP. paradigm: 28 MCP tools (utility). CodeMemory: 5 tools aligned with cognitive model, not utility functions. |
| **Time decay (unified)** | `0.5^(days/stability)` across overview/wander/validate | Mem0: ADD-only (accumulates forever). Zep: temporal facts (validity windows). CodeMemory: activation decay (recency-weighted recall). |

No competitor has all three. Mem0 has MCP + time-agnostic retrieval. Zep has temporal modeling + probabilistic graphs. paradigm-memory has MCP + activation + local-first. Only CodeMemory combines deterministic DAG resolution with time-decay activation management behind an MCP protocol.

### 4.2 Strengthening the Moat -- Three Strategic Bets

#### Bet 1: Expose the Decay Model as a User-Visible Feature

The time-decay model is currently invisible -- it operates silently in overview/wander/validate with no user-facing UI. Making it visible and controllable transforms it from infrastructure into differentiation.

**Specific steps:**
- Show `days_since_last_access` in MemoryDetail panel ("Last accessed: 23 days ago")
- Add a "Decay" column to List view (sortable by days since access)
- Dashboard "Cooling Memories" section: top 5 memories closest to `R < 0.1` threshold
- Per-memory stability slider in MemoryForm/MemoryDetail
- Make the decay curve visual: a small sparkline showing `0.5^(days/stability)` over time

This is the "make the algorithm your friend" strategy. CodeMemory's decay model produces deterministic, explainable results ("this memory's relevance is 23% because you last accessed it 32 days ago with a 14-day half-life"). Contrast Mem0, where a memory surfaced or didn't because of an opaque vector distance.

#### Bet 2: Close the MCP Write Gap

CodeMemory's MCP server is read-oriented: 4 readOnly tools (resolve, overview, wander, focus) + 1 write tool (snapshot). An AI agent can recall context but cannot contribute to the knowledge base.

**Specific steps:**
- Add `create_memory` MCP tool: agent creates a memory from conversation insights
- Add `update_memory` MCP tool: agent updates body/summary/status based on new information
- Add `suggest_imports` MCP tool: agent proposes dependency edges between memories

This closes the agentic loop: agent reads context via resolve, reasons, acts, and writes learnings back. This is Mem0's core value proposition ("self-editing memory") but done with explicit imports instead of probabilistic extraction -- CodeMemory can offer "self-editing memory you can reason about."

**Risk:** Write-capable MCP tools mean an AI agent can corrupt a carefully structured knowledge base. Mitigation: all MCP writes should be `propose_*` (staged, not applied) and require human review. paradigm-memory's `memory_propose_write` pattern is the right model.

#### Bet 3: Ship the "Aha Moment" as an Interactive Onboarding Demo

The prior audit identified this as I5. The Negotiation deferred it due to cost (medium, needs embedded Cytoscape). But with Resolve-from-search (R13-D1) shortening the path to 2 clicks, and Resolve loading state (R13-D3) removing the freeze, the aha moment is now 2 clicks from the global search bar.

**Lower-cost alternative:** Add a one-click "Demo Resolve" button to the Dashboard that:
1. Switches to a pre-built demo dataset (3-node DAG: Observation -> Analysis -> Decision)
2. Auto-triggers resolve on the Decision node
3. Shows the animation
4. Displays the resolved context
5. Returns the user to their original dataset

This doesn't require interactive cytoscape in the onboarding overlay. It uses the existing Graph view, existing Resolve pipeline, and existing MemoryDetail panel. Cost: ~50 lines of App-level orchestration + 3 .md files in a `examples/demo/` dataset. The aha moment becomes: "click one button, watch your entire thinking chain animate."

### 4.3 What NOT to Build (Differentiation Through Omission)

CodeMemory should consciously choose NOT to compete on:

- **Entity extraction / NLP pipeline:** Mem0 and Zep have multi-LLM extraction pipelines. Building one would be a year-long distraction. CodeMemory's explicit model is the differentiator -- lean into it, don't dilute it.
- **Collaborative editing / WebSocket sync:** This is Notion-level infrastructure. The MCP-native collaboration model (shared Git repository) is more aligned with the developer target.
- **Mobile app:** The file-based architecture doesn't map to mobile. A read-only mobile companion (browse graph, view memories) is feasible; full editing is not.
- **Plugin ecosystem:** Obsidian's 1,000+ plugins is not a target. CodeMemory's simplicity (three views, five cognitive primitives) IS the product.

---

## Technical Health

### 5.1 Architecture Assessment

```
Frontend (React 19 + TypeScript 6 + Vite 8, port 5318)
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

**Round 13 architecture changes:**
- Frontend: +1 file (`useExitAnimation.ts`, 46 lines -- reusable hook)
- Frontend: +2 CSS animations (`dropdownFadeIn` keyframe in index.css)
- Backend: +4 fields on MemoryEntry (`days_since_last_access`, `stability`)
- Backend: ~20 lines of decay formula changes in handlers.py, validate.py
- Backend: +16 lines in index.py for precomputation
- Backend: +1 line in resolve.py for access tracking
- Backend: +2 exemption paths in server.py middleware

**Assessment:** Clean, minimal changes. No architecture violations. The handler delegation pattern (server.py -> handlers.py, mcp_server.py -> handlers.py) remains intact. The new `useExitAnimation` hook is the right abstraction -- used in 3 components, single source of truth for exit animation timing.

### 5.2 Technical Debt -- Updated

| Item | R12 Status | R13 Status | Trend |
|------|-----------|-----------|-------|
| CSS-in-JS everywhere | Medium friction | Medium friction | UNCHANGED -- no design token work done |
| No frontend tests | 0 tests | 0 tests | UNCHANGED -- deferred to Round 14 |
| Tailwind installed, unused | Low waste | Low waste | UNCHANGED |
| OpenAPI /docs unexposed | Missing | **FIXED** | + |
| No TypeScript strict mode | Medium risk | Medium risk | UNCHANGED |
| No CI pipeline | Medium risk | Medium risk | UNCHANGED |
| Single-level undo | User-facing gap | User-facing gap | UNCHANGED |

**Net technical debt movement: -1 item resolved (OpenAPI docs), 0 items added, 6 items unchanged.**

### 5.3 Test Health

| Suite | Count | R12 | R13 | Delta |
|-------|-------|-----|-----|-------|
| Unit tests | 57 | 57/57 PASS (0.31s) | 57/57 PASS (0.27s) | UNCHANGED |
| Integration tests | 24 | 24/24 PASS | 24/24 PASS | UNCHANGED |
| API tests | 5 | 5/5 PASS (0.46s) | 5/5 PASS (0.43s) | UNCHANGED |
| TypeScript | -- | 0 errors | 0 errors | UNCHANGED |
| Vite build | -- | Built (339ms) | Built (365ms) | UNCHANGED (normal variance) |
| **Total** | **86** | **86/86 PASS** | **86/86 PASS** | **UNCHANGED** |

**Assessment:** 100% pass rate, zero regressions. The test suite correctly validates the decay model unification (CLI overview heat values match expected: 31,31,21,21,20). All 4 datasets reindex with correct `stability` and `days_since_last_access` fields. The OpenAPI /docs endpoint returns 200.

**Critical gap unchanged:** Zero frontend tests. 15 TSX components, 1 hook, and the entire user-facing surface have no automated test coverage. This is now the single highest-risk technical debt item. Every UI regression is undetectable until manual inspection.

### 5.4 New Pitfalls Introduced in Round 13

From the evaluator's code review:

1. **R13-A1: Inline Modal function blocks exit animation reuse.** Dashboard.tsx's `Modal({ children, onClose })` is a local function component that hardcodes `backdrop-fade-enter` / `modal-fade-enter` and cannot receive a `closing` prop. When multiple modals share this function, exit animation must be managed at the call site, not the component. Fix: refactor to use `useExitAnimation` pattern.

2. **R13-M3: days_since_last_access None vs 0 semantic ambiguity.** `None` means "never accessed" (treated as `days_since=0` in decay formula = no decay). `0` means "just accessed" (also no decay). These are semantically different states (never used vs just used) that collapse to the same decay value. Future wander logic may want to differentiate "never accessed" as higher priority for serendipitous recall.

3. **R13-I1: /docs middleware exemption creates a new bypass path.** The dataset header middleware now exempts `/docs` and `/openapi.json` from the `X-Codememory-Dataset` requirement. This is correct (API docs are dataset-agnostic) but creates a precedent for exempt paths. Any future endpoint that doesn't require a dataset must be explicitly added to the exemption list -- a manual maintenance point.

### 5.5 Dependency Health

Unchanged from Round 12. Python: pyyaml, pydantic v2, jinja2, python-dotenv. Frontend: React 19, TypeScript 6, Vite 8, cytoscape 3.33, dagre 0.8, react-markdown 10. Zero AI/ML dependencies. Zero transitive vulnerabilities. Python 3.13+ requirement is acceptable for developer tools. Suppy chain risk: minimal.

---

## Prioritized Recommendations

### Critical (Fix Before Any External User Sees This)

| # | Recommendation | Rationale | Effort | Status |
|---|---------------|-----------|--------|--------|
| **C1** | **Add full-text body search** | The single biggest functional gap vs every competitor. Search currently only matches ID, summary, tags, and metadata. A user with a 500-word memory body cannot find it by searching its content. Also wire into frontend search bar. | Medium | DEFERRED (search sprint) |
| **C2** | **Complete modal exit animations** | Wander, Validate, and Archive modals still vanish instantly. 3 of 6 UI exit points are dead. Fix: refactor Dashboard `Modal()` to use `useExitAnimation` pattern. ~25 lines. | Small | **FOR ROUND 14** |
| **C3** | **Add Playwright smoke tests** | 15 TSX components with zero automated test coverage. 5 tests (app loads, graph renders, node click, search, CRUD cycle) would catch ~80% of regressions. This is now the highest-risk technical debt item -- the prior audit's I6, deferred again. | Small | **FOR ROUND 14** |

### Important (Build Before Seeking Early Adopters)

| # | Recommendation | Rationale | Effort |
|---|---------------|-----------|--------|
| **I1** | **Add write-capable MCP tools** | 4 of 5 MCP tools are readOnly. Agents can recall but cannot contribute. Add `create_memory`, `update_memory` as MCP tools (with `propose_*` staging pattern for safety). This closes the agentic loop and is Mem0's #1 differentiator. | Medium |
| **I2** | **Per-memory stability UI** | The `stability` field (R13-M4) exists but is invisible. Add a slider in MemoryForm/MemoryDetail and a "Decay" column in List view. Make the time-decay model user-visible and user-controllable. Transforms an invisible algorithm into a differentiator. | Small |
| **I3** | **"Demo Resolve" button on Dashboard** | One-click demo: switch to 3-node demo dataset, auto-resolve Decision node, show animation, return to original dataset. Costs ~50 lines + 3 .md files. Delivers the aha moment in one click. Lower-cost alternative to interactive onboarding (deferred I5 from prior audit). | Small |
| **I4** | **Full-text body search -- frontend side** | The frontend search bar must match against body text alongside ID/summary/tags. This is blocked on C1 (backend body search) but the frontend wiring is independent. | Small (after C1) |
| **I5** | **Dashboard "Cooling Memories" section** | Top 5 memories closest to decay threshold (R < 0.1). Uses already-computed `days_since_last_access` and `stability`. Transforms Dashboard from passive stats to active knowledge maintenance. | Small |
| **I6** | **Multi-level undo stack** | Single-level undo is unacceptable for any product positioning. Push operations onto a stack (20 deep), expose via Ctrl+Z / Ctrl+Shift+Z. The undo data model exists -- this is wiring, not new architecture. | Small |

### Nice-to-Have (Build After Early Adopter Feedback)

| # | Recommendation | Rationale | Effort |
|---|---------------|-----------|--------|
| **N1** | **Graph keyboard navigation** | Arrow keys to traverse nodes, Enter to open detail, Escape to close. Cytoscape supports this natively -- needs event binding. Enables mouse-free exploration. | Small |
| **N2** | **Version diff viewer** | Backend stores full change_log per memory. Frontend shows only version number. Add "View changes" button in MemoryDetail showing side-by-side diff. | Medium |
| **N3** | **"Since your last visit" context injection** | When resolving a memory untouched for N days, inject summary of what changed in its dependency chain since last access. Uniquely feasible because CodeMemory tracks both DAG and time. | Medium |
| **N4** | **Memory health score Dashboard** | A 0-100 number from: cycle count, stale ratio, broken links, avg days since access, decay distribution. Gamifies knowledge maintenance. | Medium |
| **N5** | **Semantic/embedding search** | Vector similarity search as complement to deterministic DAG resolve. Not a replacement -- an addition for discovery. Use local embeddings to keep zero-cloud promise. | Large |
| **N6** | **Git integration guide + GitHub Action** | Documented workflow for version-controlling .md datasets. GitHub Action that runs validate on push. "Memory as code" story for developers. | Small |
| **N7** | **Settings panel expansion** | From 3 items (theme, dataset, font size) to meaningful configuration: default budget, default depth, default stability, review cadence. Settings currently feels like a placeholder. | Medium |

### Feature Ideas (Long-Term Strategic Assets)

| # | Idea | Why It Matters |
|---|------|---------------|
| **F1** | **Incremental resolve** | Only re-resolve changed dependencies instead of the full DAG. Reduces token cost for repeated resolves on active memories. Unique to CodeMemory's explicit dependency model -- possible because we know exactly what changed. |
| **F2** | **Per-tag stability defaults** | Set stability at the tag level ("investment" = 30 days, "facts" = 7 days). New memories inherit stability from their tags. Makes the decay model tag-aware. |
| **F3** | **FSRS-lite stability updates** | When a memory is accessed via resolve or focus, update its stability using a simplified FSRS formula (increase for successful recall, adjust for timing). This makes the decay model adaptive -- memories you use stay fresh longer. |
| **F4** | **DAG-aware editing sidebar** | When editing, show upstream dependencies and downstream dependents in a sidebar. Warn if changing this memory semantically breaks downstream assumptions. The core product insight, surfaced where it matters. |
| **F5** | **"Memory as code" CI pipeline** | GitHub Action + pre-commit hook that runs validate/reindex on every push. Reject PRs that introduce cycles or broken links. This is the developer adoption wedge. |
| **F6** | **Auto-suggested imports in MemoryForm** | The `suggest_deps.py` module exists (CLI-only). Surface it in the MemoryForm UI as auto-complete suggestions when typing import IDs. Reduces manual linking friction. |

---

## Summary: The Path to v1.0

CodeMemory is approaching a pivotal threshold. The engine is proven (86 tests, 100% pass, zero regressions across 13 rounds). The design has identity (Warm-neutral palette, typography trio, animated panels). The integration story is unique (MCP server, 5 cognitive primitives, time-decay activation). The architecture is clean (handler delegation, uniform decay formula, reusable animation hooks).

What separates the product from v1.0 readiness is now three concrete deliverables:

1. **Full-text body search** -- the last missing table-stakes feature. Without it, any external user's first search will fail to find their content. This was deferred in Round 13 and must be the centerpiece of the search sprint.

2. **Frontend test coverage** -- 15 components at zero test coverage. This is a ticking time bomb. Every new feature risks regressions in existing views with no automated detection. Five Playwright smoke tests would be the minimum viable safety net.

3. **The aha moment in the first minute** -- currently buried at 2+ clicks. The "Demo Resolve" button (Recommended I3) would deliver the product's most compelling moment in one click. The interactive onboarding (deferred I5) would deliver it in the first 30 seconds.

The decay model unification (R13-M1-M4) has done something subtle but important: it made the time dimension of memory computationally real and internally consistent. The `stability` field is a door. The question for Round 14 is whether to walk through it -- making decay visible, controllable, and per-memory -- or to close the functional gaps first.

**Recommendation:** Close gaps before deepening features. Full-text search + modal exit animations + Playwright smoke tests should be Round 14's mandate. The decay model personalization (per-memory stability UI, cooling memories dashboard) is Round 15's natural agenda.

The product's identity question from the prior audit remains unresolved: **developer tool vs knowledge worker tool.** The feature set increasingly serves developers (MCP, CLI, token budgets, explicit imports) while the visual design serves knowledge workers (warm palette, serif fonts, onboarding tour). This tension is not harmful yet -- both paths converge on the same technical foundation -- but it will become acute the moment CodeMemory seeks external users. The Round 14 plan should include a strategic decision on this question.

---

*Audit completed 2026-05-07. Next review: post-Round 14.*
