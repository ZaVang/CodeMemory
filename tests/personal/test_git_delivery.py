from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from codememory.capture import append_capture
from codememory.git_delivery import deliver_maintenance
from codememory.handlers import handle_maintenance_resume
from codememory.maintenance import (
    MaintenanceState,
    ProvenanceRef,
    TopicDraft,
    TopicParagraph,
    load_maintenance_state,
    prepare_maintenance,
    save_maintenance_state,
)
from codememory.personal_index import scan_all_topics
from codememory.profile import init_personal_profile, load_personal_profile
from codememory.promotion import promote_topic


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)


def _repo(tmp_path: Path, *, push: bool = False) -> tuple[Path, Path]:
    root = tmp_path / "profile"
    remote = tmp_path / "remote.git"
    init_personal_profile(root, auto_commit=True, auto_push=push, branch="memory")
    _git(root, "init")
    _git(root, "config", "user.name", "Test Owner")
    _git(root, "config", "user.email", "owner@example.test")
    subprocess.run(["git", "init", "--bare", str(remote)], capture_output=True, check=True)
    _git(root, "remote", "add", "origin", str(remote))
    _git(root, "add", ".")
    _git(root, "commit", "-m", "baseline")
    return root, remote


def _maintain(root: Path, text: str = "safe note"):
    capture = append_capture(root, text, now=datetime(2026, 7, 6, 9, tzinfo=ZoneInfo("Asia/Hong_Kong")))
    return prepare_maintenance(root, drafts=_drafts([capture]))


def _drafts(captures):
    return [TopicDraft(
        title="Delivery topic",
        month=captures[0].captured_at[:7],
        paragraphs=[TopicParagraph(
            text=capture.payload,
            origin="human_explicit",
            derived_from=[ProvenanceRef(capture_id=capture.id, content_hash=capture.content_hash)],
        ) for capture in captures],
    )]


def test_sensitive_scan_blocks_without_revealing_value_and_capture_continues(tmp_path: Path) -> None:
    root, _ = _repo(tmp_path)
    secret = "sk-" + "A" * 32
    run = _maintain(root, secret)
    result = deliver_maintenance(root)
    assert result.stage == "scan_blocked"
    assert result.findings[0].rule == "openai_key"
    assert secret not in result.model_dump_json()
    before = _git(root, "rev-list", "--count", "HEAD").stdout.strip()
    append_capture(root, "captured while blocked")
    assert _git(root, "rev-list", "--count", "HEAD").stdout.strip() == before
    assert load_maintenance_state(root).active_run_id == run.run_id


def test_scan_blocked_resumes_same_run_then_catches_up_new_capture(tmp_path: Path) -> None:
    root, _ = _repo(tmp_path)
    secret = "sk-" + "B" * 32
    run = _maintain(root, secret)
    assert deliver_maintenance(root).stage == "scan_blocked"
    late = append_capture(root, "late capture")
    for path in (root / "journal").rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if secret in text:
            # Explicit owner cleanup may remove raw records; Git history has no secret
            # because the safety scan prevented the first commit.
            path.write_text("", encoding="utf-8")
    incubator = root / "incubator/2026-07.md"
    incubator.write_text(incubator.read_text(encoding="utf-8").replace(secret, "[REDACTED]"), encoding="utf-8")
    resumed = deliver_maintenance(root, run.run_id)
    assert resumed.stage == "committed"
    assert load_maintenance_state(root).active_run_id is None
    caught_up = prepare_maintenance(root, drafts=_drafts([late]))
    assert caught_up.run_id != run.run_id
    assert late.id in caught_up.capture_ids


def test_commit_has_one_trailer_and_runtime_state_stays_clean(tmp_path: Path) -> None:
    root, _ = _repo(tmp_path)
    run = _maintain(root)
    result = deliver_maintenance(root)
    assert result.stage == "committed"
    body = _git(root, "show", "-s", "--format=%B", result.commit or "HEAD").stdout
    assert body.count(f"CodeMemory-Run: {run.run_id}") == 1
    assert deliver_maintenance(root, run.run_id).commit == result.commit
    assert _git(root, "rev-list", "--count", "HEAD").stdout.strip() == "2"
    status = _git(root, "status", "--porcelain").stdout
    assert ".codememory/maintenance/state.json" not in status


def test_failed_push_retries_same_commit(tmp_path: Path) -> None:
    root, remote = _repo(tmp_path, push=True)
    run = _maintain(root)
    _git(root, "remote", "set-url", "origin", str(tmp_path / "missing.git"))
    first = deliver_maintenance(root)
    assert first.stage == "committed"
    count = _git(root, "rev-list", "--count", "HEAD").stdout.strip()
    _git(root, "remote", "set-url", "origin", str(remote))
    second = deliver_maintenance(root, run.run_id)
    assert second.stage == "pushed"
    assert second.commit == first.commit
    assert _git(root, "rev-list", "--count", "HEAD").stdout.strip() == count
    remote_head = subprocess.run(
        ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/memory"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert remote_head == second.commit


def test_public_resume_retries_failed_push_and_recovers_missing_delivery_state(tmp_path: Path) -> None:
    root, remote = _repo(tmp_path, push=True)
    run = _maintain(root)
    _git(root, "remote", "set-url", "origin", str(tmp_path / "missing.git"))
    first = deliver_maintenance(root)
    assert first.stage == "committed"
    # Simulate exit after commit creation but before delivery state was persisted.
    save_maintenance_state(root, MaintenanceState(active_run_id=run.run_id, active_stage="scan_passed"))
    _git(root, "remote", "set-url", "origin", str(remote))
    resumed = json.loads(handle_maintenance_resume(root))
    assert resumed["stage"] == "pushed"
    assert resumed["commit"] == first.commit
    remote_head = subprocess.run(
        ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/memory"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert remote_head == first.commit


def test_high_entropy_value_blocks_without_echo_or_commit(tmp_path: Path) -> None:
    root, _ = _repo(tmp_path)
    value = "A7dK9pQ2sV5xY8bC1eF4hJ6mN3rT0uWzL5oP8iS2gD7kM9qR4vX6yB1cE3fH0jU"
    _maintain(root, value)
    before = _git(root, "rev-list", "--count", "HEAD").stdout.strip()
    result = deliver_maintenance(root)
    assert result.stage == "scan_blocked"
    assert any(finding.rule == "high_entropy" for finding in result.findings)
    assert value not in result.model_dump_json()
    assert _git(root, "rev-list", "--count", "HEAD").stdout.strip() == before


def test_delivery_supports_chinese_canonical_path(tmp_path: Path) -> None:
    root, _ = _repo(tmp_path)
    run = _maintain(root, "长期状态候选")
    topic = scan_all_topics(root).topics[0]
    promoted = promote_topic(root, topic.revision_id, "memory/长期状态", owner_confirmed=True)
    assert promoted.exists()
    result = deliver_maintenance(root, run.run_id)
    assert result.stage == "committed"
    names = _git(root, "-c", "core.quotePath=false", "show", "--format=", "--name-only", result.commit or "HEAD").stdout
    assert "memory/长期状态.md" in names


def test_unknown_change_blocks_and_private_runtime_never_stage(tmp_path: Path) -> None:
    root, _ = _repo(tmp_path)
    _maintain(root)
    (root / "outside.txt").write_text("owner work", encoding="utf-8")
    result = deliver_maintenance(root)
    assert result.stage == "blocked"
    assert "outside.txt" in (result.detail or "")
    assert _git(root, "diff", "--cached", "--name-only").stdout == ""
