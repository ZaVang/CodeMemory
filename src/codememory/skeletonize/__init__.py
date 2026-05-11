"""CodeMemory skeletonize — structured bulk import from source files.

Phase 1: Markdown skeletonization (markdown.py).
Phase 3 (future): code skeletonization (code.py).
"""

from .markdown import Section, skeletonize_markdown, split_sections

__all__ = ["Section", "skeletonize_markdown", "split_sections"]
