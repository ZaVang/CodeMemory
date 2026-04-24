"""
LLM Bridge — Provider registry.

Import and register all available provider adapters here.
"""

from .anthropic_provider import AnthropicProvider
from .base import BaseProvider
from .google_provider import GoogleProvider
from .openai_provider import OpenAIProvider

# Maps lowercase provider identifiers to their adapter class.
PROVIDER_REGISTRY: dict[str, type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
    "vertexai": GoogleProvider,  # same adapter, different init params
}

__all__ = [
    "BaseProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "GoogleProvider",
    "PROVIDER_REGISTRY",
]
