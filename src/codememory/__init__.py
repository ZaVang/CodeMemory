"""CodeMemory — memory atomization protocol.

Core public API for memory management: create, resolve, validate, reindex, search.
"""

from .core import compute_body_hash, get_root_dir, parse_frontmatter
from .create import create
from .index import load_index, reindex, save_index
from .resolve import build_dag, find_cycle_participants, resolve, topological_sort
from .search import search
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
    # Search
    "search",
]
