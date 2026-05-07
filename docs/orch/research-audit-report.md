# CodeMemory -- Product Research Audit Report (Sprint 13)

**Date:** 2026-05-07
**Reviewer:** Product Research Reviewer
**Build:** Post-Round 11 (7e1f84b), Sprint 13
**Methodology:** Full source code audit (16 modules), CLI hands-on testing (reindex / validate / resolve / overview / wander), adjacent domain research (knowledge graph storage patterns, ACT-R/SOAR cognitive architecture, Obsidian/Roam/Tana note-taking linking models, Git Merkle DAG, spaced repetition / forgetting curve algorithms, 2025 Agent memory management), competitive design philosophy analysis

---

## Executive Summary

### Current Design's Core Assumptions

CodeMemory rests on 5 interlocking assumptions, each of which represents a deliberate design bet:

1. **"Memory = Markdown file"** — Every memory unit is a physical `.md` file. The filesystem is the database. Dependencies are declared in YAML frontmatter. This buys portability, Git-friendliness, and human-editable transparency at the cost of fine-grained granularity (no block-level references) and O(n^2) graph operations.

2. **"Memory loading = deterministic DAG resolution, not probabilistic search"** — Explicit `imports` replace semantic similarity as the retrieval mechanism. This guarantees causal completeness for domains where it matters (investment decisions, legal reasoning, medical analysis), but creates a coverage gap for associative discovery.

3. **"Forgetting = path unreachability from the dependency graph"** — No deletion, no auto-archiving. A memory is "forgotten" when nothing imports it. This is philosophically elegant but operationally incomplete: it conflates deliberate forgetting with accidental isolation, and provides no proactive mechanism for memory hygiene.

4. **"The memory space is small to medium (10-100 units)"** — Algorithms assume O(n^2) is acceptable. `_count_dependents` scans all memories per memory in search/overview/validate. `build_dag` BFS's the entire dependency subgraph per validation check. At 10000 memories, these patterns break.

5. **"The Agent sees bash, not Python"** — The agent interface is CLI subcommands, not importable libraries. The implementation language is transparent to the user. This is a constraint, not a limitation — but it shapes what operations are ergonomic for an agent to perform.

### Biggest Research Finding: Which Dimension?

The most fruitful research findings are in **adjacent domain pattern transfer**. Specifically:

- **Cognitive architecture** (ACT-R/SOAR) provides a rigorous, experimentally validated framework for memory activation and decay that maps almost perfectly onto CodeMemory's existing data (access_count, last_access, dependents)
- **Note-taking tools** (Roam/Tana) demonstrate that **typed relationships** and **block-level granularity** are the natural next evolutionary step beyond file-level bidirectional links — and CodeMemory's schema/imports system is ideally positioned to absorb these patterns
- **Agent memory research** (SAGE, HAMR, GAM, MemAgent) confirms that **hierarchical memory with time-decayed activation** outperforms both flat-context and pure-RAG approaches by 2-4x — validating CodeMemory's structural approach while suggesting a more dynamic activation model
- **Git's Merkle DAG** provides a battle-tested model for content-addressed identity, structural sharing, branching, and immutable history — all of which map onto unsolved problems in CodeMemory's version model

### One Sentence: The Most Valuable Breakthrough Direction

**Elevate edges from a node attribute to a first-class entity; replace static heat with time-decayed activation; and adopt content-addressed identity as the foundation for trustworthy, scalable memory resolution.**

This is not a single change — it is three mutually reinforcing design shifts that together transform the system from a file-based dependency graph into a content-addressed, temporally-aware knowledge network. Each shift has a clear migration path that doesn't break backward compatibility.

---

## Phase 1: Core Assumption Questioning

### 1.1 Complete Assumption Inventory

The following is the full inventory of implicit assumptions discovered through source code analysis, CLI testing, and conceptual modeling. Each assumption is rated on how challengable it is and what the impact would be if it were revised.

| # | Assumption | Where It Manifests | Challengeability | Impact If Revised |
|---|-----------|-------------------|------------------|-------------------|
| 1 | Memory is indivisible (one file = one unit) | Entire data model; `parse_frontmatter` assumes one YAML block per file | **High** — Roam's block model and Obsidian's heading anchors prove finer granularity is valuable | resolve would need to track which sections of a file are imported, not just which files |
| 2 | Dependency edges are node attributes (imports stored in frontmatter) | `_get_imports()`, `_count_dependents()`, all graph construction | **High** — Edge-first models (Tana, knowledge graphs) enable O(1) reverse query and richer edge metadata | The entire DAG construction pipeline flips from node-scan to edge-lookup |
| 3 | Three import strengths (required/recommended/related) cover all relationship semantics | `resolve.py` token trimming, `suggest_deps.py` scoring, `validate.py` cycle detection | **Medium-High** — Tana Supertags demonstrate typed relationships (supports/contradicts/extends) add significant value | resolve output gains semantic grouping; suggest-deps becomes more precise |
| 4 | Memory IDs are human-readable paths (user/investment/context) | `create.py`, `get_memory_path()`, all import references | **High** — Content-addressed IDs (Git, IPFS) provide tamper-evidence, dedup, and structural sharing | References become cryptographically verifiable; ID assignment changes from human choice to content hash |
| 5 | Heat/importance is static (dependents * 10 + access_count) | `handle_overview()` | **Medium** — ACT-R's time-decayed activation is experimentally validated and uses data already collected (access_count, last_access) | overview ranking becomes recency-aware; cold memories naturally fade without structural changes |
| 6 | Memory set size is 10-100 | All O(n^2) algorithms: `_count_dependents` in 3+ locations, per-memory BFS in validate | **High** — Cold-start import can produce 1000+ memories instantly | Requires precomputed in-degree/out-degree in index; otherwise core operations become unusable |
| 7 | Token budget = raw character count | `estimate_tokens()` returns `len(text)` | **Low** — Well-known approximation; actual tokenization varies by model | Improved budget control accuracy but doesn't change architecture |
| 8 | Three maturity levels (draft/verified/proven) are sufficient | `resolve.py` maturity auto-upgrade; `validate.py` maturity staleness check | **Medium** — Missing "contested/disputed" and "superseded-by" states | Maturity state machine would need to support non-monotonic transitions and cross-reference |
| 9 | Tags serve triple duty (domain, semantic type, filter target) | `search.py` semantic_type filter; `resolve.py` focus filter; `suggest_deps.py` tag overlap | **Medium** — Semantic conflation creates ambiguity; "decision" can be both a domain tag and a semantic role | Tags would need namespacing or a separate `semantic_role` field |
| 10 | Protection is derived from intensity (>= 8) | `reindex()` sets `protected` based on `intensity`; `validate.py` decay exempts intensity >= 8 | **Low-Medium** — The derivation is arbitrary; explicit protection would be more intentional | Protection becomes an explicit user choice; decay eligibility is independently determined |
| 11 | Forgotten = isolated (no imports pointing to this memory) | `orphans.py` defines orphan as in-degree 0 | **Medium** — Deliberate forgetting vs accidental isolation are indistinguishable | Would need an explicit "forget" or "archive" operation; orphan detection becomes about accidental isolation only |
| 12 | The user/Agent will manually maintain imports | All CRUD operations; `suggest_deps` is a separate suggestion tool | **Medium** — Human-maintained link graphs degrade over time (link rot, missing connections) | Would need automated link maintenance, link suggestions on create, or query-based dynamic imports |

### 1.2 Deep Dive: Three Critical Assumptions

#### Assumption #1: "Memory = Markdown File" — The Indivisibility Problem

This is the deepest assumption in the system, and it creates friction in three distinct scenarios:

**Scenario A: Partial imports.** In the investment dataset, `user/investment/context` imports `user/investment/risk-tolerance`. But context only needs the *constraints* section of risk-tolerance — the historical changes section is noise. There is no way to declare "I need only section X of file Y." Everything is all-or-nothing.

Roam Research solved this with block-level addressing (every paragraph has a unique ID). Obsidian solved it with heading anchors (`[[file#heading]]`). CodeMemory has no mechanism for intra-file dependency granularity.

**Implication if revised:** Introduce section-level anchors (`#section-name`) in import references. A memory's body sections can be individually addressed. This doesn't require splitting files into blocks — it's a lightweight annotation layer. The `parse_frontmatter` function would gain a `parse_sections()` companion that splits body by headings and assigns section-level IDs. Resolve would load only referenced sections when a section-specific import is declared.

**Cost of revision:** Low to medium. File format unchanged. ImportRef model gains an optional `section` field. Resolve output becomes more token-efficient by design. Migration: backward compatible — old imports (no section) continue to load full body.

#### Assumption #5: "Heat Is Static" — The Recency Blindness Problem

The current heat formula `heat = dependents * 10 + access_count` treats all accesses equally. A memory accessed 100 times six months ago has higher heat than one accessed 5 times yesterday. This is temporally blind.

ACT-R's base-level activation formula is:

```
A_i = ln( sum( t_j ^ -d ) )
```

Where `t_j` is the time since the j-th access (in some unit) and `d` is the decay rate (typically 0.5). This means:
- Recent accesses dominate the sum
- Old accesses decay asymptotically
- The natural log compresses the range, preventing extreme values

The 2025 SAGE paper demonstrated that this exact activation model, applied to agent memory, produces a 2.26x performance improvement over flat-context approaches. The data CodeMemory already collects — `access_count` and `last_access` — is the minimum needed. Adding an `access_history` list (timestamp per access) would enable full ACT-R computation.

**Implication if revised:** `overview` output becomes recency-weighted automatically. Cold memories (not accessed in months) fall to the bottom without being structurally orphaned. Wander's cool mode becomes more precise — it can target memories approaching the "retrieval threshold" (activation < theta) rather than randomly sampling low-access memories.

**Cost of revision:** Low. The formula change is ~15 lines in `handle_overview`. Adding `access_history` is optional for full ACT-R; the current two-field model supports a reasonable approximation.

#### Assumption #12: "Users Will Manually Maintain Imports" — The Link Rot Problem

Every bidirectional linking system (Roam, Obsidian, Logseq) eventually faces link rot — connections that should exist but don't, and connections that exist but are no longer relevant. CodeMemory's approach is to make link creation deliberate and link maintenance manual.

But there is a structural asymmetry: creating a connection requires explicit human action, but *maintaining* that connection over time (updating when dependencies change, removing when dependencies become irrelevant) has no forcing function. The `suggest-deps` command helps with *missing* links but not with *stale* links.

**Implication if revised:** A `link-health` command that scans all imports and reports:
1. **Dead links** — imports pointing to non-existent memories (already in validate)
2. **Version-skewed links** — imports with pins behind the current version (already in resolve notices)
3. **Unreciprocated links** — A imports B, but B's tags/body show no relationship to A (new)
4. **Orphaned-by-oversight** — high-intensity memories with zero imports (already in orphans, but with no suggested fix)
5. **Circular-opportunity links** — two memories with high tag overlap but no imports between them (suggest-deps already does this)

**Cost of revision:** Low. Most of the detection logic already exists in validate/resolve/orphans/suggest-deps. Consolidating it into a unified `link-health` report is ~50 lines in a new handler.

### 1.3 Where the Metaphor Strains

**"Forgetting = unreachability" breaks when the user explicitly wants to forget.**

The current model says: if nothing imports X, X is forgotten. This makes forgetting an emergent property, not an intentional action. But agents sometimes need to say "I no longer believe this" or "this information is outdated and should not influence future reasoning." There is no CLI command for that. `status: archived` prevents it from appearing in overview but doesn't remove it from the DAG — if another memory still imports it, resolve loads it.

This is a philosophy gap, not a bug. The designers chose to make forgetting a structural property (unreachability) rather than an operational one (explicit forget). But the metaphor strains when:
- A belief is disproven (contradicted by new evidence)
- A fact is corrected (superseded by a more accurate version)
- A preference changes (replaced by a new value)

In these cases, the system needs a way to propagate "this memory should no longer be used" through the dependency graph — a form of **deprecation signal** — without requiring all dependent memories to update their imports.

---

## Phase 2: Adjacent Domain Research

### 2.1 Domain Scan Summary

| Domain | Core Ideas | Transferable to CodeMemory |
|--------|-----------|---------------------------|
| **Knowledge Graph Storage** (2025 survey) | Hybrid architectures dominate: Graph DB for relationships + Document DB for content + Vector DB for semantics. ISO GQL standard (2024) standardizes graph querying. GraphRAG is the #1 KG+LLM catalyst. | Precomputed in-degree index eliminates O(n^2); graph-native query language for path queries; typed edge properties with metadata |
| **Cognitive Architecture** (ACT-R / SOAR comparison, Laird 2022) | Multiple interacting memory systems (working/declarative/procedural). Activation-based retrieval with decay. Impasse-driven learning (SOAR). Spreading activation along associative edges. | ACT-R activation formula for dynamic heat; three-memory-system mapping to Layer 0; impasse detection as "missing dependency" signal |
| **Note-Taking Linking Models** (Roam / Obsidian / Tana / Logseq) | Block-level vs file-level granularity. Typed relationships (Tana Supertags). Bidirectional linking as default. Transclusion (embed, not just reference). Query-based dynamic content assembly. | Section-level imports; semantic edge types; embed/transclusion for content reuse; query blocks for dynamic imports |
| **Git Object Model** (Merkle DAG, content-addressed storage) | Content-addressed identity (SHA of content). Immutable history with structural sharing. Branching for parallel exploration. Merge for reconciliation. Cryptographic provenance. | Content-addressed memory identity; version integrity guarantees; memory branching for speculative reasoning; structural sharing of unchanged dependencies |
| **Spaced Repetition & Forgetting Curves** (FSRS, LECTOR, EDGE 2025) | Ebbinghaus forgetting curve formalized. SM-2 family algorithms. FSRS as modern open-source standard. LLM-enhanced semantic interference mitigation. Restless-bandit scheduling with optimality guarantees. | Review scheduling for memory maintenance; forgetting curve as dynamic importance; semantic interference detection between similar memories |
| **2025 Agent Memory** (SAGE, HAMR, Mem0g, MemAgent, GAM, CoA) | Hierarchical memory (STM/MTM/LTM). Graph-based relational memory. Time-decayed activation universally adopted. RL-trained memory policies. Multi-agent collaboration for context assembly. | Three-tier memory architecture; graph edges for relational reasoning; learned importance weights; collaborative context assembly patterns |

### 2.2 Five Most Transferable Patterns (Updated for Sprint 13)

These are the five patterns most worth borrowing, ranked by impact-to-effort ratio given the current codebase state:

#### Pattern 1: ACT-R Time-Decayed Activation (Cognitive Architecture)

**What it is:** Memory activation is not a static score but a function of access recency and frequency: `A = ln(sum(t_j ^ -d))`. Recent accesses matter exponentially more than old ones.

**Why it fits CodeMemory now:** The data is already collected (`access_count`, `last_access`). The current `heat = deps * 10 + access` formula is a tensor-ready placeholder. Replacing it is a formula change in one function (`handle_overview`), ~20 lines. The SAGE paper (Sept 2025) provides experimental validation: 2.26x context quality improvement with this exact model.

**Previous report status:** Proposed as R1 (High-Impact, Low-Effort). Accepted by product team, backlogged for next iteration. **Not yet implemented.** This remains the single highest-ROI design change available.

#### Pattern 2: Typed Semantic Edges (Tana Supertags + Knowledge Graph)

**What it is:** Edges carry not just strength (required/recommended/related) but semantic type (supports/contradicts/extends/replaces/exemplifies). This enables resolve output to group dependencies by their semantic role.

**Why it fits CodeMemory now:** The `imports` structure is `{strength: [refs]}`. Adding a `semantic` field to `ImportRef` is backward-compatible (default: "supports"). The resolve output can group by semantic type without changing the DAG structure. This is ~50 lines across models and handlers.

**Previous report status:** Proposed as part of "Edge Properties on Imports" (Pattern 3). Partially rejected — product team didn't see immediate value over the three-strength model. **Revisiting recommended**: the 2025 research consensus is that typed edges are the single biggest differentiator in knowledge graph quality.

#### Pattern 3: Content-Addressed Memory Identity (Git Merkle DAG)

**What it is:** Memory versions are identified by content hash, not by human-assigned version numbers. The path-based ID becomes a mutable reference (like a Git branch) pointing to the latest content hash. This enables tamper-evident citations, structural sharing between versions, and time-travel queries.

**Why it fits CodeMemory now:** `summary_hash` already exists and is computed for every memory. Extending its scope from body-only to full-content (frontmatter + body + imports structure) and using it as a content ID is conceptually straightforward. The implementation requires a `.codememory/objects/` store and reference management — significant code, but the mental model is Git-native.

**Previous report status:** Proposed as Alternative 2 (High-Impact, High-Effort). Accepted conceptually, deferred to "design document first." **No design document produced yet.** This remains the biggest architectural opportunity.

#### Pattern 4: Hierarchical Memory Tiers (SAGE/HAMR Agent Memory)

**What it is:** Memories are not in a flat index. They occupy tiers: **hot** (in current context), **warm** (high-activation, loaded on demand), **cold** (low-activation, only loaded by explicit resolve). Tiers are dynamic — a cold memory becomes warm when accessed, a warm memory cools over time.

**Why it fits CodeMemory now:** The system already has the conceptual distinction between overview (hot), resolve (warm), and wander (cold), but it's implicit. Making tiers explicit in the index enables: reindex to recalculate tier assignments; resolve to skip cold memories by default; overview to only show warm+hot. This is ~30 lines in index.py + handlers.py.

**Previous report status:** Not previously proposed as a standalone pattern. New finding from 2025 agent memory research.

#### Pattern 5: Transclusion / Content Embedding (Roam/Obsidian)

**What it is:** Beyond referencing a dependency (import), a memory can *embed* content from another memory. The embedded content is part of the importing memory's body, but traces back to its source. This enables content reuse without duplication.

**Why it fits CodeMemory now:** The current imports model only supports "I depend on X" — it doesn't support "I include content from X." A simple `embed` field alongside `imports` would enable: `embed: [{id: "user/facts/nvidia-earnings", section: "## 对市场的影响"}]`. On resolve, the embedded content is inlined into the output. This is a natural extension of the existing imports model.

**Previous report status:** Not previously proposed. Addresses the "partial dependency" problem identified in Assumption #1 analysis.

### 2.3 Competitive Design Philosophy Update

The competitive landscape has evolved since the previous research audit. Here is the updated philosophy comparison, with new entrants:

| Product | Core Metaphor | Retrieval Model | Forgetting Model | Interface Philosophy | Key Lesson for CodeMemory |
|---------|--------------|----------------|------------------|---------------------|--------------------------|
| **CodeMemory** | Memory = file; loading = compilation | DAG resolution (explicit imports) | Unreachability (advisory) | CLI for agents; Web for humans | Baseline |
| **Tana** (2025) | Memory = typed node; Supertags as schemas | Live queries over typed graph | Manual archival | Interactive graph + structured views | Typed edges > untyped links; schemas as first-class concept |
| **Mem0/Mem0g** (2025) | Memory = structured vectors + graph | Graph + embedding hybrid; multi-hop relational reasoning | Importance-weighted decay | API-first; auto-extraction | Hybrid DAG+embedding is validated; graph edges enable relational reasoning |
| **SAGE** (Sept 2025) | Memory = forgetting-curve-positioned entity | Ebbinghaus-weighted retrieval with 3-agent collaboration | Explicit forgetting curve with RL optimization | Agent collaboration protocol | Forgetting curves measurably improve context quality (2.26x) |
| **HAMR** (2025) | Memory = three-tier hierarchy (STM/MTM/LTM) | Semantic + temporal + learned-importance scoring | Simulated human consolidation | API with tier-aware routing | Explicit tiers outperform flat memory by design |
| **DiffMem** (2025) | Memory = Git-tracked markdown | Git log/blame + BM25 | History-preserving (no deletion) | Writer Agent auto-commits | Git-native version model; store "now" in files, history in Git |

**The convergence signal is unmistakable:** Every new system in this space is converging on a similar architecture: **explicit graph edges + time-decayed activation + tiered storage + hybrid deterministic/probabilistic retrieval**. CodeMemory is architecturally closer to this ideal than most — it has the DAG, the import edges, and the access tracking. What it needs is: (a) typed edges, (b) time-decayed activation, (c) explicit tiers.

---

## Phase 3: Logical Completeness

### 3.1 Concept System Assessment (Updated)

```
MemoryEntry
  ├── Identity
  │   ├── id: str              (human-readable path)
  │   ├── path: str             (filesystem location)
  │   └── summary_hash: str     (body integrity — but not used as identity)
  │
  ├── Classification
  │   ├── type: atom|schema     (structural role)
  │   ├── tags: [str]           (domain + semantic role + lifecycle — triple duty)
  │   ├── schema: str?          (structural template reference)
  │   └── status: active|archived|superseded|draft
  │
  ├── Knowledge Quality
  │   ├── intensity: 1..10      (subjective importance — static)
  │   ├── maturity: draft|verified|proven|superseded  (epistemic confidence)
  │   ├── protected: bool?      (derived from intensity >= 8)
  │   └── evidence: dict?       (provenance data — underused)
  │
  ├── Versioning
  │   ├── version: int          (linear, non-branching)
  │   ├── created/updated: str  (timestamps)
  │   ├── change_note: str?     (last change description)
  │   └── change_log: [dict]    (linear history — no diff)
  │
  ├── Structure
  │   ├── imports: {required, recommended, related}  (node-attached edges, untyped)
  │   ├── source: dict?         (external origin metadata)
  │   └── summary + body        (text content — indivisible)
  │
  └── Dynamics
      ├── access_count: int     (total accesses)
      └── last_access: str?     (timestamp of last access only — no history)
```

**Fuzzy boundaries (new and persistent):**

1. **tags triple-duty** (persistent from previous audit) — The `search --semantic-type` filter treats tags as semantic roles. The `focus` filter treats tags as domain classifiers. The `overview` display treats tags as organizational labels. All three uses share the same flat string array. **Suggestion:** Add an optional `semantic_role: str` field (decision, fact, observation, preference, thesis, context, template) to separate "what kind of memory is this" from "what domain does it belong to."

2. **intensity protected derivation** (persistent) — `protected = intensity >= 8` is an implicit rule with no user-facing explanation. If a user sets `intensity: 8` and later changes it to `7`, does protection drop? Only on reindex. The derivation is temporal and invisible.

3. **status.superseded vs maturity.superseded** (persistent) — Both fields have a "superseded" value but they mean different things. `status: superseded` means "don't use this memory anymore (lifecycle)." `maturity: superseded` means "this knowledge has been replaced by newer knowledge (epistemic)." The distinction is subtle and undocumented.

4. **evidence field is underused** (new) — The `evidence` dict exists in the model and has `verified_in` tracking, but it's only populated by the maturity auto-upgrade in resolve. There's no way for a user to add evidence manually, no search filter for evidenced memories, and no display of evidence in overview or focus.

5. **access tracking is minimal** (new) — Only `access_count` (a running total) and `last_access` (the most recent timestamp). No access history, no per-agent tracking, no distinction between "accessed in overview" vs "accessed in focus" vs "loaded by resolve." This limits the precision of any activation model.

### 3.2 Extreme Scenario Validation

#### Scenario 1: 5000-Memory Cold Import

A user imports a year of notes via `codememory import --file notes.txt`. The import produces 5000 memory atoms, each with auto-generated summaries, spanning diverse topics. Few imports are declared — most memories are isolated.

**Does the design hold?**
- `reindex`: O(5000) file parsing. ~2-5 seconds. **Works.**
- `validate`: 5000 * O(imports_check) + 5000 * BFS for cycle detection. BFS per memory on a mostly-flat graph = O(5000 * 1). ~10-20 seconds. **Borderline.**
- `search`: O(5000) scan + O(5000 * 5000) dependents count per result = **25M iterations. Fails.**
- `overview`: Same O(n^2) dependents count. **Fails.**
- `resolve user/some/entry`: BFS from entry over a flat graph = loads only itself. **Works.**
- `orphans`: O(5000 * avg_imports) referent collection + O(5000) filter. **Works.**
- `suggest-deps`: O(5000) tag overlap check + O(5000) schema pattern. ~1 second. **Works, and is the most useful command.**

**Diagnosis:** The cold-import scenario is the worst case because the graph is maximally flat (minimum edges / maximum nodes). The O(n^2) dependents counting in search and overview collapses. The fix — precomputed in-degree in the index — would reduce search/overview back to O(n). This has been proposed since the first research audit and remains unimplemented.

#### Scenario 2: All Memories Form a Symmetric Complete Graph

Every memory imports every other memory. n=100.

**Does the design hold?**
- `validate`: Cycle detection finds every node is in a cycle with every other node. n=100 BFS = fine. **Works, but produces 100 cycle warnings — noisy.**
- `resolve`: Builds a DAG then detects cycles and removes all nodes. Output is "[NOTICE] circular dependency involving..." with no content. **Technically correct but operationally useless.**
- `search`: Dependents count = 99 for every memory. n=100 iterations. **Works.**
- `overview`: 100 memories with heat = 99*10 + access_count. **Works but all heat scores are nearly identical.**

**Diagnosis:** This is an adversarial scenario — no real knowledge graph looks like this. But it reveals a weakness: the system treats all cycles as errors rather than distinguishing between "mutually reinforcing concepts" (intentional) and "dependency loops that prevent resolution" (bugs). A cycle severity classification (benign/mutual vs blocking/contradictory) would improve the user experience.

#### Scenario 3: All Knowledge Is Contested

Two memories make contradictory claims about the same topic, and both are imported by different downstream memories. No mechanism exists to mark this contradiction.

**Does the design hold?**
- System state: Two memories exist with contradictory content. No imports between them. Dependents of each load their respective "truth."
- `validate`: No errors. No mechanism detects semantic contradiction.
- `resolve`: Loading a dependent of A gives A's view. Loading a dependent of B gives B's view. No warning that there's a contradiction.
- `search`: Both memories appear, sorted by dependents. No "conflict" indicator.

**Diagnosis:** The system has no concept of contradiction. This is a direct consequence of the "all imports are positive dependency" model. A `contradicts` semantic edge type would solve this: resolve could include a "Contradictory Perspectives" section when a loaded context includes memories connected by contradiction edges. This is Pattern 2 from the adjacent domain research.

### 3.3 Operation Gaps (Updated)

| Desired Operation | Current Workaround | Gap Severity | New Since Previous Audit? |
|-------------------|-------------------|--------------|--------------------------|
| "Which memories depend on X?" (reverse deps) | Manual scan via `search` output | **HIGH** — O(n) scan, no dedicated command | No — previously identified |
| "What is the relationship between A and B?" (path query) | Manual resolve + inspection | **HIGH** — No graph traversal query | No |
| "Show me the shortest path from A to B in the dependency graph" | Not possible | **HIGH** — Path query is fundamental to graph UX | Yes — identified through graph view usage |
| "Mark this memory as contradicted by new evidence" | Change status to archived or superseded, add a note in body | **MEDIUM** — No contradiction primitive | Yes — identified through typed edges research |
| "Embed section X of memory Y into memory Z" | Manual copy-paste into body | **MEDIUM** — No transclusion | Yes — identified through Roam/Obsidian research |
| "What changed in my knowledge between January and March?" | Manual changelog inspection per memory | **MEDIUM** — No cross-memory temporal query | No |
| "Which memories are approaching their review threshold?" | `validate` decay warnings (coarse) | **MEDIUM** — No scheduled review queue | No |
| "Split this memory into two and update all imports" | Manual: create two new, update all referrers | **MEDIUM** — No refactoring primitive | No |
| "Branch from this memory state and explore an alternative" | Manual: copy all files, modify, resolve separately | **LOW** — No branching concept | No — previously proposed as "Inspiration Bomb #2" |
| "Find the most central/hub memories in the graph" | `overview` heat ranking (crude proxy) | **LOW** — No graph analytics | No |

### 3.4 Evolution Bottlenecks (Updated)

If the system needs to add new capabilities, where does the current code resist change?

**1. Adding a new import strength or semantic type** — The import strength enumeration ("required", "recommended", "related") is scattered across 7+ locations: `_get_imports()` in resolve.py, multiple `_count_dependents()` functions, `_compute_in_degree()` in validate.py, `_resolve_import_ids()` in handlers.py, `_build_graph()` in transient.py, `suggest_deps.py` three-layer filter, and `search.py` has_imports filter. Any new strength requires changes in all these places. **Fix:** Centralize import strength enumeration in `models.py` as an `ImportStrength` enum; all consumers reference the enum.

**2. Adding non-text memory types** — The entire pipeline is text-assumptive: `parse_frontmatter` splits on `---`, `compute_body_hash` hashes text, `estimate_tokens` counts characters. Adding image or structured data memories would require a new parsing pipeline, new hashing semantics, and new token estimation.

**3. Multi-agent writes** — The filesystem-based storage means concurrent writes create file-level race conditions. Git merge is the only conflict resolution. No CRDT, no lock service, no write-ahead log.

**4. Adding automatic import maintenance** — The system has no infrastructure for automated actions (cron-like scheduled tasks). Implementing progressive summarization, scheduled review reminders, or automatic link suggestions would require a scheduler component that doesn't exist.

---

## Phase 4: Alternative Design Proposals

### 4.1 Core Mechanism Alternatives

#### Alternative A: Query-Based Dynamic Imports (inspired by Roam `{{query}}` / Obsidian Dataview)

**Current:** imports are static, declared at creation time, and manually maintained.

**Proposed:** A memory can declare a `query` block alongside `imports`:

```yaml
query:
  context:
    - tags: [investment, thesis] AND maturity: [verified, proven]
    - tags: [investment, fact] AND created: "> 2026-01-01"
    - id: user/preferences/no-leverage
```

When resolved, the query is evaluated against the current index, and matching memories are dynamically included in the DAG. Static imports still work for fixed dependencies.

**Tradeoff analysis:**

| Dimension | Static Imports Only | Static + Query Imports |
|-----------|--------------------|-----------------------|
| Determinism | Full — same resolve always gives same DAG | Partial — query results depend on index state |
| Maintenance | Manual — imports go stale unless updated | Automatic — new memories matching query are auto-included |
| Precision | High — only what was explicitly chosen | Medium — query may over-match or under-match |
| Cold start | Works immediately (no query needed) | Queries need index to be populated |
| Implementation | Current | ~100 lines: query parser + query evaluator in resolve.py |
| When to adopt | Small, manually curated memory sets | Growing memory sets where manual import maintenance is unsustainable |

**Verdict:** Not a replacement for static imports, but a powerful complement. The determinism loss is real and must be clearly communicated. Worth implementing as an optional feature gated behind a `--dynamic` flag on resolve.

#### Alternative B: Edge-First Memory Model

**Current:** dependencies are stored as a field on each node's frontmatter. Finding reverse dependencies requires scanning all nodes.

**Proposed:** Edges are first-class entities stored independently in `.codememory/edges.json` or an edge index. Each edge has `from`, `to`, `strength`, `semantic`, `pin`, `reason`, and `created` fields. Both forward and reverse queries are O(1).

```json
{
  "edges": [
    {"id": "e1", "from": "user/investment/context", "to": "user/investment/semiconductor-thesis",
     "strength": "required", "semantic": "summarizes"},
    {"id": "e2", "from": "user/investment/february-buy", "to": "user/investment/risk-tolerance",
     "strength": "required", "semantic": "constrained-by", "pin": "v1"}
  ]
}
```

The Markdown frontmatter's `imports` field remains as the **editing interface** — human-readable and file-contained. On reindex, the YAML imports are mirrored into the edge index.

**Tradeoff analysis:**

| Dimension | Node-Attached Imports (Current) | Edge-First Model |
|-----------|-------------------------------|-----------------|
| Simplicity | High — everything in one .md file | Medium — dual storage (files + edge index) |
| Reverse query | O(n) scan | O(1) lookup |
| Edge metadata | Limited to pin/reason | Unlimited — strength score, semantic type, validation status, temporal data |
| Data purity | Single source of truth (.md file) | Dual source with sync guarantee |
| Editability | Direct YAML editing | YAML editing still works; edge index is derived |
| Implementation | Current | ~300 lines: edge index schema, sync on reindex, updated graph construction |
| When to adopt | Small scale (< 500 memories) | Any scale where reverse queries or graph analytics are needed |

**Verdict:** This is the single highest-impact architectural change available. The dual-source concern is mitigated by treating the edge index as a cache derived from frontmatter (similar to how `index.json` is already a cache derived from .md files). The sync is maintained on reindex and update.

#### Alternative C: Progressive Summarization as Forgetting (inspired by human memory consolidation)

**Current:** Forgetting is structural (unreachability). There is no graded degradation of memory fidelity.

**Proposed:** Instead of binary remember/forget, implement a graded summarization pipeline:

```
Full memory (accessed this month)
    ↓ 1 month without access
Level 1 summary (key points extracted, details preserved in source file)
    ↓ 3 months without access
Level 2 summary (one-paragraph gist, structured data only)
    ↓ 12 months without access
Level 3 summary (single sentence, tags + schema reference only)
```

The original content is never deleted. Each level is progressively shorter and cheaper to load. On access, the full version is always available (with a budget cost). This mirrors human episodic-to-semantic memory consolidation.

**Tradeoff analysis:**

| Dimension | Structural Forgetting (Current) | Progressive Summarization |
|-----------|-------------------------------|--------------------------|
| Fidelity | Binary — remembered or forgotten | Graded — varying levels of detail |
| Storage | Original only | Original + N summary levels |
| Retrieval cost | Full text or skip | Selectable resolution per memory |
| Automation | Manual (update imports) | Automatic (scheduled summarization) |
| LLM dependency | None | Requires LLM for summarization |
| Implementation | Current | ~200 lines: summarization pipeline + level tracking + LLM integration |
| When to adopt | Small memory sets or when LLM cost is a concern | Large memory sets or when memory hygiene automation is needed |

**Verdict:** A genuinely novel approach to the forgetting problem. The LLM dependency is the main barrier — it makes the system less self-contained. But the graded degradation model is cognitively more accurate than binary forgetting, and it naturally produces token-efficient context without structural orphan detection. Best implemented as an opt-in feature for large memory sets.

### 4.2 Concept Reorganization Proposal

**Reorganize imports into a typed edge model with precomputed graph properties:**

```
Edge (first-class entity, stored in edge index)
  ├── from: str              (source memory ID)
  ├── to: str                (target memory ID)
  ├── strength: required | recommended | related
  ├── semantic: supports | contradicts | extends | replaces | exemplifies | constrained-by | based-on | null
  ├── pin: str?              (pinned version)
  ├── reason: str?           (human explanation)
  ├── weight: float?         (continuous strength, computed or explicit)
  └── created: str           (when the edge was created)

MemoryEntry (simplified)
  ├── imports: {strength: [ImportRef]}  (editing interface — mirrored to Edge index)
  ├── _dependents: int       (precomputed in-degree — cached in index)
  ├── _dependencies: int     (precomputed out-degree — cached in index)
  └── activation: float      (computed from access history — cached, recalculated on reindex)
```

Key changes:
1. `imports` still lives in frontmatter — the editing experience doesn't change
2. On reindex, imports are mirrored into the edge index with computed properties
3. `_dependents` and `_dependencies` are precomputed, eliminating O(n^2) scans
4. `activation` replaces static `heat` — computed from access_count, last_access, and dependents

### 4.3 Tradeoff Matrix

| Proposal | Simplicity Impact | Power Gain | Migration Effort | Determinism Impact | When Worth It |
|----------|------------------|------------|-----------------|-------------------|---------------|
| A: Query-based dynamic imports | -1 | +2 | Low (~100 lines) | -2 (query results change over time) | When import maintenance burden exceeds determinism need |
| B: Edge-first model | -2 | +3 | High (~300 lines + migration) | 0 (edge index mirrors frontmatter) | When O(n^2) becomes a bottleneck (>500 memories) |
| C: Progressive summarization | -2 | +2 | Medium (~200 lines + LLM integration) | 0 (summaries are read-only derivatives) | When memory hygiene automation is needed |
| Pattern 1: Activation decay | 0 | +2 | Low (~20 lines) | 0 (formula is deterministic given same data) | Immediately |
| Pattern 2: Typed semantic edges | 0 | +2 | Low (~50 lines) | 0 (backward compatible) | Immediately |
| Pattern 3: Content-addressed identity | -3 | +3 | High (~500 lines) | 0 (content hash is deterministic) | When integrity guarantees matter (multi-agent, compliance) |
| Pattern 4: Hierarchical memory tiers | 0 | +1 | Low (~30 lines) | 0 (tiers are a cache) | When memory count > 200 |
| Pattern 5: Transclusion/embedding | 0 | +1 | Low (~40 lines) | 0 (opt-in) | When content reuse without duplication is needed |
| Concept reorganization (B + Patterns 1-4) | -2 | +4 | High (~500 lines) | 0 (all changes are backward compatible) | When multiple bottlenecks coincide |

### 4.4 Inspiration Bombs

#### Bomb 1: The "Memory Compiler" — Static Pre-Assembly of Context Packages

**The idea:** What if DAG resolution were a compile-time operation rather than a runtime one? Just as a C compiler transforms `.c` files into `.o` object files and a linker assembles them into an executable, a Memory Compiler could:

1. Parse all `.md` memory files into an intermediate representation (IR)
2. Pre-assemble common resolve paths into **static context packages**
3. Apply token budget constraints at compile time via dead-code elimination
4. Cache the results as `.ctx` files (binary or compressed markdown)

When an agent calls `resolve user/investment/context --budget 2000`, instead of dynamically building a DAG and trimming output, the system checks if a pre-compiled context package exists and serves it in O(1).

**Why it changes the game:** It moves CodeMemory from an **interpreted memory system** (every resolve is a fresh computation) to a **compiled memory system** (contexts are pre-computed assets). At 10000 memories, this is the difference between seconds and milliseconds. At the limit, compiled context packages could be distributed, cached at CDN edges, or embedded in agent system prompts as static assets.

**Feasibility:** The DAG structure is already deterministic given the same imports and versions. The compiler is a batch job that runs on reindex or on explicit `compile` command. This is concept-level research — no implementation exists.

#### Bomb 2: "Memory as a Story" — Narrative Coherence as an Organizing Principle

**The idea:** What if memories were organized not by topic tags or dependency graphs, but by **narrative coherence** — the degree to which they form a coherent story when resolved together?

Humans don't recall facts in isolation. We recall them as part of narratives: "I was risk-tolerant in January, then the March crash happened, so I adjusted my risk tolerance, which affected my February buy decision." This is a temporal-causal narrative, not a DAG.

The system could compute **narrative coherence scores** between memories by analyzing:
- Temporal adjacency (created/updated timestamps)
- Causal chains (A imports B, B imports C)
- Semantic continuity (tag overlap, body text similarity)
- Emotional arc (intensity changes over time — high → low or low → high)

A `narrate` command would assemble the most coherent narrative path through a set of memories, optimized for "story quality" rather than dependency closure. This is a fundamentally different retrieval objective — not "what does A depend on?" but "what story connects A, B, and C?"

**Why it changes the game:** It shifts the user's relationship to their memory from "query engine" to "story engine." Instead of thinking "I need to load the dependencies of my investment context," they think "tell me the story of my investment thinking." The output is narrative text, not a list of memory summaries. This is the difference between a file system and a biographer.

**Feasibility:** Requires LLM integration for narrative assembly and coherence scoring. The DAG structure provides the skeleton; the LLM provides the flesh. This is a "memory product" layer on top of the "memory engine."

#### Bomb 3: "Memory Spectroscopy" — Decomposing Memories by Cognitive Function

**The idea:** What if every memory were analyzed and tagged not by its topic (investment, semiconductor) but by its **cognitive function** in the reasoning process?

Inspired by Bloom's Taxonomy and the DIKW pyramid, each memory would be classified by:
- **Data** — raw observations, facts without interpretation
- **Pattern** — recognized regularities across data points
- **Model** — causal explanations linking patterns
- **Decision** — action commitments based on models
- **Reflection** — meta-cognition about the decision process

A `spectroscopy` analysis would show: "Your memory system is 60% Data, 20% Pattern, 15% Model, 5% Decision — you're collecting a lot of facts but not synthesizing them into decisions." This is a **cognitive health dashboard** for the memory system, analogous to how code quality tools report on codebase composition (test coverage, complexity distribution, dependency health).

**Why it changes the game:** It transforms the memory system from a passive store into an active cognitive coach — not just "here are your memories" but "here's how your thinking is structured, and here's where the gaps are."

**Feasibility:** The classification could be done via simple heuristics (memories with schema:decision are "Decision", memories with tags:fact are "Data", etc.) or via LLM analysis. The dashboard is a frontend visualization layer. This is achievable with ~200 lines of analysis code + a new dashboard panel.

---

## Prioritized Research Directions

### Red (High-Impact, Low-Effort) — Consider for Current/Next Sprint

**R1: Replace static `heat` with time-decayed activation in `overview`.**
- Replace `heat = deps * 10 + access` with `activation = ln(1 + sum(1 / sqrt(days_since_access + 1))) + deps * 2`
- Uses existing `access_count` and `last_access` data
- ~20 lines in `handle_overview`
- **Status from previous report:** Proposed as R1, accepted, backlogged. Not yet implemented.

**R2: Add optional `semantic` field to imports.**
- Add `semantic: str | None = None` to `ImportRef` model (supports/contradicts/extends/replaces/exemplifies)
- In resolve, group dependencies by semantic type in output
- Backward compatible — old imports are treated as `supports`
- ~50 lines across `models.py` + `resolve.py` + `handlers.py`

**R3: Precompute `in_degree` and `out_degree` in the index.**
- During reindex, compute `_dependents: int` (how many memories import this one) and `_dependencies: int` (how many memories this one imports)
- Store in `index.json` as computed fields
- Replace all `_count_dependents()` calls with precomputed values
- Eliminates O(n^2) bottleneck in search/overview/validate
- ~30 lines in `index.py` + removal of redundant counting functions
- **Status from previous report:** Proposed as R3, accepted, backlogged. Not yet implemented.

**R4: MCP tool annotations (readOnlyHint).**
- Add `readOnlyHint: true` to resolve_context, search_memories, focus_memory, overview, changelog, log, find_orphans, validate_memories
- Add `readOnlyHint: false` to create_memory, update_memory, snapshot, import_memories
- ~10 lines in `tools.py` per tool definition
- **Status from previous report:** Proposed as R4. Accepted (R11-P4). **Marked as not yet complete in sprint status.**

### Yellow (High-Impact, High-Effort) — Backlog

**Y1: Edge-First Memory Model.**
- Independent edge storage with bidirectional indexing
- O(1) reverse dependency queries
- Semantic edge types fully integrated into all operations
- Requires new edge index schema, sync mechanism on reindex, migration
- ~500 lines across index/models/resolve/validate/handlers
- **Status from previous report:** Proposed as "Edge-first data model" (R7). Accepted conceptually for long-term research.

**Y2: Content-Addressed Memory Identity (Merkle DAG).**
- Content hash as primary identity; path-based ID as mutable reference
- Object store for immutable memory versions
- Cryptographic provenance and tamper-evident references
- Requires design document before implementation
- **Status from previous report:** Proposed as "Alternative 2" (R6). Accepted for design document first. No design document exists yet.

**Y3: Hierarchical Memory Tiers.**
- hot/warm/cold tier classification with dynamic promotion/demotion
- Tier-aware resolve (skip cold by default)
- Requires tier recomputation on reindex and after every resolve
- ~200 lines
- **Status:** New proposal based on 2025 agent memory research.

### Green (Thought-Provoking) — Long-Term Research

**G1: Belief Revision Framework.**
- When a depended-upon memory is updated/corrected, propagate notifications to all dependents
- AGM theory (Alchourron-Gardenfors-Makinson) formal framework for belief change
- Requires dependency propagation infrastructure (enabled by Y1)

**G2: Memory Network Analytics.**
- PageRank for hub memory identification
- Community detection for knowledge cluster discovery
- Bridge detection for cross-domain connector memories
- Graph theory applied to existing DAG data with no new infrastructure

**G3: Multi-Agent Shared Memory Conflict Resolution.**
- CRDT vs Git merge vs structured negotiation for concurrent writes
- Memory "ownership" and "borrowing" concepts
- Requires Y1 + Y2 as prerequisites

**G4: Automatic Link Maintenance — Link Health Dashboard.**
- Consolidate existing detection (dead links, stale summaries, decay warnings, orphan detection, suggest-deps) into a unified health report
- ~100 lines consolidating existing logic

### Blue (Wild Ideas) — High-Risk, Potentially Game-Changing

**B1: The "Memory Compiler" — Static Pre-Assembly of Context Packages.**
- Compile-time DAG resolution → O(1) runtime context serving
- Pre-computed, cached, distributable context packages
- Analogous to compiled vs interpreted execution

**B2: "Memory Spectroscopy" — Cognitive Function Analysis.**
- Classify memories by cognitive function (Data/Pattern/Model/Decision/Reflection)
- Cognitive health dashboard: "Your memory system composition and what it says about your thinking"
- Coach, not just store

**B3: "Memory as a Story" — Narrative Coherence Retrieval.**
- Replace dependency resolution with narrative assembly
- "Tell me the story of my investment thinking" instead of "Resolve dependencies of X"
- LLM-powered narrative engine on top of DAG skeleton

---

## Appendix: Research Sources (2026 Update)

### Cognitive Architecture
- Laird, J. (2022). "An Analysis and Comparison of ACT-R and Soar." arXiv:2201.09305.
- Mohan, S. et al. (2020/2022). "Analogical Concept Memory for Architectures Implementing the Common Model of Cognition." arXiv:2006.01962 / arXiv:2210.11731.
- Dhamne, S. (2026). "Cognitive Architecture as a Blueprint." Autodesk Research.

### Knowledge Graph Storage & GraphRAG
- Napoli et al. (2025). "How to Evaluate NoSQL Database Paradigms for Knowledge Graph Processing." IEEE/ACM BDCAT 2025.
- "The Architecture of Connected Intelligence" (2025). Uplatz Blog.
- Microsoft GraphRAG (2024). https://microsoft.github.io/graphrag/
- Graphiti: Real-Time Knowledge Graphs for AI Agents. https://github.com/getzep/graphiti

### Note-Taking & Knowledge Tools
- Tana Supertags: "如何评价新一代知识管理工具 Tana?" 知乎. https://zhihu.com/question/558138387
- "Obsidian vs Roam Research vs Logseq vs Tana" (2025). Multiple community analyses.
- "Bidirectional Links vs Hierarchical Note Taking." DeepRead. https://deepread.com/bidirectional-vs-hierarchical-links/
- SiYuan (思源): Block-level bidirectional linking with local storage.

### Agent Memory (2025)
- SAGE: "Self-evolving Agents with Reflective and Memory-augmented Abilities." Neurocomputing, Sept 2025.
- Mem0/Mem0g: Scalable memory with graph-based relational reasoning. VentureBeat, 2025.
- HAMR: "Hierarchical Adaptive Memory Retrieval." GitHub: ImZackAdams/hamr-ai.
- GAM: "General Agentic Memory System." AiTechSuite, 2025.
- MemAgent: "Reshaping Long-Context LLM with Multi-Conv RL-based Memory Agent." arXiv:2507.02259.
- CoA: "Chain of Agents." Google Research, NeurIPS 2024 / Jan 2025.

### Spaced Repetition & Forgetting
- LECTOR: "LLM-Enhanced Concept-based Test-Oriented Repetition." arXiv:2508.03275, Aug 2025.
- EDGE: "Misconception-Aware Adaptive Learning." arXiv:2508.07224, Sep 2025.
- FSRS: "Free Spaced Repetition Scheduler." Open-source, used in Anki.

### Git & Content-Addressed Storage
- DiffMem: "Revolutionizing AI Memory Management with Git-Based Version Control." https://xugj520.cn/en/archives/diffmem-git-based-ai-memory-management
- Noms/Dolt: Git-inspired versioned databases with Prolly Trees.
- Chit (davidad): Version control for structured categorical data.

---

*End of research audit report — Sprint 13.*
