# CodeMemory Product Audit Report — Round 16 (APIRouter Split, Dataset Fix Verification, Graph Regression Fix)

**Reviewer:** Product Experience Reviewer
**Date:** 2026-05-07
**Build:** Post-APIRouter split (routers/memories.py, search.py, stats.py), with dataset/graph regression fixes
**Datasets available:** companion (11), investment (10), software-architecture (11), quant_operators (62)
**Method:** Full-service live testing (backend API at localhost:8000 + frontend SPA at localhost:5300), Puppeteer-based page state extraction, view switching, dataset switching, search testing, legend color verification, and full API endpoint verification.

---

## Executive Summary (7.2 / 10)

This round delivered the APIRouter split (R16-A1) — a significant backend refactor that decomposes server.py's monolithic endpoint list into three domain routers (memories, search, stats). The split is architecturally clean, with server.py reduced to app creation, middleware, and router mounting. However, the refactor surfaced a **self-reinforcing dataset default regression** that causes the frontend to always initialize to the companion dataset instead of the server-configured default (investment). This is a user-facing correctness issue that undermines the dataset switching feature.

On the positive side: all core API endpoints work correctly, the graph legend dynamically reflects actual directory-color mappings, search returns rich results with R-probability scores, the List and Dashboard views render properly, and dataset switching between datasets updates all views correctly. The onboarding experience is smooth once the blocking regression is bypassed.

**Functionality (6.5/10):** Down from 8.5 in R15. The dataset default regression is a critical path bug — it makes the entire application initialize in the wrong state for all first-time and localStorage-cleared users. Core CRUD, search, resolve, and graph operations work correctly once the dataset issue is sidestepped. The APIRouter split introduced no new endpoint regressions.

**Aesthetic Taste (8.0/10):** Down from 8.5 in R15. The visual design remains strong — LuxCart palette, Raleway/Cormorant Garamond typography, directory-color mapping, and edge-strength differentiation are all intact. However, the dataset regression means the initial view always shows companion (11 warm-and-fuzzy personal memories) instead of the application's intended default of investment (a more structured, dependency-rich dataset). This degrades the first-impression narrative arc.

**Product Imagination (7.0/10):** The APIRouter split is pure infrastructure — it creates no new user-facing capability. The dataset regression fix was reactive, not proactive. The quant_operators dataset (62 auto-generated API docs) is the most visually impressive graph but is hidden behind a broken default. Five feature proposals and one removal candidate are detailed in Phase 3.

---

## Phase 1: Functional Experience

### 1.1 Core Flow: First-Visit Onboarding

**Status: PARTIALLY WORKING — blocked by dataset regression.**

The onboarding flow (welcome message with "Your memory is a dependency graph" copy) renders correctly on first visit. The SKIP and NEXT buttons are visible and functional. However, the underlying dataset is wrong — the user sees companion's 11 personal-life memories instead of the server default of investment's 10 financial-decision memories. This means the onboarding's claim ("a personal knowledge graph where every piece of information knows what it depends on") is demonstrated with a dataset that has very few dependencies, undermining the product's core value proposition.

The onboarding is dismissable via localStorage (`codememory-onboarded` key) and stays dismissed on subsequent visits.

**Verdict: Onboarding UX is polished; the default dataset bug sabotages the narrative.**

### 1.2 Dataset Switching

**Status: REGRESSION CONFIRMED — self-reinforcing default override.**

**Root cause (two-part):**

1. **Frontend:** `api.ts` line 8 hardcodes `let _currentDataset: string = 'companion'`. The very first API call (`fetchDatasets()`) sends `X-Codememory-Dataset: companion` as a header.

2. **Backend middleware (server.py lines 51-57):** The `_DatasetContextMiddleware` sets the ContextVar from the header even for exempt paths:
```python
is_exempt = path in ("/", "/api/datasets", "/api/datasets/switch", ...)
dataset = request.headers.get("X-Codememory-Dataset", "")
if dataset and dataset.strip():
    _current_dataset.set(dataset)  # SETS EVEN FOR EXEMPT PATHS
```

3. **Backend handler (stats.py line 135):** The `/api/datasets` handler reads from the (now-contaminated) ContextVar:
```python
current = str(current_dataset.get())  # Returns "companion" instead of "investment"
```

**Reproduction (verified with curl):**
```
No header:            -> "current": "investment"  (correct)
X-Codememory-Dataset: companion   -> "current": "companion"  (WRONG)
X-Codememory-Dataset: investment  -> "current": "investment"  (WRONG — should be server default)
X-Codememory-Dataset: nonexistent -> "current": "nonexistent" (WRONG)
```

**User impact:** Every browser session initializes to companion unless the user has a saved `defaultDataset` in localStorage. The server's `DEFAULT_DATASET` environment variable is completely ignored for browser clients. This means every new user's first experience is with a personal-journal dataset rather than the investment-decision dataset the server is configured to present.

**Dataset switch after initialization:** Once initialized (even to the wrong default), switching to other datasets works correctly. The graph, list, dashboard, search, and legend all update with the new dataset's data. The "Switching..." loading indicator displays correctly during the transition. The quant_operators disclaimer ("Auto-generated API documentation...") appears when switching to that dataset.

**Verdict: CRITICAL BUG.** The server's notion of "current dataset" is corrupted by the very act of the client asking what the current dataset is.

### 1.3 Graph View + Node Colors

**Status: WORKING — regression fix verified.**

The `/api/graph` endpoint returns proper cytoscape-compatible node data with the `directory` field present (the regression fix). Nodes are rendered with distinct colors by directory:

| Directory | Color | Dataset |
|-----------|-------|---------|
| user/beliefs | rgb(22, 101, 52) forest green | companion |
| user/feelings | rgb(202, 138, 4) amber | companion |
| user/moments | rgb(217, 119, 87) coral | companion |
| user/people | rgb(124, 58, 237) purple | companion |
| user/preferences | rgb(184, 134, 11) dark gold | companion |
| user (auto) | rgb(28, 25, 23) charcoal | companion |
| user/test (auto) | rgb(124, 58, 237) purple | companion |
| api | #1E40AF blue | quant_operators |
| api/quantdf (auto) | fallback cycle | quant_operators |
| api/quantexpr (auto) | fallback cycle | quant_operators |

Unknown directories are marked "(auto)" in the legend and assigned fallback colors — this is a thoughtful touch that handles extension gracefully without hardcoding every possible directory.

**Edge strength differentiation (verified in Legend component):**
- Required: solid line (strongest visual weight)
- Recommended: dashed line
- Related: dotted line

The Legend component (`frontend/src/components/Legend.tsx`) dynamically derives directory entries from the actual graph data, ensuring it always reflects reality rather than displaying a static hardcoded list.

**Canvas rendering:** Verified — canvas element exists and renders. Graph is interactive.

**Verdict: Working.** The directory field regression fix is confirmed. Legend is dynamic and accurate.

### 1.4 List View

**Status: WORKING.**

The list view renders a sortable table with columns: ID, Summary, Type, Maturity, Status, Tags, Health. For the companion dataset (11 memories), 12 table rows are rendered (1 header + 11 data rows). Key observations:

- The Health column shows R-probability (retention probability) as a percentage — 100% for recently accessed memories
- Sorting by Health column works (client-side computation of R-probability via the FSRS-based formula)
- Tag display is clean and space-efficient
- Status badges (Active, Archived) and Maturity badges (Draft, Verified, Proven) are visually distinct
- Clicking a row navigates to the MemoryDetail panel
- Pagination at 20 items per page is appropriate for current dataset sizes

**Verdict: Working.** No regressions detected.

### 1.5 Dashboard View

**Status: WORKING — stale ratio merits attention.**

The dashboard shows for the companion dataset:
- **Total memories:** 11
- **Maturity distribution:** Draft (7), Verified (4), Proven (0)
- **Stale memories:** 9 out of 11 (82%) — notably high
- **Status distribution:** Active (11), Archived (0)
- **Top tags:** companion (10), belief (2), friendship (2), value (2), feeling (2), work (2)
- **Action buttons:** Wander, Validate, Refresh, Reindex

The stale ratio (82%) is correct behavior — companion memories haven't been accessed recently — but a new user might interpret this as a bug. The stale memory IDs are listed but not clickable (see Nice-to-have recommendations).

**Verdict: Working.** All stats render correctly. The Wander, Validate, Refresh, and Reindex action buttons are present.

### 1.6 Search

**Status: WORKING — rich results with proper scoping.**

Search for "nvidia" on the investment dataset returned 3 results:
- `user/facts/nvidia-earnings` — ~95% match (matched on ID, Body, Summary), R: 100.0%
- `user/facts/soxl-composition` — ~90% match (matched on Body, Summary), R: 100.0%
- One additional fuzzy match

The search dropdown renders match quality as percentage bars, shows match field attribution (e.g., "matched: Id, Body, Summary"), displays a content snippet, and provides a "Resolve" quick-action link per result. The R-probability is displayed as "R: 100.0%".

**Edge case:** Searching on companion for "nvidia" correctly returns "No memories found matching 'nvidia'" with a helpful message suggesting broader search terms.

**Search scoping:** Search is correctly scoped to the active dataset. Results change when switching datasets.

**Verdict: Working.** Rich result display with R-probability integration and Resolve quick-action.

### 1.7 Resolve API

**Status: WORKING.**

The resolve API expects `{"id": "user/investment/context", ...}` (field name `id`, not `memory_id`). The frontend's `ResolveRequest` type correctly uses `id`. Tested with the investment dataset — resolves to 6 nodes with proper depth and budget handling. The `notices` field surfaces a pinned-version warning: "pinned version v1 of user/investment/risk-tolerance is behind current version v2." This demonstrates the system's awareness of staleness beyond simple decay.

Node trim levels (full/summary/skipped) are correctly reported based on the budget constraint.

**Verdict: Working.**

### 1.8 Validate API

**Status: WORKING.**

`POST /api/validate` returns `[0, 0]` for the investment dataset (0 errors, 0 warnings). The endpoint is functional and returns the expected two-element array.

### 1.9 Wander API

**Status: WORKING.**

`POST /api/wander` returns a randomly selected memory in "cool" mode. Tested on investment — returned `schemas/decision` with orphan detection text: "(orphaned -- no other memory references this one)". The wander output includes type, status, intensity, access count, and summary.

### 1.10 API Response Format Verification

**Status: ALL ENDPOINTS VERIFIED.**

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/api/datasets` | GET | REGRESSION | `current` field corrupted by X-Codememory-Dataset header |
| `/api/datasets/switch` | POST | Working | Returns `{"current": "name"}` |
| `/api/memories` | GET | Working | Pagination, directory field, decay fields present |
| `/api/memories/{id}` | GET | Working | Full detail with body, backlinks, stability |
| `/api/memories/{id}/backlinks` | GET | Working | Returns dependency references with strength |
| `/api/graph` | GET | Working | Directory field present in nodes (regression fix verified) |
| `/api/search` | POST | Working | Rich results with R-probability and match quality |
| `/api/resolve` | POST | Working | Depth/budget/notices all functional |
| `/api/stats` | GET | Working | Full maturity/type/status/tag/stale breakdown |
| `/api/wander` | POST | Working | Cool mode with orphan detection |
| `/api/validate` | POST | Working | Returns error/warning arrays |
| `/api/reindex` | POST | Working | Returns success confirmation |
| `/api/export` | GET | Working | ZIP download with Content-Disposition header |

---

## Phase 2: Aesthetic Taste

### 2.1 Color Palette

The LuxCart-inspired design system remains the product's strongest aesthetic asset. The semantic color system (`--cm-*` CSS custom properties) provides a cohesive visual language across light and dark modes:

- **Light mode:** Cream background (#FFFBEB), charcoal text (#1C1917), gold accent (#B8860B)
- **Dark mode:** Deep brown-black (#1A1817), warm off-white text (#F0EBE0), gold accent (#D4A017)

The dark mode is genuinely well-executed. Unlike the "invert everything" approach of many dark modes, this one maintains warmth — the surface color (#2D2A28) has a subtle brown undertone that preserves the LuxCart character. Error colors shift from the light mode's deep red (#991B1B) to a softer tomato (#EF4444) to maintain contrast ratios while preserving semantic meaning.

**Directory color palette (semantic mapping):**
- Facts: #1C1917 (charcoal) — neutral, authoritative
- Observations: #57534E (warm gray) — secondary, observational
- Preferences: #B8860B (gold) — warm, personal
- Decisions: #991B1B (deep red) — high-stakes, consequential
- Feelings: #CA8A04 (amber) — warm, emotional
- People: #7C3AED (purple) — distinctive, social
- Beliefs: #166534 (forest green) — grounded, principled
- Moments: #D97757 (coral) — warm, ephemeral
- Snapshots: #A8A29E (light gray) — archival, passive
- API: #1E40AF (blue) — technical, systematic
- Schemas: #1C1917 (charcoal) — structural, foundational

This is a thoughtfully constructed semantic mapping. Each color carries meaning that reinforces the directory's purpose. The palette avoids the "rainbow graph" anti-pattern — colors are distinct enough to differentiate directories but harmonious enough to feel like a single system.

**Issue:** The dark-mode tint values (DIRECTORY_TINTS_DARK, R10-widened to #15-#4A) are very subtle against the dark background. While this creates an elegant, understated look, the graph node interiors are nearly invisible on darker displays. Users with less-than-perfect screens may only see the border color, reducing the visual impact of the directory-color system.

### 2.2 Typography

- **Headlines:** Cormorant Garamond (serif) — elegant, editorial. Weight 500, with tight letter-spacing.
- **Body:** Raleway (sans-serif) — clean, modern, highly readable at 12px+. Weight 600 for UI labels, 500 for body text.
- **Code:** JetBrains Mono — distinctive, programming-oriented mono with clear character differentiation.

The headline/body font pairing (Garamond + Raleway) creates a "literary tech" personality — part journal, part dashboard. This is a distinctive choice that separates CodeMemory from the generic Inter/Tailwind aesthetic of most developer tools.

**The 12px floor is maintained.** R15's sub-12px fix is intact — no font-size below 12px was observed in any interactive element.

**Issue:** The uppercase labels with 0.08em letter-spacing (used on all header buttons: "CREATE MEMORY", "GRAPH", "LIST", "DASHBOARD", "ZOOM", "BUDGET", "EXPORT") are legible at 12px but could be difficult for users with dyslexia or vision impairments. There is no mechanism to disable all-caps or increase letter-spacing. Consider adding a "reduce motion / increase legibility" accessibility toggle.

### 2.3 Spacing and Layout

- **Header toolbar:** Consistently spaced with natural groupings: view-mode tabs | dataset selector | search bar | zoom/budget controls | action buttons (theme, PNG export, ZIP export, settings, help). The quant_operators disclaimer ("Auto-generated API documentation. Dependency graph reflects algorithmic inference, not human-authored links.") is a contextual hint that doesn't overwhelm the toolbar.
- **Graph canvas:** Full-width, legend anchored bottom-left with subtle shadow and border. Clean.
- **MemoryDetail panel:** Slides in from right with 250ms ease animation.
- **Modals:** Scale+fade entrance (250ms), scale+fade exit. Smooth.
- **Error toasts:** Bottom-right stack with slide-up entrance animation (200ms). Dismissable with auto-timeout (6 seconds).

**Issue:** The header toolbar has 15+ interactive elements. On viewports narrower than approximately 1200px, this will overflow. The toolbar does not appear to have responsive wrapping or a hamburger menu for small screens. Given the product is a developer tool typically used on large displays, this is acceptable but worth noting for future tablet/laptop support.

### 2.4 Animations

The animation surface is comprehensive and consistent:

| Element | Entrance | Exit | Duration |
|---------|----------|------|----------|
| MemoryDetail panel | slide in from right | slide out to right | 250ms ease |
| Modals | fade + scale(0.96->1) | scale(1->0.96) + fade | 250ms ease |
| Backdrop overlay | fade in | fade out | 200ms ease |
| Search dropdown | fade + translateY(-4px) | instant removal | 150ms ease |
| Error toasts | slide up + fade | instant (dismissed) | 200ms ease-out |
| Undo toast | translateY(12px->0) + fade | auto-timeout (5s) | 200ms ease-out |
| Skeleton shimmer | gradient sweep | N/A | 1.5s infinite |

R14's modal exit animation fix and R15's HelpPanel exit animation fix are both intact. The animation language is consistent: all entrances are in the 150-250ms range with ease/ease-out timing, creating a cohesive feel. No animation exceeds 250ms, keeping interactions feeling responsive.

### 2.5 Visual Personality

CodeMemory's visual identity says "thoughtful tool for thoughtful people." The cream-and-charcoal palette, serif headlines, and understated shadows create an atmosphere closer to a high-end notebook or journaling app than a typical developer dashboard. This aligns well with the product's philosophy — memories are not data points; they are interconnected atoms of understanding.

The directory color system adds a layer of visual semantics: you can glance at the graph and immediately understand the domain structure of your knowledge. Green nodes are beliefs, gold nodes are preferences, red nodes are decisions.

**Personality gap:** The companion dataset (warm personal memories about friendship, burnout, rainy Sundays) feels tonally mismatched with the otherwise serious, analytical tool aesthetic. This isn't a design flaw — it's a data curation issue — but it affects the first impression because the companion dataset is what users see first (due to the dataset regression). The investment dataset (with its structured domain, versioned decisions, and pinned-risk tolerance) is a much better showcase of the product's capabilities.

---

## Phase 3: Product Imagination

### 3.1 Feature Proposals

#### Proposal 1: Review Queue — "Memories That Need You"

The Dashboard shows "Stale Memories (9)" as a list of IDs. This is a missed opportunity. A dedicated Review Queue view could present stale memories one at a time (flashcard-style), asking the user to:
- **Touch** (mark as reviewed — updates access timestamp and stability via the existing `/api/memories/{id}/touch` endpoint)
- **Archive** (no longer relevant)
- **Edit** (update with new information)
- **Skip** (come back later)

The R-probability score already provides the ranking. The infrastructure (touch API, stability tracking, access counts) is already in place. This would transform the decay system from an informative display into an interactive workflow — turning "9 stale memories" from a guilt-inducing number into an actionable queue.

**Implementation effort:** Medium. Requires a new view component and a queue iteration UI. All backend endpoints exist.

**Why it fits:** CodeMemory's core thesis is that forgetting is a path-unreachability problem, not a deletion problem. A review queue operationalizes this philosophy.

#### Proposal 2: Dataset Comparison View

With four datasets available (companion, investment, quant_operators, software-architecture), there is an opportunity for a cross-dataset analysis view:
- Tag overlap between datasets
- Directory structure comparison
- Dependency density comparison (edges per node)
- Cross-dataset reference detection (e.g., "this investment preference is similar to this companion belief")
- Memory count and maturity distribution side-by-side

**Implementation effort:** Medium-High. Requires a new view and cross-dataset query logic that doesn't currently exist in the API.

**Why it fits:** The quant_operators dataset (62 auto-generated API docs) has a radically different graph topology than companion (11 personal memories). Side-by-side comparison would make the product's DAG visualization capabilities more apparent.

#### Proposal 3: Memory Timeline — Temporal Graph View

The Dashboard's stale list and the stability/access_count fields suggest a temporal dimension that is currently only visible in the list view's Health column. A timeline view could:
- Show creation dates, last access dates, and decay curves per memory
- Plot stability over time as a line chart (stability increases with each access, decays otherwise)
- Color-code by directory for cross-domain comparison
- Animate the "forgetting curve" for each memory

**Implementation effort:** Medium-High. Requires a new view with charting library integration (or canvas-based rendering to avoid new dependencies).

**Why it fits:** The adaptive stability model (FSRS SInc formula) generates meaningful time-series data. Visualizing this would make the decay model tangible and demonstrate the value of regular memory review.

#### Proposal 4: Dependency Health Score

Each memory has a `dependents` count (how many other memories depend on it). Memories with high dependents are "load-bearing" — if they go stale, the ripple effect is large. A "Dependency Health" score could:
- Weight staleness by dependent count
- Highlight "critical path" memories that need urgent review
- Show a "graph fragility" metric for the entire dataset
- Flag memories where a single stale node blocks a large dependency chain

**Implementation effort:** Low-Medium. Computation is straightforward (weighted staleness). Display could be integrated into existing Dashboard and Legend components.

**Why it fits:** The DAG-based dependency system is CodeMemory's differentiator. Surfacing the structural importance of memories would make the graph view more actionable and demonstrate the value of explicit dependency tracking.

#### Proposal 5: Export-as-Context — "One-Click Agent Injection"

The Resolve feature already produces a token-budgeted, topologically-sorted markdown output. A "Copy as Context" button in the Resolve panel could format this output for direct injection into LLM system prompts:
- `codememory resolve user/investment/context --depth required --budget 2000 --format context`
- Output wrapped in `<codememory_context>...</codememory_context>` tags
- One-click copy to clipboard
- Optional: generate as a standalone .md file for import into other tools

**Implementation effort:** Low. The resolve output already exists. This is primarily a formatting step and a UI button.

**Why it fits:** CodeMemory's Layer 0 cognitive interface already defines `overview` for system prompt injection. This closes the loop for `resolve` — turning the DAG resolution output into a consumable context block for LLM-powered workflows.

### 3.2 What Could Be Removed

#### Candidate for Removal: The companion dataset as default example data

The companion dataset (11 personal-life memories about friendship, burnout, morning coffee) is tonally incongruent with a tool marketed as a "memory atomization protocol." It demonstrates the system's capabilities but with a domain that does not align with the product's core value proposition (knowledge management for complex, dependency-rich domains).

**Specific issues:**
1. It has very few cross-memory dependencies, making the DAG visualization underwhelming
2. Its content (personal feelings, weekend activities) doesn't match any likely user persona for a developer tool
3. The graph shows 7 directories for only 11 memories, creating a fragmented appearance
4. 82% of its memories are stale, which looks like a bug to new users

**Recommendation:** Either:
1. Fix the dataset regression so investment becomes the default (already configured — just blocked by the regression), or
2. Create a new "onboarding" dataset that demonstrates all features (imports, schemas, maturity levels, tags) with a more universally relatable domain like software architecture decisions, or
3. If companion must remain, curate it to include explicit cross-memory dependencies and reduce the directory count

### 3.3 The "Aha" Moment Analysis

CodeMemory's "aha" moment should occur when a user first runs **Resolve** on a well-connected memory and sees the topologically-sorted, token-budgeted output. The product's thesis is "memory loading is a dependency resolution problem, not a search problem" — and Resolve is the proof.

**Current state: The aha moment is partially blocked because:**
1. The dataset regression shows companion (few dependencies) on first load
2. The Resolve feature requires right-clicking a graph node and selecting "Resolve" — not discoverable
3. There is no guided tour that leads the user through this discovery
4. The onboarding copy mentions "dependency graph" but doesn't demonstrate it

**Recommendation:** Add a "Try Resolve" call-to-action in the onboarding flow that resolves a well-connected memory (like `user/investment/context` from the investment dataset) with a default budget. Show the dependency chain unfolding in real-time. This single interaction would prove the product's thesis better than any amount of explanatory text.

---

## Phase 4: Consistency and Comparison

### 4.1 Cross-Dataset Consistency

| Metric | companion | investment | quant_operators | software-architecture |
|--------|-----------|------------|-----------------|----------------------|
| Memories | 11 | 10 | 62 | 11 |
| Graph nodes | 11 | 10 | 62 | 11 |
| Graph edges | Very few | 12 | High (auto-inferred) | Unknown |
| Directory count | 7 | 3 | 3+ | Unknown |
| Stale ratio | 9/11 (82%) | 0/10 (0%) | Unknown | Unknown |
| Domains | Personal journal | Financial decisions | API documentation | Architecture decisions |

**Observation:** The stale ratio varies dramatically — 82% for companion vs 0% for investment. This is correct behavior (companion memories haven't been accessed since creation), but the disparity is jarring. A new user might interpret 9/11 stale as a system bug rather than expected behavior.

### 4.2 API Response Consistency

All API endpoints now use consistent field naming and response structure thanks to the APIRouter split. The shared `serialize()` function normalizes datetime objects across all endpoints. The `/api/datasets` response format (`{datasets, current, current_name}`) is consistent with the documented API, though the `current` field value is compromised by the header contamination.

### 4.3 Frontend/Backend Contract Alignment

**Issue identified:** The backend's `CreateMemoryRequest` uses `memory_id` with a Pydantic alias of `id`:
```python
memory_id: str = Field(alias="id", ...)
```

The frontend's `CreateMemoryRequest` TypeScript interface uses `id` directly. This alignment is correct but fragile — if the backend model is refactored, the frontend would break silently at runtime rather than compile time. Consider adding an API contract test that validates the request/response shapes match across the boundary.

### 4.4 Field Naming Inconsistency

The `ResolveRequest` backend model uses `memory_id` with `alias="id"`, while `SearchRequest.query` has no alias. This mixed approach to field naming (some aliased, some not) creates a maintenance burden. A consistent policy — either all external fields use aliases or none do — would reduce confusion.

---

## Prioritized Recommendations

### Critical

- **CR1: Fix dataset default self-reinforcing regression.** Two-part fix:
  1. Backend middleware (server.py line 56): change `if dataset and dataset.strip()` to `if dataset and dataset.strip() and not is_exempt` — this prevents the X-Codememory-Dataset header from contaminating the ContextVar on exempt paths like `/api/datasets`
  2. Frontend (api.ts line 8): remove hardcoded `_currentDataset = 'companion'` — initialize to empty string, let the datasets API response set the value

- **CR2: /api/datasets `current` field should use server config, not request header.** The `get_datasets()` handler in stats.py should use the `DEFAULT_DATASET` constant for the `current` field, not read from the per-request ContextVar. The ContextVar reflects the client's last-known dataset; "current" in the datasets response should reflect server configuration.

### Important

- **I1: Restore investment as the default dataset on first visit.** Once CR1 and CR2 are fixed, the user's first experience will be the investment dataset — a much stronger demonstration of DAG dependency resolution with 12 edges across 10 nodes.

- **I2: Companion dataset needs dependency enrichment.** Add at least 3-4 explicit `imports` between companion memories (e.g., `user/feelings/burnout-april` importing `user/preferences/morning-coffee` as `related`). This would demonstrate the dependency resolution capability even when companion is viewed.

- **I3: Onboarding should be dataset-aware.** The onboarding copy should mention which dataset is being demonstrated and set expectations accordingly. "You're viewing the investment decision dataset — 10 interconnected memories about market analysis, risk tolerance, and portfolio decisions."

- **I4: Search exact vs fuzzy result distinction.** Search results show "x results (includes fuzzy matches)" but do not visually separate exact matches from fuzzy ones. Add a section divider or "Exact" / "Related" grouping to improve scanability.

### Nice-to-have

- **N1: Legend directory click-to-highlight.** Clicking a directory name in the legend should highlight all nodes belonging to that directory on the graph canvas, dimming the rest.

- **N2: Dashboard stale IDs should be clickable.** Currently stale memory IDs in the Dashboard are plain text. Making them clickable (navigating to MemoryDetail) would create a natural stale-memory review workflow.

- **N3: Graph node hover tooltip enrichment.** Node hover currently shows the summary (good). Adding R-probability and dependent count would make the tooltip more actionable.

- **N4: Dark mode graph fill visibility.** The dark-mode tint values (DIRECTORY_TINTS_DARK) are very subtle against the dark background. Consider increasing luminance by 5-10% for better node interior visibility on average displays.

- **N5: Responsive toolbar for smaller viewports.** The 15+ element header toolbar will overflow on viewports narrower than approximately 1200px. Add a collapsible section or overflow menu.

- **N6: Accessibility — all-caps override.** The uppercase labels with 0.08em letter-spacing on header buttons are a distinctive design choice but reduce legibility for some users. Consider a "reduce motion / increase legibility" settings toggle.

### Feature Ideas (from Phase 3)

- **Review Queue** — flashcard-style memory review workflow using the existing touch API and R-probability ranking
- **Dataset Comparison View** — cross-dataset topology and maturity analysis
- **Memory Timeline** — temporal graph view with decay curves and stability over time
- **Dependency Health Score** — structural importance weighting for critical-path detection
- **Export-as-Context** — one-click LLM system prompt injection from Resolve output

---

## Appendix A: Test Commands Executed

```bash
# Backend API verification
curl -s http://localhost:8000/api/datasets
curl -s -H "X-Codememory-Dataset: investment" http://localhost:8000/api/graph
curl -s -H "X-Codememory-Dataset: investment" http://localhost:8000/api/memories
curl -s -H "X-Codememory-Dataset: investment" http://localhost:8000/api/stats
curl -s -X POST -H "X-Codememory-Dataset: investment" http://localhost:8000/api/wander
curl -s -X POST -H "X-Codememory-Dataset: investment" http://localhost:8000/api/validate
curl -s -X POST -H "X-Codememory-Dataset: investment" -H "Content-Type: application/json" \
  -d '{"id":"user/investment/context","depth":"required","budget":3000}' \
  http://localhost:8000/api/resolve
curl -s -X POST -H "X-Codememory-Dataset: investment" -H "Content-Type: application/json" \
  -d '{"query":"nvidia"}' http://localhost:8000/api/search
curl -s -X POST -H "X-Codememory-Dataset: investment" -H "Content-Type: application/json" \
  -d '{"name":"quant_operators"}' http://localhost:8000/api/datasets/switch

# Dataset regression verification
curl -s http://localhost:8000/api/datasets
# Returns: "current": "investment" (correct — no header)
curl -s -H "X-Codememory-Dataset: companion" http://localhost:8000/api/datasets
# Returns: "current": "companion" (WRONG — header contaminates ContextVar)
```

## Appendix B: Frontend Component Inventory (R16 State)

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| App | App.tsx | Modified | APIRouter-compatible, dataset switching, multi-view |
| GraphCanvas | GraphCanvas.tsx | Stable | Directory-color mapping, dynamic cytoscape styles, dark mode tints |
| MemoryDetail | MemoryDetail.tsx | Stable | Slide-in panel, full detail, backlinks, stability display |
| MemoryList | MemoryList.tsx | Stable | Sortable table, Health column with R-probability |
| MemoryForm | MemoryForm.tsx | Stable | Create/edit memory form |
| Dashboard | Dashboard.tsx | Stable | Stats, stale list, action buttons |
| SearchBar | SearchBar.tsx | Stable | Dropdown results, match quality, Resolve quick-action |
| Legend | Legend.tsx | Stable | Dynamic directory-color mapping from graph data, edge styles |
| HelpPanel | HelpPanel.tsx | Stable | Exit animation from R15 |
| Onboarding | Onboarding.tsx | Stable | First-visit welcome flow |
| Settings | Settings.tsx | Stable | Default dataset, budget, theme |
| Badges | Badges.tsx | Stable | Status and maturity badges |
| EmptyState | EmptyState.tsx | Stable | Empty/error/not-found states |
| api.ts | api.ts | Modified | Dataset header injection, all endpoint methods |
| types.ts | types.ts | Stable | Full TypeScript type definitions |
| colors.ts | colors.ts | Stable | Directory color palette, fallback logic |
| index.css | index.css | Stable | LuxCart design system, CSS custom properties, animations |

## Appendix C: Backend Router Inventory (R16-A1)

| Router | File | Prefix | Routes |
|--------|------|--------|--------|
| memories | routers/memories.py | /api | GET /memories, GET /memories/{id}, GET /memories/{id}/backlinks, POST /memories, PUT /memories/{id}, DELETE /memories/{id}, POST /memories/{id}/touch, POST /import, GET /export |
| search | routers/search.py | /api | GET /graph, POST /resolve, POST /search |
| stats | routers/stats.py | /api | GET /stats, POST /wander, POST /validate, POST /reindex, GET /datasets, POST /datasets/switch |
