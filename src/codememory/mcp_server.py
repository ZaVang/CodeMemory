"""Root-bound MCP server for CodeMemory's shared agent tool surface.

Transport is JSON-RPC 2.0 over stdio. ``CODEMEMORY_ROOT`` is mandatory;
schemas never allow a caller-controlled root.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from codememory.agent_tools import dispatch_agent_tool, standard_tool_specs, tool_specs_for_root


_logger = logging.getLogger("codememory.mcp_server")

MCP_VERSION = "2024-11-05"
SERVER_NAME = "codememory-mcp"
SERVER_VERSION = "0.1.0"


def _mcp_tools_for_root(root: Path) -> list[dict[str, Any]]:
    """Adapt the shared provider-neutral catalog to MCP tool definitions."""

    return [
        {
            "name": spec.name,
            "description": spec.description,
            "inputSchema": spec.input_schema,
            "readOnlyHint": spec.read_only,
        }
        for spec in tool_specs_for_root(root.resolve())
    ]


# Compatibility for code that inspects the standard catalog at import time.
# Runtime ``tools/list`` always resolves the explicitly bound root.
TOOLS = [
    {
        "name": spec.name,
        "description": spec.description,
        "inputSchema": spec.input_schema,
        "readOnlyHint": spec.read_only,
    }
    for spec in standard_tool_specs()
]


def _get_root_from_env() -> Path:
    """Resolve the explicit MCP instance root."""

    value = os.environ.get("CODEMEMORY_ROOT", "")
    if not value:
        raise RuntimeError(
            "CODEMEMORY_ROOT environment variable is required for explicit MCP instance binding."
        )
    root = Path(value)
    if not root.exists():
        raise RuntimeError("CODEMEMORY_ROOT path does not exist")
    if not root.is_dir():
        raise RuntimeError("CODEMEMORY_ROOT must be a directory")
    return root.resolve()


def _call_tool(name: str, arguments: dict[str, Any]) -> list[dict[str, str]]:
    """Dispatch one MCP tool through the shared root-bound handler facade."""

    try:
        result = dispatch_agent_tool(_get_root_from_env(), name, arguments)
        return [{"type": "text", "text": result}]
    except Exception as exc:
        return [{"type": "text", "text": f"Error calling '{name}': {exc}"}]


def _send_response(response_id: str | int, result: dict[str, Any]) -> None:
    message = json.dumps({"jsonrpc": "2.0", "id": response_id, "result": result})
    sys.stdout.write(message + "\n")
    sys.stdout.flush()


def _send_error(response_id: str | int | None, code: int, message: str) -> None:
    payload = {
        "jsonrpc": "2.0",
        "id": response_id,
        "error": {"code": code, "message": message},
    }
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def _send_notification(method: str, params: dict[str, Any] | None = None) -> None:
    payload = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def _handle_request(request: dict[str, Any]) -> None:
    """Process one MCP JSON-RPC request."""

    request_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params", {})

    if method == "initialize":
        _send_response(
            request_id,
            {
                "protocolVersion": MCP_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        )
        _send_notification("notifications/initialized")
    elif method == "notifications/initialized":
        return
    elif method == "tools/list":
        _send_response(request_id, {"tools": _mcp_tools_for_root(_get_root_from_env())})
    elif method == "tools/call":
        name = params.get("name", "")
        arguments = params.get("arguments", {})
        content = _call_tool(name, arguments)
        is_error = bool(content and content[0]["text"].startswith("Error calling"))
        _send_response(request_id, {"content": content, "isError": is_error})
    elif method == "ping":
        _send_response(request_id, {})
    else:
        _send_error(request_id, -32601, f"Method not found: {method}")


def main() -> None:
    """Run the MCP stdio loop after validating the explicit root."""

    logging.basicConfig(
        level=logging.WARNING,
        stream=sys.stderr,
        format="%(levelname)s: %(message)s",
    )
    try:
        _get_root_from_env()
    except RuntimeError as exc:
        _logger.error("Startup error: %s", exc)
        raise SystemExit(1) from exc

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
            _logger.exception("Unhandled MCP request error")
            _send_error(request.get("id"), -32603, f"Internal error: {exc}")


if __name__ == "__main__":
    main()
