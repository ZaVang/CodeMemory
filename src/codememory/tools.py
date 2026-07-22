"""Sandbox tool registration — exposes codememory operations to Agent harnesses."""

from __future__ import annotations

from typing import Any

from .core import get_root_dir
from .handlers import (
    handle_build,
    handle_capture,
    handle_changelog,
    handle_create,
    handle_import,
    handle_log,
    handle_orphans,
    handle_read,
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
                "kinds": {"type": "array", "items": {"type": "string", "enum": ["capture", "incubator_topic", "atom"]}},
                "date_from": {"type": "string", "description": "Earliest date (YYYY-MM-DD)"},
                "date_to": {"type": "string", "description": "Latest date (YYYY-MM-DD)"},
                "topic": {"type": "string"},
                "project": {"type": "string"},
                "person": {"type": "string"},
                "origin": {"type": "string"},
                "claim_status": {"type": "string", "description": "Canonical atom claim status only"},
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
    {
        "name": "build_memory",
        "description": "Build canonical context through the imports DAG. Captures and Topics are rejected.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "depth": {"type": "string", "enum": ["required", "recommended", "full"], "default": "recommended"},
                "budget": {"type": "integer"},
                "focus": {"type": "string"},
                "task_goal": {"type": "string"},
                "format": {"type": "string", "enum": ["xml-markdown", "markdown", "plain-markdown", "json"]},
                "root": {"type": "string", "description": "Root directory for memory data"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "capture_memory",
        "description": "Append an immutable Capture to the bound Personal Profile instance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Capture payload"},
                "actor": {"type": "string"},
                "root": {"type": "string", "description": "Root directory for memory data"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "read_memory",
        "description": "Read a Capture or Topic revision by stable ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "root": {"type": "string", "description": "Root directory for memory data"},
            },
            "required": ["id"],
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
                           schema=payload.get("schema"),
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
                            has_schema=payload.get("has_schema", False),
                            kinds=payload.get("kinds"), date_from=payload.get("date_from"),
                            date_to=payload.get("date_to"), topic=payload.get("topic"),
                            project=payload.get("project"), person=payload.get("person"),
                            origin=payload.get("origin"), claim_status=payload.get("claim_status"))
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
    result = handle_orphans(root, type_=payload.get("type"))
    return {"result": result}


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


async def _build_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    result = handle_build(
        root,
        payload["id"],
        depth=payload.get("depth", "recommended"),
        budget=payload.get("budget"),
        focus=payload.get("focus"),
        task_goal=payload.get("task_goal"),
        output_format=payload.get("format", "xml-markdown"),
    )
    return {"result": result}


async def _capture_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    return {"result": handle_capture(root, payload["text"], actor=payload.get("actor"))}


async def _read_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    return {"result": handle_read(root, payload["id"])}


_HANDLER_MAP = {
    "resolve_context": _resolve_handler,
    "create_memory": _create_handler,
    "search_memories": _search_handler,
    "validate_memories": _validate_handler,
    "update_memory": _update_handler,
    "snapshot": _snapshot_handler,
    "find_orphans": _orphans_handler,
    "changelog": _changelog_handler,
    "log": _log_handler,
    "import_memories": _import_handler,
    "build_memory": _build_handler,
    "capture_memory": _capture_handler,
    "read_memory": _read_handler,
}


# ── Registration ──────────────────────────────────────────────────────────────


async def register_all(sandbox, bound_root: str | None = None) -> None:
    """Register all codememory tools with a Sandbox instance."""
    from harnesslib.sandbox import ToolDefinition

    for td in TOOL_DEFINITIONS:
        name = td["name"]
        schema = td.get("input_schema")
        if bound_root is not None and schema:
            schema = {
                **schema,
                "properties": {
                    key: value for key, value in schema.get("properties", {}).items()
                    if key != "root"
                },
            }
        definition = ToolDefinition(
            name=name,
            description=td["description"],
            input_schema=schema,
        )
        handler = _HANDLER_MAP[name]
        if bound_root is not None:
            async def bound_handler(payload, _handler=handler, _root=bound_root):
                clean = dict(payload)
                clean["root"] = _root
                return await _handler(clean)
            await sandbox.register(definition, bound_handler)
        else:
            await sandbox.register(definition, handler)
