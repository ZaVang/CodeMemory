"""Dependency suggestion via three-layer filtering algorithm.

Layer 1: Tag intersection score — shared tags between target and candidate.
Layer 2: Schema structural pattern — what same-schema instances commonly import.
Layer 3: Heat-weighted ranking — score = tag_overlap * 3 + schema_pattern_score * 5 + dependents.

Forward: "which existing memories should the target import?"
Retroactive: "which existing memories should import the target?"
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .index import load_index
from .models import IndexData, MemoryEntry

_logger = logging.getLogger("codememory")


def _count_incoming_refs(memories: dict[str, MemoryEntry], target_id: str) -> int:
    """Count how many other memories reference *target_id* in their imports."""
    count = 0
    for other_id, entry in memories.items():
        if other_id == target_id:
            continue
        imports_dict = entry.imports
        if not isinstance(imports_dict, dict):
            continue
        for strength in ("required", "recommended", "related"):
            for ref in imports_dict.get(strength, []):
                if isinstance(ref, str) and ref == target_id:
                    count += 1
                elif isinstance(ref, dict) and ref.get("id") == target_id:
                    count += 1
    return count


def _build_schema_pattern(
    memories: dict[str, MemoryEntry],
    target_id: str,
    target_type: str,
    target_schema: str | None,
) -> dict[str, int]:
    """Count how many same-schema instances import each candidate.

    Only computed when the target is an ``instance`` with a known schema.
    """
    pattern: dict[str, int] = {}
    if target_type != "instance" or not target_schema:
        return pattern

    for mid, entry in memories.items():
        if mid == target_id:
            continue
        entry_schema = entry.schema
        if entry_schema != target_schema:
            continue
        imports_dict = entry.imports
        if not isinstance(imports_dict, dict):
            continue
        for strength in ("required", "recommended", "related"):
            for ref in imports_dict.get(strength, []):
                rid = ref if isinstance(ref, str) else ref.get("id", "")
                if rid:
                    pattern[rid] = pattern.get(rid, 0) + 1
    return pattern


def _has_same_domain_deps(
    entry: MemoryEntry,
    memories: dict[str, MemoryEntry],
    target_tags: set[str],
) -> bool:
    """Return True if *entry* already imports at least one memory that shares tags with the target."""
    imports_dict = entry.imports
    if not isinstance(imports_dict, dict) or not imports_dict:
        return False
    for strength in ("required", "recommended", "related"):
        for ref in imports_dict.get(strength, []):
            rid = ref if isinstance(ref, str) else ref.get("id", "")
            if rid and rid in memories:
                ref_tags = set(memories[rid].tags)
                if ref_tags & target_tags:
                    return True
    return False


def suggest_deps(
    root: Path,
    memory_id: str,
    min_score: int = 3,
    forward_only: bool = False,
    retroactive_only: bool = False,
) -> str:
    """Suggest dependencies for a memory using three-layer filtering.

    Parameters
    ----------
    root:
        Root directory for memory data.
    memory_id:
        Target memory to compute suggestions for.
    min_score:
        Minimum score threshold (default 3).
    forward_only:
        If True, only show forward candidates (target should import them).
    retroactive_only:
        If True, only show retroactive candidates (they should import the target).

    Returns
    -------
    Formatted suggestion text.
    """
    index: IndexData = load_index(root)
    memories: dict[str, MemoryEntry] = index.memories

    if memory_id not in memories:
        return f"Error: Memory '{memory_id}' not found in index. Did you reindex?"

    target = memories[memory_id]
    target_tags = set(target.tags)
    target_type = target.type
    target_schema = target.schema

    # ── Global incoming reference counts (used as "dependents" weight) ──
    incoming: dict[str, int] = {}
    for mid in memories:
        incoming[mid] = _count_incoming_refs(memories, mid)

    # ── Schema pattern (instance-mode only) ──
    schema_pattern = _build_schema_pattern(
        memories, memory_id, target_type, target_schema,
    )

    # ── Build candidate list ──
    candidates: list[dict[str, Any]] = []

    for other_id, entry in memories.items():
        if other_id == memory_id:
            continue

        # Layer 1: tag intersection
        other_tags = set(entry.tags)
        tag_overlap = len(target_tags & other_tags)
        if tag_overlap < 1:
            continue

        # Layer 2: schema pattern score
        schema_score = schema_pattern.get(other_id, 0)

        # Layer 3: score = tag_overlap * 3 + schema_pattern_score * 5 + dependents
        dependents = incoming.get(other_id, 0)
        score = tag_overlap * 3 + schema_score * 5 + dependents

        if score < min_score:
            continue

        candidates.append({
            "id": other_id,
            "type": entry.type,
            "summary": entry.summary,
            "tags": entry.tags,
            "tag_overlap": tag_overlap,
            "schema_score": schema_score,
            "dependents": dependents,
            "score": score,
            "retroactive": False,  # determined below
        })

    # Sort by score descending
    candidates.sort(key=lambda c: c["score"], reverse=True)

    # ── Retroactive inference ──
    # Candidate C qualifies as retroactive when:
    #   - tag_overlap >= 2, AND
    #   - C has no imports in the same tag domain (missing domain deps)
    for c in candidates:
        if c["tag_overlap"] >= 2:
            cand_entry = memories[c["id"]]
            if not _has_same_domain_deps(cand_entry, memories, target_tags):
                c["retroactive"] = True

    # ── Partition ──
    forward_candidates = [c for c in candidates if not c["retroactive"]]
    retroactive_candidates = [c for c in candidates if c["retroactive"]]

    # ── Score classification thresholds ──
    def _classify(score: int) -> str:
        if score >= 10:
            return "required"
        if score >= 6:
            return "recommended"
        return "related"

    lines: list[str] = []

    # ── Forward section ──
    if not retroactive_only:
        lines.append(f"# Suggest-deps for '{memory_id}' (forward)")
        lines.append(f"  Tags: {', '.join(target.tags)}")
        if target_type == "instance" and target_schema:
            lines.append(f"  Schema: {target_schema}")
        lines.append("")

        if forward_candidates:
            lines.append(f"{'Score':>5}  {'Class':<12}  {'Type':<9}  ID")
            lines.append(f"{'─'*5}  {'─'*12}  {'─'*9}  {'─'*40}")
            for c in forward_candidates:
                cls = _classify(c["score"])
                lines.append(
                    f"{c['score']:5d}  {cls:<12}  {c['type']:<9}  {c['id']}"
                )
                lines.append(
                    f"       tags: {', '.join(c['tags'])}"
                    f"  |  {c['summary'][:60]}"
                )
        else:
            lines.append("  (no forward candidates)")

    # ── Retroactive section ──
    if not forward_only and retroactive_candidates:
        if lines:
            lines.append("")
        lines.append(f"# Suggest-deps for '{memory_id}' (retroactive)")
        lines.append(f"  These memories may benefit from importing '{memory_id}':")
        lines.append("")
        lines.append(f"{'Score':>5}  {'Type':<9}  ID")
        lines.append(f"{'─'*5}  {'─'*9}  {'─'*40}")
        for c in retroactive_candidates:
            lines.append(
                f"{c['score']:5d}  {c['type']:<9}  {c['id']}"
            )
            lines.append(
                f"       tags: {', '.join(c['tags'])}"
                f"  |  {c['summary'][:60]}"
            )

    if not lines:
        return "(no suggestions)"

    return "\n".join(lines)
