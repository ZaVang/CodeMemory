"""Memory CRUD router — create, read, update, delete, touch, import, export."""

from __future__ import annotations

import io
import logging
import math
import os
import re
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import yaml
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from shared import (
    CreateMemoryRequest,
    ImportRequest,
    UpdateMemoryRequest,
    compute_body_hash,
    compute_r_probability,
    current_dataset,
    extract_snippet,
    get_root,
    load_cm_index,
    parse_frontmatter,
    reindex,
    resolve_root,
    save_index,
    serialize,
    stale_check,
    update_frontmatter_fields,
)
from codememory.handlers import handle_create, handle_update
from codememory.index import load_index

_logger = logging.getLogger("codememory.router.memories")

router = APIRouter(prefix="/api", tags=["memories"])


# ---------------------------------------------------------------------------
# Memory list
# ---------------------------------------------------------------------------

@router.get("/memories")
def get_memories(offset: int = 0, limit: int = 100):
    index = load_cm_index()
    memories = index.memories
    result = []
    for mem_id, entry in memories.items():
        if hasattr(entry, "model_dump"):
            d = entry.model_dump(mode="json")
        elif hasattr(entry, "dict"):
            d = entry.dict()
        else:
            d = dict(entry) if isinstance(entry, dict) else {}

        directory = "/".join(mem_id.split("/")[:-1]) if "/" in mem_id else ""
        result.append({
            "id": d.get("id", mem_id),
            "type": d.get("type", "atom"),
            "summary": d.get("summary", ""),
            "tags": d.get("tags", []),
            "intensity": d.get("intensity", 5),
            "maturity": d.get("maturity", "draft"),
            "directory": directory,
            "status": d.get("status", "active"),
            "version": d.get("version", 1),
            "access_count": d.get("access_count", 0),
            "last_access": d.get("last_access", None),
            "days_since_last_access": d.get("days_since_last_access", None),
            "stability": d.get("stability", 14.0),
            "stability_source": d.get("stability_source", None),
        })

    total = len(result)
    paginated = result[offset : offset + limit] if offset >= 0 else result
    return serialize({
        "memories": paginated,
        "total": total,
        "offset": offset,
        "limit": limit,
    })


# ---------------------------------------------------------------------------
# Backlinks
# ---------------------------------------------------------------------------

@router.get("/memories/{memory_id:path}/backlinks")
def get_backlinks(memory_id: str):
    memory_id = unquote(memory_id)
    index = load_cm_index()
    memories = index.memories
    backlinks: list[dict] = []
    entry = memories.get(memory_id)
    if not entry:
        return serialize(backlinks)

    for mid, other in memories.items():
        if mid == memory_id:
            continue
        imports_dict = other.imports if hasattr(other, "imports") else other.get("imports", {})
        if not isinstance(imports_dict, dict):
            continue
        for strength in ("required", "recommended", "related"):
            refs = imports_dict.get(strength, [])
            for ref in refs:
                ref_id = ref if isinstance(ref, str) else ref.get("id", "")
                if ref_id == memory_id:
                    backlinks.append({"id": mid, "strength": strength})
                    break

    return serialize(backlinks)


# ---------------------------------------------------------------------------
# Get single memory
# ---------------------------------------------------------------------------

@router.get("/memories/{memory_id:path}")
def get_memory(memory_id: str):
    memory_id = unquote(memory_id)
    index = load_cm_index()
    memories = index.memories
    entry = memories.get(memory_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found in index")

    if hasattr(entry, "path"):
        rel_path = entry.path
    elif isinstance(entry, dict):
        rel_path = entry.get("path", "")
    else:
        raise HTTPException(status_code=500, detail="Invalid index entry format")

    if not rel_path:
        rel_path = f"{memory_id}.md"

    filepath = get_root() / rel_path
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Memory file not found: {rel_path}")

    meta, body = parse_frontmatter(filepath)

    result = {
        **{k: v for k, v in meta.items()},
        "id": memory_id,
        "body": body,
        "days_since_last_access": entry.days_since_last_access,
        "stability": getattr(entry, "stability", 14.0),
        "stability_source": getattr(entry, "stability_source", None),
        "access_count": entry.access_count,
    }

    return serialize(result)


# ---------------------------------------------------------------------------
# Delete memory
# ---------------------------------------------------------------------------

@router.delete("/memories/{memory_id:path}")
def delete_memory(memory_id: str):
    memory_id = unquote(memory_id)
    index = load_cm_index()
    entry = index.memories.get(memory_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")

    if hasattr(entry, "path"):
        rel_path = entry.path
    elif isinstance(entry, dict):
        rel_path = entry.get("path", f"{memory_id}.md")
    else:
        rel_path = f"{memory_id}.md"

    filepath = get_root() / rel_path
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Memory file not found on disk")

    try:
        filepath.unlink()
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {e}")

    reindex(get_root())
    return serialize({"deleted": memory_id})


# ---------------------------------------------------------------------------
# Create memory
# ---------------------------------------------------------------------------

@router.post("/memories")
def post_create_memory(req: CreateMemoryRequest):
    file_path_str = handle_create(
        root=get_root(),
        memory_type=req.type,
        memory_id=req.memory_id,
        schema=req.schema,
        intensity=req.intensity,
        tags=req.tags,
        dry_run=False,
        maturity=req.maturity,
    )

    filepath = Path(file_path_str)
    if not filepath.exists():
        raise HTTPException(status_code=500, detail="Memory file was not created")

    meta, _ = parse_frontmatter(filepath)
    needs_summary_update = req.summary and req.summary != "TODO: fill in summary"
    if needs_summary_update:
        meta["summary"] = req.summary

    if req.imports:
        meta["imports"] = req.imports

    body_to_write = req.body
    meta["summary_hash"] = compute_body_hash(body_to_write.strip())

    yaml_str = yaml.dump(meta, allow_unicode=True, sort_keys=False)
    new_content = f"---\n{yaml_str}---\n{body_to_write}"
    filepath.write_text(new_content, encoding="utf-8")

    reindex(get_root())

    meta, body = parse_frontmatter(filepath)
    index = load_cm_index()
    entry = index.memories.get(req.memory_id)
    days_since = getattr(entry, "days_since_last_access", None) if entry else None
    stability_val = getattr(entry, "stability", 14.0) if entry else 14.0
    access_count_val = getattr(entry, "access_count", 0) if entry else 0

    result = {
        **{k: v for k, v in meta.items()},
        "id": req.memory_id,
        "body": body,
        "days_since_last_access": days_since,
        "stability": stability_val,
        "stability_source": getattr(entry, "stability_source", None) if entry else None,
        "access_count": access_count_val,
    }
    return serialize(result)


# ---------------------------------------------------------------------------
# Update memory
# ---------------------------------------------------------------------------

@router.put("/memories/{memory_id:path}")
def put_update_memory(memory_id: str, req: UpdateMemoryRequest):
    memory_id = unquote(memory_id)
    index = load_cm_index()
    memories = index.memories
    entry = memories.get(memory_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")

    if hasattr(entry, "path"):
        filepath = get_root() / entry.path
    elif isinstance(entry, dict):
        filepath = get_root() / entry.get("path", f"{memory_id}.md")
    else:
        filepath = get_root() / f"{memory_id}.md"

    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Memory file not found on disk")

    has_core_update = any([
        req.body is not None,
        req.summary is not None,
        req.status is not None,
    ])

    has_metadata_update = any([
        req.tags is not None,
        req.intensity is not None,
        req.imports is not None,
        req.maturity is not None,
        req.stability is not None,
    ])

    if has_core_update:
        change_note = req.change_note or "API update"
        handle_update(
            root=get_root(),
            memory_id=memory_id,
            body=req.body,
            summary=req.summary,
            change_note=change_note,
            status=req.status,
        )

    if has_metadata_update:
        meta_updates: dict[str, Any] = {}
        if req.tags is not None:
            meta_updates["tags"] = req.tags
        if req.intensity is not None:
            meta_updates["intensity"] = req.intensity
        if req.imports is not None:
            meta_updates["imports"] = req.imports
        if req.maturity is not None:
            meta_updates["maturity"] = req.maturity
        if req.stability is not None:
            meta_updates["stability"] = req.stability
            meta_updates["stability_source"] = "manual"
        update_frontmatter_fields(filepath, meta_updates)

    reindex(get_root())

    meta, body = parse_frontmatter(filepath)
    updated_index = load_cm_index()
    updated_entry = updated_index.memories.get(memory_id)
    days_since = getattr(updated_entry, "days_since_last_access", None) if updated_entry else None
    stability_val = getattr(updated_entry, "stability", 14.0) if updated_entry else 14.0
    access_count_val = getattr(updated_entry, "access_count", 0) if updated_entry else 0

    result = {
        **{k: v for k, v in meta.items()},
        "id": memory_id,
        "body": body,
        "days_since_last_access": days_since,
        "stability": stability_val,
        "stability_source": getattr(updated_entry, "stability_source", None) if updated_entry else None,
        "access_count": access_count_val,
    }
    return serialize(result)


# ---------------------------------------------------------------------------
# Touch (lightweight decay refresh)
# ---------------------------------------------------------------------------

@router.post("/memories/{memory_id:path}/touch")
def post_touch(memory_id: str):
    memory_id = unquote(memory_id)
    index = load_cm_index()
    memories = index.memories
    entry = memories.get(memory_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")

    now_iso = datetime.now().isoformat()

    if getattr(entry, "stability_source", None) != "manual":
        old_days_since = getattr(entry, "days_since_last_access", None)
        if old_days_since is not None and old_days_since > 0 and entry.stability > 0:
            R = compute_r_probability(old_days_since, entry.stability)
            s_inc = 1.05 + 0.75 * math.exp(-((R - 0.78) ** 2) / 0.125)
            diminish = math.sqrt(14.0 / max(entry.stability, 14.0))
            entry.stability = min(entry.stability * s_inc * diminish, 365.0)

    entry.access_count += 1
    entry.last_access = now_iso
    entry.days_since_last_access = 0

    save_index(get_root(), index)

    meta, body = parse_frontmatter(get_root() / entry.path)
    result = {
        **{k: v for k, v in meta.items()},
        "id": memory_id,
        "body": body,
        "days_since_last_access": 0,
        "stability": entry.stability,
        "stability_source": getattr(entry, "stability_source", None),
        "access_count": entry.access_count,
    }
    return serialize(result)


# ---------------------------------------------------------------------------
# Rehash — fix stale summary (recompute summary_hash from current body)
# ---------------------------------------------------------------------------

@router.post("/memories/{memory_id:path}/rehash")
def post_rehash(memory_id: str):
    memory_id = unquote(memory_id)
    index = load_cm_index()
    memories = index.memories
    entry = memories.get(memory_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")

    filepath = get_root() / entry.path
    meta, body = parse_frontmatter(filepath)
    new_hash = compute_body_hash(body.strip())
    entry.summary_hash = new_hash
    save_index(get_root(), index)

    return serialize({"id": memory_id, "summary_hash": new_hash, "stale": False})


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

@router.post("/import")
def post_import(req: ImportRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Text body is required for import")

    root = get_root()
    directory_map = {
        "preferences": "user/preferences",
        "decisions": "user/decisions",
        "facts": "user/facts",
        "general": "user/imports",
    }
    directory = directory_map.get(req.extract, "user/imports")
    dir_path = root / directory

    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to create import directory: {e}")

    from datetime import datetime as _dt
    safe_title = re.sub(r"[^a-z0-9]+", "-", text[:60].split("\n")[0].lower().strip())
    if len(safe_title) > 40:
        safe_title = safe_title[:40]
    ts = _dt.now().strftime("%Y%m%d-%H%M")
    filename = f"{ts}-{safe_title}.md"
    filepath = dir_path / filename

    memory_id = f"{directory}/{filename[:-3]}"

    lines = text.split("\n")
    summary = lines[0][:120] if lines else ""
    tags = [req.extract]
    intensity = 5

    file_path_str = handle_create(
        root=root,
        memory_type="atom",
        memory_id=memory_id,
        intensity=intensity,
        tags=tags,
        maturity="draft",
    )

    fp = Path(file_path_str)
    meta, _ = parse_frontmatter(fp)
    meta["summary"] = summary
    meta["summary_hash"] = compute_body_hash(text.strip())
    yaml_str = yaml.dump(meta, allow_unicode=True, sort_keys=False)
    fp.write_text(f"---\n{yaml_str}---\n{text}", encoding="utf-8")

    reindex(root)

    return serialize({
        "imported": memory_id,
        "file": str(fp.relative_to(root)),
        "summary": summary,
    })


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

@router.get("/export")
def get_export(request: Request):
    root = get_root()
    all_md = sorted(root.rglob("*.md"))
    if not all_md:
        raise HTTPException(status_code=404, detail="No memory files found")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for md_file in all_md:
            arcname = str(md_file.relative_to(root))
            zf.write(md_file, arcname)

    buf.seek(0)
    dataset = request.headers.get("X-Codememory-Dataset", "investment")
    filename = f"codememory-{dataset}-export.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
