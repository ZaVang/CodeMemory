"""
LLM Bridge — Google GenAI / Vertex AI provider adapter.

Uses the unified ``google-genai`` SDK.

**Parameter mapping (2026):**
- ``max_tokens`` → ``max_output_tokens`` in ``GenerateContentConfig``
- ``temperature`` → ``temperature``  (0.0–2.0, default varies by model)
- ``top_p`` → ``top_p``  (natively supported)
- ``top_k`` → ``top_k``  (natively supported)
- ``stop_sequences`` → ``stop_sequences``
- ``seed`` → ``seed``
- ``frequency_penalty`` → ``frequency_penalty``
- ``presence_penalty`` → ``presence_penalty``
- ``system_prompt`` → ``system_instruction``

**Structured output:**
Pass ``response_mime_type="application/json"`` and ``response_schema=<PydanticModel>``
in ``GenerateContentConfig``.  Access via ``response.parsed``.

**Response mapping:**
- ``usage_metadata.prompt_token_count`` → ``input_tokens``
- ``usage_metadata.candidates_token_count`` → ``output_tokens``
- ``usage_metadata.total_token_count`` → ``total_tokens``
- ``usage_metadata.thoughts_token_count`` → ``reasoning_tokens``
- ``candidates[0].finish_reason`` → ``stop_reason``
  (values: "STOP", "MAX_TOKENS", "SAFETY", etc.)

AI Studio vs Vertex AI is determined by ``extra`` config:
- AI Studio (default): just provide ``api_key``
- Vertex AI: set ``vertexai=True``, ``project=…``, ``location=…``
"""

from __future__ import annotations

import asyncio
from typing import Optional, Type

from google import genai
from google.genai import types
from pydantic import BaseModel

from ..models import ChatParameters, ToolParam, UnifiedResponse, UsageInfo
from .base import BaseProvider


class GoogleProvider(BaseProvider):
    """Adapter for Google Gemini (AI Studio) and Vertex AI."""

    async def chat(
        self,
        model: str,
        messages: list[dict],
        api_key: str,
        *,
        response_model: Optional[Type[BaseModel]] = None,
        params: Optional[ChatParameters] = None,
        tools: Optional[list[ToolParam]] = None,
        **kwargs,
    ) -> "tuple[UnifiedResponse, dict]":
        p = params or ChatParameters()

        # ── Determine AI Studio vs Vertex AI ──────────────────────
        vertexai = kwargs.pop("vertexai", False)
        project = kwargs.pop("project", None)
        location = kwargs.pop("location", None)

        if vertexai:
            client = genai.Client(
                vertexai=True,
                project=project,
                location=location or "us-central1",
            )
        else:
            client = genai.Client(api_key=api_key)

        # ── Build GenerateContentConfig ───────────────────────────
        gen_config_params: dict = {}

        if p.max_tokens is not None:
            gen_config_params["max_output_tokens"] = p.max_tokens
        if p.temperature is not None:
            gen_config_params["temperature"] = p.temperature
        if p.top_p is not None:
            gen_config_params["top_p"] = p.top_p
        if p.top_k is not None:
            gen_config_params["top_k"] = p.top_k
        if p.stop_sequences is not None:
            gen_config_params["stop_sequences"] = p.stop_sequences
        if p.seed is not None:
            gen_config_params["seed"] = p.seed
        if p.frequency_penalty is not None:
            gen_config_params["frequency_penalty"] = p.frequency_penalty
        if p.presence_penalty is not None:
            gen_config_params["presence_penalty"] = p.presence_penalty
        if p.system_prompt is not None:
            gen_config_params["system_instruction"] = p.system_prompt

        if response_model is not None:
            gen_config_params["response_mime_type"] = "application/json"
            gen_config_params["response_schema"] = response_model
            # Disable thinking for structured output: thinking tokens and the
            # actual JSON response share the same max_tokens budget.  Without
            # this, thinking can consume the entire budget, leaving the JSON
            # truncated and unparseable.
            if hasattr(types, "ThinkingConfig"):
                gen_config_params["thinking_config"] = types.ThinkingConfig(
                    thinking_budget=0
                )

        config = types.GenerateContentConfig(**gen_config_params)

        # ── Attach tool definitions (Google FunctionDeclaration format) ───────
        if tools:
            fn_decls = [
                types.FunctionDeclaration(
                    name=t.name,
                    description=t.description,
                    parameters=t.input_schema,
                )
                for t in tools
            ]
            config.tools = [types.Tool(function_declarations=fn_decls)]

        # ── Convert messages to contents string ───────────────────
        contents = _messages_to_contents(messages)

        # ── Call SDK ──────────────────────────────────────────────
        response = await client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        # ── Map response ──────────────────────────────────────────
        parsed = None
        content_text = None

        if response_model is not None:
            # Try SDK's parsed attribute first; it may be a dict or None.
            sdk_parsed = getattr(response, "parsed", None)
            if isinstance(sdk_parsed, response_model):
                # SDK already instantiated the Pydantic model — ideal path.
                parsed = sdk_parsed
            elif response.text:
                # Fallback: parse the JSON text manually.  Google returns the
                # structured output as plain JSON in response.text even when
                # response_schema is set.
                parsed = response_model.model_validate_json(response.text)

        if response.text:
            content_text = response.text

        # Finish reason & Thinking Text
        stop_reason = None
        thinking_text = None

        if response.candidates:
            raw_reason = getattr(response.candidates[0], "finish_reason", None)
            if raw_reason is not None:
                # google-genai returns an enum; convert to string
                stop_reason = str(raw_reason.name) if hasattr(raw_reason, "name") else str(raw_reason)
            
            # Extract thinking process if present
            if getattr(response.candidates[0], "content", None) and getattr(response.candidates[0].content, "parts", None):
                thoughts = []
                for part in response.candidates[0].content.parts:
                    if getattr(part, "thought", False) and getattr(part, "text", None):
                        thoughts.append(part.text)
                if thoughts:
                    thinking_text = "\n".join(thoughts)

        # Usage metadata
        um = response.usage_metadata
        raw: dict = {
            "model_version": getattr(response, "model_version", None),
            "finish_reason": stop_reason,
            "usage": {
                "prompt_token_count": getattr(um, "prompt_token_count", 0) or 0,
                "candidates_token_count": getattr(um, "candidates_token_count", 0) or 0,
                "total_token_count": getattr(um, "total_token_count", 0) or 0,
                "thoughts_token_count": getattr(um, "thoughts_token_count", 0) or 0,
            },
            "text": content_text,
        }
        return UnifiedResponse(
            provider="google",
            model=model,
            content=content_text,
            parsed=parsed,
            thinking=thinking_text,
            tool_calls=[],  # Google tool_use parsing not yet implemented
            usage=UsageInfo(
                input_tokens=getattr(um, "prompt_token_count", 0) or 0,
                output_tokens=getattr(um, "candidates_token_count", 0) or 0,
                total_tokens=getattr(um, "total_token_count", 0) or 0,
                reasoning_tokens=getattr(um, "thoughts_token_count", 0) or 0,
            ),
            stop_reason=stop_reason,
            model_id=getattr(response, "response_id", None),
        ), raw

    async def list_models(self, api_key: str, **kwargs) -> list[str]:
        vertexai = kwargs.pop("vertexai", False)
        project = kwargs.pop("project", None)
        location = kwargs.pop("location", None)

        if vertexai:
            client = genai.Client(
                vertexai=True,
                project=project,
                location=location or "us-central1",
            )
        else:
            client = genai.Client(api_key=api_key)

        # client.models.list() is synchronous; run it in a thread to avoid
        # blocking the event loop.
        response = await asyncio.to_thread(lambda: list(client.models.list()))
        return [getattr(m, "name", "").replace("models/", "") for m in response]


def _messages_to_contents(messages: list[dict]) -> str:
    """Flatten OpenAI-style message dicts into a single prompt string.

    Google GenAI can accept a plain string for simple use-cases.  For
    multi-turn conversations you may want to build ``types.Content``
    objects instead — this helper keeps the default path simple.
    """
    parts: list[str] = []
    for msg in messages:
        role = msg.get("role", "user")
        text = msg.get("content", "")
        if role == "system":
            parts.append(f"[System]\n{text}")
        elif role == "assistant":
            parts.append(f"[Assistant]\n{text}")
        else:
            parts.append(text)
    return "\n\n".join(parts)