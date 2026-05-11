"""Markdown skeletonization — section splitting and intensity-based truncation."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .common import parse_intensity, extract_first_sentence, strip_intensity_markers

_HEADING_RE = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)


@dataclass
class Section:
    """A single markdown section (heading + body)."""
    level: int          # heading level 0-6 (0 = preamble / no heading)
    heading: str        # heading text without # prefix
    body: str           # body content
    intensity: int      # parsed or default (5)
    raw: str            # original text including heading line


def _find_section_intensity(heading_start: int, text: str, body: str) -> int:
    """Determine intensity for a section starting at heading_start.

    Checks (in order):
    1. Line immediately before the heading
    2. First 200 chars of body text
    Returns 5 if no marker found.
    """
    # Check line before heading
    if heading_start > 0:
        line_end = text.rfind('\n', 0, heading_start)
        if line_end >= 0:
            line_start = text.rfind('\n', 0, line_end)
            prev_start = line_start + 1 if line_start >= 0 else 0
            prev_line = text[prev_start:line_end]
        else:
            prev_line = text[:heading_start]
        val = parse_intensity(prev_line)
        if val is not None:
            return val

    # Check body prefix
    val = parse_intensity(body[:200])
    if val is not None:
        return val

    return 5


def split_sections(text: str) -> list[Section]:
    """Split markdown text into sections by headings.

    Each section begins at a heading line and continues until the
    next heading. Text before the first heading becomes a level-0
    preamble section.
    """
    if not text or not text.strip():
        return [Section(level=0, heading='', body='', intensity=5, raw='')]

    headings = list(_HEADING_RE.finditer(text))

    if not headings:
        intensity = parse_intensity(text) or 5
        return [Section(level=0, heading='', body=text.strip(),
                        intensity=intensity, raw=text)]

    sections: list[Section] = []

    # Preamble: text before first heading
    first_pos = headings[0].start()
    if first_pos > 0:
        preamble = text[:first_pos].strip()
        if preamble:
            # Don't create a preamble section if it's only an intensity marker
            non_marker = strip_intensity_markers(preamble).strip()
            if non_marker:
                intensity = parse_intensity(preamble) or 5
                sections.append(Section(
                    level=0, heading='', body=preamble,
                    intensity=intensity, raw=preamble,
                ))

    for i, match in enumerate(headings):
        level = len(match.group(1))
        heading_text = match.group(2).strip()

        # Body: from end of heading line to next heading (or EOF)
        body_start = match.end()
        if body_start < len(text) and text[body_start] == '\n':
            body_start += 1
        body_end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        body = text[body_start:body_end].strip()

        intensity = _find_section_intensity(match.start(), text, body)
        raw = text[match.start():body_end]

        sections.append(Section(
            level=level, heading=heading_text, body=body,
            intensity=intensity, raw=raw,
        ))

    return sections


def skeletonize_markdown(text: str, min_intensity: int = 5) -> list[Section]:
    """Skeletonize markdown by truncating low-intensity sections.

    Sections with intensity >= min_intensity are kept in full.
    Sections with intensity < min_intensity get body truncated to
    first sentence + a `<!-- truncated: ... -->` marker.
    """
    sections = split_sections(text)

    for section in sections:
        if section.intensity < min_intensity:
            # Clean body of intensity markers before computing truncation
            clean = strip_intensity_markers(section.body).strip()
            first_sent = extract_first_sentence(clean)
            remaining = clean[len(first_sent):].strip()
            if remaining:
                token_est = len(remaining)
                section.body = (
                    first_sent
                    + f'\n\n<!-- truncated: {len(remaining)} chars, ~{token_est} tokens -->\n'
                )
            else:
                section.body = first_sent + '\n'

    return sections
