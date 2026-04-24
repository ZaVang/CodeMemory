"""Sandbox tool registration — exposes codememory operations to Agent harnesses."""

from __future__ import annotations

from typing import Any

from .core import get_root_dir
from .create import create
from .resolve import resolve
from .search import search
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
        "description": "Search memories by query, tags, and type.",
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
        "description": "Focus on a specific memory with adjustable resolution.",
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
                "root": {
                    "type": "string",
                    "description": "Root directory for memory data",
                },
            },
            "required": ["id"],
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
    )
    return {"path": str(file_path)}


async def _search_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    results = search(
        root,
        query=payload.get("query"),
        tags=payload.get("tags"),
        type_=payload.get("type"),
    )
    return {"results": results, "count": len(results)}


async def _validate_handler(payload: dict[str, Any]) -> dict[str, Any]:
    root = get_root_dir(payload.get("root"))
    errors, warnings = validate(root)
    return {"errors": errors, "warnings": warnings}


async def _focus_handler(payload: dict[str, Any]) -> dict[str, Any]:
    from .core import parse_frontmatter
    from .index import load_index

    root = get_root_dir(payload.get("root"))
    memory_id = payload["id"]
    level = payload.get("level", "full")

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
