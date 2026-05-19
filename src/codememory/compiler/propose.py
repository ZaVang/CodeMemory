"""Draft memory proposal generation for Markdown corpus migration."""

from __future__ import annotations

import re
from pathlib import Path

from codememory.skeletonize.common import extract_first_sentence, slugify

from .ingest import scan_markdown_corpus
from .models import MemoryProposal, ReviewSet, SourceSegment
from .segment import segment_markdown_doc


def _clean_slug(value: str) -> str:
    slug = slugify(value, max_len=60).strip("-")
    return slug or "untitled"


def _clean_parts(parts: tuple[str, ...]) -> list[str]:
    return [_clean_slug(re.sub(r"\.md$", "", part, flags=re.I)) for part in parts]


def _path_prefix(rel_path: str) -> str:
    path = Path(rel_path)
    parts = [*_clean_parts(path.parts[:-1]), _clean_slug(path.stem)]
    return "/".join(part for part in parts if part)


def _unique_memory_id(base_id: str, used: set[str]) -> str:
    if base_id not in used:
        used.add(base_id)
        return base_id
    suffix = 2
    while f"{base_id}-{suffix}" in used:
        suffix += 1
    unique = f"{base_id}-{suffix}"
    used.add(unique)
    return unique


def proposal_from_segment(
    segment: SourceSegment,
    source_sha256: str,
    tags: list[str] | None = None,
    namespace: str = "user/imports",
    used_ids: set[str] | None = None,
) -> MemoryProposal:
    """Create one deterministic draft proposal from a Markdown segment."""
    used_ids = used_ids if used_ids is not None else set()
    prefix = _path_prefix(segment.rel_path)
    heading_slug = _clean_slug(segment.heading)
    memory_id = _unique_memory_id(f"{namespace}/{prefix}/{heading_slug}", used_ids)
    title = segment.heading or Path(segment.rel_path).stem
    body = f"# {title}\n\n{segment.body}".strip()
    summary = extract_first_sentence(segment.body, max_chars=120) or title
    proposal_tags = list(dict.fromkeys([*(tags or []), "compiled", "markdown"]))

    return MemoryProposal(
        proposal_id=f"prop-{segment.segment_id}",
        memory_id=memory_id,
        summary=summary,
        body=body,
        tags=proposal_tags,
        maturity="draft",
        source={
            "platform": "memory-compiler",
            "created_by": "codememory compile-md",
            "original_file": segment.rel_path,
            "original_sha256": source_sha256,
            "segment_id": segment.segment_id,
            "heading": segment.heading,
            "line_start": segment.start_line,
            "line_end": segment.end_line,
        },
    )


def compile_markdown_corpus(
    source_root: Path,
    review_id: str,
    tags: list[str] | None = None,
    namespace: str = "user/imports",
) -> ReviewSet:
    """Compile a Markdown corpus into a draft review set."""
    docs = scan_markdown_corpus(source_root)
    segments = []
    proposals = []
    used_ids: set[str] = set()
    source_sha_by_id = {doc.source_id: doc.sha256 for doc in docs}

    for doc in docs:
        doc_segments = segment_markdown_doc(doc)
        segments.extend(doc_segments)
        for segment in doc_segments:
            proposals.append(
                proposal_from_segment(
                    segment,
                    source_sha256=source_sha_by_id[segment.source_id],
                    tags=tags,
                    namespace=namespace,
                    used_ids=used_ids,
                )
            )

    return ReviewSet(
        review_id=review_id,
        source_root=str(source_root.resolve()),
        sources=docs,
        segments=segments,
        proposals=proposals,
    )
