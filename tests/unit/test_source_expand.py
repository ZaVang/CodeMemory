"""Unit tests for explicit Source Artifact expansion."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from codememory.handlers import handle_source_expand
from codememory.sources import (
    SourceExpansion,
    add_source_artifact,
    compute_file_sha256,
    expand_source_artifact,
)


def test_source_expansion_model_serializes_structured_notice():
    expansion = SourceExpansion(
        artifact_id="src/missing",
        status="missing",
        message="Source Artifact 'src/missing' not found.",
    )

    data = expansion.model_dump(mode="json")

    assert data["artifact_id"] == "src/missing"
    assert data["status"] == "missing"
    assert data["content"] == ""
    assert data["message"] == "Source Artifact 'src/missing' not found."


def test_expand_source_returns_full_local_text_with_provenance(tmp_path: Path):
    source_file = tmp_path / "docs" / "design.md"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("# Design\n\nStable source text.", encoding="utf-8")
    add_source_artifact(
        tmp_path,
        uri="docs/design.md",
        source_id="src/design-md",
        kind="markdown",
        summary="Design source",
    )

    expansion = expand_source_artifact(tmp_path, "src/design-md")

    assert expansion.artifact_id == "src/design-md"
    assert expansion.kind == "markdown"
    assert expansion.uri == "docs/design.md"
    assert expansion.path == "docs/design.md"
    assert expansion.sha256 == compute_file_sha256(source_file)
    assert expansion.current_sha256 == compute_file_sha256(source_file)
    assert expansion.status == "fresh"
    assert expansion.content == "# Design\n\nStable source text."
    assert expansion.range_start == 0
    assert expansion.range_end == len(expansion.content)
    assert expansion.truncated is False


def test_expand_source_returns_requested_character_range(tmp_path: Path):
    source_file = tmp_path / "docs" / "design.md"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("alpha beta gamma", encoding="utf-8")
    add_source_artifact(tmp_path, uri="docs/design.md", source_id="src/design-md", kind="markdown")

    expansion = expand_source_artifact(tmp_path, "src/design-md", start=6, end=10)

    assert expansion.status == "fresh"
    assert expansion.content == "beta"
    assert expansion.range_start == 6
    assert expansion.range_end == 10
    assert expansion.truncated is True


def test_expand_source_respects_max_chars(tmp_path: Path):
    source_file = tmp_path / "docs" / "design.md"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("0123456789", encoding="utf-8")
    add_source_artifact(tmp_path, uri="docs/design.md", source_id="src/design-md", kind="text")

    expansion = expand_source_artifact(tmp_path, "src/design-md", max_chars=4)

    assert expansion.content == "0123"
    assert expansion.range_start == 0
    assert expansion.range_end == 4
    assert expansion.truncated is True


def test_expand_source_reports_missing_file_and_stale_hash(tmp_path: Path):
    source_file = tmp_path / "docs" / "design.md"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("version one", encoding="utf-8")
    add_source_artifact(tmp_path, uri="docs/design.md", source_id="src/design-md", kind="markdown")

    source_file.write_text("version two", encoding="utf-8")
    stale = expand_source_artifact(tmp_path, "src/design-md")
    assert stale.status == "stale"
    assert stale.current_sha256 == compute_file_sha256(source_file)
    assert stale.content == "version two"
    assert "hash differs" in stale.message

    source_file.unlink()
    missing = expand_source_artifact(tmp_path, "src/design-md")
    assert missing.status == "missing"
    assert missing.content == ""
    assert "not found" in missing.message


def test_expand_source_reports_missing_artifact_and_unsupported_external(tmp_path: Path):
    missing = expand_source_artifact(tmp_path, "src/not-registered")
    assert missing.status == "missing"
    assert missing.artifact_id == "src/not-registered"
    assert "not found" in missing.message

    add_source_artifact(
        tmp_path,
        uri="https://example.com/design",
        source_id="src/external",
        kind="url",
        summary="External source",
    )

    unsupported = expand_source_artifact(tmp_path, "src/external")
    assert unsupported.status == "unsupported"
    assert unsupported.uri == "https://example.com/design"
    assert unsupported.content == ""


def test_source_expand_handler_returns_machine_readable_json(tmp_path: Path):
    source_file = tmp_path / "docs" / "design.md"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("handler source text", encoding="utf-8")
    add_source_artifact(tmp_path, uri="docs/design.md", source_id="src/design-md", kind="markdown")

    result = handle_source_expand(tmp_path, "src/design-md", start=8, end=14)
    data = json.loads(result)

    assert data["artifact_id"] == "src/design-md"
    assert data["status"] == "fresh"
    assert data["content"] == "source"
