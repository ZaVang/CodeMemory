from __future__ import annotations

import json
import os
import subprocess
import sys
import types
from pathlib import Path

import pytest
import yaml

from codememory.build import build_context_pack
from codememory.capture import append_capture
from codememory.handlers import handle_search, handle_semantic_index, handle_semantic_status
from codememory.agent_tools import tool_specs_for_root
from codememory.index import reindex
from codememory.profile import PersonalProfile, init_personal_profile, validate_personal_profile
from codememory.semantic_local import LocalSentenceTransformerEmbedder
from codememory.semantic_index import (
    build_semantic_index,
    semantic_index_path,
    semantic_search,
    semantic_status,
)


TOPIC = """# 2026-07 Incubator

## Career direction
<!-- codememory:topic
topic_id: topic/career
revision_id: topic/career@2026-07
created_at: 2026-07-23T10:00:00+08:00
updated_at: 2026-07-23T10:00:00+08:00
origin: mixed
tags: [career]
derived_from: []
relations: []
-->

The owner prefers deep technical work.

### Claim: leadership path
<!-- codememory:claim
claim_id: claim/career/leadership
origin: agent_inference
claim_status: unassessed
derived_from: []
-->

A staff engineer path may fit.
"""


class FakeEmbedder:
    model_id = "fake-local-v1"
    fingerprint = "fingerprint-v1"

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        vectors = []
        for text in texts:
            lower = text.lower()
            vectors.append([
                2.0 if "career" in lower or "technical" in lower or "staff engineer" in lower else 0.1,
                2.0 if "coffee" in lower else 0.1,
            ])
        return vectors


def _enable(root: Path, *, model_path: str = "private-local/models/fake") -> None:
    path = root / ".codememory" / "profile.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw["discovery"]["semantic"] = {
        "enabled": True,
        "external_embeddings": False,
        "provider": "local",
        "model_path": model_path,
        "model_id": "fake-local-v1",
    }
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    (root / model_path).mkdir(parents=True, exist_ok=True)


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "memory"
    init_personal_profile(root)
    _enable(root)
    append_capture(root, "I want a deeper technical career path")
    append_capture(root, "Morning coffee ritual")
    (root / "incubator" / "2026-07.md").write_text(TOPIC, encoding="utf-8")
    active = root / "memory" / "career-context.md"
    active.write_text(
        "---\ntype: atom\nid: memory/career-context\nsummary: Career context\n"
        "status: active\nversion: 1\ntags: [career]\n---\n\nTechnical leadership options.\n",
        encoding="utf-8",
    )
    proposed = root / "memory" / "proposed.md"
    proposed.write_text(
        "---\ntype: atom\nid: memory/proposed\nsummary: Proposed secret\n"
        "status: proposed\nversion: 1\n---\n\nPROPOSED-SEMANTIC-SECRET\n",
        encoding="utf-8",
    )
    reindex(root)
    return root


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


def test_default_disabled_and_profile_path_boundary(tmp_path: Path):
    root = tmp_path / "memory"
    init_personal_profile(root)
    status = semantic_status(root)
    assert not status.enabled
    assert not semantic_index_path(root).exists()

    with pytest.raises(Exception, match="model_path"):
        PersonalProfile.model_validate({
            "discovery": {"semantic": {
                "enabled": True, "model_path": "../model", "model_id": "x",
            }}
        })
    with pytest.raises(Exception, match="model_path"):
        PersonalProfile.model_validate({
            "discovery": {"semantic": {
                "enabled": True, "model_path": str((tmp_path / "model").resolve()), "model_id": "x",
            }}
        })
    with pytest.raises(Exception, match="private_local"):
        PersonalProfile.model_validate({
            "discovery": {"semantic": {
                "enabled": True, "model_path": "models/x", "model_id": "x",
            }}
        })
    with pytest.raises(Exception, match="external embeddings"):
        PersonalProfile.model_validate({
            "discovery": {"semantic": {"external_embeddings": True}}
        })


def test_build_indexes_typed_valid_objects_and_reuses_identical_input(tmp_path: Path):
    root = _root(tmp_path)
    embedder = FakeEmbedder()

    first = build_semantic_index(root, embedder)
    path = semantic_index_path(root)
    before = path.read_bytes()
    second = build_semantic_index(root, embedder)
    payload = json.loads(path.read_text(encoding="utf-8"))
    keys = {record["key"] for record in payload["records"]}

    assert first.status == "built"
    assert second.status == "reused"
    assert len(embedder.calls) == 1
    assert path.read_bytes() == before
    assert "atom:memory/career-context" in keys
    assert "atom:memory/proposed" not in keys
    assert any(key.startswith("capture:") for key in keys)
    assert "incubator_topic:topic/career@2026-07" in keys
    assert "incubator_claim:claim/career/leadership" in keys
    text = path.read_text(encoding="utf-8")
    assert str(root) not in text
    assert "PROPOSED-SEMANTIC-SECRET" not in text
    assert path.is_relative_to(root / "private-local")


def test_corrupt_capture_is_excluded_from_semantic_index(tmp_path: Path):
    root = _root(tmp_path)
    journal = next((root / "journal").rglob("*.md"))
    text = journal.read_text(encoding="utf-8")
    journal.write_text(
        text.replace(
            "I want a deeper technical career path",
            "I want a TAMPERED technical career path",
        ),
        encoding="utf-8",
    )
    reindex(root)

    build_semantic_index(root, FakeEmbedder())
    payload = json.loads(semantic_index_path(root).read_text(encoding="utf-8"))

    assert all("TAMPERED" not in record["snippet"] for record in payload["records"])
    assert sum(record["kind"] == "capture" for record in payload["records"]) == 1


def test_semantic_search_orders_typed_candidates_and_filters_kinds(tmp_path: Path):
    root = _root(tmp_path)
    embedder = FakeEmbedder()
    build_semantic_index(root, embedder)
    path = semantic_index_path(root)
    before = path.read_bytes()

    query = "career query must never be persisted"
    results = semantic_search(root, query, embedder, limit=20)
    assert results[0].score >= results[-1].score
    assert {item.read_action for item in results} == {"read", "build"}
    captures = semantic_search(root, "career", embedder, kinds=["capture"])
    assert captures and all(item.kind == "capture" for item in captures)

    formatted = handle_search(
        root, query="career", semantic=True,
        semantic_limit=3, semantic_embedder=embedder,
    )
    assert "score:" in formatted
    assert "-> read" in formatted or "-> build" in formatted
    assert path.read_bytes() == before
    assert query not in path.read_text(encoding="utf-8")


def test_changed_content_and_model_are_stale_until_rebuild(tmp_path: Path):
    root = _root(tmp_path)
    embedder = FakeEmbedder()
    build_semantic_index(root, embedder)
    append_capture(root, "A newly captured career constraint")
    reindex(root)

    assert semantic_status(root).index_status == "stale"
    with pytest.raises(ValueError, match="content is stale"):
        semantic_search(root, "career", embedder)

    other = FakeEmbedder()
    other.fingerprint = "different"
    with pytest.raises(ValueError, match="model is stale"):
        semantic_search(root, "career", other)


def test_enabled_query_requires_explicit_index_and_existing_model_directory(tmp_path: Path):
    root = tmp_path / "memory"
    init_personal_profile(root)
    _enable(root)
    embedder = FakeEmbedder()

    with pytest.raises(ValueError, match="index is missing"):
        semantic_search(root, "career", embedder)

    model_path = root / "private-local/models/fake"
    model_path.rmdir()
    validation = validate_personal_profile(root)
    assert not validation.profile_valid
    assert any("model directory missing" in error for error in validation.errors)


def test_dimension_mismatch_and_failed_build_do_not_replace_index(tmp_path: Path):
    root = _root(tmp_path)
    embedder = FakeEmbedder()
    build_semantic_index(root, embedder)
    path = semantic_index_path(root)
    before = path.read_bytes()

    class Broken(FakeEmbedder):
        fingerprint = "broken"

        def embed(self, texts: list[str]) -> list[list[float]]:
            return [[1.0], [1.0, 2.0]]

    with pytest.raises(ValueError):
        build_semantic_index(root, Broken())
    assert path.read_bytes() == before

    payload = json.loads(before)
    payload["records"][0]["vector"] = [1.0]
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="record dimension mismatch"):
        semantic_search(root, "career", embedder)


def test_semantic_neighbors_never_affect_canonical_build(tmp_path: Path):
    root = _root(tmp_path)
    embedder = FakeEmbedder()
    build_semantic_index(root, embedder)
    before = build_context_pack(root, "memory/career-context", track_access=False)

    path = semantic_index_path(root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["records"].append({
        "key": "atom:memory/injected", "kind": "atom", "id": "memory/injected",
        "summary": "Injected", "snippet": "INJECTED", "path": "memory/injected.md",
        "display_locator": "memory/injected.md", "read_action": "build",
        "content_sha256": "x", "vector": [1.0, 0.0],
    })
    path.write_text(json.dumps(payload), encoding="utf-8")
    after = build_context_pack(root, "memory/career-context", track_access=False)

    assert [node.id for node in before.nodes] == [node.id for node in after.nodes]
    assert "memory/injected" not in [node.id for node in after.nodes]


def test_disabled_search_and_lazy_dependency_boundary(tmp_path: Path):
    root = tmp_path / "memory"
    init_personal_profile(root)
    with pytest.raises(ValueError, match="not configured"):
        handle_search(root, query="career", semantic=True)

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, codememory; "
            "assert 'sentence_transformers' not in sys.modules; "
            "print('semantic import boundary ok')",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "semantic import boundary ok" in result.stdout


def test_agent_catalog_only_advertises_semantic_for_configured_personal_root(tmp_path: Path):
    standard = tmp_path / "standard"
    standard.mkdir()
    personal = tmp_path / "personal"
    init_personal_profile(personal)

    def search_properties(root: Path) -> dict:
        spec = next(item for item in tool_specs_for_root(root) if item.name == "search_memories")
        return spec.input_schema["properties"]

    assert "semantic" not in search_properties(standard)
    assert "semantic" not in search_properties(personal)
    _enable(personal)
    assert "semantic" in search_properties(personal)


def test_local_adapter_forces_offline_model_loading(tmp_path: Path, monkeypatch):
    model_path = tmp_path / "model"
    model_path.mkdir()
    (model_path / "config.json").write_text("{}", encoding="utf-8")
    seen: dict = {}

    class FakeSentenceTransformer:
        def __init__(self, path: str, **kwargs):
            seen["path"] = path
            seen["kwargs"] = kwargs

        def encode(self, texts, **kwargs):
            seen["encode_kwargs"] = kwargs
            return [[1.0, 2.0] for _ in texts]

    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        types.SimpleNamespace(SentenceTransformer=FakeSentenceTransformer),
    )
    embedder = LocalSentenceTransformerEmbedder(model_path, "local-test")

    assert seen["path"] == str(model_path.resolve())
    assert seen["kwargs"] == {
        "local_files_only": True,
        "trust_remote_code": False,
    }
    assert embedder.embed(["one"]) == [[1.0, 2.0]]


def test_enabled_profile_validates_model_inside_private_local(tmp_path: Path):
    root = _root(tmp_path)
    result = validate_personal_profile(root)
    assert result.profile_valid


def test_private_local_junction_cannot_escape_bound_root(tmp_path: Path):
    root = tmp_path / "memory"
    outside = tmp_path / "outside-private"
    outside.mkdir()
    init_personal_profile(root)
    private_local = root / "private-local"
    private_local.rmdir()
    _directory_link(private_local, outside)
    try:
        _enable(root)
        embedder = FakeEmbedder()

        validation = validate_personal_profile(root)
        assert not validation.profile_valid
        assert any("outside bound root" in error for error in validation.errors)

        with pytest.raises(ValueError, match="outside bound root"):
            semantic_index_path(root)
        with pytest.raises(ValueError, match="outside bound root"):
            semantic_status(root)
        with pytest.raises(ValueError, match="outside bound root"):
            build_semantic_index(root, embedder)
        with pytest.raises(ValueError, match="outside bound root"):
            semantic_search(root, "career", embedder)
        with pytest.raises(ValueError, match="outside bound root"):
            handle_search(
                root,
                query="career",
                semantic=True,
                semantic_embedder=embedder,
            )
        with pytest.raises(ValueError, match="outside bound root"):
            handle_semantic_status(root)
        with pytest.raises(ValueError, match="outside bound root"):
            handle_semantic_index(root)

        assert embedder.calls == []
        assert not (outside / "semantic" / "index.json").exists()
    finally:
        os.rmdir(private_local)
