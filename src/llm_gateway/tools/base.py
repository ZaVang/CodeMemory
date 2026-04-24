"""
LLM Bridge — Tool framework base classes.

Defines ``BridgeTool`` (ABC), ``ToolRegistry``, and the module-level
default registry singleton.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from ..models import ToolParam

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class BridgeTool(ABC):
    """Abstract base class for all bridge tools.

    Subclass this to add new tools.  Two things are required:

    1. **``definition``** — returns a :class:`ToolParam` that describes the
       tool to the LLM (name, description, JSON-Schema input_schema).
    2. **``run(**kwargs)``** — async callable that executes the tool and
       returns a plain string result.

    The bridge passes ``definition`` to the provider and calls ``run`` with
    the arguments the model supplies.
    """

    @property
    @abstractmethod
    def definition(self) -> ToolParam:
        """Return the tool's definition (name, description, input schema)."""
        ...

    @abstractmethod
    async def run(self, **kwargs) -> str:
        """Execute the tool and return a plain-text result.

        Parameters
        ----------
        **kwargs
            Arguments as specified in ``definition.input_schema``.
        """
        ...


# ---------------------------------------------------------------------------
# ToolRegistry
# ---------------------------------------------------------------------------

class ToolRegistry:
    """Name-based registry for :class:`BridgeTool` instances.

    Agents declare which tool *types* they need; the registry instantiates
    them (once) and provides them by name.

    Example
    -------
    .. code-block:: python

        registry = ToolRegistry()
        registry.register(FetchURLTool(headers={"Authorization": "Bearer tok"}))
        registry.register(ReadFileTool(base_dir="/data/project"))

        tools = registry.get_many(["fetch_url", "read_file"])
        response = await bridge.chat(..., tools=tools)
    """

    def __init__(self) -> None:
        self._tools: dict[str, BridgeTool] = {}

    def register(self, tool: BridgeTool) -> None:
        """Register a tool instance under its ``definition.name``."""
        name = tool.definition.name
        self._tools[name] = tool
        logger.debug("ToolRegistry: registered '%s'", name)

    def register_many(self, tools: list[BridgeTool]) -> None:
        """Register multiple tool instances at once."""
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> BridgeTool:
        """Return the tool registered under *name*.

        Raises
        ------
        KeyError
            If no tool with that name has been registered.
        """
        try:
            return self._tools[name]
        except KeyError:
            available = sorted(self._tools)
            raise KeyError(
                f"Tool '{name}' not found in registry. "
                f"Available: {available}"
            ) from None

    def get_many(self, names: list[str]) -> list[BridgeTool]:
        """Return a list of tools by name, in the given order."""
        return [self.get(n) for n in names]

    def list_tools(self) -> list[str]:
        """Return a sorted list of registered tool names."""
        return sorted(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)


# ---------------------------------------------------------------------------
# Module-level default registry (convenience singleton)
# ---------------------------------------------------------------------------

_default_registry: ToolRegistry | None = None


def get_default_registry() -> ToolRegistry:
    """Return (and lazily create) the module-level default :class:`ToolRegistry`."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
    return _default_registry
