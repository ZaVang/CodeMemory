"""DataTool — "获取数据"通用模式。

项目层只需要提供数据源适配器，通用模式由DataTool处理。
"""

from __future__ import annotations

from typing import Any, Callable, Awaitable

from ..sandbox import ToolDefinition


class DataTool:
    """通用的数据获取工具。

    Usage:
        tool = DataTool(
            name="data_fetcher",
            description="获取Barra因子数据",
            adapter=internal_api_adapter,
        )
        await sandbox.register(tool.definition, tool.handle)
    """

    def __init__(
        self,
        name: str,
        description: str,
        adapter: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
    ) -> None:
        self.name = name
        self._adapter = adapter
        self.definition = ToolDefinition(name=name, description=description)

    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        """调用适配器获取数据。"""
        return await self._adapter(payload)