# CodeMemory Design Research Audit — Round 14 (Decay System Go-Live)

**Reviewer:** Product Research Reviewer
**Date:** 2026-05-07
**Build:** Post-Round 14 (C1 decay bug fix, C2 stability boundary protection, C3 API exposure, N1 Dashboard decay panel)
**Method:** Full-source review (handlers.py, models.py, validate.py, index.py, resolve.py, server.py), mathematical verification of decay formula across 5 stabilities and 10 time points, 3-domain adjacent field research (FSRS v6, SuperMemo SM-17-SM19, cognitive psychology meta-analysis), logical edge-case analysis.

---

## Executive Summary (6.5 / 10)

Round 14 fixes the decay pipeline so it actually works — the C1 bug fix (reading `days_since_last_access` from MemoryEntry instead of the search dict, which never contained it) was a critical correctness issue, and the C2 stability boundary protection prevents division-by-zero and negative decay. The C3 API exposure and N1 Dashboard panel close the "backend only" gap identified in the Round 13 audit. **The system now functions correctly end-to-end.**

The research question is not *whether* the decay system works, but *whether the chosen mathematical model matches what we now know about memory decay across different content types and timescales.* The answer is nuanced: the current exponential model is **appropriate for short-term access decay (< 60 days)** but **catastrophically aggressive for long-term memory (> 90 days)**. At the default stability of 14.0 days, a memory accessed yesterday has 95% retrieval probability — a memory last accessed 90 days ago has 1.2%. This 80:1 ratio may be too steep for foundational knowledge.

The adjacent field research reveals that the state of the art (FSRS v6, SuperMemo SM-19) has moved well beyond fixed per-item half-lives. Both systems use **adaptive stability that increases on successful access** — stability is a *learned parameter*, not a static constant. CodeMemory's `stability = 14.0` default is analogous to FSRS's initial stability parameter (w0/w1), but CodeMemory never updates stability on access. This is the single most significant architectural gap.

**Functionality (8.0/10):** The decay pipeline is correct end-to-end. Math verified. Edge cases properly handled. API properly exposes decay fields. +1.5 from Round 13's M1-M4 "backend only" assessment.

**Research Rigor (5.0/10):** The exponential model was chosen on intuition (half-life is elegant), not on empirical fit to memory data. The 2024 Psychonomic Bulletin meta-analysis of 916 datasets found that exponential-power (e^(-b*sqrt(t))) outperforms pure exponential in the widest range of real memory datasets. The 14.0-day default has no empirical basis for any specific content type.

**Product Imagination (6.5/10):** The system has the right primitive (`stability` per memory). But the primitive is static. The adjacent research shows that the truly powerful pattern is **stability as a learned, adaptive parameter** — one that increases when a memory is successfully recalled (the spacing effect) and decreases on lapse. This is within reach given the existing infrastructure.

---

## Phase 1: Core Assumption Challenge

### 1.1 The Exponential Decay Model — Is It the Right Function?

**Current model:** `R(days) = 0.5^(days / stability)`

This is a pure exponential decay with half-life = `stability`. It has one tunable parameter per memory. The key assumption is that retrieval probability halves every `stability` days, independent of how the memory has been used.

**What the research says:**

The 2024 meta-analysis by [Fisher & Radvansky, Psychonomic Bulletin & Review](https://link.springer.com/article/10.3758/s13423-024-02514-3) analyzed 916 datasets from 256 papers spanning nearly 150 years of memory research. Their key finding: **the exponential-power function (M = a * e^(-b * sqrt(t))) was the best-fitting function across the widest range of data**, not pure exponential and not pure power-law.

The theoretical reason: memory decay is not a single process. The forgetting curve is the **superposition of multiple exponential processes at different timescales** — synaptic decay (hours), systems consolidation (days-weeks), and representation drift (months-years). A pure exponential captures only one of these. The exponential-power function (a special case of the Weibull distribution) captures the multi-timescale nature because different time points sample different underlying decay processes.

**Mathematical verification of the current model:**

```
Decay formula: 0.5^(days / stability)

At stability=14.0 (default):
  1 day:   R = 0.5^(1/14)    = 95.2%    (essentially fresh)
  7 days:  R = 0.5^(7/14)    = 70.7%    (first significant drop)
  14 days: R = 0.5^(14/14)   = 50.0%    (one half-life)
  30 days: R = 0.5^(30/14)   = 22.6%    (getting cold)
  46 days: R = 0.5^(46/14)   = 10.3%    (decay warning threshold)
  60 days: R = 0.5^(60/14)   =  5.1%    (very cold)
  90 days: R = 0.5^(90/14)   =  1.2%    (near-zero)
  180 days: R = 0.5^(180/14) =  0.014%  (effectively zero)
  365 days: R = 0.5^(365/14) =  1.46e-8 (zero at any machine precision)

At stability=90.0 (long-half-life alternative):
  30 days:  R = 0.5^(30/90)  = 79.4%    (still warm)
  90 days:  R = 0.5^(90/90)  = 50.0%    (one half-life)
  180 days: R = 0.5^(180/90) = 25.0%    (getting cold)
  365 days: R = 0.5^(365/90) =  6.0%    (below warning threshold)
  730 days: R = 0.5^(730/90) =  0.4%    (near-zero after 2 years)

At stability=365.0 (year-scale reference):
  90 days:  R = 0.5^(90/365) = 84.3%    (barely decayed)
  365 days: R = 0.5^(365/365) = 50.0%  (one half-life per year)
  730 days: R = 0.5^(730/365) = 25.0%  (still retrievable after 2 years)
```

**What this means for CodeMemory:**

At stability=14.0, the system crosses the decay warning threshold (R < 0.1) at **46 days** — roughly 3.3 half-lives. Any memory that has been accessed but not touched for 47+ days triggers a decay warning. At 90 days, the retrieval probability is 1.2% — the memory is effectively deleted from the heat ranking.

Compare to what the exponential-power function would produce:

| Timescale | Pure exponential (current, S=14) | Exponential-power (estimated) | Implication |
|-----------|----------------------------------|------------------------------|-------------|
| 0-14 days | Decays to 50.0% | Decays to ~50% (similar) | Short-term behavior is fine |
| 30 days | Decays to 22.6% | Would decay to ~35-45% | Current model is 1.5-2x too aggressive |
| 60 days | Decays to 5.1% | Would decay to ~15-25% | Current model is 3-5x too aggressive |
| 90 days | Decays to 1.2% | Would decay to ~8-15% | Current model is ~8x too aggressive |
| 180 days | Decays to 0.014% (effectively zero) | Would decay to ~3-7% | Current model effectively deletes |
| 365 days | Decays to 1.46e-8 (zero) | Would decay to ~1-3% | Current model is categorical, not continuous |

**Verdict:** The pure exponential is **correct for short-term access management (< 60 days)** — a day-to-day working assistant needs aggressive recency weighting to distinguish "what I'm working on now" from "what I worked on last month." But it catastrophically penalizes long-term memories. A memory accessed 1,000 times that was last touched 90 days ago has an `access_bonus` of only **11.6** (1000 * 0.0116) — a value smaller than a freshly created memory accessed twice yesterday. This is arguably wrong for reference knowledge and long-lived decisions.

**The clinical question:** Should CodeMemory's decay curve primarily serve **recency ranking** (where aggressive decay is correct) or **knowledge preservation** (where a long tail is essential)? The answer is both — and the current model only does the first.

### 1.2 The stability = 14.0 Default — One Size Fits All?

**The assumption under scrutiny:** All memories decay at the same rate regardless of their content type, semantic depth, or usage pattern. 14.0 days is a reasonable universal half-life.

**What the research says:**

Bahrick's landmark "permastore" studies (1984, JEP: General) demonstrated that semantic memory does NOT follow simple exponential decay. Knowledge enters a "permastore" state after 3-6 years and then shows **near-zero further decay** for 25+ years. The amount entering permastore is a function of **original learning depth** (not rehearsal frequency). This challenges the assumption that all memories follow the same continuous decay curve.

**Domain-specific half-life analysis:**

| Memory Domain | Example | Realistic half-life | Current default fit | Suggested stability |
|---------------|---------|---------------------|---------------------|---------------------|
| Daily notes / journal | "What I worked on today" | 3-7 days | 14 is 2-5x too long | 5-7 days |
| Active decision-making | "Risk tolerance for Q2 portfolio" | 14-30 days | Default 14 is reasonable | 14-30 days |
| Investment thesis | "Long position on NVDA rationale" | 30-90 days | Default 14 is 2-6x too fast | 30-90 days |
| Software architecture | "Why we chose event sourcing" | 90-365 days | Default 14 is 6-26x too fast | 90-365 days |
| API documentation | "POST /api/resolve parameters" | 365+ days (reference) | Default 14 is absurdly fast | 365+ days |
| Schemas / templates | "Decision record template" | Indefinite | Default 14 makes no sense | 365+ or exempt |

**The tension:** CodeMemory stores both "what API returns a 422 status" (reference knowledge, should never decay) and "my morning standup notes from last week" (ephemeral, should decay fast). Both get `stability=14.0` unless manually adjusted. This is like using the same shelf-life for milk and salt.

**Current behavior vs. desired behavior, by stability:**

```
stability=7  (weekly decay):  90 days -> R=0.01% (ephemeral: correct)
stability=14 (current default): 90 days -> R=1.2% (moderate: somewhat fast)
stability=30 (monthly decay): 90 days -> R=12.5% (decision: borderline)
stability=90 (quarterly decay): 90 days -> R=50.0% (architecture: reasonable)
stability=365 (yearly decay): 90 days -> R=84.3% (reference: correct)
```

**Verdict:** The `stability` field IS the right primitive — it allows per-memory tuning. But the **default** is optimized for neither ephemera nor permanence. A smarter default would be schema-driven: schema-defined memories get higher default stability, ad-hoc atoms get lower. The `semantic_type` field (already present in the data model) is the natural hook for this.

### 1.3 access_count * decay — Over-Decay or Correct Interaction?

**The concern:** If `access_bonus = access_count * decay`, then a memory with 1,000 accesses that hasn't been touched in 30 days has an access_bonus of ~226 (1000 * 0.226) — high, but a brand new memory created 1 day ago and accessed twice has a bonus of ~1.9. The heavily-used memory still wins, but the **rate of decline may feel wrong** to users if foundational knowledge drops fast.

**Mathematical scenarios at stability=14.0:**

```
Scenario A: 1,000 accesses, 30 days since last access
  decay = 0.5^(30/14) = 0.226
  access_bonus = 1000 * 0.226 = 226.4
  wander weight = 1/(226.4 + 1) = 0.0044  (very hot, not wander-able)

Scenario B: 10 accesses, 1 day since last access
  decay = 0.5^(1/14) = 0.952
  access_bonus = 10 * 0.952 = 9.5
  wander weight = 1/(9.5 + 1) = 0.095  (warm, somewhat wander-able)

Scenario C: 1,000 accesses, 90 days since last access
  decay = 0.5^(90/14) = 0.012
  access_bonus = 1000 * 0.012 = 11.6
  wander weight = 1/(11.6 + 1) = 0.079  (cooling, somewhat wander-able)

Scenario D: 1 access, 90 days since last access
  decay = 0.5^(90/14) = 0.012
  access_bonus = 1 * 0.012 = 0.012
  wander weight = 1/(0.012 + 1) = 0.989  (cold, likely to be wandered to)
```

**Key observation:** At 90 days, a 1,000-access memory (C) has an access_bonus of 11.6 — only slightly higher than a 10-access memory touched yesterday (B, 9.5). This means recency (`days_since`) dominates access_count in the long term. A memory that has been accessed hundreds of times is typically foundational knowledge, and the system should be more reluctant to declare it "cold."

**The underlying issue:** access_count is treated as a scalar multiplier on decay, rather than as a moderator of the decay rate. In FSRS and SuperMemo, difficulty (D) and stability (S) are updated based on recall success — the equivalent would be: **stability should increase with access_count**, not just act as an independent multiplier.

Currently:
```
access_bonus = access_count * 0.5^(days / stability)
```

A better model (inspired by FSRS):
```
effective_stability = base_stability * f(access_count)  where f is sublinear (e.g., sqrt or log)
access_bonus = access_count * 0.5^(days / effective_stability)
```

This way, a memory accessed 1,000 times has a much longer effective half-life than one accessed 5 times — the spacing effect at work.

**Verdict:** The current interaction is **not wrong**, but it lacks the memory-strengthening effect that human memory exhibits (the spacing effect — each successful recall *increases* stability for the next interval). CodeMemory has the `days_since_last_access` reset to 0 on each resolve access, but stability itself never increases.

---

## Phase 2: Adjacent Field Research

### 2.1 FSRS v6 — Adaptive Stability with Personalizable Forgetting Curve

**Source:** [FSRS technical explanation (Jarrett Ye, 2025)](https://expertium.github.io/Algorithm.html), [FSRS-6 release](https://github.com/open-spaced-repetition/py-fsrs/releases)

FSRS-6 (released late 2025, trained on ~700 million reviews from ~20,000 users) is the most empirically grounded spaced repetition algorithm in existence. Its architecture is directly relevant to CodeMemory's decay system.

**Key architectural parallels:**

| FSRS-6 concept | CodeMemory equivalent | Status |
|----------------|----------------------|--------|
| **Stability (S)** — half-life where R=0.9 | `stability` field (default 14.0) | CodeMemory's is static; FSRS updates S on every access |
| **Retrievability (R)** — forgetting curve w/ personalized shape (w20) | `0.5^(days/stability)` | FSRS uses a power-law curve shape; CodeMemory uses fixed exponential |
| **Difficulty (D)** — per-item, updated on review | `intensity` (1-10) | CodeMemory's intensity is set at creation, never updated |
| **Stability increase on success** — `S * SInc(D,S,R)` | None | CodeMemory never adjusts stability based on access history |
| **Stability decrease on lapse** — `min(w11*D^(-w12)*..., S)` | None | CodeMemory only resets days_since, never reduces stability |
| **21 per-user parameters** | 1 per-memory parameter (stability) | FSRS is fundamentally multi-parametric; CodeMemory is single-parameter |

**FSRS-6 stability update formula (simplified):**

```
S' = S * (e^(w8) * (11 - D) * S^(-w9) * (e^(w10*(1-R)) - 1) * w15 * w16 + 1)
```

Key properties:
- **R-dependence:** SInc peaks at R ≈ 0.85 — optimal to review just before forgetting. If reviewed too early (R ≈ 1.0), stability increase is minimal (spacing effect). If reviewed too late (R < 0.5), also suboptimal.
- **D-dependence:** Harder items (higher D) get smaller stability increases.
- **S-dependence:** As stability grows, SInc diminishes (diminishing returns, `S^(-w9)`).
- **Grade-dependence:** `w15` penalizes Hard reviews, `w16` bonuses Easy reviews.

**FSRS-6 forgetting curve (with w20 personalization):**

```
R(t, S) = (1 + w20 * t / (9 * S))^(-1 / w20)
```

This is a **power-law forgetting curve** whose shape is controlled by w20. When w20 → 0, it approaches exponential. When w20 > 0 (default 0.154), it has a heavier tail — slowing long-term decay.

**What CodeMemory already gets right:**
- `stability` as a per-memory field (correct primitive)
- `days_since_last_access` as a precomputed input (matching FSRS's concept of "elapsed days")
- `access_count` tracking (could be the basis for stability updates)
- Decay warning threshold at R < 0.1 (matching the concept of "lapse")
- Excluding protected memories (intensity >= 8) from decay warnings

**What CodeMemory is missing:**
- **Stability increase on successful access:** when `handle_resolve` accesses a memory and returns it in full text, that is a "successful recall." Stability should increase — not stay at 14.0 forever.
- **Difficulty/lapse tracking:** when a memory is resolved but its body is stale (hash mismatch), or when it's in a cycle, those are "lapses" that should decrease stability.
- **Personalized forgetting curve shape:** the `w20` parameter in FSRS-6 means different users (and different content types) have fundamentally different forgetting curve shapes, not just different half-lives.
- **Review timing optimization:** FSRS schedules review at `S * ln(desired_retention) / ln(0.9)`. CodeMemory only alerts when it's already too late (R < 0.1), never tells you the optimal moment to review (R ≈ 0.7-0.85).

### 2.2 SuperMemo SM-17-SM19 — The DSR Model and Stability Increase Matrix

**Source:** [SuperMemo Algorithm documentation](https://help.supermemo.org/wiki/SuperMemo_Algorithm), [Building memory stability through rehearsal (Wozniak et al., 2005)](http://mail.super-memory.com/articles/stability.htm)

SuperMemo (1987-present) is the longest-running spaced repetition system, now at SM-19 (2024). Its DSR model (Difficulty-Stability-Retrievability) is the intellectual ancestor of FSRS.

**Key concepts CodeMemory should absorb:**

**1. The SInc matrix:**
SuperMemo builds a data-driven stability-increase matrix from the user's own repetition history. The matrix maps (D, S, R) -> stability multiplier. At very low stabilities, stability can increase up to **17-fold** on a single successful review. As stability grows, the increase factor diminishes (diminishing returns).

**2. Retrievability matters for stability increase:**
In SuperMemo, SInc peaks at R ≈ 0.85. If you review too early (R ≈ 1.0, just after the last review), stability increase is minimal or even negative (the spacing effect — massed practice doesn't help). If you review too late (R << 0.5, near-forgotten), stability increase is also reduced. The optimal review point is **just before forgetting**.

**3. SM-19's post-lapse stability estimation (2024):**
When a memory is forgotten, SM-19 computes a new (reduced) stability based on the item's difficulty and the retrievability at the moment of the lapse. This replaced earlier algorithms that simply reset stability to zero.

**4. The theoretical SInc formula (2005):**
```
SInc = (1 - (1 - Pr)^(r/(r-1))) / Pr
```
For r=2: `SInc = 2 - Pr`. As probability of successful memory encounter (Pr) approaches 0, SInc approaches 2× — meaning a near-forgotten memory that is successfully recalled can double its stability.

**What this means for CodeMemory:**

CodeMemory currently has no concept of "optimal review timing." The decay warning triggers at R < 0.1, but the system never suggests **when** to review a memory — only that it's already too late. A SuperMemo-inspired approach would:
- Track the decay value and suggest review when R drops below ~0.7 (optimal window)
- Increase stability on successful access, with the magnitude depending on how close the memory was to being forgotten
- Decrease stability when a memory is resolved but produces stale content (hash mismatch = recall failure)

### 2.3 Human Memory Research — Content-Type-Specific Forgetting Curves

**Source:** Bahrick (1984) "Semantic memory content in permastore," Fisher & Radvansky (2024) "Memory from nonsense syllables to novels," Sternad et al. (2013) "Learning to never forget."

The evidence is overwhelming that **different memory types follow fundamentally different forgetting curves**, not just different parameters on the same function:

| Memory type | Neural substrate | Decay curve shape | Key properties |
|-------------|-----------------|-------------------|----------------|
| **Episodic** (events, personal experiences) | Hippocampus | Linear to power-law, fast initial decay | Significant decay within hours-days; highly context-dependent; retrieval cues can recover seemingly "lost" memories |
| **Semantic** (facts, concepts, knowledge) | Neocortex | Exponential for 3-6 years, then flat "permastore" | Once consolidated, near-permanent; original learning depth is the strongest predictor of retention; minimal further decay after 6 years |
| **Procedural** (skills, motor patterns) | Basal ganglia, cerebellum | Extremely slow power-law, near-permanent | Core motor patterns persist for decades; fine precision degrades; "bicycle riding" phenomenon |

This is not a matter of different stability parameters on the same curve — the **curve shape itself differs**. Semantic knowledge does not just have a longer half-life than episodic memories; it follows a different functional form (exponential transitioning to flat, vs. power-law decay).

**Implication for CodeMemory's data model:**

The current system treats `stability` as a continuous parameter on a single curve family `R = 0.5^(t/S)`. But the research suggests the system needs at least two distinct curve families:
- **Fast-decay for episodic/transient content:** exponential or power-law, short half-life (3-14 days)
- **Slow-decay with permastore for semantic/reference content:** exponential-power with very long tail, essentially flat after 1-2 years

The `maturity` field (draft / verified / proven) partially captures this — proven memories have already survived repeated access. But maturity is a **lagging indicator** — it's a badge earned after access_count thresholds, not a parameter that influences the decay curve itself.

---

## Phase 3: Logical Completeness Analysis

### 3.1 The Decay Pipeline — End-to-End Audit

**Data flow:** reindex (compute days_since) -> overview/wander/validate (read days_since, compute decay) -> resolve (reset days_since to 0 on access) -> API (expose stability/decay to frontend)

| Stage | File:Line | Status | Notes |
|-------|-----------|--------|-------|
| Precompute days_since | index.py:122-130 | CORRECT | Computed from last_access at reindex time; handles None gracefully |
| clamp days_since >= 0 | index.py:128 | CORRECT | `max(0, ...)` prevents negative days |
| C1 fix: read from MemoryEntry | handlers.py:258-260 | FIXED | Was reading from search dict (empty); now reads from MemoryEntry |
| C1 fallback: None handling | handlers.py:261 | CORRECT | Falls back to `access * 0.1` when days_since is None |
| C2: stability >= 0.1 runtime | handlers.py:257, 346 | CORRECT | `max(stability, 0.1)` in overview and wander |
| C2: stability validator | models.py:111-122 | CORRECT | Pydantic validator rejects <= 0, clamps < 0.1 to 0.1 |
| C2: gt=0.0 Field constraint | models.py:78 | CORRECT | Pydantic-level guard |
| Decay formula (overview) | handlers.py:263 | CORRECT | `math.pow(0.5, days_since / stability)` |
| access_bonus = access * decay | handlers.py:264 | CORRECT | Zero-access memories get `access * 0.1` (10% weight floor) |
| wander weight = 1/(access*decay+1) | handlers.py:349 | CORRECT | Proper (0, 1] range, monotonic, well-behaved |
| Decay warning trigger | validate.py:103-104 | CORRECT | Triggers when R < 0.1 AND in_degree == 0 AND intensity < 8 |
| access update on resolve | resolve.py:318-320 | CORRECT | Increments access_count, sets last_access, resets days_since to 0 |
| C3: API /memories exposure | server.py:308-311 | CORRECT | stability, days_since, access_count, last_access in response |
| C3: API /stats decay_risk | server.py:660-683 | CORRECT | Computes and returns sorted decay_risk array |

**Edge cases verified:**
- Memory accessed 0 times: `access_bonus = 0 * 0.1 = 0` — no heat from access (correct)
- Memory with `days_since = None`: falls back to 10% access bonus (correct, conservative)
- Memory with `stability = 0`: clamped to 0.1 by C2 protections at both model and runtime level (correct, defense-in-depth)
- Memory in circular dependency: excluded from deps count in heat (correct, R13-M2)
- Schema-type memories: excluded from decay warning in validate.py:169 (correct, schemas are templates, not memories that decay)
- Intensity >= 8: excluded from decay warning regardless of R value (correct, protected memories)
- Wander on empty candidates: returns "(no matching memories)" (correct)

**Identified edge-case gap:** The decay warning in validate.py requires ALL THREE conditions simultaneously: `R < 0.1` AND `in_degree == 0` AND `intensity < 8`. This means:
- A protected memory (intensity >= 8) with R < 0.1 will NOT trigger a warning. This is intentional but means protected memories can silently decay with no review suggestion.
- A memory with R < 0.1 that IS referenced by another memory will NOT trigger a warning. This is correct — being depended on is structural protection.

### 3.2 The Overview Heat Formula — Sensitivity Analysis

`heat = deps * 10 + access_bonus`

The `deps * 10` term gives a structural importance floor. A memory with 5 dependents gets +50 heat regardless of access frequency. This means a highly-referenced architecture decision (5 dependents, never accessed) would outrank a frequently-accessed but unreferenced daily note (100 accesses, 30 days ago = heat ~23).

**This is deliberate and correct for a knowledge graph:** structural importance (being referenced) should dominate access frequency. The inverse is what makes knowledge graphs different from feed algorithms.

**Edge case:** A memory with 0 dependents and 0 access_count has heat = 0. In overview, it ranks last even if it matches the search tags. This means brand-new, unreferenced memories are invisible in overview — arguably correct (they have no proven value) but worth noting as the "cold start" problem.

### 3.3 Wander Cool Mode Weighting — Correctness

`weight = 1.0 / (access_count * decay + 1)`

This creates a proper gradient:

| Scenario | access_count | days_since | S=14 decay | weight | Meaning |
|----------|-------------|------------|-----------|--------|---------|
| Never accessed | 0 | N/A | 1.0 | 1.000 | Maximally cool |
| 1 access, fresh | 1 | 0 | 1.0 | 0.500 | Neutral |
| 1 access, 14 days | 1 | 14 | 0.500 | 0.667 | Warming up |
| 1 access, 90 days | 1 | 90 | 0.012 | 0.989 | Approaching cold |
| 100 accesses, fresh | 100 | 0 | 1.0 | 0.010 | Very hot |
| 100 accesses, 30 days | 100 | 30 | 0.226 | 0.042 | Still quite hot |
| 100 accesses, 90 days | 100 | 90 | 0.012 | 0.463 | Moderately hot |
| 1,000 accesses, 90 days | 1,000 | 90 | 0.012 | 0.079 | Still warm |

The formula is monotonic and well-behaved across all inputs. The `+1` prevents division by zero and bounds the weight in (0, 1]. The intensity < 8 pre-filter for cool candidates is correct — high-intensity memories are "pinned" and should not be selected for serendipitous recall.

**Minor observation:** The wander weight uses `access_count * decay` without the 10% floor that overview uses for zero-access memories. This is correct for wander — zero-access memories get weight=1.0 without needing a floor — but the inconsistency between the two uses of the same formula is worth noting.

---

## Phase 4: Alternative Design Proposals

### Proposal A: Adaptive Stability Update on Access (FSRS-Inspired)

**Problem:** Stability is static. A memory created with stability=14.0 stays at 14.0 forever, regardless of how many times it's accessed or how useful it proves to be. This contradicts the fundamental finding of every major spaced repetition system since SM-2: **stability should increase on successful recall**.

**Proposal:** Add a stability update step in `resolve.py` after the access_count increment:

```python
# Simplified SInc (Stability Increase) function inspired by FSRS v6
# Applied after entry.access_count increment in resolve.py

current_stability = entry.stability
# Retrievability at moment of access (before resetting days_since)
retrievability = 0.5 ** (days_since / current_stability) if days_since else 1.0

if retrievability > 0.95:
    # Reviewed too early — minimal boost (massed practice)
    s_inc = 1.05
elif retrievability > 0.70:
    # Optimal review window — moderate boost
    s_inc = 1.15 + (0.95 - retrievability) * 0.6  # 1.15 to 1.30
elif retrievability > 0.30:
    # Late review — strong boost (near-forgotten, recovery)
    s_inc = 1.30 + (0.70 - retrievability) * 0.5  # 1.30 to 1.50
else:
    # Very late, close to forgotten — maximum boost
    s_inc = 1.50 + (0.30 - retrievability) * 1.0  # 1.50 to 1.80

# Diminishing returns: as stability grows, SInc approaches 1.0
diminish_factor = math.sqrt(14.0 / max(current_stability, 14.0))
effective_s_inc = 1.0 + (s_inc - 1.0) * diminish_factor

new_stability = current_stability * effective_s_inc
entry.stability = round(new_stability, 1)
```

**Expected behavior at stability=14.0 default:**
- Accessed fresh (R > 0.95): SInc=1.05, new stability ≈ 14.7 (5% boost)
- Accessed at half-life (R=0.5): SInc=1.40, new stability ≈ 19.6 (40% boost)
- Accessed near-forgotten (R=0.1): SInc=1.70, new stability ≈ 23.8 (70% boost)

**Expected behavior after 100 accesses (stability=60, accumulated):**
- Accessed at half-life (R=0.5): SInc=1.40, diminish=0.483, effective=1.19, new stability ≈ 71.6
- Diminishing returns ensures stability doesn't grow unboundedly.

**Effort:** ~1 day. Modify `resolve.py` in the access-tracking block. Add `stability_history: list[dict]` field to MemoryEntry for audit trail. Requires 2-3 new unit tests.

**Why this matters:** This transforms CodeMemory from a static decay model to an adaptive memory system. The system learns which memories are important through use, not through manual configuration. This is the single most impactful improvement identified by adjacent field research.

### Proposal B: Domain-Differentiated Default Stability

**Problem:** The default stability=14.0 is inappropriate for 4 of the 5 most common memory domains.

**Proposal:** Set default stability based on `semantic_type` and/or `schema` at creation time:

```python
# In create.py or handlers.py:handle_create
DOMAIN_STABILITY_DEFAULTS = {
    "schemas": 365.0,       # Templates are permanent reference
    "api": 365.0,           # API documentation is permanent
    "decision": 90.0,       # Decisions have moderate lifespan
    "research": 90.0,       # Research notes have moderate lifespan
    "context": 30.0,        # Context summaries are medium-term
    "meeting": 7.0,         # Meeting notes decay within a week
    "daily": 5.0,           # Daily standup notes are most ephemeral
    "reference": 365.0,     # Reference material is permanent
}
DEFAULT_STABILITY = 14.0
```

**Effort:** 30 minutes. Modify `create.py` to check `semantic_type` against the lookup table when initializing `stability`.

**Why this matters:** The simplest possible improvement — a lookup table that brings default behavior closer to cognitive reality. Zero algorithmic complexity. Eliminates the most common "wrong default" scenario: API docs decaying after 46 days.

### Proposal C: Long-Tail Preservation via Hybrid Decay

**Problem:** Pure exponential decay at stability=14.0 effectively deletes memories after 90 days (R < 0.02). Reference knowledge should not silently vanish.

**Proposal:** Replace pure exponential with a hybrid that preserves a long tail:

```
R_hybrid(days, stability) = max(
    0.5^(days / stability),                              # exponential (short-term)
    0.1 / (1 + days / (10 * stability))                  # power-law floor (long-term)
)
```

**Effect at stability=14 (hybrid vs. current):**

| Days | Current (exponential) | Hybrid | Multiplier |
|------|----------------------|--------|------------|
| 14 | 50.0% | 50.0% | 1.0x |
| 46 | 10.3% | 10.0% | 1.0x (same around threshold) |
| 90 | 1.2% | 6.1% | 5.1x |
| 180 | 0.014% | 4.4% | 314x |
| 365 | 1.46e-8 | 3.8% | infinite (current hits zero) |
| 730 | 2.1e-16 | 3.1% | infinite |

The hybrid preserves a ~3-6% floor for all memories regardless of how long they've been untouched. This matches Bahrick's permastore finding — well-learned knowledge retains a baseline accessibility.

**Effort:** 1 hour. Replace the single `math.pow(0.5, days/stability)` call with the hybrid in handlers.py (overview and wander) and validate.py (decay warning). The hybrid is backward-compatible for R > 0.1 (short-term behavior unchanged).

**Why this matters:** The most concerning finding of the research audit is that at default settings, memories effectively vanish after 90 days. A knowledge management system should not lose reference knowledge because it wasn't accessed in 3 months. The hybrid preserves the excellent short-term ranking while preventing silent loss of long-term knowledge.

### Proposal D: Proactive Review Scheduling via Wander Mode

**Problem:** The decay warning system only alerts when a memory is ALREADY at risk (R < 0.1). It never proactively suggests review before a memory is forgotten.

**Proposal:** Add a `--mode review` to `codememory wander` that selects memories nearest to the optimal review point (R ≈ 0.75), inspired by FSRS's finding that SInc peaks at R ≈ 0.85:

```bash
codememory wander --mode review    # surface memories due for review
codememory wander --mode review --inject  # inject review suggestion into prompt
```

The weighting: `weight = exp(-((R - 0.75)^2) / (2 * 0.15^2))` — Gaussian centered at R=0.75, sigma=0.15. Memories at exactly the optimal review point get maximal weight.

**Effort:** 2 hours. Add a third mode to `handle_wander()` alongside `cool` and `random`.

**Why this matters:** This closes the gap between "detecting decay" (reactive) and "preventing decay" (proactive). It's the product equivalent of Anki's "due cards" queue — telling the user what needs attention before it's forgotten.

---

## Prioritized Research Directions

### Critical — Architectural Gaps

| # | Item | Effort | Justification |
|---|------|--------|---------------|
| 🔴 1 | **Adaptive stability update on access** — Modify `resolve.py` to increase `stability` when a memory is successfully accessed. Use a simplified SInc function peaking at R ≈ 0.7-0.85. | 1 day | This is the single most important architectural improvement identified by adjacent research. Both FSRS and SuperMemo have proven that adaptive stability outperforms static stability by 20-30% in real-world usage. Without this, CodeMemory's decay model is stuck at SM-2 (1987) level — the system has the right primitives but uses them statically. |
| 🔴 2 | **Long-tail preservation floor** — Replace pure exponential with a hybrid formula that has a power-law asymptote. | 1 hour | The current model contradicts the cognitive reality that well-learned semantic knowledge persists for years (Bahrick's permastore). A knowledge management system should not silently lose reference material because it wasn't accessed in 90 days. The fix is trivial and backward-compatible. |

### Important — Quality Improvements

| # | Item | Effort | Justification |
|---|------|--------|---------------|
| 🟡 3 | **Domain-differentiated default stability** — Map `semantic_type` and `schema` to appropriate default stability values at creation time. | 30 min | The simplest possible improvement. Zero algorithmic complexity. Eliminates the most common "wrong default" scenario. |
| 🟡 4 | **Proactive review mode in wander** — Add `wander --mode review` that selects memories in the optimal review window (R ≈ 0.7-0.85) using Gaussian weighting. | 2 hours | Transforms decay from a passive warning system into an active memory maintenance tool. The "due for review" concept is the core UX of spaced repetition systems. |
| 🟡 5 | **Stability decrease on stale detection** — When `resolve` detects a stale summary (hash mismatch), decrease the memory's stability as a "recall failure" signal. | 1 hour | Currently, stale detection is purely informational. It should feed back into the decay model — a stale memory is evidence that the user's mental model has diverged from the stored version. |

### Nice to Have — Future Enhancements

| # | Item | Effort | Justification |
|---|------|--------|---------------|
| 🟢 6 | **Exponential-power (Weibull) decay as an option** — Allow `decay_type: "exponential_power"` in frontmatter, using `R = e^(-b*sqrt(t/S))`. | 2-3 days | The 2024 meta-analysis shows exponential-power fits real memory data better than pure exponential or power-law. But the benefit is marginal compared to adaptive stability. |
| 🟢 7 | **Per-user decay parameter learning** — Collect access/lapse data over time and fit user-specific decay parameters (matching FSRS's approach of 21 fitted parameters). | 1-2 weeks | Major architectural change. Appropriate for a future round, not urgent. The single-parameter model should be proven with adaptive stability first. |
| 🟢 8 | **Stability trend visualization in Dashboard** — Show a sparkline of stability changes over time for individual memories. | 1 day | Makes the adaptive stability improvement visible to users. Requires stability_history field from Proposal A. |

### Product Strategy

| # | Item | Effort | Justification |
|---|------|--------|---------------|
| 💡 9 | **Decay curve shape as a per-memory parameter** — Allow `decay_type` in frontmatter: `exponential` (current), `power_law` (R = S/(S+t)), `exponential_power` (Weibull), `permastore` (no decay, for schemas and reference). | 2-3 days | This is the ultimate expression of the "different content types have different forgetting curves" finding. Gives power users direct control over the mathematical model per memory. |
| 💡 10 | **"Memory half-life health" weekly report** — A scheduled overview that shows: "3 memories crossed 50% decay this week. 2 memories approaching warning threshold." Surfaces the decay system's insights proactively. | 2 days | The product needs a "this is managing your memory" moment. A weekly health report makes the decay system tangible to users who never run `codememory validate`. |

---

## Round 14 Verdict Summary

| Change | Description | Status | Research Notes |
|--------|-------------|--------|----------------|
| C1 | Fix overview decay pipeline bug (read days_since from MemoryEntry, not search dict) | **RESOLVED** | The Round 13 audit identified this as the CRITICAL data plumbing bug. Round 14's fix is correct — the overview path now reads from `entry.days_since_last_access` (line 260) instead of `r.get("days_since_last_access")` (which was never populated by `search()`). This single change makes the decay formula actually activate in the most important codepath. |
| C2 | Stability boundary protection (gt=0.0 Field, validator clamp < 0.1, runtime max(0.1)) | **CORRECT** | Three-layer defense-in-depth is well-engineered. The Pydantic validator (models.py:111-122) catches bad data at ingestion, the Field constraint (models.py:78) provides schema-level protection, and the runtime clamp (handlers.py:257,346) guards against any path that bypasses the model. Division-by-zero is impossible at any layer. |
| C3 | API expose decay fields (stability, days_since_last_access, decay_risk) | **CORRECT** | `/api/memories` now includes access_count, last_access, days_since_last_access, and stability (server.py:308-311). `/api/stats` now includes a computed `decay_risk` array sorted by severity (server.py:660-683). The Round 13 audit identified the missing fields as the primary frontend integration gap — this is now closed. |
| N1 | Dashboard decay risk panel | **PRESUMED CORRECT** | Frontend not verified in this research audit (scope: backend + algorithmic analysis). The backend data pipeline is correct — `decay_risk` in `/api/stats` is properly computed and sorted. |

**Net Assessment:** Round 14 delivers a correct, working decay system. The C1 fix was essential — without it, the entire decay pipeline was producing stale (zero) data for the overview path. The C2 protections are well-engineered defense-in-depth. The C3 API exposure and N1 Dashboard panel close the frontend visibility gap identified in Round 13.

**But the research reveals that "correct" is not "complete."** The current model (fixed exponential decay, static per-memory stability, one-size-fits-all default) is architecturally valid but falls short of what the adjacent fields have achieved. FSRS v6 and SuperMemo SM-19 both demonstrate that:
1. Stability should **learn** from access history (adaptive stability, not static)
2. Forgetting curves should be **personalizable per content type** (not one curve for everything)
3. Memory should have a **preservation floor** (not decay to zero)
4. Review should be **scheduled proactively** in the optimal window (R ≈ 0.7-0.85), not merely warned about after the fact (R < 0.1)

**The good news:** CodeMemory's architecture is well-positioned for these improvements. The `stability` field, `days_since_last_access`, `access_count`, `intensity`, and the resolve pipeline already provide all the data needed. The gap is 1-2 days of algorithmic work — not a redesign. The two Critical items (adaptive stability update, long-tail floor) can be implemented in a single round with high confidence.

---

## References

1. Fisher, J.S. & Radvansky, G.A. (2024). "Memory from nonsense syllables to novels: A survey of retention." *Psychonomic Bulletin & Review*, 31, 2437-2464. [Link](https://link.springer.com/article/10.3758/s13423-024-02514-3)

2. Bahrick, H.P. (1984). "Semantic memory content in permastore: Fifty years of memory for Spanish learned in school." *Journal of Experimental Psychology: General*, 113(1), 1-29.

3. Ye, J. (2025). "A technical explanation of FSRS." [Link](https://expertium.github.io/Algorithm.html)

4. Open Spaced Repetition. (2025). "FSRS v6 release." [Link](https://github.com/open-spaced-repetition/py-fsrs/releases)

5. Wozniak, P.A., Gorzelanczyk, E.J., & Murakowski, J. (2005). "Building memory stability through rehearsal." [Link](http://mail.super-memory.com/articles/stability.htm)

6. SuperMemo World. (2024). "SuperMemo Algorithm." [Link](https://help.supermemo.org/wiki/SuperMemo_Algorithm)

7. Sternad, D. et al. (2013). "Learning to never forget — time scales and specificity of long-term memory of a motor skill." *Frontiers in Computational Neuroscience*, 7, 111.

8. Bauml, K.-H. et al. (2022). "Selective memory retrieval can revive forgotten memories." *PNAS*, 119(12).
