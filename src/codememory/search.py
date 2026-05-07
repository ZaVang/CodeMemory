"""Memory search: query by summary, tags, type, sorted by dependency count."""

from pathlib import Path

from .index import load_index
from .models import IndexData


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
    has_imports: bool = False,
    has_schema: bool = False,
) -> list[dict]:
    """Search memories by query, tags, type, status, maturity, and/or semantic type.

    Builds output dicts from MemoryEntry.model_dump() to eliminate field divergence
    between search output and the canonical data model (R15-C4).
    Any field added to MemoryEntry automatically appears in search results.

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
        if has_imports:
            imports_dict = entry.imports
            if not isinstance(imports_dict, dict) or not any(
                imports_dict.get(k) for k in ("required", "recommended", "related")
            ):
                continue
        if has_schema and not entry.schema:
            continue

        # R15-C4: Build output from model_dump() + computed fields.
        # This ensures all MemoryEntry fields are present, eliminating
        # "field missing from search output" bugs permanently.
        dump = entry.model_dump(mode="json")
        dump["id"] = mid  # Ensure id uses the index key
        dump["dependents"] = _count_dependents(mid, index)
        results.append(dump)

    results.sort(key=lambda r: (-r["dependents"], -r["access_count"], r["id"]))
    return results
