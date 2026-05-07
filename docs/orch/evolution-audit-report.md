# CodeMemory -- Product Evolution Audit Report

**Date:** 2026-05-07
**Reviewer:** Product Evolution Reviewer (Product Strategy)
**Build:** Post-Round 16 (16/16 PASS, 91/91 tests), APIRouter split complete, full-text body search, writable MCP tools, per-memory stability UI
**Previous score:** 6.5/10 (post-R15)
**Current score:** 7.5/10

> **Note on score increase (+1.0 from R15):** Round 16 closed the single largest product gap (full-text search, deferred R12-R15), completed the agentic loop (writable MCP tools), and delivered the APIRouter backend refactor — all while adding 0 regressions. The engine score rises to 9.5/10; the product experience score rises from 4/10 to 6/10. The remaining gap is still dominated by the Input Problem (no import UI) and the AI Copilot Paradox (no AI-assisted creation in the Web UI), both deferred to future Sprints by explicit negotiation.

**Methodology:** Full source code review (backend/server.py 142 lines + 3 routers + shared.py, frontend/src 12 components + App.tsx 1667 lines), live API testing (19 endpoints verified, /docs 200), Puppeteer page-state extraction, competitive landscape research (Obsidian v1.12.7+ CLI/Skills/Bases/MCP, Notion AI Agents 3.2, Mem.ai Mem X multi-model), Gemini audit report synthesis, negotiation document review, R16 gen_status.md verification.

---

## Executive Summary

CodeMemory emerged from Round 16 with its strongest-ever technical foundation. The Product-Loop investment cycle (Rounds 12-16) successfully delivered what it set out to deliver: a correct decay model, a tastefully restrained dark-mode UI, full-text search, and a clean backend architecture. The deterministic DAG dependency resolution engine remains the product's defensible strategic moat, and the newly added writable MCP tools (`propose_memory`, `propose_update`) close the agentic loop — an Agent can now both read from and write to the memory brain.

However, the product still sits in the **technology-validated but commercially-incomplete** zone. The two structural fractures identified in the R15 audit remain unresolved by explicit negotiation choice:

1. **The Input Problem:** Users cannot get their data into the system without using a CLI. There is zero import UI in the Web interface. This is existential for any knowledge management tool.
2. **The AI Copilot Paradox:** CodeMemory is a memory system designed *for* AI Agents, yet humans creating memory cards in the Web UI receive zero AI assistance — no auto-summary, no tag suggestion, no related-memory recommendation.

The current score of 7.5/10 reflects: **engine 9.5/10, product experience 6/10.** The next Sprint must shift investment from engine polish to intake valves and AI copilot systems.

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
| **Capture** | `codememory create` CLI + MemoryForm UI + `propose_memory` MCP tool | WARNING: Single-item entry only; no bulk pipeline; no import UI |
| **Structure** | `imports` explicit dependency declaration + `suggest_deps` CLI | WARNING: Dependency inference CLI-only; MemoryForm has no autocomplete |
| **Consumption** | Resolve DAG + Overview + Focus + Wander + full-text Search | HEALTHY: Core pipeline complete; full-text search closes last retrieval gap |
| **Feedback** | Validate + stale detection + maturity upgrade + decay risk + stability slider + Touch | HEALTHY: Feedback loop is now two-way (read + write stability) |

### C1: Bulk Import Pipeline in Web UI -- CRITICAL (unchanged from R15)

**Current state:** The system provides `codememory import --file notes.txt --extract preferences` as a CLI command and API endpoint (`POST /api/import`), but the Web UI has zero import entry points. MemoryForm only supports single-card manual creation. `suggest_deps.py` provides three-layer filtered automatic dependency inference — but is only exposed through CLI.

**Why this remains a core completeness problem:** For any knowledge management tool, "cold start" is the first retention barrier. If a user has 100 old notes, 50 solved-problem Markdown files, or an existing Obsidian vault, they need:
1. A **visible import entry point** (drag-and-drop zone, file picker)
2. A **preview-and-confirm flow** (see what will be created before committing)
3. **Post-import automatic dependency inference** (after importing 100 memories, automatically run suggest-deps and display suggestions in UI)

None of these exist today. Users must import via CLI then manually refresh the UI.

**R16 status:** Explicitly deferred by negotiation — "future Sprint 最高优先级."

**Recommendation:** Add an "Import" button to Dashboard or main nav -> multi-file Markdown drop zone -> preview table (id/summary/tags/estimated imports) -> bulk confirm creation + trigger suggest-deps.

**Estimated effort:** ~3 days

### C2: MemoryForm Imports Autocomplete -- CRITICAL (unchanged from R15)

**Current state:** `suggest_deps.py` backend logic is complete, but in the Web UI's MemoryForm, users must manually type every import as comma-separated ID strings. No autocomplete. No suggestion list. No "board-style" related memory recommendations.

**Why this remains a core completeness problem:** The DAG's quality depends on edge accuracy. If users must manually input every dependency, graph accuracy will rapidly deteriorate beyond ~20 memories. The entire value proposition of the DAG memory protocol is undermined by hand-typed imports.

**R16 status:** Deferred by negotiation.

**Recommendation:** Add a "Suggest Dependencies" button next to the Imports field in MemoryForm -> async call to suggest-deps API -> display suggestions as a checkable list (with match scores and filter rationale) -> user checks/unchecks to auto-populate imports.

**Estimated effort:** ~1 day

### C3: Writable MCP Tools -- RESOLVED (R16-M1)

**Previous state (R15):** 4 of 5 MCP tools marked `readOnly`. Agents could read but not write.

**R16 resolution:** `mcp_server.py` now exposes 7 tools total:
- **5 readOnly:** `resolve_memory`, `overview`, `wander`, `focus`, `snapshot`
- **2 writable:** `propose_memory` (creates `maturity: draft` + `status: proposed`) and `propose_update` (prefixes change_log entry with `[PROPOSED]`)

Both writable tools stage content for human review rather than silently overwriting curated memories. This is a well-designed security middle path that closes the agentic loop.

**Remaining gap:** There is no "Proposed" queue in the Web UI for humans to review/approve proposed memories. The staging mechanism exists but the review interface does not.

### C4: Full-Text Body Search -- RESOLVED (R16-C1)

**Previous state (R15):** SearchBar supported substring/fuzzy matching against ID, summary, tags, and first 120 characters of body. Did not index full body content.

**R16 resolution:** The search endpoint now reads `.md` file body content and includes it in fuzzy matching. Match priority order: ID > summary > tag > body. Search results include highlighted snippets (`<mark>` tags wrapping matched keywords). The "escape hatch" of memory retrieval is now fully open.

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
      |           |   (CLI/Skills/   |  CodeMemory <---- |   (Mem X +       |
      |           |    Bases/MCP)    |  (DAG + decay)    |    multi-model)  |
     Developer/   |                  |                   |                  |
     Agent        |   Git repos      |  HGP              |  SHIMI           |
      v           |                  |  DragonScale      |  SwiftMem        |
                  |                  |  LCM              |                  |
                  +------------------+-------------------+------------------+
```

### Key Competitor Profiles (2025-2026 updated)

| Dimension | Obsidian | Notion AI | Mem.ai | CodeMemory |
|-----------|----------|-----------|--------|------------|
| **Data model** | Markdown files + backlinks + Bases | Block-based databases | AI-organized notes | Markdown + DAG imports |
| **Retrieval** | Graph view + keyword search + CLI search | Keyword + AI Q&A + AI Agent | Semantic search + Mem Chat | DAG resolution + full-text fuzzy search |
| **AI approach** | Official Skills for Claude Code + MCP servers (2026) | Native AI Agents (GPT-5/Claude 4), $20-24/mo | AI-native (GPT-4/Claude/Gemini), $15/mo | MCP tools (7, 2 writable) |
| **Data ownership** | Full -- local plain files | Cloud-only, vendor lock-in | Cloud-only | Full -- local .md files |
| **Import** | Drag-and-drop + CLI + Web Clipper + community plugins | .csv/.md/.html + migration tools | AI extraction from Apple Notes/Gmail/Email/SMS/Voice | CLI + API only |
| **Mobile** | Native iOS + Android | Native mobile apps | iOS app (no Android) | None |
| **Price** | Free core; Sync $4-5/mo | Free tier; Plus ~$10/mo; AI +$10/mo | Free tier; Mem X ~$15/mo | Open source |
| **Key 2026 move** | Official CLI (v1.12.7+) + Agent Skills (Kepano) | AI Agents with Slack/MCP integration | Claude Connector + multi-model Chat | Writable MCP tools (propose/review) |

### Competitive Analysis: The 2026 Landscape Shift

**Obsidian's CLI and Agent Skills are the most significant competitive development for CodeMemory.** Obsidian CEO Kepano open-sourced an Agent Skills repository in January 2026 that teaches AI coding assistants (Claude Code, Codex CLI, Google Antigravity) to natively read/write Obsidian Flavored Markdown, Bases (`.base` database views), and JSON Canvas (`.canvas` whiteboards). Combined with the new CLI (`obsidian search`, `obsidian create`), Obsidian is evolving from a writing app into a machine-addressable knowledge OS.

This directly competes with CodeMemory's "Agent-accessible memory" positioning. The differentiation is that CodeMemory's DAG resolution provides *deterministic, token-budget-aware context assembly* — Obsidian's approach lacks the compilation semantics and token budget constraints.

**Notion AI Agents (3.2, Feb 2026)** are the most aggressive move in the market. Notion's AI Agents can autonomously execute multi-step tasks across hundreds of pages for up to 20 minutes, with native Slack integration and MCP extension support. This raises the bar for what "AI-assisted knowledge management" means — from in-line text generation to autonomous workflow execution.

**Mem.ai's Mem X (2025)** with multi-model Chat (Claude/Gemini/GPT), calendar integration, meeting briefings, and Claude Connector demonstrates that AI-first knowledge management is converging on "proactive context surfacing" rather than passive storage. The "Heads Up Live" feature — real-time related-note surfacing during live meeting transcripts — is a preview of where the category is heading.

### G1: Visible Import Entry Point -- CRITICAL (unchanged from R15)

**Competitor standard:** Obsidian supports Markdown file drag-and-drop + CLI import + Web Clipper + community plugins (Notion/Evernote/Roam migration). Notion supports .csv/.md/.html import + native migration tools. Mem.ai auto-extracts from Apple Notes/Google Keep/email/SMS/voice.

**CodeMemory state:** CLI-only `codememory import`. API endpoint exists (`POST /api/import`) but Web UI has zero import entry points.

**Gap severity:** This is the most basic table stake. A user's first question upon seeing the product: "How do I get my data in?" The current answer: "Open a terminal and type a command."

### G2: AI-Assisted Creation -- CRITICAL (unchanged from R15)

**Competitor standard:** Notion AI proactively offers "summarize/translate/rewrite/continue" on selected text. Mem.ai suggests related notes and auto-tags in real-time as the user types. Obsidian's official Agent Skills enable AI to generate properly formatted Obsidian content including Wikilinks, Callouts, Embeds, and Properties.

**CodeMemory state:** MemoryForm is a plain text form. No AI assistance — no auto-summary generation, no auto-tag suggestion, no "based on body content, recommend related memories." The irony is sharp: it's a memory system designed **for AI Agents**, but humans creating memories in the UI receive zero AI help.

**Gap severity:** This is CodeMemory's biggest cognitive dissonance. The competitive landscape is accelerating in this direction — Notion AI Agents, Mem.ai multi-model Chat, and Obsidian Skills all assume AI assistance is table stakes for knowledge management in 2026.

**Recommendation:** Add an "AI Assist" button beside the body field in MemoryForm -> call LLM Gateway (exists but not integrated into frontend) -> provide auto-summary extraction, tag suggestions, and related-memory link recommendations.

**Estimated effort:** ~2 days

### G3: Semantic Search (Hybrid) -- IMPORTANT (unchanged from R15)

**Competitor standard:** Mem.ai's core differentiator is semantic search — natural language queries directly return relevant notes. Notion AI supports cross-workspace semantic Q&A. Obsidian community plugins (Smart Connections) provide vector embedding search.

**CodeMemory state:** Design philosophy explicitly rejects vector search in favor of deterministic DAG resolution. R16's full-text search (C1) significantly improves the "cold memory discovery" scenario — users can now find memories by body content — but it remains keyword/fuzzy-based rather than semantic. The Wander mechanism partially fills this gap but cannot replace active semantic search.

**Gap severity:** Medium. Full-text search closes the most critical gap. Semantic search would be a nice complement for "I vaguely remember a concept but not the wording" scenarios.

**Recommendation (non-urgent):** Consider adding optional vector embeddings to support hybrid search (Hybrid Search = DAG resolution + semantic recall), complementary to, not replacing, DAG. Semantic recall results display as "Suggested to review," not overriding the deterministic resolution pipeline.

**Estimated effort:** ~5 days

### G4: Responsive/Mobile Experience -- IMPORTANT (unchanged from R15)

**Competitor standard:** Obsidian has native mobile apps (iOS + Android). Notion and Mem have responsive Web + native mobile apps. Mem 2.0 strengthened offline support and voice capture mode. Notion 3.2 added mobile-native AI Agent functionality.

**CodeMemory state:** Interface designed for large screens (1200px+). The `min-width: 360px` MemoryDetail panel still causes content squeeze on small screens. Graph view is unusable on touch devices. The header toolbar with 15+ interactive elements overflows below ~1200px with no responsive wrapping or hamburger menu.

**Gap severity:** Medium (upgraded from Low in R15). The competitive landscape's mobile investment (especially Notion's mobile AI Agents) makes this more salient. CodeMemory's current target audience (developers + AI Agents) predominantly uses desktop, but mobile capture is becoming table stakes.

### G5: Multi-User / Collaboration -- NICE-TO-HAVE (unchanged)

**Competitor standard:** Notion offers real-time collaboration, comments, and permission management. Obsidian supports up to 10 users via Sync but lacks real-time collaboration.

**CodeMemory state:** Pure single-user. File-system locks create race conditions on concurrent writes. The product's "personal second brain + AI Agent brain" positioning doesn't require collaboration, but future team knowledge base positioning would.

---

## Phase 3: Feature Depth

> Are existing features just "skin-deep"?

### D1: Create/Edit Form -- IMPROVED but still SHALLOW

**Completed (R15):** Slide-out panel form, supports id/summary/tags/intensity/body/maturity/status/imports/changenote fields. Template selector. Tag autocomplete. Import strength selector. Unsaved changes warning. Exit animations.

**Completed (R16):** None — MemoryForm was not enhanced in R16.

**Missing:**
- **Markdown preview:** body field is a plain textarea; no rendered preview visible during editing. User must save, close panel, then open MemoryDetail to see rendered output.
- **Auto-summary:** No "generate summary from body" button (G2).
- **Import suggestion integration:** imports field is fully manual (C2).
- **Version history preview:** changelog data exists but is not integrated into the edit flow — user cannot see previous versions before editing.
- **AI assistance of any kind:** No LLM-powered auto-complete, suggestion, or summarization (G2).

### D2: Graph View -- ADEQUATE

**Completed (R15):** Cytoscape graph rendering. Node styling based on type/intensity/maturity. Edge differentiation by strength. Right-click context menu (Edit/Delete/Resolve with keyboard shortcut hints in R16-P3). Node click opens MemoryDetail. Zoom controls. Layout switching. Directory-based color grouping. Legend dynamically derived from actual graph data.

**Missing:**
- **Graph-search linking:** Search-matched nodes are not highlighted in the graph view — search results and graph view are two disconnected spaces.
- **Graph walk mode:** Interactive graph exploration mode was deferred.
- **Time view:** No time dimension for the memory graph.
- **Legend click-to-highlight:** Clicking a directory in the legend does not highlight those nodes on the canvas.

### D3: Resolve Panel -- DEEP

**Completed (R15):** Resolve button triggers DAG assembly. Skeleton loading screen. Node tree display (FULL/SUMMARY/SKIPPED with color coding). Error feedback. Stale/Pin notices. Budget/depth controls.

**Remains a killer feature:** The `buildPromptContent()` function generates prompts containing complete maturity weighting guidance (proven > verified > draft), status awareness (active > archived), and node index ordering. This is an **under-recognized killer feature** — directly converting DAG resolution results into LLM-usable structured context. R16's `propose_memory` MCP tool makes this even more powerful: Agents can now resolve context, reason, and write results back.

**Missing:** An "Export as Context" one-click LLM prompt injection button that formats Resolve output for direct system-prompt insertion (Proposal 5 from Product Audit).

### D4: Dashboard -- ADEQUATE

**Completed (R15):** Stats cards (total/stale/proven). Maturity distribution. Tag frequency cloud. Stale memory list. Wander button. Validate button. Reindex button. Decay risk display. Exit animations for modals.

**Completed (R16):** Stability source tracking, stale-detection-triggered stability downgrade.

**Missing:**
- **Trend view:** Dashboard only shows current snapshot, no timeline — cannot see "how many memories were created in the past 30 days" or "stability change trends."
- **Sortable decay risk list:** Decay risk list shows 3-5 high-risk memories but lacks full sortable list.
- **Review queue:** Passive warnings (decay risk) exist, but active review mechanism is missing.
- **Stale IDs not clickable:** Dashboard stale memory list shows plain-text IDs rather than clickable links to MemoryDetail.
- **Dependency Health Score:** Memories with high dependents count are "load-bearing" but this structural importance is not surfaced.

### D5: Search -- SIGNIFICANTLY IMPROVED (R16-C1)

**Completed (R15):** SearchBar supports substring + fuzzy matching. Tag/type/status/maturity filtering. Search results display snippet + match_quality indicator.

**Completed (R16-C1, S2):** Full-text body search. Match snippets with `<mark>` highlighting. Access freshness display on search results (days since last access + R-probability with three-color signal). Resolve quick-action tooltip (R16-P2).

**Missing:**
- **Search result clustering:** All results displayed as flat list; no grouping by tag/directory/maturity.
- **Search history / saved searches:** No search history; cannot save frequent searches.
- **Graph view linking:** Search results do not highlight corresponding nodes in graph view.
- **Exact vs fuzzy visual separation:** Search results show match quality but do not visually group exact matches separately from fuzzy matches.

### D6: MemoryDetail -- ENRICHED (R16-C2, F4, S1)

**Completed (R15):** Slide-in panel with full detail, backlinks, and body rendering.

**Completed (R16):**
- **Stability slider:** Per-memory stability slider (range 1-365, step 1), with `stability_source: "manual"` tracking.
- **R-probability signal coloring:** Green (>50%), amber (10-50%), red (<10%) three-color display.
- **Touch button:** Lightweight decay refresh with ~600ms checkmark animation.

**Missing:** Limited export/copy options from detail view. No "share this memory" or "copy as markdown" button.

---

## Phase 4: Differentiation and Wow Factor

> What features could make this product uniquely dominant in the market?

### Core Differentiator: DAG Dependency Resolution + Token Budget Constraints -- MARKET-UNIQUE (strengthened by R16)

CodeMemory's strongest strategic weapon remains unchallenged. In 2026, almost all AI memory tools rely on vector similarity search. CodeMemory takes a fundamentally different approach: **memory loading is a compilation problem, not a search problem.**

**R16 strengthened this in three ways:**
1. **Full-text search as complement, not replacement:** Full-text search (C1) serves as the "escape hatch" when DAG navigation fails, without compromising the DAG-first philosophy.
2. **Writable MCP tools close the agentic loop:** Agents can now both read (resolve/overview/wander/focus) and write (propose_memory/propose_update) — making CodeMemory a true bidirectional external brain.
3. **Per-memory stability control (C2) + Touch (S1):** Decay is no longer a black-box automatic process. Users have granular control over individual memory half-lives.

**But the competition is accelerating:**
- **HGP** (History Graph Protocol) is adding evidence trails (support/refute relationships) and CRDT synchronization.
- **LCM** (Lossless Context Management) is developing structured DAG approaches from the research side.
- **Obsidian** with CLI + Agent Skills is becoming machine-addressable, competing on the "Agent-accessible memory" axis.

### Differentiation Deepening Directions

#### DF1: Semantic Edges -- Differentiation Strengthener (unchanged from R15)

**Current state:** imports distinguish `required | recommended | related` strength levels, but don't express semantic relationships.

**Differentiation opportunity:** Extend edge schema with `semantic_type` field:
- `supports` -- Memory A supports Memory B's conclusion
- `contradicts` -- Memory A contradicts Memory B
- `extends` -- Memory A extends/deepens Memory B
- `prerequisite` -- Must understand A before B

**Wow factor:** When Resolve assembles context, semantic edges translate into LLM instructions: "Memory A supports Memory B's core hypothesis; Memory C contradicts Memory B's data source." This carries orders of magnitude more information than "Memory A recommended Memory B."

**Competitive urgency:** Elevated. HGP is already implementing evidence trails. The window for CodeMemory to claim "semantic graph memory" as a differentiator is narrowing.

**Estimated effort:** ~5 days

#### DF2: DAG-Aware AI Editing Sidebar -- Killer Differentiator (unchanged from R15)

**Current state:** MemoryForm is a purely manual form. No AI assistance of any kind.

**Differentiation opportunity:** When the user edits Markdown in the MemoryForm body field, a sidebar or inline suggestion panel displays in real-time:
1. **Dependency graph preview** -- the current memory's position in the DAG
2. **Conflict detection** -- "You're editing a memory about X, but Memory Y's conclusion conflicts with your current edit"
3. **Context completion** -- "Based on your DAG, you may need to reference Memory Z"

This has no competitor in the current market. It leverages CodeMemory's unique deterministic DAG advantage to provide a structured editing experience that neither Notion AI nor Mem.ai can offer.

**Estimated effort:** ~8 days

#### DF3: "Since You Last Visited" Context Injection -- Experience Differentiator (unchanged)

**Current state:** Dashboard displays decay risk but doesn't convert it into consumable context.

**Differentiation opportunity:** Implement a "Since You Last Visited" summary — whenever the user opens Dashboard or an Agent starts a new session, automatically display:
- Memories created since last visit
- Top 3 memories at highest decay risk (suggested review)
- Updated/obsoleted memories (stale)

This aligns with Mem.ai's "proactive note suggestions" philosophy, but driven by DAG topology (not semantic similarity), displaying **structured cognitive gaps** rather than probabilistic associations.

**Estimated effort:** ~2 days

#### DF4: Memory Health Score + Contribution Heatmap -- Experience Differentiator (unchanged)

**Current state:** Decay risk displays retrieval probability, but not a composite health score.

**Differentiation opportunity:** Calculate a composite "health score" per memory: combining staleness status, maturity level, decay risk, access frequency, and dependency count. Dashboard top section displays "Memory Library Health Overview" — similar to GitHub's contribution heatmap.

**Estimated effort:** ~3 days

#### DF5: Export-as-Context -- One-Click Agent Injection

**Current state:** The Resolve feature produces token-budgeted, topologically-sorted markdown output. But there's no one-click mechanism to format this for LLM system prompt injection.

**Differentiation opportunity:** A "Copy as Context" button in the Resolve panel formats output for direct injection into LLM system prompts, wrapped in `<codememory_context>` tags, with maturity weighting guidance and status awareness.

**Estimated effort:** ~1 day

---

## Technical Health (Incidental Scan)

> Brief scan — not a full audit, but attention to "which technical issues become bottlenecks as features pile up."

### TH1: God Objects -- PARTIALLY RESOLVED

| File | R15 Lines | R16 Lines | Status |
|------|-----------|-----------|--------|
| `backend/server.py` | 1419 | 142 | RESOLVED (R16-A1): Split into 3 APIRouters + shared.py |
| `backend/routers/memories.py` | — | 463 | New: Memory CRUD + Import + Export + Touch |
| `backend/routers/search.py` | — | 353 | New: Graph + Resolve + Search |
| `backend/routers/stats.py` | — | 153 | New: Stats + Wander + Validate + Reindex + Datasets |
| `backend/shared.py` | — | 311 | New: Shared helpers, Pydantic models, configuration |
| `frontend/src/App.tsx` | 1655 | 1667 | UNCHANGED: Still hosts state management, theming, shortcuts, global error handling |

**Impact:** Backend merge conflict risk is significantly reduced. App.tsx remains a bottleneck. At 1667 lines with state management, theme handling, keyboard shortcuts, and global error handling, it will become a merge conflict hotspot if the frontend team expands beyond 1-2 developers.

**Recommendation:**
- Backend: Done. No further action needed at current scale.
- Frontend: Introduce state management (Zustand or Context API) to separate App.tsx state noise.

**Estimated effort:** ~2 days (frontend only)

### TH2: File-Based Index Bottleneck -- IMPORTANT (unchanged)

**Current state:** index.json file-based reads/writes. Each write triggers full/partial rebuild; current baseline ~200ms at <200 nodes is acceptable. Search reads all `.md` body files per query — with full-text search enabled (R16-C1), this is now a per-file read operation, not just index iteration.

**Bottleneck prediction:** At >1000 nodes, concurrent read/write lock contention becomes a performance bottleneck. The search endpoint — which now iterates all memories AND reads body files per query — becomes a multi-second operation at 1000+ nodes.

**Recommendation:** Before crossing 500 nodes, consider introducing SQLite as an index backend (preserve .md files as source data; index.json -> index.db as search cache with body full-text indexing).

**Estimated effort:** ~4 days

### TH3: CSS Architecture -- NICE-TO-HAVE (unchanged)

**Current state:** Heavy reliance on inline styles; approximately 70% of the 6,045+ lines of component code is CSS. No CSS modules, TailwindCSS, or styled-components.

**Impact:** As dark mode/theme system complexity increases, maintenance costs grow linearly. At the current scale (12 components), this is not an urgent issue.

**Estimated effort:** ~3 days (incremental migration)

### TH4: Test Coverage -- HEALTHY (strengthened in R16)

**Current state:** 57 unit tests + 24 integration tests + 5 API tests + 5 Playwright smoke tests = 91 total tests, 100% passing. R16 verified zero regressions across all 91 tests. For a high-velocity project, this regression safety net is rare and reassuring.

**R16 additions:** Playwright path resolution fix (F3) ensures tests run from both project root and `frontend/` directory. The `test:e2e:root` script was added to package.json.

**What's missing:** No frontend component-level tests (Playwright smoke tests are integration-level). Component tests (React Testing Library) would catch regression categories like "component renders with 0 interactive elements."

**Estimated effort:** ~2 days

### TH5: Dataset Default Regression -- NEW (discovered post-R16-A1)

**Current state:** The APIRouter split (R16-A1) introduced a self-reinforcing dataset default regression:
1. Frontend `api.ts` hardcodes `_currentDataset = 'companion'`
2. Backend middleware sets ContextVar from the request header even for exempt paths like `/api/datasets`
3. The `/api/datasets` handler reads the (now-contaminated) ContextVar for the `current` field

**User impact:** Every browser session initializes to the companion dataset (11 personal-life memories, 82% stale, few dependencies) instead of the server-configured default of investment (10 structured financial-decision memories with 12 edges). The server's `DEFAULT_DATASET` environment variable is completely ignored for browser clients.

**Recommendation:** Two-part fix:
1. Backend middleware: skip ContextVar setting for exempt paths
2. Frontend: initialize `_currentDataset` to empty string, let server response set the value

**Estimated effort:** ~30 minutes

---

## Prioritized Recommendations

### CRITICAL (product cannot enter next phase without these)

| # | Recommendation | Effort | Phase | R16 Status |
|---|---------------|--------|-------|------------|
| C1 | **Bulk Import Pipeline (Web UI)** : drag-drop Markdown import + preview confirmation + auto dependency inference | ~3 days | 1, 2 | Deferred to future Sprint |
| C2 | **MemoryForm Imports Autocomplete** : suggest_deps integration into MemoryForm | ~1 day | 1 | Deferred to future Sprint |
| C3 | **AI-Assisted Creation** : LLM Gateway integration into MemoryForm (auto-summary/tags/related recommendations) | ~2 days | 2 | Deferred to future Sprint |
| CR1 | **Fix Dataset Default Regression** : two-part backend middleware + frontend initialization fix | ~30 min | TH | New post-R16 discovery |

### IMPORTANT (impacts product competitiveness and user experience)

| # | Recommendation | Effort | Phase |
|---|---------------|--------|-------|
| I1 | **Review Queue** : from passive decay warnings to active flashcard-style review mechanism | ~1.5 days | 3 |
| I2 | **Graph-Search Linking** : search results highlight corresponding nodes in graph view | ~0.5 day | 3 |
| I3 | **Markdown Preview** : body rendering preview in MemoryForm | ~0.5 day | 3 |
| I4 | **"Proposed" Review Queue in Web UI** : human review interface for MCP-proposed memories | ~1 day | 1 |
| I5 | **App.tsx State Management** : Zustand or Context API to separate state from App.tsx | ~2 days | TH |
| I6 | **Dashboard Stale IDs Clickable** : make stale memory list entries navigate to MemoryDetail | ~15 min | 3 |
| I7 | **Legend Click-to-Highlight** : clicking directory in legend highlights those nodes on canvas | ~30 min | 3 |
| I8 | **Export-as-Context Button** : one-click LLM system prompt injection from Resolve output | ~1 day | 4 |

### NICE-TO-HAVE (completes the experience, can be deferred)

| # | Recommendation | Effort | Phase |
|---|---------------|--------|-------|
| N1 | **Dashboard Trend View** : timeline charts (creation trends / decay trends) | ~2 days | 3 |
| N2 | **CSS Modernization** : TailwindCSS or CSS modules migration (incremental) | ~3 days | TH |
| N3 | **Frontend Component Tests** : React Testing Library coverage for key components | ~2 days | TH |
| N4 | **Responsive Degradation** : small-screen / touch device adaptation | ~3 days | 2 |
| N5 | **Search History + Saved Searches** | ~0.5 day | 3 |
| N6 | **Time-Dimension Graph View** : color by creation time clustering | ~1 day | 3 |
| N7 | **Search Result Clustering** : group results by tag/directory/maturity | ~1 day | 3 |
| N8 | **Graph Node Tooltip Enrichment** : add R-probability and dependent count to hover tooltip | ~20 min | 3 |
| N9 | **Companion Dataset Dependency Enrichment** : add explicit imports to demonstrate DAG capability | ~30 min | 3 |

### FEATURE IDEAS (long-term differentiation strategic assets)

| # | Recommendation | Effort | Phase |
|---|---------------|--------|-------|
| F1 | **Semantic Edges** : extend imports schema, add `supports/contradicts/extends/prerequisite` semantic types | ~5 days | 4 |
| F2 | **DAG-Aware AI Editing Sidebar** : real-time related memory display, conflict detection, context completion during editing | ~8 days | 4 |
| F3 | **"Since You Last Visited" Context Summary** : auto-inject change summary on session start | ~2 days | 4 |
| F4 | **Memory Health Score + Contribution Heatmap** | ~3 days | 4 |
| F5 | **Hybrid Search** : optional vector embeddings + DAG resolution dual-path retrieval | ~5 days | 3, 4 |
| F6 | **SQLite Index Backend** : replace file-based index, break through 1000+ node bottleneck | ~4 days | TH |
| F7 | **Memory Branching / Merge** : Git-style branch management for experimental memory topology modifications | ~10 days | 4 |
| F8 | **Cross-Dataset Resolve** : DAG resolution across multiple datasets with shared index | ~3-4 days | 4 |

---

## Six-Month Strategic Roadmap (Updated for R16)

### Completed: Product-Loop Investment Cycle (Rounds 12-16)
- Correct decay model (adaptive stability, long-term retention floor, domain-differentiated defaults)
- Full-text body search with highlighted snippets
- Per-memory stability UI slider with manual/auto tracking
- Touch endpoint for lightweight decay refresh
- Writable MCP tools (propose_memory, propose_update)
- APIRouter backend split (1419 -> 142 line server.py)
- 91/91 tests passing, zero regressions

### Sprint 17: Break the Cold Start (The Input Problem) — ~7 days
- **Day 1-2:** Fix dataset default regression (CR1) + Dashboard stale IDs clickable (I6)
- **Day 3-5:** Bulk import pipeline (drag-drop Markdown -> preview -> batch create -> auto trigger suggest-deps) (C1)
- **Day 6-7:** MemoryForm imports autocomplete (suggest_deps integration) (C2) + Markdown preview (I3)

### Sprint 18: AI Copilot and Interaction Deepening — ~7 days
- **Day 1-3:** AI-assisted creation (LLM Gateway integration into MemoryForm) (C3)
- **Day 4-5:** "Proposed" review queue in Web UI (I4) + Export-as-Context button (I8)
- **Day 6-7:** Review queue (I1) + Graph-search linking (I2)

### Sprint 19: Semantic Leap — ~7 days
- **Day 1-5:** Semantic edges (schema extension + resolve prompt generation + frontend UI) (F1)
- **Day 6-7:** "Since You Last Visited" context injection (F3) + Memory Health Score (F4)

### Sprint 20: Architecture Hardening — ~7 days
- **Day 1-2:** App.tsx state management refactor (I5)
- **Day 3-4:** CSS modernization increment (N2) + component tests (N3)
- **Day 5-7:** SQLite index backend POC (F6) + responsive degradation start (N4)

---

## Round 16 Delta: What Changed Since Last Audit

| Item | R15 Status | R16 Status |
|------|-----------|------------|
| Full-text body search (C4) | MISSING — #1 feature gap | DELIVERED (R16-C1) |
| Writable MCP tools (C3) | MISSING — 4/5 readOnly | DELIVERED (R16-M1) — 7 tools, 2 writable |
| APIRouter backend split (I3/TH1) | server.py 1419 lines | DELIVERED (R16-A1) — server.py 142 lines + 3 routers |
| Per-memory stability UI (DF4) | MISSING — backend only | DELIVERED (R16-C2) — slider + manual tracking |
| Touch endpoint (S1) | MISSING | DELIVERED (R16-S1) — lightweight decay refresh |
| Search result freshness (S2) | MISSING | DELIVERED (R16-S2) — R-probability on results |
| List health column (S3) | MISSING | DELIVERED (R16-S3) — sortable R-probability bar |
| R-probability signal coloring (F4) | MISSING — raw number | DELIVERED (R16-F4) — green/amber/red |
| Stale-check stability downgrade (F5) | MISSING | DELIVERED (R16-F5) — feedback loop closed |
| Wander mode toggle removal (P1) | PRESENT | REMOVED (R16-P1) |
| Resolve tooltip (P2) | MISSING | DELIVERED (R16-P2) |
| Context menu shortcuts (P3) | MISSING | DELIVERED (R16-P3) |
| Endpoint decay field gap (F1) | BUG | FIXED (R16-F1) |
| Badges comment (F2) | BUG | FIXED (R16-F2) |
| Playwright path (F3) | BUG | FIXED (R16-F3) |
| Dataset default regression | N/A (pre-APIRouter) | NEW BUG — self-reinforcing ContextVar contamination |
| Import UI | MISSING | STILL MISSING (deferred) |
| AI-assisted creation | MISSING | STILL MISSING (deferred) |
| Semantic edges | MISSING | STILL MISSING (deferred) |
| App.tsx god object | 1655 lines | 1667 lines (unchanged structure) |

---

## Bottom Line

**CodeMemory has completed its Product-Loop investment cycle with 16/16 R16 tasks delivered, zero regressions across 91 tests, and a clean backend architecture. The deterministic DAG memory protocol is now backed by full-text search, writable MCP tools, and user-controllable per-memory decay — a feature set with no direct equivalent in the competitive landscape.**

**The next phase must pivot from engine completion to user activation.** The two remaining structural fractures — no import UI and no AI-assisted creation — are not implementation challenges; they are prioritization choices that were explicitly deferred in R16's negotiation. Both have the backend infrastructure ready (import API endpoint, suggest_deps.py, llm_gateway package). What's missing is the frontend wiring and product design decisions.

The strategic window remains open but is narrowing. Obsidian's CLI + Agent Skills (Kepano, Jan 2026) and Notion's AI Agents (3.2, Feb 2026) represent accelerating competitive pressure on the "Agent-accessible knowledge system" positioning that CodeMemory has pioneered. The next Sprint should open with the Input Problem — because a brilliant engine without intake valves remains a museum piece.

---

*End of report.*
