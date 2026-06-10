"""Search and Resolve router."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from shared import (
    ContextPackRequest,
    FUZZY_THRESHOLD,
    ResolveRequest,
    SearchRequest,
    extract_snippet,
    fuzzy_match_score,
    get_root,
    load_cm_index,
    parse_frontmatter,
    serialize,
)
from codememory.context_pack import build_context_pack, render_context_pack
from codememory.index import load_index
from codememory.models import IndexData, MemoryEntry

_logger = logging.getLogger("codememory.router.search")

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
                "intensity": d.get("intensity", 5),
                "status": d.get("status", "active"),
                "dependents": deps_count,
                "maturity": d.get("maturity", "draft"),
                "tags": d.get("tags", []),
                "days_since_last_access": d.get("days_since_last_access"),
                "stability": d.get("stability", 14.0),
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
# Resolve
# ---------------------------------------------------------------------------

@router.post("/resolve")
def post_resolve(req: ResolveRequest):
    if not req.memory_id.strip():
        raise HTTPException(status_code=422, detail="Memory id is required")

    # Check that the target ID exists in the index before resolving
    index = load_cm_index()
    memories = index.memories
    if req.memory_id not in memories:
        raise HTTPException(status_code=404, detail=f"Memory '{req.memory_id}' not found in index")

    try:
        pack = build_context_pack(
            get_root(),
            req.memory_id,
            depth=req.depth,
            budget=req.budget,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Adapter rule: consume the structured pipeline product; never parse
    # rendered text (architecture.md section 5).
    nodes: list[dict[str, Any]] = [
        {
            "id": node.id,
            "type": node.type,
            "trim": node.trim,
            "index": node.index,
            "total": node.total,
            "body": node.content or "",
            "summary": node.summary,
            "maturity": node.maturity,
            "status": node.status,
            "tags": node.tags,
        }
        for node in pack.nodes
    ]
    notices = [f"{n.type}: {n.message}" for n in pack.notices]
    full_text = render_context_pack(pack, "plain-markdown")

    return {
        "target": req.memory_id,
        "depth": req.depth,
        "budget": req.budget,
        "nodes": nodes,
        "full_text": full_text,
        "notices": notices,
    }


# ---------------------------------------------------------------------------
# Context Pack
# ---------------------------------------------------------------------------

@router.post("/context-pack")
def post_context_pack(req: ContextPackRequest):
    if not req.memory_id.strip():
        raise HTTPException(status_code=422, detail="Memory id is required")
    if req.format not in {"xml-markdown", "markdown", "plain-markdown", "json"}:
        raise HTTPException(status_code=422, detail="Unsupported context pack format")

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
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return serialize({
        "target": req.memory_id,
        "format": req.format,
        "pack": pack.model_dump(mode="json"),
        "rendered": rendered,
    })


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

    index = load_cm_index()
    memories = index.memories

    exact_matches: list[dict] = []
    fuzzy_matches: list[dict] = []

    for mem_id, entry in memories.items():
        if hasattr(entry, "model_dump"):
            d = entry.model_dump(mode="json")
        elif isinstance(entry, dict):
            d = entry
        else:
            continue

        if req.type_ and d.get("type") != req.type_:
            continue
        if req.status and d.get("status") != req.status:
            continue
        if req.maturity and d.get("maturity") != req.maturity:
            continue
        if req.tags:
            entry_tags = d.get("tags", [])
            if not all(t in entry_tags for t in req.tags):
                continue

        summary = d.get("summary", "")
        tags = d.get("tags", [])

        body = ""
        rel_path = ""
        if hasattr(entry, "path"):
            rel_path = entry.path
        elif isinstance(entry, dict):
            rel_path = entry.get("path", "")
        if rel_path:
            filepath = get_root() / rel_path
            if filepath.exists():
                _, body = parse_frontmatter(filepath)

        if has_query:
            scores: list[tuple[float, str]] = []
            id_score = fuzzy_match_score(req.query, mem_id)
            if id_score > 0:
                scores.append((id_score, "id"))
            summary_score = fuzzy_match_score(req.query, summary)
            if summary_score > 0:
                scores.append((summary_score, "summary"))
            for tag in tags:
                tag_score = fuzzy_match_score(req.query, tag)
                if tag_score > 0:
                    scores.append((tag_score, "tag"))
            if body:
                body_score = fuzzy_match_score(req.query, body)
                if body_score > 0:
                    scores.append((body_score, "body"))

            if not scores:
                continue

            best_score = max(s[0] for s in scores)
            match_fields = list(set(s[1] for s in scores))
            is_exact = any(s[0] >= 1.0 for s in scores)
            match_quality_tag = "exact" if is_exact else "fuzzy"

            snippet = extract_snippet(body, req.query) if body else ""

            match_entry = {
                "id": mem_id,
                "summary": summary,
                "type": d.get("type", "atom"),
                "tags": d.get("tags", []),
                "intensity": d.get("intensity", 5),
                "maturity": d.get("maturity", "draft"),
                "status": d.get("status", "active"),
                "snippet": snippet,
                "match_quality": match_quality_tag,
                "match_score": round(best_score, 2),
                "match_fields": match_fields,
                "days_since_last_access": d.get("days_since_last_access", None),
                "stability": d.get("stability", 14.0),
                "stability_source": d.get("stability_source", None),
                "access_count": d.get("access_count", 0),
            }

            if is_exact:
                exact_matches.append(match_entry)
            elif best_score >= FUZZY_THRESHOLD:
                fuzzy_matches.append(match_entry)
        else:
            match_entry = {
                "id": mem_id,
                "summary": summary,
                "type": d.get("type", "atom"),
                "tags": d.get("tags", []),
                "intensity": d.get("intensity", 5),
                "maturity": d.get("maturity", "draft"),
                "status": d.get("status", "active"),
                "snippet": "",
                "match_quality": "filter",
                "match_score": 0,
                "match_fields": [],
                "days_since_last_access": d.get("days_since_last_access", None),
                "stability": d.get("stability", 14.0),
                "stability_source": d.get("stability_source", None),
                "access_count": d.get("access_count", 0),
            }
            exact_matches.append(match_entry)

    all_matches = exact_matches + fuzzy_matches
    total = len(all_matches)
    limited = all_matches[:req.limit] if req.limit else all_matches

    return serialize({
        "results": limited,
        "count": len(limited),
        "total": total,
        "query": req.query,
        "limit": req.limit,
    })
