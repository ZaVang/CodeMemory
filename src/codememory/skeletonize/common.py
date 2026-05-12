"""Shared utilities: intensity annotation parsing, text truncation, slugify."""

import re

# Matches: <!-- @intensity:N --> | # @intensity:N | // @intensity:N
_INTENSITY_RE = re.compile(r'(?:<!--|#|//)\s*@intensity:\s*(\d+)\s*(?:-->)?')


def parse_intensity(text: str) -> int | None:
    """Extract @intensity value from annotation markers.

    Supported formats:
      <!-- @intensity:N -->  (Markdown / HTML)
      # @intensity:N         (Python, YAML, shell)
      // @intensity:N        (JS, TS, Go, Rust, Java)

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
    """Remove all @intensity annotation markers from text."""
    return _INTENSITY_RE.sub('', text)


def slugify(text: str, max_len: int = 50) -> str:
    """Convert text to a URL/filesystem-friendly slug."""
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    return slug[:max_len]


def render_to_html(
    sections: list,
    source_file: str,
    metadata: dict | None = None,
) -> str:
    """Render skeletonized sections as a self-contained HTML file.

    Features: collapsible sections (<details>), tab navigation for
    multi-file output, JSON-LD frontmatter embedding. No external
    dependencies — pure HTML + inline CSS.
    """
    import html

    meta = metadata or {}
    title = meta.get("title", source_file)
    tags = meta.get("tags", [])
    intensity = meta.get("intensity", 5)

    jsonld = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "name": title,
        "keywords": tags,
        "intensity": intensity,
        "sourceFile": source_file,
    }

    css = _HTML_CSS

    body_parts = [
        f'<header>',
        f'<h1>{html.escape(title)}</h1>',
        f'<div class="meta">',
        f'<span class="tag-list">Source: {html.escape(source_file)}</span>',
    ]
    if tags:
        tags_html = ''.join(
            f'<span class="tag">{html.escape(t)}</span>' for t in tags
        )
        body_parts.append(f'<span class="tag-list">Tags: {tags_html}</span>')
    body_parts.append(f'<span>Intensity: {intensity}/10</span>')
    body_parts.append('</div>')
    body_parts.append('</header>')

    body_parts.append('<main>')
    for i, section in enumerate(sections):
        heading = getattr(section, 'heading', '') or f'Section {i}'
        body_text = getattr(section, 'body', '') or ''
        sec_intensity = getattr(section, 'intensity', 5)
        sec_id = slugify(heading) or f'section-{i}'

        truncated = 'truncated' if sec_intensity < (meta.get('min_intensity', 5)) else ''

        body_parts.append(
            f'<details {"open" if not truncated else ""} class="{truncated}">'
        )
        body_parts.append(
            f'<summary>'
            f'<span class="section-heading">{html.escape(heading)}</span>'
            f'<span class="intensity-badge">{sec_intensity}</span>'
            f'</summary>'
        )
        body_parts.append(
            f'<div class="section-body">'
            f'{html.escape(body_text).replace(chr(10), "<br>")}'
            f'</div>'
        )
        body_parts.append('</details>')

    body_parts.append('</main>')

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)} — CodeMemory Skeleton</title>
<script type="application/ld+json">
{_json_escape(jsonld)}
</script>
<style>
{css}
</style>
</head>
<body>
{chr(10).join(body_parts)}
</body>
</html>'''


def _json_escape(obj: dict) -> str:
    import json
    return json.dumps(obj, indent=2, ensure_ascii=False)


_HTML_CSS = '''
:root {
    --bg: #fafafa;
    --fg: #1a1a1a;
    --border: #e0e0e0;
    --accent: #0969da;
    --muted: #666;
    --tag-bg: #ddf4ff;
    --tag-fg: #0969da;
    --badge-bg: #eee;
    --truncated-bg: #fff8f0;
    --summary-hover: #f0f0f0;
}
@media (prefers-color-scheme: dark) {
    :root {
        --bg: #0d1117;
        --fg: #c9d1d9;
        --border: #30363d;
        --accent: #58a6ff;
        --muted: #8b949e;
        --tag-bg: #0c2d6b;
        --tag-fg: #58a6ff;
        --badge-bg: #21262d;
        --truncated-bg: #1a120b;
        --summary-hover: #161b22;
    }
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--fg);
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
    line-height: 1.6;
}
header { margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
header h1 { font-size: 1.5rem; margin-bottom: 0.5rem; }
.meta { display: flex; gap: 1.5rem; flex-wrap: wrap; font-size: 0.85rem; color: var(--muted); }
.tag-list { display: flex; align-items: center; gap: 0.3rem; }
.tag {
    display: inline-block;
    padding: 0.1rem 0.5rem;
    background: var(--tag-bg);
    color: var(--tag-fg);
    border-radius: 12px;
    font-size: 0.8rem;
}
main { display: flex; flex-direction: column; gap: 0.5rem; }
details {
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
}
details.truncated { background: var(--truncated-bg); }
summary {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 1rem;
    cursor: pointer;
    user-select: none;
    font-weight: 500;
}
summary:hover { background: var(--summary-hover); }
.section-heading { flex: 1; }
.intensity-badge {
    display: inline-block;
    padding: 0.1rem 0.5rem;
    background: var(--badge-bg);
    border-radius: 10px;
    font-size: 0.75rem;
    color: var(--muted);
    min-width: 1.5rem;
    text-align: center;
    margin-left: 0.5rem;
    flex-shrink: 0;
}
.section-body {
    padding: 0.8rem 1rem;
    border-top: 1px solid var(--border);
    font-size: 0.9rem;
    line-height: 1.7;
    white-space: pre-wrap;
}
'''
