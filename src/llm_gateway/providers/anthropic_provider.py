"""
LLM Bridge — Anthropic provider adapter.

Uses the ``anthropic`` SDK.

**Parameter mapping (2026):**
- ``max_tokens`` → ``max_tokens``  (REQUIRED by Anthropic, defaults to 32000)
- ``temperature`` → ``temperature``  (0.0–1.0, default 1.0)
- ``top_k`` → ``top_k``  (natively supported)
- ``top_p`` → ``top_p``  (natively supported)
- ``stop_sequences`` → ``stop_sequences``
- ``system_prompt`` → ``system`` (top-level parameter, NOT a message role)
- ``frequency_penalty`` / ``presence_penalty`` / ``seed`` → NOT supported

**Structured output:**
Uses ``client.beta.messages.parse(response_format=…)`` with the
``anthropic-beta: structured-outputs-2025-11-13`` header.
Returns ``response.parsed_output``.

**Response mapping:**
- ``usage.input_tokens`` → ``input_tokens``
- ``usage.output_tokens`` → ``output_tokens``
- ``usage.cache_creation_input_tokens`` → ``cache_creation_input_tokens``
- ``usage.cache_read_input_tokens`` → ``cache_read_input_tokens``
- ``stop_reason`` → ``stop_reason``  (values: "end_turn", "max_tokens", "stop_sequence")
- ``id`` → ``model_id``  (format: "msg_…")
"""

from __future__ import annotations

import json
from typing import Optional, Type, Union

from anthropic import AsyncAnthropic
from pydantic import BaseModel

from ..models import ChatParameters, ToolCall, ToolParam, UnifiedResponse, UsageInfo
from .base import BaseProvider


class AnthropicProvider(BaseProvider):
    """Adapter for the Anthropic API (Claude Sonnet 4, Claude Opus, etc.)."""

    # Beta header required for structured output support.
    _BETA_HEADER = "structured-outputs-2025-11-13"

    async def chat(
        self,
        model: str,
        messages: list[dict],
        api_key: str,
        *,
        response_model: Optional[Type[BaseModel]] = None,
        params: Optional[ChatParameters] = None,
        tools: Optional[list[Union[ToolParam, dict]]] = None,
        **kwargs,
    ) -> "tuple[UnifiedResponse, dict]":
        client = AsyncAnthropic(api_key=api_key)
        p = params or ChatParameters()

        # ── Build SDK kwargs ──────────────────────────────────────
        sdk_kwargs: dict = {**kwargs}

        # max_tokens is REQUIRED by Anthropic; streaming removes the 10-min limit
        sdk_kwargs["max_tokens"] = p.max_tokens if p.max_tokens is not None else 32000

        if p.temperature is not None:
            sdk_kwargs["temperature"] = p.temperature
        if p.top_k is not None:
            sdk_kwargs["top_k"] = p.top_k
        if p.top_p is not None:
            sdk_kwargs["top_p"] = p.top_p
        if p.stop_sequences is not None:
            sdk_kwargs["stop_sequences"] = p.stop_sequences
        # system prompt is a top-level parameter (NOT a message role)
        if p.system_prompt is not None:
            sdk_kwargs["system"] = p.system_prompt
        # frequency_penalty, presence_penalty, seed → NOT supported by Anthropic

        # ── 15-B1: cache_control breakpoint support ──────────────────────────
        # When cache_system_prompt=True is passed via kwargs, wrap the system
        # prompt as a content block with cache_control: {type: "ephemeral"}.
        # This enables Anthropic prompt caching for subagent perspectives.
        cache_system_prompt = sdk_kwargs.pop("cache_system_prompt", False)
        if cache_system_prompt and "system" in sdk_kwargs:
            system_text = sdk_kwargs["system"]
            if isinstance(system_text, str):
                # Replace plain string with structured content block + cache breakpoint
                sdk_kwargs["system"] = [
                    {
                        "type": "text",
                        "text": system_text,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]

        # ── Convert OpenAI-format tool messages to Anthropic format ──────────
        adapted_messages = _adapt_messages_for_anthropic(messages)

        # ── Attach tool definitions ──────────────────────────────────────────
        # api_tools: raw API tool dicts (e.g. web_search server-side tools)
        # passed through from harnesslib gateway layer
        api_tools = sdk_kwargs.pop("api_tools", None)
        if tools:
            sdk_kwargs["tools"] = [
                (
                    {
                        "name": t.name,
                        "description": t.description,
                        "input_schema": t.input_schema,
                    }
                    if isinstance(t, ToolParam)
                    else t  # raw dict — pass through
                )
                for t in tools
            ]
        if api_tools:
            existing = sdk_kwargs.get("tools", [])
            sdk_kwargs["tools"] = existing + api_tools

        # ── Call SDK (always stream to avoid 10-min non-streaming limit) ─────
        content_text: Optional[str] = None
        thinking_text: Optional[str] = None
        tool_calls: list[ToolCall] = []

        if response_model is not None and not tools:
            # Structured output path (incompatible with tools)
            async with client.beta.messages.stream(
                model=model,
                messages=adapted_messages,
                output_format=response_model,
                betas=[self._BETA_HEADER],
                **sdk_kwargs,
            ) as stream:
                response = await stream.get_final_message()
            parsed = response.parsed_output
            # Anthropic structured output may also carry text blocks
            for block in response.content:
                if hasattr(block, "text"):
                    content_text = block.text
                    break
        else:
            async with client.messages.stream(
                model=model,
                messages=adapted_messages,
                **sdk_kwargs,
            ) as stream:
                response = await stream.get_final_message()
            parsed = None

            if hasattr(response, "content") and isinstance(response.content, list):
                text_blocks = []
                thinking_blocks = []
                for block in response.content:
                    btype = getattr(block, "type", "")
                    if btype == "text":
                        text_blocks.append(getattr(block, "text", ""))
                    elif btype == "thinking":
                        thinking_blocks.append(getattr(block, "thinking", ""))
                    elif btype == "tool_use":
                        tool_calls.append(ToolCall(
                            tool_use_id=getattr(block, "id", ""),
                            name=getattr(block, "name", ""),
                            input=getattr(block, "input", {}) or {},
                        ))

                if text_blocks:
                    content_text = "\n\n".join(text_blocks)
                if thinking_blocks:
                    thinking_text = "\n\n".join(thinking_blocks)
            elif response.content:
                content_text = response.content[0].text if hasattr(response.content[0], "text") else None

        # ── Map response ──────────────────────────────────────────
        # Build content_blocks from raw response content for downstream use
        content_blocks: list[dict] = []
        for b in (getattr(response, "content", None) or []):
            block_dict: dict = {"type": getattr(b, "type", "")}
            btype = block_dict["type"]
            if btype == "text":
                block_dict["text"] = getattr(b, "text", None)
            elif btype == "thinking":
                block_dict["thinking"] = getattr(b, "thinking", None)
            elif btype == "tool_use":
                block_dict["id"] = getattr(b, "id", "")
                block_dict["name"] = getattr(b, "name", "")
                block_dict["input"] = getattr(b, "input", {})
            elif btype == "server_tool_use":
                block_dict["id"] = getattr(b, "id", "")
                block_dict["name"] = getattr(b, "name", "")
                block_dict["input"] = getattr(b, "input", {})
            elif btype == "web_search_tool_result":
                block_dict["tool_use_id"] = getattr(b, "tool_use_id", "")
                block_dict["content"] = getattr(b, "content", [])
                # content may be a list of search result objects; serialize them
                if hasattr(block_dict["content"], "__iter__") and not isinstance(block_dict["content"], (str, dict)):
                    block_dict["content"] = [
                        {k: getattr(item, k, None) for k in ("type", "url", "title", "page_age", "snippet", "encrypted_content")}
                        if hasattr(item, "type") else item
                        for item in block_dict["content"]
                    ]
            else:
                # Generic fallback: try to capture common attributes
                for attr in ("text", "id", "name", "input", "content"):
                    val = getattr(b, attr, None)
                    if val is not None:
                        block_dict[attr] = val
            content_blocks.append(block_dict)

        raw: dict = {
            "id": getattr(response, "id", None),
            "model": getattr(response, "model", None),
            "stop_reason": getattr(response, "stop_reason", None),
            "usage": {
                "input_tokens": getattr(response.usage, "input_tokens", 0) or 0,
                "output_tokens": getattr(response.usage, "output_tokens", 0) or 0,
                "cache_creation_input_tokens": getattr(response.usage, "cache_creation_input_tokens", 0) or 0,
                "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0) or 0,
            },
            "content": content_blocks,
        }
        return UnifiedResponse(
            provider="anthropic",
            model=model,
            content=content_text,
            parsed=parsed,
            thinking=thinking_text,
            tool_calls=tool_calls,
            content_blocks=content_blocks if content_blocks else None,
            usage=UsageInfo(
                input_tokens=getattr(response.usage, "input_tokens", 0) or 0,
                output_tokens=getattr(response.usage, "output_tokens", 0) or 0,
                cache_creation_input_tokens=getattr(
                    response.usage, "cache_creation_input_tokens", 0
                )
                or 0,
                cache_read_input_tokens=getattr(
                    response.usage, "cache_read_input_tokens", 0
                )
                or 0,
                total_tokens=(
                    (getattr(response.usage, "input_tokens", 0) or 0)
                    + (getattr(response.usage, "output_tokens", 0) or 0)
                    + (getattr(response.usage, "cache_creation_input_tokens", 0) or 0)
                    + (getattr(response.usage, "cache_read_input_tokens", 0) or 0)
                ),
            ),
        ), raw

    async def list_models(self, api_key: str, **kwargs) -> list[str]:
        client = AsyncAnthropic(api_key=api_key)
        response = await client.models.list()
        return [m.id for m in response.data]


# ---------------------------------------------------------------------------
# Message format conversion helpers
# ---------------------------------------------------------------------------

def _adapt_messages_for_anthropic(messages: list[dict]) -> list[dict]:
    """Convert OpenAI-format tool messages to Anthropic's native format.

    The bridge uses OpenAI-style messages as canonical format during the
    agentic tool loop.  This function converts:

    * ``role="assistant"`` with ``tool_calls`` →
      ``role="assistant"`` with content blocks incl. ``tool_use``
    * ``role="tool"`` with ``tool_call_id`` →
      ``role="user"`` with ``content=[{type: "tool_result", ...}]``
      (consecutive tool results are merged into one user message)

    Non-tool messages are passed through unchanged.
    """
    result: list[dict] = []
    i = 0
    while i < len(messages):
        msg = messages[i]
        role = msg.get("role", "")

        if role == "assistant" and "tool_calls" in msg:
            # Build Anthropic content block list
            content: list[dict] = []
            if msg.get("content"):
                content.append({"type": "text", "text": msg["content"]})
            for tc in msg["tool_calls"]:
                fn = tc.get("function", {})
                raw_args = fn.get("arguments", "{}")
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError:
                    args = {}
                content.append({
                    "type": "tool_use",
                    "id": tc.get("id", ""),
                    "name": fn.get("name", ""),
                    "input": args,
                })
            result.append({"role": "assistant", "content": content})
            i += 1

        elif role == "tool":
            # Accumulate consecutive tool results into one user message
            tool_results: list[dict] = []
            while i < len(messages) and messages[i].get("role") == "tool":
                tm = messages[i]
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tm.get("tool_call_id", ""),
                    "content": tm.get("content", ""),
                })
                i += 1
            result.append({"role": "user", "content": tool_results})

        else:
            result.append(msg)
            i += 1

    return result
