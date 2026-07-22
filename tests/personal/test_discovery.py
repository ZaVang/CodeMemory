from __future__ import annotations

from pathlib import Path

import pytest

from codememory.capture import append_capture
from codememory.handlers import handle_build
from codememory.index import load_index, reindex
from codememory.personal_index import read_personal_object, typed_search
from codememory.profile import init_personal_profile


TOPIC = """# 2026-07 Incubator

## Personal memory decisions
<!-- codememory:topic
topic_id: topic/personal-memory/decisions
revision_id: topic/personal-memory/decisions@2026-07
created_at: 2026-07-22T12:00:00+08:00
updated_at: 2026-07-22T13:00:00+08:00
origin: mixed
tags: [memory, decisions]
project: CodeMemory
people: [owner]
content_hash: sha256:test
derived_from: []
relations: []
-->

### Current understanding

Owner material and synthesis live together.

### Claim: imports remain canonical
<!-- codememory:claim
claim_id: claim/personal-memory/imports-canonical
origin: agent_inference
claim_status: unassessed
confidence: 0.72
derived_from: []
-->

This inference stays inside the Topic file.

## Long-lived unrelated notes
<!-- codememory:topic
topic_id: topic/long-lived-notes
revision_id: topic/long-lived-notes@2026-07
created_at: 2026-07-20T12:00:00+08:00
updated_at: 2026-07-20T13:00:00+08:00
origin: agent_synthesis
tags: [reflections]
content_hash: sha256:test-two
derived_from: []
relations: []
-->

This second Topic proves that one monthly file is not one Atom.
"""


ATOM = """---
type: atom
id: ideas/canonical-boundary
summary: Imports build canonical context
status: active
tags: [memory, decisions]
version: 1
created: 2026-07-22
updated: 2026-07-22
origin: agent_inference
claim_status: supported
topic: topic/personal-memory/decisions
project: CodeMemory
people: [owner]
imports: {}
---

Only atoms enter canonical build.
"""


def _instance(tmp_path: Path):
    init_personal_profile(tmp_path)
    capture = append_capture(tmp_path, "Raw motivation for canonical decisions")
    tmp_path.joinpath("incubator/2026-07.md").write_text(TOPIC, encoding="utf-8")
    atom_path = tmp_path / "memory" / "ideas" / "canonical-boundary.md"
    atom_path.parent.mkdir(parents=True)
    atom_path.write_text(ATOM, encoding="utf-8")
    reindex(tmp_path)
    return capture


def test_reindex_distinguishes_personal_object_kinds_and_indexes_inline_claim(tmp_path: Path):
    capture = _instance(tmp_path)
    index = load_index(tmp_path)

    assert capture.id in index.personal_objects
    topic_id = "topic/personal-memory/decisions@2026-07"
    assert index.personal_objects[topic_id].kind == "incubator_topic"
    assert "codememory:claim" in index.personal_objects[topic_id].content
    claim_id = "claim/personal-memory/imports-canonical"
    assert index.personal_objects[claim_id].kind == "incubator_claim"
    assert index.personal_objects[claim_id].metadata["claim_status"] == "unassessed"
    assert index.personal_objects["topic/long-lived-notes@2026-07"].kind == "incubator_topic"
    assert "ideas/canonical-boundary" in index.memories
    reindex(tmp_path)
    assert len(load_index(tmp_path).personal_objects) == 4


def test_typed_search_filters_and_routes_actions(tmp_path: Path):
    _instance(tmp_path)

    all_results = typed_search(tmp_path, query="canonical")
    assert {result["kind"] for result in all_results} == {"capture", "incubator_topic", "incubator_claim", "atom"}
    assert all({"id", "path", "display_locator", "summary", "metadata", "read_action"}.issubset(result) for result in all_results)
    assert {result["read_action"] for result in all_results if result["kind"] != "atom"} == {"read"}
    assert next(result for result in all_results if result["kind"] == "atom")["read_action"] == "build"

    atoms = typed_search(tmp_path, kinds=["atom"], claim_status="supported")
    assert [result["id"] for result in atoms] == ["ideas/canonical-boundary"]
    assert typed_search(tmp_path, kinds=["incubator_topic"], claim_status="supported") == []
    claims = typed_search(tmp_path, kinds=["incubator_claim"], claim_status="unassessed")
    assert [result["id"] for result in claims] == ["claim/personal-memory/imports-canonical"]
    assert len(typed_search(tmp_path, project="CodeMemory", person="owner", origin="mixed")) == 1
    tagged = typed_search(
        tmp_path,
        kinds=["incubator_topic"],
        tags=["memory"],
        date_from="2026-07-22",
        date_to="2026-07-22",
    )
    assert [result["id"] for result in tagged] == ["topic/personal-memory/decisions@2026-07"]
    assert typed_search(tmp_path, date_to="2026-07-19") == []


def test_read_uses_stable_id_after_display_line_changes(tmp_path: Path):
    capture = _instance(tmp_path)
    journal = tmp_path / capture.path
    journal.write_text("preface\n" + journal.read_text(encoding="utf-8"), encoding="utf-8")
    topic = tmp_path / "incubator/2026-07.md"
    topic.write_text("preface\n" + topic.read_text(encoding="utf-8"), encoding="utf-8")

    capture_read = read_personal_object(tmp_path, capture.id)
    topic_read = read_personal_object(tmp_path, "topic/personal-memory/decisions@2026-07")
    claim_read = read_personal_object(tmp_path, "claim/personal-memory/imports-canonical")

    assert capture_read.content == "Raw motivation for canonical decisions"
    assert "This inference stays inside" in topic_read.content
    assert claim_read.content == "This inference stays inside the Topic file."
    assert capture_read.display_locator.endswith(":4")


def test_build_rejects_noncanonical_objects_with_read_instruction(tmp_path: Path):
    capture = _instance(tmp_path)

    with pytest.raises(ValueError, match="not buildable; use read"):
        handle_build(tmp_path, capture.id)
    with pytest.raises(ValueError, match="not buildable; use read"):
        handle_build(tmp_path, "topic/personal-memory/decisions@2026-07")
    with pytest.raises(ValueError, match="not buildable; use read"):
        handle_build(tmp_path, "claim/personal-memory/imports-canonical")
    assert "ideas/canonical-boundary" in handle_build(tmp_path, "ideas/canonical-boundary")


def test_mcp_exposes_bound_phase_1a_reading_paths(tmp_path: Path, monkeypatch):
    capture = _instance(tmp_path)
    from codememory import mcp_server

    monkeypatch.delenv("CODEMEMORY_ROOT", raising=False)
    with pytest.raises(RuntimeError, match="explicit MCP instance binding"):
        mcp_server._get_root_from_env()

    monkeypatch.setenv("CODEMEMORY_ROOT", str(tmp_path))
    tools = {tool["name"]: tool for tool in mcp_server.TOOLS}
    assert {"capture_memory", "search_memories", "read_memory", "build_memory"}.issubset(tools)
    assert all("root" not in tool["inputSchema"].get("properties", {}) for tool in tools.values())

    read = mcp_server._call_tool("read_memory", {"id": capture.id})
    assert "Raw motivation" in read[0]["text"]
    rejected = mcp_server._call_tool("build_memory", {"id": capture.id})
    assert "use read" in rejected[0]["text"]
