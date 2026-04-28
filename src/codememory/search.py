"""Memory search: query by summary, tags, type, sorted by dependency count."""

from pathlib import Path

from .index import load_index
from .models import IndexData, MemoryEntry


def _count_dependents(memory_id: str, index: IndexData) -> int:
    """Count how many other memories import this one."""
    count = 0
    for mid, entry in index.memories.items():
        imports_dict = entry.imports
        if not isinstance(imports_dict, dict):
            continue
        all_refs = (
            imports_dict.get("required", [])
            + imports_dict.get("recommended", [])
            + imports_dict.get("related", [])
        )
        for ref in all_refs:
            ref_id = ref if isinstance(ref, str) else ref.get("id", "")
            if ref_id == memory_id:
                count += 1
                break
    return count


def search(
    root_dir: Path,
    query: str | None = None,
    tags: list[str] | None = None,
    type_: str | None = None,
    status: str | None = None,
    maturity: str | None = None,
    semantic_type: str | None = None,
) -> list[dict]:
    """Search memories by query, tags, type, status, maturity, and/or semantic type.

    Results are sorted by dependents descending, then access_count descending,
    then id ascending.
    """
    index = load_index(root_dir)
    results: list[dict] = []

    for mid, entry in index.memories.items():
        if type_ and entry.type != type_:
            continue
        if status and entry.status != status:
            continue
        if maturity and entry.maturity != maturity:
            continue
        if semantic_type and semantic_type not in entry.tags:
            continue
        if tags:
            if not all(t in entry.tags for t in tags):
                continue
        if query:
            if query.lower() not in entry.summary.lower():
                continue

        dependents = _count_dependents(mid, index)
        results.append({
            "id": mid,
            "type": entry.type,
            "summary": entry.summary,
            "status": entry.status,
            "tags": entry.tags,
            "path": entry.path,
            "intensity": entry.intensity,
            "access_count": entry.access_count,
            "last_access": entry.last_access,
            "dependents": dependents,
            "maturity": entry.maturity,
        })

    results.sort(key=lambda r: (-r["dependents"], -r["access_count"], r["id"]))
    return results
