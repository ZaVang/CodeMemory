from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from codememory.capture import (
    append_capture,
    capture_content_hash,
    scan_all_captures,
    scan_capture_file,
)
from codememory.index import load_index, reindex
from codememory.personal_index import read_personal_object
from codememory.profile import init_personal_profile
from codememory.cli import main as cli_main


def test_hash_normalizes_newlines_without_trimming():
    assert capture_content_hash("a\r\nb\r") == capture_content_hash("a\nb\n")
    assert capture_content_hash("a") != capture_content_hash("a\n")
    assert capture_content_hash(" a") != capture_content_hash("a")


def test_capture_succeeds_without_git_and_round_trips_payload(tmp_path: Path):
    init_personal_profile(tmp_path)
    record = append_capture(tmp_path, "原文\r\n保留尾部空格 ")
    scanned = scan_all_captures(tmp_path)

    assert record.id.startswith("cap_") and len(record.id) == 30
    assert record.line == 3
    assert scanned.warnings == []
    assert scanned.captures[0].id == record.id
    assert scanned.captures[0].payload == "原文\n保留尾部空格 "
    assert scanned.captures[0].content_hash == record.content_hash


def test_capture_ids_are_unique_and_time_sortable(tmp_path: Path):
    init_personal_profile(tmp_path)
    start = datetime(2026, 7, 22, 10, 0, tzinfo=ZoneInfo("Asia/Hong_Kong"))
    first = append_capture(tmp_path, "first", now=start)
    second = append_capture(tmp_path, "second", now=start + timedelta(milliseconds=1))
    third = append_capture(tmp_path, "third", now=start + timedelta(milliseconds=2))

    assert first.id < second.id < third.id
    assert len({first.id, second.id, third.id}) == 3
    assert len(list(tmp_path.joinpath("journal").rglob("*.md"))) == 1
    assert len(scan_all_captures(tmp_path).captures) == 3


def test_concurrent_capture_produces_complete_blocks(tmp_path: Path):
    init_personal_profile(tmp_path)
    with ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(lambda i: append_capture(tmp_path, f"payload {i}"), range(12)))
    scanned = scan_all_captures(tmp_path)

    assert len({record.id for record in records}) == 12
    assert len(scanned.captures) == 12
    assert scanned.warnings == []


def test_incomplete_trailing_capture_is_ignored_and_validate_reports_it(tmp_path: Path, capsys):
    init_personal_profile(tmp_path)
    complete = append_capture(tmp_path, "complete")
    path = tmp_path / complete.path
    with path.open("a", encoding="utf-8") as handle:
        handle.write("## 11:00 — cap_01KY0000000000000000000000\n<!-- codememory:capture\nid:")

    scanned = scan_capture_file(tmp_path, path)

    assert [item.id for item in scanned.captures] == [complete.id]
    assert any("incomplete" in warning for warning in scanned.warnings)
    cli_main(["--root", str(tmp_path), "validate"])
    validation_output = capsys.readouterr().out
    assert "[CAPTURE-WARN] incomplete" in validation_output
    assert "Warnings: 1" in validation_output
    reindex(tmp_path)
    assert set(load_index(tmp_path).personal_objects) == {complete.id}


def test_hash_mismatch_is_reported_but_not_indexed_or_readable(tmp_path: Path, capsys):
    init_personal_profile(tmp_path)
    record = append_capture(tmp_path, "trusted body")
    reindex(tmp_path)
    path = tmp_path / record.path
    path.write_text(
        path.read_text(encoding="utf-8").replace("trusted body", "tampered body"),
        encoding="utf-8",
    )

    scanned = scan_capture_file(tmp_path, path)
    assert any("hash mismatch" in warning for warning in scanned.warnings)
    assert scanned.captures == []
    with pytest.raises(KeyError, match="no longer resolves"):
        read_personal_object(tmp_path, record.id)

    cli_main(["--root", str(tmp_path), "validate"])
    assert "[CAPTURE-WARN] Capture hash mismatch" in capsys.readouterr().out
    reindex(tmp_path)
    assert record.id not in load_index(tmp_path).personal_objects
    with pytest.raises(KeyError, match="not found"):
        read_personal_object(tmp_path, record.id)


def test_cli_init_and_capture_argument_path(tmp_path: Path, capsys):
    cli_main(["init", str(tmp_path), "--profile", "personal"])
    capsys.readouterr()
    cli_main(["--root", str(tmp_path), "capture", "CLI payload"])
    output = capsys.readouterr().out

    assert '"id": "cap_' in output
    assert scan_all_captures(tmp_path).captures[0].payload == "CLI payload"
