"""Unit tests for resolve.py: DAG construction, topological sort, cycle
detection, token trimming, depth filtering, and stale detection.

All tests use pure functions or mocked filesystem — no real .md files needed.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure src/ is on the path
_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from codememory.models import IndexData, MemoryEntry
from codememory.resolve import (
    _get_imports,
    build_dag,
    find_cycle_participants,
    topological_sort,
    resolve,
)
from codememory.core import compute_body_hash


# ------------------------------------------------------------------
# Helper: build a MemoryEntry with imports
# ------------------------------------------------------------------

def _make_entry(mid: str, mem_type: str = "atom",
                required: list[str] | None = None,
                recommended: list[str] | None = None,
                related: list[str] | None = None,
                summary: str = "", body: str = "",
                intensity: int = 5, access_count: int = 0,
                last_access: str | None = None,
                version: int = 1,
                path: str = "") -> MemoryEntry:
    """Build a MemoryEntry with structured imports."""
    imports: dict = {}
    if required:
        imports["required"] = required
    if recommended:
        imports["recommended"] = recommended
    if related:
        imports["related"] = related

    entry = MemoryEntry(
        type=mem_type,
        id=mid,
        summary=summary or f"Summary of {mid}",
        path=path or f"{mid.replace('/', '/')}.md",
        imports=imports,
        intensity=intensity,
        access_count=access_count,
        last_access=last_access,
        version=version,
    )
    if body:
        entry.summary_hash = compute_body_hash(body)

    # Store a _body attr for mock convenience (not part of MemoryEntry schema)
    object.__setattr__(entry, '_body', body)
    return entry


# ------------------------------------------------------------------
# Fixture: 5-node DAG
#
#      A
#     / \
#    B   C
#     \ / \
#      D   E
#
# A imports required [B, C]
# B imports required [D]
# C imports required [D, E]
# D, E are leaf nodes
# ------------------------------------------------------------------

def _five_node_index() -> IndexData:
    entries = [
        _make_entry("A", required=["B", "C"], summary="Root"),
        _make_entry("B", required=["D"], summary="Node B"),
        _make_entry("C", required=["D", "E"], summary="Node C"),
        _make_entry("D", summary="Node D"),
        _make_entry("E", summary="Node E"),
    ]
    idx = IndexData()
    for e in entries:
        idx.memories[e.id] = e
    return idx


# ==================================================================
# 1.1 DAG construction
# ==================================================================

def test_build_dag_five_nodes():
    """DAG adjacency list for 5 nodes with required depth."""
    idx = _five_node_index()
    graph = build_dag("A", "required", idx)

    assert set(graph.keys()) == {"A", "B", "C", "D", "E"}
    assert set(graph["A"]) == {"B", "C"}
    assert set(graph["B"]) == {"D"}
    assert set(graph["C"]) == {"D", "E"}
    assert graph["D"] == []
    assert graph["E"] == []


def test_build_dag_missing_target():
    """build_dag for a missing memory returns empty graph entry."""
    idx = _five_node_index()
    graph = build_dag("Z", "required", idx)
    assert "Z" in graph
    assert graph["Z"] == []


def test_build_dag_deep_required():
    """required depth only follows required imports."""
    idx = IndexData()
    idx.memories["X"] = _make_entry("X", required=["Y"], recommended=["R"], related=["L"])
    idx.memories["Y"] = _make_entry("Y", recommended=["R"])
    idx.memories["R"] = _make_entry("R")
    idx.memories["L"] = _make_entry("L")

    graph = build_dag("X", "required", idx)
    # Only Y should be traversed; R and L should NOT appear
    assert "Y" in graph
    assert "R" not in graph
    assert "L" not in graph


# ==================================================================
# 1.2 Topological sort
# ==================================================================

def test_topo_single_node():
    """Single node sorts to itself."""
    graph = {"X": []}
    order = topological_sort(graph)
    assert order == ["X"]


def test_topo_chain():
    """Chain A→B→C: C first, then B, then A."""
    graph = {"A": ["B"], "B": ["C"], "C": []}
    order = topological_sort(graph)
    assert order.index("C") < order.index("B") < order.index("A")


def test_topo_diamond():
    """Diamond: A→B, A→C, B→D, C→D: D first, A last."""
    graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
    order = topological_sort(graph)
    assert order.index("D") < order.index("B")
    assert order.index("D") < order.index("C")
    assert order.index("B") < order.index("A")
    assert order.index("C") < order.index("A")


def test_topo_five_node_ordering():
    """Dependencies come before dependents in 5-node DAG."""
    idx = _five_node_index()
    graph = build_dag("A", "required", idx)
    order = topological_sort(graph)

    # D and E are leaf dependencies — must come before B, C, A
    assert order.index("D") < order.index("B")
    assert order.index("D") < order.index("C")
    assert order.index("E") < order.index("C")
    # A depends on everything — must be last
    assert order.index("A") > order.index("B")
    assert order.index("A") > order.index("C")


# ==================================================================
# 1.3 Cycle detection
# ==================================================================

def test_no_cycle():
    """No cycle in a DAG returns empty list."""
    graph = {"A": ["B"], "B": ["C"], "C": []}
    cycles = find_cycle_participants(graph)
    assert cycles == []


def test_cycle_a_b_c_a():
    """A→B→C→A cycle returns all three nodes."""
    graph = {"A": ["B"], "B": ["C"], "C": ["A"]}
    cycles = find_cycle_participants(graph)
    assert set(cycles) == {"A", "B", "C"}


def test_cycle_self_loop():
    """Self-loop is detected as a cycle."""
    graph = {"A": ["A"]}
    cycles = find_cycle_participants(graph)
    assert "A" in cycles


def test_cycle_with_extra_nodes():
    """Cycle A↔B with external leaf C."""
    graph = {"A": ["B", "C"], "B": ["A"], "C": []}
    cycles = find_cycle_participants(graph)
    assert set(cycles) == {"A", "B"}
    assert "C" not in cycles


# ==================================================================
# 1.4 Token trimming
# ==================================================================

def _build_mock_frontmatter(body_text: str):
    """Return a mock for parse_frontmatter based on body text."""
    def mock_pfm(filepath):
        return (
            {"summary_hash": compute_body_hash(body_text)},
            body_text,
        )
    return mock_pfm


def _make_resolve_index():
    """Build a simple DAG: Root→P1→Leaf, Root→P2 (2 children, 2 grandchildren)."""
    root_body = "Root body content. " * 20   # ~400 chars
    p1_body = "P1 body. " * 30               # ~300 chars
    p2_body = "P2 body. " * 30               # ~300 chars
    leaf_body = "Leaf body. " * 20           # ~300 chars

    idx = IndexData()
    idx.memories["Root"] = _make_entry(
        "Root", required=["P1", "P2"], body=root_body,
        path="Root.md", summary="Root summary",
    )
    idx.memories["P1"] = _make_entry(
        "P1", required=["Leaf"], body=p1_body,
        path="P1.md", summary="P1 summary",
    )
    idx.memories["P2"] = _make_entry(
        "P2", body=p2_body, path="P2.md", summary="P2 summary",
    )
    idx.memories["Leaf"] = _make_entry(
        "Leaf", body=leaf_body, path="Leaf.md", summary="Leaf summary",
    )
    return idx


def test_token_budget_all_fit():
    """Large budget: all nodes get full text."""
    idx = _make_resolve_index()

    def side_effect(filepath):
        path_str = str(filepath)
        for mid, entry in idx.memories.items():
            if entry.path in path_str:
                return (
                    {"summary_hash": compute_body_hash(entry._body)},
                    entry._body,
                )
        return ({}, "")

    with patch("codememory.build.load_index", return_value=idx), \
         patch("codememory.build.parse_frontmatter", side_effect=side_effect), \
         patch("codememory.build.save_index"):
        output = resolve(Path("."), "Root", depth="required", budget=99999)

    # All 4 nodes should appear with full text (no SUMMARY marker)
    assert "Root body content" in output
    assert "P1 body" in output
    assert "P2 body" in output
    assert "Leaf body" in output
    assert "Trim: `summary`" not in output


def test_token_budget_cramped():
    """Tight budget: required root nodes downgrade to summary."""
    idx = _make_resolve_index()

    def side_effect(filepath):
        path_str = str(filepath)
        for mid, entry in idx.memories.items():
            if entry.path in path_str:
                return (
                    {"summary_hash": compute_body_hash(entry._body)},
                    entry._body,
                )
        return ({}, "")

    with patch("codememory.build.load_index", return_value=idx), \
         patch("codememory.build.parse_frontmatter", side_effect=side_effect), \
         patch("codememory.build.save_index"):
        output = resolve(Path("."), "Root", depth="required", budget=50)

    # At budget 50, no body fits (tokens = chars), so every node —
    # including the target — floors at summary.
    assert "Trim: `summary`" in output
    assert "Trim: `full`" not in output


# ==================================================================
# 1.5 Depth filtering
# ==================================================================

def test_depth_required_excludes_recommended():
    """required depth does not follow recommended/releated imports."""
    idx = IndexData()
    idx.memories["Main"] = _make_entry("Main", required=["Req"],
                                        recommended=["Rec"], related=["Rel"])
    idx.memories["Req"] = _make_entry("Req")
    idx.memories["Rec"] = _make_entry("Rec")
    idx.memories["Rel"] = _make_entry("Rel")

    graph = build_dag("Main", "required", idx)
    assert "Rec" not in graph
    assert "Rel" not in graph
    assert "Req" in graph


def test_depth_recommended_includes_recommended():
    """recommended depth follows required + recommended imports."""
    idx = IndexData()
    idx.memories["Main"] = _make_entry("Main", required=["Req"],
                                        recommended=["Rec"], related=["Rel"])
    idx.memories["Req"] = _make_entry("Req")
    idx.memories["Rec"] = _make_entry("Rec")
    idx.memories["Rel"] = _make_entry("Rel")

    graph = build_dag("Main", "recommended", idx)
    assert "Req" in graph
    assert "Rec" in graph
    assert "Rel" not in graph


def test_depth_full_includes_all():
    """full depth follows all import strengths."""
    idx = IndexData()
    idx.memories["Main"] = _make_entry("Main", required=["Req"],
                                        recommended=["Rec"], related=["Rel"])
    idx.memories["Req"] = _make_entry("Req")
    idx.memories["Rec"] = _make_entry("Rec")
    idx.memories["Rel"] = _make_entry("Rel")

    graph = build_dag("Main", "full", idx)
    assert "Req" in graph
    assert "Rec" in graph
    assert "Rel" in graph


# ==================================================================
# 1.6 Stale detection
# ==================================================================

def test_stale_check_true(tmp_path: Path):
    """_stale_check returns True when summary_hash does not match body."""
    from codememory.handlers import _stale_check

    # Create an actual file so file_path.exists() passes
    test_file = tmp_path / "test.md"
    actual_body = "This is the real body content."
    stored_hash = "abcdefg"  # Does not match actual body

    # Write frontmatter with the fake hash + actual body
    content = f"---\nsummary_hash: {stored_hash}\n---\n{actual_body}"
    test_file.write_text(content, encoding="utf-8")

    entry_dict = {"path": str(test_file.relative_to(tmp_path))}
    result = _stale_check(tmp_path, entry_dict)
    assert result is True


def test_stale_check_false_match(tmp_path: Path):
    """_stale_check returns False when summary_hash matches body."""
    from codememory.handlers import _stale_check

    body = "Body text that is up to date."
    matching_hash = compute_body_hash(body)

    test_file = tmp_path / "test.md"
    content = f"---\nsummary_hash: {matching_hash}\n---\n{body}"
    test_file.write_text(content, encoding="utf-8")

    entry_dict = {"path": str(test_file.relative_to(tmp_path))}
    result = _stale_check(tmp_path, entry_dict)
    assert result is False


def test_stale_check_no_hash(tmp_path: Path):
    """_stale_check returns False when no summary_hash in frontmatter."""
    from codememory.handlers import _stale_check

    test_file = tmp_path / "test.md"
    content = "---\n---\nsome body"
    test_file.write_text(content, encoding="utf-8")

    entry_dict = {"path": str(test_file.relative_to(tmp_path))}
    result = _stale_check(tmp_path, entry_dict)
    assert result is False


# ==================================================================
# 1.7 _get_imports edge cases
# ==================================================================

def test_get_imports_dict_entries():
    """_get_imports handles dict-style import refs with 'id' key."""
    entry = _make_entry("X", required=[], recommended=[], related=[])
    entry.imports = {
        "required": [{"id": "A", "pin": "v1"}],
        "recommended": ["B"],
    }
    deps = _get_imports(entry, "recommended")
    assert "A" in deps
    assert "B" in deps


def test_get_imports_empty_imports():
    """_get_imports returns empty list for empty imports."""
    entry = _make_entry("X")
    deps = _get_imports(entry, "full")
    assert deps == []


def test_get_imports_non_dict_imports():
    """_get_imports handles non-dict imports gracefully."""
    entry = _make_entry("X")
    object.__setattr__(entry, 'imports', "not a dict")
    deps = _get_imports(entry, "full")
    assert deps == []
