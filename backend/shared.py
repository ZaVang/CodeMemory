"""Shared helpers, constants, and Pydantic models for the CodeMemory backend.

Extracted from server.py during the R16-A1 APIRouter split so that every
router module can import the bits it needs without circular dependencies.
"""

from __future__ import annotations

import difflib
import io
import json
import logging
import math
import os
import random
import re
import sys
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import yaml
from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

# Ensure codememory package is importable
_CODEMEMORY_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_CODEMEMORY_SRC) not in sys.path:
    sys.path.insert(0, str(_CODEMEMORY_SRC))

from codememory.core import compute_body_hash, compute_retrieval_probability  # noqa: E402
from codememory.handlers import (  # noqa: E402
    handle_create,
    handle_resolve,
    handle_update,
    handle_wander,
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
    if not dataset_name or not dataset_name.strip():
        dataset_name = _DEFAULT_DATASET
    return (_EXAMPLES_DIR / dataset_name).resolve()


def get_request_root(request: Request) -> Path:
    dataset = request.headers.get("X-Codememory-Dataset", "")
    if not dataset or not dataset.strip():
        dataset = _DEFAULT_DATASET
    _current_dataset.set(dataset)
    return _resolve_root(dataset)


def get_available_datasets() -> list[dict[str, str]]:
    datasets: list[dict[str, str]] = []
    if not _EXAMPLES_DIR.exists():
        return datasets
    for entry in sorted(_EXAMPLES_DIR.iterdir()):
        if not entry.is_dir():
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
                "path": str(entry.resolve()),
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


def compute_r_probability(days_since: float, stability: float) -> float:
    """Hybrid decay formula with long-term retention floor (R15-C2)."""
    return compute_retrieval_probability(days_since, stability)


# ---------------------------------------------------------------------------
# Fuzzy search helpers
# ---------------------------------------------------------------------------

FUZZY_THRESHOLD = 0.6


def fuzzy_match_score(query: str, text: str) -> float:
    if not text or not query:
        return 0.0
    q_lower = query.lower().strip()
    t_lower = text.lower()
    if q_lower in t_lower:
        if q_lower == t_lower:
            return 1.0
        if t_lower.startswith(q_lower):
            return 0.95
        return 0.9
    seq = difflib.SequenceMatcher(None, q_lower, t_lower)
    ratio = seq.ratio()
    if ratio < FUZZY_THRESHOLD:
        return 0.0
    return round(ratio, 2)


def extract_snippet(body: str, query: str) -> str:
    if not body or not query:
        return ""
    q_lower = query.lower()
    body_lower = body.lower()
    idx = body_lower.find(q_lower)
    if idx >= 0:
        start = max(0, idx - 40)
        end = min(len(body), idx + len(query) + 60)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(body) else ""
        return prefix + body[start:end].replace("\n", " ") + suffix
    best_idx = -1
    best_ratio = 0.0
    window_size = len(q_lower) + 2
    for i in range(0, max(1, len(body_lower) - window_size + 1), max(1, len(q_lower) // 2)):
        window = body_lower[i:i + window_size]
        ratio = difflib.SequenceMatcher(None, q_lower, window).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_idx = i
    if best_idx >= 0 and best_ratio >= FUZZY_THRESHOLD:
        start = max(0, best_idx - 30)
        end = min(len(body), best_idx + window_size + 50)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(body) else ""
        return prefix + body[start:end].replace("\n", " ") + suffix
    return body[:120].replace("\n", " ") + ("..." if len(body) > 120 else "")


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
    intensity: int = Field(default=5, ge=1, le=10)
    body: str = Field(default="")
    type: str = Field(default="atom", description="atom | schema")
    schema: str | None = None
    maturity: str = Field(default="draft")
    imports: dict[str, list[str]] | None = Field(
        default=None,
        description="Dependency map by strength",
    )


class UpdateMemoryRequest(BaseModel):
    body: str | None = None
    summary: str | None = None
    tags: list[str] | None = None
    intensity: int | None = Field(default=None, ge=1, le=10)
    status: str | None = None
    maturity: str | None = None
    change_note: str | None = None
    imports: dict[str, list[str]] | None = None
    stability: float | None = Field(default=None, gt=0.0, le=365.0)


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
