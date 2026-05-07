"""Search and Resolve router."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from shared import (
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
from codememory.handlers import handle_resolve
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
        text = handle_resolve(
            root=get_root(),
            memory_id=req.memory_id,
            depth=req.depth,
            budget=req.budget,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Parse the resolve text to extract structured node information
    nodes: list[dict[str, Any]] = []
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        if line.startswith("## ["):
            break
        i += 1

    while i < len(lines):
        line = lines[i]
        m = re.match(r"^##\s+\[(\d+)/(\d+)\]\s+(.+?)\s+\((.+)\)\s*$", line)
        if not m:
            i += 1
            continue

        node_index = int(m.group(1))
        node_total = int(m.group(2))
        node_id = m.group(3).strip()
        node_info = m.group(4)

        if "SKIPPED" in node_info:
            trim = "skipped"
            node_type = node_info.replace("SKIPPED - budget", "").strip().rstrip(",").strip() or "atom"
        elif "SUMMARY" in node_info:
            trim = "summary"
            node_type = node_info.split(" - SUMMARY")[0].strip() or "atom"
        else:
            trim = "full"
            node_type = node_info

        body_lines: list[str] = []
        i += 2
        while i < len(lines):
            next_line = lines[i]
            if next_line.startswith("## [") or next_line.startswith("---"):
                break
            body_lines.append(next_line)
            i += 1

        body_text = "\n".join(body_lines).strip()

        node_meta = memories.get(node_id)
        node_entry: dict[str, Any] = {
            "id": node_id, "type": node_type, "trim": trim,
            "index": node_index, "total": node_total, "body": body_text,
        }
        if node_meta is not None:
            if hasattr(node_meta, "model_dump"):
                md = node_meta.model_dump(mode="json")
            elif isinstance(node_meta, dict):
                md = node_meta
            else:
                md = {}
            node_entry["summary"] = md.get("summary", "")
            node_entry["maturity"] = md.get("maturity", "draft")
            node_entry["status"] = md.get("status", "active")
            node_entry["tags"] = md.get("tags", [])
        else:
            node_entry["summary"] = ""
            node_entry["maturity"] = "draft"
            node_entry["status"] = "active"
            node_entry["tags"] = []

        nodes.append(node_entry)

        if i < len(lines) and lines[i].startswith("---"):
            break

    # Parse notices
    notice_lines = [ln.strip() for ln in lines if ln.strip().startswith("[NOTICE]")]
    notices = [ln.removeprefix("[NOTICE]").strip() for ln in notice_lines]

    return {
        "target": req.memory_id,
        "depth": req.depth,
        "budget": req.budget,
        "nodes": nodes,
        "full_text": text,
        "notices": notices,
    }


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
