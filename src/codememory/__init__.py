"""CodeMemory — memory atomization protocol.

Core public API for memory management: create, update, resolve, validate,
reindex, search.  One-line Agent integration via ``CodememoryToolkit``.
"""

from .compiler import (
    MaterializeResult,
    MemoryProposal,
    ReviewSet,
    SourceDoc,
    SourceParagraph,
    SourceSegment,
    compile_markdown_corpus,
    load_review_set,
    materialize_review_set,
    save_review_set,
)
from .core import compute_body_hash, get_root_dir, parse_frontmatter
from .capture import CaptureRecord, append_capture, capture_content_hash, scan_all_captures
from .build import ContextPack, ContextPackNode, ContextPackNotice, build_context_pack, render_context_pack
from .create import create
from .index import load_index, reindex, save_index
from .integrations import CodememoryToolkit
from .models import ChangeLogEntry, ImportRef, IndexData, MemoryEntry, PersonalIndexEntry, SourceRef
from .personal_index import read_personal_object, typed_search
from .periodic_review import (
    PeriodicReviewBundle,
    PeriodicReviewSaveResult,
    PeriodicReviewWindow,
    prepare_periodic_review,
    resolve_periodic_window,
    save_periodic_review,
)
from .profile import PersonalProfile, init_personal_profile, validate_personal_profile
from .orphans import find_orphans
from .resolve import build_dag, find_cycle_participants, resolve, topological_sort
from .search import search
from .sources import (
    SourceArtifact,
    SourceArtifactCheck,
    SourceExpansion,
    SourceRegistry,
    add_source_artifact,
    check_source_artifact,
    check_source_registry,
    expand_source_artifact,
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
    "append_capture",
    "capture_content_hash",
    "scan_all_captures",
    # Data Models
    "MemoryEntry",
    "PersonalIndexEntry",
    "PersonalProfile",
    "CaptureRecord",
    "IndexData",
    "ImportRef",
    "SourceRef",
    "ChangeLogEntry",
    "ContextPack",
    "ContextPackNode",
    "ContextPackNotice",
    "MaterializeResult",
    "MemoryProposal",
    "ReviewSet",
    "SourceDoc",
    "SourceParagraph",
    "SourceSegment",
    "SourceArtifact",
    "SourceArtifactCheck",
    "SourceExpansion",
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
    "typed_search",
    "read_personal_object",
    "PeriodicReviewBundle",
    "PeriodicReviewSaveResult",
    "PeriodicReviewWindow",
    "prepare_periodic_review",
    "resolve_periodic_window",
    "save_periodic_review",
    "init_personal_profile",
    "validate_personal_profile",
    # Sources
    "add_source_artifact",
    "check_source_artifact",
    "check_source_registry",
    "expand_source_artifact",
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
