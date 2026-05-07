# CodeMemory -- Product Research Audit Report

**Date:** 2026-05-06
**Reviewer:** Product Research Reviewer
**Methodology:** Full source code review (20 modules), adjacent domain research (cognitive architecture, knowledge graphs, note-taking tools, MCP server patterns, Git object model), hands-on product experience (reindex, validate, overview, resolve, wander, search, orphans, suggest-deps), design document analysis (CLAUDE.md, PRD, architecture, Layer 0 cognitive interface)

---

## Executive Summary

**Core Assumptions Underlying the Current Design:**

1. **"Memory loading is dependency resolution, not search."** — The product's foundational thesis. Explicit `imports` in YAML frontmatter replace semantic similarity as the retrieval mechanism.
2. **"Memory = Markdown file."** — Each unit of memory is a physical `.md` file with YAML frontmatter. The filesystem is the database.
3. **"Forgetting = unreachability."** — Memories are never deleted; they become unfindable through the DAG. Decay is advisory, not enforced.
4. **"Agents should see bash, not Python."** — The agent interface is CLI commands; the underlying engine is an implementation detail.
5. **"Token budget determines resolution, not recall."** — When context is too large, lower-priority memories are downgraded to summary, not dropped.

**Largest Research Finding: The "DAG as cognitive retrieval" metaphor is powerful but brittle.** It maps elegantly to causal reasoning chains (the investment context example is compelling), but it overfits to one type of memory access pattern — "I need to reconstruct the causal closure around a decision." There is a whole class of memory needs it does not address: associative recall ("what else was I thinking about when I wrote this?"), temporal adjacency ("what happened around the same time?"), contradiction detection ("do I hold two incompatible beliefs?"), and analogical retrieval ("this current situation feels like something I've seen before, but I can't name it").

**Most Valuable Breakthrough Direction:** Content-addressable identity (Git's object model) applied to memory atoms, combined with the existing DAG structure, would transform CodeMemory from a "labeled dependency graph" into a **Merkle DAG of immutable memory snapshots**. Each memory version would be hash-addressed, enabling structural sharing across versions, tamper-evident citations, and time-travel queries — all while preserving the existing `.md` file authoring experience.

---

## Phase 1: Core Assumptions Questioning

### 1.1 Assumption Inventory

Below is a complete inventory of implicit design assumptions identified through source code analysis and product experience. Each is tagged with its risk level.

| # | Assumption | Where It Lives | Risk Level |
|---|-----------|---------------|------------|
| A1 | **Memory loading is dependency resolution, not search** | CLAUDE.md, PRD, resolve.py | **HIGH** — Overfits to causal chains; ignores associative, temporal, and analogical retrieval |
| A2 | **Memory = Markdown file on filesystem** | core.py, index.py, create.py | **MEDIUM** — Constrains memory to text; no binary/media support; file count = memory count |
| A3 | **Forgetting = unreachability (path inaccessibility)** | CLAUDE.md, validate.py `_check_decay` | **MEDIUM** — Confuses "I can't find it" with "I shouldn't remember it"; no active forgetting |
| A4 | **Agent interface = bash CLI** | CLAUDE.md, cli.py, layer0-cognitive-interface.md | **MEDIUM** — Elegant for Claude Code; awkward for web-based LLM platforms |
| A5 | **Token budget = character count** | core.py `estimate_tokens` | **LOW** — Known limitation documented in architecture; tokenizer integration deferred |
| A6 | **Dependencies are manually declared** | frontmatter `imports`, suggest_deps.py | **HIGH** — Places burden on human/agent to maintain edges; DAG quality = human effort |
| A7 | **One memory = one file = one ID** | PRD rule R3, reindex logic | **MEDIUM** — Prevents memory fragmentation/merging; granularity is fixed at create time |
| A8 | **Memory integrity = body hash match** | core.py `compute_body_hash`, resolve.py stale detection | **LOW** — Good for detecting drift; doesn't detect semantic staleness |
| A9 | **Heat = dependents * 10 + access_count** | handlers.py `handle_overview` | **MEDIUM** — Simple formula, but no recency decay; a memory accessed 100x six months ago beats one accessed 5x yesterday |
| A10 | **Maturity auto-upgrade is monotonic** | resolve.py lines 322-338 | **MEDIUM** — Memories only go up (draft -> verified -> proven); no downgrade path except manual superseded |
| A11 | **Schemas define structure, not behavior** | schemas/decision.md, validate.py `check_schema_compliance` | **LOW** — Schemas are field checklists; no inheritance, composition, or validation logic |
| A12 | **Single-user, single-agent** | No auth, no multi-tenancy, no collaboration primitives | **LOW** — Appropriate for current stage; becomes critical at scale |
| A13 | **All memories are equally trustable** | No provenance verification, no cryptographic signing | **MEDIUM** — `source.platform` and `source.created_by` exist but are self-reported |
| A14 | **Transient DAG = in-process only** | transient.py — nodes vanish on process exit | **HIGH** — No shared transient state across concurrent sessions; snapshot is the only bridge |

### 1.2 Key Assumptions — Deep Dive

#### A1: "Memory loading is dependency resolution, not search"

**Why it matters:** This is the product's identity. The PRD explicitly frames CodeMemory against RAG: "RAG retrieves chunks without dependency relationships; CodeMemory resolves causal closures."

**Where the assumption holds:** The investment context example is genuinely persuasive. `resolve user/investment/context` produces a coherent causal chain: semiconductor thesis -> risk tolerance -> no-leverage constraint -> february buy decision -> current holdings -> market facts. Each step builds on the prior. The topological sort places foundational facts before derived decisions. This is a real improvement over embedding-based retrieval for this class of task.

**Where it breaks:**

1. **Associative recall** — Suppose the agent encounters a new situation that is structurally similar to a past one, but shares no tags and no imports. Example: evaluating whether to invest in biotech. No memory imports "user/investment/semiconductor-thesis" — but the reasoning pattern (evaluate thesis -> check risk tolerance -> review past decision outcomes) is identical. A pure DAG approach cannot surface this. You need either structural pattern matching across DAGs, or embedding-based similarity on the reasoning structure itself.

2. **Cross-domain insight** — A preference expressed in `user/preferences/no-leverage` ("don't use leverage") has implications not just for investment but for business strategy, career decisions, etc. But if no business memory imports it, the DAG won't surface it in those contexts. The dependency graph is a **pull model** (memory B must explicitly declare "I need memory A"). There is no **push model** ("this constraint applies everywhere").

3. **The bootstrapping problem** — To use CodeMemory effectively, the user/agent must first populate a well-connected dependency graph. But the initial state is a set of disconnected atoms with no imports. The `suggest-deps` command (tag intersection + schema pattern) is a heuristic patch, but its quality depends on consistent tagging — which is itself an upfront cost.

4. **Cold start for new domains** — In the investment dataset, `user/investment/context` is the entry point. It has 5 required + 3 recommended imports. This is a manually curated "composite" that serves as a load-bearing entry point. In a new domain, someone must build this composite first. The system has no bootstrapping mechanism for "I just entered a new domain and have 15 disconnected facts — help me find structure."

**What changes if the assumption is loosened:** A hybrid model where the DAG remains the primary retrieval mechanism, but an embedding-based associative layer serves as a "suggestion engine" that surfaces potentially relevant but not explicitly linked memories. This is not replacing DAG resolution — it's adding a **lateral retrieval** complement to the depth-first dependency traversal. The analogy: DAG resolution is like following a paper's reference chain; associative retrieval is like browsing a library shelf near a relevant book.

#### A6: "Dependencies are manually declared"

**Why it matters:** The quality of every `resolve` output depends entirely on the quality and completeness of `imports` declarations. A missing `required` import means the agent lacks crucial context; a spurious import wastes token budget.

**Where the assumption holds:** In a curated knowledge base maintained by a diligent human, explicit imports are the right model. They are auditable, explainable, and version-controlled. The `pin: v1` mechanism (locking a dependency to a specific version) only works with explicit imports.

**Where it breaks:**

1. **Agent-maintained memory** — When an agent autonomously creates memories during conversation, it must also create correct import declarations. This is a meta-cognitive task: the agent must recognize "the conclusion I just reached depends on fact X, preference Y, and observation Z." LLMs can do this but inconsistently. A missed dependency silently corrupts future resolves.

2. **Evolving understanding** — A memory created today might later be recognized as depending on something not known at creation time. The `suggest-deps` command helps retroactively, but it requires someone to run it. There is no automatic "dependency review" triggered by new memory creation.

3. **Transitive dependency depth** — `user/investment/context` imports `user/investment/february-buy`, which imports `user/investment/semiconductor-thesis`. The DAG resolver handles this transitively. But the person creating `february-buy` doesn't need to know it will eventually be part of `context`. The system works because each memory declares its immediate dependencies. However, as the graph grows, the **total resolved context** for a deep entry point can unexpectedly balloon — the creator of `context` doesn't control the transitive fan-out.

**What changes if the assumption is loosened:** A **dependency inference engine** that runs continuously, not just on-demand via `suggest-deps`. When a new memory is created or updated, the system could automatically evaluate potential dependencies against all existing memories and surface high-confidence suggestions. This is different from the current `suggest-deps` which requires manual invocation. The key shift: from "dependencies are declared" to "dependencies are declared + automatically proposed + periodically reconciled."

#### A14: "Transient DAG = in-process only"

**Why it matters:** The TransientDAG is the mechanism for session-level reasoning chain memory. It is described as the "残留" (residue) cognitive primitive — the ability to persist valuable reasoning products before they vanish.

**Where the assumption holds:** For a single-session agent working on a bounded task, in-process TransientDAG works. The agent adds reasoning nodes during the conversation, resolves them in memory, and snapshots the result.

**Where it breaks:**

1. **Multi-session reasoning** — If an agent works on a complex task across multiple sessions (e.g., a multi-day research project), the TransientDAG is lost between sessions. The snapshot is a static artifact — it can't be extended. The agent must either create persistent memories for every intermediate step (cluttering the knowledge base) or accept lost context.

2. **Concurrent agent sessions** — If two agents are working on related tasks simultaneously (e.g., one researching, one coding), their TransientDAGs are isolated. There is no shared transient workspace.

3. **Resumable reasoning** — A snapshot captures the output of reasoning, not the reasoning state. It's like saving a JPEG of a whiteboard instead of the whiteboard itself. The agent can read what was concluded, but can't continue the reasoning chain where it left off.

**What changes if the assumption is loosened:** A **persistent session DAG** that lives between process invocations — not as snapshot artifacts, but as live, extendable reasoning graphs. This could be implemented as a special category of memory that auto-expires (TTL-based cleanup) but is writable and queryable during its lifetime. Think: "workspace memory" vs "archival memory."

### 1.3 Where the Metaphor Constrains Thinking

The current system operates under several interlocking metaphors. Each is useful but creates blind spots.

#### "Memory = File"

**What it enables:** Version control (Git), human readability, platform independence, no database dependency.

**Where it becomes strained:**

- **Granularity lock-in** — A memory is created at a certain granularity (e.g., `user/investment/risk-tolerance` as one file). If you later realize "risk tolerance" should be split into "risk capacity" and "risk willingness," you must manually refactor. The file metaphor doesn't support splitting or merging as first-class operations.
- **No partial memory access** — `focus --level summary` returns either the whole body or just the summary. There's no "show me paragraph 3 of this memory" or "show me the section on constraints." The file is an indivisible unit at the focus level (distinct from the summary/full toggle).
- **Schema instances store extra fields in frontmatter** — `february-buy.md` has `what:`, `why:`, `when:`, `confidence:`, `outcome:` as top-level frontmatter fields alongside `type`, `id`, `summary`. This is a flat namespace — there's no structural distinction between "base fields the system needs" and "domain fields the schema defines." If two schemas happen to use the same field name (e.g., both have a `priority` field), there's a collision.

#### "Forgetting = Unreachability"

**What it enables:** No destructive operations, full audit trail, system only advises, never deletes.

**Where it becomes strained:**

- **Unreachable is not the same as forgotten** — An archived memory still exists in the index. It's still accessible via `search` (unless filtered out). It's still visible in the graph view. "Archived" is a status flag, not a retrieval barrier. The system doesn't actually implement forgetting — it implements labeling.
- **No active forgetting mechanism** — ACT-R's declarative memory model uses **base-level activation decay** (a power-law function of time and usage frequency). Memories not retrieved gradually become harder to access — not impossible, just requiring more activation energy. CodeMemory has no analog to activation thresholds. A memory with `intensity: 1` and zero access is equally retrievable as one with `intensity: 10` and 100 accesses — the only difference is that `overview` deprioritizes the former.
- **Protected memories are immortal** — `intensity >= 8` triggers `protected: true`, which exempts the memory from decay warnings and wander sampling. There's no mechanism for a protected memory to become unprotected over time. In human memory, even strongly held beliefs can fade or be revised.

#### "Memory Loading = Code Compilation"

The PRD explicitly draws the analogy: "resolve is like `webpack bundle`, not `vector search`." This is the deepest metaphor in the system.

**What it enables:** Deterministic output, auditable dependency chains, predictable token usage.

**Where it becomes strained:**

- **Code has a single entry point; cognition doesn't** — A webpack bundle starts from `index.js` and traces all imports. But in cognition, you rarely have a single, well-defined entry point. You have a fuzzy, evolving awareness of "what seems relevant." The `overview` command partially addresses this by surfacing high-heat memories, but it's a separate mechanism from resolve — they don't compose.
- **Code dependencies are static; cognitive dependencies evolve** — In code, if `A` imports `B`, that relationship is stable. In cognition, the fact that you used `risk-tolerance` to make the February buy decision is permanently true. But the relevance of `risk-tolerance` to future decisions may change as your risk preferences evolve. The DAG captures historical dependency but not **current relevance**.
- **Compilation is all-or-nothing; cognition is partial and approximate** — The resolve algorithm with token budget tries to simulate this via summary downgrading, but it's a linear trim — nodes are either full, summary, or skipped. There's no model of which *parts* of a memory are most relevant to the current context. A 2000-word memory might have one crucial paragraph; the system either includes all 2000 words or reduces to a one-line summary. There is no intermediate "extractive" resolution.

---

## Phase 2: Adjacent Domain Research

### 2.1 Domain Scan

Research was conducted across five adjacent domains. For each, I identify the core idea and what is directly transferable to CodeMemory.

#### Domain 1: Cognitive Architecture (ACT-R / SOAR)

**Core ideas:**
- **Declarative memory** is a set of chunks, each with an **activation level** that decays over time following a power-law function. Retrieval is probabilistic: higher activation = higher chance of retrieval.
- **Base-level learning equation**: `A_i = ln(sum(t_j^(-d)))` where `t_j` is time since the j-th reference and `d` is the decay parameter. Frequently accessed memories resist decay; unused memories become inaccessible.
- **Spreading activation**: When a chunk is retrieved, activation spreads to associated chunks, making them more retrievable. This is how human associative memory works — thinking about one thing "primes" related things.
- **Forgetting is continuous, not binary**: Chunks don't get deleted; they become progressively harder to retrieve. But they can be re-activated by related cues.
- **Working memory** has limited capacity (approximately 4 +/- 1 chunks) — analogous to token budget.

**Transferable to CodeMemory:**
1. **Replace static `heat` with activation decay** — Instead of `heat = dependents * 10 + access_count`, use a time-weighted activation function where recent accesses matter more than old ones. This would make `overview` output dynamic rather than monotonic.
2. **Spreading activation for overview** — When `resolve` accesses a set of memories, activation should spread along the import graph to connected memories, making them more likely to surface in subsequent `overview` calls. This creates a natural **priming effect** — you're more likely to "notice" memories related to what you've been thinking about.
3. **Retrieval threshold as forgetting** — Instead of "forgetting = unreachability," implement forgetting as a retrieval threshold. Memories below a certain activation level are still in the index but won't appear in `overview` or `search` unless explicitly targeted by ID. This makes forgetting **graded and reversible** rather than structural.

#### Domain 2: Knowledge Graph Storage (RDF, Property Graphs, Temporal KG)

**Core ideas:**
- **RDF triples** (subject-predicate-object) provide a universal, schema-flexible representation. RDF-star adds qualifiers (temporal, provenance) to triples.
- **Property graphs** (Neo4j-style) store properties on both nodes and edges, making edges first-class citizens with their own metadata.
- **Temporal KGs** extend triples with `time_added`, `last_accessed`, `num_recalled` — directly analogous to CodeMemory's `created`, `last_access`, `access_count`.
- **Graph RAG** (Microsoft, 2024) retrieves from knowledge graphs by combining structured query (SPARQL/Cypher) with embedding-based retrieval for unmatched patterns.

**Transferable to CodeMemory:**
1. **Edge properties** — Currently, imports are simple ID references (with optional `pin` and `reason` for structured imports). Property-graph thinking would make the **relationship itself** a rich object: `{type: "required", strength: 0.9, rationale: "...", created: "2026-01-15", validated_in: ["session-abc"]}`. This enables richer DAG analysis (e.g., "show me all relationships weaker than 0.7").
2. **Reification of imports** — RDF-star's "statements about statements" maps to: "the February buy decision depends on risk-tolerance v1" is itself a fact that can be annotated, versioned, and queried. Currently, the `pin` and `reason` fields are the only annotation on imports.
3. **Temporal KGs for evolution tracking** — Track `time_added` and `time_last_used` on each import edge. This would enable queries like "what dependencies have become less relevant over time?" or "which import relationships were added after the initial memory creation?"

#### Domain 3: Note-Taking Tools (Obsidian, Roam Research, Logseq)

**Core ideas:**
- **Bidirectional linking** — Obsidian uses file-path-based `[[wikilinks]]`; Roam assigns immutable block IDs. The key difference: Roam's links survive renames; Obsidian's require link-updating.
- **Block-level granularity** — Roam treats every paragraph/block as an addressable entity with its own ID. This enables referencing not just "a document" but "a specific claim within a document."
- **Graph view as navigation, not decoration** — In Roam, the graph is a query interface where clicking a node filters to its connected content. Obsidian's graph is primarily a visual replay.
- **Transclusion** — Ted Nelson's concept, partially implemented: embed a block or section from one note within another. Changes to the source propagate to the embedding.
- **Daily notes as temporal anchor** — Both tools encourage daily notes as a chronological entry point, from which structured pages emerge organically.

**Transferable to CodeMemory:**
1. **Block-level references in imports** — Instead of `imports: [user/investment/risk-tolerance]`, allow `imports: [user/investment/risk-tolerance#constraints]` to reference a specific section. This enables more precise dependency resolution and reduces token waste.
2. **Transclusion for memory composition** — A composite could transclude specific sections from its imports rather than the full body. Changes to the source section would be reflected in the resolve output (with stale detection on the section level).
3. **Graph-as-navigation in the frontend** — The current graph view is primarily visual. Roam-style interactive filtering (click node -> show only its neighborhood) would make it a functional exploration tool.
4. **Temporal entry points** — A "memory timeline" view, inspired by daily notes, that shows memories in chronological order of creation/access. This surfaces temporal adjacency patterns that the DAG structure misses.

#### Domain 4: MCP Server Design Patterns

**Core ideas:**
- **Capability-oriented design** — Expose tools that represent what the agent can accomplish, not what data the system stores. One tool = one complete workflow.
- **Progressive discovery** — Layer tool exposure: service category -> operation name -> parameter schema. Avoid overwhelming the model's context window.
- **Agent-oriented error handling** — Return structured errors with retry hints, not human-readable messages.
- **"Less is more"** — Fewer, more capable tools outperform many narrow tools in agent task completion rate.
- **Stateless, idempotent operations** — Each call is self-contained; no server-side session state.

**Transferable to CodeMemory:**
1. **Consolidate tools** — The MCP server currently exposes 5 tools that map 1:1 to Layer 0 primitives. Consider exposing 2-3 composite tools: `remember_context` (overview + resolve combined), `explore_memory` (wander + focus + suggest-deps), `persist_insight` (snapshot + create). This reduces the agent's tool-selection burden.
2. **Structured result metadata** — Instead of returning plain text from resolve, return structured JSON with sections: `{context: [...], notices: [...], token_usage: {used, budget}, maturity_changes: [...]}`. The agent can then decide how to use each section.
3. **Tool annotations** — Mark tools as `read-only` (resolve, focus, wander, overview) vs `destructive` (snapshot). This enables MCP clients to implement safety guardrails.

#### Domain 5: Git Object Model (Content-Addressable Storage)

**Core ideas:**
- **Content-addressable identity** — Every object is named by the hash of its content. Same content = same hash = automatic deduplication.
- **Merkle DAG** — Commits form a DAG where each commit references its parent(s) via hash. Structural sharing: unchanged subtrees are referenced by hash, not copied.
- **Immutable history** — Once created, objects never change. "Updates" create new objects that reference unchanged old ones.
- **Branching and merging** — Parallel lines of development that can be reconciled.

**Transferable to CodeMemory:**
1. **Content-addressed memory identity** — Instead of path-based IDs (`user/investment/risk-tolerance`), each memory version could have a content hash. The path-based ID becomes a **mutable reference** (like a Git branch) that points to the latest version. This enables: (a) tamper-evident citations — "I'm referencing version `a3f2e1d` of risk-tolerance" is cryptographically verifiable; (b) structural sharing — if two memories share an identical dependency graph structure, they share the same graph object.
2. **Merkle DAG for resolve snapshots** — When resolve assembles a context, the assembled output could be content-addressed. If the same resolution happens again (same entry point + same dependency versions), you get the same hash — no need to re-resolve.
3. **Branching for speculative reasoning** — An agent exploring "what if I had a higher risk tolerance?" could branch from the current memory state, modify `risk-tolerance`, and resolve the branch without affecting the "main" DAG. If the branch proves valuable, merge it back.
4. **Time-travel queries** — "What did the DAG look like on March 15, before the NVIDIA earnings report?" — answerable by traversing the Merkle DAG to the commit nearest that date.

### 2.2 Most Transferable Patterns (Top 5)

| # | Pattern | Source Domain | Why It Fits CodeMemory |
|---|---------|--------------|----------------------|
| 1 | **Activation decay with spreading activation** | Cognitive Architecture (ACT-R) | CodeMemory already has `access_count` and `last_access`. Replacing static `heat` with time-decayed activation is a formula change, not an architecture change. Adding spreading activation along import edges makes `overview` contextually adaptive. |
| 2 | **Content-addressable memory identity** | Git Object Model | CodeMemory already uses `summary_hash` (sha256[:7]) for body integrity. Extending this to full content addressing enables immutable version history, structural sharing, and cryptographic provenance — all while preserving the `.md` file authoring experience. |
| 3 | **Edge properties on imports** | Knowledge Graphs (Property Graph) | CodeMemory's imports are currently simple string lists with optional `pin`/`reason`. Making edges first-class with `strength`, `created`, `validated_in` enables richer DAG analysis at minimal schema cost. |
| 4 | **Block-level references** | Note-Taking Tools (Roam Research) | The current all-or-nothing memory resolution wastes tokens on irrelevant sections. Section-level references (`#section-id`) enable precise dependency declaration and targeted resolution. |
| 5 | **Capability-oriented MCP tool consolidation** | MCP Design Patterns | The 5-tool MCP server maps 1:1 to Layer 0 primitives. Consolidating into 2-3 composite capability tools reduces agent cognitive load and tool-selection errors. |

### 2.3 Competitive Design Philosophy Comparison

Rather than feature-by-feature comparison (covered in the evolution audit), this section compares design philosophies.

| Product | Core Metaphor | Retrieval Model | Forgetting Model | Interface Philosophy |
|---------|--------------|----------------|------------------|---------------------|
| **CodeMemory** | Memory = file; loading = compilation | DAG resolution (explicit imports) | Unreachability (advisory) | Bash CLI for agents |
| **MemForge** (47 MCP tools) | Memory = temporal event stream | Multi-modal (pgvector + full-text + temporal) | 10-phase sleep cycles (active forgetting) | Rich tool surface |
| **SuperLocalMemory** (75 tools) | Memory = cognitive channel | 7-channel retrieval (Fisher-Rao embedding) | Channel-based decay | Channel decomposition |
| **MAG** (single Rust binary) | Memory = compressed archive | ONNX embeddings + inverted index | TTL-based expiry | Minimal single-binary |
| **Roam Research** | Memory = block graph | Bidirectional link traversal + queries | Deliberate archival only | Interactive graph UI |
| **Obsidian** | Memory = interlinked files | File-level `[[wikilinks]]` + graph view | Files exist or don't | Extensible plugin ecosystem |

**Key philosophical divergence:**

CodeMemory's bet is that **explicit, auditable structure** (DAG, imports, schemas) produces higher-quality agent reasoning than **probabilistic retrieval** (embeddings, similarity scores). This is a defensible position for domains where causal completeness matters (investment decisions, medical reasoning, legal analysis). But it creates a **coverage gap**: domains where the agent doesn't know what it needs, or where the relevant connections haven't been explicitly encoded.

The competitive landscape suggests a hybrid model: deterministic DAG for causal closure + probabilistic embeddings for associative discovery. MemForge and SuperLocalMemory already implement this. CodeMemory's `suggest-deps` with three-layer filtering (tag intersection + schema pattern + heat ranking) is a non-embedding approximation of the same idea, but it's weaker than vector-based similarity because it relies on consistent tagging.

---

## Phase 3: Logical Completeness

### 3.1 Concept System Assessment

The current concept landscape, with fuzzy boundaries marked:

```
                    ┌──────────────────────────────────┐
                    │         MemoryEntry               │
                    │  (the universal unit)             │
                    └────────────┬─────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
         type: atom          type: schema        (no other types)
              │                  │
    ┌─────────┼─────────┐       │
    │         │         │       │
  with     with      with     defines
  imports  schema    neither   fields[]
    │         │         │
    │    schema field   │
    │    points to ─────┘
    │
 imports:
   required[]
   recommended[]   ←── strength distinction is used by resolve for trimming
   related[]       ←── but not by search, not by overview, not by validate

Additional orthogonal dimensions:
  maturity: draft → verified → proven   ←── monotonic only
  intensity: 1..10                      ←── >=8 = protected
  status: active/archived/superseded    ←── flat, no state machine
  tags: string[]                        ←── untyped, free-form
  access_count / last_access            ←── tracked but only used by heat
```

**Fuzzy boundaries identified:**

1. **`intensity` vs `protected`** — The `protected` field is derived from `intensity >= 8` in `reindex`. But `protected` can also be manually set in frontmatter. If `intensity` changes, does `protected` re-evaluate? Currently only on reindex. The relationship is implicit and temporal.

2. **`status` vs `maturity`** — `status: archived` and `maturity: superseded` overlap conceptually. If a memory is superseded, shouldn't its status reflect that? The two fields capture different axes (lifecycle state vs knowledge confidence), but the boundary is unclear to a user.

3. **`tags` as semantic type** — The `search --semantic-type` filter inspects tags, not a dedicated `semantic_type` field. This means a memory must be tagged consistently for semantic-type filtering to work. The architecture doc says "semantic_type: through tags," which is a design choice, but it conflates two concepts: classification (what domain) and semantic role (what function this memory serves).

4. **`imports` as both data and structure** — The imports dict serves dual purposes: it defines the DAG structure (how memories relate) AND it captures domain semantics (what kind of relationship: required vs recommended vs related). These are not cleanly separated. A memory might have a "required" dependency that is structurally required (without it, the memory is misleading) vs one that is procedurally required (the agent should always load it).

5. **TransientDAG vs persistent memories** — The boundary between "in-session reasoning" and "persistent knowledge" is the `snapshot` command. Once snapshotted, transient nodes become persistent atoms. But there's no back-link from the persistent atom to the transient session it came from, and no mechanism to "resume" a session's transient state.

### 3.2 Extreme Scenario Testing

#### Scenario 1: Zero Memories (cold start)

**Does the design hold?**
- `reindex`: Returns 0, prints "Reindexed 0 memories successfully." Works.
- `validate`: "0 memories checked. Errors: 0, Warnings: 0." Works.
- `resolve`: Target not found error. Works.
- `search`, `orphans`, `overview`, `wander`: Return "(no results)". Works.
- `create`: Creates the first memory. Works.
- `suggest-deps`: Target not found error. Works.

**Verdict:** The system handles zero-state gracefully. **But** there is no guided bootstrap experience. An agent starting from zero memories has no way to discover what memories it *should* create first. The `overview` command would be the natural place for bootstrap guidance ("You have no memories yet. Consider creating a context composite to serve as an entry point, then add facts and decisions as atoms.")

#### Scenario 2: 10,000 Memories, Densely Connected

**Does the design hold?**
- `reindex`: O(n) file scanning — ~10,000 files is fine for a single scan. Works.
- `validate`: For each of 10K memories, checks all imports. Worst case O(n * avg_imports) ~ manageable. But the DFS cycle check runs per-memory — O(n * (V+E)). At 10K nodes, this could take noticeable time. **Borderline.**
- `resolve`: The DAG build starts from the target and recursively follows imports. If the graph is densely connected, the DAG could include a large fraction of all memories. **Token budget clipping becomes essential, not optional.**
- `search`: O(n) linear scan with filter checks. 10K iterations is fast. Works.
- `overview`: Heat computation requires counting dependents for all 10K memories — O(n^2) in the worst case if done naively. The current implementation in `search.py` calls `_count_dependents` per memory. At 10K, this is ~100M import checks. **Performance concern.**

**Key fragility:** The `_count_dependents` function is O(n * avg_imports) but is called inside loops in `search`, `overview`, and `validate`. With 10K memories, this becomes a bottleneck. A precomputed `in_degree` map in the index would eliminate this.

#### Scenario 3: All Memories Are Orphaned (no imports anywhere)

**Does the design hold?**
- `reindex`: Works — imports are optional.
- `validate`: No broken links (nothing to check). No cycles. Will flag decay warnings for low-access memories without dependents. Works, but the decay warnings will be noisy — every memory qualifies.
- `resolve`: Can only resolve the target itself (no imports to traverse). The DAG is a single node. Works, but produces minimal context.
- `orphans`: Lists all memories. Correct but unhelpful.
- `suggest-deps`: Works — uses tag overlap, which doesn't require existing imports. This is the **most useful command** in this scenario.

**Verdict:** The system works but offers minimal value when there are no connections. This is the **cold-start for a populated but unstructured knowledge base** — different from the zero-memory cold start. The `suggest-deps` command is the bridge, but it requires manual invocation per memory. An `auto-connect` command that runs suggest-deps across all memories and proposes a connection plan would be transformative for this scenario.

### 3.3 Operation Gaps

Operations that an agent would likely want to perform but cannot with the current CLI:

| Desired Operation | Current Workaround | Gap Severity |
|-------------------|-------------------|--------------|
| "Find memories that contradict or are inconsistent with this one" | None — no contradiction detection | **HIGH** — Fundamental to knowledge quality |
| "What was the state of my knowledge on date X?" | Manually inspect change_log and Git history | **MEDIUM** — Time-travel query |
| "Merge these two related memories" | Manual: read both, create new, update status | **MEDIUM** — No merge primitive |
| "Split this memory into multiple atoms" | Manual: create new files, copy sections, update imports | **MEDIUM** — No split primitive |
| "Find all decisions that depended on a now-superseded fact" | `orphans` + manual graph inspection | **MEDIUM** — Impact analysis of knowledge changes |
| "Compare two versions of a memory side-by-side" | Manual: read both from Git or changelog | **LOW** — Diff view |
| "What reasoning chains have I explored that didn't lead to a conclusion?" | None — TransientDAG is ephemeral | **MEDIUM** — Dead-end tracking |
| "Show me all memories I haven't reviewed in 6 months, sorted by importance" | `validate` shows some decay warnings; no importance sort | **MEDIUM** — Review queue |
| "Export all memories that would be loaded for topic X as a standalone document" | `resolve` + manual copy | **LOW** — Export is a separate feature |
| "Find the most central/most connected memory" | `overview` shows highest heat; no explicit centrality metric | **LOW** — Graph analytics |

### 3.4 Evolution Bottlenecks

If the system needs to add new capabilities, where does the current model resist change?

1. **Adding a new dependency strength tier** (e.g., "contradicts") — Requires changes to: `_get_imports()` in resolve.py (depth filtering), all three `_count_dependents` functions (resolve.py, search.py, validate.py), `_compute_in_degree` in validate.py, `_resolve_import_ids` in handlers.py, `_build_graph` in transient.py, the suggest-deps three-layer filter, and the search `has_imports` filter. This is **7+ locations** for one new field. The import strength enumeration is scattered rather than centralized.

2. **Adding non-text memory types** (images, audio, structured data) — The file metaphor assumes Markdown. `parse_frontmatter` assumes text with `---` delimiters. `compute_body_hash` hashes text. `estimate_tokens` counts characters. The entire pipeline is text-assumptive.

3. **Multi-agent collaboration** — The index stores `access_count` and `last_access` but doesn't track which agent accessed it. There's no concept of agent identity, no access control beyond the `self/` convention, and no merge strategy for concurrent writes. The file-based storage means Git merge conflicts are the only concurrency control.

4. **Memory templates with dynamic behavior** — Schemas currently define static field lists. There's no way to say "a decision memory should automatically import the risk-tolerance memory if confidence < 0.6." Adding behavioral rules to schemas would require a new execution model.

5. **Cross-dataset references** — The current model assumes all memories live within one `CODEMEMORY_ROOT`. Cross-dataset references would require a namespace prefix system (e.g., `@investment/user/facts/nvidia-earnings`) which doesn't exist.

---

## Phase 4: Alternative Design Proposals

### 4.1 Core Mechanism Alternatives

#### Alternative 1: Probabilistic Activation Instead of Static Heat

**Current design:** `heat = dependents * 10 + access_count`. Static. A memory accessed 100 times six months ago has higher heat than one accessed 5 times yesterday.

**Proposed alternative:** ACT-R inspired activation function:

```
activation(m) = ln( sum( t_ref^(-d) ) ) + spreading_bonus(m, context)
```

Where:
- `t_ref` = time since each historical access (in hours)
- `d` = decay parameter (tunable, default 0.5)
- `spreading_bonus` = sum of activation of memories that import this one, weighted by import strength

Properties:
- Recent accesses matter exponentially more than old ones
- Memories connected to recently-active memories get a "priming" boost
- Cold memories naturally fade from overview without being structurally orphaned
- Retrieval threshold: if `activation < theta`, memory is "forgotten" (not shown in overview but still accessible by ID)

**Tradeoff analysis:**

| Dimension | Static Heat | Activation Decay |
|-----------|------------|------------------|
| Simplicity | High — two-term sum | Medium — requires log, power, sum |
| Predictability | High — deterministic | High — still deterministic given same access history |
| Temporal awareness | None | Captures recency naturally |
| Cold start behavior | All new memories have heat=0 | All new memories have low but equal activation |
| Computation | O(1) per memory | O(k) per memory where k = access history length |
| When worth it | Small, static datasets | Growing datasets where recency matters |

**Verdict:** The activation decay model is a drop-in replacement for `heat` in `overview`. It doesn't change the DAG structure, imports, or resolve algorithm. It just makes the "what should the agent be aware of?" question time-aware. Low effort, meaningful improvement.

#### Alternative 2: Content-Addressed Memory DAG (Merkle DAG Memory)

**Current design:** Memories are identified by path-based IDs. Versions are incremented integers. There's no cryptographic guarantee that "version 3" is what it claims to be.

**Proposed alternative:** Each memory version is content-addressed (SHA-256 of the entire file). The path-based ID (`user/investment/risk-tolerance`) becomes a **mutable reference** (like a Git branch) that points to the latest content hash. The DAG of dependencies uses content hashes, not path IDs — meaning the dependency graph itself is content-addressed.

```
ref: user/investment/risk-tolerance → hash: abc123def
                                           ↓ imports
                                      hash: 789xyz... (semiconductor-thesis v1)
                                      hash: 456uvw... (risk-tolerance v1, pinned)
```

Key properties:
- **Tamper-evident**: Any modification to a memory changes its hash, breaking all downstream references until explicitly updated
- **Structural sharing**: If two composites import the same version of the same memory, the hash is identical — deduplication is automatic
- **Immutable history**: All versions are retained (in `.codememory/objects/`). The current version is just a pointer
- **Time-travel resolve**: "Resolve as of commit X" by following references at that commit
- **Merkle proof of inclusion**: Prove that a specific memory version was part of a specific resolve output

**Tradeoff analysis:**

| Dimension | Path-Based ID + Integer Version | Content-Addressed Merkle DAG |
|-----------|-------------------------------|------------------------------|
| Simplicity | High | Low — requires object store, reference management |
| Human readability | High | Medium — file editing remains unchanged; object store is behind the scenes |
| Integrity guarantees | Low — trust-based | High — cryptographic |
| Storage efficiency | High — one copy per version | Higher — immutable objects accumulate; need GC |
| Git integration | Manual (user commits files) | Natural — same mental model |
| Implementation complexity | Current | Significant — object store, ref updates, GC |
| When worth it | Prototype, single-user | Production, multi-agent, compliance-critical |

**Verdict:** This is a high-effort, high-impact change. Not appropriate for immediate implementation, but the conceptual foundation (content-addressed identity) should influence design decisions now. For example, `summary_hash` could become `content_hash` and cover the entire file, not just the body. The Git object model is the single most underutilized design pattern in the current architecture.

#### Alternative 3: Hybrid Retrieval (DAG + Embeddings)

**Current design:** Pure DAG resolution. No embedding-based retrieval.

**Proposed alternative:** A two-phase retrieval model:
1. **DAG Phase (deterministic)**: `resolve` builds the causal closure via imports — exactly as now. This is the "skeleton."
2. **Associative Phase (probabilistic)**: Embeddings of all memory bodies are indexed (using a lightweight local model like all-MiniLM-L6-v2). When resolve completes, the embeddings of the resolved context are used to query for **laterally related** memories that share no explicit imports but are semantically adjacent. These are appended as a "You might also want to consider..." section.

The key design decision: **the associative phase never replaces or reorders the DAG output.** It is strictly additive and clearly labeled. The DAG output remains the authoritative context; embedding suggestions are "further reading."

**Tradeoff analysis:**

| Dimension | DAG-Only | DAG + Embeddings |
|-----------|----------|------------------|
| Determinism | Full | Core output deterministic; suggestions non-deterministic |
| Dependency | None beyond pyyaml | Requires embedding model (~90MB for all-MiniLM) |
| Cold start | Requires explicit imports | Embeddings work from creation |
| Quality of suggestions | High precision, unknown recall | High recall, lower precision |
| Token budget | All budget for DAG | Split between DAG output and suggestions |
| Implementation | Current | New module: embed.py, embedding index in .codememory/ |

**Verdict:** This is the most pragmatic path to address the "associative recall" gap without compromising the DAG-first philosophy. The embedding model can be optional (feature-gated). The `suggest-deps` command already approximates this via tag overlap — embeddings would be a strictly better signal.

### 4.2 Concept Reorganization Proposals

#### Proposal: Unify `status`, `maturity`, and `intensity` into a "Memory Vitality" Model

**Current state:** Three separate fields that partially overlap:
- `status`: lifecycle state (active, archived, superseded)
- `maturity`: knowledge confidence (draft, verified, proven)
- `intensity`: subjective importance (1-10, >=8 = protected)

**Proposed reorganization:**

```
vitality:
  state: active | dormant | archived    # lifecycle
  confidence: draft | verified | proven  # epistemic status
  importance: 1..10                      # subjective weight (replaces intensity)
  protection: none | protected | locked  # explicit, not derived from importance
```

Why this is better:
- `state` and `confidence` are cleanly separated — you can have a verified belief that is dormant
- `protection` is explicit, not derived from an importance heuristic
- All vitality-related fields are grouped under one namespace, making the conceptual model clearer

**Tradeoff:** Schema change. Requires migration of existing data. The conceptual clarity gain may not justify the migration cost at this stage.

#### Proposal: Edge-First Memory Model

**Current state:** Memories are nodes; imports are simple string references on nodes.

**Proposed reorganization:** Edges are first-class entities, stored alongside memories.

```yaml
# .codememory/edges/edge_a3f2e1d.yaml
source: user/investment/february-buy
target: user/investment/risk-tolerance
type: required
pin: v1
reason: "决策基于当时的激进风险偏好（v1）"
strength: 0.9
created: 2026-02-15
created_in_session: "#a3f8c2"
```

This has three immediate benefits:
1. **Bidirectional queries become O(1)** — finding all memories that depend on X is a lookup, not a full scan
2. **Edge metadata is extensible** — add `strength`, `validated`, `deprecated` to edges without changing the memory schema
3. **DAG operations are faster** — build_dag can directly query edges rather than scanning all memories' imports

**Tradeoff:** Moves from single-source-of-truth (`.md` files) to dual-source (`.md` files + edge store). This breaks the "everything is a Markdown file" purity but dramatically improves graph operation performance.

### 4.3 Tradeoff Matrix

| Proposal | Simplicity | Power | Migration Cost | When Worth It |
|----------|-----------|-------|---------------|---------------|
| Activation decay (replace heat) | +1 | +2 | 0 (formula change) | Immediately |
| Content-addressed Merkle DAG | -2 | +3 | High (new storage layer) | Production multi-agent deployment |
| DAG + Embeddings (hybrid) | -1 | +2 | Medium (new dependency) | When cold-start/unconnected data becomes a pain point |
| Edge-first memory model | -1 | +3 | High (data model change) | When DAG operations hit performance limits |
| Unified vitality model | 0 | +1 | Low (field rename) | When user confusion about status/maturity/intensity is observed |

### 4.4 Inspiration Bombs

These are "what if we did something completely different" ideas. Not necessarily practical, but directionally provocative.

#### Bomb 1: "Memory Diffing" — Treat Memory Evolution as a First-Class Operation

**The idea:** Instead of just tracking `version: 1 -> 2 -> 3` in changelog, compute the **semantic diff** between versions and store it as a structured artifact. When resolving, the agent can see not just the current state but "what changed from v1 to v2 and why."

This would enable: "Show me how my investment thesis evolved between January and March" — not as two separate resolves, but as a single diff-aware resolve that highlights changes.

The Git analogy is `git log -p` — not just what commits exist, but what each commit changed. Currently, CodeMemory has commit messages (`change_note`) but no diffs.

#### Bomb 2: "Memory as a Lattice, Not a Tree" — Formal Concept Analysis

**The idea:** Instead of a single DAG rooted at an entry point, model the memory space as a **concept lattice** (Formal Concept Analysis). Each memory is a formal concept with intension (its attributes: tags, schema, maturity) and extension (the set of memories that share those attributes). The lattice structure naturally reveals:
- **Generalization** (more abstract concepts that subsume specific ones)
- **Specialization** (more specific instances)
- **Meet/Join** (the least general generalization of two concepts; the most general specialization)

This is a fundamentally different mental model from dependency resolution. Instead of "what does A depend on?", the question becomes "what is the conceptual neighborhood of A?" and "what is the most abstract concept that covers both A and B?"

This maps to how humans actually recall: not by tracing dependency chains, but by navigating conceptual spaces. "Oh, semiconductor thesis? That's an investment thesis — I have a risk tolerance and a preferences file that are related because they're all in the investment space."

#### Bomb 3: "Forgetting as Compression, Not Deletion" — Summarization-Based Forgetting

**The idea:** Instead of marking memories as archived or warning about decay, implement **progressive summarization** as the forgetting mechanism. A memory that hasn't been accessed in 6 months gets automatically summarized (by an LLM) into a shorter form. After 12 months, the summary is further compressed. The original is never deleted, but the "active" version that gets loaded into context is the progressively compressed summary.

This is inspired by how human long-term memory works: we don't delete episodic memories; we consolidate them into semantic summaries. You don't remember every detail of every meeting from last year, but you retain the gist. The gist is what comes to mind first; the details require effortful retrieval.

This would give CodeMemory a true "forgetting" mechanism that is:
- **Graded** (not binary)
- **Reversible** (the original is always available with sufficient effort/budget)
- **Automatic** (no user action required)
- **Token-efficient** (compressed memories take less context space)

---

## Prioritized Research Directions

### High-Impact, Low-Effort (Consider for current/next iteration)

1. **Replace static `heat` with time-decayed activation for `overview`.** Change the formula in `handle_overview` from `dependents * 10 + access_count` to a recency-weighted function. This is a ~20 line change with significant impact on the quality of session-start context injection.

2. **Add "associative suggestions" section to `resolve` output.** After the DAG output, append a section showing memories that share tags but aren't in the import chain. This uses existing tag data — no new infrastructure needed. It partially addresses the associative recall gap.

3. **Precompute `in_degree` (dependents count) in the index.** Store `dependents: int` on each MemoryEntry in index.json, computed during reindex. This eliminates the O(n^2) scan in search/overview/validate and is a prerequisite for scaling to large datasets.

4. **Add tool annotations to MCP server.** Mark `resolve_memory`, `overview`, `wander`, `focus` as `read-only` and `snapshot` as `destructive` in the tool definitions. This enables MCP clients to implement safety guardrails.

### High-Impact, High-Effort (Backlog for future iteration)

5. **Implement hybrid DAG + embedding retrieval.** Add an optional embedding index using a lightweight local model. The embedding layer serves as a suggestion engine for associative recall, never replacing the DAG output. Feature-gate it — the system works without it.

6. **Design content-addressed memory identity (Merkle DAG).** Start with a design document specifying how content addressing would work alongside the existing path-based model. The implementation is significant, but the design decisions (hash scope, reference management, GC policy) should be made early to avoid painting into a corner.

7. **Edge-first data model with in-degree precomputation.** Move import relationships to a dedicated edge store, compute in-degree at index time, and enable O(1) reverse dependency queries. This is a prerequisite for efficient impact analysis and graph analytics.

### Thought-Provoking (Long-term research)

8. **Progressive summarization as forgetting.** Explore an LLM-driven pipeline that periodically summarizes low-access memories. Develop heuristics for when to summarize, how aggressively, and how to preserve the ability to "re-expand" a summary to full detail.

9. **Concept lattice navigation as an alternative to DAG traversal.** Prototype a Formal Concept Analysis-based navigation interface that treats the memory space as a lattice of concepts rather than a dependency graph. This would be an alternative view, not a replacement.

10. **Persistent session DAG with TTL.** Extend TransientDAG to survive process restarts, with time-to-live expiration. This enables multi-session reasoning chains without cluttering the persistent memory space.

### Wild Ideas (High-risk, potentially game-changing)

11. **Memory diffing as structured artifacts.** Instead of tracking version numbers, compute semantic diffs between memory versions and store them as queryable artifacts. An agent could ask: "What changed in my investment thinking between January and April?" and get a structured answer.

12. **"Branching" for speculative reasoning.** Apply Git's branch model to memory: an agent can branch the entire knowledge state, explore a "what if" scenario (e.g., "what if I had higher risk tolerance?"), and either merge the results back or discard the branch. This would make CodeMemory not just a memory system but a **cognitive simulation environment**.

---

## Appendix: Research Sources

- Stocco, Rice, Thomson, Smith, Morrison & Lebiere (2024). "An Integrated Computational Framework for the Neurobiology of Memory Based on the ACT-R Declarative Memory System." *Computational Brain and Behavior, 7(1), 129–149.*
- Lebiere et al. (2024). "Cognitive Models for Machine Theory of Mind." *Topics in Cognitive Science, 17(2), 268–290.*
- de Jong, Wilhelm & Akyurek (2024). "Adaptive Forgetting Speed in Working Memory." *Psychonomic Bulletin & Review, 31, 2704–2713.*
- Kim et al. (2024). "Temporal Knowledge-Graph Memory in a Partially Observable Environment." arXiv:2408.05861.
- Zeng, Fang, Liu, Meng (2024). "On the Structural Memory of LLM Agents." arXiv:2412.15266.
- Microsoft GraphRAG (2024). https://microsoft.github.io/graphrag/
- Klavis. "Less is More: 4 Design Patterns for Building Better MCP Servers." https://www.klavis.ai/blog/less-is-more-mcp-design-patterns-for-ai-agents
- TerminusDB — "Git for Data." https://github.com/terminusdb/terminusdb
- indra_db — "Git for Knowledge Graphs." https://crates.io/crates/indra_db
- Semem — Semantic Web Memory for Intelligent Agents. https://github.com/danja/semem
- Roam Research vs Obsidian bidirectional linking analysis (少数派, 2024). https://sspai.com/post/92329
