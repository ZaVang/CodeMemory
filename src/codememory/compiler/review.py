"""Review-set persistence and proposal decision helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .models import Decision, ReviewSet

_SAFE_REVIEW_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def review_dir(root: Path) -> Path:
    """Return the compiler review-set directory under a memory root."""
    return root / ".codememory" / "reviews"


def review_path(root: Path, review_id: str) -> Path:
    """Return the JSON path for one review set."""
    if (
        not _SAFE_REVIEW_ID.fullmatch(review_id)
        or review_id in {".", ".."}
        or ".." in review_id
    ):
        raise ValueError(f"unsafe review_id: {review_id}")
    return review_dir(root) / f"{review_id}.json"


def save_review_set(root: Path, review: ReviewSet) -> Path:
    """Save a review set to ``.codememory/reviews/{review_id}.json``."""
    path = review_path(root, review.review_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(review.model_dump(mode="json"), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def load_review_set(root: Path, review_id: str) -> ReviewSet:
    """Load a saved compiler review set."""
    path = review_path(root, review_id)
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ReviewSet.model_validate(raw)


def equivalent_compiler_input(existing: ReviewSet, candidate: ReviewSet) -> bool:
    """Compare deterministic compiler output while ignoring time and decisions."""

    def normalized(review: ReviewSet) -> dict:
        payload = review.model_dump(mode="json", exclude={"created_at"})
        for proposal in payload["proposals"]:
            proposal["decision"] = "pending"
        return payload

    return normalized(existing) == normalized(candidate)


def set_all_decisions(review: ReviewSet, decision: Decision) -> ReviewSet:
    """Return a copy with every proposal decision set to ``decision``."""
    return review.model_copy(
        update={
            "proposals": [proposal.model_copy(update={"decision": decision}) for proposal in review.proposals]
        }
    )
