"""Pydantic v2 data models for CodeMemory.

All module-to-module API boundaries use these models instead of bare dicts.
Serialization: ``entry.model_dump(mode="json")`` (v2 API, NOT ``.dict()``).
"""

from __future__ import annotations

import warnings
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ``schema`` is a legitimate field name in CodeMemory; suppress Pydantic's
# shadow warning (we never call the deprecated ``.schema()`` method).
warnings.filterwarnings("ignore", message=".*shadows.*BaseModel", category=UserWarning)


def _strdate(v: object) -> str:
    """Coerce YAML-parsed date objects to ISO-format strings."""
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, date):
        return v.isoformat()
    return str(v)


class ImportRef(BaseModel):
    """A single import reference with optional pin version and reason."""

    id: str
    pin: str | None = None
    reason: str | None = None


class ChangeLogEntry(BaseModel):
    """A single changelog record."""

    version: int
    date: str
    note: str = ""


class MemoryEntry(BaseModel):
    """A single indexed memory — matches both frontmatter metadata and index storage.

    ``id`` defaults to ``""`` because index.json stores the memory id as the
    dict key, not inside each entry.
    """

    type: str = Field(default="atom", description="atom | schema")
    id: str = Field(default="", description="Memory identifier (e.g. 'user/ideas/thesis')")
    summary: str = ""
    status: str = Field(default="active")
    tags: list[str] = Field(default_factory=list)
    intensity: int = Field(default=5, ge=1, le=10)
    version: int = Field(default=1)
    path: str = ""
    access_count: int = 0
    last_access: str | None = None
    days_since_last_access: int | None = Field(default=None, description="Precomputed days since last access (R13-M3)")
    created: str = ""
    updated: str = ""

    # Optional structured imports
    imports: dict[str, list[Any]] = Field(default_factory=dict)

    # Schema reference (optional)
    schema: str | None = None

    # Staleness tracking
    summary_hash: str | None = None

    # Per-memory half-life in days for exponential decay formula (R13-M4)
    stability: float = Field(default=14.0, gt=0.0, description="Half-life in days for access decay (min 0.1)")

    # R16-C2: track whether stability was manually set (skip adaptive SInc if so)
    stability_source: str | None = Field(default=None, description="None/adaptive = auto-updated; manual = user-set")

    # Protection flag (intensity >= 8)
    protected: bool | None = None

    # Prompt caching hint (Sprint 14)
    cache_stable: bool = Field(default=False, description="Suitable for LLM cache prefix")

    # Lifecycle management (R3)
    lifecycle: str = Field(default="permanent", description="permanent | stable | ephemeral")

    # Change tracking (from update)
    change_note: str | None = None
    change_log: list[dict[str, Any]] = Field(default_factory=list)

    # Source metadata
    source: dict[str, Any] | None = None

    # Knowledge governance
    maturity: str = Field(default="draft", description="draft | verified | proven | superseded")
    evidence: dict[str, Any] | None = None

    # Extra fields that may appear in frontmatter (what/why/when for instances)
    extra: dict[str, Any] = Field(default_factory=dict, exclude=True)

    model_config = ConfigDict(extra="allow", populate_by_name=True, protected_namespaces=())

    @field_validator("summary_hash", mode="before")
    @classmethod
    def _coerce_summary_hash(cls, v: object) -> str | None:
        """YAML may parse numeric hashes as int; always store as str."""
        if v is None:
            return None
        return str(v)

    # Coerce YAML-parsed date objects to strings
    _coerce_created = field_validator("created", mode="before")(_strdate)
    _coerce_updated = field_validator("updated", mode="before")(_strdate)

    @field_validator("stability", mode="before")
    @classmethod
    def _clamp_stability(cls, v: object) -> float:
        """Reject stability <= 0; clamp dangerously low values to 0.1 (R14-C2)."""
        if v is None:
            return 14.0
        val = float(v)  # type: ignore[arg-type]
        if val <= 0:
            raise ValueError(f"stability must be > 0, got {val}")
        if val < 0.1:
            return 0.1
        return val


class IndexData(BaseModel):
    """The full index.json structure."""

    version: int = 1
    updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    memories: dict[str, MemoryEntry] = Field(default_factory=dict)
