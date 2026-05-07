# CodeMemory -- Product Evolution Audit Report

**Date:** 2026-05-07
**Reviewer:** Product Evolution Reviewer (Product Strategy)
**Build:** Post-Round 15 (4f22599), 5/5 Pass, adaptive stability (FSRS SInc), long-term retention floor, domain-differentiated default stability, MemoryDetail access freshness
**Previous score:** 7.8/10 (post-Round 13)
**Current score:** 6.5/10

> **Note on score decline:** The 6.5/10 does NOT reflect regression -- Round 15 delivered exactly what it promised. Rather, the broadening competitive landscape and the growing gap between "engine maturity" (9/10) and "product experience" (4/10) become starker with each round that defers the Input Problem and AI Copilot. The engine score is rising; the product score is not.

**Methodology:** Full source code review (backend/server.py 1419 lines, frontend/src 6045 lines across 12 components, App.tsx 1655 lines), live API testing (19 endpoints verified, /docs 200), competitive landscape research (Obsidian, Notion AI, Mem.ai, HGP, LCM, SHIMI, DragonScale, SwiftMem), Gemini audit report synthesis, negotiation document review.

---

## Executive Summary

CodeMemory possesses a highly defensible core engine -- deterministic DAG dependency resolution + token budget constraints + Ebbinghaus-inspired time decay activation. In a 2026 AI memory market dominated by "probabilistic vector search," the philosophy that **memory loading is a compilation problem, not a search problem** is a genuine strategic moat.

However, the product currently sits at the **technology-validated but commercially-unusable** crossing point. The core loop (Capture -> Structure -> Consume -> Feedback) is technically closed but experientially broken. The two largest fractures are:

1. **The Input Problem:** Users cannot get their data into the system without using a CLI. There is zero import UI in the Web interface. For a product positioned as a "second brain," this is an existential onboarding failure.
2. **The AI Copilot Paradox:** CodeMemory is a memory system designed *for* AI Agents, yet humans writing memory cards in the UI receive zero AI assistance -- no auto-summary, no tag suggestion, no related-memory recommendation.

The current score of 6.5/10 reflects this asymmetry: **engine 9/10, product experience 4/10.** The next phase must shift investment from "polishing the engine" to "building the intake valves and the steering wheel."

---

## Phase 1: Core Completeness

> Demo-versions only implement the happy path. Identify what is missing for the core loop to close.

### Core Loop Definition

```
Capture -> Structure (create/link/decay) -> Consumption (resolve/recall/browse)
  ^                                                              |
  |______________ Feedback (validate/maturity upgrade) ___________|
```

### Loop Closure Status

| Stage | Mechanism | Status |
|-------|-----------|--------|
| **Capture** | `codememory create` CLI + MemoryForm UI | Warning: Single-item manual entry only; no bulk pipeline |
| **Structure** | `imports` explicit dependency declaration + `suggest_deps` CLI | Warning: Dependency inference is CLI-only; Form has no autocomplete |
| **Consumption** | Resolve DAG + Overview + Focus + Wander + Search | Healthy: Core pipeline is complete and elegant |
| **Feedback** | Validate + stale detection + maturity upgrade + decay risk | Healthy: Passive feedback loop is complete |

### C1: Bulk Import Pipeline in Web UI -- Critical

**Current state:** The system provides `codememory import --file notes.txt --extract preferences` as a CLI command and API endpoint, but the Web UI has zero import entry points. MemoryForm only supports single-card manual creation. `suggest_deps.py` provides three-layer filtered automatic dependency inference -- but is only exposed through CLI.

**Why this is a core completeness problem:** For any knowledge management tool, "cold start" is the first retention barrier. If a user has 100 old notes, 50 solved-problem Markdown files, or an existing Obsidian vault, they need:
1. A **visible import entry point** (drag-and-drop zone, file picker)
2. A **preview-and-confirm flow** (see what will be created before committing)
3. **Post-import automatic dependency inference** (after importing 100 memories, automatically run suggest-deps and display suggestions in UI)

None of these exist today. Users must import via CLI then manually refresh the UI -- for a product that claims to be a "second brain," this is a fatal experience fracture.

**Recommendation:** Add an "Import" button to Dashboard or main nav -> multi-file Markdown drop zone -> preview table (id/summary/tags/estimated imports) -> bulk confirm creation + trigger suggest-deps.

**Estimated effort:** ~3 days

### C2: Import Suggestion UI in MemoryForm -- Critical

**Current state:** `suggest_deps.py` backend logic is complete, but in the Web UI's MemoryForm, users must manually type every import as comma-separated ID strings. No autocomplete. No suggestion list. No "board-style" related memory recommendations.

**Why this is a core completeness problem:** The DAG's quality depends on edge accuracy. If users must manually input every dependency, graph accuracy will rapidly deteriorate beyond ~20 memories. The entire value proposition of the DAG memory protocol (deterministic dependencies over probabilistic similarity) is undermined by the inaccuracy of hand-typed imports.

**Recommendation:** Add a "Suggest Dependencies" button next to the Imports field in MemoryForm -> async call to a new suggest-deps API endpoint -> display suggestions as a checkable list (with match scores and filter rationale) -> user checks/unchecks to auto-populate imports.

**Estimated effort:** ~1 day

### C3: Writable MCP Tools -- Important

**Current state:** 4 of 5 MCP tools are marked `readOnly`. Agents can **read** memories but cannot **write** them. This creates a paradox: Agents are the primary consumers of the memory system, but knowledge generated during agent sessions must be manually transcribed back into the system by a human.

**Why this is a core completeness problem:** If CodeMemory is positioned as "the external brain for AI Agents," the Agent must be able to update the brain during reasoning. A `propose_memory` pattern (staging mode, requires human approval) is a reasonable security middle path.

**Recommendation (R16 deferred):** Implement `propose_memory` and `propose_update` MCP tools that write as `maturity: draft` + `status: proposed`. Add a "Proposed" queue in Web UI for human review/approval.

**Estimated effort:** ~2 days

### C4: Full-Text Body Search -- Important

**Current state:** SearchBar supports substring/fuzzy matching against ID, summary, tags, and first 120 characters of body. But it does **not index the full body content** for search. If a user doesn't remember the exact ID or summary wording but remembers a key concept from the body, they cannot find it.

**Why this is a core completeness problem:** Search is the "escape hatch" of memory tools. When DAG navigation and browsing both fail, full-text search is the last retrieval mechanism. Currently this escape hatch is half-closed.

**Recommendation (R16 planned):** Refactor the search pipeline to index and search body full-text. Consider adding frontend "search result highlighting" and "match position preview."

**Estimated effort:** ~2-3 days

---

## Phase 2: Competitive Gaps

> Research comparable products; identify missing "table stakes."

### Competitive Landscape (2026)

```
                    AI-Nativeness -->
                    Traditional Notes     AI-Assisted          AI-Native
                  +------------------+-------------------+------------------+
     Team         |                  |                   |                  |
      ^           |   Confluence     |    Notion AI      |                  |
      |           |   GitBook        |   (GPT-4.1/       |                  |
      |           |                  |    Claude 4)      |                  |
     Solo         |   Obsidian       |                   |   Mem.ai         |
      |           |   (local/AI       |  CodeMemory <---- |   (AI auto-org)  |
      |           |    plugins)       |  (DAG + decay)    |                  |
     Developer/   |                  |                   |                  |
     Agent        |   Git repos      |  HGP              |  SHIMI           |
      v           |                  |  DragonScale      |  SwiftMem        |
                  |                  |  LCM              |                  |
                  +------------------+-------------------+------------------+
```

### Key Competitor Profiles

| Dimension | Obsidian | Notion AI | Mem.ai | CodeMemory |
|-----------|----------|-----------|--------|------------|
| **Data model** | Markdown files + backlinks | Block-based databases | AI-organized notes | Markdown + DAG imports |
| **Retrieval** | Graph view + keyword search | Keyword + AI Q&A | Semantic search | DAG resolution + fuzzy search |
| **AI approach** | Community plugins (Copilot 970K+ downloads) | Native (GPT-4.1/Claude 4), $10/user/mo | AI-native from day 1 | MCP tools (5, 4 readOnly) |
| **Data ownership** | Full -- local plain files | Cloud-only, vendor lock-in | Cloud-only | Full -- local .md files |
| **Import** | Drag-and-drop + community plugins | .csv/.md/.html + migration tools | AI extraction from Apple Notes/Gmail | CLI only |
| **Price** | Free core; Sync $4-5/mo | Free tier; Plus ~$10/mo; AI +$10/mo | Free tier; Pro ~$15-24/mo | Open source |

### G1: Visible Import Entry Point -- Critical

**Competitor standard:** Obsidian supports Markdown file drag-and-drop + community plugins for bulk import (Notion/Evernote/Roam). Notion supports .csv/.md/.html import + native migration tools. Mem.ai auto-extracts from Apple Notes/Google Keep/email via AI.

**CodeMemory state:** CLI-only `codememory import`. Web UI zero import entry points.

**Gap severity:** This is the most basic table stake. A user's first question upon seeing the product: "How do I get my data in?" The current answer: "Open a terminal and type a command."

### G2: AI-Assisted Creation -- Important

**Competitor standard:** Notion AI proactively offers "summarize/translate/rewrite/continue" on selected text. Mem.ai suggests related notes and auto-tags in real-time as the user types. Obsidian's Copilot plugin (970K+ downloads) provides ChatGPT/Claude access within the editor.

**CodeMemory state:** MemoryForm is a plain text form. No AI assistance -- no auto-summary generation, no auto-tag suggestion, no "based on body content, recommend related memories."

**Gap severity:** This is CodeMemory's biggest cognitive dissonance -- it's a memory system designed **for AI Agents**, but humans creating memories in the UI receive zero AI help.

**Recommendation:** Add an "AI Assist" button beside the body field in MemoryForm -> call LLM Gateway (exists but not integrated into frontend) -> provide auto-summary extraction, tag suggestions, and related-memory link recommendations.

**Estimated effort:** ~2 days

### G3: Semantic Search -- Important

**Competitor standard:** Mem.ai's core differentiator is semantic search -- natural language queries like "What did I write about the Johnson account?" directly return relevant notes. Notion AI supports cross-workspace semantic Q&A. Obsidian community plugins (Smart Connections) provide vector embedding search.

**CodeMemory state:** Design philosophy explicitly rejects vector search in favor of deterministic DAG resolution. This IS a differentiation strength (see Phase 4), but it also means **when the user doesn't know the exact ID or tag, there is no backup retrieval path.**

**Gap severity:** Medium. Deterministic DAG is a better long-term approach, but the short-term absence of semantic search means the product has a blind spot in "cold memory discovery" scenarios (user vaguely remembers a concept but not the ID). The Wander mechanism partially fills this gap but cannot replace active search.

**Recommendation (non-urgent):** Consider adding optional vector embeddings to support hybrid search (Hybrid Search = DAG resolution + semantic recall), complementary to, not replacing, DAG. Semantic recall results display as "Suggested to review," not overriding the deterministic resolution pipeline.

**Estimated effort:** ~5 days

### G4: Responsive/Mobile Experience -- Nice-to-have

**Competitor standard:** Obsidian has a native mobile app. Notion and Mem have responsive Web + native mobile apps. Mem 2.0 specifically strengthened offline support and voice capture mode.

**CodeMemory state:** Interface designed for large screens (1200px+). The `min-width: 360px` MemoryDetail panel still causes content squeeze on small screens. Graph view is unusable on touch devices.

**Gap severity:** Low priority. CodeMemory's current target audience is developers and AI agents, who predominantly use desktop. But when the product enters consumer markets, mobile becomes mandatory.

### G5: Multi-User / Collaboration -- Nice-to-have

**Competitor standard:** Notion offers real-time collaboration, comments, and permission management. Obsidian supports up to 10 users via Sync but lacks real-time collaboration.

**CodeMemory state:** Pure single-user. File-system locks create race conditions on concurrent writes.

**Gap severity:** Low priority. The current "personal second brain + AI Agent brain" positioning doesn't require collaboration. But future team knowledge base positioning would require solving this.

---

## Phase 3: Feature Depth

> Are existing features just "skin-deep"?

### D1: Create/Edit Form -- Shallow

**Completed:** Slide-out panel form (MemoryForm), supports id/summary/tags/intensity/body/maturity/status/imports/changenote fields. Template selector. Tag autocomplete. Import strength selector. Unsaved changes warning. Exit animations.

**Missing:**
- **Markdown preview:** body field is a plain textarea; no rendered preview visible during editing. User must save, close panel, then open MemoryDetail to see rendered output.
- **Auto-summary:** No "generate summary from body" button.
- **Import suggestion integration:** imports field is fully manual (Phase 1 C2).
- **Version history preview:** changelog data exists but is not integrated into the edit flow -- user cannot see previous versions before editing.

### D2: Graph View -- Adequate

**Completed:** Cytoscape graph rendering. Node styling based on type/intensity/maturity. Edge differentiation by strength (required thick / recommended dashed / related thin). Right-click context menu (Edit/Delete/Resolve). Node click opens MemoryDetail. Zoom controls. Layout switching. Directory-based color grouping.

**Missing:**
- **Graph-search linking:** Search-matched nodes are not highlighted in the graph view -- search results and graph view are two disconnected spaces.
- **Graph walk mode:** Interactive graph exploration mode was deferred in negotiation. Competitors (Obsidian graph view) offer richer interactivity (local graph expansion, path-tracing animation).
- **Time view:** No time dimension for the memory graph -- cannot see "these memories were created simultaneously" or "this period saw a burst of related memory creation" temporal clustering.

### D3: Resolve Panel -- Deep

**Completed:** Resolve button triggers DAG assembly. Skeleton loading screen. Node tree display (FULL/SUMMARY/SKIPPED with color coding). Error feedback. Stale/Pin notices. "Generate Prompt" button copies LLM-ready context. Budget/depth controls.

**Highlight:** The `buildPromptContent()` function generates prompts containing complete maturity weighting guidance (proven > verified > draft), status awareness (active > archived), and node index ordering. This is an **under-recognized killer feature** -- directly converting DAG resolution results into LLM-usable structured context.

### D4: Dashboard -- Adequate

**Completed:** Stats cards (total/stale/proven). Maturity distribution. Tag frequency cloud. Stale memory list. Wander button. Validate button. Reindex button. Decay risk display (R15). Exit animations for modals.

**Missing:**
- **Trend view:** Dashboard only shows current snapshot, no timeline -- cannot see "how many memories were created in the past 30 days" or "stability change trends."
- **Sortable list:** Decay risk list shows 3-5 high-risk memories but lacks full sortable list (negotiation I5 deferred).
- **Review queue:** Passive warnings (decay risk) exist, but active review mechanism is missing (deferred to R16).

### D5: Search -- Shallow

**Completed:** SearchBar supports substring + fuzzy matching. Tag/type/status/maturity filtering. Search results display snippet + match_quality indicator.

**Missing:**
- **Full-text body search:** Does not search body full-text (R16 planned).
- **Search result highlighting:** Matched terms are not highlighted.
- **Graph view linking:** Search results do not highlight corresponding nodes in graph view (D2).
- **Search result clustering:** All results displayed as flat list; no grouping by tag/directory/maturity.
- **Search history / saved searches:** No search history; cannot save frequent searches.

---

## Phase 4: Differentiation and Wow Factor

> What features could make this product uniquely dominant in the market?

### Core Differentiator: DAG Dependency Resolution + Token Budget Constraints -- Market-Unique

This is CodeMemory's strongest strategic weapon. In 2026, almost all AI memory tools rely on vector similarity search to "guess" related memories. CodeMemory takes a fundamentally different approach: **memory loading is a compilation problem, not a search problem.**

What this enables:
- **Deterministic, not probabilistic:** Given the same memory ID, `resolve` returns the identical DAG topology, unaffected by embedding model drift.
- **Auditable:** Users see precise dependency chains (A imports B imports C), not "AI thinks these memories are related (similarity 0.87)."
- **Token-budget-aware:** In a world where AI agents have strict context window constraints, CodeMemory's "required -> recommended -> full depth -> token budget trim" pipeline is the only scheme that guarantees no budget overflow.

**But the competition is closing in:** HGP (History Graph Protocol) and LCM (Lossless Context Management) are developing similar structured DAG approaches. HGP has even gone further -- adding evidence trails (support/refute relationships) and CRDT synchronization. CodeMemory needs to continue deepening its differentiation, not resting at the current implementation level.

### Recommended Differentiation Deepening Directions

#### DF1: Semantic Edges -- Differentiation Strengthener

**Current state:** imports distinguish `required | recommended | related` strength levels, but don't express semantic relationships.

**Differentiation opportunity:** Extend edge schema with `semantic_type` field:
- `supports` -- Memory A supports Memory B's conclusion
- `contradicts` -- Memory A contradicts Memory B
- `extends` -- Memory A extends/deepens Memory B
- `prerequisite` -- Must understand A before B

**Wow factor:** When Resolve assembles context, semantic edges translate into LLM instructions: "Memory A supports Memory B's core hypothesis; Memory C contradicts Memory B's data source." This carries orders of magnitude more information than "Memory A recommended Memory B." HGP is already doing this -- CodeMemory needs to keep pace.

**Estimated effort:** ~5 days

#### DF2: "Since You Last Visited" Context Injection -- Experience Differentiator

**Current state:** Dashboard displays decay risk but doesn't convert it into consumable context.

**Differentiation opportunity:** Implement a "Since You Last Visited" summary -- whenever the user opens Dashboard or an Agent starts a new session, automatically display:
- Memories created since last visit
- Top 3 memories at highest decay risk (suggested review)
- Updated/obsoleted memories (stale)

This aligns with Mem.ai's "proactive note suggestions" philosophy, but is driven by DAG topology (not semantic similarity), displaying **structured cognitive gaps** rather than probabilistic associations. Deferred in negotiation, but high-value differentiation.

**Estimated effort:** ~2 days

#### DF3: DAG-Aware AI Editing Sidebar -- Killer Differentiator

**Current state:** MemoryForm is a purely manual form.

**Differentiation opportunity:** When the user edits Markdown in the MemoryForm body field, a sidebar or inline suggestion panel displays in real-time:
1. **Dependency graph preview** -- the current memory's position in the DAG (based on existing imports and suggestions)
2. **Conflict detection** -- "You're editing a memory about X, but Memory Y's conclusion conflicts with your current edit"
3. **Context completion** -- "Based on your DAG, you may need to reference Memory Z"

This has no competitor in the current market. It leverages CodeMemory's unique deterministic DAG advantage to provide a structured editing experience that neither Notion AI nor Mem.ai can offer.

**Estimated effort:** ~8 days

#### DF4: Memory Health Score -- Experience Differentiator

**Current state:** Decay risk displays retrieval probability, but not a composite health score.

**Differentiation opportunity:** Calculate a composite "health score" per memory: combining staleness status, maturity level, decay risk, access frequency, and dependency count. Dashboard top section displays "Memory Library Health Overview" -- similar to GitHub's contribution heatmap, but tracking the overall health of the memory system (how many memories are fresh, how many need review, how graph connectivity is changing).

This contrasts with Mem.ai's "auto-organization" -- CodeMemory gives you **controllable, auditable health metrics**, not a black-box "AI organized it for you" experience.

**Estimated effort:** ~3 days

---

## Technical Health (Incidental Scan)

> Brief scan -- not a full audit, but attention to "which technical issues become bottlenecks as features pile up."

### TH1: God Objects -- Important

| File | Lines | Risk |
|------|-------|------|
| `backend/server.py` | 1419 | All 17 endpoints in one file; merge conflict hotspot |
| `frontend/src/App.tsx` | 1655 | Hosts state management, theming, shortcuts, global error handling |

**Impact:** Manageable at current team size (1-2 people). But each new feature adds 50-150 lines to server.py and 50-100 lines to App.tsx. If the team expands to 3+ people, these two files will quickly become bottlenecks.

**Recommendation:**
- Backend: Introduce `APIRouter` to split endpoints (`routers/memories.py`, `routers/search.py`, `routers/stats.py`, etc.)
- Frontend: Introduce state management (Zustand or Context API) to separate App.tsx state noise

**Estimated effort:** ~3 days

### TH2: File-Based Index Bottleneck -- Important

**Current state:** index.json file-based reads/writes. Each write triggers full/partial rebuild; current baseline ~200ms at <200 nodes is acceptable.

**Bottleneck prediction:** At >1000 nodes, concurrent read/write lock contention becomes a performance bottleneck. Particularly the search endpoint -- which iterates all memories and reads body files per query -- becomes a multi-second operation at 1000+ nodes.

**Recommendation:** Before crossing 500 nodes, consider introducing SQLite as an index backend (preserve .md files as source data; index.json -> index.db as search cache).

**Estimated effort:** ~4 days

### TH3: CSS Architecture -- Nice-to-have

**Current state:** Heavy reliance on inline styles; approximately 70% of the 6,045 lines of component code is CSS. No CSS modules, TailwindCSS, or styled-components.

**Impact:** As dark mode/theme system complexity increases, maintenance costs grow linearly. But at the current scale (12 components), this is not an urgent issue.

**Estimated effort:** ~3 days (incremental migration)

### TH4: Test Coverage -- Healthy

**Current state:** 57 unit tests + 24 integration tests + 5 API smoke tests + 5 Playwright smoke tests = 91 total tests, 100% passing. For a high-velocity project, this regression safety net is rare and reassuring.

**What's missing:** No frontend component-level tests (Playwright smoke tests are integration-level). Component tests (React Testing Library) would catch regression categories like "component renders with 0 interactive elements."

**Estimated effort:** ~2 days

---

## Prioritized Recommendations

### Critical (product cannot enter next phase without these)

| # | Recommendation | Effort | Phase | R16 Status |
|---|---------------|--------|-------|------------|
| C1 | **Bulk Import Pipeline (Web UI)**: drag-drop Markdown import + preview confirmation + auto dependency inference | ~3 days | 1, 2 | Not yet included |
| C2 | **MemoryForm Import Autocomplete**: suggest_deps integration into MemoryForm | ~1 day | 1 | R16 candidate |
| C3 | **Full-Text Body Search**: index body full-text + search result highlighting | ~2-3 days | 1, 3 | R16 committed (Evolution Strategist C1) |

### Important (impacts product competitiveness and user experience)

| # | Recommendation | Effort | Phase |
|---|---------------|--------|-------|
| I1 | **Writable MCP Tools** (`propose_memory` + `propose_update`) | ~2 days | 1 |
| I2 | **AI-Assisted Creation**: LLM Gateway integration into MemoryForm (auto-summary/tags/related recommendations) | ~2 days | 2 |
| I3 | **God Object Split**: server.py APIRouter + App.tsx state management | ~3 days | TH |
| I4 | **Review Queue**: from passive decay warnings to active review mechanism | ~1.5 days | 3 |
| I5 | **Graph-Search Linking**: search results highlight in graph view | ~0.5 day | 3 |
| I6 | **Markdown Preview**: body rendering preview in MemoryForm | ~0.5 day | 3 |

### Nice-to-have (completes the experience, can be deferred)

| # | Recommendation | Effort | Phase |
|---|---------------|--------|-------|
| N1 | **Dashboard Trend View**: timeline charts (creation trends / decay trends) | ~2 days | 3 |
| N2 | **CSS Modernization**: TailwindCSS or CSS modules migration (incremental) | ~3 days | TH |
| N3 | **Frontend Component Tests**: React Testing Library coverage for key components | ~2 days | TH |
| N4 | **Responsive Degradation**: small-screen / touch device adaptation | ~3 days | 2 |
| N5 | **Search History + Saved Searches** | ~0.5 day | 3 |
| N6 | **Time-Dimension Graph View**: color by creation time clustering | ~1 day | 3 |

### Feature Ideas (long-term differentiation strategic assets)

| # | Recommendation | Effort | Phase |
|---|---------------|--------|-------|
| F1 | **Semantic Edges**: extend imports schema, add `supports/contradicts/extends/prerequisite` semantic types | ~5 days | 4 |
| F2 | **DAG-Aware AI Editing Sidebar**: real-time related memory display, conflict detection, context completion during editing | ~8 days | 4 |
| F3 | **"Since You Last Visited" Context Summary**: auto-inject change summary on session start | ~2 days | 4 |
| F4 | **Memory Health Score + Contribution Heatmap** | ~3 days | 4 |
| F5 | **Hybrid Search**: optional vector embeddings + DAG resolution dual-path retrieval | ~5 days | 3, 4 |
| F6 | **SQLite Index Backend**: replace file-based index, break through 1000+ node bottleneck | ~4 days | TH |
| F7 | **Memory Branching / Merge**: Git-style branch management, support experimental memory topology modifications (inspired by Git for Agents) | ~10 days | 4 |

---

## Six-Month Strategic Roadmap

### Months 1-2: Break the Cold Start (The Input Problem)
- **Week 1-2:** God Object split (server.py APIRouter + App.tsx state management) -- clear the foundation first
- **Week 3-4:** Bulk import pipeline (drag-drop Markdown -> preview -> batch create -> auto trigger suggest-deps)
- **Week 5-6:** MemoryForm import autocomplete (suggest_deps integration) + Markdown preview
- **Week 7-8:** Full-text body search + search result highlighting

### Months 3-4: AI Collaboration and Interaction Deepening
- **Week 9-10:** AI-assisted creation (LLM Gateway integration into MemoryForm)
- **Week 11-12:** Writable MCP tools (`propose_memory` + `propose_update`)
- **Week 13-14:** Review queue + Dashboard trend view
- **Week 15-16:** Graph-search linking + time-dimension graph view

### Months 5-6: Differentiation Moat Deepening
- **Week 17-20:** Semantic Edges (semantic edge schema extension + Resolve instruction block generation)
- **Week 21-22:** "Since You Last Visited" context injection
- **Week 23-24:** Hybrid search (optional vector embeddings) + SQLite index backend POC

---

## Bottom Line

**CodeMemory has validated the technical feasibility of the DAG memory protocol and built a tastefully restrained dark-mode UI. The next step is NOT to continue polishing the engine -- it is to equip the engine with intake valves (bulk import) and an AI co-pilot system -- so that both humans and Agents can frictionlessly enter and exit this memory system.**

The strategic window is narrow: HGP, LCM, and DragonScale are racing to build DAG-native agent memory from the research side, while Mem.ai, Notion AI, and Obsidian's plugin ecosystem are attacking from the consumer experience side. CodeMemory's unique position -- deterministic DAG resolution with a consumer-grade UI -- is defensible but not permanent. The next two months must close the Input Problem.

---
*End of report.*
