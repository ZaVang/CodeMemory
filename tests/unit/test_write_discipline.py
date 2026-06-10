"""Phase A write-discipline tests: proposed status, merge/reject, filtering semantics.

Contract: docs/plan/SPRINT.md (Phase A), docs/architecture.md §3.2/§3.3/§4.3/§4.4.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from codememory.core import parse_frontmatter
from codememory.create import create
from codememory.index import load_index, reindex


def _write_atom(
    root: Path,
    memory_id: str,
    *,
    status: str = "active",
    imports_required: list[str] | None = None,
    updated: str = "2026-06-10",
    summary: str = "fixture summary",
    body: str = "fixture body",
) -> Path:
    """Write a memory file directly (fixture isolation from create/update)."""
    file_path = root / f"{memory_id}.md"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    imports_block = ""
    if imports_required:
        deps = "".join(f"\n    - {d}" for d in imports_required)
        imports_block = f"imports:\n  required:{deps}\n  recommended: []\n  related: []\n"
    file_path.write_text(
        f"""---
type: atom
id: {memory_id}
summary: "{summary}"
status: {status}
created: 2026-06-01
updated: {updated}
version: 1
tags: [fixture]
{imports_block}---

{body}
""",
        encoding="utf-8",
    )
    return file_path


# ==================================================================
# Slice 1: create --propose + protected decoupling
# ==================================================================

def test_create_propose_sets_proposed_status(tmp_path: Path):
    """create(propose=True) writes an atom with status: proposed."""
    filepath = create(tmp_path, "atom", "user/facts/tentative", propose=True)
    assert filepath is not None
    meta, _body = parse_frontmatter(filepath)
    assert meta["status"] == "proposed"


def test_create_default_status_stays_active(tmp_path: Path):
    """Without propose, create keeps the default active status."""
    filepath = create(tmp_path, "atom", "user/facts/normal")
    meta, _body = parse_frontmatter(filepath)
    assert meta["status"] == "active"


def test_create_intensity8_no_auto_protected(tmp_path: Path):
    """Phase A decoupling: intensity >= 8 no longer auto-sets protected."""
    filepath = create(tmp_path, "atom", "user/facts/important", intensity=8)
    meta, _body = parse_frontmatter(filepath)
    assert "protected" not in meta


# ==================================================================
# Slice 2: merge / reject
# ==================================================================

def test_merge_proposed_becomes_active(tmp_path: Path):
    """merge turns a proposed atom into active and reindexes it."""
    from codememory.update import merge

    filepath = create(tmp_path, "atom", "user/facts/pending", propose=True)
    assert filepath is not None

    merge(tmp_path, "user/facts/pending")

    meta, _body = parse_frontmatter(filepath)
    assert meta["status"] == "active"
    idx = load_index(tmp_path)
    assert idx.memories["user/facts/pending"].status == "active"


def test_reject_proposed_becomes_archived(tmp_path: Path):
    """reject turns a proposed atom into archived."""
    from codememory.update import reject

    filepath = create(tmp_path, "atom", "user/facts/bad-idea", propose=True)
    assert filepath is not None

    reject(tmp_path, "user/facts/bad-idea")

    meta, _body = parse_frontmatter(filepath)
    assert meta["status"] == "archived"


def test_merge_non_proposed_exits(tmp_path: Path):
    """merge on a non-proposed atom is an error (exit 1)."""
    from codememory.update import merge

    create(tmp_path, "atom", "user/facts/already-active")

    with pytest.raises(SystemExit):
        merge(tmp_path, "user/facts/already-active")
