"""Shared utilities: intensity annotation parsing, text truncation, slugify."""

import re

_INTENSITY_RE = re.compile(r'<!--\s*@intensity:\s*(\d+)\s*-->')


def parse_intensity(text: str) -> int | None:
    """Extract @intensity value from a <!-- @intensity:N --> marker.

    Returns None if no marker found. Values clamped to 1-10.
    """
    m = _INTENSITY_RE.search(text)
    if not m:
        return None
    try:
        val = int(m.group(1))
    except (ValueError, IndexError):
        return None
    return max(1, min(10, val))


def extract_first_sentence(text: str, max_chars: int = 200) -> str:
    """Extract the first sentence from text.

    Sentence boundaries: 。！？.!? followed by end-of-sentence context,
    or newline. Strips leading intensity markers.
    """
    text = _INTENSITY_RE.sub('', text).strip()
    if not text:
        return ''

    for i, ch in enumerate(text):
        if ch in '。！？.!?\n':
            if i > 0:
                return text[:i + 1].strip()
            return ''  # leading newline or punct

    if len(text) <= max_chars:
        return text
    return text[:max_chars] + '...'


def strip_intensity_markers(text: str) -> str:
    """Remove all <!-- @intensity:N --> markers from text."""
    return _INTENSITY_RE.sub('', text)


def slugify(text: str, max_len: int = 50) -> str:
    """Convert text to a URL/filesystem-friendly slug."""
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    return slug[:max_len]
