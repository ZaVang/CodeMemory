"""Transient memory DAG — session-level reasoning chain in memory.

TransientDAG maintains an in-memory graph of session nodes that can be
resolved via topological sort. Nodes are NOT written to disk; they
vanish when the process exits.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .core import estimate_tokens
from .resolve import topological_sort


class TransientNode(BaseModel):
    """A temporary in-memory memory node — never persisted to disk."""

    id: str
    type: str = Field(default="atom", description="atom | schema")
    summary: str = ""
    body: str = ""
    imports: dict[str, list[str]] = Field(default_factory=dict)
    intensity: int = 5


class TransientDAG:
    """Session-level DAG of transient nodes. Process-exit = auto-clear.

    Usage:
        dag = TransientDAG()
        dag.add("session/step1", type="atom", summary="...", body="...")
        dag.add("session/step2", type="atom", summary="...", body="...")
        dag.add("session/conclusion", type="atom", summary="...",
                body="...", imports={"required": ["session/step1", "session/step2"]})
        text = dag.resolve(root=Path("examples/investment"))
    """

    def __init__(self) -> None:
        self._nodes: dict[str, TransientNode] = {}

    def add(
        self,
        id: str,
        type: str = "atom",
        summary: str = "",
        body: str = "",
        imports: dict[str, list[str]] | None = None,
        intensity: int = 5,
    ) -> TransientNode:
        """Add a transient node. Overwrites if id already exists."""
        node = TransientNode(
            id=id,
            type=type,
            summary=summary,
            body=body,
            imports=imports or {},
            intensity=intensity,
        )
        self._nodes[id] = node
        return node

    def remove(self, id: str) -> bool:
        """Remove a transient node by id. Returns True if removed."""
        if id in self._nodes:
            del self._nodes[id]
            return True
        return False

    def _build_graph(self) -> dict[str, list[str]]:
        """Build a graph {node_id: [dep_ids]} from transient nodes."""
        graph: dict[str, list[str]] = {}
        for nid, node in self._nodes.items():
            deps: list[str] = []
            imports = node.imports or {}
            for strength in ("required", "recommended", "related"):
                for ref in imports.get(strength, []):
                    if isinstance(ref, str):
                        deps.append(ref)
                    elif isinstance(ref, dict) and "id" in ref:
                        deps.append(ref["id"])
            graph[nid] = deps
        return graph

    def resolve(self, root: Path | None = None, budget: int | None = None) -> str:
        """Resolve all transient nodes in topological order.

        Args:
            root: Memory root directory (unused for transient-only resolution,
                  but accepted for API compatibility with persistent resolve).
            budget: Token budget (chars). When constrained, recommended nodes
                    degrade to summary instead of being skipped.

        Returns:
            Assembled context text with nodes in dependency order.
        """
        graph = self._build_graph()
        if not graph:
            return "(empty transient DAG)"

        ordered = topological_sort(graph)

        # Ensure all nodes are included
        for nid in graph:
            if nid not in ordered:
                ordered.insert(0, nid)

        # Build classification sets for degradation
        req_set: set[str] = set()
        rec_set: set[str] = set()
        for nid, node in self._nodes.items():
            imports = node.imports or {}
            for ref in imports.get("required", []):
                ref_id = ref if isinstance(ref, str) else ref.get("id", "")
                if ref_id:
                    req_set.add(ref_id)
            for ref in imports.get("recommended", []):
                ref_id = ref if isinstance(ref, str) else ref.get("id", "")
                if ref_id:
                    rec_set.add(ref_id)

        max_budget = budget if budget else float("inf")
        used = 0

        lines: list[str] = []
        lines.append("# Transient Session Context\n")
        if budget:
            lines.append(f"*(Nodes: {len(ordered)}, Budget: {max_budget} chars)*\n")
        else:
            lines.append(f"*(Nodes: {len(ordered)})*\n")

        for i, nid in enumerate(ordered):
            node = self._nodes.get(nid)
            if node is None:
                continue

            full_text = (
                f"## [{i + 1}/{len(ordered)}] {nid} ({node.type})\n\n"
                f"{node.body}\n\n"
            )
            summary_text = (
                f"## [{i + 1}/{len(ordered)}] {nid} "
                f"({node.type} - SUMMARY - budget)\n\n"
                f"> {node.summary}\n\n"
            )
            skip_text = (
                f"## [{i + 1}/{len(ordered)}] {nid} "
                f"(SKIPPED - budget)\n\n"
            )

            t_full = estimate_tokens(full_text)
            t_sum = estimate_tokens(summary_text)

            is_required = nid in req_set
            is_recommended = nid in rec_set and not is_required

            if used + t_full <= max_budget:
                lines.append(full_text)
                used += t_full
            elif is_required:
                lines.append(summary_text)
                used += t_sum
            elif is_recommended:
                # Recommended nodes degrade to summary (not skipped)
                lines.append(summary_text)
                used += t_sum
            else:
                lines.append(skip_text)

        lines.append(f"---\nTotal nodes: {len(ordered)}, Budget used: {used}/{max_budget}")
        return "\n".join(lines)

    # ── Serialization ────────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Serialize the DAG to a JSON-compatible dict."""
        return {
            "nodes": [node.model_dump(mode="json") for node in self._nodes.values()],
            "created": datetime.now().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransientDAG:
        """Deserialize a DAG from a dict (e.g. loaded from JSON)."""
        dag = cls()
        for node_data in data.get("nodes", []):
            node = TransientNode(**node_data)
            dag._nodes[node.id] = node
        return dag
