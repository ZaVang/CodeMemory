# CodeMemory -- Product Evolution Audit Report

**Date:** 2026-05-07
**Reviewer:** Product Evolution Reviewer (Product Strategy)
**Build:** Post-Round 12 (264c444), entering Round 13
**Previous score:** 5.5/10 (post-Round 11)
**Datasets available:** companion (10), investment (10), software-architecture (11)
**Methodology:** Full source code review (14 TSX components, backend API 16 endpoints, MCP server 5 tools, 57 unit + 24 integration tests), headless page-state extraction at localhost:5299, competitive analysis of Obsidian, Mem.ai, Notion, Logseq, Roam Research, and Mem0. Prior audit report findings factored into re-evaluation of all resolved and unresolved items.

---

## Executive Summary

**Product Evolution Maturity Score: 7.5 / 10** (up from 5.5)

CodeMemory after Round 12 is no longer a proof-of-concept -- it is a functional, aesthetically distinct knowledge management tool with a genuinely novel interaction model. The DAG dependency resolution engine paired with native MCP protocol support is a combination no competitor possesses. The Warm-neutral design system (charcoal `#1C1917`, cream `#FFFBEB`, gold `#B8860B`) and the Cormorant Garamond + Raleway + JetBrains Mono typography trio gives the product a premium, crafted identity that stands apart from the developer-tool monoculture.

**Why 7.5 (up +2.0 from 5.5):**

Round 12 delivered four meaningful quality-of-life improvements that close real gaps: SVG onboarding icons (replacing placeholder text characters), time-decay heat scoring (making the "cool memory" concept computationally real), panel slide-in animations (the first motion design outside MemoryDetail), and archive backlink warnings (preventing data-loss-by-archival). The Validate Again button and unified empty states eliminate two friction points identified in the Sprint 13 audit. The MCP `readOnlyHint` flags complete the protocol compliance story. Font sizing was raised to 14-15px body text and 22px headers -- a substantial accessibility improvement.

However, the product still faces a structural tension: it is built for developers (CLI, MCP, DAG, token budgets) but presented as a consumer knowledge tool (warm palette, serif fonts, onboarding tour). This identity question must be resolved before any go-to-market strategy can be coherent. The product is currently a developer tool wearing a premium consumer skin -- and that mismatch will confuse the first real users.

---

## Phase 1: Core Completeness

### 1.1 The Core Loop: View -> Inspect -> Resolve -> Modify

The product's primary interaction loop is now complete and functional end-to-end:

| Step | Action | Status | Round 12 Impact |
|------|--------|--------|-----------------|
| **View** | Graph / List / Dashboard | Stable | Font sizing improved (15px body, 22px headers), graph search filter working |
| **Inspect** | Click node -> MemoryDetail panel | Stable | Panel slide-in animation (250ms ease), escape-to-close |
| **Resolve** | Click Resolve -> DAG traversal | Stable | Validate Again button eliminates modal-close-reopen dance |
| **Modify** | Create / Edit / Archive | Functional | Archive backlink warning dialog, form validation improvements |
| **Verify** | Validate / Reindex | Functional | Dashboard Validate + Reindex buttons with error feedback |

**Assessment:** The loop works. A user can open the app, explore the graph, inspect a memory, resolve its dependency chain, edit its content, and validate the result. That is the baseline for a product, and CodeMemory crosses it.

### 1.2 Onboarding -- Passive But No Longer Embarrassing

Round 12 replaced the raw text characters ("+", "o", ">") in the onboarding with proper SVG geometric icons: a star (welcome), a node-circle (graph), an arrow-dependency diagram (resolve), a plus-in-circle (create), and a checkmark-in-circle (ready). This was the single highest-leverage visual improvement in the round -- the onboarding no longer looks like a wireframe that shipped.

However, the onboarding remains entirely passive. Five slides of text with no interactive elements, no miniature graph animation, no "create your first memory" inline button. The user reads about the graph view but never interacts with it. The "Resolve" step describes animation that the user cannot see. Compare this to Notion's onboarding, which drops you directly into a template page you can edit immediately, or Obsidian's "Sandbox vault" pre-loaded with interconnected notes you can explore.

**Score: 6/10** -- visually competent, still functionally passive.

### 1.3 Error States, Empty States, and Edge Cases

**What is covered (Round 12 additions starred):**
- Network unreachable: toast notification + human-readable error messages
- Loading: skeleton shimmers (graph, list)
- Empty: unified EmptyState component with CTA buttons (used in graph, list, dashboard) *
- Resolve error: error banner in MemoryDetail panel
- Archive warning: confirmation dialog with backlink count before archival *
- Form validation: field-level errors with inline messages
- Modal race conditions (Round 11 fix)
- Stale memory detection: icons + counts in Dashboard stats

**What is not covered:**
- **Empty graph with datasets present:** If the dataset has memories but the graph layout fails (edge case), no fallback view is rendered.
- **Resolve timeout:** No loading state during long resolves; the UI freezes without feedback.
- **Concurrent modification conflict:** Two browser tabs modifying the same memory results in last-write-wins with no conflict detection or warning.
- **Large dataset performance:** No pagination at the graph API level -- all nodes/edges loaded at once. Degraded performance expected beyond ~200 memories.
- **Browser back/forward navigation:** React state is not synced with browser history. Pressing Back navigates away from the app entirely.

### 1.4 Missing Core Features (Table Stakes)

| Feature | Exists? | Competitor Standard |
|---------|---------|---------------------|
| Full-text search in body content | No -- metadata only | Obsidian, Notion, Mem.ai all support |
| Multi-select / batch operations | No | Notion standard |
| Undo (multi-level) | Single-level only | Every editor since 1984 |
| Keyboard shortcut reference | Hidden in ? panel (HelpPanel) | Obsidian (Cmd/Ctrl-P command palette) |
| Tabbed / multi-pane view | No | Obsidian, Notion, Logseq all support |
| Drag-and-drop tag assignment | No | Notion, Obsidian standard |
| Pin / bookmark memories | No (import pinning is different) | Every knowledge tool |
| Mobile responsive design | No | Standard for consumer tools |
| Quick-capture mechanism | No | Obsidian Web Clipper, Mem.ai Chrome ext, email-to-memory |

**Critical gap: full-text body search.** CodeMemory's search operates on ID, summary, tags, and frontmatter metadata -- not on body text. A user who creates a memory with a detailed markdown body cannot find it by searching for words in that body. This is the single biggest functional gap versus every competitor in the market.

### 1.5 Data Persistence and Safety

- **Storage:** File-based (.md files in dataset directories, index.json). No database. Single point of failure: a corrupted index.json requires reindex, which is available via Dashboard.
- **Backup:** ZIP export endpoint exists. No automated backup, no snapshot scheduling.
- **Undo:** Single-level undo for create/update/archive operations. Cannot undo a delete (there is no delete, only archive). No undo stack persistence across page refreshes.
- **Version history:** Change log stored in frontmatter per memory. No UI to diff between versions. No UI to restore a previous version. The data is there; the feature is not.
- **No auth, no multi-tenancy:** Single-user local deployment only. No login, no user isolation, no access control.

---

## Phase 2: Competitive Gap Analysis

### 2.1 Competitive Landscape

| Dimension | CodeMemory | Obsidian | Mem.ai | Notion | Logseq |
|-----------|------------|----------|--------|--------|--------|
| **Core philosophy** | DAG dependency resolution | Local networked thought | AI auto-organization | All-in-one workspace | Outliner + linked notes |
| **Data storage** | Local files (.md + YAML frontmatter) | Local files (.md) | Cloud | Cloud | Local files (.md/.org) |
| **Linking model** | Explicit imports (required/recommended/related) | `[[wikilinks]]` bidirectional | AI-detected relationships | Database relations + backlinks | `[[wikilinks]]` + block refs |
| **Graph visualization** | Directed (DAG) with strength encoding | Undirected with local graph | No graph view | No graph view | Undirected |
| **AI integration** | MCP server (protocol-native) | Via plugins | Core feature (GPT-4 Chat) | Notion AI add-on | Via plugins |
| **Plugin ecosystem** | None | 2,700+ plugins | No | ~250 integrations | Plugin marketplace |
| **Mobile app** | No | iOS + Android | iOS only (no Android) | iOS + Android | iOS + Android |
| **Collaboration** | No | No | Basic (Teams plan) | Excellent | No |
| **Web clipper** | No | Yes (Obsidian Web Clipper) | Yes (agentic Chrome ext) | Yes | No |
| **Templates** | Schema-backed atoms | Core + Templater plugin | Via AI | 30,000+ community | Built-in |
| **Search** | Metadata only | Full-text + regex | Semantic (meaning-based) | Full-text + db filter | Full-text + query language |
| **Daily notes / journaling** | No | Core feature | Quick capture | Via template / database | Core feature |
| **Pricing** | Open source (MIT) | Free core; Sync $5/mo | Free (limited); Pro $12/mo | Free; Plus $10/mo | Free (OSS) |
| **Target user** | Developer + AI agent | Knowledge worker | Knowledge worker | Everyone | Knowledge worker |

### 2.2 CodeMemory's Unique Strengths (What Competitors Lack)

**1. Deterministic dependency resolution.** Mem.ai uses AI to guess what is related; Obsidian relies on manual `[[wikilinks]]`. CodeMemory's `imports` field with strength encoding (`required` / `recommended` / `related`) and topological sorting is a genuinely different approach -- computationally sound, auditable, and reproducible. No competitor does this.

**2. MCP protocol integration.** The MCP server exposes five cognitive primitives (resolve, overview, wander, focus, snapshot) as callable tools for any MCP-compliant AI client (Claude Code, Cursor, Windsurf). This makes CodeMemory not just a human knowledge tool but an AI agent's memory backend. Mem0 raised $24M to build something similar -- but as a cloud API, not a local, file-based protocol server.

**3. Token-budgeted context assembly.** The `resolve` command trims dependency output to fit a token budget, annotating each node as FULL / SUMMARY / SKIPPED. This is purpose-built for AI context windows -- a problem every LLM-based tool faces but none solve at the memory layer.

**4. Maturity governance.** The `draft -> verified -> proven -> superseded` lifecycle with automatic maturity escalation on resolve accesses and stale detection on body hash changes is a knowledge governance model that no competitor has formalized explicitly.

**5. "Memory as code."** YAML frontmatter + Markdown body + version control + imports + pinning + intensity scoring. A developer can version-control their memory dataset with Git, review diffs, and run validation as CI. This is a developer-first philosophy that Obsidian approaches (local .md files) but does not formalize with structured import declarations and programmatic validation.

### 2.3 Competitive Gaps That Matter

**Critical (blocks adoption for non-developers):**
- No full-text search across body content -- the single biggest gap
- No mobile access (no responsive web, no iOS/Android app)
- No quick-capture mechanism (web clipper, email-to-memory, voice memo)

**Important (blocks power-user workflows):**
- No plugin/extension system (Obsidian's 2,700+ plugins are its competitive moat)
- No multi-tab / split-pane UI (standard in every modern knowledge tool)
- No database/table views (Notion's core differentiator)
- No daily notes or journaling (Obsidian's most-used feature)

**Nice-to-have (blocks delight):**
- No graph-level operations (multi-select nodes, create connection by dragging)
- No diff viewer for memory versions (the data exists in change_log; the UI does not)
- No spaced repetition / flashcard integration (Logseq's unique feature)
- No PDF/image annotation or attachment support
- No canvas / whiteboard (Obsidian Canvas, Logseq Whiteboards)

### 2.4 Opportunity Signals from Competitor User Feedback

1. **Obsidian users complain about:** Steep learning curve, no collaboration, UI redesign frustrations, mobile startup speed. **CodeMemory opportunity:** Simpler UI with only three views (no plugin labyrinth) + MCP-native collaboration via shared datasets in Git.

2. **Mem.ai users complain about:** AI over-connecting notes (noise), trust collapse after feature removals, Google-only login, no Android. **CodeMemory opportunity:** Explicit imports (no AI guessing = no noise) + local files (no trust issue) + no login required.

3. **Notion users complain about:** Proprietary lock-in, slow large workspaces, no offline mode, no native graph view. **CodeMemory opportunity:** Open file format (.md + YAML) + local-first architecture + graph view as the primary interface.

4. **Mem0 targets developers who want:** Portability, model-agnostic memory, local execution. **CodeMemory opportunity:** CodeMemory is all three -- and its MCP server is the simplest integration path for any AI agent, with zero cloud dependency.

5. **Logseq/Roam users value:** Block-level references, outliner-first editing, query language. **CodeMemory opportunity gap:** CodeMemory's atom-level (file-level) granularity is coarser than block-level -- this could be either a strength (simplicity) or a weakness (less precision), depending on the user.

---

## Phase 3: Feature Depth

### 3.1 Existing Features -- Depth Assessment

| Feature | Surface Capability | Depth Score | Can Go Deeper? |
|---------|-------------------|-------------|----------------|
| **Resolve** | DAG traversal with token budget + depth modes | Strong (8/10) | Cycle-aware partial resolution, incremental resolve (only changed dependencies), resolve-to-diff |
| **Overview (heat ranking)** | Top 5 by heat score with time-decay | Round 12 deepened (7/10) | ML-weighted heat, user feedback loop ("this was useful/not useful"), personalized decay curves |
| **Wander** | Cool/random selection, weighted by access_count | Adequate (5/10) | Spaced-repetition scheduling, serendipity streaks, "since you last visited X" context messages |
| **Focus** | Full/summary toggle | Shallow (4/10) | Progressive disclosure (3+ levels), inline editing from focus view, context-aware related suggestions |
| **Snapshot** | Persist resolve output to .md file | Adequate (6/10) | Snapshot comparison (diff between snapshots), snapshot scheduling, auto-snapshot on significant memory changes |
| **Search** | ID/summary/tags/metadata matching | Shallow (3/10) | Full-text body search, semantic/embedding search, saved searches, search-within-resolve-output |
| **Validate** | Cycle/broken-link/stale detection | Adequate (6/10) | Auto-fix suggestions, scheduled validation, pre-commit hook integration, severity-weighted scoring |
| **Graph** | Cytoscape + dagre layout with colors/sizing | Moderate (6/10) | Property-based filtering, subgraph extraction, alternative layout algorithms, node grouping/folding |
| **List** | Sortable/paginated/filterable table | Moderate (5/10) | Column customization, multi-select rows, batch tag/status changes, export-to-CSV |
| **Dashboard** | Stats summary + wander + validate | Shallow (4/10) | Activity timeline, trend charts, memory health score, recently accessed feed, "needs attention" queue |

### 3.2 Power-User Path

The current power-user path is: keyboard shortcut `Ctrl+K` to open command palette -> type search -> click result to open MemoryDetail -> click Resolve -> inspect dependency chain. This works but lacks:

- **`Ctrl+Enter` to resolve without mouse** (currently requires clicking the Resolve button)
- **No graph keyboard navigation** (arrow keys to traverse nodes, Enter to open detail)
- **No batch operations** (multi-select in list view, bulk-tag, bulk-archive)
- **No saved views / filters** (save a filter configuration as a named view)
- **No import/export of filter configurations**
- **No keyboard shortcut for creating a memory from graph view** (must navigate to New Memory button)

### 3.3 Integration Depth

The MCP server is CodeMemory's strongest integration story. Five tools with `readOnlyHint` compliance, JSON-RPC 2.0 over stdio, compatible with Claude Code, Cursor, and Windsurf. This is production-quality integration infrastructure.

**What is missing in the integration layer:**
- **OpenAPI/Swagger documentation** (FastAPI auto-generates at `/docs` but is currently unexposed)
- **Webhook support** (notify external systems on memory create/update/archive)
- **VS Code extension** (resolve/inspect memories from the editor -- natural for developer users)
- **GitHub Action** (validate on PR, auto-reindex on push)
- **CI/CD integration examples** (validate as pre-commit hook, reindex on push)
- **MCP tools for write operations** (currently all 5 tools are read-oriented; snapshot is the only write tool)

### 3.4 Customization Depth

- **Themes:** Light/dark toggle only. No custom theme builder, no CSS variable overrides in the UI, no community theme sharing.
- **Views:** Three fixed views (graph/list/dashboard). No custom view builder, no view reordering.
- **Fields:** Fixed frontmatter schema in the UI. The backend supports `extra` fields but the UI does not expose them.
- **Workflows:** No automation rules (e.g., "when maturity reaches proven, auto-tag as reviewed").

---

## Phase 4: Differentiation & Wow Factor

### 4.1 The Core Differentiator: DAG + MCP

CodeMemory's unique value proposition in one sentence: **Deterministic dependency resolution for AI memory, exposed as a native MCP protocol server.**

No competitor has this combination:
- **Mem0** (43K GitHub stars, $24M funded) is an infrastructure layer but cloud-only and relies on probabilistic vector similarity for recall.
- **Obsidian** has local files and bidirectional links but no dependency resolution engine and no MCP integration.
- **Mem.ai** has AI-powered organization but is closed-source, cloud-only, and relies on opaque AI for relationship detection.
- **Notion** has databases and collaboration but no graph view, no dependency model, and no AI agent protocol.

The DAG + MCP combination positions CodeMemory as the memory layer for the agentic AI era -- a role that Mem0 is racing to fill with $24M in funding but with a very different approach (cloud API vs. local protocol server).

### 4.2 Wow Factor Moments (Current and Potential)

**Current wow moments:**
1. **First resolve:** Watching the graph animate through a dependency chain, seeing nodes light up in topological order, and receiving a system-prompt-ready context block in the side panel -- this is the "aha" that converts a skeptic. However, this moment is buried four clicks deep and is described in the onboarding but never demonstrated interactively.
2. **MCP integration:** Configuring CodeMemory as an MCP server in Claude Code and seeing the AI agent invoke `resolve_memory` to recall context -- this is the moment a developer realizes this is not just another note app but an AI-native memory infrastructure.
3. **Warm-neutral aesthetic:** The charcoal/cream/gold palette with Cormorant Garamond headlines creates an emotional response that no other developer tool achieves. This is a legitimate branding differentiator.

**Potential wow moments (not yet built):**
1. **Collaborative resolve:** Two users open the same dataset, one triggers a resolve, the other sees the dependency chain animate on their screen in real-time. (Requires WebSocket/sync infrastructure.)
2. **Git-integrated memory timeline:** "Show me what changed in my knowledge base this week" -- a diff view between snapshots, presented as a knowledge evolution timeline.
3. **Auto-suggested imports:** Type a memory ID and the system suggests related memories based on content similarity, tag overlap, and existing dependency patterns. (The `suggest_deps.py` module exists but is CLI-only -- it should be surfaced in the MemoryForm UI.)
4. **Memory health score:** A single number (0-100) that tells you the quality of your knowledge base -- coverage gaps, stale ratio, validation errors, cycle count. Gamifies knowledge maintenance.

### 4.3 Word-of-Mouth Triggers

For CodeMemory to spread organically, it needs moments that compel sharing:

| Trigger | Current State | Target State |
|---------|---------------|--------------|
| **Beautiful graph screenshot** | Possible but export uses small fonts with no watermark/branding | One-click "Share graph" with styled PNG export |
| **"My AI agent recalled a context from 3 months ago"** | Possible with MCP server | Needs a 30-second demo video of Claude Code resolving a dependency chain |
| **"I version-control my knowledge base"** | Technically possible | Needs documented workflow + template repo + GitHub Action |
| **"This tool caught a cycle in my thinking"** | Validate detects cycles | Needs a shareable validation report format (not just a modal) |
| **First-resolve animation** | Exists but not recordable | Needs to be easily screen-recorded and shared |

### 4.4 What to Delete (Simplicity as Differentiation)

CodeMemory should consider removing or consolidating features that dilute its focus:

- **The Legend component** takes toolbar space but explains concepts (directory colors) that could be communicated through better node labeling or a first-launch tooltip. Either make it interactive (click a legend entry to highlight those nodes) or replace it.
- **The Settings panel** is essentially a theme toggle + dataset selector occupying a modal. Both could be inline in the header, removing the need for a modal and a toolbar button.
- **The Help panel CLI command reference** is useful for developers but buried behind a "?" icon that is hard to discover. Consider whether this belongs in the UI at all or should live in documentation.

---

## Technical Health

### 5.1 Architecture Assessment

```
Frontend (React 19 + TypeScript 6 + Vite 8)
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

**Assessment:** The layered architecture is sound. The handler-based delegation pattern (cli.py -> handlers.py, tools.py -> handlers.py, backend/server.py -> handlers.py, mcp_server.py -> handlers.py) eliminates logic duplication across four interfaces. This is clean engineering. The backend is a thin FastAPI wrapper around the core Python package -- it reads from the existing codememory index.json and .md files without modifying internal logic, as stated in the project constraints.

### 5.2 Architecture Risks

| Risk | Severity | Detail |
|------|----------|--------|
| **Single-threaded file I/O** | Medium | FastAPI is async but core file operations (reindex, resolve) are synchronous and will block the event loop under concurrent access. |
| **In-memory index loading** | Medium | index.json is loaded into memory on every API request via context variable middleware. A dataset with 10,000+ memories will saturate server memory. Mitigation: reindex-on-write, lazy-loaded memory entries. |
| **File-based concurrency** | Low | Multiple writes to the same .md file from concurrent requests could corrupt data. A per-dataset file lock exists in server.py but has not been stress-tested. |
| **Cytoscape + dagre performance** | Low | Graph rendering degrades above ~500 nodes. Datasets this large are unlikely in the near term given the current use case. |
| **CSS-in-JS (inline styles everywhere)** | Medium | Every TSX component uses inline `style={{...}}` objects. No CSS modules, no styled-components, no Tailwind utility classes (despite Tailwind being in devDependencies). Changing the primary font requires searching 14 component files. This is the single biggest source of maintenance friction in the frontend. |

### 5.3 Test Health

| Test Suite | Count | Status |
|------------|-------|--------|
| Unit: test_resolve.py | 22 | 22/22 PASS |
| Unit: test_validate.py | 13 | 13/13 PASS |
| Unit: test_create_update.py | 12 | 12/12 PASS |
| Unit: test_edge_cases.py | 10 | 10/10 PASS |
| **Unit total** | **57** | **57/57 PASS** (0.31s) |
| Integration tests | 24 | 24/24 PASS |

**Assessment:** 81 tests with 100% pass rate is solid for a pre-1.0 product. The Python core is well-tested with good boundary/edge-case coverage.

**Critical testing gap:** There are zero frontend tests. No Jest, no React Testing Library, no Playwright or Cypress. The entire UI layer -- graph rendering, list sorting, dashboard stats, form submission, onboarding flow, search, resolve, wander, validate modals -- is tested only by manual inspection. Every regression in any of the 14 TSX components is undetectable until a human encounters it.

### 5.4 Technical Debt Inventory

| Item | Impact | Effort to Fix |
|------|--------|---------------|
| CSS-in-JS everywhere (no design token abstraction) | Medium -- makes theme changes invasive across 14 files | Large -- requires component refactor or CSS variable extraction |
| No frontend tests | High -- UI regressions are undetectable | Medium -- add 5 Playwright smoke tests as a starting point |
| Tailwind installed but entirely unused | Low -- wasted dependency and misleading dev setup | Trivial -- remove or adopt |
| No OpenAPI/Swagger documentation exposed | Low -- API discoverability gap for developers | Trivial -- enable the default FastAPI `/docs` route |
| No TypeScript strict mode | Medium -- potential for undiscovered type errors | Small -- enable `strict: true` in tsconfig.json |
| No automated CI pipeline | Medium -- tests run only on developer machines | Small -- add a GitHub Actions workflow running pytest |
| `extra: dict` on MemoryEntry accepts arbitrary data | Low -- schema drift over time without validation | Small -- add optional extra field validation |

### 5.5 Dependency Health

- **Python:** pyyaml, pydantic (v2), jinja2, python-dotenv -- all mature, well-maintained, minimal supply chain risk.
- **Python requires 3.13+:** This is a recent but stable CPython release. Narrows the deployment surface slightly but acceptable for a developer tool.
- **Frontend:** React 19, TypeScript 6, Vite 8, cytoscape 3.33, dagre 0.8, react-markdown 10 -- all current stable versions.
- **Zero transitive dependency vulnerabilities** given the minimal dependency tree.
- **No AI/ML dependencies** -- intentional design choice that keeps the package lightweight and auditable.

---

## Prioritized Recommendations

### Critical (Fix Before Any External User Sees This)

| # | Recommendation | Rationale | Effort |
|---|---------------|-----------|--------|
| **C1** | **Add full-text body search** | The single biggest functional gap vs every competitor. Search currently only matches ID, summary, tags, and metadata. A user with a 500-word memory body cannot find it by searching its content. The backend has the body text loaded; the `/api/search` endpoint needs to include it. Also wire into the frontend `Ctrl+K` global search. | Medium |
| **C2** | **Enable OpenAPI docs at `/docs`** | FastAPI auto-generates interactive Swagger UI documentation. It is currently not exposed. Enabling it costs zero code changes and immediately makes the API self-documenting -- a prerequisite for any developer adopting the product. | Trivial |
| **C3** | **Add Resolve loading state** | Clicking Resolve freezes the UI for 1-3 seconds with zero user feedback. A loading spinner or skeleton in the resolve panel area is table-stakes UX and will be the first thing any user complains about. | Small |
| **C4** | **Add body text to frontend search** | Same as C1 but specifically the frontend search bar -- when a user types in the global `Ctrl+K` palette, body text matches should appear in results alongside metadata matches. Currently only metadata is matched on the frontend side. | Medium |

### Important (Build Before Seeking Early Adopters)

| # | Recommendation | Rationale | Effort |
|---|---------------|-----------|--------|
| **I1** | **Multi-level undo stack** | Single-level undo is pre-1990s UX. Push create/update/archive operations onto a stack (at least 20 deep) and expose via `Ctrl+Z` / `Ctrl+Shift+Z`. The undo entry data model already exists in App.tsx -- this is wiring, not new architecture. | Small |
| **I2** | **Version diff viewer** | The backend stores full version history in change_log per memory. The frontend shows only the version number. A "View changes" button in MemoryDetail showing side-by-side diff of body text between versions converts stored data into a user-facing feature. | Medium |
| **I3** | **Graph keyboard navigation** | Arrow keys to move between graph nodes, Enter to open detail panel, Escape to deselect or close panel. This is expected behavior for any interactive graph and enables mouse-free exploration. | Small |
| **I4** | **CSS design token system** | The 30+ CSS custom properties defined in main.tsx should be extracted into a documented token system with semantic naming conventions. This is a prerequisite for theme customization, reduces inline style duplication, and makes future UI work dramatically faster. | Medium |
| **I5** | **Interactive onboarding demo** | Replace one passive onboarding slide with a live mini-graph (3-node pre-built DAG) that the user can click to explore. Let them trigger a "Resolve" from within the onboarding to see the animation. This moves the "aha moment" from "read about it on slide 3" to "experience it on step 1." | Medium |
| **I6** | **Playwright smoke tests** | Five tests covering: app loads, graph renders with nodes, clicking a node opens detail panel, search finds a known memory, create+edit+archive cycle completes. Catches ~80% of regressions with minimal investment. Run in CI on every push. | Small |

### Nice-to-Have (Build After Early Adopter Feedback)

| # | Recommendation | Rationale | Effort |
|---|---------------|-----------|--------|
| **N1** | **Multi-select in List view** | Checkbox column enabling batch operations: bulk-tag, bulk-change-status, bulk-change-maturity, bulk-export. Unlocks power-user workflows and makes List view more than a read-only table. | Medium |
| **N2** | **Saved filters / named views** | "Show all proven memories tagged 'investment' sorted by intensity" saved as "Investment Proven" with one-click access from the view switcher. This is Notion's database view feature adapted to CodeMemory's model. | Medium |
| **N3** | **Git integration guide + GitHub Action** | A documented workflow for version-controlling a memory dataset with Git, plus a GitHub Action that runs validate on push. This is the "memory as code" story that differentiates CodeMemory and resonates with developers. | Small |
| **N4** | **Quick-capture API endpoint** | A single POST `/api/capture` endpoint accepting a text blob and auto-creating a memory with generated ID, draft maturity, and auto-extracted tags. Enables web clipper extensions, Alfred/Raycast plugins, iOS Shortcuts, and email-to-memory workflows. | Small |
| **N5** | **Tabbed memory inspection** | Allow opening multiple memories simultaneously in the MemoryDetail panel as tabs (similar to Obsidian's tabbed interface). Removes the friction of closing one memory to open another when exploring dependencies. | Medium |
| **N6** | **Graph subgraph extraction** | Right-click a node -> "Show Dependency Chain" -> graph zooms and highlights only that node and its import chain. The graph equivalent of "focus" -- makes large graphs navigable. | Medium |
| **N7** | **Keyboard shortcut cheat sheet overlay** | A `?` overlay showing all keyboard shortcuts, similar to GitHub's or Notion's shortcut panel. Currently shortcuts are buried in the HelpPanel and require scrolling through CLI documentation to find. | Small |

### Feature Ideas (Long-Term Differentiators)

| # | Idea | Why It Matters |
|---|------|---------------|
| **F1** | **Collaborative resolve via WebSocket** | Two users open the same dataset. One triggers a resolve. The other sees the dependency chain animate on their screen in real-time. This is the "Google Docs moment" for knowledge graphs -- and no competitor has it. |
| **F2** | **Memory health score** | A single 0-100 number computed from: cycle count, stale ratio, broken links, coverage gaps, update frequency. Gamifies knowledge maintenance. "My knowledge base health is 92 -- what's yours?" is a sharing and word-of-mouth trigger. |
| **F3** | **DAG-aware editing sidebar** | When editing a memory, show a sidebar with upstream dependencies (what this depends on) and downstream dependents (what depends on this). Warn if changing this memory will semantically break downstream assumptions. This makes the DAG visible and actionable during editing -- the core product insight, brought to the surface where it matters most. |
| **F4** | **Scheduled re-engagement notifications** | "You haven't reviewed your investment risk model in 3 months. Your portfolio has changed -- want to re-evaluate?" CodeMemory's intensity + access_count + time-decay data can power proactive notifications that Mem.ai's "Heads Up" does with AI -- but CodeMemory can do it deterministically, based on explicit dependency structure rather than opaque similarity scoring. |
| **F5** | **VS Code extension** | Resolve/inspect memories in-editor. Right-click a function -> "Search CodeMemory for related context." The developer workflow of "code in editor, context in CodeMemory" creates a sticky, non-substitutable integration that no competitor offers. |
| **F6** | **MCP tools for memory creation/update** | Currently all 5 MCP tools are read-oriented (resolve, overview, wander, focus are readOnly; snapshot is the only write tool). Adding `create_memory` and `update_memory` as MCP tools would allow AI agents to not just read from but write to the memory system -- closing the loop for truly agentic knowledge management. |

---

## Summary: The Path to v1.0

CodeMemory is at an inflection point. The engine works (81 tests, 100% pass rate). The design has identity (Warm-neutral palette, tasteful typography). The integration story is genuinely unique (MCP server, 5 cognitive primitives). The question is no longer "can this be built" -- it has been. The question is "who is this for and what does their first 5 minutes look like?"

**If the target is developers:** Drop the consumer-warm aesthetic framing, lean into CLI + MCP + Git, ship the VS Code extension, write developer docs with copy-pasteable commands, and position CodeMemory as "the memory layer for AI agents." The MCP + DAG combination is strong enough to carry this positioning.

**If the target is knowledge workers:** Add full-text search, build the interactive onboarding demo, add quick-capture mechanisms, remove the developer jargon from the UI (DAG, token budget, resolve), and position as "a knowledge graph that helps AI understand your thinking." The warm palette and serif fonts already point in this direction.

**The current product is trying to serve both paths -- and succeeding at neither.** The single most important strategic decision for Round 13 is choosing one user persona and committing to it. Every feature decision, every UI polish item, and every piece of documentation should flow from that choice.

The hopeful note: both paths converge on the same technical foundation. The DAG engine, the MCP server, and the file-based architecture serve developers and knowledge workers equally well. The fork is in the UX layer, the documentation, and the go-to-market story -- not in the code.

---

*Audit completed 2026-05-07. Next review: post-Round 13.*
