"""Source corpus ingestion for Markdown migration."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .models import SourceDoc


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
        sha = _sha256_text(text)
        docs.append(
            SourceDoc(
                source_id=f"src-{sha[:12]}",
                path=str(path),
                rel_path=rel_path,
                sha256=sha,
                chars=len(text),
            )
        )
    return docs
