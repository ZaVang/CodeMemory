"""Materialize accepted memory proposals into canonical atom files."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

import yaml

from codememory.core import compute_body_hash
from codememory.index import reindex

from .models import MaterializeResult, MemoryProposal, ReviewSet


def _safe_memory_path(root: Path, memory_id: str) -> Path:
    """Resolve a memory id under root, rejecting absolute/traversal paths."""
    if not memory_id or "\\" in memory_id or ":" in memory_id:
        raise ValueError(f"unsafe memory_id: {memory_id}")

    pure = PurePosixPath(memory_id)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError(f"unsafe memory_id: {memory_id}")

    root_resolved = root.resolve()
    target = (root_resolved / f"{memory_id}.md").resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"unsafe memory_id: {memory_id}") from exc
    return target


def _frontmatter_for_proposal(proposal: MemoryProposal) -> dict:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    frontmatter = {
        "type": proposal.type,
        "id": proposal.memory_id,
        "summary": proposal.summary,
        "status": proposal.status,
        "created": today,
        "updated": today,
        "version": 1,
        "tags": proposal.tags,
        "maturity": proposal.maturity,
        "source": proposal.source,
        "evidence": {
            "contributors": ["memory-compiler"],
            "sessions": [],
        },
        "summary_hash": compute_body_hash(proposal.body.strip()),
    }
    if proposal.imports:
        frontmatter["imports"] = proposal.imports
    return frontmatter


def materialize_review_set(
    root: Path,
    review: ReviewSet,
    accept_all: bool = False,
) -> MaterializeResult:
    """Write accepted proposals to disk and refresh the index."""
    result = MaterializeResult()

    for proposal in review.proposals:
        accepted = proposal.decision == "accepted" or accept_all
        if not accepted:
            result.skipped.append(proposal.proposal_id)
            continue

        try:
            file_path = _safe_memory_path(root, proposal.memory_id)
        except ValueError as exc:
            result.errors.append(str(exc))
            continue

        if file_path.exists():
            result.errors.append(f"exists: {proposal.memory_id}")
            continue

        file_path.parent.mkdir(parents=True, exist_ok=True)
        yaml_str = yaml.dump(
            _frontmatter_for_proposal(proposal),
            allow_unicode=True,
            sort_keys=False,
        )
        file_path.write_text(f"---\n{yaml_str}---\n{proposal.body.strip()}\n", encoding="utf-8")
        result.written.append(str(file_path))

    if result.written:
        reindex(root)
    return result
