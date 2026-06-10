"""Phase B slices 3-4: two-pass trim, inert-metadata contract, command unification.

Contract: docs/architecture.md §4.1 (build pipeline), §5.1 (maturity/evidence are
inert metadata), docs/plan/SPRINT.md Phase B deliverables 2/3/5.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from codememory.build import build_context_pack
from codememory.index import load_index, reindex, save_index


def _atom(
    root: Path,
    memory_id: str,
    *,
    summary: str = "short summary",
    body: str = "short body",
    required: list[str] | None = None,
    related: list[str] | None = None,
) -> None:
    file_path = root / f"{memory_id}.md"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    imports_block = ""
    if required or related:
        imports_block = "imports:\n"
        if required:
            imports_block += "  required:\n" + "".join(f"    - {d}\n" for d in required)
        if related:
            imports_block += "  related:\n" + "".join(f"    - {d}\n" for d in related)
    file_path.write_text(
        f"""---
type: atom
id: {memory_id}
summary: "{summary}"
status: active
created: 2026-06-01
updated: 2026-06-10
version: 1
tags: [fixture]
{imports_block}---

{body}
""",
        encoding="utf-8",
    )


def _trims(pack) -> dict[str, str]:
    return {n.id: n.trim for n in pack.nodes}


# ==================================================================
# Slice 3: two-pass trim (architecture §4.1 step 4)
# ==================================================================

def test_two_pass_trim_target_wins_over_required_leaf(tmp_path: Path):
    """Budget fits one full body: the target keeps it, the leaf degrades.

    Under the old topological-greedy trim the leaf (rendered first) ate the
    budget and the target itself was downgraded to summary.
    """
    _atom(tmp_path, "user/g/entry", body="E" * 600, summary="entry summary",
          required=["user/g/leaf"])
    _atom(tmp_path, "user/g/leaf", body="L" * 600, summary="leaf summary")
    reindex(tmp_path)

    pack = build_context_pack(tmp_path, "user/g/entry", depth="required",
                              budget=800, track_access=False)
    trims = _trims(pack)
    assert trims["user/g/entry"] == "full"
    assert trims["user/g/leaf"] == "summary"


def test_two_pass_same_level_tiebreak_by_dependents(tmp_path: Path):
    """Within the required level, the dep with more dependents keeps full text."""
    _atom(tmp_path, "user/g/top", body="T" * 100, summary="top summary",
          required=["user/g/depa", "user/g/depb"])
    _atom(tmp_path, "user/g/depa", body="A" * 400, summary="depa summary")
    _atom(tmp_path, "user/g/depb", body="B" * 400, summary="depb summary")
    # depa gains an extra dependent outside the closure
    _atom(tmp_path, "user/g/outsider", body="o", summary="user/g/outsider", required=["user/g/depa"])
    reindex(tmp_path)

    pack = build_context_pack(tmp_path, "user/g/top", depth="required",
                              budget=700, track_access=False)
    trims = _trims(pack)
    assert trims["user/g/top"] == "full"
    assert trims["user/g/depa"] == "full"
    assert trims["user/g/depb"] == "summary"


def test_related_skipped_required_floors_at_summary(tmp_path: Path):
    """Tiny budget: required degrades to summary (never skipped), related skipped."""
    _atom(tmp_path, "user/g/hub", body="H" * 300, summary="hub summary",
          required=["user/g/must"], related=["user/g/maybe"])
    _atom(tmp_path, "user/g/must", body="M" * 300, summary="must summary")
    _atom(tmp_path, "user/g/maybe", body="Y" * 300, summary="maybe summary")
    reindex(tmp_path)

    pack = build_context_pack(tmp_path, "user/g/hub", depth="full",
                              budget=10, track_access=False)
    trims = _trims(pack)
    assert trims["user/g/hub"] == "summary"
    assert trims["user/g/must"] == "summary"
    assert trims["user/g/maybe"] == "skipped"


# ==================================================================
# Slice 3: inert metadata contract (architecture §5.1)
# ==================================================================

def test_build_tracking_writes_only_access_telemetry(tmp_path: Path):
    """Assembly updates access_count/last_access but never maturity/stability."""
    _atom(tmp_path, "user/g/solo", body="S" * 50, summary="solo summary")
    reindex(tmp_path)

    idx = load_index(tmp_path)
    entry = idx.memories["user/g/solo"]
    entry.access_count = 2
    entry.last_access = (datetime.now() - timedelta(days=10)).isoformat()
    entry.days_since_last_access = 10
    entry.stability = 14.0
    entry.maturity = "draft"
    save_index(tmp_path, idx)

    build_context_pack(tmp_path, "user/g/solo", budget=10_000, track_access=True)

    after = load_index(tmp_path).memories["user/g/solo"]
    assert after.access_count == 3
    assert after.days_since_last_access == 0
    assert after.maturity == "draft"      # no auto-upgrade
    assert after.stability == 14.0        # no SInc growth


# ==================================================================
# Slice 4: one pipeline behind build / resolve / context-pack
# ==================================================================

def _strip_volatile(text: str) -> str:
    """Drop the generation-timestamp line so cross-invocation outputs compare."""
    return "\n".join(
        line for line in text.splitlines()
        if "Generated At" not in line and "generated_at" not in line
    )


def _consistency_fixture(tmp_path: Path) -> None:
    _atom(tmp_path, "user/g/ctx", body="C" * 80, summary="ctx summary",
          required=["user/g/factx"])
    _atom(tmp_path, "user/g/factx", body="F" * 80, summary="factx summary")
    reindex(tmp_path)


def test_resolve_renders_through_the_pipeline(tmp_path: Path):
    """resolve output is the pipeline's plain-markdown render, not a bespoke format."""
    from codememory.resolve import resolve

    _consistency_fixture(tmp_path)
    output = resolve(tmp_path, "user/g/ctx", depth="required")
    assert output.startswith("# CodeMemory Context Pack: user/g/ctx")
    assert "C" * 80 in output
    assert "F" * 80 in output


def test_build_plain_markdown_equals_resolve(tmp_path: Path):
    """handle_build(plain-markdown) and handle_resolve produce identical output."""
    from codememory.handlers import handle_build, handle_resolve

    _consistency_fixture(tmp_path)
    built = handle_build(tmp_path, "user/g/ctx", depth="required",
                         output_format="plain-markdown")
    resolved = handle_resolve(tmp_path, "user/g/ctx", depth="required")
    assert _strip_volatile(built) == _strip_volatile(resolved)


def test_build_xml_equals_context_pack(tmp_path: Path):
    """handle_build(xml-markdown) and handle_context_pack produce identical output."""
    from codememory.handlers import handle_build, handle_context_pack

    _consistency_fixture(tmp_path)
    built = handle_build(tmp_path, "user/g/ctx", depth="recommended")
    packed = handle_context_pack(tmp_path, "user/g/ctx", depth="recommended")
    assert _strip_volatile(built) == _strip_volatile(packed)


def test_resolve_missing_target_keeps_error_string_contract(tmp_path: Path):
    """resolve still returns an Error: string for missing targets (CLI contract)."""
    from codememory.resolve import resolve

    _consistency_fixture(tmp_path)
    output = resolve(tmp_path, "user/g/nonexistent")
    assert output.startswith("Error:")
    assert "user/g/nonexistent" in output
