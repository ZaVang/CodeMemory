"""LLMTool — "给LLM一个prompt，拿回结果"通用模式。

项目层只需要指定模板和模型级别，通用模式由LLMTool处理：
模板渲染、LLM调用、版本追踪。
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from ..gateway import GatewayBase
from ..prompt_engine import PromptEngine
from ..sandbox import ToolDefinition


class LLMTool:
    """通用的LLM调用工具。

    Usage:
        tool = LLMTool(
            name="reasoner",
            description="运行深度推理",
            prompt_template="predict.j2",
            model_tier="smart",
            gateway=gateway,
            prompt_engine=prompt_engine,
        )
        # 注册到sandbox:
        await sandbox.register(tool.definition, tool.handle)
    """

    def __init__(
        self,
        name: str,
        description: str,
        prompt_template: str,
        gateway: GatewayBase,
        prompt_engine: PromptEngine,
        model_tier: str = "smart",
        tools: list[dict[str, Any]] | None = None,
        sources_parser: Optional[Callable[[list[dict[str, Any]]], list[dict[str, Any]]]] = None,
    ) -> None:
        self.name = name
        self.prompt_template = prompt_template
        self.model_tier = model_tier
        self._gateway = gateway
        self._prompt_engine = prompt_engine
        self._tools = tools
        self._sources_parser = sources_parser
        self.definition = ToolDefinition(name=name, description=description)

    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        """渲染prompt → 调LLM → 返回结果。"""
        prompt = self._prompt_engine.render(self.prompt_template, payload)
        prompt_version = self._prompt_engine.get_version(self.prompt_template)

        response = await self._gateway.chat(
            messages=[{"role": "user", "content": prompt}],
            model_tier=self.model_tier,
            tools=self._tools,
        )

        result: dict[str, Any] = {
            "content": response.content,
            "model": response.model,
            "usage": response.usage,
            "latency_ms": response.latency_ms,
            "prompt_version": prompt_version,
            "thinking": response.thinking,
        }

        # Extract sources from content_blocks if parser is provided
        if response.content_blocks is not None:
            result["content_blocks"] = response.content_blocks
            if self._sources_parser is not None:
                result["sources"] = self._sources_parser(response.content_blocks)
            else:
                result["sources"] = []
        else:
            result["sources"] = []

        return result