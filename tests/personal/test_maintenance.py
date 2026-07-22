from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from codememory.capture import append_capture
from codememory.cli import main as cli_main
from codememory.maintenance import (
    STATE_RELATIVE_PATH,
    ClaimDraft,
    MaintenanceState,
    ProvenanceRef,
    TopicDraft,
    TopicParagraph,
    load_maintenance_events,
    load_maintenance_state,
    maintenance_status,
    prepare_maintenance,
    resume_maintenance,
    save_maintenance_state,
)
from codememory.personal_index import scan_all_topics
from codememory.profile import init_personal_profile


ZONE = ZoneInfo("Asia/Hong_Kong")


def _profile(tmp_path: Path) -> Path:
    init_personal_profile(tmp_path)
    return tmp_path


def _drafts(captures, title="Catch-up"):
    return [TopicDraft(
        title=title,
        month=captures[0].captured_at[:7],
        paragraphs=[
            TopicParagraph(
                text=capture.payload,
                origin="human_explicit",
                derived_from=[ProvenanceRef(capture_id=capture.id, content_hash=capture.content_hash)],
            )
            for capture in captures
        ],
    )]


def test_missed_run_catch_up_and_same_input_are_idempotent(tmp_path: Path) -> None:
    root = _profile(tmp_path)
    start = datetime(2026, 7, 1, 9, tzinfo=ZONE)
    captures = [append_capture(root, f"note {day}", now=start + timedelta(days=day)) for day in range(3)]
    first = prepare_maintenance(root, drafts=_drafts(captures), now=start + timedelta(days=3))
    assert first.capture_ids == [item.id for item in captures]
    assert first.stage == "applied"
    before = (root / "incubator/2026-07.md").read_text(encoding="utf-8")
    second = prepare_maintenance(root)
    assert second.stage == "applied"
    assert second.run_id == first.run_id
    assert second.reused is True
    assert (root / "incubator/2026-07.md").read_text(encoding="utf-8") == before
    assert len(scan_all_topics(root).topics) == 1


def test_resume_uses_same_pending_changeset_after_write(tmp_path: Path) -> None:
    root = _profile(tmp_path)
    capture = append_capture(root, "recover me", now=datetime(2026, 7, 3, 9, tzinfo=ZONE))
    result = prepare_maintenance(root, drafts=_drafts([capture], "Recovery"))
    run_id = result.run_id
    assert run_id
    pending_path = root / ".codememory/maintenance/pending" / f"{run_id}.json"
    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    # Simulate a process that wrote the file but did not append the applied event.
    events_path = root / ".codememory/maintenance/runs.jsonl"
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    events_path.write_text(
        "\n".join(json.dumps(event) for event in events if event["stage"] != "applied") + "\n",
        encoding="utf-8",
    )
    save_maintenance_state(root, MaintenanceState(active_run_id=run_id, active_stage="applying"))
    before_pending = pending_path.read_bytes()
    resumed = resume_maintenance(root)
    assert resumed.stage == "applied"
    assert pending_path.read_bytes() == before_pending
    assert capture.id in resumed.capture_ids


def test_topic_mixed_origin_and_inline_claim(tmp_path: Path) -> None:
    root = _profile(tmp_path)
    capture = append_capture(root, "observed fact", now=datetime(2026, 7, 4, 9, tzinfo=ZONE))
    ref = ProvenanceRef(capture_id=capture.id, content_hash=capture.content_hash)
    draft = TopicDraft(
        title="Mixed topic",
        origin="mixed",
        paragraphs=[TopicParagraph(text="Synthesis", derived_from=[ref])],
        claims=[ClaimDraft(title="Likely effect", text="An inference", derived_from=[ref])],
        month="2026-07",
    )
    prepare_maintenance(root, drafts=[draft])
    path = root / "incubator/2026-07.md"
    text = path.read_text(encoding="utf-8")
    assert "origin: mixed" in text
    assert "codememory:claim" in text
    assert "claim_id: claim_" in text
    assert list((root / "incubator").glob("*.md")) == [path]


def test_existing_topic_upsert_keeps_one_section_and_old_provenance(tmp_path: Path) -> None:
    root = _profile(tmp_path)
    first = append_capture(root, "first evidence", now=datetime(2026, 7, 4, 9, tzinfo=ZONE))
    first_ref = ProvenanceRef(capture_id=first.id, content_hash=first.content_hash)
    initial = TopicDraft(
        topic_id="top_shared_subject",
        title="Shared subject",
        month="2026-07",
        paragraphs=[TopicParagraph(text="Initial", derived_from=[first_ref])],
    )
    prepare_maintenance(root, drafts=[initial])
    second = append_capture(root, "second evidence", now=datetime(2026, 7, 5, 9, tzinfo=ZONE))
    second_ref = ProvenanceRef(capture_id=second.id, content_hash=second.content_hash)
    revised = TopicDraft(
        topic_id="top_shared_subject",
        title="Renamed subject",
        month="2026-07",
        paragraphs=[TopicParagraph(text="Revised", derived_from=[first_ref, second_ref])],
    )
    prepare_maintenance(root, drafts=[revised])
    text = (root / "incubator/2026-07.md").read_text(encoding="utf-8")
    assert text.count("topic_id: top_shared_subject") == 1
    assert "## Renamed subject" in text
    assert first.id in text and second.id in text


def test_skill_interaction_contract_is_explicit() -> None:
    skill = Path(".agents/skills/personal-memory/SKILL.md").read_text(encoding="utf-8")
    assert "record-only request" in skill and "Do not ask follow-up questions" in skill
    assert "explicitly asks you to continue asking questions" in skill
    assert "critical ambiguity" in skill and "Do not interrupt for optional enrichment" in skill


def test_core_requires_skill_changeset_and_does_not_guess_topics(tmp_path: Path) -> None:
    root = _profile(tmp_path)
    capture = append_capture(root, "record only", now=datetime(2026, 7, 7, 9, tzinfo=ZONE))
    with pytest.raises(ValueError, match="requires a Topic changeset"):
        prepare_maintenance(root)
    assert capture.id in maintenance_status(root)["unconsumed_capture_ids"]
    assert list((root / "incubator").glob("*.md")) == []


def test_cli_status_and_changeset_run(tmp_path: Path, capsys) -> None:
    root = _profile(tmp_path)
    capture = append_capture(root, "CLI capture", now=datetime(2026, 7, 8, 9, tzinfo=ZONE))
    cli_main(["--root", str(root), "maintenance", "status"])
    assert capture.id in capsys.readouterr().out
    changeset = {"topics": [draft.model_dump(mode="json") for draft in _drafts([capture], "CLI topic")]}
    path = tmp_path / "changeset.json"
    path.write_text(json.dumps(changeset), encoding="utf-8")
    cli_main(["--root", str(root), "maintenance", "run", "--changeset", str(path)])
    output = capsys.readouterr().out
    assert '"stage": "applied"' in output
    assert (root / "incubator/2026-07.md").exists()


def test_concurrent_wakeups_share_one_active_run(tmp_path: Path) -> None:
    root = _profile(tmp_path)
    capture = append_capture(root, "one wakeup", now=datetime(2026, 7, 9, 9, tzinfo=ZONE))
    drafts = _drafts([capture], "Concurrent")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: prepare_maintenance(root, drafts=drafts), range(2)))
    assert results[0].run_id == results[1].run_id
    events = load_maintenance_events(root)
    assert sum(event.stage == "prepared" for event in events) == 1
    assert sum(event.stage == "applied" for event in events) == 1
