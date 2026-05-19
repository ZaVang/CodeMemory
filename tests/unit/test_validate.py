"""Unit tests for validate.py: broken links, schema compliance, cycle
detection, and all four decay rules.

Tests use pure functions where possible and mock filesystem for validate().
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from codememory.models import IndexData, MemoryEntry
from codememory.sources import add_source_artifact
from codememory.validate import (
    check_schema_compliance,
    _check_decay,
    _compute_in_degree,
    validate,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _make_entry(mid: str, mem_type: str = "atom",
                required: list[str] | None = None,
                recommended: list[str] | None = None,
                related: list[str] | None = None,
                summary: str = "", intensity: int = 5,
                access_count: int = 0, last_access: str | None = None,
                schema: str | None = None,
                path: str = "") -> MemoryEntry:
    imports: dict = {}
    if required:
        imports["required"] = required
    if recommended:
        imports["recommended"] = recommended
    if related:
        imports["related"] = related

    return MemoryEntry(
        type=mem_type,
        id=mid,
        summary=summary or f"Summary of {mid}",
        path=path or f"{mid}.md",
        imports=imports,
        intensity=intensity,
        access_count=access_count,
        last_access=last_access,
        schema=schema,
    )


# ==================================================================
# 2.1 Broken link detection
# ==================================================================

def test_broken_link_detected():
    """A importing non-existent B produces an ERROR."""
    idx = IndexData()
    idx.memories["A"] = _make_entry("A", required=["B"])

    def mock_load_index(_root):
        return idx

    def mock_pfm(_fp):
        if "A" in str(_fp):
            return ({"type": "atom", "id": "A", "imports": {"required": ["B"]}}, "body A")
        return ({}, "")

    with patch("codememory.validate.load_index", mock_load_index), \
         patch("codememory.validate.parse_frontmatter", mock_pfm):
        errors, _w = validate(Path("."))
    # Error for B not existing
    assert errors >= 1


def test_no_broken_link_when_all_exist():
    """No errors when all imports exist."""
    idx = IndexData()
    idx.memories["A"] = _make_entry("A", required=["B"])
    idx.memories["B"] = _make_entry("B")

    def mock_load_index(_root):
        return idx

    def mock_pfm(_fp):
        # Both exist, no issues
        return ({"type": "atom", "id": "X", "imports": {"required": ["B"]}}, "body")

    with patch("codememory.validate.load_index", mock_load_index), \
         patch("codememory.validate.parse_frontmatter", mock_pfm):
        errors, _w = validate(Path("."))
    assert errors == 0


# ==================================================================
# 2.2 Schema compliance
# ==================================================================

def test_schema_compliance_missing_field():
    """Instance missing required field from its schema → error."""
    schemas = {
        "schemas/decision": {
            "fields": [
                {"name": "what", "required": True},
                {"name": "why", "required": False},
            ],
        },
    }
    metadata = {"schema": "schemas/decision", "id": "test", "type": "instance"}
    errors = check_schema_compliance(metadata, schemas)
    assert len(errors) == 1
    assert "what" in errors[0]


def test_schema_compliance_all_fields_present():
    """No error when all required fields are present."""
    schemas = {
        "schemas/decision": {
            "fields": [
                {"name": "what", "required": True},
            ],
        },
    }
    metadata = {"schema": "schemas/decision", "what": "value"}
    errors = check_schema_compliance(metadata, schemas)
    assert errors == []


def test_schema_compliance_no_schema():
    """No schema field → no compliance check → no errors."""
    schemas = {}
    metadata = {"id": "test"}
    errors = check_schema_compliance(metadata, schemas)
    assert errors == []


def test_schema_compliance_schema_not_found():
    """Schema ID pointing to non-existent schema → error."""
    schemas = {}
    metadata = {"schema": "schemas/nonexistent"}
    errors = check_schema_compliance(metadata, schemas)
    assert len(errors) == 1
    assert "not found" in errors[0].lower()


# ==================================================================
# 2.3 Cycle detection in validate
# ==================================================================

def test_validate_detects_cycle():
    """A→B→A produces a WARNING in validate output."""
    idx = IndexData()
    # A imports B, B imports A — a cycle
    idx.memories["A"] = _make_entry("A", required=["B"], path="A.md")
    idx.memories["B"] = _make_entry("B", required=["A"], path="B.md")

    def mock_load_index(_root):
        return idx

    def mock_pfm(filepath):
        if "A.md" in str(filepath):
            return ({"type": "atom", "id": "A", "imports": {"required": ["B"]}}, "body A")
        return ({"type": "atom", "id": "B", "imports": {"required": ["A"]}}, "body B")

    with patch("codememory.validate.load_index", mock_load_index), \
         patch("codememory.validate.parse_frontmatter", mock_pfm):
        errors, warnings = validate(Path("."))
    assert warnings >= 1  # Cycle warning


# ==================================================================
# 2.4-2.7 Decay rules
# ==================================================================

def test_decay_rule1_protected_intensity():
    """intensity >= 8 → skip (no decay warning)."""
    idx = IndexData()
    idx.memories["P"] = _make_entry("P", intensity=9, access_count=0)

    entry = idx.memories["P"]
    warnings = _check_decay("P", entry, idx)
    assert warnings == []


def test_decay_rule2_recent_access():
    """access_count > 0 + last_access within 30 days → skip."""
    idx = IndexData()
    recent = datetime.now() - timedelta(days=10)
    idx.memories["R"] = _make_entry(
        "R", intensity=5, access_count=1,
        last_access=recent.isoformat(),
    )

    entry = idx.memories["R"]
    warnings = _check_decay("R", entry, idx)
    assert warnings == []


def test_decay_rule2_old_access_decays():
    """access_count > 0 but last_access older than 30 days → may decay."""
    idx = IndexData()
    old = datetime.now() - timedelta(days=60)
    idx.memories["O"] = _make_entry(
        "O", intensity=5, access_count=2,
        last_access=old.isoformat(),
    )

    entry = idx.memories["O"]
    warnings = _check_decay("O", entry, idx)
    # Since in_degree is also 0, this should decay
    assert len(warnings) >= 1


def test_decay_rule3_referenced_skip():
    """in_degree > 0 (referenced by another memory) → skip."""
    idx = IndexData()
    idx.memories["Ref"] = _make_entry("Ref", intensity=5, access_count=0)
    idx.memories["User"] = _make_entry("User", required=["Ref"])

    entry = idx.memories["Ref"]
    warnings = _check_decay("Ref", entry, idx)
    assert warnings == []


def test_decay_rule4_no_protection_decays():
    """No protection, no access, no references → DECAY-WARN."""
    idx = IndexData()
    idx.memories["Cold"] = _make_entry(
        "Cold", intensity=3, access_count=0,
    )

    entry = idx.memories["Cold"]
    warnings = _check_decay("Cold", entry, idx)
    assert len(warnings) >= 1
    assert "low access" in warnings[0].lower() or "re-link" in warnings[0].lower()


# ==================================================================
# 2.7 + 2.8 Empty memory library
# ==================================================================

def test_empty_memory_library_no_crash():
    """0 memories → validate() completes without exception."""
    idx = IndexData()  # No memories

    def mock_load_index(_root):
        return idx

    with patch("codememory.validate.load_index", mock_load_index):
        errors, warnings = validate(Path("."))
    assert errors == 0
    assert warnings == 0


def test_validate_warns_for_missing_and_stale_source_artifacts(tmp_path: Path):
    """validate() reports source registry missing/stale artifacts as warnings."""
    source_file = tmp_path / "docs" / "design.md"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("version one", encoding="utf-8")

    add_source_artifact(
        tmp_path,
        uri="docs/design.md",
        source_id="src/stale-design",
        kind="markdown",
        summary="Stale design",
    )
    add_source_artifact(
        tmp_path,
        uri="docs/missing.md",
        source_id="src/missing-design",
        kind="markdown",
        summary="Missing design",
    )
    source_file.write_text("version two", encoding="utf-8")

    errors, warnings = validate(tmp_path)

    assert errors == 0
    assert warnings == 2


# ==================================================================
# Helper: _compute_in_degree
# ==================================================================

def test_compute_in_degree():
    """_compute_in_degree counts how many other memories reference this one."""
    idx = IndexData()
    idx.memories["Target"] = _make_entry("Target")
    idx.memories["A"] = _make_entry("A", required=["Target"])
    idx.memories["B"] = _make_entry("B", recommended=["Target"])
    idx.memories["C"] = _make_entry("C", related=["Other"])

    assert _compute_in_degree("Target", idx) >= 1
    assert _compute_in_degree("Other", idx) == 1
    assert _compute_in_degree("C", idx) == 0
