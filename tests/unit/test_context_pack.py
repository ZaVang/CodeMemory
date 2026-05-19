"""Unit tests for structured ContextPack generation and rendering."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from codememory.context_pack import build_context_pack, render_context_pack
from codememory.core import compute_body_hash
from codememory.index import save_index
from codememory.models import IndexData, MemoryEntry
from codememory.sources import add_source_artifact


def _write_memory(
    root: Path,
    memory_id: str,
    *,
    summary: str,
    body: str,
    imports: dict[str, list[str]] | None = None,
    maturity: str = "draft",
    source_refs: list[dict[str, str]] | None = None,
) -> MemoryEntry:
    path = root / f"{memory_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    imports_yaml = ""
    if imports:
        imports_yaml = "imports:\n"
        for strength, ids in imports.items():
            imports_yaml += f"  {strength}:\n"
            for dep_id in ids:
                imports_yaml += f"    - {dep_id}\n"
    source_refs_yaml = ""
    if source_refs:
        source_refs_yaml = "source_refs:\n"
        for ref in source_refs:
            source_refs_yaml += f"  - artifact_id: {ref['artifact_id']}\n"
            if ref.get("summary"):
                source_refs_yaml += f"    summary: {ref['summary']}\n"
            if ref.get("disclosure_hint"):
                source_refs_yaml += f"    disclosure_hint: {ref['disclosure_hint']}\n"
    path.write_text(
        "\n".join([
            "---",
            "type: atom",
            f"id: {memory_id}",
            f"summary: {summary}",
            f"maturity: {maturity}",
            "tags: [agent, workflow]",
            f"summary_hash: {compute_body_hash(body)}",
            imports_yaml.rstrip(),
            source_refs_yaml.rstrip(),
            "---",
            body,
        ]),
        encoding="utf-8",
    )
    return MemoryEntry(
        type="atom",
        id=memory_id,
        summary=summary,
        path=f"{memory_id}.md",
        imports=imports or {},
        maturity=maturity,
        tags=["agent", "workflow"],
        summary_hash=compute_body_hash(body),
        source_refs=source_refs or [],
    )


def test_context_pack_preserves_structured_nodes_and_xml_markdown(tmp_path: Path):
    idx = IndexData()
    idx.memories["user/project/fact"] = _write_memory(
        tmp_path,
        "user/project/fact",
        summary="A durable project fact",
        body="Fact body with **markdown**.",
        maturity="verified",
    )
    idx.memories["user/project/context"] = _write_memory(
        tmp_path,
        "user/project/context",
        summary="Current project context",
        body="Context body.",
        imports={"required": ["user/project/fact"]},
    )
    save_index(tmp_path, idx)

    pack = build_context_pack(
        tmp_path,
        "user/project/context",
        depth="recommended",
        budget=10_000,
        task_goal="Use this to brief an agent.",
        track_access=False,
    )

    assert pack.target_id == "user/project/context"
    assert pack.task_goal == "Use this to brief an agent."
    assert [node.id for node in pack.nodes] == ["user/project/fact", "user/project/context"]
    assert pack.nodes[0].dependency_role == "required"
    assert pack.nodes[0].trim == "full"
    assert pack.nodes[0].content == "Fact body with **markdown**."
    assert pack.nodes[1].dependency_role == "target"

    rendered = render_context_pack(pack, "xml-markdown")
    assert rendered.startswith("<codememory_context_pack")
    assert 'target_id="user/project/context"' in rendered
    assert "<task_goal>Use this to brief an agent.</task_goal>" in rendered
    assert '<memory id="user/project/fact" trim="full"' in rendered
    assert "<![CDATA[\nFact body with **markdown**.\n]]>" in rendered


def test_context_pack_json_renderer_is_machine_readable(tmp_path: Path):
    idx = IndexData()
    idx.memories["user/project/context"] = _write_memory(
        tmp_path,
        "user/project/context",
        summary="Current project context",
        body="Context body.",
    )
    save_index(tmp_path, idx)

    pack = build_context_pack(tmp_path, "user/project/context", budget=10_000, track_access=False)
    rendered = render_context_pack(pack, "json")
    data = json.loads(rendered)

    assert data["target_id"] == "user/project/context"
    assert data["nodes"][0]["summary"] == "Current project context"


def test_context_pack_renders_source_refs_without_expanding_source(tmp_path: Path):
    source_file = tmp_path / "docs" / "design.md"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("FULL SOURCE TEXT SHOULD NOT RENDER", encoding="utf-8")
    add_source_artifact(
        tmp_path,
        uri="docs/design.md",
        source_id="src/design-md",
        kind="markdown",
        summary="Design source",
    )

    idx = IndexData()
    idx.memories["user/project/context"] = _write_memory(
        tmp_path,
        "user/project/context",
        summary="Current project context",
        body="Context body.",
        source_refs=[
            {
                "artifact_id": "src/design-md",
                "summary": "Design source",
                "disclosure_hint": "anchor",
            },
        ],
    )
    save_index(tmp_path, idx)

    pack = build_context_pack(tmp_path, "user/project/context", budget=10_000, track_access=False)

    assert pack.nodes[0].source_refs[0].artifact_id == "src/design-md"

    rendered_json = json.loads(render_context_pack(pack, "json"))
    assert rendered_json["nodes"][0]["source_refs"][0]["artifact_id"] == "src/design-md"

    rendered_xml = render_context_pack(pack, "xml-markdown")
    assert '<source_ref artifact_id="src/design-md"' in rendered_xml
    assert "Design source" in rendered_xml
    assert "FULL SOURCE TEXT SHOULD NOT RENDER" not in rendered_xml

    rendered_md = render_context_pack(pack, "markdown")
    assert "- Source refs:" in rendered_md
    assert "`src/design-md`" in rendered_md
    assert "FULL SOURCE TEXT SHOULD NOT RENDER" not in rendered_md
