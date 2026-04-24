"""Tracing integration for llm_gateway.

This module defines the tracing interface that llm_gateway optionally
imports. When tracing is not configured, llm_gateway silently skips
all recording.

Currently a stub — the schemas define the structure, but
get_current_trace() returns None. Once Session-based tracing is
implemented, this module will bridge llm_gateway events into the
Session event stream.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class LLMCallEntry(BaseModel):
    called_at: str
    model: str
    provider: str
    messages: list[dict[str, Any]]
    raw_response: dict[str, Any]
    content: str
    parsed: dict[str, Any] | None = None
    usage: dict[str, Any]
    stop_reason: str | None = None
    latency_ms: float


class ToolCallEntry(BaseModel):
    tool_use_id: str
    name: str
    arguments: dict[str, Any]
    result: str | None = None
    error: str | None = None
    duration_ms: float


class AgentSessionEntry(BaseModel):
    session_id: str
    turns: int
    tool_sequence: list[str]
    total_input_tokens: int
    total_output_tokens: int
    stop_reason: str
    duration_ms: float


def get_current_trace() -> Any | None:
    """Return the active trace, or None if tracing is not configured.

    TODO: once Session-based tracing is implemented, this will return
    a Trace object that writes LLMCallEntry/ToolCallEntry/AgentSessionEntry
    as Events into the current Session.
    """
    return None
