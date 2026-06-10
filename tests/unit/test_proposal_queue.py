"""Phase C slice 2: modification-class proposal patch queue (architecture §3.3).

High-risk changes to existing atoms land as patch records under
.codememory/proposals/; the owner merges (apply via update, version++) or
rejects (discard). merge/reject dispatch: proposal id first, then the
Phase A proposed-atom path.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from codememory.core import parse_frontmatter
from codememory.index import reindex


def _atom(root: Path, memory_id: str, *, summary: str = "old summary") -> Path:
    file_path = root / f"{memory_id}.md"
    file_path.parent.mkdir(parents=True, exist_ok=True)
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
---

old body
""",
        encoding="utf-8",
    )
    return file_path


def test_propose_queues_patch_without_touching_target(tmp_path: Path):
    """propose writes a patch record and leaves the target atom unmodified."""
    from codememory.proposals import create_proposal, list_proposals

    target = _atom(tmp_path, "user/facts/pin")
    reindex(tmp_path)

    prop = create_proposal(tmp_path, "user/facts/pin",
                           reason="3.14 轮子已齐", summary="new summary")

    assert prop.target_id == "user/facts/pin"
    assert prop.patch.summary == "new summary"
    queue = list_proposals(tmp_path)
    assert [p.proposal_id for p in queue] == [prop.proposal_id]

    meta, body = parse_frontmatter(target)
    assert meta["summary"] == "old summary"
    assert meta["version"] == 1
    assert "old body" in body


def test_propose_requires_nonempty_patch(tmp_path: Path):
    """A proposal with no patched fields is rejected."""
    from codememory.proposals import create_proposal

    _atom(tmp_path, "user/facts/pin")
    reindex(tmp_path)

    with pytest.raises(SystemExit):
        create_proposal(tmp_path, "user/facts/pin", reason="无实际变更")


def test_merge_applies_patch_and_clears_queue(tmp_path: Path):
    """merge(proposal_id) applies the patch via update: version++, change_log, queue cleared."""
    from codememory.proposals import create_proposal, list_proposals
    from codememory.update import merge

    target = _atom(tmp_path, "user/facts/pin")
    reindex(tmp_path)
    prop = create_proposal(tmp_path, "user/facts/pin",
                           reason="解除版本钉死", summary="new summary",
                           body="new body")

    merge(tmp_path, prop.proposal_id)

    meta, body = parse_frontmatter(target)
    assert meta["summary"] == "new summary"
    assert "new body" in body
    assert meta["version"] == 2
    assert any("解除版本钉死" in c.get("note", "") for c in meta["change_log"])
    assert list_proposals(tmp_path) == []

    log_text = (tmp_path / ".codememory" / "log.md").read_text(encoding="utf-8")
    assert prop.proposal_id in log_text


def test_reject_discards_patch_leaving_target_intact(tmp_path: Path):
    """reject(proposal_id) drops the record; the target atom is untouched."""
    from codememory.proposals import create_proposal, list_proposals
    from codememory.update import reject

    target = _atom(tmp_path, "user/facts/pin")
    reindex(tmp_path)
    prop = create_proposal(tmp_path, "user/facts/pin",
                           reason="不该改", summary="bad idea")

    reject(tmp_path, prop.proposal_id)

    assert list_proposals(tmp_path) == []
    meta, _ = parse_frontmatter(target)
    assert meta["summary"] == "old summary"
    assert meta["version"] == 1


def test_validate_warns_on_stale_and_orphaned_proposals(tmp_path: Path, capsys):
    """check reports patch backlog (>14 days) and proposals whose target vanished."""
    from codememory.proposals import create_proposal, proposals_dir
    from codememory.validate import validate

    _atom(tmp_path, "user/facts/pin")
    reindex(tmp_path)
    prop = create_proposal(tmp_path, "user/facts/pin",
                           reason="老提案", summary="stale change")

    # Backdate the record and retarget a second one at a ghost atom
    record_path = proposals_dir(tmp_path) / f"{prop.proposal_id}.json"
    data = json.loads(record_path.read_text(encoding="utf-8"))
    data["created_at"] = "2026-05-01T00:00:00"
    record_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    ghost = dict(data)
    ghost["proposal_id"] = "0099-ghost"
    ghost["target_id"] = "user/facts/ghost"
    (proposals_dir(tmp_path) / "0099-ghost.json").write_text(
        json.dumps(ghost, ensure_ascii=False), encoding="utf-8")

    validate(tmp_path)
    out = capsys.readouterr().out
    assert "[PROPOSAL-WARN]" in out
    assert prop.proposal_id in out          # backlog warning
    assert "user/facts/ghost" in out        # missing-target warning
