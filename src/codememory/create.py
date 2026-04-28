"""Memory creation: generate template markdown files with frontmatter."""

import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

from .core import compute_body_hash, get_memory_path
from .index import reindex

_logger = logging.getLogger("codememory")


def create(
    root_dir: Path,
    memory_type: str,
    memory_id: str,
    schema: str | None = None,
    intensity: int = 5,
    tags: list[str] | None = None,
    dry_run: bool = False,
    maturity: str = "draft",
) -> Path | None:
    """Create a new memory file with frontmatter template.

    Args:
        root_dir: The memory root directory.
        memory_type: 'atom' or 'schema'.
        memory_id: The memory identifier (e.g. 'user/ideas/my-thesis').
        schema: Optional schema ID reference.
        intensity: Relevance score 1-10 (default 5).
        tags: Custom tags list (defaults to ["untagged"]).
        dry_run: If True, preview frontmatter + body to stdout without writing.
        maturity: Initial maturity (default "draft").

    Returns:
        Path to the created file, or None if dry_run.
    """
    file_path = get_memory_path(root_dir, memory_id)

    if not dry_run and file_path.exists():
        _logger.error("Memory %s already exists at %s", memory_id, file_path)
        sys.exit(1)

    now = datetime.now().strftime("%Y-%m-%d")

    tag_list = tags if tags is not None else ["untagged"]

    frontmatter = {
        "type": memory_type,
        "id": memory_id,
        "summary": "TODO: fill in summary",
        "status": "active",
        "created": now,
        "updated": now,
        "version": 1,
        "tags": tag_list,
        "intensity": intensity,
        "maturity": maturity,
        "evidence": {
            "contributors": ["user"],
            "sessions": [],
        },
        "source": {
            "platform": "manual",
            "created_by": "user",
        },
    }

    if schema:
        frontmatter["schema"] = schema

    if intensity >= 8:
        frontmatter["protected"] = True

    body_template = (
        f"\n# {memory_id.split('/')[-1].replace('-', ' ').title()}\n\n"
        "Write content here...\n"
    )

    frontmatter["summary_hash"] = compute_body_hash(body_template)

    yaml_str = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
    content = f"---\n{yaml_str}---\n{body_template}"

    if dry_run:
        print("=== DRY RUN PREVIEW ===")
        print(content)
        return None

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    print(f"Created memory at {file_path}")

    # Auto-update index
    print("Updating index...")
    reindex(root_dir)

    # Append to global log
    try:
        from .log import append_log
        append_log(root_dir, "create", f"{memory_id} ({memory_type})")
    except ImportError:
        pass

    return file_path
