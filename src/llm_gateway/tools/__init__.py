"""
LLM Bridge — Tool framework.

This package re-exports everything that was previously available from
the single ``tools.py`` module, ensuring full backward compatibility.

Public API::

    from llm_gateway.tools import BridgeTool, FetchURLTool, ToolRegistry
"""

from .base import BridgeTool, ToolRegistry, get_default_registry
from .io import (
    FetchURLTool,
    GlobTool,
    ReadFileTool,
    SearchDocsTool,
    # Internal helpers (used by tests)
    _cosine,
    _html_to_text,
    _score_paragraphs,
    _split_paragraphs,
    _tfidf_scores,
    _tokenize,
)

# Re-export ToolParam for backward compatibility (previously importable from tools.py)
from ..models import ToolParam

__all__ = [
    # base
    "BridgeTool",
    "ToolRegistry",
    "get_default_registry",
    # io tools
    "FetchURLTool",
    "GlobTool",
    "ReadFileTool",
    "SearchDocsTool",
    # internal helpers (backward compat for tests)
    "_cosine",
    "_html_to_text",
    "_score_paragraphs",
    "_split_paragraphs",
    "_tfidf_scores",
    "_tokenize",
    # models re-export
    "ToolParam",
]
