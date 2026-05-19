"""Memory creation: generate template markdown files with frontmatter."""

import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

from .core import compute_body_hash, get_memory_path
from .index import reindex

_logger = logging.getLogger("codememory")

# R15-C3: Domain-differentiated default stability lookup
# Maps semantic_type (tag) to default stability in days.
# These override the universal default of 14.0 for new memories at creation time.
SEMANTIC_TYPE_STABILITY: dict[str, float] = {
    "schemas": 365.0,          # Schema definitions are permanent reference
    "api": 365.0,               # API documentation is permanent reference
    "architectural-decision": 90.0,  # Architecture decisions have medium lifecycle
    "decision": 90.0,           # General decisions have medium lifecycle
    "research": 90.0,           # Research notes have medium lifecycle
    "context": 30.0,            # Context summaries are medium-term
    "meeting": 7.0,             # Meeting notes decay within a week
    "daily": 5.0,               # Daily notes are ephemeral
    "daily-notes": 5.0,         # Daily notes alias
}


def _default_stability(tags: list[str] | None, schema: str | None, root_dir: Path | None = None) -> float:
    """Determine the default stability for a newly created memory.

    Priority:
    1. Any tag matching a known semantic_type → lookup table value
    2. Schema reference → inherit schema's stability default (365d)
    3. Universal default 14.0
    """
    # Check tags for semantic type matches
    if tags:
        for tag in tags:
            if tag in SEMANTIC_TYPE_STABILITY:
                return SEMANTIC_TYPE_STABILITY[tag]

    # Check if the schema itself has a stability default
    if schema:
        # Schemas get permanent retention
        if schema.startswith("schemas/"):
            return 365.0
        # Could load schema entry from index to inherit its stability,
        # but keeping it simple: schema-backed memories get 365d
        return 365.0

    return 14.0


def create(
    root_dir: Path,
    memory_type: str,
    memory_id: str,
    schema: str | None = None,
    intensity: int = 5,
    tags: list[str] | None = None,
    dry_run: bool = False,
    maturity: str = "draft",
    stability: float | None = None,
    cache_stable: bool = False,
    lifecycle: str = "permanent",
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
        stability: Explicit stability override. If None, use domain default.
        cache_stable: Mark as suitable for LLM cache prefix.
        lifecycle: permanent | stable | ephemeral.

    Returns:
        Path to the created file, or None if dry_run.
    """
    file_path = get_memory_path(root_dir, memory_id)

    if not dry_run and file_path.exists():
        _logger.error("Memory %s already exists at %s", memory_id, file_path)
        sys.exit(1)

    now = datetime.now().strftime("%Y-%m-%d")

    tag_list = tags if tags is not None else ["untagged"]

    # R15-C3: determine default stability from semantic_type / schema
    # Explicit stability override takes precedence over domain defaults
    if stability is None:
        stability = _default_stability(tag_list, schema, root_dir)
    else:
        stability = max(stability, 0.1)  # safety floor

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
        "stability": stability,
        "cache_stable": cache_stable,
        "lifecycle": lifecycle,
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
        "\n"
    )

    # Use stripped body for hash so it matches what _parse_frontmatter returns.
    # Without strip(), the leading \n in body_template causes a permanent stale
    # false positive because the stale-check parses with .strip().
    frontmatter["summary_hash"] = compute_body_hash(body_template.strip())

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
