"""Compatibility shim — the assembly pipeline lives in ``build.py`` (Phase B).

Kept so existing import paths (`codememory.context_pack`) continue to work;
disposition of this shim is a Phase C decision.
"""

from .build import (
    ContextPack,
    ContextPackFormat,
    ContextPackNode,
    ContextPackNotice,
    DependencyRole,
    TrimMode,
    build_context_pack,
    render_context_pack,
)

__all__ = [
    "ContextPack",
    "ContextPackFormat",
    "ContextPackNode",
    "ContextPackNotice",
    "DependencyRole",
    "TrimMode",
    "build_context_pack",
    "render_context_pack",
]
