"""Markdown source segmentation with provenance."""

from __future__ import annotations

from pathlib import Path

from codememory.skeletonize.markdown import split_sections

from .models import SourceDoc, SourceSegment


def _line_number_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, max(0, offset)) + 1


def segment_markdown_doc(doc: SourceDoc) -> list[SourceSegment]:
    """Split one Markdown source doc into heading-based segments."""
    text = Path(doc.path).read_text(encoding="utf-8")
    sections = split_sections(text)
    segments: list[SourceSegment] = []
    search_from = 0

    for ordinal, section in enumerate(sections):
        raw = section.raw or section.body
        start = text.find(raw, search_from)
        if start < 0:
            start = search_from
        end = start + len(raw)
        search_from = max(end, search_from)

        heading = section.heading or Path(doc.rel_path).stem
        segments.append(
            SourceSegment(
                segment_id=f"{doc.source_id}-seg-{ordinal}",
                source_id=doc.source_id,
                rel_path=doc.rel_path,
                heading=heading,
                level=section.level,
                ordinal=ordinal,
                body=section.body.strip(),
                start_line=_line_number_for_offset(text, start),
                end_line=_line_number_for_offset(text, end),
            )
        )
    return segments
