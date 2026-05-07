# CodeMemory Design Research Audit — Round 12 Post-Mortem

**Reviewer:** Product Research Reviewer
**Date:** 2026-05-07
**Trigger:** Round 12 introduces ACT-R time-decay activation (heat formula `deps*10 + access*0.5^(days_since/14)`). This audit asks: is this the right direction, and what would a radical rethink look like?

**Method:** Full source review (resolve.py, handlers.py, models.py, index.py, validate.py, search.py, transient.py, orphans.py, suggest_deps.py, update.py, create.py, integrations.py) + adjacent domain research via WebSearch (3 domains: cognitive architectures, knowledge graphs, human memory models) + gap analysis + proposal synthesis.

---

## Executive Summary

Round 12's time-decay activation formula is a valid first step toward a richer memory lifecycle model — but it is a **local maximum**, not the destination. Three deeper findings reshape the design space:

1. **ACT-R's full activation model does something CodeMemory ignores entirely: spreading activation from context.** The current formula only models recency/frequency (base-level activation). A memory about risk tolerance should be "hotter" when the user is working on risk analysis — regardless of when it was last accessed. This contextual dimension is the single largest missing piece.

2. **The "memory = file" metaphor is already cracking under its own success.** TransientDAG nodes are memories with no file. Snapshots flatten internal topology. DAG edges carry rich semantics (required/recommended/related, pin versions, reasons) but are compressed to a single integer (dependents count) in the heat formula. The real memory is the graph topology, not the individual files.

3. **The FSRS community has solved a problem we are only beginning to touch.** FSRS models each memory unit with three parameters (Difficulty, Stability, Retrievability) that create a personalized forgetting curve. Its key finding — reviewing when retrieval probability is low maximizes learning — **inverts** CodeMemory's current design where frequent access = promoted.

**Biggest opportunity:** Shift from a one-dimensional heat ranking to a **three-dimensional memory state model** (structural x temporal x stability), enabling distinct "surfacing" vs "reviewing" vs "fading" operations.

**One-sentence direction:** Replace the global 14-day half-life with per-memory stability learned from access history; add context-dependent activation from tags/domain; and treat edges as first-class entities with their own lifecycle.

---

## Phase 1: Core Assumption Questioning

### 1.1 Assumption Inventory (7 examined)

| # | Assumption | Where It Manifests | Stress Test |
|---|-----------|-------------------|-------------|
| A1 | Memory = file (.md with frontmatter) | `create.py`, `index.py`, `resolve.py` | TransientDAG nodes are memories with no file; snapshot compresses topology |
| A2 | Heat = structural (dependents) + temporal (access decay) | `handle_overview()` in `handlers.py:256` | No spreading activation; no task-context awareness |
| A3 | Access frequency signals importance | `MemoryEntry.access_count`, `handle_overview()` | A memory accessed 50 times by accident is "hotter" than a critical one accessed 3 times intentionally |
| A4 | 14-day half-life is universal | `handle_overview():249` | Investment research and software architecture have different natural forgetting rates |
| A5 | Primary user is an AI agent | All CLI commands, MCP integration | Human users need temporal browsing, social sharing, visual navigation |
| A6 | Maturity moves forward only (draft->verified->proven) | `resolve.py:322-338` | A "proven" memory unaccessed for 2 years remains proven; no demotion path exists |
| A7 | Dependents count = structural importance | `handle_overview():256` (`deps * 10`) | One `required` import carries more semantic weight than ten `related` imports, but all count equally |

### 1.2 Deep Dive: The "Memory = File" Metaphor Under Stress

The file metaphor holds well for the core atom model: one conceptual unit, one file, one path. But it breaks in three emerging use cases:

**Break 1: Compound memories (TransientDAG).** `transient.py` defines in-process memory nodes never written to disk. When a session reasoning chain produces a conclusion depending on 4 intermediate steps, where is the "memory"? The 5 transient nodes existed in memory. The snapshot (`snapshot.py`) flattens them into one file — losing the internal topology. The file is a lossy compression of the actual memory structure.

**Break 2: The DAG edges are memories too.** An import like `{required: [user/risk/tolerance], pin: "v3", reason: "underpins all sector analysis"}` encodes a judgment with author, timestamp, rationale. This judgment IS a memory — but edges are stored as metadata on nodes, not as first-class entities. You cannot search for "all edges that were added in the last month" or "all edges with pinned versions that need review."

**Break 3: Version history is temporal memory.** `update.py` versions a file (v1->v2->v3). Version 3 of a memory represents an evolved understanding. But the index only stores one `MemoryEntry` per id. The temporal dimension of "how did my thinking change from v1 to v3?" is flattened into a version number and a changelog. The v1 DAG topology (which imports existed at v1) is lost — only the current topology is preserved.

**Assessment:** The file metaphor is excellent for the atom unit (stable, authored, versioned). It is strained for compound, relational, and temporal memory. The system needs a **second representation** for edges as first-class and temporal sequences as queryable — augmenting rather than replacing the file model.

### 1.3 Is Time Decay Enough?

Round 12 formula: `heat = deps*10 + access * 0.5^(days_since/14)`

This models **base-level activation** (B_i) from ACT-R — frequency and recency. But ACT-R's full activation equation has three more components:

```
ACT-R Full:  A_i = B_i(base-level) + S_i(spreading activation) + P_i(partial matching) + noise
CodeMemory:  heat = deps*10 + access * decay(days_since)
              ↕                ↕
         structural proxy   temporal recency
         (approximates B_i)  (B_i component only)
```

**What's missing:**

| ACT-R Component | Description | CodeMemory Equivalent | Status |
|----------------|-------------|----------------------|--------|
| Base-Level Activation: `ln(Σ t_j^(-d))` | Power-law sum over all access history | `access * 0.5^(days_since/14)` | Partially modeled — exponential instead of power-law, no sum over full history |
| Spreading Activation: context-dependent boost | Boost from active goal/context | None | **Missing entirely** |
| Partial Matching: relevance to retrieval request | Mismatch penalty for partial matches | None (search is binary substring) | **Missing entirely** |
| Retrieval Threshold τ: below this, can't retrieve | Functional forgetting boundary | None (all memories always reachable) | **Missing entirely** |
| Noise: logistic noise on retrieval | Probabilistic retrieval | None (deterministic) | Deliberately absent |

The biggest gap is **spreading activation from context**. When a user resolves `user/investment/context` (tagged: investment, risk, portfolio), the memory `user/risk/tolerance` (tagged: investment, risk) should receive a context-dependent activation boost through shared tags — regardless of when it was last accessed. The DAG captures structural relationships, but activation should also be **context-dependent**.

The second gap is the **decay function itself**. ACT-R uses power-law decay `t^(-d)` with d typically 0.5. CodeMemory uses exponential `0.5^(t/half_life)`. These behave differently:
- Power-law: long tail, preserves signal of sustained historical importance
- Exponential: sharp initial decay, near-zero after ~4-5 half-lives

For a memory accessed 1000 times 2 years ago:
- Exponential: `1000 * 0.5^(730/14) = 1000 * 2.0e-16 ≈ 0` (completely erased)
- Power-law (d=0.5): `1000 * (731)^(-0.5) ≈ 1000 * 0.037 = 37` (still meaningful)

The power-law better preserves the signal of sustained historical engagement.

### 1.4 Human User vs AI Agent — Design Collapse Points

If a human user opens CodeMemory directly (not through an AI agent), these assumptions break:

1. **Resolution = Token budget.** Humans don't think in token budgets. They think in "give me the gist" vs "show me everything." The `--budget` parameter is an agent-optimized concept.

2. **Overview as injection format.** `--format inject` produces `[id](type, heat:N)` — optimized for LLM system prompts. A human would want cards, timelines, or network views.

3. **No temporal-first navigation.** Humans think in timelines: "what was I working on last Tuesday?" The system has `created`/`updated` fields, but no "browse by date" interface.

4. **No collaboration primitives.** `evidence.contributors` and `source.created_by` exist but are vestigial — no multi-user conflict detection, no shared ownership.

5. **CLI semantics leak into UI.** `--depth required|recommended|full` is a CLI parameter. In the management panel, it maps to a Budget slider — a vastly different interaction model.

---

## Phase 2: Adjacent Domain Research

### 2.1 Domain 1: Cognitive Architectures (ACT-R, SOAR)

**Key sources:** ACT-R 7 reference (Carnegie Mellon), Pavlik & Anderson (2005) "Practice and Forgetting Effects," Laird (2022) "An Analysis and Comparison of ACT-R and Soar," Fisher, Houpt et al. (2025) "SFT-GMA framework for testing ACT-R core assumptions," MDPI Applied Sciences (2025) "Retrieving Memory Content from a Cognitive Architecture by Impressions from Language Models for Use in a Social Robot."

**Findings:**

1. **Power-law vs exponential decay.** ACT-R's canonical base-level activation is `B_i = ln(Σ t_j^(-d))` — a power-law sum over all past accesses. CodeMemory's single-exponential `0.5^(days_since/14)` decays faster initially. The power-law form has stronger empirical support for human memory.

2. **Pavlik-Anderson recursive decay (the spacing effect).** In the most important ACT-R variant, decay rate is NOT constant. `d_k = c * e^(m_(k-1)) + alpha` — decay **accelerates** when activation is high (producing the spacing effect: you need longer gaps between reviews). This creates a natural optimization: review items right before they are forgotten. CodeMemory has no mechanism to adjust decay rate based on current activation state.

3. **SOAR's explicit episodic memory.** SOAR separates episodic (temporal sequences) from semantic (general facts) memory. This maps to CodeMemory's TransientDAG (episodic) vs persistent atoms (semantic). SOAR's key mechanism: episodic traces are **mined** to create semantic knowledge through analogical generalization — exactly the pattern TransientDAG cannot currently do.

4. **SOAR's impasse-driven learning.** When SOAR doesn't know what to do, an "impasse" triggers subgoal reasoning and automatic knowledge creation (chunking). CodeMemory has no equivalent self-awareness — it cannot detect knowledge gaps in the memory graph.

5. **ACT-R + LLM integration (2025).** Recent research uses LLM-generated keywords to trigger ACT-R chunk retrieval in social robots. The LLM produces "impressions"; ACT-R retrieves matching chunks; this reduces hallucination. This is structurally similar to how CodeMemory could use an LLM to produce context keywords that then trigger spreading activation.

**Transferable patterns for CodeMemory:**

| Pattern | Source | Application |
|---------|--------|-------------|
| Spreading activation from buffer contents | ACT-R | Context-dependent heat boost: shared tags between current task and memory |
| Power-law activation `ln(Σ t_j^(-d))` | ACT-R | Replace exponential decay with power-law sum for more realistic long-tail behavior |
| Adaptive decay rate `d_k = c*e^m + alpha` | Pavlik-Anderson | Per-memory half-life that adjusts with access patterns |
| Episodic -> Semantic mining | SOAR | Auto-propose atom creation from recurring TransientDAG patterns |
| Impasse detection / knowledge gap | SOAR | Detect domains with high reference count but zero memories ("you depend on X but know nothing about it") |
| Chunking (compile subgoal solutions) | SOAR | Auto-collapse repeated resolve patterns into composite atoms |

### 2.2 Domain 2: Human Memory & Spaced Repetition (FSRS, SM-2, Leitner)

**Key sources:** Open Spaced Repetition community / FSRS-4.5 (2024), Jarrett Ye et al., Ebbinghaus (1885), Leitner (1972), Wozniak / SuperMemo, DRL-SRS (Xiao & Wang, 2024, Applied Sciences), DKVMN&MRI (PLoS ONE, 2024), "AI, Memorization, and Forgetting" (IERJ, 2024).

**Findings:**

1. **FSRS DSR model (Difficulty-Stability-Retrievability).** Each memory item has three continuous parameters:
   - **D (Difficulty):** [1, 10] — inherent difficulty, converges through practice
   - **S (Stability):** [0, +inf) — days for retrieval probability to drop from 1.0 to 0.9
   - **R (Retrievability):** [0, 1] — current probability of successful recall, `R(t) = 0.9^(t/S)`

   After each review, stability is updated: `S' = S * (1 + exp(-0.2*D) * gain(R_at_review))`. The gain is largest when R is moderate (~0.7-0.8) — the "desirable difficulty" sweet spot. This is the most validated open-source spaced repetition model, integrated into Anki as the default alternative scheduler.

2. **The counterintuitive optimization.** FSRS discovers that **reviewing when R is LOW maximizes stability gain, but also maximizes forgetting risk.** The optimal review balances these forces. For CodeMemory, this inverts current logic: a memory that is "cold" (low access, long gap since last access) might be at the **optimal review point**. The system should surface it for re-engagement, not bury it further.

3. **Leitner box model** — the simplest possible model: 5 boxes, correct answer moves up (longer interval), incorrect moves back to box 1. Creates an elegant self-correcting schedule with zero mathematical complexity. Formal queueing network analysis reveals sharp phase transitions in learning outcomes when new item introduction exceeds review capacity.

4. **DRL-SRS (2024).** Deep reinforcement learning (DQN) applied to spaced repetition scheduling — uses Ebbinghaus forgetting curve parameterization as the reward function. Achieves state-of-the-art schedule optimization. Validates that learning the optimal review policy per item is possible.

5. **Deep Knowledge Tracing + Ebbinghaus (2024).** DKVMN&MRI incorporates the Ebbinghaus forgetting curve directly into a neural knowledge tracing architecture, showing significant AUC improvements. Demonstrates that parameterized forgetting functions are essential for accurate memory modeling.

**Transferable patterns for CodeMemory:**

| Pattern | Source | Application |
|---------|--------|-------------|
| Per-memory Stability S | FSRS | Replace global 14-day half-life with learnable per-memory stability |
| Retrievability R(t) = 0.9^(t/S) | FSRS | Replace binary access_count with continuous probability of "being remembered" |
| Desirable difficulty scheduling | FSRS | Wander should target R ≈ 0.7 (optimal review), not just R ≈ 0 (coldest) |
| Leitner boxes as explicit tiers | Leitner | Implement Hot/Warm/Cold/Cool/Frozen tiers with clear transition rules |
| Phase transition in capacity | Leitner queueing | Warn when memory creation rate exceeds review capacity |
| Per-item difficulty estimation | FSRS | Track "forgetting rate": if a memory requires frequent re-access, it's "difficult" (low stability) |

### 2.3 Domain 3: Knowledge Graphs (Property Graph vs RDF)

**Key sources:** Neo4j knowledge graph documentation (2024), University of Murcia / L3S Hannover benchmark study (2024), Amazon Neptune Statement Graphs, ISO GQL standard (2024), Unified Knowledge Graph Model (Plain English, 2024).

**Findings:**

1. **Property graph model maps directly to CodeMemory's DAG.** Nodes = atoms/schemas (with properties: type, summary, tags, intensity, maturity). Edges = imports (with properties: strength, pin version, reason). CodeMemory's edge model is actually richer than basic property graphs by distinguishing three edge strengths — but edges still lack temporal metadata (added_date, deprecated_date) and are not independently queryable.

2. **Performance findings (2024 benchmark).** Neo4j (property graph) outperformed GraphDB (RDF) for simple-to-moderate queries with lower memory consumption. GraphDB was more memory-efficient for complex subgraph traversals. Key finding: query complexity impacts performance more than graph size. For CodeMemory, most queries (overview, wander, resolve) are moderate complexity — property graph approach is well-suited.

3. **Edges as first-class citizens.** Property graph databases store edges with independent properties, metadata, and identity. CodeMemory stores edge data in frontmatter (file-level) but the index flattens imports to raw dicts — edge metadata is preserved in the file but not queryable from the index. You cannot query "all required imports that were pinned and are now behind by 3+ versions."

4. **The "unified model" trend (RDF*, Statement Graphs, Domain Graphs).** The research community is converging toward models that treat both nodes and edges as first-class with independent properties. CodeMemory's architecture (nodes in index, edges in frontmatter) is a split model — unifying them would align with the trend.

5. **Transitive closure as precomputation.** RDF stores support ontological reasoning (transitive inference). CodeMemory's DAG traversal computes transitive dependencies at resolve time but never **precomputes** them. A materialized transitive closure would make overview/wander/validate O(1) for dependency queries rather than O(n) BFS.

**Transferable patterns for CodeMemory:**

| Pattern | Source | Application |
|---------|--------|-------------|
| First-class edge properties with independent metadata | Property Graph | Index imports as separate entities with added_date, deprecation status, pin history |
| Incremental indexing (change detection) | Graph DB | Reindex only changed files using hash-based change detection |
| Transitive closure precomputation | RDF Inference | Precompute "all ancestors" and "all descendants" for each node |
| Graph query language (Cypher/GQL) | ISO GQL | `codememory query "MATCH (a)-[:required]->(b) WHERE b.maturity='proven'"` |
| Graph-native storage backend | Neo4j/DuckDB | Research: replace index.json with embedded graph database at 10k+ memory scale |

### 2.4 Cross-Domain Synthesis: Three Axes of Memory State

Synthesizing across all three domains, a memory's state is best characterized along three independent axes:

```
                    STRUCTURAL IMPORTANCE
                    (how connected? weighted
                     incoming edges + PageRank)
                         ▲
                        /|\
                       / | \
                      /  |  \
                     /   M   \
                    /    E    \
                   /     M     \
                  /      O      \
                 /       R       \
                /        Y        \
               ◄───────────────────►
          TEMPORAL RECENCY       KNOWLEDGE STABILITY
      (FSRS retrievability:     (how fast does it fade?
       R = 0.9^(days/S))         per-memory S parameter)
```

| Axis | Current Model (R12) | Rich Model (from research) |
|------|---------------------|---------------------------|
| **Structural** | `dependents * 10` (flat count, no strength weighting) | Weighted incoming edges: required=5, recommended=3, related=1 + transitive PageRank on DAG |
| **Temporal** | `access * 0.5^(days/14)` (exponential, global half-life) | FSRS retrievability `R = 0.9^(days/S)` with per-memory stability S |
| **Stability** | Not modeled (constant 14-day half-life for all) | Per-memory S, updated on each access via FSRS formula; converges to domain-specific value |

**The operational sweet spot:** Each axis creates distinct "attention zones" for different system behaviors:

- High structural + High temporal + High stability = **Pillars** (core of current work — always surfaced)
- High structural + Low temporal + Low stability = **Review targets** (important but fading — needs re-engagement)
- Low structural + Low temporal + High stability = **Fragile gems** (important to someone, but unlinked — needs imports)
- Low structural + Low temporal + Low stability = **Candidates for archiving** (not connected, not accessed, not stable)

---

## Phase 3: Logical Completeness

### 3.1 Conceptual Coherence After R12

Time-decay activation (R12-UX5) changed overview output's semantic meaning while leaving wander, stale detection, and validate unchanged. This creates inconsistencies:

| Component | Pre-R12 Logic | Post-R12 Logic | Coherence Gap |
|-----------|--------------|----------------|---------------|
| **Overview** | Top 5 by dependents + raw access | Top 5 by `deps*10 + access*decay` | Internally consistent; ranks recency over raw frequency |
| **Wander (cool)** | Weighted by `1/(access_count+1)` | Unchanged — uses raw access_count | Wander ignores time decay. A memory accessed 50 times 2 years ago (heat ~0) is treated as "hot" and excluded from cool mode. Inconsistent. |
| **Stale detection** | body hash mismatch flag | Unchanged | Stale flag doesn't affect heat. A stale memory with high dependents ranks high in overview despite being out-of-date. No feedback loop. |
| **Validate (decay)** | 30-day threshold in `_check_decay()` | Unchanged — hardcoded 30-day window | Uses a binary 30-day window while overview uses a continuous exponential function. Two different decay models in one system. |
| **Maturity auto-upgrade** | access_count >= 3 -> verified | Unchanged — uses raw access_count | No recency consideration. 3 accesses in one day (burst) triggers "verified." 2 accesses over 3 years stays "draft." |

**Critical inconsistency:** `validate.py:_check_decay()` uses `last_access > now - 30 days` as a binary threshold. `handle_overview` uses `0.5^(days_since/14)` as a continuous decay. If the decay formula is the chosen model, validate should derive its warning from it — e.g., `retrievability < 0.3` rather than `days > 30`.

### 3.2 Extreme Scenario Analysis

**Scenario 1: All-zero-access memories (fresh dataset import).**
- Heat = deps * 10 + 0 (access_bonus = 0 * 0.1 = 0)
- All memories rank by structure only. This is defensible.
- But: after first resolve, one memory gets access_count=1 with fresh last_access. Its heat jumps `deps*10 + 1.0`. This is a discontinuity — the access_bonus goes from 0 to 1 in one access. Better: give zero-access memories a floor of 0.5 rather than 0.

**Scenario 2: One memory accessed 1000 times, 2 years ago.**
- Exponential: `1000 * 0.5^(730/14) = 1000 * 2.0e-16 ≈ 0` — completely erased
- The memory may have been genuinely important for 2 years. A power-law `1000 * (731)^(-0.5) ≈ 37` preserves the signal.
- Implication: exponential decay over-erases sustained historical importance. Consider power-law or a hybrid (exponential for recent, power-law tail for historical).

**Scenario 3: 10,000 memories, frequent overview calls.**
- Current loop: search (O(n) tag matching) -> for each result: datetime.fromisoformat + math.pow -> sort -> take top k.
- At 10k memories with rich tags, search could return 5k matches. datetime.fromisoformat per memory is the bottleneck.
- Mitigation options: (a) precompute days_since_last_access as an integer in the index, (b) two-phase approach: compute heat only for top 50 structurally-ranked results, (c) cache heat values until next access event.

**Scenario 4: Circular dependency + time decay interaction.**
- A 3-node cycle A->B->C->A gives each node `dependents = 1`, multiplied by 10 = 10 heat structural contribution.
- But these are structurally broken — none are resolvable in practice. Dependents count should exclude cycle participants.

### 3.3 Operational Gaps

| Operation | Current | Gap |
|-----------|---------|-----|
| **Overview with --tags** | Filters search, computes heat | Heat formula is tag-agnostic. Matching tags should provide context boost (spreading activation). |
| **Wander mode=cool** | `1/(access_count+1)` weight | Should use decayed access, not raw — otherwise old high-frequency memories are never surfaced |
| **Validate decay check** | Hard 30-day binary threshold | Should use the same decay formula as overview (retrievability threshold) |
| **Reindex** | Full directory scan every time | Should be incremental: hash file mtime + body, only reparse changed files |
| **Focus --resolve** | Delegates to resolve(depth=recommended) | Should include active transient session nodes if a session is in progress |
| **Snapshot** | Flattens TransientDAG to single file | Should preserve internal DAG topology as structured imports in the snapshot |
| **Suggest-deps** | score = tag_overlap*3 + schema_score*5 + dependents | Should incorporate heat: higher-heat candidates are more "active" and thus better deps |

### 3.4 Evolution Bottlenecks

**Bottleneck 1: Index.json as single serialization point.** Every resolve increments access_count and saves the entire index. At 10k memories with rich metadata, index.json could reach 5-10 MB. Every access event triggers a full save. Solution: batch access_count writes or use an append-only journal.

**Bottleneck 2: No version history in the graph view.** When a memory is updated (v2 -> v3), old imports may be removed. The v2 DAG topology is lost — only the current index reflects current imports. This prevents graph diffs and temporal queries like "what did my dependency structure look like in January?"

**Bottleneck 3: Single-machine, single-user by design.** File-based architecture assumes local filesystem. No multi-user collaboration path, no sync. The MCP server runs locally. Deliberate constraint (portability over collaboration) but limits future market.

---

## Phase 4: Alternative Design Proposals

### 4.1 Core Mechanism Alternatives

#### Alternative A: FSRS-Style Stability Model (Replaces time decay)

**Current (R12):**
```python
heat = deps * 10 + access * 0.5^(days_since / 14)
```

**Proposed (FSRS-inspired):**
```python
# New fields on MemoryEntry
stability: float = 14.0       # days for R to drop from 1.0 to 0.9 (initially = half-life)
difficulty: float = 5.0       # [1, 10], converges through access patterns

# On each access, update stability:
R_at_review = 0.9^(days_since / stability)
post_stability = stability * (1 + exp(-0.2 * difficulty) * 10 * max(0, 1 - R_at_review))
difficulty = difficulty - 0.1 * (access_quality - 3)  # 1=forced, 3=neutral, 5=organic

# Heat becomes:
retrievability = 0.9^(days_since / stability)
heat = deps * 10 + stability * retrievability
```

**Why better:**
- Personalized per memory — investment research fades differently than software architecture
- Burst access handled naturally: multiple accesses in one day produce minimal gain (R was already near 1.0)
- "Desirable difficulty": reviewing when R is moderate maximizes stability gain
- Produces a "next review" date: `next_review = now + stability * ln(0.9) / ln(target_R)`
- FSRS has strong empirical validation (20-30% fewer reviews for same retention vs SM-2)

**Cost:** +2 float fields on MemoryEntry, per-access stability update logic, slightly more complex overview computation.

#### Alternative B: Leitner Box Model (Replaces continuous heat with discrete tiers)

**Proposed:**
```python
# 5 explicit tiers
Tier 1 (Hot):   active in current session, auto-resolved on startup
Tier 2 (Warm):  accessed in last 7 days, full attention
Tier 3 (Cool):  accessed in last 30 days, summary only
Tier 4 (Cold):  accessed 30+ days ago, wander/search only
Tier 5 (Frozen): archived/superseded, never surfaced automatically

# Transition rules:
# - On access: promote one tier (ceil)
# - No access for threshold[tier] days: demote one tier
thresholds = {1: 2, 2: 7, 3: 30, 4: 90, 5: float('inf')}
```

**Why better:**
- Drastically simpler for users: no heat numbers, just "this lives in your Warm box"
- Gamification natural: "You have 12 memories in Cold. Review 3 to warm them."
- Self-correcting: predictable, debuggable behavior
- Distinct visual treatment per tier in the management panel

**Why worse:**
- Loses fine-grained ranking within tiers
- Hard boundaries create edge effects (29 vs 31 days = tier change)
- Less mathematically grounded

**Verdict:** Use FSRS as the mathematical engine, Leitner tiers as the presentation metaphor. Compute per-memory stability and retrievability via FSRS, but display them as "Hot (5) / Warm (12) / Cold (8) / Frozen (3)."

#### Alternative C: Graph-Native Storage (Replaces files with embedded graph DB)

**Proposed:** Store memories in an embedded graph database (SQLite + graph extension or DuckDB with recursive CTEs). Memories and imports are nodes and edges directly. No reindex step, no file parsing, native graph queries.

**Why better:**
- Incremental updates (only changed nodes/edges recomputed)
- "Find all nodes transitively depending on X" = one query
- Edge properties first-class and queryable
- Scales to 100k+ memories

**Why worse:**
- Loses filesystem portability (can't `ls`, `git diff` individual memories)
- Adds a dependency (embedded graph DB)
- Breaks "each .md is a memory" simplicity

**Verdict:** This is a Phase 3 (distant future) consideration. The file model is strategically important now. But the system should be designed with a pluggable storage abstraction so the backend can be swapped without changing the cognitive model.

### 4.2 Conceptual Reorganization: Three-Dimensional Memory State

Replace the single `heat` integer with a state triple:

```python
class MemoryState(BaseModel):
    structural_score: float     # weighted incoming edges + PageRank
    retrievability: float       # R = 0.9^(days_since / stability)
    stability: float           # learned half-life from FSRS
```

Each operation uses a different projection:

| Operation | State Projection | Rationale |
|-----------|-----------------|-----------|
| **Overview (surfacing)** | structural_score * retrievability | Surface well-connected, currently relevant memories |
| **Wander (cool recall)** | 1 / retrievability | Find memories at risk of being forgotten |
| **Wander (optimal review)** | retrievability ≈ 0.7 | Find memories at FSRS optimal review point |
| **Resolve (ordering)** | structural_score (deps before dependents) | Topological order with strength weighting |
| **Validate (decay)** | retrievability < 0.3 AND structural_score < 0.2 | At-risk memories for archiving or re-linking |
| **Focus (context display)** | All three dimensions shown | Full state awareness |
| **Suggest-deps** | structural_score weighted by retrievability | Active, well-connected memories are better dependency candidates |

### 4.3 Memory Lifecycle with Demotion

Current model: draft -> verified -> proven (forward only).

Proposed lifecycle with demotion paths:

```
[Create] ──> DRAFT ──access≥3──> VERIFIED ──access≥10+deps>0──> PROVEN
                ▲                    ▲         ▲                        │
                │                    │         │                        │
                │   imports broken   │  18mo   │   all deps            │  12mo
                │   or body stale    │  no     │   superseded           │  no
                │                    │  access │                        │  access
                │                    │         │                        │
                └────────────────────┴─────────┴────────────────────────┘
                                    DEMOTION PATHS
```

Demotion rules:
- PROVEN -> VERIFIED: 12 months without access (validate warns at 365 days already)
- VERIFIED -> DRAFT: all imports broken or summary stale for 90+ days
- Any -> SUPERSEDED: explicit user action (already exists)
- SUPERSEDED -> ACTIVE: explicit user re-activation

This makes maturity a true lifecycle reflecting the marriage of structural integrity and temporal engagement.

### 4.4 Tradeoff Matrix

| Dimension | Current (R12) | Alt A: FSRS Stability | Alt B: Leitner Tiers | Alt C: Graph DB |
|-----------|---------------|----------------------|----------------------|-----------------|
| Implementation cost | Baseline | +2 fields, stability math (~50 LOC) | +1 tier field, threshold logic (~30 LOC) | New storage layer (~500+ LOC) |
| Mathematical grounding | Medium (ACT-R inspired) | High (FSRS, peer-reviewed) | Low (heuristic) | N/A (storage only) |
| User understandability | Medium (heat number) | Low (stability is abstract) | High (boxes are intuitive) | Transparent |
| Personalization | None (global half-life) | High (per-memory stability) | Low (global thresholds) | N/A |
| Portability/Git-friendliness | High | High (same file model) | High (same file model) | Low (binary DB) |
| 10k+ memory scalability | Medium (O(n) per overview) | Medium (more computation per item) | Medium (less computation per item) | High (native queries) |
| Backward compatibility | — | High (additive fields) | High (additive field) | Low (migration) |
| Synergy with DAG resolution | Medium | Medium | Medium | High (native graph traversal) |

**Recommended path:** Adopt Alternative A (FSRS) as the math engine, present results through Alternative B (Leitner-style tiers) in the UI. This gives mathematical rigor under the hood with user-friendly presentation on the surface.

### 4.5 Inspiration Bombs

#### Bomb 1: The Memory Compiler

**Core idea:** The DAG is not a visualization. It is a **program**. Resolution is compilation.

In a compiler pipeline: source files (.md) → AST (index) → dependency analysis (imports) → linking + optimization (topological sort + token budget) → executable output (system prompt).

**What this changes:**
- **Type checking:** A memory tagged `decision` importing only `observation` memories (missing `analysis` or `criterion`) = type error. The compiler suggests missing dependency types.
- **Dead code elimination:** Orphaned low-intensity memories are "unreachable code." The compiler warns.
- **Optimization passes beyond token budget:** inline expansion (embed dependency summaries), constant folding (precompute stable cross-references), loop detection (cyclic imports = infinite loop).
- **Linking errors:** Importing a non-existent memory = undefined symbol error at "compile time" (validate already does this, but the metaphor unifies it).
- **Hot reload:** When a dependency updates, all dependents marked stale = incremental build (Makefile semantics).

**Killer feature:** `codememory build` — compile the entire graph into a single optimized, type-checked system prompt in one command. Fail with clear compiler-style error messages if the graph doesn't compile.

#### Bomb 2: Forgetfulness as a Feature

**Core idea:** Current assumption: forgetting is failure, should be prevented. Counter-assumption: **intelligent forgetting is essential for knowledge quality.**

Cognitive science (ACT-R, SOAR) shows forgetting serves critical functions:
- **Abstraction:** Forgetting details forces generalization — the principle is remembered, not the specifics
- **Resource allocation:** Not everything deserves to be remembered
- **Reconsolidation:** Each recall slightly modifies the memory; over time, memories become more useful (and less perfectly accurate)

**What this changes:**
- **Auto-archive by retrievability:** When R < 0.05 for 90 consecutive days, propose archiving with user notification
- **Summary distillation:** Before archiving, generate a 3-line "essence" and inject it as a `derived_from` note into all memories that imported the archived one. The detail is forgotten; the insight is preserved.
- **Reconsolidation tracking:** Version updates record not just "what changed" but "how my understanding shifted" — this becomes the most valuable content
- **Forgetting curve as audit trail:** R(t) for each memory reveals which memories were "sticky" vs "brittle." The system learns which types of memories tend to persist.

**Killer feature:** `codememory distill <id>` — extract essence from an archived memory, inject it into dependent memories, then remove the original. Signal preserved, noise discarded.

#### Bomb 3: Context-Aware Activation (Spreading Activation Engine)

**Core idea:** The heat formula is static. Every memory has one heat score. But a memory's relevance depends on what the user is currently working on. A memory about risk tolerance should be "hotter" when the user resolves `investment/context`.

**Implementation sketch:**
```python
def context_aware_heat(memory, active_context_tags, active_context_memories):
    base_heat = deps * 10 + access * 0.5^(days_since / stability)

    # Spreading activation from context
    context_boost = 0
    for context_memory_id in active_context_memories:
        if memory.id in index.memories[context_memory_id].imports:
            # This memory is a dependency of what the user is working on
            context_boost += 5  # structural relevance

    # Tag overlap with current context
    tag_overlap = len(set(memory.tags) & active_context_tags)
    context_boost += tag_overlap * 3

    # Context-referenced memories get a boost
    context_boost += _count_context_references(memory, active_context_memories) * 2

    return base_heat + context_boost
```

This makes overview/wander/resolve **situationally aware** — the same memory has different activation depending on what the agent or user is currently doing. This is exactly what ACT-R's spreading activation component provides and what CodeMemory currently lacks.

#### Bomb 4: Memory as a Garden Ecosystem

**Core idea:** Replace the library-catalog metaphor with a **garden ecosystem** metaphor. Memories are not books to be catalogued — they are plants in various states of growth.

In a garden:
- Some plants are in season (hot, actively growing — need daily attention)
- Some are dormant (cold, alive but not growing — check occasionally)
- Some cross-pollinate (new imports between domains = cross-pollination)
- Some die and become compost (archived, their nutrients feed new growth)
- The gardener walks through and **observes** — they don't "search" a catalog

**What this changes:**
- The overview becomes "the state of your garden" — not a query result, but ambient awareness
- Access count becomes a growth metric, not a frequency counter
- Wander becomes seasonal rotation — different memory domains come into focus on weekly cycles
- Archive becomes composting — essence extracted, injected into dependents, original decomposed

**Killer feature:** "Weekly Memory Digest" — an auto-generated report: which memories grew (new versions), which were pruned (archived), which cross-pollinated (new imports between domains), which are wilting (need review), and which sprouted (newly created).

---

## Prioritized Research Directions

### High-Impact, Low-Effort

**1. Unify decay models across overview, wander, and validate.**
Replace the hard 30-day threshold in `validate.py:_check_decay()` with the same exponential/power-law formula used in overview. Replace wander's raw `access_count` weight with decayed access from the same formula. One decay model, used everywhere. ~20 LOC change across two files.

**2. Exclude cycle participants from dependents count.**
In `_count_dependents()` (search.py) and `handle_overview()`: when counting incoming references, skip nodes that participate in a cycle with the target. Prevents structurally misleading heat scores for unresolvable memories. ~15 LOC change.

**3. Precompute `days_since_last_access` in the index.**
Store as integer in `MemoryEntry`, updated on each access. Avoids the most expensive operation in the overview O(n) loop — datetime.fromisoformat per memory. ~5 LOC for the field, ~3 LOC for the update, ~1 LOC replacement in overview.

**4. Add a `stability` field to MemoryEntry (default 14.0).**
This single field enables per-memory half-life without changing the core formula: `heat = deps*10 + access * 0.5^(days_since / stability)`. Initially all 14.0 (backward compatible). Migrate to per-memory values in future rounds. ~5 LOC for field definition, ~3 LOC formula change in overview.

### High-Impact, High-Effort

**5. Implement spreading activation from tag context.**
When `overview --tags "investment,risk"` is called, boost heat for memories that share those tags: `context_boost = shared_tags * 5`. This adds the spreading activation dimension from ACT-R. Requires tag comparison in the overview loop. ~30 LOC.

**6. Build FSRS-style per-memory stability updates.**
On each access (resolve, focus, explicit review), update memory.stability and memory.difficulty using the FSRS-4.5 formulas. Over time, frequently-reviewed memories develop high stability (slow decay) and rarely-reviewed critical memories show low stability (fast decay — needs check-ins). Most transformative improvement. ~80 LOC across handlers and models. Requires schema migration for two new fields.

**7. Memory tier visualization (Hot/Warm/Cold/Frozen).**
Compute FSRS retrievability and map to explicit tiers with distinct visual treatments in the management panel: Hot (R > 0.7, auto-surfaced), Warm (0.3 < R <= 0.7, summary display), Cold (0.1 < R <= 0.3, wander/search only), Frozen (R <= 0.1, archived or dormant). Bridges mathematical model with user-friendly metaphor. ~100 LOC frontend + ~30 LOC backend.

### Thought-Provoking

**8. The Memory Compiler metaphor.** Reframe `resolve` as `compile` — a pipeline with type checking, linking, optimization, and executable output. Unifies validate (type checking), resolve (compilation), and stale detection (incremental build). Opens design space for optimization passes beyond token budget. Primarily a metaphor/positioning shift with architectural implications.

**9. Episodic-to-semantic mining.** Track recurring TransientDAG patterns. When the same reasoning chain appears N times across sessions, propose creating a schema atom that formalizes it. SOAR's chunking mechanism applied to CodeMemory. Requires TransientDAG pattern storage (not currently persisted).

**10. Demotion path for maturity.** Add explicit downgrade: proven -> verified (12 months no access, already warned by validate), verified -> draft (all imports broken for 90 days). Makes maturity a true lifecycle reflecting both structural integrity and temporal engagement. Requires ~30 LOC in maturity check logic + frontend indicator.

### Wild Ideas

**11. Auto-archiving with essence distillation.** When R < 0.05 for 90 consecutive days, automatically propose archiving. Before archiving, use the MCP-connected LLM to generate a 3-line essence of the memory body. Inject this essence as a `derived_from` note into all memories that import the archived one. The detail is forgotten; the insight is preserved. Intelligent forgetting as resource management.

**12. Weekly Memory Digest.** Auto-generated report (markdown, optionally injected into agent context): which memories grew this week (new versions), which cross-pollinated (new inter-domain imports), which are wilting (R dropping below 0.3), and which sprouted (newly created). Transforms CodeMemory from a passive store into an active cognitive partner that reflects the user's own thinking patterns back at them.

---

*End of research audit report. Generated 2026-05-07. Adjacent domains researched: ACT-R/SOAR cognitive architectures (base-level activation, spreading activation, Pavlik-Anderson recursive decay, episodic/semantic separation), FSRS/spaced repetition/forgetting curves (DSR model, Leitner boxes, Ebbinghaus parameterization, DRL-SRS), property graph vs RDF knowledge graph models (performance benchmarks, edge-first-class, transitive closure, unified models).*
