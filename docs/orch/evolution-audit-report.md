# CodeMemory -- Product Evolution Audit Report

**Date:** 2026-05-06
**Reviewer:** Product Evolution Reviewer (Sprint 13 Audit)
**Methodology:** Full-stack manual testing (all 16 API endpoints), MCP server JSON-RPC 2.0 protocol verification, puppeteer DOM state capture, frontend source code review (17 components), backend architecture review, API smoke tests, all unit (57) and integration (24) tests, TypeScript compilation check, Vite production build, competitive research (SuperLocalMemory V3.4, MAG, AutoMem, Cognee, Cuba-Memorys, Obsidian, Notion)

---

## Executive Summary

**Product Evolution Maturity Score: 4.5 / 10**

CodeMemory has a genuine technical moat — DAG-based dependency resolution with topological sorting and token-budgeted context assembly — that no competitor replicates. The MCP server (5 tools) and the three-view web panel (Graph/List/Dashboard) constitute a credible v0.1 infrastructure product for AI agent memory. All 57 unit tests, 24 integration tests, 5 API smoke tests, and both TypeScript and Vite builds pass clean.

However, the product remains a **developer tool with a thin product shell**, not a product ready for users. The gap between "works for the builders" and "works for a new user" is wide and spans four categories:

1. **No data import path in the UI** — a user with 200 existing notes must create 200 memories one at a time through a form. The CLI has `codememory import --file` but the web panel has no import button, drag zone, or bulk endpoint.

2. **Primitive search** — difflib-based word matching (2005-era technology) versus competitors offering 7-channel retrieval (semantic, BM25, entity graph, temporal, associative, Hopfield, consolidation). The product's core promise of "finding connections" is undermined by its inability to search by meaning.

3. **Absent product-layer features** — no favorites/bookmarks, no batch operations, no collaboration, no mobile/responsive design, no Markdown preview, no draft auto-save, no memory templates, no graph export (buttons exist but are not wired), no API documentation surfaced to users.

4. **Missing user guidance** — empty search returns no feedback (reads as broken), empty wander returns a 404 with no user-friendly message, graph rendering failures show a blank canvas, errors are raw technical strings, and the onboarding explains concepts but doesn't guide users through their first workflow.

The competitive landscape has accelerated dramatically. SuperLocalMemory offers 35 MCP tools with 7-channel cognitive retrieval and neuroscience-inspired forgetting. MAG scores 91.1% on LoCoMo from a single Rust binary with ONNX embeddings. CodeMemory's 5 MCP tools and difflib search are a credible entry — but the feature depth gap versus multi-year incumbents is significant.

**The single largest evolution opportunity:** Core completeness — bridging the gap from "works for the developer" to "works for a new user." Import UI, semantic search, and error message UX are the three critical blocking items. Only after these are addressed should the team invest in wow-factor features.

---

## Phase 1: Core Completeness

### Current Core Loop Analysis

**What works end-to-end (with no bugs detected):**
1. A user opens the web panel, sees a 5-step onboarding wizard (skippable, persisted in localStorage)
2. They select a dataset from the header dropdown (companion/investment/quant_operators/software-architecture)
3. They view memories in three modes:
   - **Graph** — interactive D3 force-directed layout, node sizing by intensity, directory-based coloring, solid/dashed/dotted edges by import strength, zoom slider, right-click context menu (Edit/Archive), resolve animation
   - **List** — paginated table with columns (ID, summary, tags, maturity, intensity, status), text filter, click-to-select, shimmer skeleton loader
   - **Dashboard** — stats (total, maturity/type/status breakdowns, tags), validate/reindex/wander buttons, shimmer skeleton
4. They create a memory via a form (ID, summary, tags with autocomplete, body in Markdown, imports, intensity 1-10, maturity level, schema reference, semantic type)
5. They resolve a memory to see its DAG dependency chain with token-budget trimming and LLM prompt generation
6. They search memories by keyword (with tag/type/status/maturity filter support)
7. They edit or archive memories, with single-action undo
8. They export all memories as .zip (backend API), with a .zip download button in the toolbar
9. They change settings (dataset, budget, theme) persisted in localStorage
10. They access the Help panel (keyboard shortcuts, concept reference)
11. They trigger wander for serendipitous recall of cold memories
12. They run validation to check for broken links, cycles, schema compliance

**What the loop looks like for a real user:**
The ideal flow is: import existing knowledge -> wire dependencies -> browse graph -> resolve context -> inject into AI agent. But the import step is missing, so the flow breaks at step one. The user must manually create every memory through a form.

### Missing Critical Links

#### 1. Data Import — CLI-Only, No UI Path (CRITICAL)

The backend has `/api/memories` POST for single-memory creation and the CLI has `codememory import --file` for text extraction. But the web UI has **zero import capability**. A new user with existing notes, bookmarks, or chat logs has no way to bootstrap their memory graph.

**Current state:**
- CLI: `codememory import --file notes.txt --extract preferences` (works)
- CLI: `codememory import --stdin --extract decisions` (works)
- Web UI: No import button, no drag-and-drop zone, no file picker, no paste area
- API: No bulk-import endpoint, no folder-import endpoint

**Impact:** This is the #1 adoption blocker. Nobody will manually create 100+ memories through a form. The product requires users to already have the patience and technical skill to use a CLI for data ingestion.

#### 2. No Cross-Device or Cross-Session Persistence Strategy

Settings persist in `localStorage` (browser-local, per-machine). Memory files are on the local filesystem. There is no cloud sync, no remote storage option, no way to access memories from a different machine. This is acceptable for a local-first tool, but the product doesn't articulate this tradeoff — there's no documentation about data location, backup strategy, or migration path.

#### 3. Onboarding Covers Concepts, Not Workflows

The 5-step onboarding explains what Graph View and Resolve do conceptually. After clicking "Get Started," the user faces a pre-populated dataset but no guidance on what to do next:
- No "Create your first memory" CTA
- No interactive tutorial that guides through the full loop
- No progressive disclosure of advanced features
- No way to re-trigger onboarding from the UI (there is no "Tour" button)

The onboarding is well-written and skippable — this is good. But it teaches vocabulary, not workflows.

#### 4. Settings Panel is Skeletal (3 items)

Current settings: default dataset, default budget (200-5000), theme (system/light/dark). Missing:
- Keyboard shortcut customization/remapping
- Graph layout preferences (force strength, node sizing, link distance)
- Data directory configuration (change memory root from UI)
- Export format options (what to include in .zip)
- Notification preferences
- Onboarding re-trigger
- Page size for list view
- MCP server configuration guidance

#### 5. Error Messages — Raw Technical Strings

The error toast queue is well-implemented (stacked, individually dismissable, 6s auto-dismiss, slide-in animation). But error messages are raw technical strings from FastAPI or fetch exceptions:
- `"500 Internal Server Error"` — no explanation, no recovery suggestion
- `"Cannot reach server"` — no "Retry" button
- FastAPI validation error arrays dumped as joined strings — confusing for non-developers

There is no error categorization (network vs. validation vs. server), no user-friendly rewording, and no suggested recovery actions.

#### 6. No Batch Operations

Users cannot:
- Select multiple memories and tag/archive/delete them together
- Batch-update maturity levels or status
- Batch-add imports
- Bulk-import from a folder or clipboard
- Select all in filtered view

#### 7. No Draft Auto-Save in MemoryForm

If the browser crashes or the form is accidentally closed during composition, all work is lost. No localStorage draft persistence, no "unsaved changes" warning on navigation away from the form.

#### 8. No Memory Templates

Beyond referencing a schema (which defines structure fields), users cannot create and save reusable templates with pre-filled tags, imports, or body scaffolding. Schema provides structure; templates would provide content.

#### 9. MemoryForm Missing Polish

- No live Markdown preview panel (only raw textarea)
- No Markdown formatting toolbar (bold, italic, links, lists)
- No import-ID autocomplete or validation against existing memory IDs
- Schema reference selector works but shows raw schema IDs with no preview

### Empty States and Edge Cases — Inventory

| State | Handled? | Quality |
|-------|----------|---------|
| First visit (onboarding) | Yes — 5-step tour, skippable | Good |
| Dataset with 0 memories (all views) | Yes — shared EmptyState component | Good — has icon, title, description, CTA |
| Empty search results | **No** | **Critical gap** — shows nothing, reads as broken |
| Empty wander (no cold memories) | **No** | **Critical gap** — returns 404 with no user-friendly UI message |
| Graph rendering failure | **No** | Blank canvas, no error state |
| Loading states | Yes — shimmer skeleton for Graph, List, Dashboard | Good |
| Network error (server unreachable) | Yes — network error toast | Adequate — but no "Retry" button |
| Validation errors | Yes — detailed modal | Good |
| Stale memory detected | Yes — indicator in resolve output | Good |
| Budget overrun in resolve | Yes — trim level annotations | Good |
| Dataset with memories but zero imports | **No** | All 62 quant_operators memories are isolated nodes — contradicts product philosophy |

### What the quant_operators Dataset Reveals

The `quant_operators` dataset has 62 memories with **zero imports**. This violates the product's core philosophy ("memory is a dependency graph, not a search index"). A new user browsing this dataset sees 62 disconnected circles — the opposite of the interconnected knowledge graph the product promises. This dataset should either be wired with imports or removed from the default set.

---

## Phase 2: Competitive Gaps

### Competitive Landscape (May 2026)

Research covered: SuperLocalMemory (SLM) V3.4, MAG (Rust MCP server), AutoMem, Cognee, Cuba-Memorys, Obsidian, Notion, and the MAGMA research paper (arXiv:2601.03236).

The AI agent memory infrastructure market has consolidated into clear tiers:

| Tier | System | LoCoMo Score | MCP Tools | Key Architecture |
|------|--------|-------------|-----------|------------------|
| Leader | SuperLocalMemory V3.4 | 74.8-87.7% | 35 | SQLite + FTS5 + 7-channel cognitive retrieval + Fisher-Rao metric + Ebbinghaus decay |
| Strong | MAG | 91.1% | ~12 | Single Rust binary + SQLite + ONNX embeddings + FTS5 + graph traversal |
| Strong | agent-memory-store | 92.1% | ~10 | Zero-install npx + no-LLM retrieval |
| Growing | Cognee | N/A | 0 | Python SDK + LanceDB + Kuzu graph DB + ECL pipeline |
| Growing | Cuba-Memorys | N/A | 12 | Rust + KG + FSRS-6 spaced repetition + Hebbian learning |
| Growing | AutoMem | ~90.5% | N/A | FalkorDB graph + Qdrant vector + neuroscience consolidation |
| PKM | Obsidian | N/A | Via plugins | Local .md files + 1000+ plugins + Canvas + Graph View |
| PKM | Notion | N/A | No | Cloud database + Notion AI + collaboration + templates |
| **New Entry** | **CodeMemory** | **Untested** | **5** | **DAG topological sort + token budget + explicit imports + 3-view web panel** |

### Feature Comparison Matrix

| Capability | CodeMemory | SLM V3.4 | MAG | Obsidian | Notion |
|---|---|---|---|---|---|
| **Local-first** | Yes | Yes | Yes | Yes | No |
| **MCP tools** | 5 | 35 | 12+ | Via plugins | No |
| **Retrieval channels** | 2 (DAG + word search) | 7 (semantic, BM25, entity graph, temporal, associative, Hopfield, consolidation) | 3+ (FTS5, ONNX embeddings, graph traversal) | 1 (full-text + graph view) | 1 (search + DB filter) |
| **Semantic/vector search** | No | Yes (Fisher-Rao geodesic) | Yes (ONNX embeddings) | Via plugins | Via Notion AI |
| **Automatic memory lifecycle** | Manual only | Ebbinghaus decay + consolidation | Neuroscience-inspired cycles | Manual | Manual |
| **Multi-agent trust** | No | Bayesian trust scoring | No | No | Permissions |
| **Web dashboard** | 3 views | 23 tabs | CLI only | Full app | Full app |
| **Plugin ecosystem** | No | No | No | 1000+ plugins | Templates + API |
| **Collaboration** | No | No | No | Paid sync | Real-time |
| **Mobile** | No | No | No | Paid app | Native apps |
| **Data format** | YAML frontmatter + .md | SQLite + FTS5 | SQLite | Plain .md | Proprietary |
| **Embedding model** | None | TF-IDF (zero-LLM) | ONNX (local) | Via plugins | Notion AI |
| **Graph visualization** | Interactive D3 | 23-tab dashboard | No | Graph + Canvas | No |
| **Import from external tools** | CLI only | No | No | Community plugins | Native importers |
| **SDK / client libraries** | No | npm + pip | Cargo crate | Plugin API | REST API |
| **Pricing** | Free (open source) | $0 forever (AGPL) | Free (MIT) | Free + $4/mo sync | Free + $10-20/mo AI |
| **LoCoMo benchmark** | Untested | 87.7% | 91.1% | N/A | N/A |

### Critical Missing "Table Stakes"

These features are present in at least 2 competitors and absent from CodeMemory, making the product feel incomplete to anyone evaluating alternatives:

1. **Semantic search** — Every competitor has some form of embedding-based retrieval. CodeMemory's difflib is a placeholder, not a feature.

2. **Multiple retrieval strategies** — SLM has 7, MAG has 3+. CodeMemory has 1.5 (exact + difflib). The product philosophy ("memory is a dependency resolution problem, not a search problem") is a strong thesis — but it doesn't excuse having only one retrieval mode. Users need both: explicit DAG resolution AND fuzzy discovery.

3. **Memory lifecycle automation** — Competitors offer automatic decay, consolidation, and pruning based on access patterns. CodeMemory requires manual stale checks and manual status updates.

4. **Import/ingestion pipeline** — SLM has an 11-step ingestion pipeline. CodeMemory has a CLI `import` command with basic text extraction and no UI.

5. **Benchmark scores** — Every competitor publishes LoCoMo scores. CodeMemory has none. For AI engineers evaluating tools, "what's the score?" is the first filter. Without a number, CodeMemory is invisible.

### Competitive Pain Points — CodeMemory's Opportunities

| Competitor Weakness | CodeMemory's Advantage |
|--------------------|----------------------|
| SLM: 7-channel fusion is probabilistic; no deterministic dependency chains | CodeMemory's explicit `imports` DAG is auditable, traceable, zero-hallucination |
| MAG: Single SQLite file, no graph visualization | CodeMemory's D3 graph is unique among agent memory tools |
| All agent memory tools: No visual knowledge graph UX | CodeMemory has a polished graph + resolve + prompt-generation UX |
| All competitors: Implicit/similarity-based connections | CodeMemory's explicit dependency declarations enable formal reasoning |
| Obsidian: No MCP, no AI agent integration | CodeMemory's MCP server makes it AI-agent-native |
| Notion: Cloud-dependent, proprietary format | CodeMemory is local-first with open .md files |

### User Feedback Themes from Competitor Research

- **"I want to auto-tag and auto-link"** — SLM users praise automatic pattern extraction. CodeMemory has `suggest-deps` CLI but no UI for it and no learning layer.
- **"I need my memory everywhere"** — Cross-device sync is the #1 Obsidian feature request. CodeMemory has no answer to this.
- **"Don't make me think about graph structure"** — Notion users prefer databases over explicit graph wiring. CodeMemory demands users manually manage imports. This is the product's identity, but it needs better tooling (auto-suggest, templates) to reduce the burden.
- **"Show me what I forgot"** — SLM's wander shows access counts. CodeMemory's wander stores this data but doesn't display it in the UI.

---

## Phase 3: Functional Depth

### Feature Depth Assessment

#### Graph View — Moderate Depth (7/10)

**Deep:**
- Interactive D3 force-directed layout
- Node sizing by intensity (1-10 scale)
- Directory-based coloring (10+ directories, both themes)
- Edge styling by import strength (solid = required, dashed = recommended, dotted = related)
- Zoom slider with percentage display
- Right-click context menu (Edit, Archive)
- Resolve animation (topological highlight pulse + trim dimming)
- Search highlighting
- Hover tooltips with summary
- Dynamic legend (updates with visible directories)

**Shallow:**
- No graph filtering by tag/type/maturity (must rely on search)
- No subgraph extraction ("focus on this node and its 2-hop neighborhood")
- No layout algorithm choice (only force-directed)
- No node pinning
- No graph analytics (centrality, clustering, connected components)
- No export of current view as SVG/PNG (buttons in toolbar but functionality unverified)
- No comparison view (two subgraphs side-by-side)

#### Resolve — Strong Depth (8/10) — Core Differentiator

**Deep:**
- Three depth levels: required, recommended, full
- Token budget slider (200-5000)
- Topological sort of DAG
- Three trim levels: full, summary, skipped
- Stale detection with indicator
- Pinned version notices
- Debounced re-resolution (300ms)
- Resolve-to-prompt generation with formatted LLM context
- Copy-to-clipboard with visual feedback
- Budget overrun indicators

**Shallow:**
- No diff view (what changed since last resolve?)
- No side-by-side comparison of two resolves
- No resolve history or caching
- No bookmark/save of resolve configurations
- No scheduling/automation of resolves
- No multi-target resolve (resolve several IDs in one operation)

#### Memory CRUD — Adequate (6/10)

**Deep:**
- Full form: ID, summary, tags (autocomplete), body (Markdown), imports, intensity, maturity, schema, semantic type
- Undo for most recent action
- Tag autocomplete with keyboard nav
- Import management (add/remove dependency edges)
- Schema reference selection

**Shallow:**
- No Markdown preview in the form
- No Markdown formatting toolbar
- No duplicate/clone memory
- No version history beyond changelog
- No draft auto-save
- No import-ID autocomplete or validation
- No templates beyond schema reference

#### Search — Shallow (4/10)

**Deep:**
- Full-text keyword search
- Tag filtering without query text
- Type/status/maturity filter support
- Debounced input (300ms)
- Paginated results (20 per page)

**Shallow:**
- No fuzzy/semantic matching (difflib-based word overlap only)
- No search within body text (body content loaded from disk on each search — not indexed)
- No advanced query syntax (AND/OR/NOT, `tag:`, `type:`, `before:`)
- No saved searches
- No search history
- No search result sorting options
- No "no results" empty state feedback
- Results dropped silently in certain filter combinations (known issue R7-N3)

#### Dashboard — Shallow (4/10)

**Deep:**
- Stats: total count, maturity breakdown, type breakdown, status breakdown
- Tag cloud
- Stale count
- Validate and reindex trigger buttons
- Wander button

**Shallow:**
- No trends over time (memory creation rate, decay rate)
- No health score aggregation
- No recommendations ("3 memories stale, 2 have broken links")
- No activity feed (what changed recently?)
- No customizable widgets
- No export of dashboard data

#### List View — Adequate (6/10)

**Deep:**
- Paginated with First/Prev/Next/Last controls
- Columns: ID, summary, tags, maturity, intensity, status
- Click to select and view detail
- Text filter (client-side)
- Shimmer skeleton loader

**Shallow:**
- No sorting by column
- No multi-select checkboxes
- No inline editing
- No customizable columns
- No quick-filter chips
- Loads all memories client-side (not scalable beyond ~1000)

### Integration and Extensibility

| Aspect | Status | Notes |
|--------|--------|-------|
| MCP Server | 5 tools, stdio JSON-RPC 2.0 | Good architecture, zero logic duplication. But 5 tools vs 35 from SLM. |
| REST API | 16 endpoints, no auth, no rate limiting, no versioning | Functional but no versioning strategy. |
| API Docs | OpenAPI at `/docs`, not linked from UI | Users must know to visit `/docs` manually. |
| SDK | None | No Python/TypeScript client libraries. |
| Webhooks | None | No external tool integration. |
| Plugin system | None | No extensibility model. |
| Import connectors | CLI only | No GitHub, Notion, Obsidian, or bookmark import. |
| Code splitting | None | Single 987KB JS bundle (297KB gzipped). |

### Collaboration — Zero

No sharing, no multi-user, no comments, no suggestions, no version merge. This is a deliberate choice for a local-first tool, but it means the product cannot serve team use cases.

---

## Phase 4: Differentiation and Wow Factor

### The Genuine Moat

CodeMemory's core differentiator — **"memory loading is a dependency resolution problem, not a search problem"** — is the only genuinely unique architectural position in the AI memory market. Explicit DAG-based resolution with topological sorting and token-budgeted trimming has no equivalent in any competitor. This is the product's identity and should be amplified, not diluted.

The MCP server makes this moat externally callable. Any MCP-compatible AI agent can now use CodeMemory's deterministic resolution as its memory backbone. No competitor offers deterministic, auditable dependency resolution as an MCP tool.

### "If Only It Could..." — Wow-Factor Proposals

#### 1. Temporal Memory Graph — "Time-Travel Through Your Thinking"

A timeline slider that shows how the knowledge graph evolved over weeks or months. As the user drags, nodes appear, edges form, old memories fade, new ones emerge. The data already exists (created_at, updated_at, changelog history, access_count).

**Why it matters:** No product in the market visualizes knowledge evolution temporally. This would be screenshot-worthy, shareable, and unique. It makes the implicit evolution of thinking explicit.

#### 2. AI-Powered Dependency Suggestion — "The Graph That Writes Itself"

As users create memories, the system proactively suggests imports: "This new memory about React hooks probably depends on 'JavaScript fundamentals.' Add import?" Over time, a learning layer observes patterns and auto-suggests edges with confidence scores.

**Why it matters:** Manual import wiring is the #1 friction point. The `suggest-deps` CLI already proves this is feasible. A learning layer on top creates a "magic" feeling — the tool understands how you think.

#### 3. Memory Publishing & Discovery — "GitHub for Ideas"

Let users publish individual memories or subgraphs as public, shareable, citable artifacts. Other users can "fork" a memory into their own graph. Creates a network of interconnected knowledge graphs across users.

**Why it matters:** No tool allows sharing granular memory atoms with dependency context. Obsidian Publish shares entire vaults; this shares semantic units. Academic and research communities would adopt this for literature reviews and knowledge synthesis.

#### 4. Resolve-to-Notebook — "Interactive Dependency Exploration"

Instead of flat text output, resolve a memory into an interactive notebook where each dependency is a collapsible section with source links, graphs, and expandable context. The current resolve-to-prompt is already well-formatted — this is the next level.

**Why it matters:** Makes the resolve output explorable rather than just readable. Turns a linear text dump into an interactive exploration tool.

#### 5. Memory Health Dashboard with Decay Visualization

Visualize which parts of the knowledge graph are atrophying using existing stale detection, access_count, and maturity data. Show clusters that have no remaining importers, memories approaching staleness, and knowledge that needs refreshing.

**Why it matters:** Unique to CodeMemory's explicit dependency model. Vector-similarity systems cannot show "this cluster has no importers" because they don't have explicit imports.

### Word-of-Mouth Triggers

| Trigger | Current Status | Viral Potential |
|---------|---------------|----------------|
| "My AI agent has perfect memory via CodeMemory MCP" | MCP server shipped, 5 tools | High |
| "It showed me a connection I didn't realize existed" | Resolve DAG traversal works | Medium — under-marketed |
| "The graph is gorgeous" | D3 visualization, dark mode tints | High — aesthetic is shareable |
| "I imported 200 notes and it auto-wired the dependencies" | No import, no auto-wire | Zero — critical gap |
| "It told me which memories I'd forgotten" | Wander works but doesn't show decay context | Low — needs improvement |
| "CodeMemory beat SLM on structured reasoning benchmarks" | No benchmarks | Zero — untapped |

### What to Delete or Simplify

1. **Remove or wire the quant_operators dataset.** 62 memories with zero imports contradicts the product's core philosophy. It teaches new users the wrong thing about CodeMemory.

2. **Remove the duplicate PNG export button.** The toolbar has a PNG button; cytoscape renders its own. Consolidate to one that actually works.

3. **Retire legacy "type" terminology from the UI.** The codebase has unified to "atom" — but Graph colors nodes by "type" and List shows a "type" column. Show only `atom` and `schema`. Hide the implementation history.

4. **Consider reducing the Settings panel to a slide-out drawer.** With only 3 settings, a full fixed panel occupying 34vw is disproportionate. Or expand Settings to justify the space.

5. **Auto-dismiss the dataset disclaimer.** "Stats, validation, and reindex apply to the selected dataset" is shown persistently. Show it briefly on dataset switch (3 seconds), then auto-dismiss.

---

## Technical Health (Ancillary)

### Architecture Scalability Risks

| Risk | Severity | Detail |
|------|----------|--------|
| Monolithic `server.py` (~1400 lines) | Medium | All routes, search, export, reindex in single file. Each new feature adds to the monolith. No route group boundaries. |
| Monolithic `App.tsx` (~1540 lines) | Medium | 15+ useState hooks, all view logic, error handling, context menu, undo. No context provider or state management library. |
| Synchronous FastAPI endpoints | High | All endpoints are `def` (synchronous). Reindex, validate, export are blocking. At 10,000+ memories, these will block the event loop. No background task queue. |
| In-memory index with file persistence | Medium | Full index loaded into memory on startup. Fine at 10-62 memories; will consume significant RAM and slow startup at 10,000+. |
| No API versioning | Medium | All routes at `/api/*` with no version prefix. Breaking changes break all clients. |
| Single 987KB JS bundle | Medium | No code splitting, no lazy loading. Entire app downloads on first load. Will hurt on slow connections and mobile. |
| CORS wildcard | Low (local dev) / High (deployment) | `allow_origins=["*"]` with no authentication. Acceptable for localhost; a security incident for any deployment. |
| Path traversal risk | Low | Memory IDs contain `/` and are used in file paths. Input validation exists but defense-in-depth is absent. |

### Key Performance Bottlenecks

| Bottleneck | Impact | Fix Effort |
|-----------|--------|-----------|
| Reindex scans all .md files synchronously | O(n) file I/O. Fine at 62 files; problematic at 1000+. | Medium — add async/background processing |
| Graph API returns all nodes + edges | No pagination or subgraph queries. Frontend receives entire graph every refresh. | Medium |
| Search is O(n*m) linear scan with difflib | Body text read from disk for every candidate on every search. Degrades at 500+ memories. | Medium — index body text; add embedding search |
| `_load_index()` reads from disk on every request | I/O per API call. Cached minimally. | Low — add TTL cache |
| D3 force simulation on every graph render | No Web Worker offloading. No virtualization. | Medium |
| Client-side list filtering loads all memories | `fetchAllMemories(10000)` loads everything to filter client-side. | Medium — server-side filtered pagination |

### Test Coverage

| Layer | Tests | Assessment |
|-------|-------|-----------|
| **Unit (Python)** | 57 | Good — resolve, validate, create/update, edge cases. Gaps: search, index, handlers, CLI, tools. |
| **Integration (Python)** | 24 | Good — full workflow (create, update, resolve, wander, snapshot, cleanup). |
| **API smoke tests** | 5 | Minimal — covers GET /memories, GET /memories/{id}, POST /search, POST /resolve, GET /stats. No write-path coverage. |
| **MCP server** | 0 | **Gap** — no JSON-RPC protocol tests, no tool call verification. |
| **Frontend** | 0 | **Gap** — no Jest, no Vitest, no React Testing Library, no Playwright/Cypress. |
| **TypeScript** | Clean | `tsc --noEmit` passes with zero errors. |
| **Vite build** | Clean | Builds in 333ms. Warning: single chunk >500KB. |

**Assessment:** Backend core engine has adequate coverage. Frontend has zero automated tests — this is a significant quality risk as complexity grows. MCP server has zero tests despite being the strategic differentiator.

### Minimum Test Additions for Next Sprint

- 3 MCP server tests: initialize handshake, tools/list returns 5 tools, tools/call resolve_memory
- 3 API write-path tests: POST create, PUT update, POST wander
- 1 integration test: create -> update body -> confirm stale -> reindex -> confirm cleared
- 1 frontend smoke test: App renders without crash (React Testing Library)

---

## Prioritized Recommendations

### Critical — Blocking Market Readiness (Sprint 13-14)

| # | Recommendation | Effort | Rationale |
|---|---|---|---|
| **C1** | **Data Import UI** — Build an import page/dialog supporting: plain text paste, file upload (.md, .txt, .json), and URL fetch. Leverage existing `import_cmd.py` extraction logic. Add bulk-import API endpoint. | Medium | #1 adoption blocker. No one types 100 memories by hand. |
| **C2** | **Semantic/Fuzzy Search** — Integrate a lightweight local embedding model (all-MiniLM-L6-v2 via ONNX, or TF-IDF + BM25 as lighter option). Generate embeddings on reindex. Store in index.json. Complement, not replace, existing search. Following MAG's proven pattern. | Medium-High | Every competitor has multi-strategy retrieval. Current difflib search undermines the product's credibility. |
| **C3** | **Error Message UX Pass** — Rewrite all user-facing error messages to be actionable: (1) what happened, (2) why, (3) what to do next. Add "Retry" and "Copy error details" buttons. Categorize errors (network/validation/server). | Low | Current raw technical strings erode trust. Fast fix, high impact. |
| **C4** | **Empty State Completion** — Add "No results matching your search" with suggestions for search. Add "No cold memories found — create more memories to enable Wander" for empty wander. Add graph rendering failure state. | Low | Empty states that show nothing read as broken features. |
| **C5** | **First-Run Workflow** — After onboarding, show an interactive tutorial: "Let's create your first 3 memories and link them. (1) Create a memory. (2) Create another. (3) Link them with an import. (4) Resolve to see the chain." | Medium | Onboarding explains concepts but doesn't build a habit. |
| **C6** | **Publish Benchmark Scores** — Run CodeMemory's resolve engine against LoCoMo and LongMemEval. Publish results. | Medium | Every competitor has a score. Without one, CodeMemory is filtered out before evaluation begins. |

### Important — Significant Completeness Gains (Sprint 14-15)

| # | Recommendation | Effort | Rationale |
|---|---|---|---|
| **I1** | **Favorites/Bookmarks** — Let users star/bookmark memories. Add "Favorites" filter and "Recently Viewed" list. Persist in localStorage. | Low | Simple feature with high perceived value. Builds attachment. |
| **I2** | **Wander Improvements** — Show access_count, last_access, and decay context in the wander card. Add "Wander Again" button. | Low | R7-wander-improve is already spec'd. Makes Wander feel like a feature. |
| **I3** | **Batch Operations** — Multi-select checkboxes in List view with batch: tag, archive, change maturity, add imports. Add bulk PATCH endpoint. | Medium | Users managing 50+ memories need this. |
| **I4** | **Auto-Import Suggestion in UI** — Surface `suggest-deps` as a button in MemoryForm: "Suggest dependencies." Show confidence scores, let users accept/reject. | Medium | Manual import wiring is friction. CLI already has this logic. |
| **I5** | **Memory Templates** — Beyond schema reference, allow users to create and save memory templates (pre-filled tags, imports, body scaffolding). | Low-Medium | Accelerates memory creation. Schema provides structure; templates add content. |
| **I6** | **Draft Auto-Save** — localStorage persistence of in-progress MemoryForm. "Unsaved changes" warning on navigation. | Low | Prevents data loss. Standard in all modern form UX. |
| **I7** | **Graph Export (SVG/PNG)** — Wire the existing PNG/EXPORT toolbar buttons to actual D3 SVG/PNG export functionality. | Low | Buttons exist but may not work. Low-hanging fruit. |
| **I8** | **Index Caching** — In-memory TTL cache for `_load_index()` with write-through invalidation on reindex. Cache body text in index during reindex. | Low | Eliminates disk read on every API request. Foundation for scale. |
| **I9** | **Responsive Layout** — CSS pass to make List and Dashboard views usable on tablets. Mobile graph view is stretch; List and Dashboard should work on phones. | Medium | 40%+ of knowledge workers use mobile for reference. |
| **I10** | **Expand Settings** — Keyboard shortcut customization, graph layout preferences, page size for list view, onboarding re-trigger, MCP configuration guidance. | Medium | 3 settings is insufficient for a tool with this feature surface. |

### Nice-to-Have — Power-User and Polish (Sprint 15-16)

| # | Recommendation | Effort | Rationale |
|---|---|---|---|
| **N1** | **Graph Analytics** — Centrality metrics, connected components, clustering coefficient. "Most central memory" and "most isolated memory" shown in Dashboard. | Medium | Builds on existing D3 integration. Differentiates the graph view. |
| **N2** | **Markdown Preview + Toolbar** — Split-pane editor with live preview. Bold, italic, links, lists toolbar buttons. | Medium | Reduces edit-save-check loop. Standard in Markdown editors. |
| **N3** | **Advanced Search Syntax** — Support `tag:`, `type:`, `imports:`, `maturity:`, `before:`, `after:` query filters. | Medium | Power users expect this. GitHub/Notion/Obsidian all have it. |
| **N4** | **Memory Diff View** — Side-by-side comparison of memory versions with highlighted changes. | Low-Medium | Builds on existing changelog. Makes editing feel safe. |
| **N5** | **Server-Side Filtered Pagination** — Replace `fetchAllMemories(10000)` with server-filtered pagination for List view. | Medium | Current approach breaks at scale. |
| **N6** | **Code Splitting** — Use `React.lazy()` for Dashboard, Settings, Help, Onboarding. | Low | Reduces initial JS bundle by ~30%. |
| **N7** | **Search History & Saved Queries** — Recent searches dropdown, save and name search queries. | Low | Power-user feature that costs almost nothing. |
| **N8** | **Wander History Sidebar** — Show recently wandered memories with timestamps. | Low | Simple addition to the wander feature. |
| **N9** | **MCP Tools Expansion** — Add `search_memory`, `validate_memory`, `suggest_deps` as MCP tools. | Medium | 5 tools is credible for v0.1. 8 tools starts to close the gap. |
| **N10** | **MCP Server Tests** — JSON-RPC protocol tests, tool call verification, error path tests. | Low | MCP server is the strategic differentiator with zero tests. |

### Feature Ideas — Differentiated Innovation (Backlog)

| # | Idea | Effort | Why It Matters |
|---|---|---|---|
| **F1** | **Temporal Graph View** — Timeline slider showing graph evolution. Uses existing created_at/updated_at/changelog data. | High | Unique in the market. Screenshot-worthy organic marketing. |
| **F2** | **Memory Publishing & Discovery** — Publish memories as public URLs. Fork into personal graphs. | Very High | Creates network effects. Tool becomes a platform. |
| **F3** | **AI Co-Pilot for Graph Building** — Learning layer that observes import patterns and auto-suggests edges. | High | `suggest-deps` CLI is the proof of concept. Learning layer creates magic. |
| **F4** | **Resolve-to-Notebook** — Interactive dependency exploration with collapsible sections, graphs, expandable context. | Medium | Transforms resolve from text dump to exploration tool. |
| **F5** | **Memory Health Dashboard** — Atrophy visualization, orphan clusters, staleness trends, decay forecasts. | Medium | Unique to CodeMemory's explicit dependency model. No competitor can show "this cluster has no importers." |
| **F6** | **Voice Notes to Memory Graph** — Record voice, transcribe, extract entities/claims, suggest structure and imports. | High | Expands user base beyond text-heavy workflows. |
| **F7** | **Collaborative DAG Merge** — Share subgraphs, merge perspectives, highlight dependency conflicts. | Very High | Transforms from personal tool to collaborative reasoning platform. |

---

## Summary

CodeMemory is a technically sound kernel surrounded by a thin product shell. The DAG resolution engine is a genuine moat — no competitor does deterministic dependency-based context assembly with token budgeting. The MCP server correctly positions the product as AI agent infrastructure.

But the product is not ready for users who don't already understand dependency graphs. The import path is CLI-only. Search is primitive. Settings are skeletal. Errors are raw. Empty states are incomplete. Onboarding teaches vocabulary but not workflows.

**The two sprints ahead should focus relentlessly on Core Completeness (C1-C6) and Competitive Gaps (I1-I10).** Only after these are addressed should the team invest in wow-factor features (F1-F7). A product that works reliably for basic workflows with good error recovery, import paths, and search will attract users. A product with a temporal graph view but no way to get data into it will not.

**The single most impactful action this sprint: Build the data import UI.** Everything else is polish on an empty room.

### Score Breakdown by Dimension

| Dimension | Score | Key Gap |
|-----------|-------|---------|
| Core Completeness | 3/10 | No import UI, skeletal settings, incomplete empty states, raw errors |
| Competitive Gaps | 3/10 | No semantic search, 5 tools vs 35, no benchmarks, no memory lifecycle automation |
| Functional Depth | 5/10 | Resolve is deep (8/10), Search is shallow (4/10), Dashboard is shallow (4/10) |
| Differentiation | 7/10 | DAG resolution is unique and defensible. MCP server makes it callable. |

**Overall: 4.5 / 10**
