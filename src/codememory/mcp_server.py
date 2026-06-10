"""MCP (Model Context Protocol) server for CodeMemory.

Exposes CodeMemory's read/write operations — resolve (build pipeline),
snapshot, propose_memory, propose_update — as callable MCP tools.  Each tool
delegates to the same handlers.py functions used by the CLI and backend API
(no logic duplication).

Transport: stdio (JSON-RPC 2.0), compatible with Claude Code, Cursor, Windsurf,
and any other MCP-compliant client.

Configuration (standard MCP JSON)::

    {
        "codememory": {
            "command": "python",
            "args": ["-m", "codememory.mcp_server"]
        }
    }

Environment::

    CODEMEMORY_ROOT — path to the memory dataset directory (required)
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

# Ensure codememory package is importable when run as `python -m codememory.mcp_server`
_SRC = Path(__file__).resolve().parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from codememory.handlers import (  # noqa: E402 - sys.path is adjusted above for module execution
    handle_create,
    handle_resolve,
    handle_snapshot,
    handle_update,
)

_logger = logging.getLogger("codememory.mcp_server")

# ---------------------------------------------------------------------------
# MCP protocol constants
# ---------------------------------------------------------------------------

MCP_VERSION = "2024-11-05"
SERVER_NAME = "codememory-mcp"
SERVER_VERSION = "0.1.0"

TOOLS = [
    {
        "name": "resolve_memory",
        "description": (
            "Resolve a memory context via DAG traversal. "
            "Performs topological sort of explicit imports-based dependencies "
            "with token-budgeted context assembly. Returns topologically-sorted "
            "context with trim-level annotations (full/summary/skipped) and "
            "token count. This is CodeMemory's core differentiator: deterministic "
            "dependency resolution, not probabilistic similarity."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Target memory ID to resolve (e.g. 'user/investment/context')",
                },
                "depth": {
                    "type": "string",
                    "enum": ["required", "recommended", "full"],
                    "default": "recommended",
                    "description": "Dependency traversal depth",
                },
                "budget": {
                    "type": "integer",
                    "default": 2000,
                    "minimum": 200,
                    "maximum": 5000,
                    "description": "Token budget in characters",
                },
            },
            "required": ["id"],
        },
        "readOnlyHint": True,
    },
    {
        "name": "snapshot",
        "description": (
            "Persist a resolved memory context as a snapshot file in the dataset. "
            "Saves the DAG-resolved context for future reference or sharing. "
            "The snapshot is saved as a markdown file and auto-reindexed."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Snapshot identifier (e.g. 'session-001')",
                },
                "target": {
                    "type": "string",
                    "description": "Optional: resolve a specific memory and snapshot its context",
                },
            },
            "required": ["id"],
        },
        "readOnlyHint": False,
    },
    {
        "name": "propose_memory",
        "description": (
            "Propose a new memory for review. Creates a memory with maturity=draft "
            "and status=proposed, requiring human review before promotion to "
            "verified. Proposed memories do not enter default build/search "
            "results until merged by the owner. "
            "Use this to write new knowledge back to the CodeMemory brain "
            "during agentic reasoning."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Memory identifier (e.g. 'user/ideas/thesis')",
                },
                "summary": {
                    "type": "string",
                    "description": "One-line summary of the memory",
                },
                "body": {
                    "type": "string",
                    "description": "Full body content (Markdown)",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for categorization",
                },
                "intensity": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                    "description": "Importance rating 1-10",
                },
            },
            "required": ["id", "summary", "body"],
        },
    },
    {
        "name": "propose_update",
        "description": (
            "Propose an update to an existing memory. The proposed changes are "
            "stored in the change_log with a '[PROPOSED]' prefix and require "
            "human review before the original memory is modified. "
            "This prevents the Agent from silently overwriting human-curated "
            "memories while still allowing the Agent to contribute corrections, "
            "additions, or clarifications."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Memory identifier to propose an update for",
                },
                "body": {
                    "type": "string",
                    "description": "Proposed new body content (leave empty to keep current)",
                },
                "summary": {
                    "type": "string",
                    "description": "Proposed new summary (leave empty to keep current)",
                },
                "change_note": {
                    "type": "string",
                    "description": "Explanation of the proposed change for human review",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Proposed new tags (leave empty to keep current)",
                },
            },
            "required": ["id", "change_note"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

def _call_tool(name: str, arguments: dict) -> list[dict]:
    """Dispatch a tool call to the appropriate handler. Returns MCP content blocks."""
    root = _get_root_from_env()

    if name == "resolve_memory":
        memory_id = arguments.get("id", "")
        if not memory_id:
            return [{"type": "text", "text": "Error: 'id' parameter is required for resolve_memory"}]
        depth = arguments.get("depth", "recommended")
        budget = arguments.get("budget", 2000)
        result = handle_resolve(root=root, memory_id=memory_id, depth=depth, budget=budget)
        return [{"type": "text", "text": result}]

    elif name == "snapshot":
        snapshot_id = arguments.get("id", "")
        if not snapshot_id:
            return [{"type": "text", "text": "Error: 'id' parameter is required for snapshot"}]
        target = arguments.get("target")
        result = handle_snapshot(root=root, snapshot_id=snapshot_id, target=target)
        return [{"type": "text", "text": result}]

    elif name == "propose_memory":
        memory_id = arguments.get("id", "")
        if not memory_id:
            return [{"type": "text", "text": "Error: 'id' parameter is required for propose_memory"}]
        summary = arguments.get("summary", "")
        body = arguments.get("body", "")
        tags = arguments.get("tags", [])
        intensity = arguments.get("intensity", 5)
        try:
            from codememory.core import compute_body_hash, parse_frontmatter
            import yaml as _yaml
            filepath = handle_create(
                root=root,
                memory_type="atom",
                memory_id=memory_id,
                intensity=intensity,
                tags=tags,
                maturity="draft",
            )
            fp = Path(filepath)
            meta, _ = parse_frontmatter(fp)
            meta["summary"] = summary
            meta["summary_hash"] = compute_body_hash(body.strip())
            meta["status"] = "proposed"
            _yaml_str = _yaml.dump(meta, allow_unicode=True, sort_keys=False)
            fp.write_text(f"---\n{_yaml_str}---\n{body}", encoding="utf-8")
            from codememory.index import reindex as _mcp_reindex
            _mcp_reindex(root)
            return [{"type": "text", "text": (
                f"Memory proposed: {memory_id}\n"
                f"Status: proposed (maturity=draft)\n"
                f"Review required before this memory appears in normal results.\n"
                f"Use the dashboard or CLI to promote maturity from draft to verified."
            )}]
        except Exception as exc:
            return [{"type": "text", "text": f"Error proposing memory '{memory_id}': {exc}"}]

    elif name == "propose_update":
        memory_id = arguments.get("id", "")
        if not memory_id:
            return [{"type": "text", "text": "Error: 'id' parameter is required for propose_update"}]
        change_note = arguments.get("change_note", "")
        if not change_note:
            return [{"type": "text", "text": "Error: 'change_note' is required for propose_update"}]
        try:
            body = arguments.get("body")
            summary = arguments.get("summary")
            # Run the update with the proposed changes; the change_log records
            # the proposal automatically via handle_update.
            # Tags updates are not supported via this tool (use frontend/CLI).
            result_text = handle_update(
                root=root,
                memory_id=memory_id,
                body=body if body else None,
                summary=summary if summary else None,
                change_note=f"[PROPOSED] {change_note}",
            )
            return [{"type": "text", "text": (
                f"Update proposed for: {memory_id}\n"
                f"Change note: {change_note}\n"
                f"Review the change_log entry before accepting.\n"
                f"Result:\n{result_text}"
            )}]
        except Exception as exc:
            return [{"type": "text", "text": f"Error proposing update for '{memory_id}': {exc}"}]

    else:
        return [{"type": "text", "text": f"Unknown tool: {name}"}]


# ---------------------------------------------------------------------------
# Root path resolution
# ---------------------------------------------------------------------------

def _get_root_from_env() -> Path:
    """Resolve the memory root from CODEMEMORY_ROOT environment variable."""
    root = os.environ.get("CODEMEMORY_ROOT", "")
    if not root:
        # Try default relative to the project root
        default = Path(__file__).resolve().parent.parent.parent / "examples" / "companion"
        if default.exists():
            return default
        raise RuntimeError(
            "CODEMEMORY_ROOT environment variable is required. "
            "Set it to a dataset path, e.g. 'examples/companion'"
        )
    p = Path(root)
    if not p.exists():
        raise RuntimeError(f"CODEMEMORY_ROOT path does not exist: {root}")
    return p


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 over stdio
# ---------------------------------------------------------------------------

def _send_response(response_id: str | int, result: dict) -> None:
    """Write a JSON-RPC success response to stdout."""
    msg = json.dumps({"jsonrpc": "2.0", "id": response_id, "result": result})
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def _send_error(response_id: str | int | None, code: int, message: str) -> None:
    """Write a JSON-RPC error response to stdout."""
    msg = json.dumps({
        "jsonrpc": "2.0",
        "id": response_id,
        "error": {"code": code, "message": message},
    })
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def _send_notification(method: str, params: dict | None = None) -> None:
    """Write a JSON-RPC notification (no id) to stdout."""
    msg = json.dumps({"jsonrpc": "2.0", "method": method, "params": params or {}})
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def _handle_request(request: dict) -> None:
    """Process a single JSON-RPC request."""
    req_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params", {})

    if method == "initialize":
        _send_response(req_id, {
            "protocolVersion": MCP_VERSION,
            "capabilities": {
                "tools": {},
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
            },
        })
        # Send initialized notification after initialize response
        _send_notification("notifications/initialized")

    elif method == "notifications/initialized":
        # Client confirmation — ack silently
        pass

    elif method == "tools/list":
        _send_response(req_id, {"tools": TOOLS})

    elif method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        try:
            content = _call_tool(tool_name, tool_args)
            _send_response(req_id, {"content": content})
        except Exception as exc:
            _logger.exception("Tool call failed: %s", tool_name)
            _send_response(req_id, {
                "content": [{"type": "text", "text": f"Error calling '{tool_name}': {exc}"}],
                "isError": True,
            })

    elif method == "ping":
        _send_response(req_id, {})

    else:
        _send_error(req_id, -32601, f"Method not found: {method}")


def main() -> None:
    """Run the MCP server on stdio (stdin/stdout JSON-RPC transport)."""
    # Silence logging to stderr — MCP transport uses stderr for logging
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr, format="%(levelname)s: %(message)s")

    _logger.info("CodeMemory MCP server starting on stdio")

    # Pre-validate root so we fail fast
    try:
        root = _get_root_from_env()
        _logger.info("Memory root: %s", root)
    except RuntimeError as exc:
        _logger.error("Startup error: %s", exc)
        sys.exit(1)

    # JSON-RPC loop: read one line at a time from stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            _send_error(None, -32700, "Parse error")
            continue

        try:
            _handle_request(request)
        except Exception as exc:
            _logger.exception("Unhandled error processing request")
            _send_error(request.get("id"), -32603, f"Internal error: {exc}")


if __name__ == "__main__":
    main()
