"""Sandbox tool registration — exposes codememory operations to Agent harnesses."""

from __future__ import annotations

from typing import Any

from .core import get_root_dir
from .create import create
from .orphans import find_orphans
from .resolve import resolve
from .search import search
from .snapshot import snapshot_dag
from .update import update
from .validate import validate


# ── Tool Definitions ──────────────────────────────────────────────────────────

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "resolve_context",
        "description": "Resolve and assemble memory context for a given memory ID via DAG.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Memory ID to resolve"},
                "depth": {
                    "type": "string",
                    "enum": ["required", "recommended", "full"],
                    "default": "required",
                    "description": "How deep to traverse imports",
                },
                "budget": {
                    "type": "integer",
                    "description": "Token budget in characters",
                },
                "root": {
                    "type": "string",
                    "description": "Root directory for memory data",
                },
            },
            "required": ["id"],
        },
    },
    {
        "name": "create_memory",
        "description": "Create a new memory atom with frontmatter template.",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["atom", "schema", "instance", "composite"],
                    "description": "Memory type",
                },
                "id": {"type": "string", "description": "Memory identifier"},
                "schema": {"type": "string", "description": "Schema ID (for instances)"},
                "intensity": {
                    "type": "integer",
                    "default": 5,
                    "description": "Relevance score 1-10",
                },
                "dry_run": {
                    "type": "boolean",
                    "default": False,
                    "description": "Preview without creating file",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Custom tags list",
                },
                "root": {
                    "type": "string",
                    "description": "Root directory for memory data",
                },
            },
            "required": ["type", "id"],
        },
    },
    {
        "name": "search_memories",
        "description": "Search memories by query, tags, type, and status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Substring match against summary"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by tags (AND logic)",
                },
                "type": {
                    "type": "string",
                    "enum": ["atom", "schema", "instance", "composite"],
                    "description": "Filter by memory type",
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "archived", "superseded", "draft"],
                    "description": "Filter by memory status",
                },
                "root": {
                    "type": "string",
                    "description": "Root directory for memory data",
                },
            },
        },
    },
    {
        "name": "validate_memories",
        "description": "Run integrity checks on all indexed memories.",
        "input_schema": {
            "type": "object",
            "properties": {
                "root": {
                    "type": "string",
                    "description": "Root directory for memory data",
                },
            },
        },
    },
    {
        "name": "focus_memory",
        "description": "Focus on a specific memory with adjustable resolution. Supports in-context zoom (--content/--summary) and auto-resolve (--resolve).",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Memory ID to focus on"},
                "level": {
                    "type": "string",
                    "enum": ["full", "summary"],
                    "default": "full",
                    "description": "Resolution level",
                },
                "content": {
                    "type": "string",
                    "description": "Body content for in-context zoom (skip disk read)",
                },
                "summary": {
                    "type": "string",
                    "description": "Summary text for in-context zoom (skip disk read)",
                },
                "resolve": {
                    "type": "boolean",
                    "default": False,
                    "description": "Auto-resolve dependency subgraph before focusing",
                },
                "root": {
                    "type": "string",
                    "description": "Root directory for memory data",
                },
            },
            "required": ["id"],
        },
    },
    {
        "name": "update_memory",
        "description": "Update an existing memory with version control and change tracking.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Memory ID to update"},
                "change_note": {"type": "string", "description": "Explanation of what changed"},
                "body": {"type": "string", "description": "New body text"},
                "summary": {"type": "string", "description": "New summary"},
                "status": {
                    "type": "string",
                    "enum": ["active", "archived", "superseded", "draft"],
                    "description": "New status",
                },
                "import_required": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Replacement required imports",
                },
                "import_recommended": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Replacement recommended imports",
                },
                "import_related": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Replacement related imports",
                },
                "root": {
                    "type": "string",
                    "description": "Root directory for memory data",
                },
            },
            "required": ["id", "change_note"],
        },
    },
    {
        "name": "snapshot",
        "description": "Persist a TransientDAG as a composite .md memory file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Snapshot identifier"},
                "dag_data": {
                    "type": "object",
                    "description": "Serialized TransientDAG (from dag.to_dict())",
                },
                "root": {
                    "type": "string",
                    "description": "Root directory for memory data",
                },
            },
            "required": ["id", "dag_data"],
        },
    },
    {
        "name": "find_orphans",
        "description": "Find orphaned memories with zero in-degree in the dependency graph.",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["atom", "schema", "instance", "composite"],
                    "description": "Filter by memory type",
                },
                "min_intensity": {
                    "type": "integer",
                    "description": "Minimum intensity filter",
                },
                "root": {
                    "type": "string",
                    "description": "Root directory for memory data",
                },
            },
        },
    },
    {
        "name": "overview",
        "description": "Overview of top relevant memories with heat scores, status annotations, and stale detection.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by tags (AND logic)",
                },
                "limit": {
                    "type": "integer",
                    "default": 5,
                    "description": "Max results (default: 5)",
                },
                "format": {
                    "type": "string",
                    "enum": ["default", "inject"],
                    "default": "default",
                    "description": "Output format: 'inject' for compact system-prompt injection",
                },
                "status": {
                    "type": "string",
                    "description": "Filter by status. Default excludes archived. Use 'all' for all.",
                },
                "with_recall": {
                    "type": "boolean",
                    "default": False,
                    "description": "Append a wander recall line at the end",
                },
                "root": {
                    "type": "string",
                    "description": "Root directory for memory data",
                },
            },
        },
    },
]


# ── Handlers ──────────────────────────────────────────────────────────────────


async def _resolve_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    memory_id = payload["id"]
    depth = payload.get("depth", "required")
    budget = payload.get("budget")
    result = resolve(root, memory_id, depth=depth, budget=budget)
    return {"result": result}


async def _create_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    file_path = create(
        root,
        memory_type=payload["type"],
        memory_id=payload["id"],
        schema=payload.get("schema"),
        intensity=payload.get("intensity", 5),
        tags=payload.get("tags"),
        dry_run=payload.get("dry_run", False),
    )
    if file_path is None:
        return {"result": "dry-run: no file created"}
    return {"result": str(file_path)}


async def _search_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    results = search(
        root,
        query=payload.get("query"),
        tags=payload.get("tags"),
        type_=payload.get("type"),
        status=payload.get("status"),
    )
    return {"results": results, "count": len(results)}


async def _validate_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    errors, warnings = validate(root)
    return {"errors": errors, "warnings": warnings}


async def _update_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    file_path = update(
        root,
        memory_id=payload["id"],
        body=payload.get("body"),
        summary=payload.get("summary"),
        change_note=payload["change_note"],
        status=payload.get("status"),
        import_required=payload.get("import_required"),
        import_recommended=payload.get("import_recommended"),
        import_related=payload.get("import_related"),
    )
    return {"result": str(file_path)}


async def _snapshot_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    from .transient import TransientDAG

    dag_data = payload["dag_data"]
    dag = TransientDAG.from_dict(dag_data)
    snap_path = snapshot_dag(root, dag, payload["id"])
    return {"result": str(snap_path)}


async def _orphans_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    orphans = find_orphans(
        root,
        type_=payload.get("type"),
        min_intensity=payload.get("min_intensity"),
    )
    # Format output for Sandbox (returns text, per Sandbox handler convention)
    lines = []
    for o in orphans:
        ann = f"[{o['annotation']}]"
        last = o.get("last_access") or "never"
        lines.append(
            f"{o['id']:45s} {o['type']:9s} "
            f"intensity:{o['intensity']:2d}  "
            f"access:{o['access_count']:3d}  "
            f"last:{last}  {ann}"
        )
    result_text = "\n".join(lines) if lines else "(no orphaned memories)"
    return {"result": result_text}


async def _overview_handler(payload: dict[str, Any]) -> dict[str, Any]:
    import random as _random

    from .core import compute_body_hash as _cbh, parse_frontmatter as _pfm
    from .index import load_index as _load_index

    root = get_root_dir(payload.get("root"))
    results = search(root, tags=payload.get("tags"))

    # Filter by status: exclude archived by default
    status_filter = payload.get("status")
    if status_filter and status_filter != "all":
        results = [r for r in results if r.get("status") == status_filter]
    elif not status_filter or status_filter != "all":
        results = [r for r in results if r.get("status") != "archived"]

    limit = payload.get("limit", 5)
    format_mode = payload.get("format", "default")

    lines = []
    for r in results[:limit]:
        mid = r["id"]
        mem_type = r["type"]
        deps = r.get("dependents", 0)
        access = r.get("access_count", 0)
        heat = deps * 10 + access
        status = r.get("status", "active")
        tags_str = ", ".join(r.get("tags", []))
        summary = r.get("summary", "")

        # Stale detection
        stale = False
        file_path = root / r["path"]
        if file_path.exists():
            meta, body = _pfm(file_path)
            stored_hash = meta.get("summary_hash", "")
            if stored_hash:
                actual_hash = _cbh(body)
                if stored_hash != actual_hash:
                    stale = True

        stale_mark = " [stale]" if stale else ""
        status_mark = f"[{status}]"

        if format_mode == "inject":
            line = (
                f"[{mid}]({mem_type}, heat:{heat}, {status})"
                f"[{tags_str}] {summary}{stale_mark}"
            )
            if len(line) > 120:
                line = line[:117] + "..."
            lines.append(line)
        else:
            lines.append(
                f"{mid:45s} {mem_type:9s} heat:{heat:3d} "
                f"{status_mark}{stale_mark}  [{tags_str}]"
            )
            if summary:
                lines.append(f"    {summary}")

    # --with-recall: append wander inject
    if payload.get("with_recall"):
        _index = _load_index(root)
        _all_mems = _index["memories"]
        _candidates = [
            (_mid, _e)
            for _mid, _e in _all_mems.items()
            if _e.get("intensity", 5) < 8
        ]
        if _candidates:
            _candidates.sort(key=lambda x: x[1].get("access_count", 0))
            _cutoff = max(1, len(_candidates) // 3)
            _pool = _candidates[:_cutoff]
            _mid, _entry = _random.choice(_pool)
            _tags_str = ", ".join(_entry.get("tags", []))
            lines.append(
                f"[recall] {_mid} — {_entry.get('summary', '')}"
                f"（tags: {_tags_str}）"
            )

    return {"result": "\n".join(lines)}


async def _focus_handler(payload: dict[str, Any]) -> dict[str, Any]:
    from .core import parse_frontmatter
    from .index import load_index

    root = get_root_dir(payload.get("root"))
    memory_id = payload["id"]
    level = payload.get("level", "full")

    # --resolve: auto-resolve dependency subgraph first
    if payload.get("resolve"):
        result = resolve(root, memory_id, depth="recommended")
        return {"content": result, "type": "resolved_context"}

    # In-context zoom: use provided content/summary, skip disk read
    content_override = payload.get("content")
    summary_override = payload.get("summary")

    if content_override is not None and summary_override is not None:
        if level == "summary":
            return {"content": summary_override, "type": "in_context"}
        else:
            return {"content": content_override, "type": "in_context"}

    # Default: read from disk (backward compatible)
    index = load_index(root)
    if memory_id not in index["memories"]:
        return {"error": f"Memory '{memory_id}' not found"}

    entry = index["memories"][memory_id]
    file_path = root / entry["path"]
    meta, body = parse_frontmatter(file_path)

    if level == "summary":
        return {"content": entry.get("summary", ""), "type": entry["type"]}
    else:
        return {"content": body, "type": entry["type"], "metadata": meta}


_HANDLER_MAP = {
    "resolve_context": _resolve_handler,
    "create_memory": _create_handler,
    "search_memories": _search_handler,
    "validate_memories": _validate_handler,
    "focus_memory": _focus_handler,
    "update_memory": _update_handler,
    "snapshot": _snapshot_handler,
    "find_orphans": _orphans_handler,
    "overview": _overview_handler,
}


# ── Registration ──────────────────────────────────────────────────────────────


async def register_all(sandbox) -> None:
    """Register all codememory tools with a Sandbox instance.

    Usage:
        from harnesslib.sandbox import Sandbox
        from codememory.tools import register_all

        sandbox = Sandbox()
        await register_all(sandbox)

    Args:
        sandbox: A Sandbox instance implementing register(def, handler) and
                 execute(name, payload) -> result.
    """
    from harnesslib.sandbox import ToolDefinition

    for td in TOOL_DEFINITIONS:
        name = td["name"]
        definition = ToolDefinition(
            name=name,
            description=td["description"],
            input_schema=td.get("input_schema"),
        )
        handler = _HANDLER_MAP[name]
        await sandbox.register(definition, handler)
