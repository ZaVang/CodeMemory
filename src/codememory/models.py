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

    type: str = Field(default="atom", description="atom | schema | instance | composite")
    id: str = Field(default="", description="Memory identifier (e.g. 'user/ideas/thesis')")
    summary: str = ""
    status: str = Field(default="active")
    tags: list[str] = Field(default_factory=list)
    intensity: int = Field(default=5, ge=1, le=10)
    version: int = Field(default=1)
    path: str = ""
    access_count: int = 0
    last_access: str | None = None
    created: str = ""
    updated: str = ""

    # Optional structured imports (instance / composite)
    imports: dict[str, list[Any]] = Field(default_factory=dict)

    # Schema reference (instance only)
    schema: str | None = None

    # Staleness tracking
    summary_hash: str | None = None

    # Protection flag (intensity >= 8)
    protected: bool | None = None

    # Change tracking (from update)
    change_note: str | None = None
    change_log: list[dict[str, Any]] = Field(default_factory=list)

    # Source metadata
    source: dict[str, Any] | None = None

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


class IndexData(BaseModel):
    """The full index.json structure."""

    version: int = 1
    updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    memories: dict[str, MemoryEntry] = Field(default_factory=dict)
