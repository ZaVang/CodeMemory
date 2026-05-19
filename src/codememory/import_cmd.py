"""Cold-start import: extract initial draft memories from raw text."""

import logging
from datetime import datetime
from pathlib import Path

import yaml

from .core import compute_body_hash, get_memory_path

_logger = logging.getLogger("codememory")


def import_text(
    root_dir: Path,
    text: str,
    extract_types: list[str] | None = None,
) -> list[Path]:
    """Import memories from raw text, producing draft-atom .md files.

    Each paragraph becomes a separate atom memory with maturity=draft.

    Args:
        root_dir: The memory root directory.
        text: Input text to extract memories from.
        extract_types: Tags to apply to extracted memories (e.g. ["preferences"]).

    Returns:
        List of Paths to created memory files.
    """
    if not text or not text.strip():
        _logger.error("No input text provided.")
        return []

    # Split text into paragraphs (non-empty lines)
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        _logger.error("No content extracted from input.")
        return []

    tags = (extract_types or []) + ["imported"]
    now = datetime.now().strftime("%Y-%m-%d")
    created: list[Path] = []

    # Generate a batch prefix from timestamp
    batch = datetime.now().strftime("%Y%m%d-%H%M%S")

    for i, para in enumerate(paragraphs):
        # Generate a memory ID from the paragraph content
        # Use first few words as a slug
        words = para.split()
        slug_words = [w.strip(".,;:!?()[]{}。，；：！？、") for w in words[:5]]
        slug = "-".join(slug_words).lower()[:60]
        if not slug:
            slug = f"import-{i}"
        memory_id = f"user/test/import-{batch}-{slug}" if "test" in (extract_types or []) else f"user/imports/{batch}-{slug}"

        # Truncate summary from first 100 chars
        summary = para[:100] + ("..." if len(para) > 100 else "")

        frontmatter = {
            "type": "atom",
            "id": memory_id,
            "summary": summary,
            "status": "active",
            "created": now,
            "updated": now,
            "version": 1,
            "tags": tags,
            "intensity": 3,
            "maturity": "draft",
            "evidence": {
                "contributors": ["import"],
                "sessions": [],
            },
            "source": {
                "platform": "import",
                "created_by": "codememory import",
            },
        }

        body = f"\n# {memory_id.split('/')[-1].replace('-', ' ').title()}\n\n{para}\n"
        frontmatter["summary_hash"] = compute_body_hash(body)

        yaml_str = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
        content = f"---\n{yaml_str}---\n{body}"

        file_path = get_memory_path(root_dir, memory_id)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        print(f"Imported: {file_path} ({len(para)} chars)")
        created.append(file_path)

    # Reindex
    from .index import reindex
    reindex(root_dir)

    # Append to global log
    try:
        from .log import append_log
        append_log(root_dir, "create", f"import batch: {len(created)} memories")
    except ImportError:
        pass

    return created
