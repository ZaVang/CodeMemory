"""Shared MCP / Toolkit agent-surface contracts."""

from __future__ import annotations

import asyncio
import importlib
import json
from pathlib import Path

import pytest

from codememory import mcp_server
from codememory.agent_tools import dispatch_agent_tool, tool_specs_for_root
from codememory.core import get_memory_path, parse_frontmatter
from codememory.create import create
from codememory.integrations import CodememoryToolkit
from codememory.profile import init_personal_profile
from codememory.proposals import list_proposals
from codememory.sources import add_source_artifact


CORE_NAMES = {
    "build_memory",
    "search_memories",
    "expand_source",
    "create_memory",
    "propose_memory",
}
PERSONAL_NAMES = {
    "capture_memory",
    "read_memory",
    "maintenance_status",
    "maintain_memory",
    "resume_memory_maintenance",
    "review_personal_memory",
}
LEGACY_NAMES = {
    "resolve_context",
    "resolve_memory",
    "update_memory",
    "propose_update",
    "validate_memories",
    "snapshot",
    "find_orphans",
    "changelog",
    "log",
    "import_memories",
}


def _toolkit_schema_map(root: Path) -> dict[str, dict]:
    tools = CodememoryToolkit(str(root)).get_tools_for_openai()
    return {
        tool["function"]["name"]: tool["function"]["parameters"]
        for tool in tools
    }


def _mcp_schema_map(root: Path) -> dict[str, dict]:
    return {tool["name"]: tool["inputSchema"] for tool in mcp_server._mcp_tools_for_root(root)}


def test_standard_toolkit_and_mcp_have_exact_shared_surface(tmp_path: Path):
    toolkit = _toolkit_schema_map(tmp_path)
    mcp = _mcp_schema_map(tmp_path)

    assert set(toolkit) == CORE_NAMES
    assert set(mcp) == CORE_NAMES
    assert toolkit == mcp
    assert not (set(toolkit) & LEGACY_NAMES)
    assert all("root" not in schema["properties"] for schema in toolkit.values())

    read_only = {
        tool["name"] for tool in mcp_server._mcp_tools_for_root(tmp_path)
        if tool["readOnlyHint"]
    }
    assert read_only == {"build_memory", "search_memories", "expand_source"}


def test_personal_toolkit_and_mcp_add_exact_extension(tmp_path: Path):
    init_personal_profile(tmp_path)

    toolkit = _toolkit_schema_map(tmp_path)
    mcp = _mcp_schema_map(tmp_path)

    assert set(toolkit) == CORE_NAMES | PERSONAL_NAMES
    assert toolkit == mcp
    assert toolkit["create_memory"]["properties"]["propose"]["enum"] == [True]
    assert all("root" not in schema["properties"] for schema in toolkit.values())


def test_provider_exports_are_schema_equivalent(tmp_path: Path):
    toolkit = CodememoryToolkit(str(tmp_path))
    openai = {
        item["function"]["name"]: item["function"]["parameters"]
        for item in toolkit.get_tools_for_openai()
    }
    anthropic = {item["name"]: item["input_schema"] for item in toolkit.get_tools_for_anthropic()}
    gemini = {item["name"]: item["parameters"] for item in toolkit.get_tools_for_gemini()}
    assert openai == anthropic == gemini == _mcp_schema_map(tmp_path)


def test_standard_create_is_complete_atomic_and_supports_proposed(tmp_path: Path, monkeypatch):
    reindex_calls: list[Path] = []
    create_module = importlib.import_module("codememory.create")
    monkeypatch.setattr(create_module, "reindex", lambda root: reindex_calls.append(Path(root)))
    result = dispatch_agent_tool(
        tmp_path,
        "create_memory",
        {
            "id": "user/ideas/complete",
            "summary": "Complete creation",
            "body": "# Complete\n\nWritten once.",
            "tags": ["agent"],
            "import_related": ["user/facts/reference"],
            "propose": True,
        },
    )

    path = tmp_path / "user/ideas/complete.md"
    meta, body = parse_frontmatter(path)
    assert "Status: proposed" in result
    assert meta["summary"] == "Complete creation"
    assert meta["status"] == "proposed"
    assert meta["imports"]["related"] == ["user/facts/reference"]
    assert meta["source"]["created_by"] == "agent"
    assert body == "# Complete\n\nWritten once."
    assert reindex_calls == [tmp_path.resolve()]


def test_personal_create_forces_proposed_and_ignores_forged_root(tmp_path: Path):
    root = tmp_path / "personal"
    other = tmp_path / "other"
    init_personal_profile(root)
    other.mkdir()

    dispatch_agent_tool(
        root,
        "create_memory",
        {
            "id": "memory/agent-created",
            "summary": "Owner gated",
            "body": "# Owner gated",
            "propose": False,
            "root": str(other),
        },
    )

    path = root / "memory/agent-created.md"
    meta, _body = parse_frontmatter(path)
    assert meta["status"] == "proposed"
    assert path.exists()
    assert not (other / "memory/agent-created.md").exists()
    assert "agent-created" not in dispatch_agent_tool(root, "search_memories", {})
    with pytest.raises(ValueError, match="not assemblable"):
        dispatch_agent_tool(root, "build_memory", {"id": "memory/agent-created"})


def test_create_memory_rejects_all_reported_id_escape_forms(tmp_path: Path):
    root = tmp_path / "bound"
    root.mkdir()
    sibling_forward = tmp_path / "other" / "escape.md"
    sibling_backslash = tmp_path / "other" / "backslash-escape.md"
    drive_target = tmp_path / "drive-escape.md"
    unsafe_ids = [
        "../other/escape",
        r"..\other\backslash-escape",
        drive_target.with_suffix("").as_posix(),
        "/escape-abs",
    ]

    for memory_id in unsafe_ids:
        with pytest.raises(ValueError, match="unsafe memory_id"):
            dispatch_agent_tool(
                root,
                "create_memory",
                {
                    "id": memory_id,
                    "summary": "Must stay bound",
                    "body": "# Must stay bound",
                },
            )

    assert list(root.rglob("*.md")) == []
    assert not sibling_forward.exists()
    assert not sibling_backslash.exists()
    assert not drive_target.exists()


@pytest.mark.parametrize(
    "memory_id",
    [
        "",
        "user//empty",
        "user/./dot",
        "user/../parent",
        "user/trailing/",
        " user/leading-space",
        "user/trailing-space ",
        "C:drive-relative",
    ],
)
def test_memory_id_requires_strict_relative_segments(tmp_path: Path, memory_id: str):
    with pytest.raises(ValueError, match="unsafe memory_id"):
        get_memory_path(tmp_path, memory_id)


def test_memory_id_accepts_nested_unicode_path_inside_root(tmp_path: Path):
    root = tmp_path / "bound"
    expected = root.resolve() / "memory" / "长期状态.md"
    assert get_memory_path(root, "memory/长期状态") == expected


def test_propose_memory_rejects_escaped_target_before_queue_write(tmp_path: Path):
    root = tmp_path / "bound"
    root.mkdir()
    with pytest.raises(ValueError, match="unsafe memory_id"):
        dispatch_agent_tool(
            root,
            "propose_memory",
            {
                "id": "../other/escape",
                "reason": "Must not inspect an external target",
                "body": "# Escaped proposal",
            },
        )
    assert list_proposals(root) == []
    assert not (root / ".codememory" / "proposals").exists()


def test_propose_memory_queues_patch_without_target_mutation(tmp_path: Path):
    create(
        tmp_path,
        "atom",
        "user/facts/target",
        summary="Before",
        body="# Before\n\nOriginal body.",
    )
    target = tmp_path / "user/facts/target.md"
    before = target.read_bytes()

    result = dispatch_agent_tool(
        tmp_path,
        "propose_memory",
        {
            "id": "user/facts/target",
            "reason": "Correct the durable fact",
            "summary": "After",
            "body": "# After\n\nProposed body.",
        },
    )

    assert target.read_bytes() == before
    proposals = list_proposals(tmp_path)
    assert len(proposals) == 1
    assert proposals[0].target_id == "user/facts/target"
    assert proposals[0].patch.summary == "After"
    assert proposals[0].proposal_id in result


@pytest.mark.parametrize("state", ["fresh", "stale", "missing"])
def test_expand_source_uses_shared_structured_handler(tmp_path: Path, state: str):
    source = tmp_path / "source.md"
    source.write_text("abcdef", encoding="utf-8")
    add_source_artifact(tmp_path, str(source), source_id="src/test")
    if state == "stale":
        source.write_text("changed", encoding="utf-8")
    elif state == "missing":
        source.unlink()

    payload = json.loads(
        dispatch_agent_tool(
            tmp_path,
            "expand_source",
            {"artifact_id": "src/test", "max_chars": 3},
        )
    )
    assert payload["status"] == state
    if state == "fresh":
        assert payload["content"] == "abc"
        assert payload["truncated"] is True


def test_expand_source_payload_matches_sandbox_and_mcp(tmp_path: Path, monkeypatch):
    from harnesslib.sandbox import Sandbox

    source = tmp_path / "source.md"
    source.write_text("shared payload", encoding="utf-8")
    add_source_artifact(tmp_path, str(source), source_id="src/shared")
    arguments = {"artifact_id": "src/shared", "max_chars": 6}
    expected = json.loads(dispatch_agent_tool(tmp_path, "expand_source", arguments))

    sandbox = Sandbox()
    asyncio.run(CodememoryToolkit(str(tmp_path)).register_to_sandbox(sandbox))
    sandbox_result = asyncio.run(sandbox.execute("expand_source", arguments))
    assert json.loads(sandbox_result["result"]) == expected

    monkeypatch.setenv("CODEMEMORY_ROOT", str(tmp_path))
    mcp_result = mcp_server._call_tool("expand_source", arguments)
    assert json.loads(mcp_result[0]["text"]) == expected


def test_sandbox_registration_is_bound_and_legacy_names_are_unavailable(tmp_path: Path):
    from harnesslib.sandbox import Sandbox

    other = tmp_path / "other"
    other.mkdir()
    sandbox = Sandbox()
    asyncio.run(CodememoryToolkit(str(tmp_path)).register_to_sandbox(sandbox))
    assert {tool.name for tool in sandbox.list_tools()} == CORE_NAMES

    result = asyncio.run(
        sandbox.execute(
            "create_memory",
            {
                "id": "user/facts/bound",
                "summary": "Bound root",
                "body": "# Bound",
                "root": str(other),
            },
        )
    )
    assert "Created memory" in result["result"]
    assert (tmp_path / "user/facts/bound.md").exists()
    assert not (other / "user/facts/bound.md").exists()


def test_mcp_uses_bound_root_and_returns_bounded_errors(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CODEMEMORY_ROOT", raising=False)
    with pytest.raises(RuntimeError, match="required"):
        mcp_server._get_root_from_env()

    monkeypatch.setenv("CODEMEMORY_ROOT", str(tmp_path))
    result = mcp_server._call_tool(
        "create_memory",
        {
            "id": "user/facts/mcp",
            "summary": "MCP bound",
            "body": "# MCP",
            "root": str(tmp_path / "elsewhere"),
        },
    )
    assert "Created memory" in result[0]["text"]
    assert (tmp_path / "user/facts/mcp.md").exists()

    unknown = mcp_server._call_tool("update_memory", {"id": "user/facts/mcp"})
    assert unknown[0]["text"].startswith("Error calling 'update_memory'")
    assert "Traceback" not in unknown[0]["text"]


def test_mcp_jsonrpc_list_and_unknown_call_use_bound_profile(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    init_personal_profile(tmp_path)
    monkeypatch.setenv("CODEMEMORY_ROOT", str(tmp_path))

    mcp_server._handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    listed = json.loads(capsys.readouterr().out)
    assert {tool["name"] for tool in listed["result"]["tools"]} == CORE_NAMES | PERSONAL_NAMES

    mcp_server._handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "update_memory", "arguments": {}},
        }
    )
    called = json.loads(capsys.readouterr().out)
    assert called["result"]["isError"] is True
    assert "Traceback" not in called["result"]["content"][0]["text"]


def test_shared_catalog_has_no_root_property(tmp_path: Path):
    for spec in tool_specs_for_root(tmp_path):
        assert spec.input_schema["additionalProperties"] is False
        assert "root" not in spec.input_schema["properties"]
