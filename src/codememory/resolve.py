"""Memory resolution: DAG construction, cycle detection, topological sort, token budget."""

import logging
import sys
from datetime import datetime
from pathlib import Path

from .core import compute_body_hash, estimate_tokens, parse_frontmatter
from .index import load_index, save_index
from .models import IndexData, MemoryEntry

_logger = logging.getLogger("codememory")


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
) -> str:
    """Resolve and assemble memory context for a given memory ID."""
    index = load_index(root_dir)

    if memory_id not in index.memories:
        msg = f"Error: Target memory '{memory_id}' not found. Did you reindex?"
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

        full_text = (
            f"## [{i + 1}/{len(ordered)}] {mid} ({entry.type})\n\n{body}\n\n"
        )
        summary_text = (
            f"## [{i + 1}/{len(ordered)}] {mid} ({entry.type} - SUMMARY - budget)\n\n"
            f"> {entry.summary}\n\n"
        )

        t_full = estimate_tokens(full_text)
        t_sum = estimate_tokens(summary_text)

        is_required = mid in req_graph
        is_recommended = mid in rec_graph and not is_required

        if used + t_full <= max_budget:
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

    # Track access: increment access_count for full-text nodes
    now_iso = datetime.now().isoformat()
    for mid in full_text_nodes:
        if mid in index.memories:
            entry = index.memories[mid]
            entry.access_count += 1
            entry.last_access = now_iso

    save_index(root_dir, index)

    return "\n".join(lines)
