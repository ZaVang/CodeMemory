"""Lazy optional ``llm_gateway`` adapter for the semantic importer."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Type

from pydantic import BaseModel

from .llm_proposer import SemanticCallResult


class LLMGatewaySemanticClient:
    """Use structured gateway output without tools or raw-response persistence."""

    def __init__(
        self,
        bridge: Any,
        model: str,
        max_tokens: int = 4096,
        params_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._bridge = bridge
        self._model = model
        self._max_tokens = max_tokens
        self._params_factory = params_factory

    @classmethod
    def from_config(
        cls,
        config_path: str | Path,
        model: str,
        max_tokens: int = 4096,
    ) -> "LLMGatewaySemanticClient":
        from llm_gateway import ChatParameters, LLMBridge

        return cls(
            LLMBridge.from_config(config_path),
            model=model,
            max_tokens=max_tokens,
            params_factory=ChatParameters,
        )

    async def propose(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel],
    ) -> SemanticCallResult:
        if self._params_factory is None:
            from llm_gateway import ChatParameters

            self._params_factory = ChatParameters
        response = await self._bridge.chat(
            model=self._model,
            messages=[{"role": "user", "content": user_prompt}],
            response_model=response_model,
            params=self._params_factory(
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=self._max_tokens,
            ),
        )
        if response.parsed is None:
            raise ValueError("LLM proposer returned no structured output")
        return SemanticCallResult(
            parsed=response.parsed,
            provider=response.provider,
            model=response.model,
            model_id=response.model_id,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.total_tokens,
        )
