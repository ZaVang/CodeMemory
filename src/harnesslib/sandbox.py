"""Sandbox — 通用执行环境。

所有工具通过 execute(name, payload) -> result 统一接口注册和调用。
不预设具体有哪些工具、每个工具的Schema是什么。
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
    """Sandbox的默认内存实现。"""

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
        self._tools[definition.name] = definition
        self._handlers[definition.name] = handler

    async def execute(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if name not in self._handlers:
            raise KeyError(f"Tool not registered: {name}")
        return await self._handlers[name](payload)

    def list_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())