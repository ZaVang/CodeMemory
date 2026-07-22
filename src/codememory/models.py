"""Pydantic v2 data models for CodeMemory.

All module-to-module API boundaries use these models instead of bare dicts.
Serialization: ``entry.model_dump(mode="json")`` (v2 API, NOT ``.dict()``).
"""

from __future__ import annotations

import warnings
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ``schema`` is a legitimate field name in CodeMemory; suppress Pydantic's
# shadow warning (we never call the deprecated ``.schema()`` method).
warnings.filterwarnings("ignore", message=".*shadows.*BaseModel", category=UserWarning)

# Statuses that never enter default context assembly (architecture.md §3.2):
# proposed awaits owner merge; archived/superseded are out of the canonical graph.
NON_ASSEMBLABLE_STATUSES: tuple[str, ...] = ("proposed", "archived", "superseded")


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


class SourceRef(BaseModel):
    """A reference from an atom to a Source Artifact.

    ``source_refs`` are provenance links. They do not participate in the
    imports DAG and should not be used as dependency edges.
    """

    artifact_id: str
    section_id: str | None = None
    range: str | None = None
    summary: str = ""
    disclosure_hint: str = "anchor"


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
    version: int = Field(default=1)
    path: str = ""
    access_count: int = 0
    last_access: str | None = None
    created: str = ""
    updated: str = ""

    # Optional structured imports
    imports: dict[str, list[Any]] = Field(default_factory=dict)

    # Schema reference (optional)
    schema: str | None = None

    # Staleness tracking
    summary_hash: str | None = None

    # Protection flag (owner-set; changes must go through a proposal)
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
    source_refs: list[SourceRef] = Field(default_factory=list)

    # Knowledge governance
    maturity: str = Field(default="draft", description="draft | verified | proven | superseded")
    evidence: dict[str, Any] | None = None

    # Personal Profile discovery/provenance metadata.  claim_status applies to
    # a canonical atom (or an inline claim block), never to a whole Topic.
    origin: str | None = None
    claim_status: str | None = None
    topic: str | None = None
    project: str | None = None
    people: list[str] = Field(default_factory=list)

    # Golden-question test contract (architecture §3.4). Stored raw so a
    # malformed atom cannot break reindex; shape is reported by validate.
    golden_questions: list[Any] = Field(default_factory=list)

    # Extra fields that may appear in frontmatter (what/why/when for instances)
    extra: dict[str, Any] = Field(default_factory=dict, exclude=True)

    model_config = ConfigDict(extra="allow", populate_by_name=True, protected_namespaces=())

    @field_validator("golden_questions", mode="before")
    @classmethod
    def _coerce_golden_questions(cls, v: object) -> list[Any]:
        """Keep reindex resilient: non-list shapes degrade to [] (validate reports them)."""
        if isinstance(v, list):
            return v
        return []

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
    personal_objects: dict[str, "PersonalIndexEntry"] = Field(default_factory=dict)


class PersonalIndexEntry(BaseModel):
    """A non-canonical Personal Profile object stored in the unified index."""

    kind: Literal["capture", "incubator_topic"]
    id: str
    path: str
    display_locator: str
    summary: str = ""
    content: str = ""
    timestamp: str = ""
    tags: list[str] = Field(default_factory=list)
    origin: str | None = None
    topic: str | None = None
    project: str | None = None
    people: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    read_action: Literal["read"] = "read"
