# CodeMemory Design Research Audit — Round 13 Post-Mortem

**Reviewer:** Product Research Reviewer
**Date:** 2026-05-07
**Build:** Post-Round 13 (10/11 FULL PASS + 1 PARTIAL PASS per EVAL.md)
**Method:** Full source review (models.py, handlers.py, resolve.py, validate.py, search.py, index.py) + adjacent-field web research (FSRS v4-v6, Ebbinghaus forgetting curves / Radvansky 2024 meta-analysis, Duolingo HLR half-life regression, recommender systems: CF-KAN, knowledge-graph CF) + logical edge-case analysis (stability=0, negative, None; data plumbing verification; cross-system interaction audit)

---

## Executive Summary (6.5 / 10)

Round 13 made a conceptually correct and architecturally ambitious move: introducing a unified exponential decay formula `0.5^(days/stability)` anchored by a per-memory `stability` field (default 14.0 days) and precomputed `days_since_last_access`. This replaced three independent decay heuristics (overview flat 10%, wander raw count, validate 30-day binary threshold) with a single continuous model. The direction is right. The implementation is directionally correct but suffers from one blocking data-plumbing bug, three unexamined edge cases, and a design philosophy that stops at "uniform model" without reaching "differentiated model."

**Key findings:**

1. **Data plumbing bug (CRITICAL):** `handle_overview()` reads `days_since_last_access` from the search result dict (line 258) — but `search()` never includes this field in its output. The decay formula `0.5^(days/stability)` never activates in the overview path. All accessed memories fall back to the pre-R13 flat `access * 0.1` multiplier. The eval heat values (31, 31, 21, 21, 20) passed because they match the old formula, not because the new formula was verified. Contrast: `handle_wander()` correctly reads from `entry.days_since_last_access` (line 345) and works as designed.

2. **Uniform 14.0-day stability lacks empirical grounding.** Adjacent-field research shows memory half-lives span four orders of magnitude: hours (rote facts) to years (procedural skills). A single default is an arbitrary midpoint. The 2024 Radvansky meta-analysis (916 datasets) found no single function fits all content types — exponential, power-law, logarithmic, and linear functions each dominate different domains.

3. **High-frequency access paradox unresolved.** Memories accessed daily have `days_since=0` → `decay=1.0` perpetually. Their overview heat climbs monotonically. Wander's "cool mode" correctly gives them minimal weight, but there is no mechanism to detect or discourage "over-access" — a memory reviewed daily provides near-zero new learning benefit (massed practice regime per spacing effect research).

4. **Three edge cases unguarded:** stability=0 (ZeroDivisionError → crash), stability<0 (decay>1.0 → nonsensical), and `days_since_last_access=None` semantics inconsistent between overview (treated as 0, accidental) and wander (treated as max weight, intentional).

**Research Contribution (7.0/10):** The stability field + unified formula is the right abstraction at the right time. The three-pronged application (overview heat, wander cool weighting, validate decay check) shows systems thinking.

**Potential Impact (6.5/10):** Fixing the overview plumbing bug unlocks the intended UX. But uniform 14.0-day stability and single-curve assumption limit expressiveness. The biggest missed opportunity: stability remains static when FSRS research shows adaptive stability (updated per access) is what makes the model personal.

**Risk Level (5.5/10):** Medium. The overview bug is hidden (eval passes, no crash) but neuters the flagship R13 feature in the most-used code path. The stability=0 edge case is a crash vector waiting for a user to set it. The None semantics ambiguity creates divergent behavior between overview and wander for unaccessed memories.

---

## Phase 1: Core Assumptions Under Scrutiny

### 1.1 The 14.0-Day Default Stability — Empirically Unanchored

**The assumption:** `stability: float = Field(default=14.0)` in models.py:78. All four datasets reindex with stability=14.0 across every memory. The choice of 14 appears to derive from the pre-R13 30-day hard threshold (14 * 2 = 28, approximately 30).

**Adjacent-field evidence contradicts a single default:**

| Source | Half-Life Range | Context |
|--------|----------------|---------|
| Ebbinghaus (1885) | ~1 day | Nonsense syllables, no reinforcement |
| Duolingo HLR (Settles & Meeder, 2016) | Hours to multiple days | Per-word, lexeme-specific; 45% error reduction vs Leitner boxes |
| SuperMemo (Wozniak) | ~1 day (first interval) → months/years | Depends on repetition count and item difficulty |
| Husna et al. (2025) | Optimal review at 26.5 hours | Real Analysis students, 80% retention target |
| MIT (Subirana, Bagiati, Sarma, 2017) | ~2 years half-life | College academics, unreinforced |
| Procedural skills (Karni & Sagi, 1993) | Months to years | Motor sequences, mirror tracing — near-immune to decay once overlearned |
| FSRS v6 (2024) | Learned per-card from review history | 17-21 trainable parameters including personalized forgetting curve exponent w20 |

A single 14.0-day half-life is an arbitrary midpoint in a domain where half-lives span four orders of magnitude (hours to years). For CodeMemory's current datasets, different defaults would be empirically better justified:

| Dataset | Dominant Memory Type | Best-Fit Decay Profile (from research) | Suggested Default Stability |
|---------|---------------------|--------------------------------------|---------------------------|
| investment | Declarative facts + time-sensitive decisions | Exponential-power (steep initial drop) | 7-14 days |
| software-architecture | Conceptual + structural patterns | Logarithmic or linear (gentle, schema-aided reconstruction) | 30-60 days |
| companion | Episodic + personal interactions | Power-law (moderate) | 14-30 days |
| quant_operators | Procedural formulas + trading rules | Slow power-law or plateau (procedural consolidation) | 60-180 days |

**The risk of a single default:** With stability=14.0 and the exponential formula, a memory unaccessed for 90 days has `R = 0.5^(90/14) ≈ 0.011` — effectively zero retrieval probability. This is appropriate for a volatile fact (e.g., "NVDA guidance for Q3") but aggressively wrong for a stable concept (e.g., "event-driven architecture pattern"). The latter at 90 days with power-law decay (tau=0.5) would have `R ≈ 0.38` — still substantially retrievable. The uniform exponential encodes a philosophy that unsupported by research: "all memories fade at the same rate."

### 1.2 The Exponential Decay Curve — Valid Approximation, Not the Best Fit

**The assumption:** `decay = 0.5^(days/stability)` — a simple exponential with base 0.5 and half-life = stability.

**The evidence:** The 2024 Radvansky, Parra & Doolen meta-analysis (Psychonomic Bulletin & Review) reviewed 256 papers and 916 datasets spanning 150 years of memory research. Key findings:

| Best-Fit Function | Equation | Best For |
|-------------------|----------|----------|
| **Exponential-power** | `M = a * e^(-b * sqrt(t))` | Widest range of data; special case of Weibull |
| **Logarithmic** | `M = a - b * ln(t)` | Non-autobiographical memory; Ebbinghaus's original |
| **Linear** | `M = bt + a` | Complex/event memories; well-learned material |
| **Power** | `M = a * t^b` | Less well-learned information; consolidation-based |

Surprisingly, the power function — long considered the default — was **not** the best-fitting function most often. The simple exponential (CodeMemory's choice) was adequate for short intervals but failed at long retention periods.

**The Memory Phases Framework** (Radvansky, Doolen, Pettijohn & Ritchey, 2022, JEP:LMC) argues no single continuous function captures forgetting across all phases. Different functions apply at different timescales. CodeMemory operates entirely in the transitional-to-long-lasting domain (>1 week), where power-law or logarithmic decay is better supported by data.

**Practical consequence for CodeMemory:**

| days_since | Exponential (stability=14) | Power-law (tau=0.5, S=14) | Ratio |
|-----------|---------------------------|--------------------------|-------|
| 0 | 1.0 | 1.0 | 1.0x |
| 14 | 0.5 | 0.71 | 1.4x |
| 30 | 0.22 | 0.57 | 2.6x |
| 90 | 0.011 | 0.38 | 34x |
| 180 | 0.00012 | 0.27 | 2200x |

The exponential erases long-tail signal at a rate that is 2,200x more aggressive than power-law at 180 days. For a PKM system where memories can be valuable years after creation, this is a design choice with consequences: the exponential implicitly declares "not accessed in 90+ days = effectively forgotten." Power-law declares "not accessed in 90 days = harder to recall but still potentially valuable."

**The choice of formula encodes a philosophy about what forgetting means.** CodeMemory's current exponential says forgetting is near-binary after a few half-lives. Power-law says forgetting has a long, thin tail — old memories never truly vanish, they just become progressively harder to access.

### 1.3 High-Frequency Access Paradox — No Cooling Mechanism

**The assumption:** `days_since_last_access = 0` (set in resolve.py:320 after access) means `decay = 1.0` for recently-accessed memories. They never decay.

**The paradox:**
- A memory accessed daily: `days_since=0 → decay=1.0` always. Its heat = `deps*10 + access_count * 1.0`. Both components climb monotonically.
- A memory accessed 13 days ago (just shy of one half-life): `decay = 0.5^(13/14) ≈ 0.53`.
- The daily memory gets 2x the access bonus of the 13-day memory — perpetually.

**Is this desired?** For overview ("what should the agent see now?"), yes — recently-used memories are relevant. For wander ("what needs serendipitous rediscovery?"), wander's cool mode correctly handles this by giving `weight = 1/(access*decay + 1)` → near-zero weight for high-access recent memories. But no mechanism discourages over-access.

**The spacing effect from cognitive science:** In spaced repetition research, a memory reviewed daily provides near-zero new learning benefit — it's in the "massed practice" regime. The optimal review point is when retrieval probability drops to ~70-90% (the "desirable difficulty" sweet spot per FSRS research). A memory at R=1.0 (just accessed) gives the smallest stability gain; a memory at R=0.7-0.8 gives the largest.

**What's missing:** CodeMemory has no mechanism to detect that a memory is being "over-accessed" (massed practice) and to suggest spacing it out. The system could track `avg_days_between_accesses` and warn when it drops below the optimal review interval for that memory's stability.

### 1.4 The "days_since" Precomputation Enables Fast Heat But Loses Temporal Resolution

**The assumption:** `days_since_last_access` is an integer (precomputed as `(now - last_access).days` during reindex). This is efficient — avoids datetime parsing in every heat calculation.

**What's lost:** Integer-day resolution means a memory accessed 30 minutes ago and a memory accessed 23.5 hours ago both have `days_since=0`. They receive identical decay=1.0. In FSRS and ACT-R, sub-day temporal precision matters for working memory → early LTM transitions. For CodeMemory's current use cases (overview, wander, validate), day-level resolution is adequate. But if the system ever adds "same-session" activation (which FSRS v6 now models explicitly with its w19 parameter), sub-day precision becomes necessary.

**The precomputation timing issue:** `days_since_last_access` is computed at reindex time and updated at resolve time. If reindex runs on Monday and resolve runs on Friday, a memory accessed on Friday gets `days_since=0`. But a memory accessed on Monday and never reindexed still shows `days_since=0` on Friday (it was 0 at Monday's reindex, and no resolve refreshed it). The field is a **snapshot**, not a live computation. This is fine for overview (which runs frequently with fresh index loads) but could cause stale values in long-running server processes that cache the index.

---

## Phase 2: Adjacent Field Research Synthesis

### 2.1 FSRS (Free Spaced Repetition Scheduler) — Full Model Mapping

FSRS v6 (Jarrett Ye / open-spaced-repetition, 2024) is the current state-of-the-art in open-source spaced repetition. It models each memory card with three continuous parameters and 21 trainable weights. Its architecture maps surprisingly well to CodeMemory's current data model:

| FSRS v6 Concept | Symbol | Definition | CodeMemory Analog | Convergence Effort |
|---|---|---|---|---|
| **Stability** | S | Days for R to decay from 100% to 90% | `stability` field — but CodeMemory uses 50% point (half-life) | Trivial: `S_cm ≈ 6.6 * S_fsrs` |
| **Difficulty** | D [1,10] | Inherent complexity; learned from review outcomes | `intensity` field [1,10] — but assigned by user, not learned | Medium: repurpose intensity or add D field |
| **Retrievability** | R [0,1] | Instantaneous recall probability | `0.5^(days/stability)` — same concept | None: already computed |
| **Stability Increase (SInc)** | S' = S * (1 + ...) | S increases after successful recall; magnitude depends on D and R at review | NOT PRESENT | High: new update logic needed |
| **Forgetting Curve Exponent** | w20 [0.1, 0.8] | Personalized curve shape per user (FSRS v6) | NOT PRESENT | Very high: requires ML optimization |
| **Same-Day Review** | w19 | Models within-day multiple reviews (FSRS v6) | NOT PRESENT | Medium: requires sub-day timestamping |
| **Desired Retention** | r (e.g., 0.90) | User-specified target retention rate | NOT PRESENT | Low: add config field |

**The critical missing piece: adaptive stability.** In FSRS, stability is not a static field — it is updated after every review according to a formula that incorporates difficulty, current retrievability, and the review grade:

```
S' = S * [1 + (11-D) * S^(-w9) * (e^(w10*(1-R)) - 1) * h * b * e^w8]
```

The SInc magnitude is:
- **Larger when R is moderate** (~0.7-0.8) — the "spacing effect": gains are maximal when you're close to forgetting
- **Larger for easy material** (low D) — easy material consolidates faster
- **Smaller for high-S material** — stability saturates (harder to make stable memories even more stable)

Applying this to CodeMemory: on each `resolve` or `focus`, compute `R_at_access = 0.5^(days_since / stability)`, then update stability proportional to `(11 - intensity) * S_increase_factor(R_at_access)`. Over time:
- Frequently-accessed, low-intensity memories stabilize fast → their overview heat drops less rapidly between accesses
- Rarely-accessed, high-intensity memories stabilize slowly → they stay in the "needs review" zone longer
- The system converges to per-memory review intervals optimized for actual usage patterns

**FSRS performance data:** On 1.7B reviews from 20K users, FSRS v6 achieves 84% less prediction error than SM-2 and requires 20-30% fewer reviews for the same retention level. Parameter optimization starts outperforming defaults at just 16 reviews per card.

### 2.2 Ebbinghaus Forgetting Curve — Content-Type Differentiation

The 2024 Radvansky et al. meta-analysis (Psychonomic Bulletin & Review) provides the strongest evidence yet that different content types require different mathematical models of forgetting:

**Finding 1: Content type determines best-fit function.**

| Content Type | Dominant Decay Function | Half-Life (Unreinforced) | With Spaced Practice |
|---|---|---|---|
| **Facts** (declarative, rote) | Exponential / Exponential-power | ~1-7 days | Weeks to months |
| **Concepts** (semantic, meaningful) | Logarithmic / Linear | Weeks to months | Months to years |
| **Skills** (procedural) | Slow power-law / Plateau | Months to years | Years (near-permanent) |

**Finding 2: Concepts decay differently because they support reconstruction.** Fisher & Radvansky (2022a, 2022b) found that well-learned conceptual information is best fit by a linear function, explained by the RAFT computational model — concepts allow partial reconstruction from related knowledge, which produces a shallower apparent decay curve. Facts don't benefit from reconstruction and thus show steeper exponential-like decay.

**Finding 3: Murre (2023) averaging artifact.** Averaging individual exponential forgetting curves produces artifact power functions. This means observing power-law behavior in aggregate data does not prove power-law decay at the individual level — a critical methodological insight for any system that models individual memory decay.

**Finding 4: Interleaving vs. blocking.** A 2024 study (PMC, JARMAC) found that interleaved presentation enhances category generalization (concept learning), while blocked presentation improves memory for specific episodic details (fact learning). Category knowledge remained stable over time; episodic details declined. This maps to CodeMemory's tag structure: concept-tagged memories should have longer effective stability than fact-tagged memories.

### 2.3 Recommender Systems — Collaborative Memory Discovery

Three recommender system paradigms transfer directly to CodeMemory's memory discovery and surfacing operations:

**Technique 1: Memory Co-Occurrence Matrix (Item-Item Collaborative Filtering).**
When a user resolves memory A and memory B appears in the same DAG, increment a co-occurrence score. Over time, a memory-memory co-occurrence matrix emerges. This is implicit feedback — "memories that are frequently resolved together." Unlike the explicit imports DAG (what the author thought was related), co-occurrence encodes what the reader actually found useful together.

Formula: `cooccurrence_score(A, B) = cooccurrence_count(A, B) * 0.5^(days_since_cooccurrence / stability)`

**Technique 2: Tag-Based TF-IDF Weighting.**
Treat tags as "terms" and memories as "documents." Compute tag-memory TF-IDF scores. Rare tags (e.g., "options-trading") have higher IDF weight than common tags (e.g., "investment"). When resolving a memory with rare tags, boost the heat of other memories sharing those rare tags — higher-signal associations.

**Technique 3: CF-KAN for Continual Learning (Park, Kim, Shin, 2024).**
Kolmogorov-Arnold Networks applied to collaborative filtering demonstrate inherent robustness to catastrophic forgetting — the tendency of recommenders to "forget" old user preferences when new data arrives. Applied to CodeMemory: the overview ranking could use KAN-inspired weight preservation to ensure that memories from less-active domains (e.g., "software-architecture" when the user is deep in "investment") don't drop to zero heat.

**Technique 4: Knowledge Graph + Collaborative Filtering Hybrid.**
The 2024 hybrid model from Ain Shams Engineering Journal combines knowledge graph embeddings (TransE) with neural collaborative filtering, achieving ~6% F1 improvement over baselines. CodeMemory already has a knowledge graph (DAG). Adding collaborative signals (co-occurrence, shared access patterns) on top of the structural graph would produce a hybrid recommendation — "memories you should review based on what similar memories you've been reviewing."

### 2.4 Cross-Domain Synthesis: The Three-Axis Memory State (Updated for R13)

R12 proposed a three-axis model (Structural x Temporal x Stability). R13 partially implemented one axis (temporal decay via stability-anchored exponential) but left the other two unaddressed:

```
                    STRUCTURAL IMPORTANCE
                    (weighted incoming edges
                     + PageRank on DAG)
                         ▲
                        /|\
                       / | \
                      /  |  \   ← R13: stability added but STATIC
                     /   M   \     No per-memory differentiation.
                    /    E    \    No spreading activation.
                   /     M     \
                  /      O      \     R13: M3 precomputes days_since,
                 /       R       \    M1 unifies formula. But
                /        Y        \   plumbing bug blocks overview.
               ◄───────────────────►
          TEMPORAL RECENCY       KNOWLEDGE STABILITY
      (M3: precomputed days)     (M4: stability=14.0 static)
```

The three axes create four operational zones that each demand different system behaviors:

| Zone | Structural | Temporal (R) | Stability | Behavior |
|------|-----------|-------------|-----------|----------|
| **Pillars** | High | High | High | Always surfaced. Core of current work. |
| **Review Targets** | High | Low | Low | Important but fading. Needs re-engagement. Optimal wander targets. |
| **Fragile Gems** | Low | Low | High | Important to someone, but unlinked. Needs imports. |
| **Archive Candidates** | Low | Low | Low | Not connected, not accessed, not stable. Archive proposal. |

---

## Phase 3: Logical Completeness Analysis

### 3.1 Data Plumbing Bug: Overview Decay Formula Never Activates (CRITICAL)

**Location:** `handlers.py` line 258, `handle_overview()`.

**Root cause:**
```python
# Line 256-258: entry IS a MemoryEntry (has .days_since_last_access)
entry = index.memories.get(mid)
stability = entry.stability if entry else 14.0
days_since = r.get("days_since_last_access") if isinstance(r, dict) else getattr(r, "days_since_last_access", None)
```

`r` is a dict returned by `search()` (search.py lines 73-85). The search function builds result dicts that include `access_count`, `last_access`, `dependents` — but NOT `days_since_last_access`. The field exists on `entry` (the MemoryEntry object at line 256) but the handler reads from `r`, where it is always `None`.

**Effect:**
```python
# Line 259-264: days_since is always None from search results
if access > 0 and days_since is not None:  # Always False
    days_since = max(0, days_since)
    decay = math.pow(0.5, days_since / stability)  # NEVER REACHED
    access_bonus = access * decay
else:
    access_bonus = access * 0.1  # ALWAYS TAKEN — pre-R13 flat 10% multiplier
```

The entire R13 decay model is inert in the most-used code path. The `0.5^(days/stability)` formula never executes for overview.

**Why the eval didn't catch it:** The eval verified heat values as 31, 31, 21, 21, 20 for the investment dataset. Under the bug, heat = `deps*10 + access*0.1`:
- risk-tolerance: `3*10 + 10*0.1 = 31` ✓
- semiconductor-thesis: `3*10 + 10*0.1 = 31` ✓
- nvidia-earnings: `2*10 + 10*0.1 = 21` ✓
- soxl-composition: `2*10 + 10*0.1 = 21` ✓
- february-buy: `2*10 + 0*0.1 = 20` ✓

All eval heat values are consistent with the **old** formula. The eval verified the old behavior was preserved — not that the new behavior was active.

If the decay formula were active (assuming `days_since=0` for recently reindexed data with resolved memories): risk-tolerance heat would be `30 + 10*1.0 = 40`, not 31. The eval would have caught this discrepancy — **if** the formula were active.

**Fix:**
```python
# Line 258: read from entry, not from r
days_since = entry.days_since_last_access if entry else None
```

One line. **Impact: Unlocks the entire R13 decay model for overview.**

**Contrast with wander:** `handle_wander()` line 345 correctly reads:
```python
days_since = getattr(entry, 'days_since_last_access', None)
```
This reads from the MemoryEntry object, which has the precomputed field. Wander's decay weighting works correctly. This is why the eval's wander-related tests didn't expose the issue.

### 3.2 Stability Edge Cases

**Case: stability = 0** → `math.pow(0.5, days_since / 0)` → `ZeroDivisionError` → **CRASH** in overview, wander, and validate. No guard exists in any of the three code paths.

**Case: stability < 0** → `0.5^(positive / negative) = 0.5^(negative) = 2^(positive) > 1.0`. Decay exceeds 1.0 — the memory appears to "strengthen" over time. Nonsensical. No guard exists.

**Case: stability very large (e.g., 10000)** → `0.5^(days/10000) ≈ 1.0` for any practical days. Memory is effectively immortal. May be intentional for "eternal" memories but should be explicit — either a `stability = float('inf')` sentinel or a check: if `days_since / stability < 0.001`, skip computation and set decay=1.0.

**Case: days_since_last_access = None** → Three different behaviors across three code paths:

| Code Path | None Handling | Behavior | Intentional? |
|-----------|--------------|----------|-------------|
| **Overview (broken)** | `access > 0 and days_since is not None` → False | `access_bonus = access * 0.1` (flat 10%) | Accidental — falls through due to bug |
| **Wander cool mode** | `entry.access_count > 0 and days_since is not None` → False | `weight = 1.0` (max cool weight) | Intentional — unaccessed = maximally cool |
| **Validate _check_decay** | Falls back to `datetime.fromisoformat(entry.last_access)` | Computes days_since from last_access | Defensive — safety net for un-reindexed data |

The EVAL.md Section 8 already flagged this ambiguity as pitfall R13-M3: "None means never accessed vs 0 means just accessed. Current code treats both similarly but future wander may need to distinguish."

### 3.3 Interaction Between Decay and Other Systems

**Decay vs. Stale Detection:**
- Stale = body hash mismatch (content changed without reindex). Decay = access-based (not accessed recently).
- They operate independently. A stale-but-frequently-accessed memory appears in overview with high heat AND a stale warning. A fresh-but-never-accessed memory appears with low heat and no warning.
- No combined risk score exists. A "stale AND decayed" memory is double-at-risk but both systems fire independently with no synthesis.

**Decay vs. Maturity Auto-Upgrade:**
- `resolve.py:323-339`: `access_count >= 3` → draft→verified. `access_count >= 10 + has dependents` → verified→proven.
- These thresholds use lifetime access count with no recency weighting. A memory accessed 3 times in one day triggers "verified." A memory accessed 3 times over 3 years also triggers "verified."
- With the decay model active, maturity should require *recent* access: `access_count >= 3 AND max(R_at_access_times) > 0.5` or similar recency gate.

**Decay vs. Search:**
- `search()` does not use decay at all. Results sorted by `(-dependents, -access_count, id)`. No recency factor.
- Even after fixing the overview bug, search remains decay-unaware. A user searching for "investment" gets the most-connected and most-accessed results — regardless of recency.

**Decay vs. Intensity (protection):**
- `validate.py:_check_decay` line 88: memories with `intensity >= 8` are exempt from decay warnings.
- This is the only place intensity interacts with decay. Overview and wander apply decay regardless of intensity.
- Should high-intensity memories get proportionally higher effective stability? Currently no. An intensity=10 memory and intensity=1 memory with the same stability=14.0 decay identically.

**Decay vs. Overview `--with-recall` flag:**
- `handle_overview()` lines 292-307: `with_recall` sorts candidates by `access_count` (ascending), takes the lowest third, picks randomly.
- The comment says "use unified decay formula for cool wander weighting" but the code does no such thing — it sorts by raw access_count. The comment is aspirational, not actual.

### 3.4 Wander Cool Mode — Correctly Implemented But Could Be Stronger

The wander cool mode (handlers.py lines 332-352) correctly:
1. Filters for `intensity < 8` (respects protection)
2. Reads `entry.days_since_last_access` from MemoryEntry (not from search dict — correct!)
3. Computes `decay = 0.5^(days/stability)`
4. Computes `weight = 1/(access_count * decay + 1)`
5. Uses `random.choices()` with these weights

This means wander correctly gives high weight to cold (unaccessed, long days_since) memories. The formula works as designed for the wander path.

**The limitation:** The max weight is 1.0 (for unaccessed memories). All unaccessed memories receive equal weight. Within the unaccessed pool, wander is random — no differentiation by tags, creation date, type, or structural position. The "coolness" is purely a function of access frequency weighted by recency. Structural coolness (low dependents, orphan status) is not considered, despite the handler's orphan annotation display (line 404-405) suggesting it should be.

### 3.5 Search Result Dict Field Coverage Gap

`search()` (search.py lines 73-85) builds result dicts. The fields included are:
`id, type, summary, status, tags, path, intensity, access_count, last_access, dependents, maturity`

Fields in MemoryEntry but **not** in search results:
`version, created, updated, schema, imports, stability, days_since_last_access, protected, change_note, change_log, source, evidence, summary_hash`

The missing `stability` and `days_since_last_access` are now critical compute inputs for R13. The missing `schema` prevents search-based consumers from displaying schema references. The missing `imports` prevents lightweight dependency queries without loading the full index.

---

## Phase 4: Alternative Design Proposals (Inspiration Bombs)

### Bomb 1: Domain-Calibrated Stability Presets (Low Effort, High Impact)

**Current state:** All memories share `stability=14.0`. User must manually change it.

**Proposal:** Auto-assign stability based on detectable memory characteristics during `create`:

| Heuristic | Assigned Stability | Rationale |
|-----------|-------------------|-----------|
| Tag contains "fact" / "data" / "earnings" / "price" | 7 days | Declarative fact — fast decay per Ebbinghaus |
| Tag contains "concept" / "architecture" / "pattern" / "principle" | 30 days | Conceptual — slow, schema-aided decay per Radvansky (2024) |
| Tag contains "decision" / "trade" / "buy" / "sell" | 14 days | Time-sensitive decision — current default |
| `type: schema` | 90 days | Structural template — near-immortal |
| `intensity >= 8` | stability * 2.0 | High-importance memories decay slower |
| Has imports (serves as dependency for others) | stability * 1.5 | Referenced memories are reinforced by backlinks |
| `maturity: proven` | stability * 2.0 | Proven knowledge is consolidated; slower decay |

**Implementation:** A `suggest_stability(tags, type_, intensity, has_imports, maturity) -> float` function. Called during `create` to auto-set the field with an `[auto]` annotation. Existing memories keep manually-set stability. Validate can suggest changes for mismatched stability values.

**Impact:** Makes the stability field semantically meaningful immediately. Users see different decay rates for different memory types, which communicates the concept better than a uniform default. The heuristics are transparent and overridable.

### Bomb 2: FSRS-Inspired Adaptive Stability (Medium Effort, Transformative)

**Current state:** Stability is static. Never changes unless manually edited.

**Proposal:** On each `resolve` or `focus`, update stability using a simplified FSRS SInc formula:

```python
def update_stability(memory: MemoryEntry, access_quality: int = 3) -> float:
    """Update stability after an access. access_quality: 1=forced, 3=normal, 5=organic."""
    days_since = memory.days_since_last_access or 0
    R_at_access = 0.5 ** (days_since / memory.stability)  # retrievability at access time

    # FSRS-inspired: gain is maximal when R is moderate (~0.5-0.7)
    # Low R (nearly forgotten) -> larger gain (spacing effect)
    # High R (just accessed)  -> smaller gain (massed practice penalty)
    retrievability_gain = max(0, 1 - R_at_access) ** 0.5

    # Difficulty from intensity: higher intensity = harder (D ∈ [0.1, 1.0])
    difficulty = memory.intensity / 10.0

    # Stability increase factor
    s_inc = 1 + (1 - difficulty) * retrievability_gain * 0.5

    # Quality adjustment
    quality_bonus = 1 + (access_quality - 3) * 0.1

    return memory.stability * s_inc * quality_bonus
```

**How this converges:**
- Memory accessed daily: `days_since=0 → R=1.0 → gain=0 → S' ≈ S * 1.0`. Stability barely changes. The system signals "this is massed practice — no learning benefit."
- Memory accessed at `days_since=14` (R=0.5): `gain=0.71 → S' ≈ S * 1.2`. 20% stability increase. The system signals "good spacing — memory is consolidating."
- Memory accessed at `days_since=46` (R≈0.1): `gain=0.95 → S' ≈ S * 1.3`. 30% increase. The system signals "near-forgotten but recovered — strongest consolidation signal."

**Why transformative:**
1. Stability converges to each memory's natural review interval
2. Frequently-accessed memories stabilize rapidly (less need to surface them)
3. Rarely-accessed but high-intensity memories stay in the "needs review" zone longer
4. The system learns from actual usage patterns rather than imposing a priori defaults
5. FSRS research shows: with 16+ reviews, personalized parameters outperform defaults; CodeMemory's `access_count` already tracks this

**Requirements:** `stability` field already exists. Need to call `update_stability()` in `resolve.py` after line 320 (where `days_since_last_access` is already set to 0). Need a minimum `access_count` threshold (~3) before adaptive updates begin, to avoid overfitting to early noise.

### Bomb 3: Collaborative Memory Graph for Associative Wander (Medium Effort, Novel)

**Current state:** Wander's cool mode picks from low-access memories randomly. No relationship to current work context.

**Proposal:** Build a memory-memory co-occurrence matrix from resolve history. When memory A is resolved and memory B appears in the same DAG, increment `cooccurrence[A][B]`. Over time, this produces "memories frequently resolved together" — an implicit relevance signal orthogonal to the explicit imports DAG.

**Application to a new `wander --mode associative`:**

```python
# Step 1: Start from the most-recently-resolved memory (the "seed")
# Step 2: With probability p, jump to a co-occurring memory from the seed
# Step 3: With probability (1-p), jump to an imported memory from the seed
# Step 4: Repeat for 3-5 steps, decaying jump probability (random walk with teleport)
# Step 5: Output the landing memory — serendipitous but contextually-connected discovery
```

**Why this is novel:** No existing PKM tool combines explicit dependency graphs with implicit co-occurrence for memory discovery. Obsidian's graph view shows explicit links. Anki's FSRS schedules reviews. CodeMemory could be the first to do associative wandering through a learned co-occurrence graph on top of explicit imports — modeling how human memory works (one thought triggers another through associative links).

**Storage:** The co-occurrence matrix is sparse (most memory pairs never co-occur). Store as a JSON dict in `.codememory/cooccurrence.json`. Update during `resolve()` in a fire-and-forget pattern (don't block resolution for co-occurrence tracking).

### Bomb 4: Per-Memory-Type Decay Curves (High Effort, Research-Grade)

**Current state:** Single formula `0.5^(t/S)` for all memories. Stability is the only tunable parameter.

**Proposal:** Add a `decay_curve` field to MemoryEntry that selects the mathematical function, not just its parameter:

```python
# New field on MemoryEntry
decay_curve: str = Field(default="exponential",
    description="exponential | power | logarithmic | linear | step")

def compute_decay(days_since: float, stability: float, curve: str) -> float:
    if curve == "exponential":
        return 0.5 ** (days_since / stability)
    elif curve == "power":
        # Power-law: (1 + t/S)^(-tau), tau=0.5 default
        return (1 + days_since / stability) ** (-0.5)
    elif curve == "logarithmic":
        # Logarithmic: 1 - a * ln(1 + t/S)
        return max(0.0, 1.0 - 0.15 * math.log(1 + days_since / stability))
    elif curve == "linear":
        # Linear decay to zero at t = stability
        return max(0.0, 1.0 - days_since / stability)
    elif curve == "step":
        # Binary: 1.0 until stability days, then 0.0
        return 1.0 if days_since <= stability else 0.0
    else:
        return 0.5 ** (days_since / stability)
```

**Rationale from research:**

| Curve | Best For | Empirical Support |
|-------|----------|-------------------|
| Exponential | Rote facts, volatile data | Ebbinghaus (1885), HLR (2016) |
| Power-law | General declarative, mixed types | Wixted & Carpenter (2007), ACT-R |
| Logarithmic | Concepts, semantic knowledge | Radvansky et al. (2024) — best fit for non-autobiographical |
| Linear | Well-learned complex material | Fisher & Radvansky (2022) — RAFT model |
| Step | Decisions with explicit expiry | Practical heuristic (no research backing yet) |

**Why research-grade:** This directly implements the 2024 meta-analysis finding that no single function fits all forgetting. It makes CodeMemory's decay model a composable function rather than a single formula — a defensible design position against future competitors. The challenge: users shouldn't need to choose a decay curve. The `suggest_stability()` function (Bomb 1) should also suggest the curve based on detectable memory characteristics.

### Bomb 5: Context-Aware Activation (Spreading Activation Engine)

**Current state:** Heat is computed from the memory's own properties — structural position (`deps`) and temporal recency (`access * decay`). No awareness of what the user is currently doing.

**Proposal:** Add a second heat component — spreading activation from the current context:

```python
def compute_context_heat(memory, context_tags, context_memories, index):
    """Spreading activation from current task context."""
    boost = 0

    # Tag overlap with current working context
    shared_tags = set(memory.tags) & context_tags
    # Weight rare tags higher (IDF-like): rare tags are more informative
    for tag in shared_tags:
        tag_frequency = sum(1 for m in index.memories.values() if tag in m.tags)
        boost += 3 * math.log(1 + len(index.memories) / max(tag_frequency, 1))

    # Direct dependency: is this memory imported by what the user is working on?
    for ctx_id in context_memories:
        ctx_entry = index.memories.get(ctx_id)
        if ctx_entry:
            ctx_imports = ctx_entry.imports
            if isinstance(ctx_imports, dict):
                for strength in ("required", "recommended"):
                    for ref in ctx_imports.get(strength, []):
                        ref_id = ref if isinstance(ref, str) else ref.get("id", "")
                        if ref_id == memory.id:
                            weight = 5 if strength == "required" else 3
                            boost += weight

    return boost
```

This makes overview context-dependent: `heat = deps*10 + access*decay + context_heat`. The same memory has different activation depending on what the agent or user is currently doing. This is exactly ACT-R's spreading activation component — the single largest missing piece identified in the R12 research audit.

---

## Prioritized Research Directions

### Critical (blocking issues)

- **[R-RED-1] Fix overview data plumbing bug.** `handle_overview()` line 258 reads `days_since_last_access` from search result dict instead of from MemoryEntry object. Decay formula never activates. One-line fix: `days_since = entry.days_since_last_access if entry else None`. Also add `days_since_last_access` and `stability` to the search result dict (search.py lines 73-85) for API consumers. **Impact: Unlocks the entire R13 decay model for the most-used code path.**

### High Priority (should address next round)

- **[R-RED-2] Add stability validation.** Enforce `stability > 0` in a Pydantic `@field_validator` on `MemoryEntry.stability`. Guard against division by zero (crash) and negative stability (nonsensical decay > 1.0). Consider a minimum of 0.1 days (2.4 hours) as a practical lower bound. **Impact: Prevents crash and undefined behavior.**

- **[R-RED-3] Resolve `days_since_last_access=None` semantics.** Define a clear contract: `None` = never accessed (distinct from `0` = just accessed). Update all three consumption points (overview, wander, validate) to handle both cases consistently. Specifically: in overview, never-accessed memories should get a small but non-zero access bonus (e.g., 0.5) to avoid the current accidental 0.0. **Impact: Fixes the semantic ambiguity flagged in EVAL.md Section 8.**

- **[R-RED-4] Include fields in search results.** Add `stability` and `days_since_last_access` to the search result dict. Consider also adding `schema` and `imports` (or at least import count) — consumers increasingly need these fields. **Impact: Makes R13 fields available to API consumers and the `with_recall` path.**

### Medium Priority (design exploration)

- **[R-YLW-1] Domain-calibrated stability presets (Bomb 1).** Implement tag/type-based stability suggestion during `create`. Train on existing datasets as calibration data. **Impact: Makes stability immediately meaningful across datasets without requiring manual tuning. ~50 LOC in create.py.**

- **[R-YLW-2] Add recency factor to search ranking.** Sort search results with a recency multiplier: `score = dependents_rank + access_count * 0.5^(days_since/stability)`. This makes search time-aware — recently-accessed memories rank higher for equal structural importance. **Impact: Search becomes decay-aware. ~15 LOC in search.py.**

- **[R-YLW-3] Decay-aware maturity upgrade.** Require recent access for draft→verified transitions: `access_count >= 3 AND max_days_since_last_access_at_upgrade_times <= 60`. Prevents "maturity inflation" from old, unreviewed memories. **Impact: Makes maturity reflect actual engagement quality. ~10 LOC in resolve.py.**

- **[R-YLW-4] Apply decay to `--with-recall` path.** In `handle_overview()` lines 292-307, use the decay formula for sorting candidates rather than raw access_count. Currently the comment says "use unified decay formula" but the code uses raw access_count. **Impact: Aligns with_recall behavior with the unified model. ~5 LOC.**

- **[R-YLW-5] Unify intensity-decay interaction.** Currently only `validate._check_decay` exempts `intensity >= 8` memories from decay warnings. Overview and wander apply decay regardless of intensity. Decide: should high-intensity memories get a stability multiplier (e.g., `effective_stability = stability * (intensity / 5)`)? Or should intensity only affect the decision to warn, not the decay computation? **Impact: Consistent semantics across all decay consumers.**

### Exploratory (future rounds)

- **[R-GRN-1] FSRS-inspired adaptive stability (Bomb 2).** Stability updates on each resolve/focus using simplified SInc formula. Requires `access_count >= 3` before adaptive updates begin. **Impact: Self-tuning memory lifecycle. ~60 LOC across handlers.py and resolve.py.**

- **[R-GRN-2] Collaborative memory graph for associative wander (Bomb 3).** Co-occurrence matrix from resolve history. New `wander --mode associative` command. **Impact: Novel PKM feature with no known competitor. ~150 LOC across new module + handlers.py.**

- **[R-GRN-3] Per-memory-type decay curves (Bomb 4).** `decay_curve` field with exponential/power/logarithmic/linear/step options. Auto-suggested during create. **Impact: Makes CodeMemory's decay model research-grade and defensible. ~80 LOC across models.py + core.py + handlers.py.**

### Inspiration Bombs (backlog)

- **[R-BOMB-1] Context-aware activation (Bomb 5).** Spreading activation from current task tags and active resolve targets. Context-dependent heat component. **Novelty: ACT-R spreading activation applied to PKM — no existing tool does this.**

- **[R-BOMB-2] Forgetting-as-feature.** Surface "what you're about to forget" — memories with `R` near the decay warning threshold (0.1-0.2). A "Rescue Queue" in Dashboard showing 3-5 memories at risk of effective forgetting. Turn the decay model into a proactive UX feature. **Novelty: Transforms decay from backend mechanism to user-facing product feature.**

- **[R-BOMB-3] Stability inheritance through the DAG.** When memory A imports memory B, A partially inherits B's stability. A concept depending on a well-established memory should be more stable than one depending on a volatile memory. Weighted by import strength. **Novelty: Makes DAG topology influence decay dynamics — uniquely CodeMemory.**

- **[R-BOMB-4] Duolingo HLR-style trained stability.** Train per-memory stability from access history using maximum likelihood estimation (like half-life regression). Requires 16+ accesses per memory for statistical significance (per FSRS optimization research). **Novelty: Treats stability as a learned parameter, not a configured one.**

---

## Appendix A: CodeMemory-FSRS v6 Concept Mapping

| CodeMemory R13 | FSRS v6 | Compatibility | Migration Difficulty |
|---|---|---|---|
| `stability` (half-life, days to R=50%) | Stability S (days to R=90%) | Direct mapping: S_cm ≈ 6.6 * S_fsrs | Trivial — rename and rescale if desired |
| `intensity` [1,10] | Difficulty D [1,10] | Same numeric range; different semantics | Medium — intensity is importance, D is inherent difficulty learned from outcomes |
| `0.5^(t/S)` | `(1 + F*t/S)^C` (v4-5) or `(1 + factor*t/S)^(-w20)` (v6) | Both are continuous decay | Low — replace formula, keep field. v6's trainable w20 enables personalized curve shape |
| `access_count` | Review count | Same concept | None — already tracked |
| `days_since_last_access` | t (elapsed days since last review) | Same concept | None — already tracked (day resolution vs FSRS's second resolution) |
| NOT PRESENT | SInc (stability increase after review) | No analog | High — new logic needed; ~60 LOC |
| NOT PRESENT | Desired retention r | No analog | Low — add config field |
| NOT PRESENT | w8-w20 (21 trainable parameters) | No analog | Very high — requires ML optimization pipeline |
| NOT PRESENT | Same-day review modeling (w19) | No analog | Medium — requires sub-day timestamp resolution |
| NOT PRESENT | Post-lapse stability (S_f) | No analog | Medium — would model "forgetting after a failed recall" |

## Appendix B: Decay Formula Behavior Under Edge Cases

| days_since | stability | `0.5^(days/stability)` | Practical Meaning | Issue |
|---|---|---|---|---|
| 0 | 14.0 | 1.0 | No decay — just accessed | Correct |
| 14 | 14.0 | 0.5 | One half-life — 50% retrieval prob | Expected |
| 46 | 14.0 | ~0.098 | ~3.3 half-lives — below validate warning threshold | Triggers DECAY-WARN |
| 90 | 14.0 | ~0.011 | ~6.4 half-lives — near-zero | May be too aggressive for concepts |
| 180 | 14.0 | ~0.00012 | ~12.8 half-lives — effectively zero | Definitely too aggressive for anything but rote facts |
| 0 | 0 | `0.5^(0/0)` → ZeroDivisionError | **CRASH** | No Pydantic guard, no runtime guard |
| 14 | 0 | `0.5^(14/0)` → ZeroDivisionError | **CRASH** | Same — any non-zero days with stability=0 crashes |
| 14 | -7 | `0.5^(14/-7) = 0.5^(-2) = 4.0` | Decay > 1.0 — memory "strengthens" with time | Nonsensical; need Pydantic `gt=0` |
| None | 14.0 | (overview, broken path) | Falls to `access*0.1` (pre-R13 default) | Accidental; differed from wander |
| None | 14.0 | (wander, correct path) | `weight = 1.0` (max cool weight) | Intentional; matches "never accessed = cool" semantics |
| None | 14.0 | (validate, fallback) | Computes from `datetime.fromisoformat(last_access)` | Defensive; safety net for un-reindexed data |

## Appendix C: Summary of Changes Since R12 Research Audit

| R12 Recommendation | R13 Status | Notes |
|---|---|---|
| 1. Unify decay models (overview/wander/validate) | **IMPLEMENTED (R13-M1)** | Single formula `0.5^(t/S)` across all three. But overview path broken by plumbing bug. |
| 2. Exclude cycle participants from dependents count | **IMPLEMENTED (R13-M2)** | `find_cycle_participants()` precomputed in overview; cycle member deps=0. |
| 3. Precompute `days_since_last_access` | **IMPLEMENTED (R13-M3)** | Integer precomputed at reindex + set to 0 on resolve. Day resolution only. |
| 4. Add `stability` field to MemoryEntry | **IMPLEMENTED (R13-M4)** | `stability: float = 14.0`. Static. No adaptive update. No Pydantic `gt=0` guard. |
| 5. Spreading activation from tag context | **NOT IMPLEMENTED** | Deferred to future round. Research audit now provides concrete implementation sketch. |
| 6. FSRS-style per-memory stability updates | **NOT IMPLEMENTED** | Stability field exists but is static. Bomb 2 provides concrete adaptive formula. |
| 7. Memory tier visualization (Hot/Warm/Cold/Frozen) | **NOT IMPLEMENTED** | Deferred. R13 decay model provides the mathematical foundation for tier boundaries. |
| 8. Demotion path for maturity | **NOT IMPLEMENTED** | Maturity still forward-only. Decay model now provides the R<0.1 threshold for demotion suggestions. |

---

*End of research audit report. Generated 2026-05-07. Adjacent domains researched: FSRS v4-v6 (DSR model, SInc update formula, 21-parameter optimization, 1.7B-review benchmark), Ebbinghaus/Radvansky 2024 meta-analysis (916 datasets, exponential-power/logarithmic/linear/power best-fit functions, Memory Phases Framework, content-type differentiation), Duolingo HLR half-life regression (lexeme-specific stability, MLE training, 45% error reduction), recommender systems (CF-KAN catastrophic forgetting mitigation, knowledge-graph collaborative filtering hybrids, item-item co-occurrence, TF-IDF tag weighting).*
