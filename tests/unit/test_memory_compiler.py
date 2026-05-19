"""Unit tests for the Memory Compiler Markdown migration pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def test_review_set_round_trip(tmp_path: Path):
    from codememory.compiler.models import (
        MemoryProposal,
        ReviewSet,
        SourceDoc,
        SourceSegment,
    )
    from codememory.compiler.review import load_review_set, save_review_set

    doc = SourceDoc(
        source_id="src-1",
        path=str(tmp_path / "docs" / "adr.md"),
        rel_path="adr.md",
        sha256="a" * 64,
        chars=120,
    )
    segment = SourceSegment(
        segment_id="seg-1",
        source_id="src-1",
        rel_path="adr.md",
        heading="Decision",
        level=2,
        ordinal=0,
        body="We chose a file-based memory root.",
        start_line=1,
        end_line=3,
    )
    proposal = MemoryProposal(
        proposal_id="prop-1",
        memory_id="user/imports/adr/decision",
        summary="We chose a file-based memory root.",
        body="# Decision\n\nWe chose a file-based memory root.",
        tags=["architecture", "migration"],
        source={
            "platform": "memory-compiler",
            "original_file": "adr.md",
            "original_sha256": "a" * 64,
            "segment_id": "seg-1",
        },
    )
    review = ReviewSet(
        review_id="review-1",
        source_root=str(tmp_path / "docs"),
        sources=[doc],
        segments=[segment],
        proposals=[proposal],
    )

    saved = save_review_set(tmp_path, review)
    loaded = load_review_set(tmp_path, "review-1")

    assert saved == tmp_path / ".codememory" / "reviews" / "review-1.json"
    assert loaded.review_id == "review-1"
    assert loaded.proposals[0].decision == "pending"
    assert loaded.proposals[0].maturity == "draft"
    assert loaded.proposals[0].type == "atom"


def test_scan_markdown_corpus_preserves_sources_and_ignores_codememory(tmp_path: Path):
    from codememory.compiler.ingest import scan_markdown_corpus

    source = tmp_path / "source"
    source.mkdir()
    (source / "adr.md").write_text("# ADR\n\nDecision text.", encoding="utf-8")
    (source / "notes.txt").write_text("not markdown", encoding="utf-8")
    (source / ".codememory").mkdir()
    (source / ".codememory" / "internal.md").write_text("skip", encoding="utf-8")

    before = (source / "adr.md").read_text(encoding="utf-8")
    docs = scan_markdown_corpus(source)
    after = (source / "adr.md").read_text(encoding="utf-8")

    assert before == after
    assert [doc.rel_path for doc in docs] == ["adr.md"]
    assert docs[0].chars == len(before)
    assert len(docs[0].sha256) == 64


def test_segment_markdown_doc_tracks_headings_and_lines(tmp_path: Path):
    from codememory.compiler.ingest import scan_markdown_corpus
    from codememory.compiler.segment import segment_markdown_doc

    source = tmp_path / "source"
    source.mkdir()
    md = source / "design.md"
    md.write_text(
        "# Design\n\nIntro.\n\n## Decision\n\nUse Markdown.\n\n## Risks\n\nDrift.\n",
        encoding="utf-8",
    )

    doc = scan_markdown_corpus(source)[0]
    segments = segment_markdown_doc(doc)

    assert [segment.heading for segment in segments] == ["Design", "Decision", "Risks"]
    assert segments[0].rel_path == "design.md"
    assert segments[0].start_line == 1
    assert segments[1].start_line == 5
    assert segments[1].end_line >= segments[1].start_line


def test_compile_markdown_corpus_generates_draft_proposals_with_provenance(tmp_path: Path):
    from codememory.compiler.propose import compile_markdown_corpus

    source = tmp_path / "docs"
    source.mkdir()
    (source / "architecture.md").write_text(
        "# Architecture\n\nCodeMemory uses a Core plus Layer Profiles.\n\n"
        "## Work Layer\n\nWork Layer is the first official product layer.\n",
        encoding="utf-8",
    )

    review = compile_markdown_corpus(
        source_root=source,
        review_id="r1",
        tags=["work"],
    )

    assert review.review_id == "r1"
    assert len(review.sources) == 1
    assert len(review.segments) == 2
    assert len(review.proposals) == 2

    first = review.proposals[0]
    assert first.memory_id == "user/imports/architecture/architecture"
    assert first.maturity == "draft"
    assert first.decision == "pending"
    assert first.source["original_file"] == "architecture.md"
    assert first.source["original_sha256"] == review.sources[0].sha256
    assert "work" in first.tags
    assert "compiled" in first.tags


def test_compile_markdown_corpus_disambiguates_duplicate_memory_ids(tmp_path: Path):
    from codememory.compiler.propose import compile_markdown_corpus

    source = tmp_path / "docs"
    source.mkdir()
    (source / "dup.md").write_text("# Same\n\nA.\n\n## Same\n\nB.", encoding="utf-8")

    review = compile_markdown_corpus(source_root=source, review_id="r2")
    ids = [proposal.memory_id for proposal in review.proposals]

    assert len(ids) == len(set(ids))
    assert any(memory_id.endswith("-2") for memory_id in ids)


def test_materialize_review_set_writes_only_accepted_proposals_and_reindexes(tmp_path: Path):
    from codememory.compiler.materialize import materialize_review_set
    from codememory.compiler.models import MemoryProposal, ReviewSet
    from codememory.core import parse_frontmatter
    from codememory.index import load_index

    accepted = MemoryProposal(
        proposal_id="p1",
        memory_id="user/imports/design/decision",
        summary="Use Markdown.",
        body="# Decision\n\nUse Markdown.",
        tags=["compiled"],
        decision="accepted",
        source={
            "platform": "memory-compiler",
            "original_file": "design.md",
            "original_sha256": "b" * 64,
            "segment_id": "seg-1",
        },
    )
    rejected = MemoryProposal(
        proposal_id="p2",
        memory_id="user/imports/design/rejected",
        summary="Rejected.",
        body="# Rejected\n\nDo not write me.",
        tags=["compiled"],
        decision="rejected",
        source={
            "platform": "memory-compiler",
            "original_file": "design.md",
            "original_sha256": "b" * 64,
            "segment_id": "seg-2",
        },
    )
    review = ReviewSet(
        review_id="r3",
        source_root=str(tmp_path / "docs"),
        proposals=[accepted, rejected],
    )

    result = materialize_review_set(tmp_path, review)

    written = tmp_path / "user" / "imports" / "design" / "decision.md"
    rejected_path = tmp_path / "user" / "imports" / "design" / "rejected.md"
    assert result.written == [str(written)]
    assert written.exists()
    assert not rejected_path.exists()

    meta, body = parse_frontmatter(written)
    assert meta["id"] == "user/imports/design/decision"
    assert meta["maturity"] == "draft"
    assert meta["source"]["original_file"] == "design.md"
    assert body.strip() == "# Decision\n\nUse Markdown."

    idx = load_index(tmp_path)
    assert "user/imports/design/decision" in idx.memories


def test_materialize_review_set_rejects_unsafe_memory_ids(tmp_path: Path):
    from codememory.compiler.materialize import materialize_review_set
    from codememory.compiler.models import MemoryProposal, ReviewSet

    unsafe_ids = [
        "/tmp/evil",
        r"\tmp\evil",
        "C:/Temp/evil",
        "user/../../evil",
        r"user\..\evil",
    ]
    review = ReviewSet(
        review_id="unsafe",
        source_root=str(tmp_path / "docs"),
        proposals=[
            MemoryProposal(
                proposal_id=f"p{i}",
                memory_id=memory_id,
                summary="Unsafe",
                body="# Unsafe\n\nDo not write.",
                decision="accepted",
            )
            for i, memory_id in enumerate(unsafe_ids)
        ],
    )

    result = materialize_review_set(tmp_path, review)

    assert result.written == []
    assert len(result.errors) == len(unsafe_ids)
    assert not (tmp_path / "evil.md").exists()
    assert not (tmp_path.parent / "evil.md").exists()


def test_handle_compile_md_saves_review_set(tmp_path: Path):
    from codememory.compiler.review import load_review_set
    from codememory.handlers import handle_compile_md

    source = tmp_path / "docs"
    source.mkdir()
    (source / "guide.md").write_text("# Guide\n\nUse the compiler.", encoding="utf-8")

    output = handle_compile_md(root=tmp_path, source=str(source), review_id="handler-test")
    review = load_review_set(tmp_path, "handler-test")

    assert "Review set saved" in output
    assert len(review.proposals) == 1


def test_save_review_set_rejects_unsafe_review_id(tmp_path: Path):
    import pytest
    from codememory.compiler.models import ReviewSet
    from codememory.compiler.review import save_review_set

    review = ReviewSet(review_id="../outside", source_root=str(tmp_path / "docs"))

    with pytest.raises(ValueError, match="unsafe review_id"):
        save_review_set(tmp_path, review)


def test_compile_markdown_corpus_uses_unique_source_and_proposal_ids_for_identical_files(tmp_path: Path):
    from codememory.compiler.propose import compile_markdown_corpus

    source = tmp_path / "docs"
    source.mkdir()
    content = "# Same\n\nIdentical content."
    (source / "a.md").write_text(content, encoding="utf-8")
    (source / "b.md").write_text(content, encoding="utf-8")

    review = compile_markdown_corpus(source_root=source, review_id="identical")
    source_ids = [doc.source_id for doc in review.sources]
    proposal_ids = [proposal.proposal_id for proposal in review.proposals]

    assert len(source_ids) == len(set(source_ids))
    assert len(proposal_ids) == len(set(proposal_ids))


def test_handle_materialize_review_accept_all(tmp_path: Path):
    from codememory.handlers import handle_compile_md, handle_materialize_review
    from codememory.index import load_index

    source = tmp_path / "docs"
    source.mkdir()
    (source / "guide.md").write_text("# Guide\n\nUse the compiler.", encoding="utf-8")

    handle_compile_md(root=tmp_path, source=str(source), review_id="apply-test")
    output = handle_materialize_review(root=tmp_path, review_id="apply-test", accept_all=True)

    assert "written: 1" in output
    idx = load_index(tmp_path)
    assert "user/imports/guide/guide" in idx.memories


def test_cli_compile_md_and_materialize_review(tmp_path: Path, capsys):
    from codememory.cli import main
    from codememory.index import load_index

    source = tmp_path / "docs"
    source.mkdir()
    (source / "guide.md").write_text("# Guide\n\nUse the compiler.", encoding="utf-8")

    main([
        "--root", str(tmp_path),
        "compile-md",
        str(source),
        "--review-id", "cli-review",
        "--tags", "guide,import-test",
    ])
    compile_output = capsys.readouterr().out
    assert "Review set saved" in compile_output

    main([
        "--root", str(tmp_path),
        "materialize-review",
        "cli-review",
        "--accept-all",
    ])
    materialize_output = capsys.readouterr().out
    assert "written: 1" in materialize_output

    idx = load_index(tmp_path)
    assert "user/imports/guide/guide" in idx.memories
