"""Sandbox registration for the shared root-bound agent tool surface."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .agent_tools import dispatch_agent_tool, standard_tool_specs, tool_specs_for_root


def get_tool_definitions(root: str | Path) -> list[dict[str, Any]]:
    """Return provider-neutral definitions for one resolved instance root."""

    bound_root = Path(root).resolve()
    return [spec.as_legacy_dict() for spec in tool_specs_for_root(bound_root)]


# Compatibility for callers that only inspect the standard catalog. Runtime
# registration and Toolkit exports always use ``get_tool_definitions(root)``.
TOOL_DEFINITIONS: list[dict[str, Any]] = [
    spec.as_legacy_dict() for spec in standard_tool_specs()
]


async def register_all(sandbox, bound_root: str | Path | None = None) -> None:
    """Register the exact shared tool profile for a bound CodeMemory root."""

    if bound_root is None:
        raise ValueError("bound_root is required for agent tool registration")

    from harnesslib.sandbox import ToolDefinition

    root = Path(bound_root).resolve()
    for spec in tool_specs_for_root(root):
        definition = ToolDefinition(
            name=spec.name,
            description=spec.description,
            input_schema=spec.input_schema,
        )

        async def bound_handler(
            payload: dict[str, Any],
            *,
            _name: str = spec.name,
            _root: Path = root,
        ) -> dict[str, Any]:
            return {"result": dispatch_agent_tool(_root, _name, payload)}

        await sandbox.register(definition, bound_handler)
