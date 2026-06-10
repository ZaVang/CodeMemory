"""Unified build pipeline: DAG resolution, ContextPack assembly, renderers.

The single implementation behind `build`, `resolve`, and `context-pack`
(architecture.md section 4.1). ContextPack is the pipeline's product model;
render targets are output formats only.
"""


from __future__ import annotations

import html
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from .core import (
    compute_body_hash,
    estimate_tokens,
    parse_frontmatter,
)
from .index import load_index, save_index
from .models import NON_ASSEMBLABLE_STATUSES, IndexData, MemoryEntry, SourceRef

ContextPackFormat = Literal["xml-markdown", "markdown", "plain-markdown", "json"]
TrimMode = Literal["full", "summary", "skipped"]
DependencyRole = Literal["target", "required", "recommended", "related", "unknown"]

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


class ContextPackNotice(BaseModel):
    """A data-quality or assembly notice emitted during context-pack creation."""

    type: str = "notice"
    message: str
    memory_id: str | None = None


class ContextPackNode(BaseModel):
    """A single memory node included in a ContextPack."""

    id: str
    index: int
    total: int
    type: str
    summary: str
    trim: TrimMode
    dependency_role: DependencyRole = "unknown"
    maturity: str = "draft"
    status: str = "active"
    tags: list[str] = Field(default_factory=list)
    source_refs: list[SourceRef] = Field(default_factory=list)
    content: str | None = None
    source_path: str | None = None
    token_estimate: int = 0


class ContextPack(BaseModel):
    """Structured context bundle for agent handoff."""

    format_version: str = "context-pack/v1"
    target_id: str
    task_goal: str | None = None
    depth: str = "recommended"
    budget: int | None = None
    used_budget: int = 0
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    nodes: list[ContextPackNode] = Field(default_factory=list)
    notices: list[ContextPackNotice] = Field(default_factory=list)
    render_policy: dict[str, object] = Field(default_factory=dict)


def build_context_pack(
    root_dir: Path,
    memory_id: str,
    *,
    depth: str = "recommended",
    budget: int | None = None,
    focus: str | None = None,
    task_goal: str | None = None,
    track_access: bool = True,
) -> ContextPack:
    """Build a structured ContextPack from a memory DAG.

    This mirrors the existing resolve semantics while returning a typed object
    instead of requiring downstream systems to parse plain text.
    """

    index = load_index(root_dir)
    if memory_id not in index.memories:
        raise ValueError(f"Target memory '{memory_id}' not found. Did you reindex?")

    target_status = index.memories[memory_id].status
    if target_status in NON_ASSEMBLABLE_STATUSES:
        raise ValueError(
            f"Target memory '{memory_id}' has status '{target_status}' and is not assemblable; "
            f"if it is a proposal, review it and run: codememory merge {memory_id}"
        )

    graph = build_dag(memory_id, depth, index)
    notices: list[ContextPackNotice] = []

    cycle_ids = find_cycle_participants(graph)
    if cycle_ids:
        notices.append(ContextPackNotice(
            type="circular_dependency",
            message=f"Circular dependency detected; cycle nodes were de-prioritized: {', '.join(sorted(cycle_ids))}",
        ))
        for node_id in list(graph.keys()):
            graph[node_id] = [dep for dep in graph[node_id] if dep not in cycle_ids]

    excluded_ids = sorted(
        nid for nid in graph
        if nid != memory_id and nid in index.memories
        and index.memories[nid].status in NON_ASSEMBLABLE_STATUSES
    )
    if excluded_ids:
        notices.append(ContextPackNotice(
            type="excluded_status",
            message=(
                "Skipped non-assemblable nodes "
                f"(proposed/archived/superseded): {', '.join(excluded_ids)}"
            ),
        ))
        for node_id in list(graph.keys()):
            graph[node_id] = [dep for dep in graph[node_id] if dep not in excluded_ids]
        for node_id in excluded_ids:
            graph.pop(node_id, None)

    ordered = topological_sort(graph)
    for node_id in graph:
        if node_id not in ordered and node_id not in cycle_ids:
            ordered.insert(0, node_id)
    for node_id in cycle_ids:
        if node_id not in ordered:
            ordered.append(node_id)

    required_graph = build_dag(memory_id, "required", index)
    recommended_graph = build_dag(memory_id, "recommended", index)
    full_graph = build_dag(memory_id, "full", index)
    max_budget: int | float = budget if budget is not None else float("inf")
    used_budget = 0
    full_text_nodes: list[str] = []
    stale_ids: list[str] = []
    nodes: list[ContextPackNode] = []

    for node_id in ordered:
        if node_id not in index.memories:
            notices.append(ContextPackNotice(
                type="missing_memory",
                memory_id=node_id,
                message=f"Referenced memory '{node_id}' was not found in the index.",
            ))

    positions = [node_id for node_id in ordered if node_id in index.memories]
    total = len(positions)

    # Pass 0: read bodies, compute render costs and roles at final positions.
    node_info: dict[str, dict] = {}
    for pos, node_id in enumerate(positions, start=1):
        entry = index.memories[node_id]
        file_path = root_dir / entry.path
        meta, body = parse_frontmatter(file_path)
        _collect_metadata_notices(index, entry, node_id, body, meta, notices, stale_ids)
        node_info[node_id] = {
            "entry": entry,
            "body": body,
            "pos": pos,
            "role": _dependency_role(memory_id, node_id, required_graph, recommended_graph, full_graph),
            "full_cost": estimate_tokens(_node_render_text(node_id, entry, body, pos, total, trim="full")),
            "summary_cost": estimate_tokens(_node_render_text(node_id, entry, entry.summary, pos, total, trim="summary")),
        }

    # Pass 1: budget allocation (architecture §4.1 step 4). Roles claim budget
    # in priority order; within a level, more dependents (then access_count)
    # keep full text. target/required/recommended floor at summary; related
    # and unknown nodes may be skipped entirely.
    trim_for: dict[str, TrimMode] = {}
    remaining = max_budget
    if focus:
        # Legacy focus semantics: matching tags get full text while budget
        # lasts (in reading order); everything else stays summary.
        for node_id in positions:
            info = node_info[node_id]
            if focus in info["entry"].tags and info["full_cost"] <= remaining:
                trim_for[node_id] = "full"
                remaining -= info["full_cost"]
            else:
                trim_for[node_id] = "summary"
                remaining -= info["summary_cost"]
    else:
        role_rank = {"target": 0, "required": 1, "recommended": 2, "related": 3, "unknown": 4}
        by_value = sorted(
            positions,
            key=lambda nid: (
                role_rank.get(node_info[nid]["role"], 4),
                -_count_dependents(nid, index),
                -node_info[nid]["entry"].access_count,
                node_info[nid]["pos"],
            ),
        )
        for node_id in by_value:
            info = node_info[node_id]
            if info["full_cost"] <= remaining:
                trim_for[node_id] = "full"
                remaining -= info["full_cost"]
            elif info["role"] in ("target", "required", "recommended"):
                trim_for[node_id] = "summary"
                remaining -= info["summary_cost"]
            else:
                trim_for[node_id] = "skipped"

    # Pass 2: render in topological (reading) order with the allocated trims —
    # reading order and budget allocation are decoupled by design.
    for node_id in positions:
        info = node_info[node_id]
        entry = info["entry"]
        trim = trim_for[node_id]
        if trim == "full":
            content = info["body"]
            cost = info["full_cost"]
            full_text_nodes.append(node_id)
        elif trim == "summary":
            content = None
            cost = info["summary_cost"]
        else:
            content = None
            cost = 0

        used_budget += cost
        nodes.append(ContextPackNode(
            id=node_id,
            index=info["pos"],
            total=total,
            type=entry.type,
            summary=entry.summary,
            trim=trim,
            dependency_role=info["role"],
            maturity=entry.maturity,
            status=entry.status,
            tags=entry.tags,
            source_refs=entry.source_refs,
            content=content,
            source_path=entry.path,
            token_estimate=cost,
        ))

    if budget is not None and used_budget > budget:
        notices.append(ContextPackNotice(
            type="budget_exceeded",
            message=(
                f"Context pack used {used_budget} characters, exceeding requested budget {budget}; "
                "required/target summaries are retained to preserve graph coherence."
            ),
        ))

    if track_access:
        _track_context_pack_access(root_dir, index, full_text_nodes)

    return ContextPack(
        target_id=memory_id,
        task_goal=task_goal,
        depth=depth,
        budget=budget,
        used_budget=used_budget,
        nodes=nodes,
        notices=notices,
        render_policy={
            "default_format": "xml-markdown",
            "budget_unit": "characters",
            "track_access": track_access,
        },
    )


def render_context_pack(pack: ContextPack, output_format: ContextPackFormat = "xml-markdown") -> str:
    """Render a ContextPack for humans, agents, or machine transport."""

    if output_format == "json":
        return json.dumps(pack.model_dump(mode="json"), ensure_ascii=False, indent=2)
    if output_format in ("markdown", "plain-markdown"):
        return _render_markdown(pack)
    if output_format == "xml-markdown":
        return _render_xml_markdown(pack)
    raise ValueError(f"Unsupported context pack format: {output_format}")


def _dependency_role(
    target_id: str,
    node_id: str,
    required_graph: dict[str, list[str]],
    recommended_graph: dict[str, list[str]],
    full_graph: dict[str, list[str]],
) -> DependencyRole:
    if node_id == target_id:
        return "target"
    if node_id in required_graph:
        return "required"
    if node_id in recommended_graph:
        return "recommended"
    if node_id in full_graph:
        return "related"
    return "unknown"


def _node_render_text(node_id: str, entry: MemoryEntry, text: str, index: int, total: int, *, trim: TrimMode) -> str:
    if trim == "full":
        return f"## [{index}/{total}] {node_id} ({entry.type})\n\n{text}\n\n"
    if trim == "summary":
        return f"## [{index}/{total}] {node_id} ({entry.type} - SUMMARY)\n\n> {text}\n\n"
    return f"## [{index}/{total}] {node_id} (SKIPPED - budget)\n\n"


def _collect_metadata_notices(
    index: IndexData,
    entry: MemoryEntry,
    node_id: str,
    body: str,
    meta: dict,
    notices: list[ContextPackNotice],
    stale_ids: list[str],
) -> None:
    stored_hash = meta.get("summary_hash", "")
    if stored_hash:
        actual_hash = compute_body_hash(body)
        if str(stored_hash) != actual_hash:
            notices.append(ContextPackNotice(
                type="stale_summary",
                memory_id=node_id,
                message=f"Summary may be stale for {node_id} (hash mismatch).",
            ))
            if node_id not in stale_ids:
                stale_ids.append(node_id)

    imports_dict = entry.imports
    if not isinstance(imports_dict, dict):
        return

    for strength in ("required", "recommended", "related"):
        for ref in imports_dict.get(strength, []):
            if not isinstance(ref, dict) or "pin" not in ref:
                continue
            ref_id = ref.get("id", "")
            pin_version_str = ref.get("pin", "")
            if not ref_id or not pin_version_str or ref_id not in index.memories:
                continue
            current_version = index.memories[ref_id].version
            try:
                pin_num = int(str(pin_version_str).lstrip("v"))
            except ValueError:
                continue
            if current_version > pin_num:
                notices.append(ContextPackNotice(
                    type="pin_outdated",
                    memory_id=node_id,
                    message=f"Pinned version {pin_version_str} of {ref_id} is behind current version v{current_version}.",
                ))


def _track_context_pack_access(
    root_dir: Path,
    index: IndexData,
    full_text_nodes: list[str],
) -> None:
    """Record access telemetry for assembled nodes.

    architecture.md §5.1: assembly writes only access_count / last_access;
    maturity stays inert metadata and is never fed by build.
    """
    now_iso = datetime.now().isoformat()
    for node_id in full_text_nodes:
        if node_id not in index.memories:
            continue
        entry = index.memories[node_id]
        entry.access_count += 1
        entry.last_access = now_iso

    save_index(root_dir, index)


def _render_markdown(pack: ContextPack) -> str:
    lines: list[str] = [
        f"# CodeMemory Context Pack: {pack.target_id}",
        "",
        f"- Format Version: `{pack.format_version}`",
        f"- Depth: `{pack.depth}`",
        f"- Budget: `{pack.budget if pack.budget is not None else 'unlimited'}`",
        f"- Used Budget: `{pack.used_budget}`",
        f"- Generated At: `{pack.generated_at}`",
    ]
    if pack.task_goal:
        lines.extend(["", "## Task Goal", "", pack.task_goal])
    lines.extend(["", "## Memories"])
    for node in pack.nodes:
        lines.extend([
            "",
            f"### [{node.index}/{node.total}] {node.id}",
            "",
            f"- Trim: `{node.trim}`",
            f"- Role: `{node.dependency_role}`",
            f"- Maturity: `{node.maturity}`",
            f"- Status: `{node.status}`",
            f"- Tags: `{', '.join(node.tags)}`",
        ])
        if node.source_refs:
            lines.append(f"- Source refs: {', '.join(f'`{ref.artifact_id}`' for ref in node.source_refs)}")
        lines.extend(["", f"> {node.summary}"])
        if node.content:
            lines.extend(["", node.content])
    if pack.notices:
        lines.extend(["", "## Notices"])
        for notice in pack.notices:
            prefix = f"{notice.type}"
            if notice.memory_id:
                prefix += f": {notice.memory_id}"
            lines.append(f"- **{prefix}** — {notice.message}")
    return "\n".join(lines).rstrip() + "\n"


def _render_xml_markdown(pack: ContextPack) -> str:
    attrs = {
        "format_version": pack.format_version,
        "target_id": pack.target_id,
        "depth": pack.depth,
        "budget": str(pack.budget if pack.budget is not None else "unlimited"),
        "used_budget": str(pack.used_budget),
        "generated_at": pack.generated_at,
    }
    attr_text = " ".join(f'{key}="{_attr(value)}"' for key, value in attrs.items())
    lines = [f"<codememory_context_pack {attr_text}>"]
    if pack.task_goal:
        lines.append(f"  <task_goal>{_text(pack.task_goal)}</task_goal>")
    lines.append("  <purpose>Use this context as durable project memory. Prefer it over assumptions.</purpose>")
    lines.append("  <memories>")
    for node in pack.nodes:
        node_attrs = {
            "id": node.id,
            "trim": node.trim,
            "role": node.dependency_role,
            "type": node.type,
            "maturity": node.maturity,
            "status": node.status,
            "source_path": node.source_path or "",
        }
        node_attr_text = " ".join(f'{key}="{_attr(value)}"' for key, value in node_attrs.items())
        lines.append(f"    <memory {node_attr_text}>")
        lines.append(f"      <summary>{_text(node.summary)}</summary>")
        if node.tags:
            lines.append("      <tags>")
            for tag in node.tags:
                lines.append(f"        <tag>{_text(tag)}</tag>")
            lines.append("      </tags>")
        if node.source_refs:
            lines.append("      <source_refs>")
            for ref in node.source_refs:
                ref_attrs = {
                    "artifact_id": ref.artifact_id,
                    "disclosure_hint": ref.disclosure_hint,
                }
                if ref.section_id:
                    ref_attrs["section_id"] = ref.section_id
                if ref.range:
                    ref_attrs["range"] = ref.range
                ref_attr_text = " ".join(f'{key}="{_attr(value)}"' for key, value in ref_attrs.items())
                lines.append(f"        <source_ref {ref_attr_text}>")
                if ref.summary:
                    lines.append(f"          <summary>{_text(ref.summary)}</summary>")
                lines.append("        </source_ref>")
            lines.append("      </source_refs>")
        if node.content is not None:
            lines.append("      <content format=\"markdown\">")
            lines.append(_cdata(node.content))
            lines.append("      </content>")
        else:
            lines.append("      <content omitted=\"true\" />")
        lines.append("    </memory>")
    lines.append("  </memories>")
    if pack.notices:
        lines.append("  <notices>")
        for notice in pack.notices:
            attrs = f'type="{_attr(notice.type)}"'
            if notice.memory_id:
                attrs += f' memory_id="{_attr(notice.memory_id)}"'
            lines.append(f"    <notice {attrs}>{_text(notice.message)}</notice>")
        lines.append("  </notices>")
    lines.append("</codememory_context_pack>")
    return "\n".join(lines) + "\n"


def _attr(value: object) -> str:
    return html.escape(str(value), quote=True)


def _text(value: object) -> str:
    return html.escape(str(value), quote=False)


def _cdata(value: str) -> str:
    safe = value.replace("]]>", "]]]]><![CDATA[>")
    return f"<![CDATA[\n{safe}\n]]>"
