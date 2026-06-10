"""Memory resolution: DAG construction, cycle detection, topological sort, token budget."""

import logging
import math
from datetime import datetime
from pathlib import Path

from .core import compute_body_hash, compute_retrieval_probability, estimate_tokens, parse_frontmatter
from .index import load_index, save_index
from .models import NON_ASSEMBLABLE_STATUSES, IndexData, MemoryEntry

_logger = logging.getLogger("codememory")


def _count_dependents(memory_id: str, index: IndexData) -> int:
    """Count how many other memories import this one."""
    count = 0
    for mid, entry in index.memories.items():
        if mid == memory_id:
            continue
        imports_dict = entry.imports
        if not isinstance(imports_dict, dict):
            continue
        all_refs = (
            imports_dict.get("required", [])
            + imports_dict.get("recommended", [])
            + imports_dict.get("related", [])
        )
        for ref in all_refs:
            ref_id = ref if isinstance(ref, str) else ref.get("id", "")
            if ref_id == memory_id:
                count += 1
                break
    return count


def _get_imports(entry: MemoryEntry | dict, depth: str) -> list[str]:
    """Extract dependency IDs from a memory's imports dict based on depth.

    Accepts both MemoryEntry and legacy dict for backward compatibility.
    """
    if isinstance(entry, MemoryEntry):
        imports_dict = entry.imports
    else:
        imports_dict = entry.get("imports", {})

    if not isinstance(imports_dict, dict):
        return []

    deps: list[str] = []
    for r in imports_dict.get("required", []):
        if isinstance(r, str):
            deps.append(r)
        elif isinstance(r, dict) and "id" in r:
            deps.append(r["id"])

    if depth in ("recommended", "full"):
        for r in imports_dict.get("recommended", []):
            if isinstance(r, str):
                deps.append(r)
            elif isinstance(r, dict) and "id" in r:
                deps.append(r["id"])

    if depth == "full":
        for r in imports_dict.get("related", []):
            if isinstance(r, str):
                deps.append(r)
            elif isinstance(r, dict) and "id" in r:
                deps.append(r["id"])

    return deps


def build_dag(memory_id: str, depth: str, index: IndexData) -> dict[str, list[str]]:
    """Build a dependency graph from the target memory.

    Returns {node_id: [dependency_ids]}.
    """
    graph: dict[str, list[str]] = {}
    queue = [memory_id]

    while queue:
        curr = queue.pop(0)
        if curr in graph:
            continue

        if curr not in index.memories:
            _logger.warning("Memory '%s' not found in index.", curr)
            graph[curr] = []
            continue

        entry = index.memories[curr]
        deps = _get_imports(entry, depth)
        graph[curr] = deps
        queue.extend(deps)

    return graph


def find_cycle_participants(graph: dict) -> list[str]:
    """Find all nodes involved in cycles using DFS coloring.

    0=white, 1=gray, 2=black
    """
    color = {u: 0 for u in graph}
    cycle_nodes: set[str] = set()

    def dfs(u, path):
        color[u] = 1
        for v in graph.get(u, []):
            if color.get(v, 0) == 1:
                cycle_start = path.index(v) if v in path else 0
                cycle_nodes.update(path[cycle_start:])
                cycle_nodes.add(v)
            elif color.get(v, 0) == 0:
                dfs(v, path + [v])
        color[u] = 2

    for u in graph:
        if color[u] == 0:
            dfs(u, [u])

    return list(cycle_nodes)


def topological_sort(graph: dict) -> list[str]:
    """Kahn's algorithm, reversed so dependencies come before dependents."""
    in_degree = {u: 0 for u in graph}
    for u in graph:
        for v in graph[u]:
            in_degree[v] = in_degree.get(v, 0) + 1

    queue = [u for u in in_degree if in_degree[u] == 0]
    topo_order: list[str] = []

    while queue:
        u = queue.pop(0)
        topo_order.append(u)
        for v in graph.get(u, []):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    return list(reversed(topo_order))


def resolve(
    root_dir: Path,
    memory_id: str,
    depth: str = "required",
    budget: int | None = None,
    focus: str | None = None,
) -> str:
    """Resolve and assemble memory context for a given memory ID.

    If ``focus`` is provided, nodes whose tags contain the focus type get
    full-text output; all others are downgraded to summary (never deleted).
    """
    index = load_index(root_dir)

    if memory_id not in index.memories:
        msg = f"Error: Target memory '{memory_id}' not found. Did you reindex?"
        _logger.error(msg)
        return msg

    target_status = index.memories[memory_id].status
    if target_status in NON_ASSEMBLABLE_STATUSES:
        msg = (
            f"Error: Target memory '{memory_id}' has status '{target_status}' and is not "
            f"assemblable. If it is a proposal, review it and run: codememory merge {memory_id}"
        )
        _logger.error(msg)
        return msg

    # 1. Build DAG
    graph = build_dag(memory_id, depth, index)

    # 2. Cycle Detection
    cycle_ids = find_cycle_participants(graph)
    if cycle_ids:
        _logger.warning("Circular dependency detected involving: %s", cycle_ids)
        _logger.warning("Skipping cycle nodes to continue resolution...")
        for u in list(graph.keys()):
            graph[u] = [v for v in graph[u] if v not in cycle_ids]

    # 2b. Drop non-assemblable nodes (proposed/archived/superseded) from the closure
    excluded_nodes = sorted(
        n for n in graph
        if n != memory_id and n in index.memories
        and index.memories[n].status in NON_ASSEMBLABLE_STATUSES
    )
    if excluded_nodes:
        for u in list(graph.keys()):
            graph[u] = [v for v in graph[u] if v not in excluded_nodes]
        for n in excluded_nodes:
            graph.pop(n, None)

    # 3. Topo Sort
    ordered = topological_sort(graph)

    for node in graph:
        if node not in ordered and node not in cycle_ids:
            ordered.insert(0, node)

    for node in cycle_ids:
        if node not in ordered:
            ordered.append(node)

    # 4. Token Trim & Output
    max_budget = budget if budget else float("inf")
    used = 0

    lines: list[str] = []
    lines.append(f"# Resolved Context for '{memory_id}'\n")
    if budget:
        lines.append(f"*(Depth: {depth}, Budget: {max_budget} chars)*\n")
    else:
        lines.append(f"*(Depth: {depth}, Budget: unlimited)*\n")

    req_graph = build_dag(memory_id, "required", index)
    rec_graph = build_dag(memory_id, "recommended", index)
    full_text_nodes: list[str] = []
    notices: list[str] = []
    stale_ids: list[str] = []  # R16-F5: track stale memories for stability decrease

    if excluded_nodes:
        notices.append(
            "[NOTICE] skipped non-assemblable nodes "
            f"(proposed/archived/superseded): {', '.join(excluded_nodes)}"
        )

    for i, mid in enumerate(ordered):
        if mid not in index.memories:
            continue

        entry = index.memories[mid]
        file_path = root_dir / entry.path
        meta, body = parse_frontmatter(file_path)

        # Stale detection
        stored_hash = meta.get("summary_hash", "")
        if stored_hash:
            actual_hash = compute_body_hash(body)
            if stored_hash != actual_hash:
                notices.append(
                    f"[NOTICE] summary may be stale for {mid} (hash mismatch). "
                    f"Run: codememory update {mid} --change-note \"update summary\""
                )
                # R16-F5: mark for stability decrease (applied after loop)
                if mid not in stale_ids:
                    stale_ids.append(mid)

        # Pin version check
        imports_dict = entry.imports
        if isinstance(imports_dict, dict):
            for strength in ("required", "recommended", "related"):
                for ref in imports_dict.get(strength, []):
                    if isinstance(ref, dict) and "pin" in ref:
                        ref_id = ref.get("id", "")
                        pin_version_str = ref.get("pin", "")
                        if ref_id and pin_version_str and ref_id in index.memories:
                            current_version = index.memories[ref_id].version
                            try:
                                pin_num = int(pin_version_str.lstrip("v"))
                            except ValueError:
                                continue
                            if current_version > pin_num:
                                notices.append(
                                    f"[NOTICE] pinned version {pin_version_str} of "
                                    f"{ref_id} is behind current version v{current_version}. "
                                    f"Review whether pin is still needed."
                                )

        # Build display labels
        cache_tag = ' [cache-stable]' if getattr(entry, 'cache_stable', False) else ''
        if focus:
            if focus in entry.tags:
                full_text = (
                    f"## [{i + 1}/{len(ordered)}] {mid} ({entry.type} - FOCUS{cache_tag})\n\n{body}\n\n"
                )
                summary_text = (
                    f"## [{i + 1}/{len(ordered)}] {mid} ({entry.type} - FOCUS - SUMMARY (budget){cache_tag})\n\n"
                    f"> {entry.summary}\n\n"
                )
            else:
                full_text = (
                    f"## [{i + 1}/{len(ordered)}] {mid} ({entry.type}{cache_tag})\n\n{body}\n\n"
                )
                summary_text = (
                    f"## [{i + 1}/{len(ordered)}] {mid} ({entry.type} - SUMMARY (focus filter){cache_tag})\n\n"
                    f"> {entry.summary}\n\n"
                )
        else:
            full_text = (
                f"## [{i + 1}/{len(ordered)}] {mid} ({entry.type}{cache_tag})\n\n{body}\n\n"
            )
            summary_text = (
                f"## [{i + 1}/{len(ordered)}] {mid} ({entry.type} - SUMMARY - budget{cache_tag})\n\n"
                f"> {entry.summary}\n\n"
            )

        t_full = estimate_tokens(full_text)
        t_sum = estimate_tokens(summary_text)

        is_required = mid in req_graph
        is_recommended = mid in rec_graph and not is_required

        # Focus mode: matching nodes get full text, others get summary
        if focus:
            if focus in entry.tags:
                # Matching focus: try full text first
                if used + t_full <= max_budget:
                    lines.append(full_text)
                    used += t_full
                    full_text_nodes.append(mid)
                else:
                    lines.append(summary_text)
                    used += t_sum
            else:
                # Not matching focus: always summary
                lines.append(summary_text)
                used += t_sum
        elif used + t_full <= max_budget:
            lines.append(full_text)
            used += t_full
            full_text_nodes.append(mid)
        elif is_required:
            lines.append(summary_text)
            used += t_sum
        elif is_recommended:
            lines.append(summary_text)
            used += t_sum
        else:
            lines.append(f"## [{i + 1}/{len(ordered)}] {mid} (SKIPPED - budget)\n\n")

    lines.append(f"---\nTotal Budget Used: {used}/{max_budget}")

    if notices:
        lines.append("")
        lines.append("## Notices")
        for notice in notices:
            lines.append(notice)

    # R16-F5: stability decrease for stale memories (recall failure signal)
    # Applied BEFORE access tracking so stale decrease and SInc don't conflict.
    STALE_DECAY = 0.90  # mild penalty — a single recall failure shouldn't erase consolidation
    STABILITY_FLOOR = 14.0  # never drop below the default domain baseline
    for mid in stale_ids:
        if mid in index.memories:
            stale_entry = index.memories[mid]
            old_stability = stale_entry.stability
            new_stability = max(old_stability * STALE_DECAY, STABILITY_FLOOR)
            if new_stability < old_stability:
                stale_entry.stability = new_stability
                notices.append(
                    f"[NOTICE] stability decreased for {mid}: "
                    f"{old_stability:.1f}d → {new_stability:.1f}d (stale recall)"
                )

    # Track access: increment access_count for full-text nodes
    now_iso = datetime.now().isoformat()
    maturity_changes: list[str] = []
    for mid in full_text_nodes:
        if mid in index.memories:
            entry = index.memories[mid]

            # R15-C1: Adaptive stability — compute retrieval probability BEFORE
            # updating access fields (days_since represents time before this access).
            # R16-C2: skip SInc if stability was manually set by the user.
            if getattr(entry, "stability_source", None) != "manual":
                old_days_since = entry.days_since_last_access
                if old_days_since is not None and old_days_since > 0 and entry.stability > 0:
                    R = compute_retrieval_probability(old_days_since, entry.stability)
                    # Simplified SInc — Gaussian peak at R ~ 0.78, range 1.05-1.80
                    s_inc = 1.05 + 0.75 * math.exp(-((R - 0.78) ** 2) / 0.125)
                    # Diminishing returns at high stability
                    diminish = math.sqrt(14.0 / max(entry.stability, 14.0))
                    entry.stability = min(entry.stability * s_inc * diminish, 365.0)

            entry.access_count += 1
            entry.last_access = now_iso
            entry.days_since_last_access = 0  # R13-M3: just accessed

            # Maturity auto-upgrade
            old_maturity = entry.maturity
            if old_maturity == "draft" and entry.access_count >= 3:
                entry.maturity = "verified"
                if "evidence" not in entry.__dict__ or entry.evidence is None:
                    entry.evidence = {}
                verified_in = entry.evidence.get("verified_in", [])
                verified_in.append({"version": entry.version, "date": now_iso[:10]})
                entry.evidence["verified_in"] = verified_in
                maturity_changes.append(f"{mid}: draft -> verified")
            elif old_maturity == "verified" and entry.access_count >= 10 and _count_dependents(mid, index) > 0:
                entry.maturity = "proven"
                if "evidence" not in entry.__dict__ or entry.evidence is None:
                    entry.evidence = {}
                verified_in = entry.evidence.get("verified_in", [])
                verified_in.append({"version": entry.version, "date": now_iso[:10]})
                entry.evidence["verified_in"] = verified_in
                maturity_changes.append(f"{mid}: verified -> proven")

    save_index(root_dir, index)

    # Append maturity change log
    if maturity_changes:
        try:
            from .log import append_log
            for change in maturity_changes:
                append_log(root_dir, "maturity", change)
        except ImportError:
            pass  # log module created in T2

    return "\n".join(lines)
