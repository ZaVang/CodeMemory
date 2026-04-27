"""Orphan detection: find memory atoms with in-degree zero in the dependency graph."""

from pathlib import Path

from .index import load_index


def find_orphans(
    root_dir: Path,
    type_: str | None = None,
    min_intensity: int | None = None,
) -> list[dict]:
    """Find memories that are not referenced by any other memory's imports.

    An atom/schema/instance/composite is "orphaned" if no other indexed memory
    lists it as a required, recommended, or related import.

    Args:
        root_dir: The memory root directory.
        type_: Optional filter by memory type.
        min_intensity: Optional minimum intensity filter.

    Returns:
        List of orphan entries with id, type, intensity, status, access_count,
        last_access, and an 'annotation' field ("protected" or "decay-risk").
    """
    index = load_index(root_dir)
    memories = index["memories"]

    # Build the set of all IDs that are referenced by ANY memory's imports
    referenced: set[str] = set()
    for mid, entry in memories.items():
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
            if ref_id:
                referenced.add(ref_id)

    orphans = []
    for mid, entry in memories.items():
        if mid in referenced:
            continue

        # Optional type filter
        if type_ and entry.get("type") != type_:
            continue

        # Optional intensity filter
        intensity = entry.get("intensity", 5)
        if min_intensity is not None and intensity < min_intensity:
            continue

        annotation = "protected" if intensity >= 8 else "decay-risk"
        orphans.append({
            "id": mid,
            "type": entry.get("type", "?"),
            "intensity": intensity,
            "status": entry.get("status", "active"),
            "access_count": entry.get("access_count", 0),
            "last_access": entry.get("last_access"),
            "annotation": annotation,
        })

    # Sort by intensity descending (protected first), then id
    orphans.sort(key=lambda o: (-o["intensity"], o["id"]))
    return orphans
