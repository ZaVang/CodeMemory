"""
LLM Bridge — Lightweight multi-provider LLM gateway.

Public API::

    from llm_bridge import LLMBridge, ChatParameters, UnifiedResponse

    bridge = LLMBridge.from_config("llm_bridge_config.yaml")
    response = await bridge.chat(
        "openai/gpt-4o",
        messages=[{"role": "user", "content": "Hello!"}],
        params=ChatParameters(temperature=0.5, max_tokens=32000),
    )

Tool use::

    from llm_gateway import LLMBridge
    from llm_gateway.tools import FetchURLTool

    response = await bridge.chat(
        "smart",
        messages=[{"role": "user", "content": "Summarise http://docs.internal/api"}],
        tools=[FetchURLTool()],
    )

Skill loading::

    response = await bridge.chat(
        "openai/gpt-4o",
        messages=[{"role": "user", "content": "Review this code: ..."}],
        skills=["code-reviewer"],
        skill_vars={"language": "Python"},
    )
"""

from .bridge import LLMBridge
from .models import (
    BridgeConfig,
    ChatParameters,
    ModelConfig,
    RetryConfig,
    ToolCall,
    ToolParam,
    UnifiedResponse,
    UsageInfo,
)
from .skills import LLMBridgeError, SkillLoader, SkillNotFoundError, SkillRenderError
from .tools import (
    BridgeTool,
    FetchURLTool,
    GlobTool,
    ReadFileTool,
    SearchDocsTool,
    ToolRegistry,
    get_default_registry,
)

__all__ = [
    # Core gateway
    "LLMBridge",
    "ChatParameters",
    "UnifiedResponse",
    "UsageInfo",
    "BridgeConfig",
    "ModelConfig",
    "RetryConfig",
    # Tool use
    "BridgeTool",
    "FetchURLTool",
    "ReadFileTool",
    "GlobTool",
    "SearchDocsTool",
    "ToolRegistry",
    "get_default_registry",
    "ToolParam",
    "ToolCall",
    # Skill loader
    "SkillLoader",
    "LLMBridgeError",
    "SkillNotFoundError",
    "SkillRenderError",
]
