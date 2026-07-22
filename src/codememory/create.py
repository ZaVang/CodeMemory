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
    tags: list[str] | None = None,
    dry_run: bool = False,
    maturity: str = "draft",
    cache_stable: bool = False,
    lifecycle: str = "permanent",
    propose: bool = False,
    summary: str | None = None,
    body: str | None = None,
    import_required: list[str] | None = None,
    import_recommended: list[str] | None = None,
    import_related: list[str] | None = None,
    created_by: str = "user",
) -> Path | None:
    """Create a new memory file with frontmatter template.

    Args:
        root_dir: The memory root directory.
        memory_type: 'atom' or 'schema'.
        memory_id: The memory identifier (e.g. 'user/ideas/my-thesis').
        schema: Optional schema ID reference.
        tags: Custom tags list (defaults to ["untagged"]).
        dry_run: If True, preview frontmatter + body to stdout without writing.
        maturity: Initial maturity (default "draft").
        cache_stable: Mark as suitable for LLM cache prefix.
        lifecycle: permanent | stable | ephemeral.
        propose: If True, write the atom as a proposal (status: proposed);
            it stays out of default build/search until merged.
        summary: Optional complete initial summary. CLI template creation keeps
            the historical TODO default when omitted.
        body: Optional complete initial Markdown body. CLI template creation
            keeps the historical generated heading when omitted.
        import_required/import_recommended/import_related: Optional initial
            imports lists, written in the same shape used by update.
        created_by: Audit identity for the initial source/evidence metadata.

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
        "summary": summary if summary is not None else "TODO: fill in summary",
        "status": "proposed" if propose else "active",
        "created": now,
        "updated": now,
        "version": 1,
        "tags": tag_list,
        "maturity": maturity,
        "cache_stable": cache_stable,
        "lifecycle": lifecycle,
        "evidence": {
            "contributors": [created_by],
            "sessions": [],
        },
        "source": {
            "platform": "manual",
            "created_by": created_by,
        },
    }

    if schema:
        frontmatter["schema"] = schema

    imports: dict[str, list[str]] = {}
    if import_required is not None:
        imports["required"] = import_required
    if import_recommended is not None:
        imports["recommended"] = import_recommended
    if import_related is not None:
        imports["related"] = import_related
    if imports:
        frontmatter["imports"] = imports

    body_template = (
        f"\n# {memory_id.split('/')[-1].replace('-', ' ').title()}\n\n"
        "\n"
    )

    body_content = body.strip() if body is not None else body_template.strip()

    # Use stripped body for hash so it matches what _parse_frontmatter returns.
    # Without strip(), the leading \n in body_template causes a permanent stale
    # false positive because the stale-check parses with .strip().
    frontmatter["summary_hash"] = compute_body_hash(body_content)

    yaml_str = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
    content = f"---\n{yaml_str}---\n{body_content}\n"

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
