"""Edge-case tests: empty library, cycle resilience, extreme budgets,
missing imports, missing schema.

These test that codememory handles boundary conditions gracefully
without crashing or producing incorrect results.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from codememory.models import IndexData, MemoryEntry
from codememory.resolve import resolve, build_dag, topological_sort, find_cycle_participants
from codememory.validate import validate, check_schema_compliance
from codememory.core import compute_body_hash


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _make_entry(mid: str, mem_type: str = "atom",
                required: list[str] | None = None,
                recommended: list[str] | None = None,
                related: list[str] | None = None,
                summary: str = "", body: str = "",
                intensity: int = 5, schema: str | None = None,
                path: str = "") -> MemoryEntry:
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
        path=path or f"{mid}.md",
        imports=imports,
        intensity=intensity,
        schema=schema,
    )
    if body:
        entry.summary_hash = compute_body_hash(body)
    object.__setattr__(entry, '_body', body)
    return entry


# ==================================================================
# 4.1 Empty memory library
# ==================================================================

def test_empty_index_validate():
    """validate on empty index completes without error."""
    idx = IndexData()
    with patch("codememory.validate.load_index", return_value=idx):
        errors, warnings = validate(Path("."))
    assert errors == 0
    assert warnings == 0


def test_empty_index_resolve_nonexistent():
    """resolve for missing ID returns an error message, does not crash."""
    idx = IndexData()

    with patch("codememory.build.load_index", return_value=idx):
        output = resolve(Path("."), "nonexistent/id")
    assert "not found" in output.lower() or "Error" in output


# ==================================================================
# 4.2 Cycle resilience — resolve does not crash
# ==================================================================

def test_resolve_handles_cycle_gracefully():
    """resolve with A→B→A cycle skips cycle nodes, still produces output."""
    idx = IndexData()
    body_a = "Body A. " * 10
    body_b = "Body B. " * 10
    idx.memories["A"] = _make_entry("A", required=["B"], body=body_a, path="A.md",
                                     summary="Summary A")
    idx.memories["B"] = _make_entry("B", required=["A"], body=body_b, path="B.md",
                                     summary="Summary B")

    def mock_pfm(filepath):
        if "A.md" in str(filepath):
            return ({"summary_hash": compute_body_hash(body_a)}, body_a)
        return ({"summary_hash": compute_body_hash(body_b)}, body_b)

    with patch("codememory.build.load_index", return_value=idx), \
         patch("codememory.build.parse_frontmatter", side_effect=mock_pfm), \
         patch("codememory.build.save_index"):
        output = resolve(Path("."), "A", depth="required", budget=99999)

    # Should produce some output without crashing
    assert "# CodeMemory Context Pack" in output
    assert "circular_dependency" in output  # cycle surfaces as a structured notice
    assert "Budget" in output or "budget" in output.lower()


# ==================================================================
# 4.3 Huge budget — all nodes full text
# ==================================================================

def test_huge_budget_all_full_text():
    """budget=99999 outputs all nodes as full text, no summary fallback."""
    idx = IndexData()
    bodies = {
        "Root": "Root " * 50,
        "Child": "Child " * 50,
        "Grandchild": "Grandchild " * 50,
    }
    idx.memories["Root"] = _make_entry("Root", required=["Child"],
                                        body=bodies["Root"], path="Root.md",
                                        summary="Root summary")
    idx.memories["Child"] = _make_entry("Child", required=["Grandchild"],
                                         body=bodies["Child"], path="Child.md",
                                         summary="Child summary")
    idx.memories["Grandchild"] = _make_entry("Grandchild",
                                              body=bodies["Grandchild"],
                                              path="Grandchild.md",
                                              summary="Grandchild summary")

    def mock_pfm(filepath):
        for mid, body in bodies.items():
            if mid in str(filepath):
                return ({"summary_hash": compute_body_hash(body)}, body)
        return ({}, "")

    with patch("codememory.build.load_index", return_value=idx), \
         patch("codememory.build.parse_frontmatter", side_effect=mock_pfm), \
         patch("codememory.build.save_index"):
        output = resolve(Path("."), "Root", depth="required", budget=99999)

    assert "Trim: `summary`" not in output
    assert "Root " in output
    assert "Child " in output
    assert "Grandchild " in output


# ==================================================================
# 4.4 Zero budget — all required nodes as summary
# ==================================================================

def test_zero_budget_all_summary():
    """budget=0 is honored as a real zero budget: everything floors at summary."""
    idx = IndexData()
    bodies = {
        "R": "Root " * 100,
        "C": "Child " * 100,
    }
    idx.memories["R"] = _make_entry("R", required=["C"],
                                     body=bodies["R"], path="R.md",
                                     summary="Root summary")
    idx.memories["C"] = _make_entry("C", body=bodies["C"], path="C.md",
                                     summary="Child summary")

    def mock_pfm(filepath):
        for mid, body in bodies.items():
            if mid in str(filepath):
                return ({"summary_hash": compute_body_hash(body)}, body)
        return ({}, "")

    with patch("codememory.build.load_index", return_value=idx), \
         patch("codememory.build.parse_frontmatter", side_effect=mock_pfm), \
         patch("codememory.build.save_index"):
        output = resolve(Path("."), "R", depth="required", budget=0)

    # Phase B: budget=0 is a real budget — required nodes floor at summary.
    assert "# CodeMemory Context Pack" in output
    assert "Trim: `summary`" in output
    assert "Trim: `full`" not in output


# ==================================================================
# 4.5 Missing imports — validate errors, resolve skips
# ==================================================================

def test_validate_reports_missing_import():
    """validate reports ERROR when a memory imports a non-existent ID."""
    idx = IndexData()
    idx.memories["A"] = _make_entry("A", required=["Ghost"], path="A.md")

    def mock_load_index(_root):
        return idx

    def mock_pfm(filepath):
        return ({"type": "atom", "id": "A", "imports": {"required": ["Ghost"]}}, "body")

    with patch("codememory.validate.load_index", mock_load_index), \
         patch("codememory.validate.parse_frontmatter", mock_pfm):
        errors, _w = validate(Path("."))
    assert errors >= 1


def test_resolve_skips_missing_imports():
    """resolve gracefully skips missing imported nodes, does not crash."""
    idx = IndexData()
    body_a = "Body for A. " * 10
    idx.memories["A"] = _make_entry("A", required=["Ghost"], body=body_a,
                                     path="A.md", summary="Summary A")

    def mock_pfm(filepath):
        return ({"summary_hash": compute_body_hash(body_a)}, body_a)

    with patch("codememory.build.load_index", return_value=idx), \
         patch("codememory.build.parse_frontmatter", side_effect=mock_pfm), \
         patch("codememory.build.save_index"):
        output = resolve(Path("."), "A", depth="required", budget=99999)

    # The missing import surfaces as a notice but resolve completes
    assert "# CodeMemory Context Pack" in output
    assert "missing_memory" in output


# ==================================================================
# 4.6 Missing schema — instance with non-existent schema
# ==================================================================

def test_validate_reports_missing_schema():
    """instance referencing a non-existent schema produces validate ERROR."""
    idx = IndexData()
    idx.memories["inst"] = _make_entry("inst", mem_type="instance",
                                        schema="schemas/nonexistent",
                                        path="inst.md")

    def mock_load_index(_root):
        return idx

    def mock_pfm(filepath):
        return ({"type": "instance", "id": "inst",
                 "schema": "schemas/nonexistent"}, "body")

    with patch("codememory.validate.load_index", mock_load_index), \
         patch("codememory.validate.parse_frontmatter", mock_pfm):
        errors, _w = validate(Path("."))
    assert errors >= 1


def test_build_dag_handles_nonexistent_dep_in_graph():
    """build_dag with a reference to non-indexed memory still works."""
    idx = IndexData()
    idx.memories["A"] = _make_entry("A", required=["B"])
    # B is not in index

    graph = build_dag("A", "required", idx)
    assert "A" in graph
    assert "B" in graph
    assert graph["B"] == []  # Warning logged, but graph built
