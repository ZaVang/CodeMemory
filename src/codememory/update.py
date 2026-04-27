"""Memory update: version control, change tracking, summary_hash recalc."""

import sys
from datetime import datetime, date
from pathlib import Path

import yaml

from .core import compute_body_hash, get_memory_path, parse_frontmatter
from .index import reindex


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


def update(
    root_dir: Path,
    memory_id: str,
    body: str | None = None,
    summary: str | None = None,
    change_note: str | None = None,
    status: str | None = None,
    import_required: list[str] | None = None,
    import_recommended: list[str] | None = None,
    import_related: list[str] | None = None,
) -> Path:
    """Update an existing memory with version control and change tracking.

    Args:
        root_dir: The memory root directory.
        memory_id: The memory identifier to update.
        body: New body text (optional).
        summary: New summary (optional).
        change_note: Required explanation of what changed and why.
        status: New status: active, archived, superseded, or draft.
        import_required: New required imports list (replaces existing).
        import_recommended: New recommended imports list (replaces existing).
        import_related: New related imports list (replaces existing).

    Returns:
        Path to the updated file.
    """
    if not change_note:
        print(
            "Error: --change-note is required for update operations.",
            file=sys.stderr,
        )
        sys.exit(1)

    file_path = get_memory_path(root_dir, memory_id)

    if not file_path.exists():
        print(
            f"Error: Memory '{memory_id}' not found at {file_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Read and parse existing file
    raw = file_path.read_text(encoding="utf-8-sig")
    parts = raw.split("---", 2)

    if len(parts) < 3:
        print(
            f"Error: {file_path} does not have valid YAML frontmatter",
            file=sys.stderr,
        )
        sys.exit(1)

    frontmatter_str = parts[1]
    existing_body = parts[2]

    try:
        meta = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError as e:
        print(f"Error parsing YAML in {file_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Check protected
    if meta.get("protected") is True:
        print(
            f"Warning: Memory '{memory_id}' is protected. "
            "Update will proceed but protection flag remains.",
            file=sys.stderr,
        )

    # Version increment
    old_version = meta.get("version", 1)
    new_version = old_version + 1
    meta["version"] = new_version

    # Update date
    today = datetime.now().strftime("%Y-%m-%d")
    meta["updated"] = today

    # Change log
    previous_note = meta.get("change_note")
    change_log = meta.get("change_log", [])
    if not isinstance(change_log, list):
        change_log = []

    # If there was a previous change_note not yet in log, add it
    if previous_note and previous_note not in [c.get("note", "") for c in change_log]:
        change_log_entry = {
            "version": old_version,
            "date": _serialize_date(meta.get("updated", today)),
            "note": str(previous_note),
        }
        change_log.insert(0, change_log_entry)

    # Add new change entry
    change_log_entry = {
        "version": new_version,
        "date": today,
        "note": change_note,
    }
    change_log.insert(0, change_log_entry)
    meta["change_log"] = change_log

    # Move change_note to new value
    meta["change_note"] = change_note

    # Update body if provided
    new_body = existing_body
    if body is not None:
        new_body = body

    # Update summary if provided
    if summary is not None:
        meta["summary"] = summary

    # Update status if provided
    if status is not None:
        valid_statuses = {"active", "archived", "superseded", "draft"}
        if status not in valid_statuses:
            print(
                f"Error: Invalid status '{status}'. "
                f"Must be one of: {', '.join(sorted(valid_statuses))}",
                file=sys.stderr,
            )
            sys.exit(1)
        meta["status"] = status

    # Update imports if provided
    if "imports" not in meta:
        meta["imports"] = {}

    imports = meta["imports"]
    if not isinstance(imports, dict):
        imports = {}

    if import_required is not None:
        imports["required"] = import_required
    if import_recommended is not None:
        imports["recommended"] = import_recommended
    if import_related is not None:
        imports["related"] = import_related

    if import_required is not None or import_recommended is not None or import_related is not None:
        meta["imports"] = imports

    # Recompute summary_hash only when summary is explicitly updated.
    # When only body changes, leave old summary_hash so stale detection works.
    if summary is not None:
        meta["summary_hash"] = compute_body_hash(new_body.strip())

    # Format frontmatter values (convert dates)
    meta = _format_frontmatter_value(meta)

    # Serialize and write
    yaml_str = yaml.dump(meta, allow_unicode=True, sort_keys=False)
    content = f"---\n{yaml_str}---\n{new_body}"

    file_path.write_text(content, encoding="utf-8")
    print(f"Updated {memory_id} to version {new_version}")

    # Auto-update index
    print("Updating index...")
    reindex(root_dir)

    return file_path
