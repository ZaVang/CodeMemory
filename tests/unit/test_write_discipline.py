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


def test_create_writes_no_heat_fields(tmp_path: Path):
    """Phase C: create no longer writes intensity/stability frontmatter."""
    filepath = create(tmp_path, "atom", "user/facts/clean")
    meta, _body = parse_frontmatter(filepath)
    assert "intensity" not in meta
    assert "stability" not in meta


def test_memory_entry_has_no_heat_fields():
    """Phase C: the data model drops the four heat-machinery fields."""
    from codememory.models import MemoryEntry

    dump = MemoryEntry(id="x", type="atom").model_dump(mode="json")
    for field in ("intensity", "stability", "stability_source", "days_since_last_access"):
        assert field not in dump


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


# ==================================================================
# Slice 3: search default status filter
# ==================================================================

def _status_zoo(tmp_path: Path) -> None:
    """One atom per status, sharing a searchable summary token."""
    for status in ("active", "draft", "proposed", "archived", "superseded"):
        _write_atom(tmp_path, f"user/facts/zoo-{status}", status=status,
                    summary=f"zootoken {status} entry")
    reindex(tmp_path)


def test_search_default_returns_only_active_and_draft(tmp_path: Path):
    """Without an explicit status filter, search hides proposed/archived/superseded."""
    from codememory.search import search

    _status_zoo(tmp_path)
    results = search(tmp_path, query="zootoken")
    ids = {r["id"] for r in results}
    assert ids == {"user/facts/zoo-active", "user/facts/zoo-draft"}


def test_search_explicit_status_shows_proposed(tmp_path: Path):
    """--status proposed makes proposals visible."""
    from codememory.search import search

    _status_zoo(tmp_path)
    results = search(tmp_path, query="zootoken", status="proposed")
    ids = {r["id"] for r in results}
    assert ids == {"user/facts/zoo-proposed"}


# ==================================================================
# Slice 4: build paths skip non-assemblable statuses
# ==================================================================

def _graph_with_status_dep(tmp_path: Path, dep_status: str) -> None:
    """Active entry atom importing a dependency with the given status."""
    _write_atom(tmp_path, "user/contexts/entry", status="active",
                imports_required=["user/facts/dep"],
                summary="entry summary", body="ENTRY-BODY-MARKER")
    _write_atom(tmp_path, "user/facts/dep", status=dep_status,
                summary="dep summary", body="DEP-BODY-MARKER")
    reindex(tmp_path)


def test_resolve_skips_proposed_dependency(tmp_path: Path):
    """resolve assembles the active entry but skips its proposed import, with a notice."""
    from codememory.resolve import resolve

    _graph_with_status_dep(tmp_path, "proposed")
    output = resolve(tmp_path, "user/contexts/entry", depth="required")

    assert "ENTRY-BODY-MARKER" in output
    assert "DEP-BODY-MARKER" not in output
    assert "user/facts/dep" in output  # named in the notice
    assert "excluded_status" in output


def test_resolve_skips_archived_dependency(tmp_path: Path):
    """archived dependencies are equally non-assemblable."""
    from codememory.resolve import resolve

    _graph_with_status_dep(tmp_path, "archived")
    output = resolve(tmp_path, "user/contexts/entry", depth="required")

    assert "ENTRY-BODY-MARKER" in output
    assert "DEP-BODY-MARKER" not in output


def test_resolve_refuses_proposed_target(tmp_path: Path):
    """Resolving a proposed atom as the target is refused with guidance."""
    from codememory.resolve import resolve

    _write_atom(tmp_path, "user/facts/pending-target", status="proposed",
                body="PENDING-BODY-MARKER")
    reindex(tmp_path)

    output = resolve(tmp_path, "user/facts/pending-target")
    assert "PENDING-BODY-MARKER" not in output
    assert "proposed" in output
    assert "merge" in output


def test_context_pack_excludes_proposed_dependency(tmp_path: Path):
    """ContextPack drops proposed nodes from the graph and emits a notice."""
    from codememory.context_pack import build_context_pack

    _graph_with_status_dep(tmp_path, "proposed")
    pack = build_context_pack(tmp_path, "user/contexts/entry", depth="required")

    node_ids = {n.id for n in pack.nodes}
    assert "user/facts/dep" not in node_ids
    assert "user/contexts/entry" in node_ids
    assert any(n.type == "excluded_status" for n in pack.notices)


def test_context_pack_refuses_proposed_target(tmp_path: Path):
    """ContextPack raises for a proposed target, matching missing-target style."""
    from codememory.context_pack import build_context_pack

    _write_atom(tmp_path, "user/facts/pending-pack", status="proposed")
    reindex(tmp_path)

    with pytest.raises(ValueError, match="proposed"):
        build_context_pack(tmp_path, "user/facts/pending-pack")


# ==================================================================
# Slice 5: validate warnings (proposed backlog, status edges)
# ==================================================================

def test_validate_warns_stale_proposed_backlog(tmp_path: Path, capsys):
    """A proposal sitting unreviewed for >14 days triggers PROPOSED-WARN."""
    from codememory.validate import validate

    _write_atom(tmp_path, "user/facts/old-proposal", status="proposed",
                updated="2026-05-01")
    reindex(tmp_path)

    _errors, warnings = validate(tmp_path)
    out = capsys.readouterr().out
    assert "[PROPOSED-WARN]" in out
    assert "user/facts/old-proposal" in out
    assert warnings >= 1


def test_validate_fresh_proposed_no_backlog_warning(tmp_path: Path, capsys):
    """A proposal updated today is not flagged as backlog."""
    from datetime import datetime
    from codememory.validate import validate

    _write_atom(tmp_path, "user/facts/new-proposal", status="proposed",
                updated=datetime.now().strftime("%Y-%m-%d"))
    reindex(tmp_path)

    validate(tmp_path)
    out = capsys.readouterr().out
    assert "[PROPOSED-WARN]" not in out


def test_validate_warns_active_imports_proposed(tmp_path: Path, capsys):
    """An active atom importing a proposed one triggers STATUS-WARN."""
    from datetime import datetime
    from codememory.validate import validate

    today = datetime.now().strftime("%Y-%m-%d")
    _write_atom(tmp_path, "user/contexts/live-entry", status="active",
                imports_required=["user/facts/limbo"], updated=today)
    _write_atom(tmp_path, "user/facts/limbo", status="proposed", updated=today)
    reindex(tmp_path)

    _errors, warnings = validate(tmp_path)
    out = capsys.readouterr().out
    assert "[STATUS-WARN]" in out
    assert "user/facts/limbo" in out
    assert warnings >= 1


# ==================================================================
# Slice 6: update --source-ref (asset binding via CLI path)
# ==================================================================

def test_update_appends_source_ref(tmp_path: Path):
    """update with source_ref binds an asset reference into frontmatter and index."""
    from codememory.update import update

    filepath = create(tmp_path, "atom", "user/contexts/cache-layer")
    assert filepath is not None

    update(tmp_path, "user/contexts/cache-layer",
           change_note="bind rfc asset",
           source_ref="src/rfc-001-cache",
           source_ref_summary="RFC-001 cache design")

    meta, _body = parse_frontmatter(filepath)
    refs = meta.get("source_refs", [])
    assert any(r.get("artifact_id") == "src/rfc-001-cache" for r in refs)

    idx = load_index(tmp_path)
    entry_refs = idx.memories["user/contexts/cache-layer"].source_refs
    assert any(r.artifact_id == "src/rfc-001-cache" for r in entry_refs)
    assert any(r.summary == "RFC-001 cache design" for r in entry_refs)

    # Acceptance signal 5: the bound ref is carried into the context pack.
    from codememory.context_pack import build_context_pack

    pack = build_context_pack(tmp_path, "user/contexts/cache-layer", track_access=False)
    target_node = next(n for n in pack.nodes if n.id == "user/contexts/cache-layer")
    assert any(r.artifact_id == "src/rfc-001-cache" for r in target_node.source_refs)


def test_update_source_ref_duplicate_skipped(tmp_path: Path):
    """Binding the same artifact twice keeps a single source_ref entry."""
    from codememory.update import update

    filepath = create(tmp_path, "atom", "user/contexts/dup-check")
    assert filepath is not None

    update(tmp_path, "user/contexts/dup-check",
           change_note="bind once", source_ref="src/spec-md")
    update(tmp_path, "user/contexts/dup-check",
           change_note="bind twice", source_ref="src/spec-md")

    meta, _body = parse_frontmatter(filepath)
    refs = [r for r in meta.get("source_refs", [])
            if r.get("artifact_id") == "src/spec-md"]
    assert len(refs) == 1
