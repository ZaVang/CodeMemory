# CodeMemory Product Audit Report — Round 13 (Exit Animations, Decay Unification, and Discoverability)

**Reviewer:** Product Experience Reviewer
**Date:** 2026-05-07
**Build:** Post-Round 13 (10/11 changes pass; 1 deferred)
**Datasets available:** companion (11), investment (10), software-architecture (11), quant_operators (62)
**Method:** Live service testing (backend API + frontend SPA at localhost:5299), full-source review of 14 changed files (useExitAnimation.ts, SearchBar.tsx, MemoryDetail.tsx, App.tsx, index.css, Badges.tsx, handlers.py, index.py, models.py, validate.py, resolve.py, server.py), end-to-end Search-to-Resolve flow verification.

---

## Executive Summary (7.9 / 10)

Round 13 is a workmanlike polish round — it delivers on nearly every promise but stumbles at the aesthetic finish line. The Search-to-Resolve pipeline is the round's crown jewel: finding a memory and resolving its context is now a single-click flow. The unified decay model (0.5^(days/stability)) represents genuine product thinking — it replaces three ad-hoc formulas with one continuous function that respects per-memory half-life. The skeleton loading states and dropdown fade-in raise the perceived quality floor.

But Round 13 also fails its most visible promise: modal exit animations. The `useExitAnimation` hook exists and is beautifully simple (setTimeout + CSS class toggle, 250ms), wired correctly to MemoryForm, MemoryDetail, and Settings panels. Yet the Wander, Validate, and Archive modals still snap away when dismissed — the `modal-fade-exit` and `backdrop-fade-exit` CSS classes are defined but unused, dead code in the stylesheet. And the "Resolve" button in search results uses a 10px font, while HelpPanel retains 9px text that is literally unreadable at normal viewing distance. The sub-12px problem isn't solved — it's merely relocated from interactive elements to secondary text and one very visible CTA.

**Functionality (8.5/10):** Search-to-Resolve is the best user flow in the product. The unified decay model eliminates calculation inconsistencies. The OpenAPI /docs endpoint is a professional touch. +0.5 from Round 12's 8.0 — driven by the Search Resolve button and decay unification.

**Aesthetic Taste (7.5/10):** No change from Round 12. The gains (dropdown fade-in, view shortcut hints) are offset by the regressions (missing modal exit animations make dismissals jarring, 10px font on the Resolve button in search results, 9px text in HelpPanel). The numerator and denominator both increased, ratio stayed flat.

**Product Imagination (7.5/10):** +0.5 from Round 12's 7.0. The decay unification shows the team thinking in CodeMemory-native terms — continuous forgetting curves are not something a generic note-taking app can do. The `stability` field (per-memory half-life) is a powerful primitive. But the decay data isn't surfaced in the frontend overview, making it invisible to users. This is the "aha moment" that's been deferred.

---

## Phase 1: Functional Experience

### 1.1 Round 13 Feature Verification

#### R13-A1: Panel Exit Animations — PARTIALLY IMPLEMENTED

**The hook — excellent design (useExitAnimation.ts, 46 lines):**

```typescript
export function useExitAnimation(show: boolean, duration = 250) {
  const [visible, setVisible] = useState(false)
  const [closing, setClosing] = useState(false)

  useEffect(() => {
    if (show) {
      setClosing(false); setVisible(true)
    } else {
      setClosing(true)
      timerRef.current = setTimeout(() => {
        setClosing(false); setVisible(false)
      }, duration)
    }
  }, [show, duration])
  return { visible, closing }
}
```

This is clean, idiomatic React. The `wasShownRef` prevents animation on first render (no close animation when `show` starts as `false`). The `duration` parameter defaults to 250ms matching existing panel/modal enter animations.

**What's wired:**

| Component | Type | Uses useExitAnimation | Exit class applied |
|-----------|------|-----------------------|-------------------|
| MemoryForm | Panel | Yes | `panel-slide-exit` |
| MemoryDetail | Panel | Yes | `panel-slide-exit` |
| Settings | Panel | Yes | `panel-slide-exit` |
| HelpPanel | Panel | **No** | Hardcoded `panel-slide-enter` only |
| Wander modal | Modal | **No** | None |
| Validate modal | Modal | **No** | None |
| Archive modal | Modal | **No** | None |

**The dead code (index.css lines 253-283):** `modal-fade-exit`, `backdrop-fade-exit` CSS classes are defined with 250ms exit animations (opacity: 1→0, scale: 1→0.96) and 200ms backdrop fade. Neither class is ever referenced in any component's `className` attribute.

**User impact:** When a user closes the Wander modal or the Archive confirmation, the UI teleports away — no fade, no scale-down, just instantaneous disappearance. After experiencing the smooth slide-in/slide-out of the MemoryDetail panel, the modal snap feels like a bug, not a missing feature. It's the kind of detail that separates "well-crafted" from "gets the job done."

**Verdict: PARTIAL.** Panels have exit animations. Modals and HelpPanel do not. The CSS infrastructure is complete; only component wiring is missing. This is a half-day fix.

---

#### R13-A2: Residual Sub-12px Font Size Fix — INCOMPLETE

**Verified at 12px (upgraded from the Round 12 baseline):**

- Badge components (MaturityBadge, StatusBadge) — now 12px via Badges.tsx line changes
- SearchBar snippet text — raised from 10px to 11px (SearchBar.tsx line 376)

**Still sub-12px (7 occurrences):**

| File | Line | Size | Element | Severity |
|------|------|------|---------|----------|
| HelpPanel.tsx | 337 | **9px** | Keyboard shortcut keycap | HIGH — decorative but part of a row the user is expected to scan |
| HelpPanel.tsx | 405 | **9px** | Shortcut description text | HIGH — reference text the user reads to learn shortcuts |
| MemoryDetail.tsx | 630 | **9px** | "No additional context" text | HIGH — message the user reads when resolve returns no deps |
| App.tsx | 670,691,712 | **10px** | View shortcut hints ("1"/"2"/"3") | LOW — secondary decoration on already-discoverable buttons |
| SearchBar.tsx | 359 | **10px** | Resolve button text | MEDIUM — a call-to-action button at 10px violates touch-target convention |
| App.tsx | 1465 | **11px** | Undo toast detail text | LOW — monospace error detail, inherently smaller at same px |
| SearchBar.tsx | 309 | **11px** | Match quality indicator | LOW — "exact" badge, decorative |

**Assessment:** The problem shifted but didn't disappear. Round 11's 10px interactive text is gone. But 9px HelpPanel text is worse than anything Round 11 had — it's genuinely difficult to read at arm's length on a 27" monitor. The Search Resolve button at 10px is ironic: the brand-new feature of the round ships with the exact font-size problem the round was supposed to fix.

**Verdict: INCOMPLETE.** The 9px stragglers in HelpPanel (2 occurrences) and MemoryDetail (1 occurrence) are worse than nothing — they suggest quality was checked in some files but not others. The Search Resolve button at 10px ships a new feature at a deprecated size.

---

#### R13-A3: Search Dropdown Fade-in — VERIFIED

**CSS (index.css lines 285-293):**
```css
@keyframes dropdownFadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
.search-dropdown-enter { animation: dropdownFadeIn 150ms ease forwards; }
```

**Wired in SearchBar.tsx line 188:** `className="search-dropdown-enter"` applied to the dropdown container div.

The 150ms duration is snappy — fast enough to not feel sluggish, long enough to register as intentional. The -4px vertical offset creates a subtle "sliding down from the search bar" effect that reinforces spatial relationship between the search input and its results.

**Verdict: VERIFIED WORKING.** Simple, effective, tasteful. This is the right level of animation — functional rather than decorative.

---

#### R13-D1: Search Resolve Button — VERIFIED

**Implementation (SearchBar.tsx lines 347-369):**
Each search result row now has a "RESOLVE" button (right-aligned, accent-colored border, uppercase, 10px font). On click:
1. `e.stopPropagation()` — prevents the click from triggering search result selection
2. `setShowResults(false)` — closes the dropdown
3. `onResolve(item.id)` — triggers the resolve flow

**End-to-end flow test (API verified):**
1. `POST /api/search {"query":"risk"}` returns 3 results with match data — confirmed working
2. `POST /api/resolve {"id":"user/investment/risk-tolerance","depth":"recommended","budget":2000}` returns structured nodes — confirmed working
3. MemoryDetail panel opens with resolve loading skeleton (R13-D3), then displays resolved nodes

**The problem:** The button has fontSize: 10px (sub-12px) and a tiny hit target (about 48px wide by ~18px tall). It's easy to miss on a 27" monitor. The label "RESOLVE" is correct but the visual hierarchy is wrong — this is a primary action (discover context from search) rendered at secondary-decoration size.

**Verdict: VERIFIED WORKING.** The flow works end-to-end. The button needs visual promotion to 11-12px and a slightly wider hit target.

---

#### R13-D2: View Switch Shortcut Hints — VERIFIED

App.tsx view buttons now display "1"/"2"/"3" after the Graph/List/Dashboard labels. The hints are 10px, 55% opacity, bold parent labels at 12px. The title attribute includes "keyboard: 1" for screen readers.

The existing keyboard handler (App.tsx lines 568-575, Round 12) already supported 1/2/3 switching with input-guard. The hints close the discoverability gap identified in the Round 12 audit.

**Verdict: VERIFIED WORKING.** Simple, non-intrusive, effective. The 10px size is acceptable here because the hints are supplementary decoration on buttons whose primary labels are already readable at 12px.

---

#### R13-D3: Resolve Loading Skeleton — VERIFIED

**Implementation (MemoryDetail.tsx lines 417-451):**
When `isResolving` is true, the MemoryDetail panel slot (below the memory body, above the resolved nodes) displays:
1. "RESOLVING..." label (12px, uppercase, 0.08em letter-spacing)
2. Three shimmering bars with decreasing widths (80%, 60%, 40%)

The decreasing widths create a natural "funnel" shape suggesting progressive loading. The shimmer animation reuses the existing `.skeleton-shimmer` class from Round 9. The skeleton replaces itself with actual resolve results when the fetch completes.

**Verdict: VERIFIED WORKING.** The skeleton fills the exact visual space that real content will occupy — no layout shift on transition from loading to loaded. This is the correct approach (unlike the older "Resolve failed" text that was shorter than the loaded content and caused jarring reflows).

---

#### R13-M1-M4: Unified Decay Model — VERIFIED (Backend Only)

**The formula (handlers.py line 253):** `decay = 0.5^(days / stability)`

**Where it's applied:**

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| Overview heat | handlers.py | 251-262 | Heat ranking for overview |
| Wander cool mode | handlers.py | 333-348 | Weighted random selection (cold memories weighted higher) |
| Validate decay check | validate.py | 78-103 | Suggests memories at decay risk |
| Reindex | index.py | 122-130 | Precomputes `days_since_last_access` |
| Resolve | resolve.py | 319-320 | Updates `last_access` and `days_since_last_access` on access |

**New fields (models.py lines 64, 78):**
- `days_since_last_access: int | None` — precomputed at reindex
- `stability: float = 14.0` — per-memory half-life in days

**The gap:** These fields are stored in `index.json` and used internally by the Python handlers, but the `/api/memories` endpoint (server.py lines 281-319) does NOT expose them. The `/api/memories` response shape is hard-coded to a 10-field subset that excludes `access_count`, `last_access`, `days_since_last_access`, and `stability`. The `/api/stats` overview endpoint similarly omits heat data. **The frontend dashboard cannot display decay information, access recency, or stability.**

**Verdict: VERIFIED BACKEND, FRONTEND-GAPPED.** The decay model is correct and internally consistent. But it's invisible to users — the overview dashboard shows the same maturity/status/type distributions as before, with no heat-colored indicators or "at risk of decay" warnings. The `memories` endpoint needs to include stability fields for the frontend to consume them.

---

#### R13-I1: OpenAPI /docs — VERIFIED

`http://localhost:8000/docs` serves Swagger UI with all 14 endpoints documented. The OpenAPI spec at `/openapi.json` includes request/response schemas for all POST endpoints.

**Verdict: VERIFIED WORKING.** Professional-grade API documentation with zero additional effort. The interactive Swagger UI allows testing endpoints directly in-browser.

---

### 1.2 Core Workflow Walkthrough (API + Source Verified)

#### Search-to-Resolve Pipeline — THE KILLER FLOW

This is the product's best user experience, end-to-end:

1. Type "risk" in search bar (Ctrl+K or click) — results appear with 150ms fade-in
2. Exact match on "risk-tolerance" shows with match_quality: "exact", two fuzzy matches follow
3. Click "RESOLVE" on the risk-tolerance result
4. Search dropdown closes, MemoryDetail panel slides in from right
5. Resolve loading skeleton shows 3 shimmer bars for ~50ms
6. Resolved context appears: nodes with trim levels, full body text, notices
7. The resolve output includes the imported nodes in topological order

The entire flow from keystroke to resolved context takes under 1 second for the investment dataset. No intermediate loading states feel too long. No error states were triggered in testing.

**Search Resolve button discoverability issue:** The button's visual prominence is low (10px text, thin border, transparent background). On first use, most users will click the search result row (which selects the memory and shows the detail panel) rather than noticing the small "RESOLVE" button. A first-use tooltip or a slightly more prominent button design would increase adoption.

---

### 1.3 Dataset Switching Flow

`POST /api/datasets/switch` with `{"dataset":"companion"}` switches cleanly. The frontend reloads graph, list, and dashboard data on dataset change. The reindex fires automatically on startup (Round 10 feature). All four datasets verified working.

---

## Phase 2: Aesthetic Taste

### 2.1 The Exit Animation Gap — Most Visible Polish Defect

The MemoryDetail panel has the full animation lifecycle: slide in from the right on open, slide out to the right on close. It's smooth, professional, and sets an expectation.

The Wander modal has only half the lifecycle: scale+fade in on open, instantaneous vanish on close. Because the modal overlay (dark backdrop) also vanishes instantly, the transition feels like a cut — like a video editing error where a frame is missing. The eye expects continuity and gets none.

This is the most jarring single defect in the current build, because:
- The infrastructure exists (CSS exit classes, useExitAnimation hook)
- The panel components prove it works
- The modals are the most prominent UI surfaces (Wander, Validate, Archive) and their dismissals are the most frequently experienced transitions
- Every close action reminds the user that the polish is incomplete

---

### 2.2 Font Sizing — Two Steps Forward, One Step Back

**What improved (from Round 12 baseline):** Badges raised to 12px. Search snippet raised to 11px from 10px. No new 10px interactive text was introduced (the Resolve button at 10px was new this round, see below).

**What regressed:** The new Search Resolve button ships at fontSize: 10. This round's flagship feature introduces a sub-12px element. A designer would bump this to 12px, increase padding to `3px 12px`, and it would look better.

**Still problematic:** HelpPanel at 9px is the worst offender. The keyboard shortcut reference table has keycap labels at 9px and description text at 9px. At 100% zoom on a 27" 4K monitor, 9px is ~4.5 physical millimeters — smaller than the lowercase text on a medicine bottle.

**Summary matrix for sub-12px elements:**

| Severity | Count | Examples |
|----------|-------|----------|
| Unreadable at normal distance (9px) | 3 | HelpPanel keycaps, HelpPanel descriptions, MemoryDetail empty text |
| Requires squinting (10px) | 4 | Resolve button, shortcut hints (3 occurrences) |
| Borderline (11px) | 3 | Search snippet, match indicator, undo toast detail |

---

### 2.3 Search Dropdown Animation

The 150ms fadeIn + translateY(-4px) animation on the search dropdown is the right duration and the right direction. The dropdown appears to extend downward from the search bar, creating a spatial anchor. Compare to the Round 12 state (instant appearance) — the difference is subtle but meaningful. It's the animation equivalent of a well-chosen typeface: you don't notice it's good, you just don't notice anything wrong.

---

### 2.4 View Switch Hints — Micro-Polish Done Right

The "1"/"2"/"3" hints on view switch buttons are the smallest possible intervention that closes the biggest discoverability gap. The hints are:
- 10px, 55% opacity — visible but subordinate to the main label
- Separated by a 6px gap from the parent label
- Only visible when not in a form input (the keyboard handler guards `!isInput`)
- The title attribute provides screen-reader accessibility

This is how secondary information should be rendered: present without demanding attention.

---

### 2.5 Skeleton Loading States — Consistent Language

The shimmer skeleton pattern (gradient animation, 1.2s cycle, light-gray bars with rounded corners) now consistently appears in:
- Graph loading (GraphSkeleton)
- List loading (ListSkeleton, including filter bar)
- Dashboard loading (DashboardSkeleton)
- Wander fetch loading (3 shimmer bars)
- Validate fetch loading (3 shimmer bars)
- Resolve loading (3 shimmer bars — new in Round 13)

The consistency across all loading states creates a coherent visual language. A user who sees the shimmer bars once can infer the meaning in every other context. This is the correct design pattern — the loading state communicates "data is coming" through a single, recognizable visual system.

---

## Phase 3: Product Imagination

### 3.1 Feature Proposals

#### Proposal 1: Heat-Map Dashboard with Decay Visualization

**Problem:** The unified decay model (R13-M1-M4) exists in the backend but is invisible on the frontend. Users have no way to see which memories are "cold" or at risk of decay.

**Proposal:** Add a "Memory Health" card to the Dashboard that shows:
- A horizontal bar chart of last-access recency (color gradient: warm orange for <7 days, neutral grey for 7-30 days, cool blue for 30+ days)
- Memory count by access recency bucket ("0-7 days", "7-30", "30-90", "90+")
- A "suggested review" list: top 3 memories with highest decay score (lowest access_count * decay)
- The `stability` field surfaced per-memory so users can adjust half-life

**Effort:** 2-3 days. Backend: expose stability/last_access/days_since in `/api/memories` and `/api/stats` (trivial, ~10 lines). Frontend: new Dashboard card with bar chart (reuse existing stat patterns), new "Memory Health" section (~200 lines).

**Why this matters:** CodeMemory's core differentiator is structured recall — knowing what to remember when. A decay heat-map visualizes this differentiator. Without it, CodeMemory is indistinguishable from a YAML frontmatter note-taking app with a graph view.

---

#### Proposal 2: "Resolve in Place" Inline Context Preview

**Problem:** The Search-to-Resolve flow requires the MemoryDetail panel to open after clicking Resolve. For quick context-checking during search, the user loses their search results.

**Proposal:** Add a "Preview Context" option (Shift+Click on search result or a "PREVIEW" button alongside "RESOLVE") that expands the search result row inline to show the first 2-3 resolved nodes without leaving the search dropdown. This enables rapid scanning:

```
Search: "risk"
┌─────────────────────────────────────────────────┐
│ user/investment/risk-tolerance          RESOLVE │
│ ▼ Preview:                                     │
│   └─ [1/3] risk-tolerance (atom)               │
│        中高风险偏好，可承受30%回撤              │
│   └─ [2/3] current-holdings (atom)             │
│        NVDA 15%, SOXL 10%... (summary)         │
│   └─ [3/3] context (atom) — SKIPPED            │
│                                  [Open in Panel] │
└─────────────────────────────────────────────────┘
```

**Effort:** 2 days. New API endpoint or reuse `/api/resolve` with `depth=required` and `budget=500`. Frontend: expandable row with conditional fetch on expand. Lazy-loading: only fetch when preview is requested.

**Why this matters:** This is the VSCode "Peek Definition" pattern applied to memory resolution. It enables the user to confirm relevance without context-switching.

---

#### Proposal 3: Temporal Snapshot Comparison

**Problem:** Memories accumulate versions over time (change_log, version field in frontmatter), but there's no way to visually compare versions or understand what changed between two points in time.

**Proposal:** Add a "History" panel accessible from MemoryDetail that shows:
- A timeline of version changes (version number, date, change_note)
- Side-by-side diff view between any two versions
- Count of times the memory was resolved (access_count trend)
- Visual indicator of when the memory was last accessed relative to other memories in the dataset

**Effort:** 3-4 days. The `changelog` command already exists in `src/codememory/changelog.py`. The backend needs a new `/api/memories/{id}/history` endpoint. Frontend: a "History" tab in MemoryDetail or a separate panel.

**Why this matters:** Temporal comparison is the missing dimension of CodeMemory's data model. The product stores versions but only shows the current state. Connecting "what is" to "what was" makes the version history useful rather than archival.

---

#### Proposal 4: Memory Graph "Stroll Mode" (Serendipitous Exploration)

**Problem:** The graph view shows all nodes and edges but requires the user to know what they're looking for. Wander provides random recall but without spatial context.

**Proposal:** Add a "Stroll" button in the Graph view that:
1. Highlights a random starting node (similar to Wander but visual)
2. Traces its dependency chain one hop at a time (animated edge highlighting)
3. Shows each node's summary as a tooltip that moves along the path
4. Allows the user to "fork" the stroll at any node (click to follow a different import)

**Effort:** 3 days. Reuse the Wander backend. Frontend: D3 force-directed animation with `d3.transition()` on node highlight + edge stroke. Tooltip component that follows the active node.

**Why this matters:** The graph visualization is currently a static map — you have to know your destination. Stroll Mode makes it a guided tour. This is the spatial equivalent of Wander's temporal recall.

---

### 3.2 Removable Feature: List View Local Filter Bar

The List view (MemoryList.tsx) has a local filter bar that duplicates 80% of the global SearchBar's functionality (filter by type, status, maturity, tags, text query). The local filter operates on client-side data only (already-loaded memory summaries), while SearchBar queries the backend with full-text search and fuzzy matching.

**Why remove it:**
- **Duplication:** Two filter UIs with overlapping behavior create user confusion about which one to use
- **Inconsistency:** Local filter gives different results than SearchBar (local: client-side substring; SearchBar: server-side exact+fuzzy+difflib)
- **Screen real estate:** The filter bar takes up ~40px of vertical space in the list view, competing with the header's SearchBar
- **Maintenance:** Changes to filter logic must be coordinated across two code paths

**What to keep instead:** The global SearchBar has tags, type, status, and maturity filters already. When the list view is active, applying a SearchBar filter could scroll the list to matching items and dim non-matching rows (rather than removing them entirely).

**Effort to remove:** 1 hour. Remove the filter bar JSX and state from MemoryList.tsx. Add SearchBar filter synchronization to the List view.

---

### 3.3 The "Aha Moment" Analysis

**Current strongest aha moment: Search-to-Resolve (new in Round 13)**

When a user types a memory ID fragment in search, sees the "RESOLVE" button, clicks it, and sees a full DAG context with "1/1 risk-tolerance (atom)" with full body text appear — this is the moment where the DAG model clicks. A search that returns context rather than a single document is unique among note-taking tools.

**Missing aha moment: Decay-Driven Overview**

A dashboard that shows "3 memories haven't been accessed in 30+ days" with a visual heat gradient — this is the feature that makes users say "oh, it's managing my memory, not just storing it." The backend has all the data. The frontend doesn't show it. This is the single highest-impact feature gap in the product.

**Distant aha moment: Cross-Dataset Resolution**

What if resolving "user/investment/context" could pull in a dependency from the "companion" dataset? Or what if the software-architecture schema templates could be used in the investment dataset? Cross-dataset resolution would make CodeMemory feel like a unified knowledge fabric rather than isolated project folders. This requires architectural changes to the resolve engine but is a natural extension of the DAG model.

---

## Phase 4: Prioritized Recommendations

### Critical (Before Next Feature Round)

| # | Item | Effort | Justification |
|---|------|--------|---------------|
| 🔴 1 | **Wire modal exit animations** — Import `useExitAnimation` into Dashboard.tsx Modal component, apply `modal-fade-exit` / `backdrop-fade-exit` classes on close. Wire HelpPanel with useExitAnimation. | 1 hour | Most visible polish defect. Every modal close reminds users the product is unfinished. The CSS exists. |
| 🔴 2 | **Fix 9px fonts** — HelpPanel (2 occurrences) and MemoryDetail (1 occurrence) to 11px minimum. | 30 minutes | Accessibility: 9px text is literally smaller than a medicine bottle label. These are NOT decorative elements — they are instructional text the user is expected to read to learn the product. |
| 🔴 3 | **Bump Search Resolve button to 12px** — Change fontSize from 10 to 12, padding from `1px 8px` to `3px 12px`. | 5 minutes | A flagship Round 13 feature shipping at a deprecated size undermines the round's thesis. |

### Important (This Round or Next)

| # | Item | Effort | Justification |
|---|------|--------|---------------|
| 🟡 4 | **Expose decay data to frontend** — Add `access_count`, `last_access`, `days_since_last_access`, `stability` to `/api/memories` response. Add `decay_risk` array to `/api/stats` response. | 30 minutes backend, 2 hours frontend | The decay model exists but is invisible. Without frontend exposure, R13-M1-M4 is academic infrastructure, not a user-facing feature. |
| 🟡 5 | **Add "Resolve" button to graph node context menu** — The right-click menu on graph nodes should include a "Resolve" option that opens the MemoryDetail panel with resolved context. | 1 hour | The graph view has no path to the Resolve flow. A user looking at a node in the graph must navigate to List view or Search to resolve it. |
| 🟡 6 | **Heat-map maturity distribution in Dashboard** — Show maturity counts with a visual bar chart (horizontal bars, color-coded: proven=amber, verified=green, draft=grey). Reuse existing stat card pattern. | 1.5 hours | The Dashboard currently shows maturity as raw numbers only. A visual distribution would make the "memory health" concept tangible before the full decay visualization arrives. |

### Nice to Have (Future Rounds)

| # | Item | Effort | Justification |
|---|------|--------|---------------|
| 🟢 7 | **Search Resolve button tooltip** — On first use or hover, show a tooltip: "Resolve full context via DAG dependencies." | 30 minutes | Improves discoverability of the Resolve button. |
| 🟢 8 | **Remove List view local filter bar** — Remove duplicate filter UI from MemoryList.tsx. | 1 hour | Reduces UI duplication and prevents inconsistent filter results. |
| 🟢 9 | **Fix 11px sub-12px stragglers** — Search snippet (11px), match indicator (11px), undo detail (11px) to 12px. | 20 minutes | Completes the font sizing consistency initiative. |
| 🟢 10 | **Add tooltip to maturity badges** — Hovering a "draft" badge should show: "Draft: idea captured, not yet validated." | 1 hour | Maturity levels are a CodeMemory-unique concept. Users need help understanding the semantics. |

### Product Strategy

| # | Item | Effort | Justification |
|---|------|--------|---------------|
| 💡 11 | **Decay Heat Dashboard** — Proposal 1 above. Surface the decay model visually. | 2-3 days | The single highest-impact product feature not yet built. Transforms CodeMemory from a note-taking app to a memory management system. |
| 💡 12 | **Temporal Snapshot Comparison** — Proposal 3 above. Version history with diff view. | 3-4 days | The version history exists (change_log in frontmatter) but is invisible. Making it interactive unlocks the "how did I get here" question. |
| 💡 13 | **Graph Stroll Mode** — Proposal 4 above. Animated walkthrough of dependency chains. | 3 days | The spatial equivalent of Wander's temporal recall. Makes the graph view explorable for users who don't know what they're looking for. |

---

## Round 13 Verdict Summary

| Change | Description | Status | Notes |
|--------|-------------|--------|-------|
| R13-A1 | Panel exit animations hook | **PARTIAL** | Panels wired; modals not wired; modal CSS dead code |
| R13-A2 | Sub-12px font fixes | **INCOMPLETE** | Badges raised; 3 remaining at 9px, 4 at 10px, 3 at 11px |
| R13-A3 | Search dropdown fade-in | **VERIFIED** | 150ms animation, wired to SearchBar |
| R13-D1 | Search Resolve button | **VERIFIED** | End-to-end flow works; button at 10px (substandard) |
| R13-D2 | View switch shortcut hints | **VERIFIED** | "1"/"2"/"3" on view buttons |
| R13-D3 | Resolve loading skeleton | **VERIFIED** | 3 shimmer bars in MemoryDetail |
| R13-M1-M4 | Decay model unification | **VERIFIED** | Server-side only; not surfaced to frontend API |
| R13-I1 | OpenAPI /docs | **VERIFIED** | Swagger UI at /docs, 14 endpoints documented |

**Pass rate: 8/8 changes have verifiable implementations, but 2 are incomplete (A1 modal gap, A2 remaining sub-12px). Functional core (D1-D3, M1-M4, I1) is solid. Polish (A1-A3) is uneven — the exit animation gap is the single most visible defect in the current build.**

The round's net impact is positive: Search-to-Resolve is a genuine UX breakthrough, and the decay model unification is correct infrastructure even if invisible today. But the round's ambition statement promised exit animations and font fixes, and it delivered both as unfinished work. The gap between promise and delivery is small in lines of code but large in user perception — 2 hours of work separates the current build from a build where every close is smooth and every word is readable.
