"""Modification-class proposal patch queue (architecture.md §3.3).

A single .md file cannot hold two versions, so high-risk changes to
existing atoms land as patch records under ``.codememory/proposals/``.
The owner merges (patch applied through ``update`` — version++ and
change_log for free) or rejects (record discarded). Deliberately NOT
built on the compiler review machinery: that is corpus-import-set
granularity, this is a single-change queue.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from .core import get_memory_path, resolve_safe_relative_path

_logger = logging.getLogger("codememory")


class ProposalPatch(BaseModel):
    """Field-level new values; only provided fields are applied."""

    summary: str | None = None
    body: str | None = None
    import_required: list[str] | None = None
    import_recommended: list[str] | None = None
    import_related: list[str] | None = None
    source_ref: str | None = None

    def is_empty(self) -> bool:
        return all(
            getattr(self, name) is None
            for name in ("summary", "body", "import_required",
                         "import_recommended", "import_related", "source_ref")
        )


class Proposal(BaseModel):
    """One pending modification proposal."""

    proposal_id: str
    target_id: str
    patch: ProposalPatch
    reason: str
    created_by: str = "agent"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


def proposals_dir(root_dir: Path) -> Path:
    return root_dir / ".codememory" / "proposals"


def _proposal_path(root_dir: Path, proposal_id: str) -> Path:
    return resolve_safe_relative_path(
        proposals_dir(root_dir),
        proposal_id,
        suffix=".json",
        label="proposal_id",
        allow_nested=False,
    )


def _next_seq(root_dir: Path) -> int:
    directory = proposals_dir(root_dir)
    if not directory.exists():
        return 1
    seqs = []
    for p in directory.glob("*.json"):
        head = p.stem.split("-", 1)[0]
        if head.isdigit():
            seqs.append(int(head))
    return max(seqs, default=0) + 1


def create_proposal(
    root_dir: Path,
    target_id: str,
    *,
    reason: str,
    summary: str | None = None,
    body: str | None = None,
    import_required: list[str] | None = None,
    import_recommended: list[str] | None = None,
    import_related: list[str] | None = None,
    source_ref: str | None = None,
    created_by: str = "agent",
) -> Proposal:
    """Queue a modification proposal without touching the target atom."""
    if not reason:
        _logger.error("--reason is required for propose.")
        sys.exit(1)

    if not get_memory_path(root_dir, target_id).exists():
        _logger.error("Target memory '%s' not found; cannot propose against it.", target_id)
        sys.exit(1)

    patch = ProposalPatch(
        summary=summary,
        body=body,
        import_required=import_required,
        import_recommended=import_recommended,
        import_related=import_related,
        source_ref=source_ref,
    )
    if patch.is_empty():
        _logger.error("Proposal has no patched fields; provide at least one change.")
        sys.exit(1)

    slug = target_id.replace("/", "-")
    proposal = Proposal(
        proposal_id=f"{_next_seq(root_dir):04d}-{slug}",
        target_id=target_id,
        patch=patch,
        reason=reason,
        created_by=created_by,
    )

    directory = proposals_dir(root_dir)
    directory.mkdir(parents=True, exist_ok=True)
    _proposal_path(root_dir, proposal.proposal_id).write_text(
        json.dumps(proposal.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Queued proposal {proposal.proposal_id} -> {target_id}")

    try:
        from .log import append_log
        append_log(root_dir, "propose", f"{proposal.proposal_id} -> {target_id}: {reason}")
    except ImportError:
        pass

    return proposal


def load_proposal(root_dir: Path, proposal_id: str) -> Proposal | None:
    path = _proposal_path(root_dir, proposal_id)
    if not path.exists():
        return None
    return Proposal.model_validate(json.loads(path.read_text(encoding="utf-8")))


def list_proposals(root_dir: Path) -> list[Proposal]:
    directory = proposals_dir(root_dir)
    if not directory.exists():
        return []
    out: list[Proposal] = []
    for path in sorted(directory.glob("*.json")):
        try:
            out.append(Proposal.model_validate(json.loads(path.read_text(encoding="utf-8"))))
        except (json.JSONDecodeError, ValueError) as exc:
            _logger.warning("Skipping unreadable proposal file %s: %s", path.name, exc)
    return out


def merge_proposal(root_dir: Path, proposal_id: str) -> Path:
    """Apply a queued patch to its target via update(), then clear the record."""
    proposal = load_proposal(root_dir, proposal_id)
    if proposal is None:
        _logger.error("Proposal '%s' not found.", proposal_id)
        sys.exit(1)

    from .update import update

    patch = proposal.patch
    file_path = update(
        root_dir,
        proposal.target_id,
        change_note=f"[merge {proposal.proposal_id}] {proposal.reason}",
        summary=patch.summary,
        body=patch.body,
        import_required=patch.import_required,
        import_recommended=patch.import_recommended,
        import_related=patch.import_related,
        source_ref=patch.source_ref,
    )

    _proposal_path(root_dir, proposal_id).unlink(missing_ok=True)
    print(f"Merged proposal {proposal_id} into {proposal.target_id}")

    try:
        from .log import append_log
        append_log(root_dir, "merge", f"proposal {proposal_id} applied to {proposal.target_id}")
    except ImportError:
        pass

    return file_path


def reject_proposal(root_dir: Path, proposal_id: str) -> None:
    """Discard a queued patch; the target atom is untouched."""
    proposal = load_proposal(root_dir, proposal_id)
    if proposal is None:
        _logger.error("Proposal '%s' not found.", proposal_id)
        sys.exit(1)

    _proposal_path(root_dir, proposal_id).unlink(missing_ok=True)
    print(f"Rejected proposal {proposal_id} (target {proposal.target_id} untouched)")

    try:
        from .log import append_log
        append_log(root_dir, "reject", f"proposal {proposal_id} discarded ({proposal.target_id})")
    except ImportError:
        pass
