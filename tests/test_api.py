"""API smoke tests using FastAPI TestClient.

Five tests covering the most-used endpoints against real companion dataset data.
Requires: PYTHONPATH=src python -m pytest tests/test_api.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

# Ensure backend server is importable
_BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# Ensure codememory package is importable
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Set the default dataset before importing server (which reads env at module level)
import os
os.environ.setdefault("CODEMEMORY_DEFAULT_DATASET", "companion")

from backend.server import app  # noqa: E402
import routers.memories as memories_router  # noqa: E402
import routers.reviews as reviews_router  # noqa: E402
import routers.search as search_router  # noqa: E402
import routers.stats as stats_router  # noqa: E402
import shared as backend_shared  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from codememory.core import parse_frontmatter  # noqa: E402
from codememory.create import create  # noqa: E402
from codememory.index import load_index, reindex  # noqa: E402
from codememory.proposals import create_proposal, list_proposals  # noqa: E402

# All API requests require X-Codememory-Dataset header (R10-require-dataset-header)
HEADERS = {"X-Codememory-Dataset": "companion"}

client = TestClient(app)


def test_dataset_header_rejects_absolute_root_without_writing(tmp_path: Path):
    outside_root = tmp_path / "codememory-ui-root-escape"

    response = client.post(
        "/api/memories",
        headers={"X-Codememory-Dataset": str(outside_root)},
        json={"id": "memory/escape", "summary": "Must not be written"},
    )

    assert response.status_code == 400
    assert not outside_root.exists()


@pytest.mark.parametrize(
    "dataset",
    ["../escape", r"..\escape", "C:escape", "not-a-dataset", " companion ", " "],
)
def test_dataset_header_accepts_only_exact_known_aliases(dataset: str):
    before = {path.name for path in backend_shared.EXAMPLES_DIR.iterdir()}
    response = client.get("/api/stats", headers={"X-Codememory-Dataset": dataset})
    assert response.status_code == 400
    assert {path.name for path in backend_shared.EXAMPLES_DIR.iterdir()} == before


@pytest.mark.parametrize(
    "dataset",
    ["../escape", r"..\escape", "C:escape", "not-a-dataset", " companion ", " "],
)
def test_resolve_root_rejects_non_alias_dataset(dataset: str):
    with pytest.raises(ValueError, match="dataset"):
        backend_shared.resolve_root(dataset)


def test_resolve_root_enforces_containment_after_alias_lookup(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        backend_shared,
        "get_available_datasets",
        lambda: [{"name": "forged", "path": str(tmp_path), "memory_count": 0}],
    )

    with pytest.raises(ValueError, match="outside"):
        backend_shared.resolve_root("forged")


# ---------------------------------------------------------------------------
# Test 1: GET /api/memories returns paginated results
# ---------------------------------------------------------------------------

def test_get_memories_returns_paginated_results():
    """GET /api/memories should return a paginated list of memory summaries."""
    resp = client.get("/api/memories", headers=HEADERS)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "memories" in data, "Response should contain 'memories' key"
    assert "total" in data, "Response should contain 'total' key"
    assert "offset" in data, "Response should contain 'offset' key"
    assert "limit" in data, "Response should contain 'limit' key"
    assert data["total"] > 0, "Should have at least one memory"
    assert len(data["memories"]) <= data["limit"], "Returned count should not exceed limit"

    # Spot-check a memory entry structure
    mem = data["memories"][0]
    assert "id" in mem
    assert "type" in mem
    assert "summary" in mem
    assert "tags" in mem
    assert "maturity" in mem
    assert "status" in mem
    assert "directory" in mem

    # Test pagination: offset + limit
    resp2 = client.get("/api/memories?offset=0&limit=3", headers=HEADERS)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2["memories"]) <= 3
    assert data2["limit"] == 3
    assert data2["offset"] == 0


# ---------------------------------------------------------------------------
# Test 2: GET /api/memories/{id} returns a specific memory
# ---------------------------------------------------------------------------

def test_get_memory_by_id_returns_full_content():
    """GET /api/memories/{id} should return a specific memory with all fields."""
    # First, get a valid memory ID from the list
    resp = client.get("/api/memories?limit=1", headers=HEADERS)
    assert resp.status_code == 200
    mem_id = resp.json()["memories"][0]["id"]

    resp2 = client.get(f"/api/memories/{mem_id}", headers=HEADERS)
    assert resp2.status_code == 200, f"Expected 200 for '{mem_id}', got {resp2.status_code}: {resp2.text}"
    data = resp2.json()
    assert data["id"] == mem_id
    assert "body" in data, "Should have body field"
    assert "type" in data, "Should have type field"
    assert "summary" in data, "Should have summary field"
    assert "tags" in data, "Should have tags field"
    assert "maturity" in data, "Should have maturity field"

    # Non-existent ID should return 404
    resp3 = client.get("/api/memories/nonexistent/id", headers=HEADERS)
    assert resp3.status_code == 404, f"Expected 404 for nonexistent ID, got {resp3.status_code}"


# ---------------------------------------------------------------------------
# Test 3: POST /api/search returns match results
# ---------------------------------------------------------------------------

def test_post_search_returns_matches():
    """POST /api/search with a query should return ranked results with
    match metadata."""
    # Search for a term that should match at least one memory
    resp = client.post(
        "/api/search",
        json={"query": "context"},
        headers=HEADERS,
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "results" in data
    assert "count" in data
    assert "total" in data
    assert "query" in data
    assert data["query"] == "context"
    assert data["total"] > 0, "Should find at least one match for 'context'"

    # Spot-check result structure
    result = data["results"][0]
    assert "id" in result
    assert "summary" in result
    assert "match_quality" in result
    assert "match_score" in result
    assert "match_fields" in result

    # Filter-only query (R10-search-filter-fix): tags filter without query text
    resp2 = client.post(
        "/api/search",
        json={"tags": []},
        headers=HEADERS,
    )
    assert resp2.status_code == 200
    # Empty query + empty tags = empty results (unchanged)
    data2 = resp2.json()
    assert data2["count"] == 0
    assert data2["total"] == 0


def test_post_search_delegates_discovery_to_core(monkeypatch):
    calls: list[dict] = []

    def fake_core_search(root: Path, **kwargs):
        calls.append({"root": root, **kwargs})
        return [{
            "id": "memory/from-core",
            "summary": "Core result",
            "type": "atom",
            "tags": ["core"],
            "maturity": "verified",
            "status": "active",
            "score": 4.0,
            "match_field": "id",
            "snippet": "",
            "access_count": 0,
        }]

    monkeypatch.setattr(search_router, "core_search", fake_core_search)
    response = client.post(
        "/api/search",
        json={"query": "from-core", "tags": ["core"]},
        headers=HEADERS,
    )

    assert response.status_code == 200
    assert len(calls) == 1
    assert calls[0]["root"] == backend_shared.resolve_root("companion")
    assert calls[0]["query"] == "from-core"
    assert calls[0]["tags"] == ["core"]
    assert response.json()["results"][0]["id"] == "memory/from-core"


# ---------------------------------------------------------------------------
# Test 4: POST /api/resolve returns DAG-resolved context
# ---------------------------------------------------------------------------

def test_post_resolve_returns_topologically_sorted_context():
    """POST /api/resolve with a valid ID should return DAG-resolved context
    with structured node list."""
    # Get a valid memory ID to resolve
    resp = client.get("/api/memories?limit=1", headers=HEADERS)
    assert resp.status_code == 200
    mem_id = resp.json()["memories"][0]["id"]

    resp2 = client.post(
        "/api/resolve",
        json={"id": mem_id, "depth": "recommended", "budget": 2000},
        headers=HEADERS,
    )
    assert resp2.status_code == 200, f"Expected 200 for resolve, got {resp2.status_code}: {resp2.text}"
    data = resp2.json()
    assert data["target"] == mem_id
    assert "depth" in data
    assert "budget" in data
    assert "nodes" in data
    assert "full_text" in data
    assert "notices" in data

    # At least the target memory should be in nodes
    assert len(data["nodes"]) >= 1, "Should have at least the target node"
    target_node = next((n for n in data["nodes"] if n["id"] == mem_id), None)
    assert target_node is not None, "Target node should be in the resolved nodes"
    assert "trim" in target_node
    assert target_node["trim"] in ("full", "summary", "skipped")

    # Non-existent ID should return 404
    resp3 = client.post(
        "/api/resolve",
        json={"id": "nonexistent/id", "depth": "recommended", "budget": 2000},
        headers=HEADERS,
    )
    assert resp3.status_code == 404, f"Expected 404 for nonexistent, got {resp3.status_code}"


# ---------------------------------------------------------------------------
# Test 5: GET /api/stats returns aggregated statistics
# ---------------------------------------------------------------------------

def test_get_stats_returns_aggregated_statistics():
    """GET /api/stats should return total_count, stale_count, maturity
    distribution, and tag frequencies."""
    resp = client.get("/api/stats", headers=HEADERS)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "total" in data, "Should have total count"
    assert "maturity" in data, "Should have maturity distribution"
    assert "type" in data, "Should have type counts"
    assert "status" in data, "Should have status counts"
    assert "stale_count" in data, "Should have stale count"
    assert "stale_ids" in data, "Should have stale IDs list"
    assert "tags" in data, "Should have tag frequencies"

    assert data["total"] > 0, "Total should be > 0 for companion dataset"
    assert isinstance(data["stale_count"], int), "stale_count should be an integer"
    assert isinstance(data["stale_ids"], list), "stale_ids should be a list"
    assert isinstance(data["maturity"], dict), "maturity should be a dict"
    assert isinstance(data["tags"], list), "tags should be a list"

    # Spot-check tag structure
    if data["tags"]:
        tag_entry = data["tags"][0]
        assert "tag" in tag_entry
        assert "count" in tag_entry


def test_post_validate_returns_frontend_contract():
    """POST /api/validate should return the object shape expected by Dashboard."""
    resp = client.post("/api/validate", headers=HEADERS)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    assert set(data) >= {
        "validated_count",
        "error_count",
        "warning_count",
        "errors",
        "warnings",
    }
    assert isinstance(data["validated_count"], int)
    assert isinstance(data["error_count"], int)
    assert isinstance(data["warning_count"], int)
    assert isinstance(data["errors"], list)
    assert isinstance(data["warnings"], list)


def test_validate_parser_exposes_current_warning_kinds():
    text = "\n".join([
        "[PROPOSED-WARN] memory/draft has waited too long",
        "[STATUS-WARN] memory/active imports memory/proposed",
        "[GOLDEN-WARN] memory/test golden_questions must be a list",
        "[PROPOSAL-WARN] proposal-1 targets a missing memory",
        "[CAPTURE-WARN] incomplete Capture ignored",
        "[TOPIC-WARN] malformed Topic ignored",
    ])

    errors, warnings = stats_router._parse_validate_output(text)

    assert errors == []
    assert [item["type"] for item in warnings] == [
        "proposed", "status", "golden_questions", "proposal", "capture", "topic",
    ]


def test_post_context_pack_returns_structured_pack_and_xml_markdown():
    """POST /api/context-pack should expose backend-first agent handoff output."""
    mem_resp = client.get("/api/memories?limit=1", headers=HEADERS)
    assert mem_resp.status_code == 200
    mem_id = mem_resp.json()["memories"][0]["id"]

    resp = client.post(
        "/api/context-pack",
        json={
            "id": mem_id,
            "depth": "recommended",
            "budget": 2000,
            "format": "xml-markdown",
            "task_goal": "Use this as agent handoff context.",
        },
        headers=HEADERS,
    )

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["target"] == mem_id
    assert data["format"] == "xml-markdown"
    assert "pack" in data and isinstance(data["pack"], dict)
    assert data["pack"]["target_id"] == mem_id
    assert data["pack"]["task_goal"] == "Use this as agent handoff context."
    assert data["pack"]["nodes"], "Context pack should include at least the target memory"
    assert "rendered" in data
    assert "<codememory_context_pack" in data["rendered"]
    assert f'target_id="{mem_id}"' in data["rendered"]


def test_post_build_is_primary_structured_context_endpoint():
    mem_resp = client.get("/api/memories?limit=1", headers=HEADERS)
    mem_id = mem_resp.json()["memories"][0]["id"]
    request = {
        "id": mem_id,
        "depth": "recommended",
        "budget": 2000,
        "format": "xml-markdown",
        "task_goal": "Operator handoff",
    }

    response = client.post("/api/build", json=request, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["target"] == mem_id
    assert data["pack"]["target_id"] == mem_id
    assert data["pack"]["task_goal"] == "Operator handoff"
    assert data["pack"]["nodes"]
    assert "<codememory_context_pack" in data["rendered"]

    compatibility = client.post("/api/context-pack", json=request, headers=HEADERS)
    assert compatibility.status_code == 200
    legacy = compatibility.json()
    assert legacy["pack"]["nodes"] == data["pack"]["nodes"]


def _bind_operator_root(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setattr(reviews_router, "get_root", lambda: root)
    monkeypatch.setattr(reviews_router, "load_cm_index", lambda: load_index(root))


def test_review_queue_and_actions_use_core_state_transitions(tmp_path: Path, monkeypatch):
    active = create(tmp_path, "atom", "memory/active", summary="Active", body="# Active")
    merge_atom = create(
        tmp_path, "atom", "memory/merge-me", summary="Merge me", body="# Proposed", propose=True,
    )
    reject_atom = create(
        tmp_path, "atom", "memory/reject-me", summary="Reject me", body="# Proposed", propose=True,
    )
    patch_target = create(tmp_path, "atom", "memory/patch-target", summary="Before", body="# Before")
    rejected_target = create(tmp_path, "atom", "memory/rejected-target", summary="Untouched", body="# Untouched")
    merge_patch = create_proposal(
        tmp_path, "memory/patch-target", reason="Improve summary", summary="After",
    )
    reject_patch = create_proposal(
        tmp_path, "memory/rejected-target", reason="Do not apply", summary="Wrong",
    )
    rejected_before = rejected_target.read_bytes()
    _bind_operator_root(monkeypatch, tmp_path)

    queued = client.get("/api/reviews", headers=HEADERS)
    assert queued.status_code == 200
    queue = queued.json()
    assert queue["total"] == 4
    assert {item["id"] for item in queue["proposed_atoms"]} == {
        "memory/merge-me", "memory/reject-me",
    }
    assert all(item["created_by"] == "user" for item in queue["proposed_atoms"])
    patch_item = next(item for item in queue["patch_proposals"] if item["id"] == merge_patch.proposal_id)
    assert patch_item["target_id"] == "memory/patch-target"
    assert patch_item["patch_fields"] == ["summary"]
    assert patch_item["patch"]["summary"] == "After"

    assert client.post(
        "/api/reviews/atoms/merge", json={"id": "memory/merge-me"}, headers=HEADERS,
    ).status_code == 200
    assert parse_frontmatter(merge_atom)[0]["status"] == "active"

    assert client.post(
        "/api/reviews/atoms/reject", json={"id": "memory/reject-me"}, headers=HEADERS,
    ).status_code == 200
    assert parse_frontmatter(reject_atom)[0]["status"] == "archived"

    assert client.post(
        "/api/reviews/patches/merge", json={"id": merge_patch.proposal_id}, headers=HEADERS,
    ).status_code == 200
    assert parse_frontmatter(patch_target)[0]["summary"] == "After"

    assert client.post(
        "/api/reviews/patches/reject", json={"id": reject_patch.proposal_id}, headers=HEADERS,
    ).status_code == 200
    assert rejected_target.read_bytes() == rejected_before
    assert list_proposals(tmp_path) == []

    active_before = active.read_bytes()
    conflict = client.post(
        "/api/reviews/atoms/merge", json={"id": "memory/active"}, headers=HEADERS,
    )
    assert conflict.status_code == 409
    assert active.read_bytes() == active_before

    escaped = client.post(
        "/api/reviews/patches/merge", json={"id": "../escape"}, headers=HEADERS,
    )
    assert escaped.status_code == 400


def test_golden_question_endpoint_exports_core_bundle(tmp_path: Path, monkeypatch):
    path = create(tmp_path, "atom", "memory/tested", summary="Tested", body="# Tested")
    meta, body = parse_frontmatter(path)
    meta["golden_questions"] = [
        {"q": "What is tested?", "expect": "The canonical build."},
        {"q": "Is an LLM run here?"},
    ]
    path.write_text(
        f"---\n{yaml.dump(meta, allow_unicode=True, sort_keys=False)}---\n{body}\n",
        encoding="utf-8",
    )
    empty = create(tmp_path, "atom", "memory/no-questions", summary="Empty", body="# Empty")
    reindex(tmp_path)
    _bind_operator_root(monkeypatch, tmp_path)

    response = client.get("/api/tests/memory/tested", headers=HEADERS)
    assert response.status_code == 200
    bundle = response.json()
    assert bundle["format_version"] == "memory-test/v1"
    assert bundle["entry"] == "memory/tested"
    assert bundle["questions"] == [
        {"q": "What is tested?", "expect": "The canonical build."},
        {"q": "Is an LLM run here?", "expect": None},
    ]
    assert "<codememory_context_pack" in bundle["context"]
    assert bundle["notices"] == []

    no_questions = client.get("/api/tests/memory/no-questions", headers=HEADERS)
    assert no_questions.status_code == 200
    assert no_questions.json()["questions"] == []
    assert no_questions.json()["notices"]
    assert empty.exists()


def test_operator_create_is_one_complete_core_write(tmp_path: Path, monkeypatch):
    calls: list[dict] = []
    real_handle_create = memories_router.handle_create

    def recording_create(*args, **kwargs):
        calls.append(dict(kwargs))
        return real_handle_create(*args, **kwargs)

    monkeypatch.setattr(memories_router, "get_root", lambda: tmp_path)
    monkeypatch.setattr(memories_router, "load_cm_index", lambda: load_index(tmp_path))
    monkeypatch.setattr(memories_router, "handle_create", recording_create)

    response = client.post(
        "/api/memories",
        headers=HEADERS,
        json={
            "id": "memory/完整创建",
            "summary": "Complete owner creation",
            "body": "# Complete\n\nOne write.",
            "tags": ["operator"],
            "maturity": "verified",
            "propose": True,
            "imports": {"related": ["memory/reference"]},
        },
    )
    assert response.status_code == 200
    assert len(calls) == 1
    assert calls[0]["summary"] == "Complete owner creation"
    assert calls[0]["body"] == "# Complete\n\nOne write."
    assert calls[0]["propose"] is True
    meta, body = parse_frontmatter(tmp_path / "memory/完整创建.md")
    assert meta["status"] == "proposed"
    assert meta["imports"]["related"] == ["memory/reference"]
    assert body == "# Complete\n\nOne write."


def test_operator_update_is_one_complete_core_write(tmp_path: Path, monkeypatch):
    path = create(
        tmp_path,
        "atom",
        "memory/update-me",
        summary="Before",
        body="# Before",
        import_required=["memory/old"],
    )
    calls: list[dict] = []
    real_handle_update = memories_router.handle_update

    def recording_update(*args, **kwargs):
        calls.append(dict(kwargs))
        return real_handle_update(*args, **kwargs)

    monkeypatch.setattr(memories_router, "get_root", lambda: tmp_path)
    monkeypatch.setattr(memories_router, "load_cm_index", lambda: load_index(tmp_path))
    monkeypatch.setattr(memories_router, "handle_update", recording_update)

    response = client.put(
        "/api/memories/memory/update-me",
        headers=HEADERS,
        json={
            "summary": "After",
            "body": "# After",
            "tags": ["operator"],
            "maturity": "verified",
            "imports": {},
            "change_note": "Complete operator edit",
        },
    )

    assert response.status_code == 200
    assert len(calls) == 1
    assert calls[0]["tags"] == ["operator"]
    assert calls[0]["maturity"] == "verified"
    assert calls[0]["import_required"] == []
    meta, body = parse_frontmatter(path)
    assert meta["summary"] == "After"
    assert meta["tags"] == ["operator"]
    assert meta["maturity"] == "verified"
    assert meta["imports"] == {"required": [], "recommended": [], "related": []}
    assert body == "# After"


def test_build_rejects_proposed_target_without_writing(tmp_path: Path, monkeypatch):
    path = create(tmp_path, "atom", "memory/proposed", summary="Proposed", propose=True)
    before = path.read_bytes()
    monkeypatch.setattr(search_router, "get_root", lambda: tmp_path)

    response = client.post(
        "/api/build",
        headers=HEADERS,
        json={"id": "memory/proposed", "format": "plain-markdown"},
    )

    assert response.status_code == 400
    assert "proposed" in response.json()["detail"]
    assert path.read_bytes() == before


def test_get_source_expand_returns_structured_missing_notice():
    """GET /api/sources/expand should expose the shared expand_source contract."""
    resp = client.get(
        "/api/sources/expand?artifact_id=src/not-registered",
        headers=HEADERS,
    )

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["artifact_id"] == "src/not-registered"
    assert data["status"] == "missing"
    assert data["content"] == ""
