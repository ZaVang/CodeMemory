"""Memory validation: broken links, schema compliance, cycle detection, decay suggestions."""

import sys
from datetime import datetime, timedelta
from pathlib import Path

from .core import parse_frontmatter
from .index import load_index
from .resolve import _get_imports, build_dag, find_cycle_participants


def check_schema_compliance(metadata: dict, schemas: dict) -> list[str]:
    """Check if an instance's metadata conforms to its declared schema."""
    schema_id = metadata.get("schema")
    if not schema_id:
        return []
    schema = schemas.get(schema_id)
    if not schema:
        return [f"Schema '{schema_id}' not found"]
    return [
        f"Missing required field: {f['name']}"
        for f in schema.get("fields", [])
        if f.get("required") and f["name"] not in metadata
    ]


def _compute_in_degree(memory_id: str, index: dict) -> int:
    """Count how many other memories reference this one via imports."""
    count = 0
    for mid, entry in index["memories"].items():
        if mid == memory_id:
            continue
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
                return 1  # Only need to know if referenced at all
    return 0


def _check_decay(memory_id: str, entry: dict, index: dict) -> list[str]:
    """Check whether a memory is at risk of decay.

    Returns a list of warning messages (empty if no risk).
    """
    warnings = []

    # Protected memories (intensity >= 8) are never at risk
    intensity = entry.get("intensity", 5)
    if intensity >= 8:
        return warnings

    # If it has been accessed recently (within 30 days), not at risk
    access_count = entry.get("access_count", 0)
    last_access_str = entry.get("last_access")
    if access_count > 0 and last_access_str:
        try:
            # Parse ISO datetime (may have microseconds or be date-only)
            last_access = datetime.fromisoformat(last_access_str)
            cutoff = datetime.now() - timedelta(days=30)
            if last_access > cutoff:
                return warnings
        except (ValueError, TypeError):
            pass  # If we can't parse the date, proceed with warning

    # If it's referenced by other memories (in_degree > 0), not at risk
    if _compute_in_degree(memory_id, index) > 0:
        return warnings

    # Otherwise, at risk of decay
    warnings.append(
        f"{memory_id} has low access (access_count={access_count}), "
        f"no recent access, and is not referenced by any other memory. "
        f"Consider re-linking or archiving this memory."
    )
    return warnings


def validate(root_dir: Path) -> tuple[int, int]:
    """Run integrity checks on all indexed memories.

    Returns (error_count, warning_count).
    """
    index = load_index(root_dir)
    memories = index["memories"]

    errors = 0
    warnings = 0

    # Build full schema dict for lookup
    schemas = {}
    for mid, entry in memories.items():
        if entry["type"] == "schema":
            file_path = root_dir / entry["path"]
            meta, _ = parse_frontmatter(file_path)
            schemas[mid] = meta

    print("Running CodeMemory Validation...\n")

    for mid, entry in memories.items():
        # 1. Broken link check
        deps = _get_imports(entry, "full")
        for dep in deps:
            if dep not in memories:
                print(f"[ERROR] {mid} imports non-existent memory: {dep}")
                errors += 1

        # 2. Schema compliance
        if entry["type"] == "instance":
            file_path = root_dir / entry["path"]
            meta, _ = parse_frontmatter(file_path)
            compliance_errors = check_schema_compliance(meta, schemas)
            for err in compliance_errors:
                print(f"[ERROR] {mid} schema compliance: {err}")
                errors += 1

        # 3. Cycle check
        graph = build_dag(mid, "required", index)
        cycle_ids = find_cycle_participants(graph)
        if cycle_ids and mid in cycle_ids:
            print(
                f"[WARNING] {mid} is part of a circular dependency involving: {cycle_ids}"
            )
            print(
                "          Fix: Consider merging atoms or placing in a composite as siblings."
            )
            warnings += 1

        # 4. Decay check (only for non-schema types)
        if entry["type"] != "schema":
            decay_warnings = _check_decay(mid, entry, index)
            for msg in decay_warnings:
                print(f"[DECAY-WARN] {msg}")
                warnings += 1

    print(f"\nValidation complete. {len(memories)} memories checked.")
    print(f"Errors: {errors}, Warnings: {warnings}")
    return errors, warnings
