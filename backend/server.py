"""CodeMemory Backend API — FastAPI server.

Reads from the existing codememory index.json and .md files.
Does NOT modify src/codememory/ internal logic.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import random
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

# Ensure codememory package is importable
_CODEMEMORY_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_CODEMEMORY_SRC) not in sys.path:
    sys.path.insert(0, str(_CODEMEMORY_SRC))

from codememory.handlers import handle_create, handle_resolve, handle_update, handle_wander  # noqa: E402
from codememory.index import load_index, reindex  # noqa: E402
from codememory.validate import validate  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"

MEMORY_ROOT = Path(
    os.environ.get("CODEMEMORY_ROOT", _EXAMPLES_DIR / "investment")
).resolve()


def _get_index_path() -> Path:
    return MEMORY_ROOT / ".codememory" / "index.json"


def _get_available_datasets() -> list[dict[str, str]]:
    """Scan examples/ directory for valid datasets (directories with .codememory/index.json)."""
    datasets: list[dict[str, str]] = []
    if not _EXAMPLES_DIR.exists():
        return datasets
    for entry in sorted(_EXAMPLES_DIR.iterdir()):
        if not entry.is_dir():
            continue
        idx = entry / ".codememory" / "index.json"
        if idx.exists():
            # Try to read memory count from index
            try:
                with open(idx, "r", encoding="utf-8") as f:
                    data = json.load(f)
                count = len(data.get("memories", {}))
            except Exception:
                count = 0
            datasets.append({"name": entry.name, "path": str(entry.resolve()), "memory_count": count})
    return datasets


# Remove the stale INDEX_PATH constant — use _get_index_path() instead
INDEX_PATH = _get_index_path()  # kept for backward compat, but callers should use _get_index_path()

app = FastAPI(title="CodeMemory API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class DateEncoder(json.JSONEncoder):
    """Handle datetime.date objects from YAML parsing."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def _load_index() -> dict[str, Any]:
    """Load index.json as a plain dict."""
    ip = _get_index_path()
    if not ip.exists():
        return {"memories": {}}
    with open(ip, "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_frontmatter(filepath: Path) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter and body from a markdown file."""
    try:
        content = filepath.read_text(encoding="utf-8-sig")
    except Exception:
        return {}, ""

    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_str = parts[1]
    body = parts[2].strip()

    try:
        metadata = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError:
        metadata = {}

    # Convert date objects to strings (pitfall: YAML parses dates as datetime.date)
    for key, value in list(metadata.items()):
        if isinstance(value, (datetime, date)):
            metadata[key] = value.isoformat()
        elif isinstance(value, list):
            metadata[key] = [
                v.isoformat() if isinstance(v, (datetime, date)) else v
                for v in value
            ]

    return metadata, body


def _serialize(obj: Any) -> Any:
    """Recursively convert datetime.date objects to strings for JSON serialization."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize(v) for v in obj]
    return obj


def _stale_check(memory_id: str, entry: Any) -> bool:
    """Return True if the stored summary_hash does not match the actual body."""
    if hasattr(entry, "path"):
        rel_path = entry.path
    elif isinstance(entry, dict):
        rel_path = entry.get("path", "")
    else:
        return False

    file_path = MEMORY_ROOT / rel_path
    if not file_path.exists():
        return False

    meta, body = _parse_frontmatter(file_path)

    if hasattr(entry, "summary_hash"):
        stored_hash = entry.summary_hash
    elif isinstance(entry, dict):
        stored_hash = entry.get("summary_hash", "")
    else:
        return False

    if not stored_hash:
        return False

    from codememory.core import compute_body_hash
    return str(stored_hash) != compute_body_hash(body)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/")
def root():
    return {"service": "CodeMemory API", "version": "0.1.0"}


@app.get("/api/memories")
def get_memories(offset: int = 0, limit: int = 100):
    """Return summary list of all indexed memories with pagination support."""
    index = _load_index()
    memories = index.get("memories", {})
    result = []
    for mem_id, entry in memories.items():
        # entry could be dict or Pydantic model (pitfall: handle both)
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
        })

    total = len(result)
    # Apply pagination
    paginated = result[offset : offset + limit] if offset >= 0 else result

    return _serialize({
        "memories": paginated,
        "total": total,
        "offset": offset,
        "limit": limit,
    })


# NOTE: backlinks and any future /api/memories/{id}/<suffix> routes MUST be
# registered BEFORE the generic GET /api/memories/{memory_id:path} route below.
# FastAPI matches routes in registration order, and {memory_id:path} greedily
# captures all path segments including "/backlinks" and similar suffixes.

@app.get("/api/memories/{memory_id:path}/backlinks")
def get_backlinks(memory_id: str):
    """Return a list of memories that import (reference) the given memory ID."""
    index = _load_index()
    memories = index.get("memories", {})

    backlinks: list[dict[str, str]] = []

    for other_id, entry in memories.items():
        if other_id == memory_id:
            continue

        # Extract imports from entry
        if hasattr(entry, "model_dump"):
            d = entry.model_dump(mode="json")
        elif isinstance(entry, dict):
            d = entry
        else:
            continue

        imports = d.get("imports", {})
        if not imports:
            continue

        # Check each strength level
        for strength in ("required", "recommended", "related"):
            deps = imports.get(strength, [])
            if not deps:
                continue
            dep_ids: list[str] = []
            for dep in deps:
                if isinstance(dep, dict):
                    dep_ids.append(dep.get("id", ""))
                else:
                    dep_ids.append(str(dep))

            if memory_id in dep_ids:
                backlinks.append({
                    "id": other_id,
                    "strength": strength,
                    "summary": d.get("summary", ""),
                })
                break  # only add once per memory

    return _serialize(backlinks)


@app.get("/api/memories/{memory_id:path}")
def get_memory(memory_id: str):
    """Return full content of a single memory (frontmatter + body)."""
    index = _load_index()
    memories = index.get("memories", {})

    entry = memories.get(memory_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found in index")

    # Resolve file path
    if hasattr(entry, "path"):
        rel_path = entry.path
    elif isinstance(entry, dict):
        rel_path = entry.get("path", "")
    else:
        raise HTTPException(status_code=500, detail="Invalid index entry format")

    if not rel_path:
        # Fallback: construct path from ID
        rel_path = f"{memory_id}.md"

    filepath = MEMORY_ROOT / rel_path
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Memory file not found: {rel_path}")

    meta, body = _parse_frontmatter(filepath)

    result = {
        "id": memory_id,
        "body": body,
        **{k: v for k, v in meta.items()},
    }

    return _serialize(result)


# ---------------------------------------------------------------------------
# Helper: direct frontmatter field updates (for tags/intensity not supported
# by handle_update)
# ---------------------------------------------------------------------------

def _update_frontmatter_fields(filepath: Path, updates: dict[str, Any]) -> None:
    """Update specific frontmatter fields in a markdown file directly.

    Used for tags and intensity changes that don't need version tracking.
    """
    content = filepath.read_text(encoding="utf-8-sig")
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("File does not have valid YAML frontmatter")

    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2]

    for key, value in updates.items():
        meta[key] = value

    yaml_str = yaml.dump(meta, allow_unicode=True, sort_keys=False)
    new_content = f"---\n{yaml_str}---\n{body}"
    filepath.write_text(new_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Management endpoints (Task 1: create / update / stats / wander / validate)
# ---------------------------------------------------------------------------

class CreateMemoryRequest(BaseModel):
    id: str = Field(description="Memory identifier (e.g. 'user/ideas/thesis')")
    summary: str = Field(default="TODO: fill in summary")
    tags: list[str] = Field(default_factory=list)
    intensity: int = Field(default=5, ge=1, le=10)
    body: str = Field(default="")
    type: str = Field(default="atom", description="atom | schema")
    schema: str | None = None
    maturity: str = Field(default="draft")
    imports: dict[str, list[str]] | None = Field(
        default=None,
        description="Dependency map by strength: {'required': ['user/ideas/a'], 'recommended': ['user/facts/b']}",
    )

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Ensure memory ID has the required format: non-empty and contains at least one '/'."""
        v = v.strip()
        if not v:
            raise ValueError("Memory ID must not be empty")
        if "/" not in v:
            raise ValueError('Memory ID must contain at least one "/" separator (e.g. "user/ideas/my-thesis")')
        return v


@app.post("/api/memories")
def post_create_memory(req: CreateMemoryRequest):
    """Create a new memory via handle_create, then reindex and return the
    created memory's full data."""
    # Delegate to handlers.py for business logic
    file_path_str = handle_create(
        root=MEMORY_ROOT,
        memory_type=req.type,
        memory_id=req.id,
        schema=req.schema,
        intensity=req.intensity,
        tags=req.tags,
        dry_run=False,
        maturity=req.maturity,
    )

    filepath = Path(file_path_str)
    if not filepath.exists():
        raise HTTPException(status_code=500, detail="Memory file was not created")

    # Customize the created file: always write body to ensure summary_hash matches
    meta, _ = _parse_frontmatter(filepath)
    needs_summary_update = req.summary and req.summary != "TODO: fill in summary"
    if needs_summary_update:
        meta["summary"] = req.summary

    # PL1-9: write imports to frontmatter if provided
    if req.imports:
        meta["imports"] = req.imports

    from codememory.core import compute_body_hash
    body_to_write = req.body  # may be empty (valid minimal memory)
    meta["summary_hash"] = compute_body_hash(body_to_write.strip())

    yaml_str = yaml.dump(meta, allow_unicode=True, sort_keys=False)
    new_content = f"---\n{yaml_str}---\n{body_to_write}"
    filepath.write_text(new_content, encoding="utf-8")

    # Reindex to pick up the new memory
    reindex(MEMORY_ROOT)

    # Return the created memory as structured data
    meta, body = _parse_frontmatter(filepath)
    result = {
        "id": req.id,
        "body": body,
        **{k: v for k, v in meta.items()},
    }
    return _serialize(result)


class UpdateMemoryRequest(BaseModel):
    body: str | None = None
    summary: str | None = None
    tags: list[str] | None = None
    intensity: int | None = Field(default=None, ge=1, le=10)
    status: str | None = None
    maturity: str | None = None
    change_note: str | None = None
    imports: dict[str, list[str]] | None = None


@app.put("/api/memories/{memory_id:path}")
def put_update_memory(memory_id: str, req: UpdateMemoryRequest):
    """Update an existing memory. Delegates to handle_update for core fields,
    directly edits frontmatter for tags/intensity, then reindexes."""
    index = _load_index()
    memories = index.get("memories", {})
    entry = memories.get(memory_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")

    if hasattr(entry, "path"):
        filepath = MEMORY_ROOT / entry.path
    elif isinstance(entry, dict):
        filepath = MEMORY_ROOT / entry.get("path", f"{memory_id}.md")
    else:
        filepath = MEMORY_ROOT / f"{memory_id}.md"

    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Memory file not found on disk")

    # Determine which update strategy to use
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
    ])

    # Use handle_update for core fields (version tracking, change_log, etc.)
    if has_core_update:
        change_note = req.change_note or "API update"
        handle_update(
            root=MEMORY_ROOT,
            memory_id=memory_id,
            body=req.body,
            summary=req.summary,
            change_note=change_note,
            status=req.status,
        )

    # Directly update tags/intensity/imports in frontmatter
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
        _update_frontmatter_fields(filepath, meta_updates)

    # Reindex to pick up changes
    reindex(MEMORY_ROOT)

    # Return updated memory
    meta, body = _parse_frontmatter(filepath)
    result = {
        "id": memory_id,
        "body": body,
        **{k: v for k, v in meta.items()},
    }
    return _serialize(result)


@app.get("/api/stats")
def get_stats():
    """Return memory statistics: total count, maturity distribution, stale
    count, and tag frequencies."""
    index = _load_index()
    memories = index.get("memories", {})

    total = 0
    maturity_counts: dict[str, int] = {}
    stale_count = 0
    stale_ids: list[str] = []
    tag_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}

    for mem_id, entry in memories.items():
        total += 1

        # Extract entry data
        if hasattr(entry, "model_dump"):
            d = entry.model_dump(mode="json")
        elif isinstance(entry, dict):
            d = entry
        else:
            continue

        # Maturity
        maturity = d.get("maturity", "draft")
        maturity_counts[maturity] = maturity_counts.get(maturity, 0) + 1

        # Type
        mem_type = d.get("type", "atom")
        type_counts[mem_type] = type_counts.get(mem_type, 0) + 1

        # Status
        status = d.get("status", "active")
        status_counts[status] = status_counts.get(status, 0) + 1

        # Tags
        for tag in d.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Stale check
        if _stale_check(mem_id, entry):
            stale_count += 1
            stale_ids.append(mem_id)

    # Sort tag_counts by frequency descending
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

    return _serialize({
        "total": total,
        "maturity": maturity_counts,
        "type": type_counts,
        "status": status_counts,
        "stale_count": stale_count,
        "stale_ids": stale_ids,
        "tags": [{"tag": t, "count": c} for t, c in sorted_tags],
    })


class WanderRequest(BaseModel):
    tags: list[str] | None = None
    mode: str = Field(default="cool", description="cool | random")


@app.post("/api/wander")
def post_wander(req: WanderRequest = WanderRequest()):
    """Return a cold memory via weighted random selection.

    Wander logic (per plan): pick from low-access-count memories, weighted by
    intensity. Delegates to handle_wander and parses the result for the API.
    """
    # Use handle_wander for the core wander logic (delegates to handlers.py)
    wander_text = handle_wander(
        root=MEMORY_ROOT,
        tags=req.tags,
        mode=req.mode,
    )

    # Parse the wander output to extract the memory ID and structured info.
    # handle_wander returns formatted text; we also load the index to get
    # structured data for the API response.
    index = load_index(MEMORY_ROOT)
    memories = index.memories

    # Extract the selected memory ID from the wander text
    # Format: "# Wander [cool]: memory_id  [tags]" or "# Wander [random]: ..."
    match = re.search(r"# Wander .+?: (\S+)", wander_text)
    if match:
        selected_id = match.group(1)
        entry = memories.get(selected_id)
        if entry:
            return _serialize({
                "id": selected_id,
                "type": entry.type,
                "summary": entry.summary,
                "tags": entry.tags,
                "intensity": entry.intensity,
                "access_count": entry.access_count,
                "status": entry.status,
                "maturity": entry.maturity,
            })

    # Fallback: implement wander directly if handle_wander parsing fails
    candidates = list(memories.items())
    if req.tags:
        candidates = [
            (mid, e) for mid, e in candidates
            if all(t in e.tags for t in req.tags)
        ]
    if not candidates:
        raise HTTPException(status_code=404, detail="No matching memories found")

    if req.mode == "cool":
        cool = [(mid, e) for mid, e in candidates if e.intensity < 8]
        if not cool:
            cool = candidates
        weights = [1.0 / (e.access_count + 1) for _mid, e in cool]
        mid, entry = random.choices(cool, weights=weights, k=1)[0]
    else:
        mid, entry = random.choice(candidates)

    return _serialize({
        "id": mid,
        "type": entry.type,
        "summary": entry.summary,
        "tags": entry.tags,
        "intensity": entry.intensity,
        "access_count": entry.access_count,
        "status": entry.status,
        "maturity": entry.maturity,
    })


class ValidateRequest(BaseModel):
    pass  # no parameters needed; validates all memories


@app.post("/api/validate")
def post_validate(req: ValidateRequest = ValidateRequest()):
    """Run integrity checks on all indexed memories. Returns structured
    list of errors and warnings.

    Delegates to the validate module from codememory for business logic.
    """
    # Capture stdout from validate() which prints diagnostics
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        error_count, warning_count = validate(MEMORY_ROOT)

    output = captured.getvalue()

    # Parse the captured output to build structured lists
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("[ERROR]"):
            errors.append({
                "type": "error",
                "message": line.removeprefix("[ERROR]").strip(),
            })
        elif line.startswith("[WARNING]"):
            warnings.append({
                "type": "warning",
                "message": line.removeprefix("[WARNING]").strip(),
            })
        elif line.startswith("[MATURITY-WARN]"):
            warnings.append({
                "type": "maturity",
                "message": line.removeprefix("[MATURITY-WARN]").strip(),
            })
        elif line.startswith("[DECAY-WARN]"):
            warnings.append({
                "type": "decay",
                "message": line.removeprefix("[DECAY-WARN]").strip(),
            })

    # Count how many memories were actually scanned
    index = _load_index()
    validated_count = len(index.get("memories", {}))

    return _serialize({
        "validated_count": validated_count,
        "error_count": error_count,
        "warning_count": warning_count,
        "errors": errors,
        "warnings": warnings,
    })


# ---------------------------------------------------------------------------
# Graph endpoint (existing)
# ---------------------------------------------------------------------------


@app.get("/api/graph")
def get_graph():
    """Build cytoscape-compatible nodes + edges from index.json."""
    index = _load_index()
    memories = index.get("memories", {})

    nodes = []
    edges = []
    seen_ids = set()

    for mem_id, entry in memories.items():
        if hasattr(entry, "model_dump"):
            d = entry.model_dump(mode="json")
        elif hasattr(entry, "dict"):
            d = entry.dict()
        else:
            d = dict(entry) if isinstance(entry, dict) else {}

        seen_ids.add(mem_id)

        # Determine directory for color grouping
        directory = "/".join(mem_id.split("/")[:-1]) if "/" in mem_id else ""
        top_dir = mem_id.split("/")[0] if "/" in mem_id else mem_id

        nodes.append({
            "data": {
                "id": mem_id,
                "label": d.get("summary", mem_id),
                "type": d.get("type", "atom"),
                "intensity": d.get("intensity", 5),
                "maturity": d.get("maturity", "draft"),
                "group": top_dir,
                "directory": directory,
                "tags": d.get("tags", []),
                "status": d.get("status", "active"),
            }
        })

    # Build edges from imports
    for mem_id, entry in memories.items():
        if hasattr(entry, "model_dump"):
            d = entry.model_dump(mode="json")
        elif hasattr(entry, "dict"):
            d = entry.dict()
        else:
            d = dict(entry) if isinstance(entry, dict) else {}

        imports = d.get("imports", {})
        if not imports:
            continue

        for strength in ("required", "recommended", "related"):
            deps = imports.get(strength, [])
            if not deps:
                continue
            if isinstance(deps[0], dict):
                dep_ids = [dep.get("id", "") for dep in deps]
            else:
                dep_ids = deps

            for dep_id in dep_ids:
                if not dep_id:
                    continue
                edges.append({
                    "data": {
                        "id": f"{mem_id}->{dep_id}",
                        "source": mem_id,
                        "target": dep_id,
                        "strength": strength,
                    }
                })

    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# Resolve endpoint (Sprint 12)
# ---------------------------------------------------------------------------

class ResolveRequest(BaseModel):
    id: str = Field(description="Target memory ID to resolve from")
    depth: str = Field(default="recommended", description="required | recommended | full")
    budget: int = Field(default=2000, description="Token budget in characters", ge=200, le=5000)


@app.post("/api/resolve")
def post_resolve(req: ResolveRequest):
    """Resolve a memory context via DAG. Returns structured node list + full text.

    Delegates to the existing codememory resolve handler — does NOT reimplement
    DAG construction, topological sort, or token trimming logic.
    """
    # B3: check that the target ID exists in the index before resolving
    index = _load_index()
    memories = index.get("memories", {})
    if req.id not in memories:
        raise HTTPException(status_code=404, detail=f"Memory '{req.id}' not found in index")

    text = handle_resolve(
        root=MEMORY_ROOT,
        memory_id=req.id,
        depth=req.depth,
        budget=req.budget,
    )

    # Parse the resolve text to extract structured node information
    nodes: list[dict[str, Any]] = []
    lines = text.split("\n")
    i = 0

    # Skip preamble lines (title, budget info)
    while i < len(lines):
        line = lines[i]
        if line.startswith("## ["):
            break
        i += 1

    # Parse node sections
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

        # Determine trim level from the parenthetical info
        if "SKIPPED" in node_info:
            trim = "skipped"
            node_type = node_info.replace("SKIPPED - budget", "").strip().rstrip(",").strip() or "atom"
        elif "SUMMARY" in node_info:
            trim = "summary"
            # Extract type before " - SUMMARY"
            node_type = node_info.split(" - SUMMARY")[0].strip() or "atom"
        else:
            trim = "full"
            node_type = node_info

        # Collect body lines until the next section or end marker
        body_lines: list[str] = []
        i += 2  # skip the blank line after header
        while i < len(lines):
            next_line = lines[i]
            if next_line.startswith("## [") or next_line.startswith("---"):
                break
            body_lines.append(next_line)
            i += 1

        body_text = "\n".join(body_lines).strip()

        nodes.append({
            "id": node_id,
            "type": node_type,
            "trim": trim,
            "index": node_index,
            "total": node_total,
            "body": body_text,
        })

        # Skip the "---" separator and "Total Budget Used" line
        if i < len(lines) and lines[i].startswith("---"):
            break

    # Parse pinned version notices from the resolve output
    notice_lines = [ln.strip() for ln in lines if ln.strip().startswith("[NOTICE]")]
    notices = [ln.removeprefix("[NOTICE]").strip() for ln in notice_lines]

    return {
        "target": req.id,
        "depth": req.depth,
        "budget": req.budget,
        "nodes": nodes,
        "full_text": text,
        "notices": notices,
    }


# ---------------------------------------------------------------------------
# Search endpoint (R4-search-ui)
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str = Field(default="", description="Free-text search query for body and summary")
    tags: list[str] | None = None
    type_: str | None = Field(default=None, alias="type")
    status: str | None = None
    maturity: str | None = None
    limit: int = Field(default=50, description="Maximum number of results to return", ge=1, le=500)


@app.post("/api/search")
def post_search(req: SearchRequest):
    """Full-text search across memory body content and metadata.
    Returns ranked results with ID, summary, and matching body snippet.
    """
    # B5: empty query means "no search performed" — short-circuit immediately
    if not req.query or not req.query.strip():
        return _serialize({"results": [], "count": 0, "total": 0, "query": req.query, "limit": req.limit})

    from codememory.search import search

    results = search(
        MEMORY_ROOT,
        query=req.query if req.query else None,
        tags=req.tags,
        type_=req.type_,
        status=req.status,
        maturity=req.maturity,
    )

    # Apply limit before enrichment (snippet extraction is expensive)
    results = results[:req.limit]

    # Enrich results with a body snippet showing the match context
    enriched = []
    for r in results:
        mem_id = r.get("id", "")
        snippet = ""
        # Try to extract a body snippet containing the query
        if req.query and mem_id:
            index = _load_index()
            memories = index.get("memories", {})
            entry = memories.get(mem_id)
            if entry:
                if hasattr(entry, "path"):
                    rel_path = entry.path
                elif isinstance(entry, dict):
                    rel_path = entry.get("path", "")
                else:
                    rel_path = ""
                if rel_path:
                    filepath = MEMORY_ROOT / rel_path
                    if filepath.exists():
                        _, body = _parse_frontmatter(filepath)
                        if body:
                            q_lower = req.query.lower()
                            body_lower = body.lower()
                            idx = body_lower.find(q_lower)
                            if idx >= 0:
                                start = max(0, idx - 40)
                                end = min(len(body), idx + len(req.query) + 60)
                                prefix = "..." if start > 0 else ""
                                suffix = "..." if end < len(body) else ""
                                snippet = prefix + body[start:end].replace("\n", " ") + suffix
                            else:
                                snippet = body[:120].replace("\n", " ") + ("..." if len(body) > 120 else "")
        enriched.append({
            "id": mem_id,
            "summary": r.get("summary", ""),
            "type": r.get("type", "atom"),
            "tags": r.get("tags", []),
            "intensity": r.get("intensity", 5),
            "maturity": r.get("maturity", "draft"),
            "status": r.get("status", "active"),
            "snippet": snippet,
        })

    return _serialize({"results": enriched, "count": len(enriched), "total": len(enriched), "query": req.query, "limit": req.limit})


# ---------------------------------------------------------------------------
# Reindex endpoint (R4-reindex-ui)
# ---------------------------------------------------------------------------

@app.post("/api/reindex")
def post_reindex():
    """Rebuild the index from all .md files on disk."""
    try:
        reindex(MEMORY_ROOT)
        idx = _load_index()
        return {"status": "ok", "count": len(idx.get("memories", {}))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Dataset switching endpoints (R4-backend-default)
# ---------------------------------------------------------------------------

@app.get("/api/datasets")
def get_datasets():
    """List available datasets found in examples/ directory."""
    current = MEMORY_ROOT.resolve()
    datasets = _get_available_datasets()
    return _serialize({
        "datasets": datasets,
        "current": str(current),
        "current_name": current.name,
    })


class SwitchDatasetRequest(BaseModel):
    name: str = Field(description="Dataset name (e.g. 'investment' or 'software-architecture')")


@app.post("/api/datasets/switch")
def post_switch_dataset(req: SwitchDatasetRequest):
    """Switch the active dataset and reindex automatically."""
    global MEMORY_ROOT

    new_root = (_EXAMPLES_DIR / req.name).resolve()
    if not new_root.exists():
        raise HTTPException(status_code=404, detail=f"Dataset '{req.name}' not found in examples/")
    idx = new_root / ".codememory" / "index.json"
    if not idx.exists():
        raise HTTPException(status_code=404, detail=f"Dataset '{req.name}' has no .codememory/index.json")

    MEMORY_ROOT = new_root

    # Reindex the new dataset
    reindex(MEMORY_ROOT)

    # Return stats for the new dataset
    return get_stats()


# ---------------------------------------------------------------------------
# Entry point: run with `python backend/server.py`
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    print(f"CodeMemory API starting on http://localhost:8000")
    print(f"Memory root: {MEMORY_ROOT}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
