# Skeletonize Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `codememory skeletonize` command that reads Markdown files, parses `<!-- @intensity:N -->` annotations, skeletonizes low-intensity sections, and writes each section as a CodeMemory memory atom.

**Architecture:** New `src/codememory/skeletonize/` sub-package (3 files). Integration through `handlers.py` (1 new handler) and `cli.py` (1 new subcommand). Zero new dependencies.

**Tech Stack:** Python stdlib — `re`, `dataclasses`, `pathlib`.

---

### Task 1: Create skeletonize package scaffold

**Files:**
- Create: `src/codememory/skeletonize/__init__.py`
- Create: `src/codememory/skeletonize/code.py`

- [ ] **Step 1: Write __init__.py**

```python
"""CodeMemory skeletonize — structured bulk import from source files.

Phase 1: Markdown skeletonization (markdown.py).
Phase 3 (future): code skeletonization (code.py).
"""

from .markdown import Section, skeletonize_markdown, split_sections

__all__ = ["Section", "skeletonize_markdown", "split_sections"]
```

- [ ] **Step 2: Write code.py stub**

```python
"""Code skeletonization — Phase 3 stub (future: Tree-sitter multi-language)."""
```

- [ ] **Step 3: Verify package is importable**

Run: `cd /d/work/CodeMemory && PYTHONPATH=src python -c "from codememory.skeletonize import Section, skeletonize_markdown; print('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add src/codememory/skeletonize/__init__.py src/codememory/skeletonize/code.py
git commit -m "feat: add skeletonize package scaffold"
```

---

### Task 2: Write common.py — intensity parsing + text utilities

**Files:**
- Create: `src/codememory/skeletonize/common.py`
- Create: `tests/unit/test_skeletonize.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Unit tests for skeletonize — common utilities and markdown processing."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pytest
from codememory.skeletonize.common import parse_intensity, extract_first_sentence, slugify
from codememory.skeletonize.markdown import split_sections, skeletonize_markdown, Section


class TestParseIntensity:
    def test_standard_marker(self):
        assert parse_intensity("<!-- @intensity:7 -->") == 7

    def test_marker_with_surrounding_text(self):
        assert parse_intensity("<!-- @intensity:3 -->\n## Some Heading") == 3

    def test_marker_with_whitespace(self):
        assert parse_intensity("<!--   @intensity:  9  -->") == 9

    def test_no_marker(self):
        assert parse_intensity("## Just a heading") is None

    def test_empty_string(self):
        assert parse_intensity("") is None

    def test_clamp_low(self):
        assert parse_intensity("<!-- @intensity:0 -->") == 1

    def test_clamp_high(self):
        assert parse_intensity("<!-- @intensity:99 -->") == 10

    def test_malformed_marker(self):
        assert parse_intensity("<!-- @intensity:abc -->") is None

    def test_bare_text_not_matched(self):
        assert parse_intensity("@intensity:5") is None


class TestExtractFirstSentence:
    def test_chinese_period(self):
        assert extract_first_sentence("这是第一句。这是第二句。") == "这是第一句。"

    def test_english_period(self):
        assert extract_first_sentence("First sentence. Second sentence.") == "First sentence."

    def test_exclamation(self):
        assert extract_first_sentence("Important! Less important.") == "Important!"

    def test_question(self):
        assert extract_first_sentence("Is this right? More text here.") == "Is this right?"

    def test_newline_as_boundary(self):
        assert extract_first_sentence("Single line\nmore text here") == "Single line"

    def test_no_terminator(self):
        text = "One long unpunctuated paragraph without sentence boundary"
        result = extract_first_sentence(text, max_chars=50)
        assert len(result) <= 53  # 50 + "..."

    def test_strips_intensity_marker(self):
        assert extract_first_sentence("<!-- @intensity:3 -->\nActual first sentence. More.") == "Actual first sentence."

    def test_empty_string(self):
        assert extract_first_sentence("") == ""


class TestSlugify:
    def test_english(self):
        assert slugify("Core Architecture") == "core-architecture"

    def test_chinese(self):
        assert slugify("核心架构") == "核心架构"

    def test_mixed(self):
        assert slugify("API 接口设计") == "api-接口设计"

    def test_special_chars(self):
        assert slugify("hello/world:test") == "helloworldtest"

    def test_truncation(self):
        result = slugify("a" * 100, max_len=20)
        assert len(result) <= 20
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /d/work/CodeMemory && PYTHONPATH=src python -m pytest tests/unit/test_skeletonize.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'codememory.skeletonize.common'`

- [ ] **Step 3: Write common.py**

```python
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


def slugify(text: str, max_len: int = 50) -> str:
    """Convert text to a URL/filesystem-friendly slug."""
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    return slug[:max_len]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /d/work/CodeMemory && PYTHONPATH=src python -m pytest tests/unit/test_skeletonize.py -v`
Expected: 17 passed

- [ ] **Step 5: Commit**

```bash
git add src/codememory/skeletonize/common.py tests/unit/test_skeletonize.py
git commit -m "feat: add skeletonize common utilities"
```

---

### Task 3: Write markdown.py — section splitting + skeletonization

**Files:**
- Create: `src/codememory/skeletonize/markdown.py`
- Modify: `tests/unit/test_skeletonize.py` (append tests)

- [ ] **Step 1: Append tests to test_skeletonize.py**

Append the following after the TestSlugify class:

```python
class TestSplitSections:
    def test_two_sections(self):
        text = "# Title\n\nIntro text.\n\n## Section A\nContent A.\n\n## Section B\nContent B."
        sections = split_sections(text)
        assert len(sections) == 3  # preamble + 2 sections
        assert sections[0].heading == ''
        assert 'Intro text' in sections[0].body
        assert sections[1].heading == 'Section A'
        assert sections[1].body == 'Content A.'
        assert sections[1].level == 2
        assert sections[2].heading == 'Section B'
        assert sections[2].body == 'Content B.'

    def test_no_headings(self):
        text = "Just plain text without any headings."
        sections = split_sections(text)
        assert len(sections) == 1
        assert sections[0].heading == ''
        assert sections[0].body == text

    def test_default_intensity(self):
        text = "## Plain Section\nSome content without marker."
        sections = split_sections(text)
        assert sections[0].intensity == 5

    def test_intensity_before_heading(self):
        text = "<!-- @intensity:8 -->\n## Important Section\nFull content here."
        sections = split_sections(text)
        assert sections[0].intensity == 8
        assert sections[0].heading == 'Important Section'

    def test_intensity_in_body(self):
        text = "## Section\n<!-- @intensity:3 -->\nMore text."
        sections = split_sections(text)
        assert sections[0].intensity == 3

    def test_nested_headings_create_separate_sections(self):
        text = "## Top\nTop content.\n### Sub\nSub content.\n## Another\nMore."
        sections = split_sections(text)
        assert len(sections) == 3
        assert sections[0].heading == 'Top'
        assert sections[1].heading == 'Sub'
        assert sections[1].level == 3
        assert sections[2].heading == 'Another'

    def test_empty_document(self):
        sections = split_sections("")
        assert len(sections) == 1
        assert sections[0].body == ''


class TestSkeletonizeMarkdown:
    def test_high_intensity_preserved(self):
        text = "## Core Logic\n<!-- @intensity:8 -->\nDetailed implementation kept fully."
        sections = skeletonize_markdown(text, min_intensity=5)
        assert 'Detailed implementation' in sections[0].body
        assert 'truncated' not in sections[0].body

    def test_low_intensity_truncated(self):
        text = "## Helper\n<!-- @intensity:2 -->\nFirst sentence. Second sentence to be cut."
        sections = skeletonize_markdown(text, min_intensity=5)
        assert 'truncated' in sections[0].body
        assert 'First sentence.' in sections[0].body
        assert 'Second sentence' not in sections[0].body

    def test_boundary_intensity_kept(self):
        text = "## Boundary\n<!-- @intensity:5 -->\nFull content at boundary."
        sections = skeletonize_markdown(text, min_intensity=5)
        assert 'Full content' in sections[0].body
        assert 'truncated' not in sections[0].body

    def test_mixed_intensities(self):
        text = (
            "## Important\n<!-- @intensity:8 -->\nKeep all of this.\n\n"
            "## Minor\n<!-- @intensity:2 -->\nDrop most. Extra filler."
        )
        sections = skeletonize_markdown(text, min_intensity=5)
        assert len(sections) == 2
        assert 'Keep all' in sections[0].body
        assert 'truncated' not in sections[0].body
        assert 'truncated' in sections[1].body

    def test_no_headings_document(self):
        text = "<!-- @intensity:2 -->\nNo heading doc. Extra filler text here."
        sections = skeletonize_markdown(text, min_intensity=5)
        assert 'truncated' in sections[0].body

    def test_short_low_intensity_not_truncated(self):
        """Single short sentence with low intensity — nothing to truncate."""
        text = "## Note\n<!-- @intensity:1 -->\nShort."
        sections = skeletonize_markdown(text, min_intensity=5)
        # First sentence is the whole body, no remaining text to truncate
        assert 'truncated' not in sections[0].body
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /d/work/CodeMemory && PYTHONPATH=src python -m pytest tests/unit/test_skeletonize.py -v`
Expected: FAIL — `cannot import name 'split_sections'`

- [ ] **Step 3: Write markdown.py**

```python
"""Markdown skeletonization — section splitting and intensity-based truncation."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .common import parse_intensity, extract_first_sentence

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
        prev_nl = text.rfind('\n', 0, heading_start)
        prev_start = prev_nl + 1 if prev_nl >= 0 else 0
        prev_line = text[prev_start:heading_start]
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
            first_sent = extract_first_sentence(section.body)
            remaining = section.body[len(first_sent):].strip()
            if remaining:
                token_est = len(remaining)
                section.body = (
                    first_sent
                    + f'\n\n<!-- truncated: {len(remaining)} chars, ~{token_est} tokens -->\n'
                )

    return sections
```

- [ ] **Step 4: Run all tests**

Run: `cd /d/work/CodeMemory && PYTHONPATH=src python -m pytest tests/unit/test_skeletonize.py -v`
Expected: ~30 passed

- [ ] **Step 5: Commit**

```bash
git add src/codememory/skeletonize/markdown.py tests/unit/test_skeletonize.py
git commit -m "feat: add markdown section splitting and skeletonization"
```

---

### Task 4: Add handle_skeletonize to handlers.py

**Files:**
- Modify: `src/codememory/handlers.py`

- [ ] **Step 1: Add import for skeletonize module**

Add after line 28 (`from .suggest_deps import suggest_deps`):

```python
from .skeletonize.markdown import skeletonize_markdown
```

- [ ] **Step 2: Add handle_skeletonize function**

Add after `handle_import` (after line 511):

```python
def handle_skeletonize(
    root: Path,
    source: str,
    min_intensity: int = 5,
    dry_run: bool = False,
    tags: list[str] | None = None,
) -> str:
    """Skeletonize Markdown files into CodeMemory memories.

    Reads .md files from *source* (file or directory), splits each into
    sections, applies intensity-based truncation, and writes each section
    as a memory atom in *root*.
    """
    import re as _re
    import yaml as _yaml

    from .skeletonize.common import slugify as _slug
    from .skeletonize.common import extract_first_sentence as _first_sent

    source_path = Path(source).resolve()
    if not source_path.exists():
        return f"Error: source not found: {source}"

    # Collect .md files
    md_files: list[Path] = []
    if source_path.is_file():
        if source_path.suffix == '.md':
            md_files = [source_path]
        else:
            return f"Error: not a .md file: {source}"
    else:
        md_files = sorted(source_path.rglob('*.md'))

    if not md_files:
        return f"No .md files found in: {source}"

    tags = tags or []
    total_sections = 0
    created: list[str] = []

    for md_file in md_files:
        try:
            text = md_file.read_text(encoding='utf-8')
        except Exception as e:
            _logger.warning("Skipping %s: %s", md_file, e)
            continue

        sections = skeletonize_markdown(text, min_intensity=min_intensity)

        # Build ID prefix from relative path
        try:
            rel = md_file.relative_to(source_path) if source_path.is_dir() else Path(md_file.name)
        except ValueError:
            rel = Path(md_file.name)
        # /-separated path parts with sanitized names
        parts = list(rel.parts[:-1]) + [rel.stem]
        clean_parts = [_re.sub(r'[^\w-]', '-', p.lower()).strip('-')[:30] for p in parts]
        prefix = '/'.join(p for p in clean_parts if p)

        for i, section in enumerate(sections):
            heading_slug = _slug(section.heading) if section.heading else f'section-{i}'
            memory_id = f'user/imports/{prefix}/{heading_slug}'

            summary = _first_sent(section.body, max_chars=100) if section.body else (section.heading or 'Untitled')

            body_text = f'# {section.heading}\n\n{section.body}' if section.heading else section.body

            frontmatter = {
                'type': 'atom',
                'id': memory_id,
                'summary': summary,
                'status': 'active',
                'created': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                'updated': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                'version': 1,
                'tags': tags + ['skeletonized'],
                'intensity': section.intensity,
                'maturity': 'draft',
                'source': {
                    'platform': 'skeletonize',
                    'created_by': 'codememory skeletonize',
                    'original_file': str(rel),
                },
            }

            frontmatter['summary_hash'] = _cbh(body_text)

            yaml_str = _yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
            content = f'---\n{yaml_str}---\n{body_text}\n'

            if dry_run:
                print(f'[{memory_id}] (intensity={section.intensity})')
                preview = body_text[:200] + ('...' if len(body_text) > 200 else '')
                print(preview)
                print()
                created.append(f'[dry-run] {memory_id}')
            else:
                file_path = get_memory_path(root, memory_id)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding='utf-8')
                print(f'Skeletonized: {file_path} (intensity={section.intensity})')
                created.append(str(file_path))

            total_sections += 1

    if not dry_run and created:
        from .index import reindex as _reindex
        _reindex(root)
        try:
            from .log import append_log as _append_log
            _append_log(root, 'skeletonize', f'{len(created)} memories from {len(md_files)} file(s)')
        except ImportError:
            pass

    return (
        f'Skeletonized {total_sections} section(s) from {len(md_files)} file(s)\n'
        + '\n'.join(created)
    )
```

- [ ] **Step 3: Verify handler is importable**

Run: `cd /d/work/CodeMemory && PYTHONPATH=src python -c "from codememory.handlers import handle_skeletonize; print('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add src/codememory/handlers.py
git commit -m "feat: add handle_skeletonize handler"
```

---

### Task 5: Add skeletonize subcommand to cli.py

**Files:**
- Modify: `src/codememory/cli.py`

- [ ] **Step 1: Add import**

In the `from .handlers import (` block (line 7), add `handle_skeletonize,`:

```python
from .handlers import (
    handle_changelog,
    handle_create,
    handle_focus,
    handle_import,
    handle_log,
    handle_orphans,
    handle_overview,
    handle_reindex,
    handle_resolve,
    handle_search,
    handle_skeletonize,
    handle_snapshot,
    handle_suggest_deps,
    handle_update,
    handle_validate,
    handle_wander,
)
```

- [ ] **Step 2: Add subparser definition**

Add after the `suggest-deps` subparser block (after line 155):

```python
    # skeletonize
    p = subparsers.add_parser("skeletonize", help="Import structured memories from Markdown files")
    _add_logging_flags(p)
    p.add_argument("source", help=".md file or directory of .md files")
    p.add_argument("--min-intensity", type=int, default=5,
                   help="Sections below this intensity are truncated (default: 5)")
    p.add_argument("--dry-run", action="store_true",
                   help="Preview without writing files")
    p.add_argument("--tags", help="Comma-separated tags for generated memories")
```

- [ ] **Step 3: Add dispatch branch**

Add before `if __name__ == "__main__":` (before line 229):

```python
    elif cmd == "skeletonize":
        tags_list = None
        if args.tags:
            tags_list = [t.strip() for t in args.tags.split(",") if t.strip()]
        print(handle_skeletonize(
            root, args.source,
            min_intensity=args.min_intensity,
            dry_run=args.dry_run,
            tags=tags_list,
        ))
```

- [ ] **Step 4: Verify CLI help works**

Run: `cd /d/work/CodeMemory && PYTHONPATH=src python -m codememory.cli skeletonize --help`
Expected: help text showing `source`, `--min-intensity`, `--dry-run`, `--tags`

- [ ] **Step 5: Commit**

```bash
git add src/codememory/cli.py
git commit -m "feat: add skeletonize subcommand to CLI"
```

---

### Task 6: End-to-end verification

- [ ] **Step 1: Create test Markdown file**

```bash
mkdir -p /tmp/skel-test
cat > /tmp/skel-test/design.md << 'EOF'
# System Design

Overview paragraph that introduces the design document.

<!-- @intensity:8 -->
## Core Architecture
The system uses a microservices architecture with event-driven communication.
This decision was made after evaluating monolithic and serverless alternatives.

<!-- @intensity:2 -->
## Deployment Details
The deployment uses Kubernetes on AWS EKS. First sentence kept. Lots of
operational details about node groups, autoscaling configuration, IAM roles,
and monitoring setup that should be truncated because it's low intensity.
EOF
```

- [ ] **Step 2: Run dry-run**

Run: `cd /d/work/CodeMemory && PYTHONPATH=src python -m codememory.cli skeletonize /tmp/skel-test/ --dry-run --root /tmp/skel-memories`
Expected: prints sections with `[dry-run]` prefix, "Core Architecture" at intensity=8 kept, "Deployment Details" at intensity=2 shows truncated marker, preamble shown

- [ ] **Step 3: Run actual import**

Run: `cd /d/work/CodeMemory && PYTHONPATH=src python -m codememory.cli skeletonize /tmp/skel-test/ --root /tmp/skel-memories --tags "test"`
Expected: creates `.md` files under `/tmp/skel-memories/user/imports/skel-test/design/`, reindexes

- [ ] **Step 4: Verify via CodeMemory tools**

```bash
# Check reindex + validate
PYTHONPATH=src python -m codememory.cli validate --root /tmp/skel-memories

# Search for skeletonized memories
PYTHONPATH=src python -m codememory.cli search --tags test --root /tmp/skel-memories

# Resolve a specific memory
PYTHONPATH=src python -m codememory.cli resolve user/imports/skel-test/design/core-architecture --root /tmp/skel-memories
```
Expected: validate passes, search finds memories, resolve outputs full content for high-intensity section, truncated content for low-intensity

- [ ] **Step 5: Run full unit test suite to check no regressions**

Run: `cd /d/work/CodeMemory && PYTHONPATH=src python -m pytest tests/unit/ -v`
Expected: all ~57 + ~30 = ~87 tests pass

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: end-to-end verification of skeletonize import"
```
