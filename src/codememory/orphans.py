"""Orphan detection: find memory atoms with in-degree zero in the dependency graph."""

from pathlib import Path

from .index import load_index


def find_orphans(
    root_dir: Path,
    type_: str | None = None,
) -> list[dict]:
    """Find memories that are not referenced by any other memory's imports."""
    index = load_index(root_dir)
    memories = index.memories

    referenced: set[str] = set()
    for mid, entry in memories.items():
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
            if ref_id:
                referenced.add(ref_id)

    orphans: list[dict] = []
    for mid, entry in memories.items():
        if mid in referenced:
            continue
        if type_ and entry.type != type_:
            continue

        annotation = "protected" if entry.protected else "unreachable"
        orphans.append({
            "id": mid,
            "type": entry.type,
            "status": entry.status,
            "access_count": entry.access_count,
            "last_access": entry.last_access,
            "annotation": annotation,
        })

    orphans.sort(key=lambda o: (-o["access_count"], o["id"]))
    return orphans
