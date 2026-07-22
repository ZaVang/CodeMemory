"""Deterministic source-aware proposals for Markdown corpus migration."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from codememory.models import SourceRef
from codememory.skeletonize.common import extract_first_sentence, slugify
from codememory.sources import add_source_artifact

from .ingest import scan_markdown_corpus
from .models import MemoryProposal, ReviewSet, SourceDoc, SourceParagraph, SourceSegment
from .segment import paragraphs_from_segments, segment_markdown_doc


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


def _source_summary(doc: SourceDoc) -> str:
    return f"Markdown source: {doc.rel_path}"


def _source_ref(
    doc: SourceDoc,
    *,
    section_id: str | None = None,
    line_range: str | None = None,
    disclosure_hint: str = "anchor",
) -> SourceRef:
    return SourceRef(
        artifact_id=doc.source_id,
        section_id=section_id,
        range=line_range,
        summary=_source_summary(doc),
        disclosure_hint=disclosure_hint,
    )


def register_source_docs(memory_root: Path, docs: list[SourceDoc]) -> None:
    """Idempotently upsert compiler-discovered documents in the registry."""

    for doc in docs:
        add_source_artifact(
            memory_root,
            uri=doc.uri or doc.path,
            source_id=doc.source_id,
            kind="markdown",
            summary=_source_summary(doc),
        )


def anchor_proposal(
    doc: SourceDoc,
    tags: list[str] | None = None,
    namespace: str = "user/imports",
    used_ids: set[str] | None = None,
) -> MemoryProposal:
    """Create the one lightweight Source Artifact anchor for a document."""

    used_ids = used_ids if used_ids is not None else set()
    prefix = _path_prefix(doc.rel_path)
    memory_id = _unique_memory_id(f"{namespace}/{prefix}/anchor", used_ids)
    title = Path(doc.rel_path).stem
    summary = _source_summary(doc)
    body = (
        f"# {title}\n\n"
        f"Source Artifact `{doc.source_id}` anchors `{doc.rel_path}`. "
        f"Use `codememory source expand {doc.source_id}` to read the original."
    )
    proposal_tags = list(dict.fromkeys([*(tags or []), "compiled", "markdown", "source-anchor"]))
    return MemoryProposal(
        proposal_id=f"prop-{doc.source_id.replace('/', '-')}-anchor",
        role="anchor",
        memory_id=memory_id,
        summary=summary,
        body=body,
        tags=proposal_tags,
        source_refs=[_source_ref(doc)],
        source={
            "platform": "memory-compiler-v2",
            "created_by": "codememory compile-md",
            "original_file": doc.rel_path,
            "original_sha256": doc.sha256,
            "artifact_id": doc.source_id,
            "proposal_role": "anchor",
        },
    )


def proposal_from_paragraph(
    paragraph: SourceParagraph,
    doc: SourceDoc,
    tags: list[str] | None = None,
    namespace: str = "user/imports",
    used_ids: set[str] | None = None,
) -> MemoryProposal:
    """Create one deterministic derived proposal from a Markdown paragraph."""

    used_ids = used_ids if used_ids is not None else set()
    prefix = _path_prefix(paragraph.rel_path)
    heading = paragraph.heading or Path(paragraph.rel_path).stem
    heading_slug = _clean_slug(heading)
    base_id = f"{namespace}/{prefix}/{heading_slug}-p{paragraph.section_ordinal + 1}"
    memory_id = _unique_memory_id(base_id, used_ids)
    summary = extract_first_sentence(paragraph.body, max_chars=120) or heading
    body = f"# {heading}\n\n{paragraph.body}".strip()
    proposal_tags = list(dict.fromkeys([*(tags or []), "compiled", "markdown", "derived"]))
    line_range = f"L{paragraph.start_line}-L{paragraph.end_line}"

    return MemoryProposal(
        proposal_id=f"prop-{paragraph.paragraph_id}",
        role="derived",
        memory_id=memory_id,
        summary=summary,
        body=body,
        tags=proposal_tags,
        source_refs=[
            _source_ref(
                doc,
                section_id=paragraph.paragraph_id,
                line_range=line_range,
                disclosure_hint="excerpt",
            )
        ],
        source={
            "platform": "memory-compiler-v2",
            "created_by": "codememory compile-md",
            "original_file": paragraph.rel_path,
            "original_sha256": doc.sha256,
            "artifact_id": doc.source_id,
            "segment_id": paragraph.segment_id,
            "paragraph_id": paragraph.paragraph_id,
            "paragraph_sha256": paragraph.sha256,
            "heading": paragraph.heading,
            "line_start": paragraph.start_line,
            "line_end": paragraph.end_line,
            "proposal_role": "derived",
        },
    )


def compile_markdown_corpus(
    memory_root: Path,
    source_root: Path,
    review_id: str,
    tags: list[str] | None = None,
    namespace: str = "user/imports",
    *,
    register_sources: bool = True,
) -> ReviewSet:
    """Register a Markdown corpus and return its deterministic draft review set."""

    docs = scan_markdown_corpus(source_root)
    segments = []
    paragraphs = []
    proposals = []
    used_ids: set[str] = set()

    if register_sources:
        register_source_docs(memory_root, docs)

    for doc in docs:
        proposals.append(anchor_proposal(doc, tags=tags, namespace=namespace, used_ids=used_ids))

        doc_segments = segment_markdown_doc(doc)
        doc_paragraphs = paragraphs_from_segments(doc_segments)
        segments.extend(doc_segments)
        paragraphs.extend(doc_paragraphs)
        for paragraph in doc_paragraphs:
            proposals.append(
                proposal_from_paragraph(
                    paragraph,
                    doc=doc,
                    tags=tags,
                    namespace=namespace,
                    used_ids=used_ids,
                )
            )

    return ReviewSet(
        review_id=review_id,
        source_root=str(source_root.resolve()),
        namespace=namespace,
        tags=list(tags or []),
        compiler_version=2,
        sources=docs,
        segments=segments,
        paragraphs=paragraphs,
        proposals=proposals,
    )


def proposal_from_segment(
    segment: SourceSegment,
    source_sha256: str,
    tags: list[str] | None = None,
    namespace: str = "user/imports",
    used_ids: set[str] | None = None,
) -> MemoryProposal:
    """Compatibility wrapper treating the whole legacy segment as one paragraph."""

    body = segment.body.strip()
    paragraph = SourceParagraph(
        paragraph_id=f"{segment.source_id}-para-{segment.ordinal}",
        source_id=segment.source_id,
        segment_id=segment.segment_id,
        rel_path=segment.rel_path,
        heading=segment.heading,
        ordinal=segment.ordinal,
        section_ordinal=0,
        body=body,
        sha256=hashlib.sha256(body.encode("utf-8")).hexdigest(),
        start_line=segment.body_start_line,
        end_line=segment.end_line,
    )
    doc = SourceDoc(
        source_id=segment.source_id,
        path=segment.rel_path,
        uri=segment.rel_path,
        rel_path=segment.rel_path,
        sha256=source_sha256,
        chars=len(body),
    )
    return proposal_from_paragraph(
        paragraph,
        doc=doc,
        tags=tags,
        namespace=namespace,
        used_ids=used_ids,
    )
