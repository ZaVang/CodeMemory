"""Markdown source segmentation with provenance."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from codememory.skeletonize.markdown import split_sections

from .models import SourceDoc, SourceParagraph, SourceSegment


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

        body_search_from = 0
        if section.level > 0:
            heading_end = raw.find("\n")
            body_search_from = heading_end + 1 if heading_end >= 0 else len(raw)
        body_offset = raw.find(section.body, body_search_from) if section.body else body_search_from
        if body_offset < 0:
            body_offset = 0
        body_start = start + body_offset

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
                body_start_line=_line_number_for_offset(text, body_start),
            )
        )
    return segments


_PARAGRAPH_RE = re.compile(
    r"\S(?:.*?\S)?(?=(?:\r?\n[ \t]*){2,}|\Z)",
    re.DOTALL,
)


def paragraphs_from_segments(segments: list[SourceSegment]) -> list[SourceParagraph]:
    """Split section bodies into deterministic non-empty paragraph records."""

    paragraphs: list[SourceParagraph] = []
    ordinal = 0
    for segment in segments:
        section_ordinal = 0
        for match in _PARAGRAPH_RE.finditer(segment.body):
            body = match.group(0).strip()
            if not body:
                continue
            leading = segment.body[:match.start()]
            start_line = segment.body_start_line + leading.count("\n")
            end_line = start_line + body.count("\n")
            digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
            paragraphs.append(
                SourceParagraph(
                    paragraph_id=f"{segment.source_id}-para-{ordinal}",
                    source_id=segment.source_id,
                    segment_id=segment.segment_id,
                    rel_path=segment.rel_path,
                    heading=segment.heading,
                    ordinal=ordinal,
                    section_ordinal=section_ordinal,
                    body=body,
                    sha256=digest,
                    start_line=start_line,
                    end_line=end_line,
                )
            )
            ordinal += 1
            section_ordinal += 1
    return paragraphs
