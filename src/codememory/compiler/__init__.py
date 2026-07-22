"""Memory Compiler: source corpus → reviewable draft memory graph."""

from .materialize import materialize_review_set
from .models import (
    MaterializeResult,
    MemoryProposal,
    ReviewSet,
    SourceDoc,
    SourceParagraph,
    SourceSegment,
)
from .propose import (
    anchor_proposal,
    compile_markdown_corpus,
    proposal_from_paragraph,
    proposal_from_segment,
    register_source_docs,
)
from .review import load_review_set, save_review_set

__all__ = [
    "MaterializeResult",
    "MemoryProposal",
    "ReviewSet",
    "SourceDoc",
    "SourceParagraph",
    "SourceSegment",
    "anchor_proposal",
    "compile_markdown_corpus",
    "load_review_set",
    "materialize_review_set",
    "proposal_from_segment",
    "proposal_from_paragraph",
    "register_source_docs",
    "save_review_set",
]
