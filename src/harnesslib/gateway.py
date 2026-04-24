"""Gateway — LLM统一调用入口。

harnesslib的Gateway是一个轻量接口层。
实际的多Provider支持、重试、熔断等由 llm_gateway.LLMBridge 提供。

两层关系：
- harnesslib.gateway: 定义GatewayBase接口（通用抽象）
- llm_gateway.LLMBridge: 完整实现（多Provider/重试/熔断/工具调用）
- deepthought层通过 BridgeGateway 适配器连接两者
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel


class GatewayResponse(BaseModel):
    """LLM调用响应（通用层的简化视图）。"""

    content: Optional[str] = None
    model: str
    usage: dict[str, Any]
    latency_ms: int
    content_blocks: list[dict[str, Any]] | None = None
    thinking: Optional[str] = None


class GatewayBase(ABC):
    """LLM统一调用入口（通用层接口）。

    harnesslib只定义这个最小接口。
    具体实现由 llm_gateway.LLMBridge 通过适配器提供。
    """

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        model_tier: str = "smart",
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> GatewayResponse:
        """发送消息，返回响应。

        model_tier: "fast"（降噪/摘要）或 "smart"（深度推理）
        tools: Claude API tools列表（如 web_search），透传给LLMBridge
        """


class BridgeGateway(GatewayBase):
    """将 llm_gateway.LLMBridge 适配为 harnesslib.GatewayBase。

    这是连接harnesslib通用层和llm_gateway的适配器。
    """

    def __init__(self, bridge: Any) -> None:
        """bridge: llm_gateway.LLMBridge 实例。"""
        self._bridge = bridge

    async def chat(
        self,
        messages: list[dict[str, Any]],
        model_tier: str = "smart",
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> GatewayResponse:
        call_kwargs: dict[str, Any] = {**kwargs}
        if tools is not None:
            # Pass raw API tool dicts (e.g. web_search) as api_tools
            # to avoid conflict with bridge's BridgeTool-based tools parameter.
            # api_tools flows through **kwargs → merged_kwargs → provider sdk_kwargs.
            call_kwargs["api_tools"] = tools

        response = await self._bridge.chat(
            model=model_tier,
            messages=messages,
            **call_kwargs,
        )

        # Extract content_blocks from response if available
        content_blocks: list[dict[str, Any]] | None = getattr(
            response, "content_blocks", None
        )

        return GatewayResponse(
            content=response.content,
            model=response.model_id or model_tier,
            usage=response.usage.model_dump() if response.usage else {},
            latency_ms=int(getattr(response, "latency_ms", 0)),
            content_blocks=content_blocks,
            thinking=getattr(response, "thinking", None),
        )