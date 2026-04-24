"""Memory resolution: DAG construction, cycle detection, topological sort, token budget."""

import sys
from pathlib import Path

from .core import parse_frontmatter, estimate_tokens
from .index import load_index


def _get_imports(meta: dict, depth: str) -> list[str]:
    """Extract dependency IDs from a memory's imports dict based on depth.

    Args:
        meta: The frontmatter metadata dict.
        depth: One of "required", "recommended", "full".
    """
    imports_dict = meta.get("imports", {})
    if not isinstance(imports_dict, dict):
        return []

    deps = []
    reqs = imports_dict.get("required", [])
    for r in reqs:
        if isinstance(r, str):
            deps.append(r)
        elif isinstance(r, dict) and "id" in r:
            deps.append(r["id"])

    if depth in ("recommended", "full"):
        recs = imports_dict.get("recommended", [])
        for r in recs:
            if isinstance(r, str):
                deps.append(r)
            elif isinstance(r, dict) and "id" in r:
                deps.append(r["id"])

    if depth == "full":
        rels = imports_dict.get("related", [])
        for r in rels:
            if isinstance(r, str):
                deps.append(r)
            elif isinstance(r, dict) and "id" in r:
                deps.append(r["id"])

    return deps


def build_dag(memory_id: str, depth: str, index: dict) -> dict:
    """Build a dependency graph from the target memory.

    Returns {node_id: [dependency_ids]}.
    """
    graph = {}
    queue = [memory_id]

    while queue:
        curr = queue.pop(0)
        if curr in graph:
            continue

        if curr not in index["memories"]:
            print(f"Warning: Memory '{curr}' not found in index.", file=sys.stderr)
            graph[curr] = []
            continue

        entry = index["memories"][curr]
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
                # Cycle detected
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
    topo_order = []

    while queue:
        u = queue.pop(0)
        topo_order.append(u)
        for v in graph.get(u, []):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    # Reverse so dependencies load before dependents
    return list(reversed(topo_order))


def resolve(
    root_dir: Path,
    memory_id: str,
    depth: str = "required",
    budget: int | None = None,
) -> str:
    """Resolve and assemble memory context for a given memory ID.

    Returns the assembled context as a string (also prints it).
    """
    index = load_index(root_dir)

    if memory_id not in index["memories"]:
        msg = f"Error: Target memory '{memory_id}' not found. Did you reindex?"
        print(msg, file=sys.stderr)
        return msg

    # 1. Build DAG
    graph = build_dag(memory_id, depth, index)

    # 2. Cycle Detection
    cycle_ids = find_cycle_participants(graph)
    if cycle_ids:
        print(
            f"WARNING: Circular dependency detected involving: {cycle_ids}",
            file=sys.stderr,
        )
        print("Skipping cycle nodes to continue resolution...", file=sys.stderr)
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

    lines = []
    lines.append(f"# Resolved Context for '{memory_id}'\n")
    lines.append(f"*(Depth: {depth}, Budget: {max_budget} chars)*\n")

    req_graph = build_dag(memory_id, "required", index)

    for i, mid in enumerate(ordered):
        if mid not in index["memories"]:
            continue

        entry = index["memories"][mid]
        file_path = root_dir / entry["path"]
        meta, body = parse_frontmatter(file_path)

        full_text = (
            f"## [{i + 1}/{len(ordered)}] {mid} ({entry['type']})\n\n{body}\n\n"
        )
        summary_text = (
            f"## [{i + 1}/{len(ordered)}] {mid} ({entry['type']} - SUMMARY ONLY)\n\n"
            f"> {entry['summary']}\n\n"
        )

        t_full = estimate_tokens(full_text)
        t_sum = estimate_tokens(summary_text)

        if used + t_full <= max_budget:
            lines.append(full_text)
            used += t_full
        elif mid in req_graph:
            lines.append(summary_text)
            used += t_sum
        else:
            lines.append(
                f"## [{i + 1}/{len(ordered)}] {mid} (SKIPPED - Out of budget)\n\n"
            )

    lines.append(f"---\nTotal Budget Used: {used}/{max_budget}")

    result = "\n".join(lines)
    return result
