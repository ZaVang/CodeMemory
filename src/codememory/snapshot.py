"""Snapshot persistence — export TransientDAG as a composite .md memory."""

import sys
from datetime import datetime, date
from pathlib import Path

import yaml

from .core import compute_body_hash


def _serialize_date(obj):
    """Convert date objects to string for YAML serialization."""
    if isinstance(obj, (datetime, date)):
        return obj.strftime("%Y-%m-%d")
    return obj


def _format_frontmatter_value(value):
    """Recursively convert date objects in frontmatter values for safe YAML dump."""
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, dict):
        return {k: _format_frontmatter_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_format_frontmatter_value(v) for v in value]
    return value


def snapshot_dag(root_dir: Path, dag, snapshot_id: str) -> Path:
    """Export a TransientDAG as a persistent composite .md memory.

    Args:
        root_dir: The memory root directory.
        dag: A TransientDAG instance with added nodes.
        snapshot_id: The snapshot identifier (used in filename).

    Returns:
        Path to the created snapshot .md file.
    """
    from .transient import TransientDAG

    nodes = list(dag._nodes.values())

    if not nodes:
        print("Error: TransientDAG is empty, nothing to snapshot.", file=sys.stderr)
        sys.exit(1)

    # Collect all required imports from the DAG edges
    # A required import is any node referenced as a required dep by another node
    required_imports: list[str] = []
    recommended_imports: list[str] = []
    related_imports: list[str] = []

    seen_required: set[str] = set()
    seen_recommended: set[str] = set()
    seen_related: set[str] = set()

    for node in nodes:
        imports = node.imports or {}
        for ref in imports.get("required", []):
            ref_id = ref if isinstance(ref, str) else ref.get("id", "")
            if ref_id and ref_id not in seen_required:
                required_imports.append(ref_id)
                seen_required.add(ref_id)
        for ref in imports.get("recommended", []):
            ref_id = ref if isinstance(ref, str) else ref.get("id", "")
            if ref_id and ref_id not in seen_recommended:
                recommended_imports.append(ref_id)
                seen_recommended.add(ref_id)
        for ref in imports.get("related", []):
            ref_id = ref if isinstance(ref, str) else ref.get("id", "")
            if ref_id and ref_id not in seen_related:
                related_imports.append(ref_id)
                seen_related.add(ref_id)

    # Assemble body: all node contents
    body_parts: list[str] = []
    body_parts.append(f"# Snapshot: {snapshot_id}\n")
    body_parts.append(f"Snapshotted {len(nodes)} transient nodes.\n")

    for i, node in enumerate(nodes):
        body_parts.append(f"## [{i + 1}/{len(nodes)}] {node.id} ({node.type})\n")
        body_parts.append(f"\n{node.body}\n")

    body = "\n".join(body_parts)

    # Build frontmatter
    today = datetime.now().strftime("%Y-%m-%d")

    imports_dict: dict[str, list[str]] = {}
    if required_imports:
        imports_dict["required"] = required_imports
    if recommended_imports:
        imports_dict["recommended"] = recommended_imports
    if related_imports:
        imports_dict["related"] = related_imports

    frontmatter = {
        "type": "composite",
        "id": f"user/snapshots/{snapshot_id}",
        "summary": f"Session snapshot: {snapshot_id}",
        "status": "active",
        "created": today,
        "updated": today,
        "version": 1,
        "tags": ["snapshot"],
        "intensity": 7,
        "source": {
            "platform": "codememory",
            "created_by": "snapshot",
        },
    }

    if imports_dict:
        frontmatter["imports"] = imports_dict

    frontmatter["summary_hash"] = compute_body_hash(body)

    # Format for safe serialization
    frontmatter = _format_frontmatter_value(frontmatter)

    # Write file
    snap_dir = root_dir / "user" / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    snap_path = snap_dir / f"{today}-{snapshot_id}.md"

    yaml_str = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
    content = f"---\n{yaml_str}---\n{body}"

    snap_path.write_text(content, encoding="utf-8")
    print(f"Snapshot '{snapshot_id}' saved to {snap_path} ({len(content)} chars)")

    # Auto-update index
    from .index import reindex
    reindex(root_dir)

    return snap_path
