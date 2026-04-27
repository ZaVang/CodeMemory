"""Sandbox — Generic tool execution environment.

All tools are registered and invoked through a unified
``execute(name, payload) -> result`` interface.  The sandbox makes
no assumptions about which tools exist or what their schemas are.

Key classes
-----------
- ``ToolDefinition`` — Pydantic model describing a tool (name, description, input_schema).
- ``SandboxBase`` — Abstract base defining the sandbox contract.
- ``Sandbox`` — Default in-memory implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Awaitable

from pydantic import BaseModel


class ToolDefinition(BaseModel):
    """工具定义——任何可以描述为名称和输入形状的能力。"""

    name: str
    description: str
    input_schema: dict[str, Any] | None = None

    class Config:
        arbitrary_types_allowed = True


class SandboxBase(ABC):
    """通用执行环境。meta-sandbox——不对具体实现做假设。"""

    @abstractmethod
    async def register(
        self,
        definition: ToolDefinition,
        handler: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
    ) -> None:
        """注册一个工具及其handler。"""

    @abstractmethod
    async def execute(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """执行一个已注册的工具。"""

    @abstractmethod
    def list_tools(self) -> list[ToolDefinition]:
        """列出所有已注册的工具。"""


class Sandbox(SandboxBase):
    """Default in-memory Sandbox implementation.

    Stores tool definitions and handlers in dicts.  Suitable for
    single-process agents and testing.

    Examples
    --------
    >>> sandbox = Sandbox()
    >>> await sandbox.register(
    ...     ToolDefinition(name="echo", description="Echo input"),
    ...     handler=lambda p: {"result": p["text"]},
    ... )
    >>> result = await sandbox.execute("echo", {"text": "hi"})
    >>> print(result["result"])
    hi
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._handlers: dict[
            str, Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]
        ] = {}

    async def register(
        self,
        definition: ToolDefinition,
        handler: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
    ) -> None:
        """Register a tool with its async handler.

        Parameters
        ----------
        definition :
            Tool metadata (name, description, optional input_schema).
        handler :
            Async callable receiving a ``dict`` payload and returning a
            ``dict`` result.  Convention: return ``{"result": str}`` for
            text output, or a structured dict for programmatic consumers.
        """
        self._tools[definition.name] = definition
        self._handlers[definition.name] = handler

    async def execute(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a registered tool by name.

        Parameters
        ----------
        name :
            Tool name (must have been registered via ``register()``).
        payload :
            Keyword arguments forwarded to the tool's handler.

        Returns
        -------
        dict
            Whatever the handler returns (typically ``{"result": str}``).

        Raises
        ------
        KeyError
            If the tool name has not been registered.
        """
        if name not in self._handlers:
            raise KeyError(f"Tool not registered: {name}")
        return await self._handlers[name](payload)

    def list_tools(self) -> list[ToolDefinition]:
        """Return all registered tool definitions.

        Returns
        -------
        list[ToolDefinition]
            Tool definitions in registration order.
        """
        return list(self._tools.values())