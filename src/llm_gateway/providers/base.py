"""
LLM Bridge — Abstract base provider.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Type

from pydantic import BaseModel

if TYPE_CHECKING:
    from ..models import ChatParameters, ToolParam, UnifiedResponse


class BaseProvider(ABC):
    """Interface that every LLM provider adapter must implement."""

    @abstractmethod
    async def chat(
        self,
        model: str,
        messages: list[dict],
        api_key: str,
        *,
        response_model: Optional[Type[BaseModel]] = None,
        params: Optional["ChatParameters"] = None,
        tools: Optional[list["ToolParam"]] = None,
        **kwargs,
    ) -> "tuple[UnifiedResponse, dict]":
        """Send a chat completion request.

        Parameters
        ----------
        model :
            Model identifier passed to the provider SDK (e.g. ``"gpt-4o"``).
        messages :
            OpenAI-style message list: ``[{"role": "user", "content": "…"}]``.
            Tool-result messages follow the OpenAI format (``role="tool"``,
            ``tool_call_id=…``); provider adapters convert to their native
            format before calling the SDK.
        api_key :
            API key for authentication.
        response_model :
            Optional Pydantic model class for structured (JSON) output.
        params :
            Optional ``ChatParameters`` containing temperature, top_p, etc.
        tools :
            Optional list of ``ToolParam`` definitions.  When provided the
            provider passes them to the SDK and parses any ``tool_use`` /
            ``tool_calls`` blocks in the response into
            ``UnifiedResponse.tool_calls``.
        **kwargs :
            Any extra provider-specific arguments.

        Returns
        -------
        tuple[UnifiedResponse, dict]
            (unified_response, raw_response_dict) — ``raw_response_dict`` is the
            provider's SDK response serialized to a plain dict for tracing purposes.
        """
        ...

    @abstractmethod
    async def list_models(self, api_key: str, **kwargs) -> list[str]:
        """Fetch a list of available model IDs from the provider.

        Parameters
        ----------
        api_key : str
            API key for authentication.
        **kwargs :
            Extra optional arguments (e.g. project, location for Vertex AI).
        """
        ...
