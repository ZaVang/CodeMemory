"""CodeMemory — memory atomization protocol.

Core public API for memory management: create, update, resolve, validate,
reindex, search.  One-line Agent integration via ``CodememoryToolkit``.
"""

from .compiler import (
    MaterializeResult,
    MemoryProposal,
    ReviewSet,
    SourceDoc,
    SourceSegment,
    compile_markdown_corpus,
    load_review_set,
    materialize_review_set,
    save_review_set,
)
from .core import compute_body_hash, get_root_dir, parse_frontmatter
from .context_pack import ContextPack, ContextPackNode, ContextPackNotice, build_context_pack, render_context_pack
from .create import create
from .index import load_index, reindex, save_index
from .integrations import CodememoryToolkit
from .models import ChangeLogEntry, ImportRef, IndexData, MemoryEntry
from .orphans import find_orphans
from .resolve import build_dag, find_cycle_participants, resolve, topological_sort
from .search import search
from .sources import (
    SourceArtifact,
    SourceArtifactCheck,
    SourceRegistry,
    add_source_artifact,
    check_source_artifact,
    check_source_registry,
    get_source_artifact,
    list_source_artifacts,
    load_source_registry,
    save_source_registry,
)
from .transient import TransientDAG, TransientNode
from .update import update
from .validate import validate

__all__ = [
    # Core
    "parse_frontmatter",
    "compute_body_hash",
    "get_root_dir",
    # Data Models
    "MemoryEntry",
    "IndexData",
    "ImportRef",
    "ChangeLogEntry",
    "ContextPack",
    "ContextPackNode",
    "ContextPackNotice",
    "MaterializeResult",
    "MemoryProposal",
    "ReviewSet",
    "SourceDoc",
    "SourceSegment",
    "SourceArtifact",
    "SourceArtifactCheck",
    "SourceRegistry",
    # Index
    "load_index",
    "save_index",
    "reindex",
    # Resolve
    "build_dag",
    "find_cycle_participants",
    "topological_sort",
    "resolve",
    "build_context_pack",
    "render_context_pack",
    # Validate
    "validate",
    # Create
    "create",
    # Update
    "update",
    # Transient
    "TransientDAG",
    "TransientNode",
    # Search
    "search",
    # Sources
    "add_source_artifact",
    "check_source_artifact",
    "check_source_registry",
    "get_source_artifact",
    "list_source_artifacts",
    "load_source_registry",
    "save_source_registry",
    # Orphans
    "find_orphans",
    # Compiler
    "compile_markdown_corpus",
    "load_review_set",
    "materialize_review_set",
    "save_review_set",
    # Integration
    "CodememoryToolkit",
]
