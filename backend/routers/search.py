"""Graph, Build, and Search REST adapter."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from shared import (
    ContextPackRequest,
    ResolveRequest,
    SearchRequest,
    get_root,
    load_cm_index,
    serialize,
)
from codememory.build import build_context_pack, render_context_pack
from codememory.models import IndexData
from codememory.search import search as core_search

router = APIRouter(prefix="/api", tags=["search"])


def _count_dependents(memory_id: str, index: IndexData) -> int:
    count = 0
    for mid, entry in index.memories.items():
        if mid == memory_id:
            continue
        imports_dict = entry.imports
        if not isinstance(imports_dict, dict):
            continue
        all_refs = (
            imports_dict.get("required", [])
            + imports_dict.get("recommended", [])
            + imports_dict.get("related", [])
        )
        for ref in all_refs:
            ref_id = ref if isinstance(ref, str) else ref.get("id", "")
            if ref_id == memory_id:
                count += 1
                break
    return count


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

@router.get("/graph")
def get_graph(focus: str | None = None):
    index = load_cm_index()
    memories = index.memories
    nodes: list[dict] = []
    edges: list[dict] = []

    for mem_id, entry in memories.items():
        if hasattr(entry, "model_dump"):
            d = entry.model_dump(mode="json")
        elif isinstance(entry, dict):
            d = entry
        else:
            continue

        deps_count = _count_dependents(mem_id, index)
        # Derive directory from the ID (e.g. user/beliefs/friendship-view → user/beliefs)
        _parts = mem_id.rsplit("/", 1)
        _directory = _parts[0] if len(_parts) > 1 else ""
        nodes.append({
            "data": {
                "id": mem_id,
                "label": mem_id.split("/")[-1],
                "directory": _directory,
                "type": d.get("type", "atom"),
                "summary": d.get("summary", ""),
                "status": d.get("status", "active"),
                "dependents": deps_count,
                "maturity": d.get("maturity", "draft"),
                "tags": d.get("tags", []),
                "days_since_last_access": d.get("days_since_last_access"),
            },
        })

        imports_dict = d.get("imports", {})
        if isinstance(imports_dict, dict):
            for strength, refs in imports_dict.items():
                for ref in refs:
                    ref_id = ref if isinstance(ref, str) else ref.get("id", "")
                    if ref_id in memories:
                        edges.append({
                            "data": {
                                "source": mem_id,
                                "target": ref_id,
                                "strength": strength,
                            },
                        })

    return serialize({"nodes": nodes, "edges": edges})


# ---------------------------------------------------------------------------
# Build (primary operator assembly endpoint)
# ---------------------------------------------------------------------------

def _build_response(req: ContextPackRequest) -> dict[str, Any]:
    if not req.memory_id.strip():
        raise HTTPException(status_code=422, detail="Memory id is required")
    if req.format not in {"xml-markdown", "markdown", "plain-markdown", "json"}:
        raise HTTPException(status_code=422, detail="Unsupported build format")

    try:
        pack = build_context_pack(
            get_root(),
            req.memory_id,
            depth=req.depth,
            budget=req.budget,
            focus=req.focus,
            task_goal=req.task_goal,
        )
        rendered = render_context_pack(pack, req.format)  # type: ignore[arg-type]
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        raise HTTPException(status_code=status, detail=message)

    return serialize({
        "target": req.memory_id,
        "format": req.format,
        "pack": pack.model_dump(mode="json"),
        "rendered": rendered,
    })


@router.post("/build")
def post_build(req: ContextPackRequest):
    return _build_response(req)


# ---------------------------------------------------------------------------
# Resolve (legacy compatibility shape; same build pipeline)
# ---------------------------------------------------------------------------

@router.post("/resolve")
def post_resolve(req: ResolveRequest):
    built = _build_response(ContextPackRequest(
        id=req.memory_id,
        depth=req.depth,
        budget=req.budget,
        format="plain-markdown",
    ))
    pack_data = built["pack"]

    # Adapter rule: consume the structured pipeline product; never parse
    # rendered text (architecture.md section 5).
    nodes: list[dict[str, Any]] = [
        {
            "id": node["id"],
            "type": node["type"],
            "trim": node["trim"],
            "index": node["index"],
            "total": node["total"],
            "body": node.get("content") or "",
            "summary": node.get("summary"),
            "maturity": node.get("maturity"),
            "status": node.get("status"),
            "tags": node.get("tags", []),
        }
        for node in pack_data["nodes"]
    ]
    notices = [f"{n['type']}: {n['message']}" for n in pack_data["notices"]]

    return {
        "target": req.memory_id,
        "depth": req.depth,
        "budget": req.budget,
        "nodes": nodes,
        "full_text": built["rendered"],
        "notices": notices,
    }


# ---------------------------------------------------------------------------
# Context Pack
# ---------------------------------------------------------------------------

@router.post("/context-pack")
def post_context_pack(req: ContextPackRequest):
    return _build_response(req)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@router.post("/search")
def post_search(req: SearchRequest):
    has_query = bool(req.query and req.query.strip())
    has_filters = bool(req.tags or req.type_ or req.status or req.maturity)
    if not has_query and not has_filters:
        return serialize({
            "results": [],
            "count": 0,
            "total": 0,
            "query": req.query,
            "limit": req.limit,
        })

    canonical = core_search(
        get_root(),
        query=req.query.strip() if has_query else None,
        tags=req.tags,
        type_=req.type_,
        status=req.status,
        maturity=req.maturity,
    )
    results = [
        {
            "id": item["id"],
            "summary": item.get("summary", ""),
            "type": item.get("type", "atom"),
            "tags": item.get("tags", []),
            "maturity": item.get("maturity", "draft"),
            "status": item.get("status", "active"),
            "snippet": item.get("snippet", ""),
            "match_quality": "exact" if has_query else "filter",
            "match_score": item.get("score", 0),
            "match_fields": [item["match_field"]] if item.get("match_field") else [],
            "access_count": item.get("access_count", 0),
        }
        for item in canonical
    ]
    total = len(results)
    limited = results[:req.limit]

    return serialize({
        "results": limited,
        "count": len(limited),
        "total": total,
        "query": req.query,
        "limit": req.limit,
    })
