# CodeMemory Product Audit Report — Iteration 10 (Deep Re-Examination)

**Reviewer:** Product Experience Reviewer
**Date:** 2026-05-06
**Build:** Post-Iteration 10 (f760fac)
**Datasets tested:** companion (10), investment (10), software-architecture (11), quant_operators (62)
**Method:** Headless browser deep exploration (puppeteer) + manual API verification + source code analysis

---

## Executive Summary (7.0/10)

CodeMemory is a product with genuinely sharp thinking at its core — the insight that memory loading is a dependency resolution problem, not a search problem — but the execution in the web management panel lags behind the ambition. The MCP server is a strategic home run that opens real agent integration, and the design system (LuxCart) shows taste. However, two concrete bugs undermine the core user workflow (dataset switching silently fails for List/Dashboard views; modals stack on top of each other), and several smaller frictions accumulate to make the product feel less polished than its conceptual foundations deserve.

The product passes functional verification (0 API errors, auto-reindex works, MCP server delivers all 5 tools) but fails the "would I trust this with my data?" gut check — not because of data integrity concerns, but because the UI doesn't yet inspire the confidence that a memory system should. Memory tools need to feel solid, permanent, and trustworthy. Right now the panel feels like a capable prototype rather than the permanent home for someone's knowledge graph.

**Score reasoning:** Starting from I9's 8.0/10 baseline, the I10 improvements (error queue, dark tints, header enforcement, MCP server, smoke tests) are real wins (+0.5). But the newly discovered dataset switching bug and modal stacking issue are high-severity UX regressions that would cause real-world user frustration (-1.0). The search not filtering graph view, REINDEX having no feedback, and various smaller frictions contribute to the remaining deduction (-0.5). The MCP server is excellent infrastructure but doesn't materially improve the primary web UI experience.

---

## Phase 1: Functional Experience

### 1.1 First Impression & Onboarding Path

**What works:**
- The onboarding appears immediately on first visit, blocking the full UI with a focused welcome message
- The tagline "Your memory is a dependency graph, not a search index" sets the right conceptual frame
- Two clear paths: SKIP (power user) or NEXT (guided tour)

**What doesn't:**
- The onboarding is ephemeral — after SKIP, there is no way to replay it. A HELP button exists but it's a reference manual, not a guided tour. For a product introducing a novel paradigm (DAG-based memory), this is a missed opportunity.
- The onboarding has no interactive elements — it's a passive text walkthrough. There's no "try clicking a node" or "try switching to List view" guided interaction.
- On first load with no persisted settings, the dataset defaults to "investment" rather than the first dataset alphabetically ("companion"). This is likely a server-side default, but the user has no way of knowing why investment was chosen.
- The onboarding text is exclusively in English with no localization support, while the memory data itself is in mixed Chinese/English (investment dataset's summaries are Chinese).

**Rating: 6/10** — Functional but forgettable. Gets the user to the app but doesn't make a memorable first impression.

### 1.2 Core Workflow Walkthrough

#### Graph View (Primary Experience)

The graph view is the product's centerpiece and it mostly delivers. Cytoscape.js + Dagre produces clean top-to-bottom dependency layouts. Nodes are color-coded by directory with the LuxCart palette, and the three edge types (required/recommended/related) are distinguishable.

**Good:**
- The Budget slider is a genuinely innovative UI control — it directly ties to the product's core value proposition (token-budgeted memory resolution)
- The Zoom slider gives users control over information density
- The Legend auto-derives from actual dataset directories
- Dark mode toggle is instant and covers the full canvas
- Right-click context menu provides direct access to View Details / Edit / Archive / Resolve (verified in code; not testable headlessly with Cytoscape)

**Issues found:**
- **Search bar doesn't filter the graph** — entering text in the search bar and pressing Enter has no visible effect on the graph nodes. The search input value persists (verified via DOM inspection) but the graph remains unchanged. This is a critical disconnect: users expect search to highlight or filter nodes.
- **Dataset switch only works for Graph view** — switching datasets refreshes the graph correctly (fetchGraph is in App's useEffect on currentDataset) but List and Dashboard views load data with the old dataset (detailed below in Critical Bug section).
- **No graph loading skeleton** — carried forward from I9. The blank canvas before Cytoscape renders is especially noticeable with quant_operators (62 nodes).
- **"All nodes fit" toast** is a thoughtful touch — it tells the user when their budget is sufficient and no trimming occurred. But it only appears in response to the budget slider, not when first loading a resolve result. A user who sees all nodes in their resolve output has no indication that everything fits.

#### List View

The List view is a competent data table with sortable columns and client-side filtering.

**Good:**
- Column sorting works (ascending/descending toggle) with clear indicators
- Pagination (First/Prev/Next/Last) handles the 62-item quant_operators dataset correctly
- The 10-of-10 / 62-of-62 counter provides clear dataset scope awareness
- Clickable rows navigate to detail view
- Empty state with CTA button when no memories exist
- Loading skeleton with realistic shimmer animation

**Issues found:**
- **Summary column is truncated with `text-overflow: ellipsis`** — this is fine for scanning but there's no tooltip to reveal the full text on hover. Long Chinese summaries like the risk-tolerance memory are cut off mid-sentence.
- **Filter box resets on dataset switch** — but since dataset switch doesn't actually change the visible data (see Critical Bug), this behavior is hidden.
- **The filter uses substring matching** — searching "soxl" finds the soxl-composition memory but also "context" (because it contains the substring "so" somewhere else). This is correct substring behavior but produces noisy results on larger datasets.

#### Dashboard View

The Dashboard is the most polished of the three views.

**Good:**
- Stat cards provide at-a-glance dataset health (Total / Stale / Proven / Draft)
- Maturity distribution horizontal bars are clickable to filter list view
- Tag cloud is clickable to filter list view
- Wander modal shows access_count, intensity, and last_access with contextual explanations ("This memory has never been accessed — it may contain overlooked insights")
- Validate modal groups errors by type with clickable memory IDs
- WANDER AGAIN button enables serendipitous browsing
- All four action buttons (Wander / Validate / Refresh / Reindex) have loading states

**Issues found:**
- **Modals stack** — opening Wander then Validate (without closing Wander first) results in both modals being visible simultaneously. Two backdrops, two content dialogs, two close buttons. This creates a confusing user experience.
- **REINDEX has no confirmation or success feedback** — the button shows "Reindexing..." while loading, but on completion it silently refreshes stats with no toast, no "Reindex complete" message, no visual indication anything happened.
- **Status distribution section at the bottom** is less useful than the maturity and tags sections above it. For the current datasets, every memory is "active" so this section adds no information.
- **The stale memories section shows stale ID as both the clickable title AND the monospace subtitle** — this is redundant. The `memId` is displayed twice (lines 367 and 377 in Dashboard.tsx).

#### Memory Form (Create/Edit)

**Good:**
- Template selector lets users start from schema templates (schemas/decision)
- Form validation catches missing required fields (shows "ID is required" error)
- Tag and imports fields support comma-separated input with placeholder guidance
- Intensity slider (1-10) with default value 5
- Maturity select with all four levels
- Markdown body textarea

**Issues found:**
- **CREATE button not disabled on validation error** — submitting an empty form shows the error message but the CREATE button remains enabled and clickable, suggesting multi-submit is possible.
- **No inline validation** — fields only validate on submit, not on blur. The user doesn't know their ID is invalid until they click CREATE.
- **No tag autocomplete in the create form** — the search bar has tag autocomplete (prefix match) but the form does not. A user creating a new memory in the investment dataset should see "investment", "fact", "preference" tags suggested.
- **Imports field is raw comma-separated IDs** — no validation that referenced IDs actually exist, no autocomplete. User can create broken links from the form.
- **Form doesn't close after successful creation** — good (allows creating multiple memories), but there's no success toast either. The only feedback is the graph refresh. If the user is in Graph view, they might not notice the new node.

### 1.3 Edge Cases & Error Handling

**Tested and working:**
- Empty form submission shows "ID is required" error
- API returns 400 with helpful message when X-Codememory-Dataset header is missing
- Non-existent memory ID returns 404 with clear error
- Switching to dataset then back preserves data isolation
- Network error banner appears on server unreachable
- Error toast queue stacks correctly with auto-dismiss (6s) and manual close

**Tested and problematic:**
- **Dataset switch shows stale data** in List and Dashboard views (Critical Bug — see below)
- **Modals stack** without management (Important UX Bug)
- **Search in graph view is non-functional** (Important UX Bug)
- **REINDEX is silent** (Usability gap)
- **Ctrl+K shortcut fails** — `document.getElementById('global-search-input')` doesn't match any element ID in SearchBar.tsx (the search input uses no id attribute)
- **No loading error recovery UI** — if a data fetch fails, the view shows whatever data it had before, with no "Retry" button

### 1.4 Critical Bug: Dataset Switching Race Condition

**Severity: Critical**
**Reproduction:** Switch dataset via dropdown while in List or Dashboard view. The data does not update to reflect the new dataset.

**Root Cause:** React effect ordering. When `handleSwitchDataset` completes, both `setCurrentDataset(name)` and `setRefreshTrigger(prev => prev + 1)` fire in the same render batch. After render, child component effects run before parent effects:
1. `MemoryList.useEffect([refreshTrigger])` fires → calls `fetchAllMemories()` with OLD `_currentDataset`
2. `Dashboard.useEffect([refreshTrigger])` fires → calls `fetchStats()` with OLD `_currentDataset`
3. `App.useEffect([currentDataset])` fires → calls `setApiDataset(newValue)` → too late

The fix requires either:
- Updating `_currentDataset` BEFORE incrementing `refreshTrigger` (synchronously, not via useEffect)
- Or having child components accept `currentDataset` as a prop and use it directly instead of relying on the module-level `_currentDataset` variable

**Evidence:** Verbatim DOM text from quant_operators List view after switching: "10 of 10 memories" (should be "62 of 62"), and the memory IDs shown are all `user/*` (investment dataset) rather than `api/*` (quant_operators dataset).

### 1.5 Undo & Backlinks Verification

- **Undo:** Functional for create, update, and archive operations. 5-second toast with manual dismiss. Single-level undo only — no undo history.
- **Backlinks:** API endpoint returns correct reverse references. Verified via `GET /api/memories/{id}/backlinks`.
- **Archive confirmation modal:** Non-destructive styling (neutral border, not red). Confirmation required.

---

## Phase 2: Aesthetic Taste

### 2.1 Color Palette & Visual Hierarchy

The LuxCart design system is the product's strongest aesthetic asset. The warm-neutral palette (charcoal `#1C1917`, cream `#FFFBEB`, gold `#B8860B`) creates a distinctive editorial/luxury feel that separates CodeMemory from the generic blue-gray of most developer tools.

**What works:**
- The cream background (`#FFFBEB`) is unusual and memorable — it signals "this is not Jira" immediately
- Gold as the accent color is semantically coherent (memory as valuable, knowledge as treasure)
- Directory colors are deliberately chosen: facts are charcoal (neutral, grounded), preferences are gold (personal, valuable), observations are warm gray (processed, interpreted), decisions are deep red (consequential)
- The dark mode palette is a complete rethinking, not just inverted colors — text goes from `#1C1917` to `#F0EBE0` (not pure white), backgrounds shift to warm dark tones (`#1A1817`, `#2D2A28`)
- Dark directory tints now span `#15`–`#4A` (from I10), providing genuine glanceability
- Semantic colors are used correctly: success = green, error = red, warning = amber, info = blue

**What doesn't:**
- The schema purple (`#7C3AED` in light, `#A78BFA` in dark) is the one color that doesn't belong in the warm-neutral palette. It's the standard Tailwind purple — a cool tone that clashes with the warm golds and browns. A warmer violet or plum would maintain consistency.
- The info blue (`#1E40AF`) is similarly cool — a slate-blue would harmonize better with the palette.
- The "quant_operators" dataset disclaimer uses the info-blue subtle background (`--cm-bg-info-subtle`), making it the only blue-tinted element in a warm-toned header. It draws attention but for the wrong reason.
- In light mode, the difference between `--cm-bg-primary` (cream `#FFFBEB`) and `--cm-bg-surface` (white `#FFFFFF`) is subtle enough that cards and panels don't clearly separate from the background. A 1% tint difference is barely perceptible.

### 2.2 Typography & Typesetting

**Font stack:** Cormorant Garamond (headlines) + Raleway (body) + JetBrains Mono (code). This is a thoughtful, tasteful combination. Garamond for the "CodeMemory" logo gives it gravitas; Raleway's geometric clarity works for UI labels; JetBrains Mono is the gold standard for code.

**What works:**
- Font pairing is distinctive — you won't mistake this UI for Material Design
- Headline sizing follows a rhythmic scale: 36px (prose h1) → 32px (Dashboard title) → 24px (App title, prose h2) → 20px (prose h3, modal titles) → 16px (body default)
- Monospace is used correctly for IDs, counts, and values
- Letter-spacing on uppercase labels (`0.08em`) adds polish
- Line-height of 1.7 is generous and readable

**What doesn't:**
- **11px is too small for interactive UI text.** The view switcher (Graph/List/Dashboard), dataset selector, "+ New" button, and many labels use 11px. On a 1440p display at 100% scaling, this is at the edge of legibility. On a 4K display, it would be microscopic.
- **12px is borderline for body text in some components.** The List view table cells, filter inputs, and form fields all use 12px. Combined with Raleway's thin strokes, this can be hard to read.
- **The skip from 24px (App title) to 11px (UI controls) is harsh.** The header has a 24px serif title and everything else is 10-11px sans-serif. There's no 16px or 14px intermediate tier creating a smooth hierarchy.
- **Chinese text rendering in Raleway** — Raleway doesn't have CJK glyphs, so Chinese text falls back to system fonts. The investment dataset's Chinese summaries render in a different font than the English UI, creating a typographic seam. This is a technical limitation, not a design choice, but it's noticeable.
- **Monospace text color inconsistency** — sometimes `--cm-text-primary` (strong), sometimes `--cm-text-secondary` (medium), sometimes `--cm-text-tertiary` (weak). The List view memory IDs use primary color (good), but the pagination page counter uses secondary (acceptable), and the Dashboard stale ID uses tertiary for the exact same ID text (confusing).

### 2.3 Spacing & Information Density

**What works:**
- The dashboard uses generous 32px padding and 24px gaps — it breathes
- Stat cards have consistent internal padding (20px 24px) with a clear label→value→gap rhythm
- The header bar is compact but not cramped (16px padding, 16px gaps)
- Form fields have adequate spacing between them
- Modal padding (28px) creates a clear content boundary

**What doesn't:**
- **The Graph view toolbar is crowded.** Zoom slider, Budget slider, theme toggle, PNG, Export, Settings, Help, Legend, Directories, Edge types — all in a space roughly 200px wide. On a smaller screen, this would be unmanageable.
- **The "Stats, validation, and reindex apply to the selected dataset" disclaimer text is 10px italic** — it's essentially invisible. Either make it useful or remove it.
- **The List view table has no horizontal padding on the container** — rows stretch edge-to-edge with only 12px cell padding, making the table feel pressed against the viewport edges.
- **No responsive breakpoints.** The UI assumes a minimum width of roughly 1200px. On smaller viewports, elements would overflow or overlap.

### 2.4 Motion & Transitions

**What works:**
- Undo toast has a 200ms slide-up entrance (`undo-toast-enter`)
- Error toasts have a 200ms slide-up + fade-in (`toastSlideIn`)
- Dashboard maturity bars have 300ms width transition
- Settings Save button transitions background-color on success (gold → green, 200ms)
- The `transition: background-color 200ms ease` on the Save button is subtle and satisfying

**What doesn't:**
- **No panel slide-in animation** — MemoryDetail, Settings, and Help panels appear instantly. The code comment says "250ms ease transform" but there's no CSS transition on the panel container. Panels just appear.
- **No modal entrance animation** — Wander and Validate modals appear instantly without fade or scale transition.
- **No view switch transition** — changing from Graph to List to Dashboard is an instant cut with no crossfade or morph.
- **No node hover feedback in the graph** — Cytoscape nodes respond to hover (the library provides this), but there's no custom styling enhancement.
- **Skeleton shimmer animation is clean** (1.5s infinite ease-in-out gradient shift) — this is well executed.
- **The dark mode toggle is instant** — which is actually correct. Theme switches should be immediate, not animated.

### 2.5 Visual Personality

CodeMemory's visual identity sits at an interesting intersection: it's trying to be both a utilitarian developer tool (the relentless use of uppercase labels, monospace IDs, 11px text) and a premium knowledge product (Cormorant Garamond, cream background, gold accents, "LuxCart" design system name).

**The tension:** A developer tool with luxurious typography creates a specific mood — it's like a Moleskine notebook for code. This works when the execution is consistent. But the tiny font sizes and dense toolbar undercut the "luxury" signal. You can't feel premium while squinting at 10px italic disclaimers.

**What the visual personality communicates successfully:** "This is serious. Knowledge matters. Memory deserves care."

**What it fails to communicate:** "This is easy to use. You'll enjoy being here. Come back often."

**The personality is more "private library" than "workshop."** For a memory tool that users should interact with daily, the workshop metaphor (active, hands-on, iterative) might serve better than the library metaphor (passive, archival, final). The current design leans library — which is beautiful but may discourage the casual, frequent interaction that memory tools thrive on.

---

## Phase 3: Product Imagination

### 3.1 Three Features That Would Make Users Never Leave

**1. "Context Compass" — Visual dependency impact analysis**

When a user edits a memory, show a live preview of what else would be affected. "If you change this fact about NVIDIA earnings, 4 other memories import it directly, and 2 more import those." This is the visual equivalent of `suggest-deps` but interactive and always-on. A small panel in the detail view showing "Depended on by:" with a mini-DAG of downstream impacts.

Why users would stay: It transforms editing from a solo act into a systems-thinking exercise. You see your knowledge graph breathe. Every change has visible consequences. This is the killer feature for knowledge workers who think in systems.

**2. "Memory Sessions" — Time-travel through your thinking**

Save the state of a resolve operation as a named session. "Here's what I was thinking about during the Q1 review" — a frozen snapshot of the exact DAG that was loaded, with annotations, at that moment. Sessions are browsable, comparable, and diffable. "What changed in my thinking between January and March?"

Why users would stay: Memory tools are ultimately about understanding how your thinking evolves. Current CodeMemory captures WHAT you know but not WHEN or WHY you knew it in a particular configuration. Sessions would add the temporal dimension that makes knowledge graphs truly personal.

**3. "Memory Health Dashboard" — Proactive knowledge maintenance**

Instead of waiting for users to run Validate, surface memory health issues proactively. A decaying memory (not accessed in 90 days, intensity < 5) gets a subtle amber border. A stale memory gets a dotted outline. A proven memory that hasn't been revisited in 6 months gets a gentle nudge. The graph itself becomes a visual health indicator.

Why users would stay: It transforms the product from a passive storage system into an active thinking partner. "Hey, you haven't thought about this thesis in 3 months — the market has changed, want to revisit it?" This is what makes a memory tool feel alive.

### 3.2 The "Aha Moment" Analysis

**Current aha moment:** When a user runs Resolve for the first time and sees their memories topologically sorted into a coherent context with exact token counts. The moment they realize "this isn't search — this is dependency-aware context assembly" is when the product's core value proposition clicks.

**How to strengthen it:**
- Make Resolve the default action on the first graph node click (not "show detail panel" but "resolve this memory's context")
- Add a subtle animation showing the traversal path through the graph as resolve assembles the context
- Show a side-by-side: "Here's what keyword search would give you (scattered, missing context)" vs. "Here's what DAG resolve gives you (complete causal chain)"
- Let users toggle between "search mode" and "resolve mode" so the paradigm difference is always visible

**How to make it come sooner:**
- The onboarding should end with "Try resolving your first memory" as a call-to-action, not "here are the features"
- Pre-load a resolve result for the most-connected memory in the dataset so first-time users see the value immediately

### 3.3 What Could Be Deleted

**1. The "Stats, validation, and reindex apply to the selected dataset" disclaimer text.**

This 10px italic line in the header adds no value. Users can see which dataset is selected from the dropdown. The validation and reindex buttons are in the Dashboard, not the header. This text is visual noise that developers added for clarity but users will never read or need. Remove it. If the concern is that users might not understand dataset scoping, solve it with a tooltip on the dataset dropdown itself.

**2. The Status Distribution section in Dashboard (for now).**

Every memory across all four datasets is "active." This section shows one card with "ACTIVE" and a count — it communicates nothing. When archived memories actually exist in user datasets, this section will become useful. Until then, it's dead space. Replace it with a "Recently Accessed" list (pulled from last_access timestamps) which would provide actionable information.

**3. The Zoom slider in the header.**

The zoom level is adjustable from 0.15 to 2.0, but the default 0.5 is sensible for most datasets, and users can also zoom with scroll wheel. The slider takes up header space and adds cognitive load. Move it to a graph view toolbar that appears on hover, or make it a keyboard-only control (+/- keys).

### 3.4 Competitive Comparison

| Feature | CodeMemory | Obsidian Graph | Notion Database | Django Admin |
|---------|-----------|----------------|-----------------|--------------|
| Graph visualization | Cytoscape + Dagre (directed, colored) | Force-directed (undirected) | None | None |
| Dependency resolution | DAG topology sort + budget | Manual backlinks | Relations (manual) | ForeignKey relations |
| Token budget control | Slider 200-5000 | N/A | N/A | N/A |
| Memory CRUD | Form with schema templates | Markdown editor | Rich text + properties | Django forms |
| Search | Keyword + tag/type/maturity filter | Full-text (Omnisearch plugin) | Database queries + filters | Django filters |
| Dark mode | Full CSS variable system | Community themes | Built-in | Admin theme |
| MCP server | 5 tools over stdio JSON-RPC | No | No | No |
| Undo | 1 level (create/update/archive) | File history (plugin) | Version history | Django admin history |
| Export | PNG graph + ZIP all memories | Various plugins | CSV/PDF export | CSV/JSON export |
| Onboarding | 5-step text walkthrough | None | Template gallery | None |

CodeMemory's differentiators are clear: the MCP server (unique), token-budgeted resolution (unique), and the Layer 0 cognitive primitives (unique). Where it lags is in the basics: undo is single-level vs. Notion's full version history, search is keyword-only vs. Obsidian's plugin ecosystem, and the form experience is functional but bare vs. Django Admin's mature CRUD patterns.

---

## Phase 4: Consistency & Cross-View Analysis

### 4.1 Internal Consistency Audit

| Pattern | Graph | List | Dashboard | Consistent? |
|---------|-------|------|-----------|-------------|
| View title | None | "N of M memories" | "Dashboard" (h1) | No — Graph has no title |
| Search/filter | SearchBar (global) | Filter input (local) | None | No — different mechanisms |
| Loading state | None (blank canvas) | Skeleton shimmer | Skeleton shimmer | No — Graph has no skeleton |
| Empty state | Not shown (graph renders anyway) | EmptyState component | EmptyState component | Partial |
| Error feedback | Error toast queue | No inline error recovery | onError callback | Partial — List has no error handling |
| Create button | "+ New" in header | "+ New" in header | "+ New" in header | Yes |
| Dataset switch | Works | Broken (stale data) | Broken (stale data) | No — critical inconsistency |
| Theme toggle | Sun/Moon button | Sun/Moon button | Sun/Moon button | Yes |
| PNG export | Button visible | Button hidden | Button hidden | Yes (by design) |
| Keyboard shortcuts | All 6 | All 6 (Ctrl+K broken) | All 6 | Partial — Ctrl+K broken |

### 4.2 Cross-Dataset Experience

| Aspect | companion (10) | investment (10) | quant_operators (62) | software-architecture (11) |
|--------|---------------|-----------------|---------------------|---------------------------|
| Graph render time | ~1s | ~1s | ~3s | ~1s |
| Nodes visible | 10 | 10 | 62 (dense) | 11 |
| Directory colors | 3 dirs | 5 dirs (1 auto) | 4 dirs (3 auto) | 5 dirs |
| Stale detection | 0 | 0 | 0 | 0 |
| Validate warnings | 0 | 0 | 0 | 7 (legit) |
| Header disclaimer | "Stats, validation..." | "Stats, validation..." | "Auto-generated API..." | "Stats, validation..." |

The quant_operators dataset exposes scaling limits: the graph becomes dense and hard to read at 62 nodes, and the special disclaimer text is a one-off solution that doesn't scale to other auto-generated datasets. The software-architecture dataset's 7 validation warnings are a legitimate finding but the user has no way to distinguish "these warnings are expected for this type of dataset" from "these warnings need action."

### 4.3 Comparison with Previous Audit Claims

The I10 eval.md claims "all 9 tasks completed." My verification:

| Claim | Verified? | Notes |
|-------|-----------|-------|
| MCP server (5 tools) | Yes | Stdio JSON-RPC 2.0, all 5 tools functional |
| Auto-reindex on startup | Yes | All 4 datasets reindexed, stale_count: 0 |
| Error toast queue | Yes | Stacked, dismissable, 6s auto-dismiss |
| Search filter fix | Yes | Filter-only search works correctly |
| Dark mode tints widened | Yes | `#15`–`#4A` range verified in colors.ts |
| X-Codememory-Dataset required | Yes | 400 returned with dataset list |
| API smoke tests (5) | Yes | All pass in ~0.5s |
| Tag autocomplete prefix match | Yes | Uses startsWith |
| Loading skeletons | Partial | Dashboard and List have them; Graph does not |

**One previously claimed fix is incomplete:** The eval.md states the search filter fix addresses "tag/type/status filters returning zero results when no text query was provided." This is true for the API but the UI integration is incomplete — the search bar in Graph view doesn't visibly filter or highlight nodes when results are returned.

**One new issue not present in previous audits:** The dataset switching race condition is a fresh bug. It's possible this was introduced during the R10 changes (the `setApiDataset` via useEffect was likely added as part of the multi-dataset architecture) or it existed before but wasn't tested with List/Dashboard views during dataset switching.

---

## Prioritized Recommendations

### Critical

1. **Fix dataset switching in List and Dashboard views.**
   The race condition between `setApiDataset` (parent effect) and `loadData` (child effect) causes List and Dashboard to display stale data after dataset switch. Move the `_currentDataset` assignment into the synchronous code path — either call `setApiDataset(name)` directly in `handleSwitchDataset` before the state updates, or pass the dataset name to child components as a dependency.
   - **Files:** `frontend/src/App.tsx` (handleSwitchDataset), `frontend/src/api.ts` (setCurrentDataset)
   - **Estimated effort:** 1 hour
   - **Verification:** Switch dataset in List view and confirm the memory count and IDs update correctly.

2. **Prevent modal stacking.**
   Opening Wander then Validate (or vice versa) should close the first modal. Add a `closeWander()` call to the Validate handler and a `closeValidate()` call to the Wander handler. Alternatively, implement a modal stack manager in App.tsx.
   - **File:** `frontend/src/components/Dashboard.tsx`
   - **Estimated effort:** 30 minutes
   - **Verification:** Open Wander, then Validate, confirm Wander modal closes.

### Important

3. **Make search actually filter the graph view.**
   The SearchBar component renders in Graph view but searching has no visual effect on the graph. Pass search results to GraphCanvas and use Cytoscape's filtering/highlighting to dim non-matching nodes and highlight matches.
   - **Files:** `frontend/src/components/SearchBar.tsx`, `frontend/src/components/GraphCanvas.tsx`
   - **Estimated effort:** 2-3 hours
   - **Carried forward from:** implicit in I9 search improvements

4. **Add user feedback for REINDEX.**
   Show a success toast ("Reindexed N memories") on completion. The button currently only shows "Reindexing..." during the operation.
   - **File:** `frontend/src/components/Dashboard.tsx`
   - **Estimated effort:** 15 minutes

5. **Fix Ctrl+K keyboard shortcut.**
   `document.getElementById('global-search-input')` doesn't match any element. Either add the ID to the SearchBar input or use a ref-based approach.
   - **Files:** `frontend/src/App.tsx`, `frontend/src/components/SearchBar.tsx`
   - **Estimated effort:** 15 minutes

6. **Add graph loading skeleton.**
   Last missing loading state. A centered skeleton with placeholder node circles and edge lines, matching the shimmer pattern used in List and Dashboard.
   - **File:** `frontend/src/components/GraphCanvas.tsx`
   - **Estimated effort:** 1 hour
   - **Carried forward from:** I9

7. **Disable CREATE button on form validation failure or add loading state.**
   Currently the button stays enabled after showing validation errors, allowing repeated submissions.
   - **File:** `frontend/src/components/MemoryForm.tsx`
   - **Estimated effort:** 20 minutes

### Nice-to-Have

8. **Add tooltip on hover for truncated List view summaries.**
   The `text-overflow: ellipsis` truncation hides long summaries. A title attribute or CSS tooltip on the summary cell would reveal the full text.
   - **File:** `frontend/src/components/MemoryList.tsx`
   - **Estimated effort:** 10 minutes

9. **Remove the "Stats, validation, and reindex apply to the selected dataset" disclaimer from the header.**
   It's visual noise. Replace with a tooltip on the dataset dropdown.
   - **File:** `frontend/src/App.tsx`
   - **Estimated effort:** 5 minutes

10. **Add tag autocomplete to the create/edit form.**
    The search bar has tag autocomplete (prefix match); the form should too. Fetch tags from stats endpoint and provide suggestions as the user types in the tags field.
    - **File:** `frontend/src/components/MemoryForm.tsx`
    - **Estimated effort:** 1 hour

11. **Remove duplicate memId display in Dashboard stale section.**
    Lines 367 and 377 in Dashboard.tsx both render `memId` — the monospace subtitle is redundant.
    - **File:** `frontend/src/components/Dashboard.tsx`
    - **Estimated effort:** 5 minutes

12. **Replace the Status Distribution section with a "Recently Accessed" list.**
    Since all memories are currently "active," the status distribution adds no information. A list of the 5 most recently accessed memories (from last_access timestamps) would be more actionable.
    - **File:** `frontend/src/components/Dashboard.tsx`
    - **Estimated effort:** 1 hour

### Feature Ideas (for backlog, not this iteration)

13. **Data Import UI.** The CLI has `codememory import --file` but there's no UI equivalent. A drag-and-drop markdown importer that parses frontmatter and creates memories would bridge the gap between CLI power users and GUI-first users.

14. **Memory comparison view.** Select two memories and see them side-by-side with highlighted differences. Essential for understanding how decisions evolved or how facts were updated.

15. **"Context Compass" — downstream impact preview.** When editing a memory, show which other memories import it. Transform editing from a solo act into systems thinking.

16. **Session snapshots browser.** Browse, compare, and restore previous resolve sessions. Adds the temporal dimension to memory management.

17. **Memory health indicators on graph nodes.** Visual cues for stale, unaccessed, or decaying memories directly on the graph. No need to check the Dashboard — the graph itself becomes the health monitor.

18. **Favorites/bookmarking.** Pin frequently accessed memories for quick retrieval. "Star" a memory in List view or right-click menu, see starred memories as a filtered view.

19. **Batch operations.** Select multiple memories in List view and bulk-change tags, maturity, or archive status.

20. **Changelog viewer in UI.** The CLI has `codememory changelog <id>` but there's no UI equivalent. A version history panel in the memory detail view would close this gap.

---

## Verdict

CodeMemory Iteration 10 is an infrastructure win with a UX regression. The MCP server, error queue, dark tint widening, and header enforcement are genuine improvements that make the product more robust and integrable. But the newly discovered dataset switching bug and modal stacking issue undermine the primary user-facing workflow — the very workflow the management panel exists to serve.

The product's conceptual foundation (DAG-based memory resolution, Layer 0 cognitive primitives, the insight that memory loading is dependency resolution) remains brilliant. The MCP server proves the concept can extend beyond the web UI into agent workflows. The LuxCart design system gives the product a distinctive visual identity that separates it from generic developer tools.

But the execution in the web panel still feels like a capable prototype rather than a polished product. The small frictions add up: search doesn't filter the graph, modals stack on top of each other, REINDEX is silent, Ctrl+K fails silently, font sizes strain readability, the form has no inline validation. None of these individually is a dealbreaker, but collectively they create a "death by a thousand paper cuts" experience that undermines trust in a tool whose entire purpose is to be trustworthy with your knowledge.

**The core question this product needs to answer:** Is the web panel a primary interface that should feel polished and trustworthy, or is it a debugging/admin tool where rough edges are acceptable because the real interface is the MCP/CLI? The current execution straddles this line — too much effort for a pure debug tool, not enough polish for a primary interface.

**Recommended priority for next iteration:** Fix the two critical bugs (dataset switch, modal stacking), add search-to-graph filtering, add REINDEX feedback, and fix Ctrl+K. These are high-impact, low-effort fixes that would substantially improve the user's trust in the product. Then decide whether to invest in further UX polish (the Nice-to-Have and Feature Idea tiers) or to double down on the MCP/CLI integration path where the core value proposition is strongest.
