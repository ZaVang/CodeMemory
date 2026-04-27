"""Memory search: query by summary, tags, type, sorted by dependency count."""

from pathlib import Path

from .index import load_index


def _count_dependents(memory_id: str, index: dict) -> int:
    """Count how many other memories import this one."""
    count = 0
    for mid, entry in index["memories"].items():
        imports_dict = entry.get("imports", {})
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
) -> list[dict]:
    """Search memories by query, tags, type, and/or status.

    Results are sorted by dependents descending, then access_count descending,
    then id ascending for stability.

    Args:
        root_dir: The memory root directory.
        query: Case-insensitive substring match against summary.
        tags: Filter to memories that have ALL listed tags.
        type_: Filter by memory type (atom, schema, instance, composite).
        status: Filter by memory status (active, archived, superseded, draft).

    Returns:
        List of matching memory entries with 'dependents' count added.
    """
    index = load_index(root_dir)
    results = []

    for mid, entry in index["memories"].items():
        # Filter by type
        if type_ and entry.get("type") != type_:
            continue

        # Filter by status
        if status and entry.get("status") != status:
            continue

        # Filter by tags (AND logic)
        if tags:
            entry_tags = entry.get("tags", [])
            if not all(t in entry_tags for t in tags):
                continue

        # Filter by query (case-insensitive summary match)
        if query:
            summary = entry.get("summary", "").lower()
            if query.lower() not in summary:
                continue

        dependents = _count_dependents(mid, index)
        access_count = entry.get("access_count", 0)
        results.append({**entry, "id": mid, "dependents": dependents, "access_count": access_count})

    # Sort by dependents descending, access_count descending, then id ascending
    results.sort(key=lambda r: (-r["dependents"], -r["access_count"], r["id"]))
    return results
