"""CodeMemory — memory atomization protocol.

Core public API for memory management: create, update, resolve, validate,
reindex, search.  One-line Agent integration via ``CodememoryToolkit``.
"""

from .core import compute_body_hash, get_root_dir, parse_frontmatter
from .create import create
from .index import load_index, reindex, save_index
from .integrations import CodememoryToolkit
from .orphans import find_orphans
from .resolve import build_dag, find_cycle_participants, resolve, topological_sort
from .search import search
from .transient import TransientDAG, TransientNode
from .update import update
from .validate import validate

__all__ = [
    # Core
    "parse_frontmatter",
    "compute_body_hash",
    "get_root_dir",
    # Index
    "load_index",
    "save_index",
    "reindex",
    # Resolve
    "build_dag",
    "find_cycle_participants",
    "topological_sort",
    "resolve",
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
    # Orphans
    "find_orphans",
    # Integration
    "CodememoryToolkit",
]
