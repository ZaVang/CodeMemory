"""Phase C slice 1: golden-question test contract (architecture.md §3.4).

Core exports the question set plus assembled context as JSON; the agent/CI
is the runner; `test report` writes results back to the audit log.
Core stays free of any LLM dependency.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from codememory.index import reindex


def _atom(
    root: Path,
    memory_id: str,
    *,
    summary: str = "fixture summary",
    body: str = "fixture body",
    golden_block: str = "",
) -> Path:
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
{golden_block}---

{body}
""",
        encoding="utf-8",
    )
    return file_path


GOLDEN = """golden_questions:
  - q: "缓存层用什么失效策略？"
    expect: "写穿透 + 5min TTL"
  - q: "谁负责判分？"
"""


def test_test_command_exports_questions_and_context(tmp_path: Path):
    """handle_test returns JSON with format_version, entry, context, questions."""
    from codememory.handlers import handle_test

    _atom(tmp_path, "user/contexts/cache", body="CACHE-BODY-MARKER",
          golden_block=GOLDEN)
    reindex(tmp_path)

    data = json.loads(handle_test(tmp_path, "user/contexts/cache"))
    assert data["format_version"] == "memory-test/v1"
    assert data["entry"] == "user/contexts/cache"
    assert "CACHE-BODY-MARKER" in data["context"]
    assert [q["q"] for q in data["questions"]] == ["缓存层用什么失效策略？", "谁负责判分？"]
    assert data["questions"][0]["expect"] == "写穿透 + 5min TTL"
    assert data["questions"][1]["expect"] is None


def test_test_command_empty_questions_is_notice_not_error(tmp_path: Path):
    """An entry without golden_questions exports an empty set plus a notice."""
    from codememory.handlers import handle_test

    _atom(tmp_path, "user/contexts/bare")
    reindex(tmp_path)

    data = json.loads(handle_test(tmp_path, "user/contexts/bare"))
    assert data["questions"] == []
    assert any("golden_questions" in n for n in data["notices"])


def test_test_report_writes_audit_log(tmp_path: Path):
    """test report validates {q, answer, pass} entries and logs a summary."""
    from codememory.handlers import handle_test_report

    _atom(tmp_path, "user/contexts/cache", golden_block=GOLDEN)
    reindex(tmp_path)

    results_file = tmp_path / "results.json"
    results_file.write_text(json.dumps([
        {"q": "缓存层用什么失效策略？", "answer": "写穿透", "pass": True},
        {"q": "谁负责判分？", "answer": "agent", "pass": False},
    ], ensure_ascii=False), encoding="utf-8")

    summary = handle_test_report(tmp_path, "user/contexts/cache", str(results_file))
    assert "1/2" in summary

    log_text = (tmp_path / ".codememory" / "log.md").read_text(encoding="utf-8")
    assert "test_report" in log_text
    assert "user/contexts/cache" in log_text


def test_test_report_rejects_malformed_results(tmp_path: Path):
    """Results missing required keys are rejected with an error."""
    from codememory.handlers import handle_test_report

    _atom(tmp_path, "user/contexts/cache", golden_block=GOLDEN)
    reindex(tmp_path)

    results_file = tmp_path / "bad.json"
    results_file.write_text(json.dumps([{"question": "no q key"}]), encoding="utf-8")

    with pytest.raises(ValueError):
        handle_test_report(tmp_path, "user/contexts/cache", str(results_file))


def test_validate_warns_on_malformed_golden_questions(tmp_path: Path, capsys):
    """check reports golden_questions entries that are not {q, ...} mappings."""
    from codememory.validate import validate

    _atom(tmp_path, "user/contexts/broken",
          golden_block="golden_questions:\n  - 只是一个字符串\n")
    reindex(tmp_path)

    validate(tmp_path)
    out = capsys.readouterr().out
    assert "[GOLDEN-WARN]" in out
    assert "user/contexts/broken" in out
