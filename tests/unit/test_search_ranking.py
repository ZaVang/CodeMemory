"""Phase B slice 1: lexical ranking for search (architecture.md §4.2).

score = Σ(field_weight × matched_tokens_in_field / total_tokens),
weights id=4 / summary=3 / tags=2 / body=1; OR semantics across tokens;
tie-break: dependents desc → access_count desc → id asc.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from codememory.index import reindex
from codememory.search import search


def _atom(
    root: Path,
    memory_id: str,
    *,
    summary: str = "plain summary",
    tags: str = "[fixture]",
    body: str = "plain body",
    imports_required: list[str] | None = None,
) -> None:
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
status: active
created: 2026-06-01
updated: 2026-06-10
version: 1
tags: {tags}
{imports_block}---

{body}
""",
        encoding="utf-8",
    )


def test_multitoken_ranks_strong_field_hits_above_body_hits(tmp_path: Path):
    """Both tokens hitting id+summary outranks a body-only single-token hit."""
    _atom(tmp_path, "user/facts/cache-layer-design",
          summary="cache layer write-through policy", body="nothing relevant")
    _atom(tmp_path, "user/facts/unrelated-note",
          summary="random note", body="mentions cache once in passing")
    reindex(tmp_path)

    results = search(tmp_path, query="cache layer")
    ids = [r["id"] for r in results]

    assert "user/facts/cache-layer-design" in ids
    assert "user/facts/unrelated-note" in ids  # OR semantics: partial hit stays
    assert ids[0] == "user/facts/cache-layer-design"


def test_or_semantics_partial_token_miss_does_not_eliminate(tmp_path: Path):
    """A token with zero hits anywhere does not eliminate entries matching others."""
    _atom(tmp_path, "user/facts/cache-note", summary="cache invalidation rules")
    reindex(tmp_path)

    results = search(tmp_path, query="cache zzzznonexistent")
    ids = [r["id"] for r in results]
    assert ids == ["user/facts/cache-note"]


def test_all_tokens_miss_eliminates(tmp_path: Path):
    """Entries where no token matches any field are excluded."""
    _atom(tmp_path, "user/facts/python-pin", summary="python version pin")
    reindex(tmp_path)

    results = search(tmp_path, query="qqqq zzzz")
    assert results == []


def test_equal_score_tiebreak_by_dependents(tmp_path: Path):
    """Same lexical score: the atom with more dependents ranks first."""
    _atom(tmp_path, "user/facts/widget-b", summary="widget token here")
    _atom(tmp_path, "user/facts/widget-a", summary="widget token here")
    # widget-b gains a dependent (importer should not match the query itself)
    _atom(tmp_path, "user/contexts/entry-point", summary="entry context",
          imports_required=["user/facts/widget-b"])
    reindex(tmp_path)

    results = search(tmp_path, query="widget")
    ids = [r["id"] for r in results]
    assert ids[0] == "user/facts/widget-b"
    assert ids[1] == "user/facts/widget-a"


def test_single_token_substring_compat(tmp_path: Path):
    """Single-token query still matches by substring (weighted version of old behavior)."""
    _atom(tmp_path, "user/facts/encoding-triage",
          summary="Windows encoding triage checklist")
    reindex(tmp_path)

    results = search(tmp_path, query="encod")
    assert [r["id"] for r in results] == ["user/facts/encoding-triage"]
