"""Unit tests for Source Artifact registry primitives."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from codememory.sources import (
    SourceArtifact,
    add_source_artifact,
    check_source_artifact,
    compute_file_sha256,
    get_source_artifact,
    get_sources_index_path,
    list_source_artifacts,
    load_source_registry,
    save_source_registry,
)
from codememory.handlers import (
    handle_source_add,
    handle_source_check,
    handle_source_get,
    handle_source_list,
)


def test_source_artifact_serializes_with_defaults():
    from codememory import SourceArtifact as PublicSourceArtifact

    assert PublicSourceArtifact is SourceArtifact

    artifact = SourceArtifact(
        id="src/design-md",
        kind="markdown",
        uri="docs/design.md",
        sha256="abc123",
        summary="Design document",
    )

    data = artifact.model_dump(mode="json")

    assert data["id"] == "src/design-md"
    assert data["kind"] == "markdown"
    assert data["uri"] == "docs/design.md"
    assert data["sha256"] == "abc123"
    assert data["summary"] == "Design document"
    assert data["status"] == "active"


def test_missing_source_registry_loads_empty(tmp_path: Path):
    registry = load_source_registry(tmp_path)

    assert get_sources_index_path(tmp_path) == tmp_path / ".codememory" / "sources" / "index.json"
    assert registry.sources == {}


def test_add_list_get_save_and_reload_source_artifact(tmp_path: Path):
    source_file = tmp_path / "docs" / "design.md"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("# Design\n\nStable source text.", encoding="utf-8")

    artifact = add_source_artifact(
        tmp_path,
        uri="docs/design.md",
        source_id="src/design-md",
        kind="markdown",
        summary="Design source",
    )

    assert artifact.id == "src/design-md"
    assert artifact.sha256 == compute_file_sha256(source_file)
    assert get_source_artifact(tmp_path, "src/design-md") == artifact
    assert [a.id for a in list_source_artifacts(tmp_path)] == ["src/design-md"]

    reloaded = load_source_registry(tmp_path)
    assert reloaded.sources["src/design-md"].summary == "Design source"

    save_source_registry(tmp_path, reloaded)
    assert get_sources_index_path(tmp_path).exists()


def test_check_source_artifact_detects_fresh_missing_and_stale(tmp_path: Path):
    source_file = tmp_path / "docs" / "design.md"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("version one", encoding="utf-8")
    artifact = add_source_artifact(
        tmp_path,
        uri="docs/design.md",
        source_id="src/design-md",
        kind="markdown",
        summary="Design source",
    )

    fresh = check_source_artifact(tmp_path, artifact)
    assert fresh.state == "fresh"

    source_file.write_text("version two", encoding="utf-8")
    stale = check_source_artifact(tmp_path, artifact)
    assert stale.state == "stale"
    assert stale.current_sha256 == compute_file_sha256(source_file)

    source_file.unlink()
    missing = check_source_artifact(tmp_path, artifact)
    assert missing.state == "missing"


def test_source_handlers_expose_registry_primitives(tmp_path: Path):
    source_file = tmp_path / "docs" / "design.md"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("handler source", encoding="utf-8")

    added = handle_source_add(
        tmp_path,
        uri="docs/design.md",
        source_id="src/design-md",
        kind="markdown",
        summary="Design source",
    )
    listed = handle_source_list(tmp_path)
    fetched = handle_source_get(tmp_path, "src/design-md")
    checked = handle_source_check(tmp_path, "src/design-md")

    assert "source added: src/design-md" in added
    assert "src/design-md" in listed
    assert '"id": "src/design-md"' in fetched
    assert "src/design-md" in checked
    assert "fresh" in checked
