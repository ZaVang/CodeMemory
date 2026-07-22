"""Source corpus ingestion for Markdown migration."""

from __future__ import annotations

from pathlib import Path

from codememory.sources import compute_file_sha256, default_source_id

from .models import SourceDoc


def scan_markdown_corpus(source_root: Path) -> list[SourceDoc]:
    """Scan a file or directory for Markdown source docs without modifying them."""
    root = source_root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"source root not found: {source_root}")

    if root.is_file():
        files = [root] if root.suffix.lower() == ".md" else []
        rel_base = root.parent
    else:
        rel_base = root
        files = [
            path
            for path in sorted(root.rglob("*.md"))
            if ".codememory" not in path.parts
        ]

    docs: list[SourceDoc] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        rel_path = path.relative_to(rel_base).as_posix()
        resolved_path = path.resolve()
        uri = str(resolved_path)
        sha = compute_file_sha256(resolved_path)
        docs.append(
            SourceDoc(
                source_id=default_source_id(uri),
                path=str(resolved_path),
                uri=uri,
                rel_path=rel_path,
                sha256=sha,
                chars=len(text),
            )
        )
    return docs
