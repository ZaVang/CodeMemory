"""Shared helpers, constants, and Pydantic models for the CodeMemory backend.

Extracted from server.py during the R16-A1 APIRouter split so that every
router module can import the bits it needs without circular dependencies.
"""

from __future__ import annotations

import io
import json
import logging
import os
import re
import sys
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal
from urllib.parse import unquote

import yaml
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

# Ensure codememory package is importable
_CODEMEMORY_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_CODEMEMORY_SRC) not in sys.path:
    sys.path.insert(0, str(_CODEMEMORY_SRC))

from codememory.core import compute_body_hash  # noqa: E402
from codememory.handlers import (  # noqa: E402
    handle_create,
    handle_resolve,
    handle_update,
)
from codememory.index import load_index, reindex, save_index  # noqa: E402
from codememory.models import IndexData, MemoryEntry  # noqa: E402
from codememory.profile import PROFILE_RELATIVE_PATH, validate_personal_profile  # noqa: E402
from codememory.validate import validate  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"

_DEFAULT_DATASET = os.environ.get("CODEMEMORY_DEFAULT_DATASET", "investment")
_INSTANCE_REGISTRY_ENV = "CODEMEMORY_INSTANCE_REGISTRY"
_SAFE_ALIAS_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


class DatasetRecord(BaseModel):
    name: str
    root: Path
    memory_count: int
    profile: Literal["standard", "personal"]
    source: Literal["demo", "registry"]

    def public_dict(self) -> dict[str, str | int]:
        return {
            "name": self.name,
            "memory_count": self.memory_count,
            "profile": self.profile,
            "source": self.source,
        }

# Per-request dataset root via context variable
from contextvars import ContextVar  # noqa: E402

_current_dataset: ContextVar[str] = ContextVar("current_dataset", default=_DEFAULT_DATASET)


def get_root() -> Path:
    return _resolve_root(_current_dataset.get())


def _validate_dataset_alias(alias: str) -> None:
    if (
        not alias
        or alias != alias.strip()
        or not _SAFE_ALIAS_RE.fullmatch(alias)
        or Path(alias).is_absolute()
        or any(mark in alias for mark in ("/", "\\", ":", ".."))
    ):
        raise ValueError("Invalid dataset alias")


def _index_count(root: Path) -> int:
    path = root / ".codememory" / "index.json"
    if not path.is_file():
        return 0
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return 0
    memories = payload.get("memories", {})
    personal = payload.get("personal_objects", {})
    return (len(memories) if isinstance(memories, dict) else 0) + (
        len(personal) if isinstance(personal, dict) else 0
    )


def _demo_dataset_records() -> list[DatasetRecord]:
    records: list[DatasetRecord] = []
    if not _EXAMPLES_DIR.exists():
        return records
    examples_root = _EXAMPLES_DIR.resolve()
    for entry in sorted(_EXAMPLES_DIR.iterdir()):
        if not entry.is_dir():
            continue
        try:
            _validate_dataset_alias(entry.name)
            resolved_entry = entry.resolve()
            resolved_entry.relative_to(examples_root)
        except ValueError:
            continue
        if not (resolved_entry / ".codememory" / "index.json").is_file():
            continue
        records.append(DatasetRecord(
            name=entry.name,
            root=resolved_entry,
            memory_count=_index_count(resolved_entry),
            profile=(
                "personal"
                if (resolved_entry / PROFILE_RELATIVE_PATH).is_file()
                else "standard"
            ),
            source="demo",
        ))
    return records


def _external_dataset_records() -> list[DatasetRecord]:
    configured = os.environ.get(_INSTANCE_REGISTRY_ENV)
    if not configured:
        return []
    config_path = Path(configured)
    if not config_path.is_absolute() or not config_path.is_file():
        raise ValueError(f"{_INSTANCE_REGISTRY_ENV} must name an existing absolute file")
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError("Invalid Personal instance registry") from exc
    if not isinstance(raw, dict) or set(raw) != {"instances"}:
        raise ValueError("Personal instance registry must contain only 'instances'")
    instances = raw["instances"]
    if not isinstance(instances, dict):
        raise ValueError("Personal instance registry 'instances' must be a mapping")

    records: list[DatasetRecord] = []
    roots: set[Path] = set()
    for raw_alias, raw_root in instances.items():
        if not isinstance(raw_alias, str) or not isinstance(raw_root, str):
            raise ValueError("Personal instance registry aliases and roots must be strings")
        _validate_dataset_alias(raw_alias)
        root = Path(raw_root)
        if not root.is_absolute() or not root.is_dir():
            raise ValueError(f"Registered Personal root is invalid: {raw_alias}")
        resolved_root = root.resolve()
        if resolved_root in roots:
            raise ValueError("Personal instance registry contains duplicate resolved roots")
        roots.add(resolved_root)
        if not (resolved_root / PROFILE_RELATIVE_PATH).is_file():
            raise ValueError(f"Registered root is not a Personal Profile: {raw_alias}")
        validation = validate_personal_profile(resolved_root)
        if not validation.profile_valid:
            raise ValueError(f"Registered Personal Profile is invalid: {raw_alias}")
        records.append(DatasetRecord(
            name=raw_alias,
            root=resolved_root,
            memory_count=_index_count(resolved_root),
            profile="personal",
            source="registry",
        ))
    return records


def get_dataset_records() -> list[DatasetRecord]:
    records = [*_demo_dataset_records(), *_external_dataset_records()]
    seen: set[str] = set()
    for record in records:
        if record.name in seen:
            raise ValueError(f"Duplicate dataset alias: {record.name}")
        seen.add(record.name)
    return sorted(records, key=lambda item: item.name)


def _resolve_root(dataset_name: str) -> Path:
    """Resolve an exact server-owned dataset alias.

    Request-controlled values must never be interpreted as filesystem paths.
    Demo roots are contained under examples; external Personal roots are exact
    prevalidated targets from the server-owned registry.
    """
    _validate_dataset_alias(dataset_name)
    registry = {item.name: item for item in get_dataset_records()}
    if dataset_name not in registry:
        raise ValueError(f"Unknown dataset alias: {dataset_name}")
    return registry[dataset_name].root


def get_available_datasets() -> list[dict[str, str | int]]:
    return [record.public_dict() for record in get_dataset_records()]


def get_default_dataset_name() -> str:
    names = [record.name for record in get_dataset_records()]
    if _DEFAULT_DATASET in names:
        return _DEFAULT_DATASET
    if not names:
        raise ValueError("No CodeMemory datasets are available")
    return names[0]


# Expose the context var and default dataset for middleware / main
current_dataset = _current_dataset
DEFAULT_DATASET = _DEFAULT_DATASET
EXAMPLES_DIR = _EXAMPLES_DIR
resolve_root = _resolve_root

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class DateEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def load_cm_index() -> IndexData:
    root = _resolve_root(_current_dataset.get())
    return load_index(root)


def parse_frontmatter(filepath: Path) -> tuple[dict[str, Any], str]:
    try:
        content = filepath.read_text(encoding="utf-8-sig")
    except Exception:
        return {}, ""

    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_str = parts[1]
    body = parts[2].strip()

    try:
        metadata = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError:
        metadata = {}

    for key, value in list(metadata.items()):
        if isinstance(value, (datetime, date)):
            metadata[key] = value.isoformat()
        elif isinstance(value, list):
            metadata[key] = [
                v.isoformat() if isinstance(v, (datetime, date)) else v
                for v in value
            ]

    return metadata, body


def serialize(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize(v) for v in obj]
    return obj


def stale_check(memory_id: str, entry: Any, root: Path | None = None) -> bool:
    if root is None:
        root = _resolve_root(_current_dataset.get())
    entry_path = getattr(entry, "path", None) or entry.get("path", "")
    file_path = root / entry_path
    if not file_path.exists():
        return False
    meta, body = parse_frontmatter(file_path)
    stored_hash = meta.get("summary_hash", "")
    if not stored_hash:
        return False
    actual_hash = compute_body_hash(body)
    return stored_hash != actual_hash


def update_frontmatter_fields(filepath: Path, updates: dict[str, Any]) -> None:
    content = filepath.read_text(encoding="utf-8-sig")
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("File does not have valid YAML frontmatter")
    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2]
    for key, value in updates.items():
        meta[key] = value
    yaml_str = yaml.dump(meta, allow_unicode=True, sort_keys=False)
    new_content = f"---\n{yaml_str}---\n{body}"
    filepath.write_text(new_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------


class CreateMemoryRequest(BaseModel):
    memory_id: str = Field(
        alias="id",
        description="Memory identifier (e.g. 'user/ideas/thesis')",
    )
    summary: str = Field(default="TODO: fill in summary")
    tags: list[str] = Field(default_factory=list)
    body: str = Field(default="")
    type: Literal["atom", "schema"] = Field(default="atom")
    schema: str | None = None
    maturity: Literal["draft", "verified", "proven", "superseded"] = Field(default="draft")
    propose: bool = Field(default=False)
    imports: dict[str, list[str]] | None = Field(
        default=None,
        description="Dependency map by strength",
    )


class UpdateMemoryRequest(BaseModel):
    body: str | None = None
    summary: str | None = None
    tags: list[str] | None = None
    status: Literal["active", "archived", "superseded", "draft"] | None = None
    maturity: Literal["draft", "verified", "proven", "superseded"] | None = None
    change_note: str | None = None
    imports: dict[str, list[str]] | None = None


class ReviewActionRequest(BaseModel):
    id: str = Field(description="Proposed Atom ID or patch proposal ID")


class SearchRequest(BaseModel):
    query: str = Field(default="", description="Free-text search query")
    tags: list[str] | None = None
    type_: str | None = Field(default=None, alias="type")
    status: str | None = None
    maturity: str | None = None
    limit: int = Field(default=50, ge=1, le=500)


class ResolveRequest(BaseModel):
    memory_id: str = Field(alias="id", description="Target memory ID to resolve")
    depth: str = Field(default="recommended", description="required | recommended | full")
    budget: int = Field(default=2000, ge=200, le=5000)


class ContextPackRequest(BaseModel):
    memory_id: str = Field(alias="id", description="Target memory ID to package")
    depth: str = Field(default="recommended", description="required | recommended | full")
    budget: int = Field(default=2000, ge=200, le=5000)
    format: str = Field(default="xml-markdown", description="xml-markdown | markdown | plain-markdown | json")
    focus: str | None = None
    task_goal: str | None = None


class ImportRequest(BaseModel):
    text: str
    extract: str = Field(default="general", description="preferences | decisions | facts | general")


class DatasetSwitchRequest(BaseModel):
    name: str
