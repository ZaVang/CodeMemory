"""Unit tests for skeletonize — common utilities and markdown processing."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pytest
from codememory.skeletonize.common import parse_intensity, extract_first_sentence, slugify


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


from codememory.skeletonize.markdown import split_sections, skeletonize_markdown, Section


class TestSplitSections:
    def test_two_sections(self):
        text = "## Section A\nContent A.\n\n## Section B\nContent B."
        sections = split_sections(text)
        assert len(sections) == 2
        assert sections[0].heading == 'Section A'
        assert sections[0].body == 'Content A.'
        assert sections[0].level == 2
        assert sections[1].heading == 'Section B'
        assert sections[1].body == 'Content B.'

    def test_with_preamble(self):
        text = "Intro text.\n\n## Section A\nContent A."
        sections = split_sections(text)
        assert len(sections) == 2  # preamble + 1 section
        assert sections[0].heading == ''
        assert 'Intro text' in sections[0].body
        assert sections[1].heading == 'Section A'

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
        assert 'truncated' not in sections[0].body


# ── Code skeletonization tests ─────────────────────────────────────────

from codememory.skeletonize.code import skeletonize_code, supports_extension


class TestSupportsExtension:
    def test_python_supported(self):
        assert supports_extension('.py') is True

    def test_javascript_supported(self):
        assert supports_extension('.js') is True

    def test_typescript_supported(self):
        assert supports_extension('.ts') is True

    def test_unsupported(self):
        assert supports_extension('.go') is False

    def test_case_insensitive(self):
        assert supports_extension('.PY') is True


class TestSkeletonizePython:
    def test_low_intensity_replaced(self):
        code = "# @intensity:3\ndef foo():\n    return 1\n"
        result = skeletonize_code(code, '.py', min_intensity=5)
        assert 'pass' in result
        assert '@intensity:3' in result
        assert 'truncated' in result

    def test_high_intensity_preserved(self):
        code = "# @intensity:8\ndef foo():\n    return 1\n"
        result = skeletonize_code(code, '.py', min_intensity=5)
        assert 'return 1' in result
        assert 'pass' not in result

    def test_no_annotation_default_kept(self):
        code = "def foo():\n    return 1\n"
        result = skeletonize_code(code, '.py', min_intensity=5)
        assert 'return 1' in result

    def test_mixed_intensities(self):
        code = (
            "# @intensity:2\n"
            "def helper():\n"
            "    return 1\n"
            "\n"
            "# @intensity:9\n"
            "def core():\n"
            "    return 99\n"
        )
        result = skeletonize_code(code, '.py', min_intensity=5)
        assert 'pass' in result  # helper skeletonized
        assert 'return 99' in result  # core preserved

    def test_class_definition_skeletonized(self):
        code = "# @intensity:3\nclass Helper:\n    def method(self):\n        return 1\n"
        result = skeletonize_code(code, '.py', min_intensity=5)
        assert 'pass' in result


class TestSkeletonizeJavaScript:
    def test_low_intensity_replaced(self):
        code = "// @intensity:2\nfunction foo() {\n  return 1;\n}\n"
        result = skeletonize_code(code, '.js', min_intensity=5)
        assert 'truncated' in result
        assert '{' in result
        assert '}' in result

    def test_high_intensity_preserved(self):
        code = "// @intensity:8\nfunction foo() {\n  return 1;\n}\n"
        result = skeletonize_code(code, '.js', min_intensity=5)
        assert 'return 1' in result

    def test_parse_error_returns_original(self):
        result = skeletonize_code("not valid javascript {{{", '.js')
        assert 'not valid' in result


class TestSkeletonizeTypeScript:
    def test_low_intensity_replaced(self):
        code = "// @intensity:2\nfunction foo(x: number): number {\n  return x;\n}\n"
        result = skeletonize_code(code, '.ts', min_intensity=5)
        assert 'truncated' in result

    def test_high_intensity_preserved(self):
        code = "// @intensity:7\nfunction foo(x: number): number {\n  return x;\n}\n"
        result = skeletonize_code(code, '.ts', min_intensity=5)
        assert 'return x' in result
