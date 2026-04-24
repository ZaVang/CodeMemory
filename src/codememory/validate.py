"""Memory validation: broken links, schema compliance, cycle detection."""

import sys
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

    print(f"\nValidation complete. {len(memories)} memories checked.")
    print(f"Errors: {errors}, Warnings: {warnings}")
    return errors, warnings
