"""Memory update: version control, change tracking, summary_hash recalc."""

import logging
import sys
from datetime import datetime, date
from pathlib import Path

import yaml

from .core import compute_body_hash, get_memory_path
from .index import reindex

_logger = logging.getLogger("codememory")


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


def _transition_proposed(root_dir: Path, memory_id: str, new_status: str, op_name: str) -> Path:
    """Transition a proposed memory to a final status (merge/reject shared core)."""
    file_path = get_memory_path(root_dir, memory_id)

    if not file_path.exists():
        _logger.error("Memory '%s' not found at %s", memory_id, file_path)
        sys.exit(1)

    raw = file_path.read_text(encoding="utf-8-sig")
    parts = raw.split("---", 2)
    if len(parts) < 3:
        _logger.error("%s does not have valid YAML frontmatter", file_path)
        sys.exit(1)

    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as e:
        _logger.error("Error parsing YAML in %s: %s", file_path, e)
        sys.exit(1)

    if meta.get("status") != "proposed":
        _logger.error(
            "Cannot %s '%s': status is '%s', expected 'proposed'.",
            op_name, memory_id, meta.get("status"),
        )
        sys.exit(1)

    meta["status"] = new_status
    meta["updated"] = datetime.now().strftime("%Y-%m-%d")
    meta = _format_frontmatter_value(meta)

    yaml_str = yaml.dump(meta, allow_unicode=True, sort_keys=False)
    file_path.write_text(f"---\n{yaml_str}---{parts[2]}", encoding="utf-8")
    print(f"{op_name.capitalize()}d {memory_id}: proposed -> {new_status}")

    print("Updating index...")
    reindex(root_dir)

    try:
        from .log import append_log
        append_log(root_dir, op_name, f"{memory_id}: proposed -> {new_status}")
    except ImportError:
        pass

    return file_path


def merge(root_dir: Path, memory_id: str) -> Path:
    """Merge a proposal: patch-queue id first, else proposed atom -> active."""
    from .proposals import load_proposal, merge_proposal

    if load_proposal(root_dir, memory_id) is not None:
        return merge_proposal(root_dir, memory_id)
    return _transition_proposed(root_dir, memory_id, "active", "merge")


def reject(root_dir: Path, memory_id: str) -> Path | None:
    """Reject a proposal: patch-queue id first, else proposed atom -> archived."""
    from .proposals import load_proposal, reject_proposal

    if load_proposal(root_dir, memory_id) is not None:
        reject_proposal(root_dir, memory_id)
        return None
    return _transition_proposed(root_dir, memory_id, "archived", "reject")


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
    source_ref: str | None = None,
    source_ref_summary: str | None = None,
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
        source_ref: Asset artifact_id to append to source_refs (Phase A).
        source_ref_summary: Optional summary for the appended source_ref.

    Returns:
        Path to the updated file.
    """
    if not change_note:
        _logger.error("--change-note is required for update operations.")
        sys.exit(1)

    file_path = get_memory_path(root_dir, memory_id)

    if not file_path.exists():
        _logger.error("Memory '%s' not found at %s", memory_id, file_path)
        sys.exit(1)

    # Read and parse existing file
    raw = file_path.read_text(encoding="utf-8-sig")
    parts = raw.split("---", 2)

    if len(parts) < 3:
        _logger.error("%s does not have valid YAML frontmatter", file_path)
        sys.exit(1)

    frontmatter_str = parts[1]
    existing_body = parts[2]

    try:
        meta = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError as e:
        _logger.error("Error parsing YAML in %s: %s", file_path, e)
        sys.exit(1)

    # Check protected
    if meta.get("protected") is True:
        _logger.warning(
            "Memory '%s' is protected. Update will proceed but protection flag remains.",
            memory_id,
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
            _logger.error(
                "Invalid status '%s'. Must be one of: %s",
                status, ", ".join(sorted(valid_statuses)),
            )
            sys.exit(1)
        meta["status"] = status
        # Auto-set maturity: superseded status → superseded maturity
        if status == "superseded":
            meta["maturity"] = "superseded"

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

    # Append asset reference (Phase A: CLI write path for source_refs).
    # Existence of the artifact is not enforced here; validate reports
    # missing artifacts via SOURCE-REF-WARN without blocking the write.
    if source_ref is not None:
        source_refs = meta.get("source_refs", [])
        if not isinstance(source_refs, list):
            source_refs = []
        existing_ids = {r.get("artifact_id") for r in source_refs if isinstance(r, dict)}
        if source_ref in existing_ids:
            _logger.warning(
                "source_ref '%s' already present on %s; skipping duplicate.",
                source_ref, memory_id,
            )
        else:
            source_refs.append({
                "artifact_id": source_ref,
                "summary": source_ref_summary or "",
                "disclosure_hint": "anchor",
            })
            meta["source_refs"] = source_refs

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

    # Append to global log
    try:
        from .log import append_log
        append_log(root_dir, "update", f"{memory_id} v{new_version}: {change_note}")
    except ImportError:
        pass

    return file_path
