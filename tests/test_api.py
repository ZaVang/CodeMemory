"""API smoke tests using FastAPI TestClient.

Five tests covering the most-used endpoints against real companion dataset data.
Requires: PYTHONPATH=src python -m pytest tests/test_api.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

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
from fastapi.testclient import TestClient  # noqa: E402

# All API requests require X-Codememory-Dataset header (R10-require-dataset-header)
HEADERS = {"X-Codememory-Dataset": "companion"}

client = TestClient(app)


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


def test_post_wander_returns_frontend_contract():
    """POST /api/wander should return a structured memory card, not only text."""
    resp = client.post("/api/wander", headers=HEADERS)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    assert "id" in data and data["id"]
    assert "summary" in data
    assert "type" in data
    assert "tags" in data and isinstance(data["tags"], list)
    assert "intensity" in data and isinstance(data["intensity"], int)
    assert "access_count" in data and isinstance(data["access_count"], int)
    assert "status" in data
    assert "maturity" in data


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
