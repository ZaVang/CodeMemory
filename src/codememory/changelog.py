"""Changelog command — view change history for a memory."""

from __future__ import annotations

from pathlib import Path

from .core import parse_frontmatter
from .index import load_index


def changelog(root_dir: Path, memory_id: str) -> str:
    """Read the changelog for a memory and return formatted output.

    Returns formatted text suitable for display or empty string if no history.
    """
    index = load_index(root_dir)
    if memory_id not in index.memories:
        return f"Error: Memory '{memory_id}' not found in index. Did you reindex?"

    entry = index.memories[memory_id]
    file_path = root_dir / entry.path
    meta, _body = parse_frontmatter(file_path)

    change_log = meta.get("change_log", [])
    if not isinstance(change_log, list) or not change_log:
        return f"No change history for '{memory_id}'."

    lines: list[str] = []
    lines.append(f"# Changelog for '{memory_id}'\n")
    for record in change_log:
        if isinstance(record, dict):
            ver = record.get("version", "?")
            date = record.get("date", "?")
            note = record.get("note", "")
            lines.append(f"v{ver} ({date}): {note}")
        elif isinstance(record, str):
            lines.append(f"- {record}")
    return "\n".join(lines)
