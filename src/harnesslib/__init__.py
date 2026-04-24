"""harnesslib — 通用Agent编排框架。

借鉴 Anthropic Managed Agents 的 Harness 架构设计。
跨项目复用，不含任何业务假设。
"""

from .harness import Harness
from .sandbox import Sandbox, SandboxBase, ToolDefinition

__all__ = ["Harness", "Sandbox", "SandboxBase", "ToolDefinition"]