"""Index management: load, save, and rebuild the memory index."""

import json
import sys
from datetime import date, datetime
from pathlib import Path

from .core import parse_frontmatter


def get_index_path(root_dir: Path) -> Path:
    return root_dir / ".codememory" / "index.json"


def load_index(root_dir: Path) -> dict:
    """Load the index from disk. Returns a fresh index dict if not found."""
    idx_path = get_index_path(root_dir)
    if not idx_path.exists():
        return {"version": 1, "updated": datetime.now().isoformat(), "memories": {}}
    try:
        with open(idx_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load index: {e}", file=sys.stderr)
        return {"version": 1, "updated": datetime.now().isoformat(), "memories": {}}


class DateEncoder(json.JSONEncoder):
    """Handle datetime.date objects that come from YAML parsing."""

    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def save_index(root_dir: Path, index_data: dict):
    """Save the index to disk with date-aware JSON encoding."""
    idx_path = get_index_path(root_dir)
    idx_path.parent.mkdir(parents=True, exist_ok=True)
    index_data["updated"] = datetime.now().isoformat()
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False, cls=DateEncoder)


def reindex(root_dir: Path) -> int:
    """Scan memory directories and rebuild the index from scratch.

    Returns the count of indexed memories.
    """
    index_data = {
        "version": 1,
        "updated": datetime.now().isoformat(),
        "memories": {},
    }

    search_dirs = ["user", "self", "schemas"]
    count = 0

    for d in search_dirs:
        dir_path = root_dir / d
        if not dir_path.exists():
            continue

        for filepath in dir_path.rglob("*.md"):
            try:
                rel_path = filepath.relative_to(root_dir).as_posix()
                memory_id = (
                    str(filepath.relative_to(root_dir).with_suffix(""))
                    .replace("\\", "/")
                )

                meta, _ = parse_frontmatter(filepath)

                # Require type + id to be a valid memory
                if "type" not in meta or "id" not in meta:
                    continue

                actual_id = meta.get("id", memory_id)

                entry = {
                    "type": meta.get("type"),
                    "summary": meta.get("summary", ""),
                    "status": meta.get("status", "active"),
                    "tags": meta.get("tags", []),
                    "created": meta.get("created", ""),
                    "updated": meta.get("updated", ""),
                    "version": meta.get("version", 1),
                    "path": rel_path,
                }

                if "schema" in meta:
                    entry["schema"] = meta["schema"]
                if "imports" in meta:
                    entry["imports"] = meta["imports"]

                index_data["memories"][actual_id] = entry
                count += 1
            except Exception as e:
                print(f"Error indexing {filepath}: {e}", file=sys.stderr)

    save_index(root_dir, index_data)
    print(f"Reindexed {count} memories successfully.")
    return count
