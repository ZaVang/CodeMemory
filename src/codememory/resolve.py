"""Thin alias over the unified build pipeline (architecture.md §4.1).

``resolve`` = ``build_context_pack`` + plain-markdown render. The bespoke
resolver implementation was retired in Phase B; DAG utilities are
re-exported from ``build.py`` for compatibility with existing import paths
(validate, transient, handlers, tests).
"""

import logging
from pathlib import Path

from .build import (  # noqa: F401
    _count_dependents,
    _get_imports,
    build_context_pack,
    build_dag,
    find_cycle_participants,
    render_context_pack,
    topological_sort,
)

_logger = logging.getLogger("codememory")


def resolve(
    root_dir: Path,
    memory_id: str,
    depth: str = "required",
    budget: int | None = None,
    focus: str | None = None,
) -> str:
    """Resolve and assemble memory context for a given memory ID.

    Pipeline errors (missing or non-assemblable targets) are returned as
    ``Error: ...`` strings to preserve the CLI contract.
    """
    try:
        pack = build_context_pack(
            root_dir,
            memory_id,
            depth=depth,
            budget=budget,
            focus=focus,
        )
    except ValueError as exc:
        msg = f"Error: {exc}"
        _logger.error(msg)
        return msg
    return render_context_pack(pack, "plain-markdown")
