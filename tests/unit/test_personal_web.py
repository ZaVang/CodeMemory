from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
import yaml
from fastapi.testclient import TestClient

_BACKEND = Path(__file__).resolve().parents[2] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from backend.server import app, lifespan  # noqa: E402
import backend.server as backend_server  # noqa: E402
import routers.personal as personal_router  # noqa: E402
import shared as backend_shared  # noqa: E402
from codememory.capture import append_capture, capture_content_hash  # noqa: E402
from codememory.personal_web import (  # noqa: E402
    get_personal_captures,
    get_personal_overview,
    get_personal_timeline,
    get_personal_topics,
)
from codememory.profile import init_personal_profile  # noqa: E402


ZONE = ZoneInfo("Asia/Hong_Kong")


def _personal(root: Path) -> Path:
    result = init_personal_profile(root)
    assert result.profile_valid
    return root


def _topic(root: Path, capture_id: str, capture_hash: str) -> None:
    root.joinpath("incubator/2026-07.md").write_text(
        f"""# 2026-07 Incubator

## Durable decisions
<!-- codememory:topic
topic_id: topic/durable-decisions
revision_id: rev/durable-decisions/2026-07
created_at: 2026-07-20T09:00:00+08:00
updated_at: 2026-07-21T10:00:00+08:00
origin: mixed
content_hash: sha256:topic
derived_from:
  - kind: capture
    id: {capture_id}
    content_hash: {capture_hash}
    private_path: C:/outside/private-local
relations:
  - relation: evolves_from
    target_id: rev/durable-decisions/2026-06
    registry_path: C:/outside/instances.yaml
merged_from: []
-->

The stable synthesis.

### Claim: explicit imports remain canonical
<!-- codememory:claim
claim_id: claim/durable-decisions/imports
origin: agent_inference
claim_status: supported
confidence: 0.8
derived_from:
  - kind: capture
    id: {capture_id}
    content_hash: {capture_hash}
-->

An independently reviewable inference.
""",
        encoding="utf-8",
    )


def _registry(tmp_path: Path, root: Path, alias: str = "mymemory") -> Path:
    path = tmp_path / "instances.yaml"
    path.write_text(
        yaml.safe_dump({"instances": {alias: str(root.resolve())}}, sort_keys=False),
        encoding="utf-8",
    )
    return path


def test_personal_read_models_filter_invalid_capture_and_keep_stable_objects(tmp_path: Path) -> None:
    root = _personal(tmp_path / "memory")
    first = append_capture(root, "first note", now=datetime(2026, 7, 20, 8, tzinfo=ZONE))
    second = append_capture(root, "second note", now=datetime(2026, 7, 21, 8, tzinfo=ZONE))
    _topic(root, first.id, first.content_hash)

    journal = root / "journal/2026/07/2026-07-22.md"
    journal.write_text(
        "# 2026-07-22\n\n"
        + "## 10:00 — cap_01K0R8Y7M0M8QW8R1J4Y4S0F4M\n"
        + "<!-- codememory:capture\n"
        + "id: cap_01K0R8Y7M0M8QW8R1J4Y4S0F4M\n"
        + "captured_at: 2026-07-22T10:00:00+08:00\n"
        + "actor: owner\n"
        + f"content_hash: {capture_content_hash('untampered')}\n"
        + "-->\ntampered\n",
        encoding="utf-8",
    )

    page = get_personal_captures(root, offset=0, limit=1)
    assert page.total == 2
    assert [item.id for item in page.items] == [second.id]
    assert not any(Path(item.locator).is_absolute() for item in page.items)

    topics = get_personal_topics(root)
    assert len(topics) == 1
    assert topics[0].topic_id == "topic/durable-decisions"
    assert topics[0].claims[0].claim_id == "claim/durable-decisions/imports"
    assert topics[0].claims[0].claim_status == "supported"
    assert "C:/outside" not in json.dumps(
        [item.model_dump(mode="json") for item in topics],
    )

    overview = get_personal_overview(root)
    assert overview.capture_count == 2
    assert overview.topic_count == 1
    assert overview.claim_count == 1
    assert overview.diagnostics_count >= 1


def test_timeline_uses_only_explicit_provenance_and_timestamps(tmp_path: Path) -> None:
    root = _personal(tmp_path / "memory")
    capture = append_capture(root, "source note", now=datetime(2026, 7, 20, 8, tzinfo=ZONE))
    unrelated = append_capture(
        root,
        "same words but no provenance",
        now=datetime(2026, 7, 20, 9, tzinfo=ZONE),
    )
    _topic(root, capture.id, capture.content_hash)

    atom = root / "memory/ideas/promoted.md"
    atom.parent.mkdir(parents=True)
    atom.write_text(
        """---
type: atom
id: memory/ideas/promoted
summary: Promoted idea
status: active
created: 2026-07-22
updated: 2026-07-22
provenance:
  topic_revision_id: rev/durable-decisions/2026-07
---
# Promoted
""",
        encoding="utf-8",
    )

    timeline = get_personal_timeline(root, topic_id="topic/durable-decisions")
    event_ids = {item.id for item in timeline.events}
    assert capture.id in event_ids
    assert unrelated.id not in event_ids
    assert "rev/durable-decisions/2026-07" in event_ids
    assert "promotion:memory/ideas/promoted" in event_ids
    edges = {(item.relation, item.source_id, item.target_id) for item in timeline.edges}
    assert ("derived_from", capture.id, "rev/durable-decisions/2026-07") in edges
    assert (
        "promoted_to",
        "rev/durable-decisions/2026-07",
        "promotion:memory/ideas/promoted",
    ) in edges
    assert ("evolves_from", "rev/durable-decisions/2026-07", "rev/durable-decisions/2026-06") in edges


@pytest.mark.parametrize(
    "alias",
    ["../escape", r"..\escape", "C:escape", " spaced", "spaced ", "a/b", "a..b"],
)
def test_registry_rejects_unsafe_aliases(tmp_path: Path, monkeypatch, alias: str) -> None:
    root = _personal(tmp_path / "memory")
    monkeypatch.setenv("CODEMEMORY_INSTANCE_REGISTRY", str(_registry(tmp_path, root, alias)))
    with pytest.raises(ValueError, match="alias"):
        backend_shared.get_dataset_records()


def test_registry_exposes_safe_metadata_and_resolves_exact_alias(tmp_path: Path, monkeypatch) -> None:
    root = _personal(tmp_path / "memory")
    registry = _registry(tmp_path, root)
    monkeypatch.setenv("CODEMEMORY_INSTANCE_REGISTRY", str(registry))

    record = next(item for item in backend_shared.get_dataset_records() if item.name == "mymemory")
    assert record.root == root.resolve()
    assert backend_shared.resolve_root("mymemory") == root.resolve()
    public = next(item for item in backend_shared.get_available_datasets() if item["name"] == "mymemory")
    assert public == {
        "name": "mymemory",
        "memory_count": 0,
        "profile": "personal",
        "source": "registry",
    }
    assert str(root) not in json.dumps(public)
    assert "path" not in public


def test_registry_alias_cannot_collide_with_demo_dataset(tmp_path: Path, monkeypatch) -> None:
    root = _personal(tmp_path / "memory")
    monkeypatch.setenv(
        "CODEMEMORY_INSTANCE_REGISTRY",
        str(_registry(tmp_path, root, alias="companion")),
    )
    with pytest.raises(ValueError, match="Duplicate dataset alias"):
        backend_shared.get_dataset_records()


@pytest.mark.parametrize("kind", ["relative", "missing", "standard", "invalid"])
def test_registry_fails_closed_for_invalid_roots(
    tmp_path: Path,
    monkeypatch,
    kind: str,
) -> None:
    if kind == "relative":
        value = "relative/root"
    elif kind == "missing":
        value = str((tmp_path / "missing").resolve())
    elif kind == "standard":
        target = tmp_path / "standard"
        target.mkdir()
        value = str(target.resolve())
    else:
        target = _personal(tmp_path / "invalid")
        (target / ".gitignore").write_text("", encoding="utf-8")
        value = str(target.resolve())
    registry = tmp_path / "instances.yaml"
    registry.write_text(yaml.safe_dump({"instances": {"bad": value}}), encoding="utf-8")
    monkeypatch.setenv("CODEMEMORY_INSTANCE_REGISTRY", str(registry.resolve()))
    with pytest.raises(ValueError):
        backend_shared.get_dataset_records()


@pytest.mark.asyncio
async def test_startup_does_not_reindex_external_registry_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = _personal(tmp_path / "memory")
    monkeypatch.setenv("CODEMEMORY_INSTANCE_REGISTRY", str(_registry(tmp_path, root)))
    calls: list[Path] = []
    monkeypatch.setattr(backend_server, "_cm_reindex", lambda value: calls.append(value.resolve()))
    async with lifespan(app):
        pass
    assert root.resolve() not in calls


def test_personal_api_rejects_standard_and_delegates_one_confirmed_batch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = _personal(tmp_path / "memory")
    capture = append_capture(root, "review source", now=datetime(2026, 7, 20, 8, tzinfo=ZONE))
    _topic(root, capture.id, capture.content_hash)
    monkeypatch.setenv("CODEMEMORY_INSTANCE_REGISTRY", str(_registry(tmp_path, root)))
    client = TestClient(app)
    headers = {"X-Codememory-Dataset": "mymemory"}

    assert client.get("/api/personal/overview", headers=headers).status_code == 200
    assert client.get("/api/personal/topics", headers=headers).json()[0]["claims"][0]["claim_id"]
    assert client.get(
        "/api/personal/timeline",
        headers=headers,
        params={"topic_id": "topic/durable-decisions"},
    ).status_code == 200
    assert client.get(
        "/api/personal/overview",
        headers={"X-Codememory-Dataset": "companion"},
    ).status_code == 409

    calls: list[tuple[Path, list[dict]]] = []

    def fake_batch(bound_root: Path, decisions: list[dict]) -> str:
        calls.append((bound_root, decisions))
        return json.dumps({"promoted": ["memory/ideas/durable"], "merged": [], "deleted": []})

    monkeypatch.setattr(personal_router, "handle_review_batch", fake_batch)
    response = client.post(
        "/api/personal/review-batch",
        headers=headers,
        json={
            "owner_confirmed": True,
            "decisions": [{
                "action": "promote",
                "revision_id": "rev/durable-decisions/2026-07",
                "atom_id": "memory/ideas/durable",
            }],
        },
    )
    assert response.status_code == 200
    assert len(calls) == 1
    assert calls[0][0] == root.resolve()
    assert calls[0][1][0]["owner_confirmed"] is True
