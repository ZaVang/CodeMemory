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
from codememory.validate import validate  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"

_DEFAULT_DATASET = os.environ.get("CODEMEMORY_DEFAULT_DATASET", "investment")

# Per-request dataset root via context variable
from contextvars import ContextVar  # noqa: E402

_current_dataset: ContextVar[str] = ContextVar("current_dataset", default=_DEFAULT_DATASET)


def get_root() -> Path:
    return _resolve_root(_current_dataset.get())


def _resolve_root(dataset_name: str) -> Path:
    """Resolve an exact registered dataset alias inside ``examples/``.

    Request-controlled values must never be interpreted as filesystem paths.
    The alias lookup is the primary boundary; the containment check is the
    final defense against a symlink or future registry regression.
    """
    if not dataset_name or dataset_name != dataset_name.strip():
        raise ValueError("Invalid dataset alias")
    if Path(dataset_name).is_absolute() or any(mark in dataset_name for mark in ("/", "\\", ":")):
        raise ValueError("Invalid dataset alias")

    registry = {item["name"]: Path(item["path"]) for item in get_available_datasets()}
    if dataset_name not in registry:
        raise ValueError(f"Unknown dataset alias: {dataset_name}")

    examples_root = _EXAMPLES_DIR.resolve()
    root = registry[dataset_name].resolve()
    try:
        root.relative_to(examples_root)
    except ValueError as exc:
        raise ValueError("Dataset root is outside the examples directory") from exc
    return root


def get_available_datasets() -> list[dict[str, str]]:
    datasets: list[dict[str, str]] = []
    if not _EXAMPLES_DIR.exists():
        return datasets
    for entry in sorted(_EXAMPLES_DIR.iterdir()):
        if not entry.is_dir():
            continue
        try:
            resolved_entry = entry.resolve()
            resolved_entry.relative_to(_EXAMPLES_DIR.resolve())
        except ValueError:
            continue
        idx = entry / ".codememory" / "index.json"
        if idx.exists():
            try:
                with open(idx, "r", encoding="utf-8") as f:
                    data = json.load(f)
                count = len(data.get("memories", {}))
            except Exception:
                count = 0
            datasets.append({
                "name": entry.name,
                "path": str(resolved_entry),
                "memory_count": count,
            })
    return datasets


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
