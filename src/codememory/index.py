"""Index management: load, save, and rebuild the memory index."""

import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path

from .core import parse_frontmatter
from .models import IndexData, MemoryEntry

_logger = logging.getLogger("codememory")


def get_index_path(root_dir: Path) -> Path:
    return root_dir / ".codememory" / "index.json"


def load_index(root_dir: Path) -> IndexData:
    """Load the index from disk. Returns a fresh IndexData if not found."""
    idx_path = get_index_path(root_dir)
    if not idx_path.exists():
        return IndexData()
    try:
        with open(idx_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return IndexData.model_validate(raw)
    except Exception as e:
        _logger.warning("Could not load index: %s", e)
        return IndexData()


class DateEncoder(json.JSONEncoder):
    """Handle datetime.date objects that come from YAML parsing."""

    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def save_index(root_dir: Path, index_data: IndexData):
    """Save the index to disk with date-aware JSON encoding."""
    idx_path = get_index_path(root_dir)
    idx_path.parent.mkdir(parents=True, exist_ok=True)
    index_data.updated = datetime.now().isoformat()
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(
            index_data.model_dump(mode="json"),
            f, indent=2, ensure_ascii=False, cls=DateEncoder,
        )


def reindex(root_dir: Path) -> int:
    """Scan memory directories and rebuild the index from scratch.

    Preserves access_count and last_access from the previous index.
    Returns the count of indexed memories.
    """
    old_index = load_index(root_dir)
    old_memories = old_index.memories

    index_data = IndexData()
    search_dirs = ["user", "self", "schemas"]
    count = 0

    for d in search_dirs:
        dir_path = root_dir / d
        if not dir_path.exists():
            continue

        for filepath in dir_path.rglob("*.md"):
            try:
                rel_path = filepath.relative_to(root_dir).as_posix()
                meta, _body = parse_frontmatter(filepath)

                # Require type + id to be a valid memory
                if "type" not in meta or "id" not in meta:
                    continue

                actual_id = meta.get("id")

                # Preserve access stats from old index
                old_entry = old_memories.get(actual_id)

                entry = MemoryEntry(
                    type=meta.get("type", "?"),
                    id=actual_id,
                    summary=meta.get("summary", ""),
                    status=meta.get("status", "active"),
                    tags=meta.get("tags", []),
                    created=meta.get("created", ""),
                    updated=meta.get("updated", ""),
                    version=meta.get("version", 1),
                    path=rel_path,
                    intensity=meta.get("intensity", 5),
                    access_count=old_entry.access_count if old_entry else 0,
                    last_access=old_entry.last_access if old_entry else None,
                )

                if "schema" in meta:
                    entry.schema = meta["schema"]
                if "imports" in meta:
                    entry.imports = meta["imports"]
                if "summary_hash" in meta:
                    entry.summary_hash = meta["summary_hash"]
                if meta.get("protected") is True:
                    entry.protected = True
                if "source" in meta:
                    entry.source = meta["source"]

                index_data.memories[actual_id] = entry
                count += 1
            except Exception as e:
                _logger.error("Error indexing %s: %s", filepath, e)

    save_index(root_dir, index_data)
    print(f"Reindexed {count} memories successfully.")
    return count
