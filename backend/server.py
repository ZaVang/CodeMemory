"""CodeMemory Backend API — FastAPI server.

Reads from the existing codememory index.json and .md files.
Does NOT modify src/codememory/ internal logic.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MEMORY_ROOT = Path(os.environ.get("CODEMEMORY_ROOT", Path(__file__).resolve().parent.parent / "examples" / "investment")).resolve()
INDEX_PATH = MEMORY_ROOT / ".codememory" / "index.json"

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
    if not INDEX_PATH.exists():
        return {"memories": {}}
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
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


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/")
def root():
    return {"service": "CodeMemory API", "version": "0.1.0"}


@app.get("/api/memories")
def get_memories():
    """Return summary list of all indexed memories."""
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

    return _serialize(result)


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
