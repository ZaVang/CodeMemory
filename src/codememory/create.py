"""Memory creation: generate template markdown files with frontmatter."""

import sys
from datetime import datetime
from pathlib import Path

import yaml

from .core import get_memory_path
from .index import reindex


def create(
    root_dir: Path,
    memory_type: str,
    memory_id: str,
    schema: str | None = None,
    intensity: int = 5,
) -> Path:
    """Create a new memory file with frontmatter template.

    Args:
        root_dir: The memory root directory.
        memory_type: One of 'atom', 'schema', 'instance', 'composite'.
        memory_id: The memory identifier (e.g. 'user/ideas/my-thesis').
        schema: Schema ID (required for type='instance').
        intensity: Relevance score 1-10 (default 5).

    Returns:
        Path to the created file.
    """
    file_path = get_memory_path(root_dir, memory_id)

    if file_path.exists():
        print(
            f"Error: Memory {memory_id} already exists at {file_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d")

    frontmatter = {
        "type": memory_type,
        "id": memory_id,
        "summary": "TODO: fill in summary",
        "status": "active",
        "created": now,
        "updated": now,
        "version": 1,
        "tags": ["untagged"],
        "intensity": intensity,
        "source": {
            "platform": "manual",
            "created_by": "user",
        },
        "summary_hash": "placeholder",
    }

    if schema:
        frontmatter["schema"] = schema

    if memory_type in ("composite", "instance"):
        frontmatter["imports"] = {
            "required": [],
            "recommended": [],
            "related": [],
        }

    body_template = (
        f"\n# {memory_id.split('/')[-1].replace('-', ' ').title()}\n\n"
        "Write content here...\n"
    )

    yaml_str = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
    content = f"---\n{yaml_str}---\n{body_template}"

    file_path.write_text(content, encoding="utf-8")
    print(f"Created memory at {file_path}")

    # Auto-update index
    print("Updating index...")
    reindex(root_dir)

    return file_path
