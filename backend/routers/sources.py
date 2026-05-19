"""Source Artifact router."""

from __future__ import annotations

from fastapi import APIRouter

from shared import get_root, serialize
from codememory.sources import expand_source_artifact

router = APIRouter(prefix="/api", tags=["sources"])


@router.get("/sources/expand")
def get_source_expand(
    artifact_id: str,
    start: int | None = None,
    end: int | None = None,
    max_chars: int | None = None,
):
    """Expand a Source Artifact through the shared core contract."""

    expansion = expand_source_artifact(
        get_root(),
        artifact_id,
        start=start,
        end=end,
        max_chars=max_chars,
    )
    return serialize(expansion.model_dump(mode="json"))
