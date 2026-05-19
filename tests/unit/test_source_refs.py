"""Unit tests for atom-to-source artifact references."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from codememory.core import compute_body_hash
from codememory.index import load_index, reindex
from codememory.models import MemoryEntry, SourceRef
from codememory.sources import add_source_artifact
from codememory.validate import validate


def test_source_ref_model_accepts_frontmatter_shape():
    ref = SourceRef(
        artifact_id="src/design-md",
        section_id="overview",
        summary="Design overview",
        disclosure_hint="anchor",
    )

    assert ref.artifact_id == "src/design-md"
    assert ref.section_id == "overview"
    assert ref.summary == "Design overview"
    assert ref.disclosure_hint == "anchor"


def test_memory_entry_carries_source_refs():
    entry = MemoryEntry(
        id="user/project/context",
        summary="Context",
        source_refs=[
            {"artifact_id": "src/design-md", "summary": "Design source"},
        ],
    )

    assert entry.source_refs[0].artifact_id == "src/design-md"


def test_reindex_preserves_source_refs_from_frontmatter(tmp_path: Path):
    body = "Context body."
    memory_path = tmp_path / "user" / "project" / "context.md"
    memory_path.parent.mkdir(parents=True)
    memory_path.write_text(
        "\n".join([
            "---",
            "type: atom",
            "id: user/project/context",
            "summary: Context",
            "intensity: 8",
            f"summary_hash: {compute_body_hash(body)}",
            "source_refs:",
            "  - artifact_id: src/design-md",
            "    summary: Design source",
            "    disclosure_hint: anchor",
            "---",
            body,
        ]),
        encoding="utf-8",
    )

    reindex(tmp_path)
    index = load_index(tmp_path)

    entry = index.memories["user/project/context"]
    assert entry.source_refs[0].artifact_id == "src/design-md"
    assert entry.source_refs[0].summary == "Design source"


def test_validate_reports_missing_source_ref_without_import_error(tmp_path: Path):
    body = "Context body."
    memory_path = tmp_path / "user" / "project" / "context.md"
    memory_path.parent.mkdir(parents=True)
    memory_path.write_text(
        "\n".join([
            "---",
            "type: atom",
            "id: user/project/context",
            "summary: Context",
            "intensity: 8",
            f"summary_hash: {compute_body_hash(body)}",
            "source_refs:",
            "  - artifact_id: src/missing-md",
            "    summary: Missing source",
            "---",
            body,
        ]),
        encoding="utf-8",
    )
    reindex(tmp_path)

    errors, warnings = validate(tmp_path)

    assert errors == 0
    assert warnings == 1


def test_validate_accepts_existing_source_ref(tmp_path: Path):
    source_file = tmp_path / "docs" / "design.md"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("Design source", encoding="utf-8")
    add_source_artifact(
        tmp_path,
        uri="docs/design.md",
        source_id="src/design-md",
        kind="markdown",
        summary="Design source",
    )

    body = "Context body."
    memory_path = tmp_path / "user" / "project" / "context.md"
    memory_path.parent.mkdir(parents=True)
    memory_path.write_text(
        "\n".join([
            "---",
            "type: atom",
            "id: user/project/context",
            "summary: Context",
            "intensity: 8",
            f"summary_hash: {compute_body_hash(body)}",
            "source_refs:",
            "  - artifact_id: src/design-md",
            "    summary: Design source",
            "---",
            body,
        ]),
        encoding="utf-8",
    )
    reindex(tmp_path)

    errors, warnings = validate(tmp_path)

    assert errors == 0
    assert warnings == 0
