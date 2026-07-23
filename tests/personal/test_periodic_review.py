from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
import yaml

from codememory.agent_tools import tool_specs_for_root
from codememory.capture import append_capture, capture_content_hash
from codememory.cli import main as cli_main
from codememory.index import load_index, reindex
from codememory.periodic_review import (
    PeriodicReviewBundle,
    load_periodic_review_bundle,
    prepare_periodic_review,
    resolve_periodic_window,
    save_periodic_review,
    serialize_periodic_review,
    write_periodic_review_bundle,
)
from codememory.profile import init_personal_profile


ZONE = ZoneInfo("Asia/Hong_Kong")


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "memory"
    assert init_personal_profile(root).profile_valid
    return root


def _topic(
    root: Path,
    *,
    month: str,
    topic_id: str,
    revision_id: str,
    updated_at: str,
    capture_id: str,
    capture_hash: str,
    claim_status: str = "unassessed",
    title: str = "Long-running idea",
) -> None:
    path = root / "incubator" / f"{month}.md"
    text = f"""# {month} Incubator

## {title}
<!-- codememory:topic
topic_id: {topic_id}
revision_id: {revision_id}
created_at: {updated_at}
updated_at: {updated_at}
origin: mixed
content_hash: sha256:{revision_id.replace('/', '-')}
tags: [review]
derived_from:
  - kind: capture
    id: {capture_id}
    content_hash: {capture_hash}
relations: []
merged_from: []
-->

Understanding at {revision_id}.

### Claim: durable claim
<!-- codememory:claim
claim_id: claim/durable
origin: agent_inference
claim_status: {claim_status}
derived_from:
  - kind: capture
    id: {capture_id}
    content_hash: {capture_hash}
-->

Claim snapshot at {revision_id}.
"""
    path.write_text(text, encoding="utf-8")


def _instance(tmp_path: Path) -> tuple[Path, object, object, object]:
    root = _root(tmp_path)
    old = append_capture(
        root,
        "June evidence",
        now=datetime(2026, 6, 20, 8, tzinfo=ZONE),
    )
    current = append_capture(
        root,
        "July evidence",
        now=datetime(2026, 7, 10, 8, tzinfo=ZONE),
    )
    unrelated = append_capture(
        root,
        "Old unrelated evidence",
        now=datetime(2026, 5, 10, 8, tzinfo=ZONE),
    )
    _topic(
        root,
        month="2026-06",
        topic_id="topic/durable",
        revision_id="rev/durable/2026-06",
        updated_at="2026-06-25T10:00:00+08:00",
        capture_id=old.id,
        capture_hash=old.content_hash,
    )
    _topic(
        root,
        month="2026-07",
        topic_id="topic/durable",
        revision_id="rev/durable/2026-07",
        updated_at="2026-07-20T10:00:00+08:00",
        capture_id=current.id,
        capture_hash=current.content_hash,
        claim_status="supported",
    )
    _topic(
        root,
        month="2026-05",
        topic_id="topic/unrelated",
        revision_id="rev/unrelated/2026-05",
        updated_at="2026-05-20T10:00:00+08:00",
        capture_id=unrelated.id,
        capture_hash=unrelated.content_hash,
        title="Unrelated history",
    )
    atom = root / "memory/ideas/durable.md"
    atom.parent.mkdir(parents=True)
    atom.write_text(
        """---
type: atom
id: memory/ideas/durable
summary: Promoted durable idea
status: active
created: 2026-07-21
updated: 2026-07-21
version: 1
tags: [review]
imports: {}
origin: agent_synthesis
topic: topic/durable
provenance:
  topic_id: topic/durable
  topic_revision_id: rev/durable/2026-07
  topic_revision_hash: sha256:revision
  owner_confirmed: true
---
# Durable
""",
        encoding="utf-8",
    )
    proposed = root / "memory/ideas/proposed.md"
    proposed.write_text(
        """---
type: atom
id: memory/ideas/proposed
summary: Proposed
status: proposed
created: 2026-07-21
version: 1
tags: []
imports: {}
provenance:
  topic_revision_id: rev/durable/2026-07
---
# Proposed
""",
        encoding="utf-8",
    )
    reindex(root)
    return root, old, current, unrelated


def _bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _directory_link(link: Path, target: Path) -> None:
    if os.name == "nt":
        subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
            check=True,
            capture_output=True,
            text=True,
        )
    else:
        link.symlink_to(target, target_is_directory=True)


def test_calendar_windows_use_profile_timezone(tmp_path: Path) -> None:
    root = _root(tmp_path)
    monthly = resolve_periodic_window(root, period="monthly", anchor="2026-07")
    yearly = resolve_periodic_window(root, period="yearly", anchor="2026")

    assert monthly.date_from == "2026-07-01T00:00:00.000000+08:00"
    assert monthly.date_to == "2026-07-31T23:59:59.999999+08:00"
    assert yearly.date_from == "2026-01-01T00:00:00.000000+08:00"
    assert yearly.date_to == "2026-12-31T23:59:59.999999+08:00"
    with pytest.raises(ValueError, match="YYYY-MM"):
        resolve_periodic_window(root, period="monthly", anchor="2026-7")
    with pytest.raises(ValueError, match="YYYY"):
        resolve_periodic_window(root, period="yearly", anchor="26")


def test_bundle_is_deterministic_read_only_and_selects_bounded_evidence(tmp_path: Path) -> None:
    root, old, current, unrelated = _instance(tmp_path)
    before = _bytes(root)
    first = prepare_periodic_review(root, period="monthly", anchor="2026-07")
    second = prepare_periodic_review(root, period="monthly", anchor="2026-07")

    assert serialize_periodic_review(first) == serialize_periodic_review(second)
    assert first.bundle_digest == second.bundle_digest
    assert _bytes(root) == before
    assert [(item.revision_id, item.is_baseline) for item in first.topics] == [
        ("rev/durable/2026-06", True),
        ("rev/durable/2026-07", False),
    ]
    captures = {item.id: item for item in first.captures}
    assert captures[old.id].in_period is False
    assert captures[current.id].in_period is True
    assert unrelated.id not in captures
    assert first.claim_transitions[0].from_status == "unassessed"
    assert first.claim_transitions[0].to_status == "supported"
    assert [item.id for item in first.canonical] == ["memory/ideas/durable"]
    assert str(root.resolve()) not in serialize_periodic_review(first)


def test_invalid_capture_is_excluded_with_bounded_diagnostic(tmp_path: Path) -> None:
    root, _, _, _ = _instance(tmp_path)
    journal = root / "journal/2026/07/2026-07-22.md"
    journal.write_text(
        "# 2026-07-22\n\n"
        "## 10:00 — cap_01K0R8Y7M0M8QW8R1J4Y4S0F4M\n"
        "<!-- codememory:capture\n"
        "id: cap_01K0R8Y7M0M8QW8R1J4Y4S0F4M\n"
        "captured_at: 2026-07-22T10:00:00+08:00\n"
        "actor: owner\n"
        f"content_hash: {capture_content_hash('expected secret value')}\n"
        "-->\ntampered secret value\n",
        encoding="utf-8",
    )

    bundle = prepare_periodic_review(root, period="monthly", anchor="2026-07")
    assert all(item.id != "cap_01K0R8Y7M0M8QW8R1J4Y4S0F4M" for item in bundle.captures)
    diagnostics = "\n".join(bundle.diagnostics)
    assert "hash mismatch" in diagnostics
    assert "secret value" not in diagnostics
    assert str(root.resolve()) not in diagnostics


def test_malformed_topic_and_claim_are_excluded_with_diagnostics(tmp_path: Path) -> None:
    root, *_ = _instance(tmp_path)
    incubator = root / "incubator/2026-07.md"
    with open(incubator, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(
            "\n\n### Claim: malformed\n"
            "<!-- codememory:claim\n"
            "claim_id: claim/malformed\n"
            "claim_status: invented\n"
            "-->\n"
            "Must not enter the bundle.\n\n"
            "## Invalid topic\n"
            "<!-- codememory:topic\n"
            "topic_id: topic/invalid\n"
            "updated_at: 2026-07-22T10:00:00+08:00\n"
            "-->\n"
            "Must not enter the bundle.\n"
        )

    bundle = prepare_periodic_review(root, period="monthly", anchor="2026-07")
    assert all(topic.topic_id != "topic/invalid" for topic in bundle.topics)
    assert all(
        claim.claim_id != "claim/malformed"
        for topic in bundle.topics
        for claim in topic.claims
    )
    diagnostics = "\n".join(bundle.diagnostics)
    assert "invalid Topic ignored" in diagnostics
    assert "invalid claim_status ignored: claim/malformed" in diagnostics


def test_output_is_atomic_no_clobber_and_load_verifies_digest(tmp_path: Path) -> None:
    root, *_ = _instance(tmp_path)
    bundle = prepare_periodic_review(root, period="monthly", anchor="2026-07")
    output = tmp_path / "bundle.json"
    write_periodic_review_bundle(output, bundle)

    assert load_periodic_review_bundle(output) == bundle
    with pytest.raises(FileExistsError):
        write_periodic_review_bundle(output, bundle)
    raw = json.loads(output.read_text(encoding="utf-8"))
    raw["window"]["anchor"] = "2026-08"
    output.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="digest mismatch"):
        load_periodic_review_bundle(output)


def test_explicit_save_is_bounded_idempotent_and_noncanonical(tmp_path: Path) -> None:
    root, *_ = _instance(tmp_path)
    bundle = prepare_periodic_review(root, period="monthly", anchor="2026-07")
    first = save_periodic_review(root, bundle, "## Facts\n\nA bounded review.")
    path = root / first.path
    before = path.read_bytes()
    second = save_periodic_review(root, bundle, "## Facts\n\nA bounded review.")

    assert first.path == "reviews/monthly/2026-07.md"
    assert second.reused is True
    assert path.read_bytes() == before
    assert "bundle_digest:" in path.read_text(encoding="utf-8")
    with pytest.raises(FileExistsError):
        save_periodic_review(root, bundle, "Changed")
    replaced = save_periodic_review(root, bundle, "Changed", overwrite=True)
    assert replaced.overwritten is True
    reindex(root)
    assert all("reviews/" not in entry.path for entry in load_index(root).memories.values())


def test_save_rejects_tamper_empty_and_reviews_junction_escape(tmp_path: Path) -> None:
    root, *_ = _instance(tmp_path)
    bundle = prepare_periodic_review(root, period="monthly", anchor="2026-07")
    tampered = PeriodicReviewBundle.model_validate(bundle.model_dump(mode="json"))
    tampered.source_ids.append("forged")
    with pytest.raises(ValueError, match="digest mismatch"):
        save_periodic_review(root, tampered, "Review")
    with pytest.raises(ValueError, match="must not be empty"):
        save_periodic_review(root, bundle, " ")

    outside = tmp_path / "outside"
    outside.mkdir()
    reviews = root / "reviews"
    reviews.rmdir()
    _directory_link(reviews, outside)
    try:
        with pytest.raises(ValueError, match="outside bound root"):
            save_periodic_review(root, bundle, "Review")
        assert list(outside.rglob("*")) == []
    finally:
        os.rmdir(reviews)


@pytest.mark.parametrize("profile_path", ["journal", "incubator"])
def test_prepare_rejects_input_junction_escape(
    tmp_path: Path,
    profile_path: str,
) -> None:
    root = _root(tmp_path)
    outside = tmp_path / f"outside-{profile_path}"
    outside.mkdir()
    configured = root / profile_path
    configured.rmdir()
    _directory_link(configured, outside)
    try:
        with pytest.raises(ValueError, match=f"paths.{profile_path} resolves outside bound root"):
            prepare_periodic_review(root, period="monthly", anchor="2026-07")
        assert list(outside.rglob("*")) == []
    finally:
        os.rmdir(configured)


def test_cli_prepare_and_save_remain_owner_only(tmp_path: Path, capsys) -> None:
    root, *_ = _instance(tmp_path)
    output = tmp_path / "bundle.json"
    cli_main([
        "--root", str(root),
        "periodic-review", "prepare",
        "--period", "monthly",
        "--anchor", "2026-07",
        "--output", str(output),
    ])
    assert '"status": "prepared"' in capsys.readouterr().out
    content = tmp_path / "review.md"
    content.write_text("Owner-requested review", encoding="utf-8")
    cli_main([
        "--root", str(root),
        "periodic-review", "save",
        "--bundle", str(output),
        "--content", str(content),
    ])
    assert '"path": "reviews/monthly/2026-07.md"' in capsys.readouterr().out

    names = {spec.name for spec in tool_specs_for_root(root)}
    assert all("periodic" not in name for name in names)
