"""Data models for Memory Compiler review sets."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


Decision = Literal["pending", "accepted", "rejected"]


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class SourceDoc(BaseModel):
    """A Markdown source document discovered during corpus ingestion."""

    source_id: str
    path: str
    rel_path: str
    sha256: str
    chars: int


class SourceSegment(BaseModel):
    """A heading-based Markdown segment with source provenance."""

    segment_id: str
    source_id: str
    rel_path: str
    heading: str = ""
    level: int = 0
    ordinal: int = 0
    body: str = ""
    start_line: int = 1
    end_line: int = 1


class MemoryProposal(BaseModel):
    """A draft memory atom proposal awaiting human review."""

    proposal_id: str
    memory_id: str
    summary: str
    body: str
    tags: list[str] = Field(default_factory=list)
    source: dict[str, Any] = Field(default_factory=dict)
    decision: Decision = "pending"
    type: str = "atom"
    status: str = "active"
    maturity: str = "draft"
    intensity: int = Field(default=5, ge=1, le=10)
    imports: dict[str, list[Any]] = Field(default_factory=dict)


class ReviewSet(BaseModel):
    """A saved compiler review set containing source manifest and proposals."""

    review_id: str
    source_root: str
    created_at: str = Field(default_factory=_utc_timestamp)
    sources: list[SourceDoc] = Field(default_factory=list)
    segments: list[SourceSegment] = Field(default_factory=list)
    proposals: list[MemoryProposal] = Field(default_factory=list)


class MaterializeResult(BaseModel):
    """Result summary for materializing a review set."""

    written: list[str] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
