from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from codememory.build import build_context_pack
from codememory.capture import append_capture
from codememory.core import parse_frontmatter
from codememory.maintenance import ProvenanceRef, TopicDraft, TopicParagraph, prepare_maintenance
from codememory.personal_index import scan_all_topics
from codememory.profile import init_personal_profile
from codememory.promotion import ReviewAction, apply_review_batch, merge_topics, promote_topic
from codememory.search import search


def _topic(tmp_path: Path):
    init_personal_profile(tmp_path)
    capture = append_capture(tmp_path, "formal candidate", now=datetime(2026, 7, 5, 9, tzinfo=ZoneInfo("Asia/Hong_Kong")))
    prepare_maintenance(tmp_path, drafts=_drafts([capture]))
    return scan_all_topics(tmp_path).topics[0]


def _drafts(captures):
    return [TopicDraft(
        title=capture.payload,
        month=capture.captured_at[:7],
        topic_id=f"top_{capture.id[4:]}",
        paragraphs=[TopicParagraph(
            text=capture.payload,
            origin="human_explicit",
            derived_from=[ProvenanceRef(capture_id=capture.id, content_hash=capture.content_hash)],
        )],
    ) for capture in captures]


def test_agent_promotion_is_proposed_and_hidden(tmp_path: Path) -> None:
    topic = _topic(tmp_path)
    path = promote_topic(tmp_path, topic.revision_id, "memory/candidate")
    meta, _ = parse_frontmatter(path)
    assert meta["status"] == "proposed"
    assert search(tmp_path, query="formal candidate") == []
    with pytest.raises(ValueError, match="not assemblable"):
        build_context_pack(tmp_path, "memory/candidate")


def test_explicit_owner_confirmation_activates_with_provenance(tmp_path: Path) -> None:
    topic = _topic(tmp_path)
    path = promote_topic(tmp_path, topic.revision_id, "memory/formal", owner_confirmed=True)
    meta, _ = parse_frontmatter(path)
    assert meta["status"] == "active"
    assert meta["provenance"]["owner_confirmed"] is True
    assert meta["provenance"]["topic_revision_id"] == topic.revision_id
    assert meta["provenance"]["captures"][0]["content_hash"].startswith("sha256:")


def test_one_review_batch_can_promote_merge_and_delete(tmp_path: Path) -> None:
    init_personal_profile(tmp_path)
    zone = ZoneInfo("Asia/Hong_Kong")
    captures = [
        append_capture(tmp_path, text, now=datetime(2026, 7, 5, hour, tzinfo=zone))
        for text, hour in (("one", 9), ("merge source", 10), ("merge target", 11), ("delete me", 12))
    ]
    prepare_maintenance(tmp_path, drafts=_drafts(captures))
    topics = scan_all_topics(tmp_path).topics
    result = apply_review_batch(tmp_path, [
        ReviewAction(action="promote", revision_id=topics[0].revision_id, atom_id="memory/one", owner_confirmed=True),
        ReviewAction(action="merge", revision_id=topics[1].revision_id, target_revision_id=topics[2].revision_id),
        ReviewAction(action="delete", revision_id=topics[3].revision_id),
    ])
    assert result.promoted == ["memory/one"]
    assert len(result.merged) == 1
    assert result.deleted == [topics[3].revision_id]
    assert len(scan_all_topics(tmp_path).topics) == 2


def test_review_batch_can_merge_topics_without_new_claim_file(tmp_path: Path) -> None:
    init_personal_profile(tmp_path)
    zone = ZoneInfo("Asia/Hong_Kong")
    captures = [
        append_capture(tmp_path, "merge source", now=datetime(2026, 7, 5, 9, tzinfo=zone)),
        append_capture(tmp_path, "merge target", now=datetime(2026, 7, 5, 10, tzinfo=zone)),
    ]
    prepare_maintenance(tmp_path, drafts=_drafts(captures))
    topics = scan_all_topics(tmp_path).topics
    result = apply_review_batch(tmp_path, [
        ReviewAction(action="merge", revision_id=topics[0].revision_id, target_revision_id=topics[1].revision_id),
    ])
    remaining = scan_all_topics(tmp_path).topics
    assert len(result.merged) == 1
    assert len(remaining) == 1
    assert "merge source" in remaining[0].content
    assert list((tmp_path / "incubator").glob("*.md")) == [tmp_path / "incubator/2026-07.md"]


def test_self_merge_rejects_before_mutating_topic_file(tmp_path: Path) -> None:
    topic = _topic(tmp_path)
    path = tmp_path / topic.path
    before = path.read_bytes()
    with pytest.raises(ValueError, match="cannot merge a Topic revision into itself"):
        merge_topics(tmp_path, topic.revision_id, topic.revision_id)
    assert path.read_bytes() == before
