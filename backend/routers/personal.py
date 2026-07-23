"""Thin REST adapter for the allowlisted Personal owner workspace."""

from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from shared import get_root
from codememory.handlers import handle_review_batch
from codememory.personal_web import (
    get_personal_captures,
    get_personal_overview,
    get_personal_timeline,
    get_personal_topics,
)
from codememory.promotion import ReviewAction


router = APIRouter(prefix="/api/personal", tags=["personal"])


class PersonalReviewBatchRequest(BaseModel):
    owner_confirmed: Literal[True]
    decisions: list[ReviewAction] = Field(min_length=1, max_length=100)


def _mapped_error(exc: Exception) -> HTTPException:
    if isinstance(exc, KeyError):
        return HTTPException(status_code=404, detail=str(exc).strip("'"))
    return HTTPException(status_code=409, detail=str(exc))


@router.get("/overview")
def personal_overview():
    try:
        return get_personal_overview(get_root()).model_dump(mode="json")
    except (ValueError, FileNotFoundError) as exc:
        raise _mapped_error(exc) from exc


@router.get("/captures")
def personal_captures(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return get_personal_captures(get_root(), offset=offset, limit=limit).model_dump(mode="json")
    except (ValueError, FileNotFoundError) as exc:
        raise _mapped_error(exc) from exc


@router.get("/topics")
def personal_topics():
    try:
        return [item.model_dump(mode="json") for item in get_personal_topics(get_root())]
    except (ValueError, FileNotFoundError) as exc:
        raise _mapped_error(exc) from exc


@router.get("/timeline")
def personal_timeline(topic_id: str | None = None):
    try:
        return get_personal_timeline(get_root(), topic_id=topic_id).model_dump(mode="json")
    except (KeyError, ValueError, FileNotFoundError) as exc:
        raise _mapped_error(exc) from exc


@router.post("/review-batch")
def personal_review_batch(req: PersonalReviewBatchRequest):
    root = get_root()
    try:
        # Validate the Personal boundary before entering the shared mutation handler.
        get_personal_overview(root)
        decisions = [
            {
                **item.model_dump(mode="json"),
                "owner_confirmed": True if item.action == "promote" else item.owner_confirmed,
            }
            for item in req.decisions
        ]
        return json.loads(handle_review_batch(root, decisions))
    except (KeyError, ValueError, FileNotFoundError, FileExistsError) as exc:
        raise _mapped_error(exc) from exc
