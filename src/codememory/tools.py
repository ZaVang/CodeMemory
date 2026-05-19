"""Sandbox tool registration — exposes codememory operations to Agent harnesses."""

from __future__ import annotations

from typing import Any

from .core import get_root_dir
from .handlers import (
    handle_changelog,
    handle_create,
    handle_import,
    handle_log,
    handle_orphans,
    handle_overview,
    handle_resolve,
    handle_search,
    handle_update,
    handle_validate,
)
from .snapshot import snapshot_dag
from .transient import TransientDAG


# ── Tool Definitions ──────────────────────────────────────────────────────────

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "resolve_context",
        "description": "Resolve and assemble memory context for a given memory ID via DAG.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Memory ID to resolve"},
                "depth": {"type": "string", "enum": ["required", "recommended", "full"], "default": "required"},
                "budget": {"type": "integer", "description": "Token budget in characters"},
                "focus": {"type": "string", "description": "Keep full text only for nodes with this semantic type tag"},
                "root": {"type": "string", "description": "Root directory for memory data"},
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
                "type": {"type": "string", "enum": ["atom", "schema"], "default": "atom"},
                "id": {"type": "string", "description": "Memory identifier"},
                "schema": {"type": "string", "description": "Schema ID (for atoms with schema)"},
                "intensity": {"type": "integer", "default": 5, "description": "Relevance score 1-10"},
                "dry_run": {"type": "boolean", "default": False},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Custom tags list"},
                "root": {"type": "string", "description": "Root directory for memory data"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "search_memories",
        "description": "Search memories by query, tags, type, status, maturity, and semantic type.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Substring match against summary"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags (AND logic)"},
                "type": {"type": "string", "enum": ["atom", "schema"]},
                "status": {"type": "string", "enum": ["active", "archived", "superseded", "draft"]},
                "maturity": {"type": "string", "enum": ["draft", "verified", "proven", "superseded"]},
                "semantic_type": {"type": "string", "description": "Filter by semantic type tag"},
                "has_imports": {"type": "boolean", "description": "Only show memories with non-empty imports"},
                "has_schema": {"type": "boolean", "description": "Only show memories with a schema reference"},
                "root": {"type": "string", "description": "Root directory for memory data"},
            },
        },
    },
    {
        "name": "validate_memories",
        "description": "Run integrity checks on all indexed memories.",
        "input_schema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "description": "Root directory for memory data"},
            },
        },
    },
    {
        "name": "focus_memory",
        "description": "Focus on a specific memory with adjustable resolution. Supports in-context zoom and auto-resolve.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Memory ID"},
                "level": {"type": "string", "enum": ["full", "summary"], "default": "full"},
                "content": {"type": "string", "description": "Body content for in-context zoom"},
                "summary": {"type": "string", "description": "Summary for in-context zoom"},
                "resolve": {"type": "boolean", "default": False, "description": "Auto-resolve before focusing"},
                "root": {"type": "string", "description": "Root directory for memory data"},
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
                "status": {"type": "string", "enum": ["active", "archived", "superseded", "draft"]},
                "import_required": {"type": "array", "items": {"type": "string"}},
                "import_recommended": {"type": "array", "items": {"type": "string"}},
                "import_related": {"type": "array", "items": {"type": "string"}},
                "root": {"type": "string", "description": "Root directory for memory data"},
            },
            "required": ["id", "change_note"],
        },
    },
    {
        "name": "snapshot",
        "description": "Persist a TransientDAG as an atom .md memory file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Snapshot identifier"},
                "dag_data": {"type": "object", "description": "Serialized TransientDAG"},
                "root": {"type": "string", "description": "Root directory for memory data"},
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
                "type": {"type": "string", "enum": ["atom", "schema"]},
                "min_intensity": {"type": "integer", "description": "Minimum intensity filter"},
                "root": {"type": "string", "description": "Root directory for memory data"},
            },
        },
    },
    {
        "name": "overview",
        "description": "Overview of top relevant memories with heat scores, status annotations, and stale detection.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags (AND logic)"},
                "limit": {"type": "integer", "default": 5, "description": "Max results (default: 5)"},
                "format": {"type": "string", "enum": ["default", "inject"], "default": "default"},
                "status": {"type": "string", "description": "Filter by status"},
                "with_recall": {"type": "boolean", "default": False, "description": "Append wander recall line"},
                "root": {"type": "string", "description": "Root directory for memory data"},
            },
        },
    },
    {
        "name": "changelog",
        "description": "View change history for a memory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Memory ID"},
                "root": {"type": "string", "description": "Root directory for memory data"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "log",
        "description": "View the global operation log (create/update/snapshot/maturity events).",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 20, "description": "Max entries to show"},
                "root": {"type": "string", "description": "Root directory for memory data"},
            },
        },
    },
    {
        "name": "import_memories",
        "description": "Import memories from raw text (cold start). All imports are maturity=draft.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Raw text to extract memories from"},
                "extract_types": {"type": "array", "items": {"type": "string"}, "description": "Tags for extracted memories"},
                "root": {"type": "string", "description": "Root directory for memory data"},
            },
            "required": ["text"],
        },
    },
]


# ── Handlers (thin delegates to handlers.py) ──────────────────────────────────


async def _resolve_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    result = handle_resolve(root, payload["id"], depth=payload.get("depth", "required"),
                           budget=payload.get("budget"), focus=payload.get("focus"))
    return {"result": result}


async def _create_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    result = handle_create(root, memory_type=payload.get("type", "atom"), memory_id=payload["id"],
                           schema=payload.get("schema"), intensity=payload.get("intensity", 5),
                           tags=payload.get("tags"), dry_run=payload.get("dry_run", False),
                           maturity=payload.get("maturity", "draft"))
    return {"result": result}


async def _search_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    results = handle_search(root, query=payload.get("query"), tags=payload.get("tags"),
                            type_=payload.get("type"), status=payload.get("status"),
                            maturity=payload.get("maturity"),
                            semantic_type=payload.get("semantic_type"),
                            has_imports=payload.get("has_imports", False),
                            has_schema=payload.get("has_schema", False))
    return {"result": results}


async def _validate_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    errors = handle_validate(root)
    return {"errors": errors, "result": f"Validation complete. Errors: {errors}"}


async def _update_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    result = handle_update(root, memory_id=payload["id"], body=payload.get("body"),
                           summary=payload.get("summary"), change_note=payload["change_note"],
                           status=payload.get("status"),
                           import_required=payload.get("import_required"),
                           import_recommended=payload.get("import_recommended"),
                           import_related=payload.get("import_related"))
    return {"result": result}


async def _snapshot_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    dag = TransientDAG.from_dict(payload["dag_data"])
    snap_path = snapshot_dag(root, dag, payload["id"])
    return {"result": str(snap_path)}


async def _orphans_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    result = handle_orphans(root, type_=payload.get("type"), min_intensity=payload.get("min_intensity"))
    return {"result": result}


async def _overview_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    result = handle_overview(root, tags=payload.get("tags"), limit=payload.get("limit", 5),
                             format_mode=payload.get("format", "default"),
                             status=payload.get("status"), with_recall=payload.get("with_recall", False))
    return {"result": result}


async def _focus_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    from .core import parse_frontmatter
    from .index import load_index

    # --resolve shortcut
    if payload.get("resolve"):
        content = handle_resolve(root, payload["id"], depth="recommended")
        return {"content": content, "type": "resolved_context"}

    # In-context zoom
    content_override = payload.get("content")
    summary_override = payload.get("summary")
    if content_override is not None and summary_override is not None:
        level = payload.get("level", "full")
        if level == "summary":
            return {"content": summary_override, "type": "in_context"}
        return {"content": content_override, "type": "in_context"}

    # Disk read
    index = load_index(root)
    if payload["id"] not in index.memories:
        return {"error": f"Memory '{payload['id']}' not found"}
    entry = index.memories[payload["id"]]
    file_path = root / entry.path
    meta, body = parse_frontmatter(file_path)
    if payload.get("level") == "summary":
        return {"content": entry.summary or "", "type": entry.type}
    return {"content": body, "type": entry.type, "metadata": meta}


async def _changelog_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    result = handle_changelog(root, payload["id"])
    return {"result": result}


async def _log_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    result = handle_log(root, limit=payload.get("limit", 20))
    return {"result": result}


async def _import_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    result = handle_import(root, text=payload["text"],
                          extract_types=payload.get("extract_types"))
    return {"result": result}


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
    "changelog": _changelog_handler,
    "log": _log_handler,
    "import_memories": _import_handler,
}


# ── Registration ──────────────────────────────────────────────────────────────


async def register_all(sandbox) -> None:
    """Register all codememory tools with a Sandbox instance."""
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
