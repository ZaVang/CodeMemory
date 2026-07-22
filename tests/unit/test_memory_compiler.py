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
        uri=str(tmp_path / "docs" / "adr.md"),
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


def test_segment_body_locator_does_not_match_same_text_in_heading(tmp_path: Path):
    from codememory.compiler.ingest import scan_markdown_corpus
    from codememory.compiler.segment import paragraphs_from_segments, segment_markdown_doc

    source = tmp_path / "source.md"
    source.write_text("# Same\n\nSame\n", encoding="utf-8")
    doc = scan_markdown_corpus(source)[0]

    paragraphs = paragraphs_from_segments(segment_markdown_doc(doc))

    assert len(paragraphs) == 1
    assert paragraphs[0].start_line == 3
    assert paragraphs[0].end_line == 3


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
        memory_root=tmp_path,
        source_root=source,
        review_id="r1",
        tags=["work"],
    )

    assert review.review_id == "r1"
    assert len(review.sources) == 1
    assert len(review.segments) == 2
    assert len(review.paragraphs) == 2
    assert len(review.proposals) == 3

    first = review.proposals[0]
    assert first.memory_id == "user/imports/architecture/anchor"
    assert first.role == "anchor"
    assert first.status == "proposed"
    assert first.maturity == "draft"
    assert first.decision == "pending"
    assert first.source["original_file"] == "architecture.md"
    assert first.source["original_sha256"] == review.sources[0].sha256
    assert first.source_refs[0].artifact_id == review.sources[0].source_id
    assert "work" in first.tags
    assert "compiled" in first.tags

    derived = review.proposals[1]
    assert derived.role == "derived"
    assert derived.source["paragraph_id"] == review.paragraphs[0].paragraph_id
    assert derived.source_refs[0].range == "L3-L3"
    assert derived.imports == {}


def test_compile_markdown_corpus_disambiguates_duplicate_memory_ids(tmp_path: Path):
    from codememory.compiler.propose import compile_markdown_corpus

    source = tmp_path / "docs"
    source.mkdir()
    (source / "dup.md").write_text("# Same\n\nA.\n\n## Same\n\nB.", encoding="utf-8")

    review = compile_markdown_corpus(memory_root=tmp_path, source_root=source, review_id="r2")
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
    assert len(review.proposals) == 2
    assert "registered sources: 1" in output
    assert "anchors: 1" in output
    assert "derived: 1" in output


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

    review = compile_markdown_corpus(
        memory_root=tmp_path,
        source_root=source,
        review_id="identical",
    )
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

    assert "written: 2" in output
    idx = load_index(tmp_path)
    assert "user/imports/guide/anchor" in idx.memories
    assert "user/imports/guide/guide-p1" in idx.memories
    assert idx.memories["user/imports/guide/anchor"].status == "proposed"
    assert idx.memories["user/imports/guide/guide-p1"].source_refs[0].artifact_id.startswith("src/")


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
    assert "written: 2" in materialize_output

    idx = load_index(tmp_path)
    assert "user/imports/guide/anchor" in idx.memories
    assert "user/imports/guide/guide-p1" in idx.memories


def test_importer_v2_registers_one_source_and_anchor_per_doc_with_paragraph_locators(tmp_path: Path):
    from codememory.compiler.review import load_review_set
    from codememory.handlers import handle_compile_md
    from codememory.sources import load_source_registry

    memory_root = tmp_path / "memory"
    source = tmp_path / "docs"
    source.mkdir()
    first = source / "a.md"
    second = source / "b.md"
    first.write_bytes(b"# A\r\n\r\nOne.\r\n \r\nTwo lines\r\ncontinue.\r\n")
    second.write_text("# B\n\nThree.\n", encoding="utf-8")
    before = {path: path.read_bytes() for path in (first, second)}

    handle_compile_md(memory_root, str(source), review_id="v2-contract")
    review = load_review_set(memory_root, "v2-contract")
    registry = load_source_registry(memory_root)

    assert len(registry.sources) == 2
    assert len(review.sources) == 2
    assert all(registry.sources[doc.source_id].sha256 == doc.sha256 for doc in review.sources)
    assert len([p for p in review.proposals if p.role == "anchor"]) == 2
    assert len([p for p in review.proposals if p.role == "derived"]) == 3
    assert len(review.paragraphs) == 3
    assert all(p.status == "proposed" and p.decision == "pending" for p in review.proposals)
    assert all(p.imports == {} for p in review.proposals)

    source_lines = {
        doc.source_id: Path(doc.path).read_text(encoding="utf-8").splitlines()
        for doc in review.sources
    }
    for paragraph in review.paragraphs:
        lines = source_lines[paragraph.source_id]
        located = "\n".join(lines[paragraph.start_line - 1 : paragraph.end_line])
        assert located == paragraph.body
        proposal = next(
            item for item in review.proposals
            if item.source.get("paragraph_id") == paragraph.paragraph_id
        )
        assert proposal.source_refs[0].artifact_id == paragraph.source_id
        assert proposal.source_refs[0].section_id == paragraph.paragraph_id
        assert proposal.source_refs[0].range == f"L{paragraph.start_line}-L{paragraph.end_line}"

    assert {path: path.read_bytes() for path in (first, second)} == before


def test_compile_retry_preserves_decisions_and_registry_and_review_bytes(tmp_path: Path):
    from codememory.compiler.review import load_review_set, save_review_set
    from codememory.handlers import handle_compile_md
    from codememory.sources import get_sources_index_path

    source = tmp_path / "docs"
    source.mkdir()
    (source / "guide.md").write_text("# Guide\n\nOne.\n\nTwo.", encoding="utf-8")

    handle_compile_md(tmp_path, str(source), review_id="retry")
    review = load_review_set(tmp_path, "retry")
    review.proposals[1].decision = "accepted"
    review_path = save_review_set(tmp_path, review)
    registry_path = get_sources_index_path(tmp_path)
    review_bytes = review_path.read_bytes()
    registry_bytes = registry_path.read_bytes()

    handle_compile_md(tmp_path, str(source), review_id="retry")

    assert review_path.read_bytes() == review_bytes
    assert registry_path.read_bytes() == registry_bytes
    assert load_review_set(tmp_path, "retry").proposals[1].decision == "accepted"


def test_conflicting_review_id_does_not_replace_review_or_registry(tmp_path: Path):
    import pytest

    from codememory.compiler.review import review_path
    from codememory.handlers import handle_compile_md
    from codememory.sources import get_source_artifact, get_sources_index_path, load_source_registry

    source = tmp_path / "docs"
    source.mkdir()
    document = source / "guide.md"
    document.write_text("# Guide\n\nOriginal.", encoding="utf-8")
    handle_compile_md(tmp_path, str(source), review_id="fixed")
    old_review = review_path(tmp_path, "fixed").read_bytes()
    old_registry = get_sources_index_path(tmp_path).read_bytes()
    artifact_id = next(iter(load_source_registry(tmp_path).sources))
    old_hash = get_source_artifact(tmp_path, artifact_id).sha256

    document.write_text("# Guide\n\nChanged.", encoding="utf-8")
    with pytest.raises(ValueError, match="different compiler input"):
        handle_compile_md(tmp_path, str(source), review_id="fixed")

    assert review_path(tmp_path, "fixed").read_bytes() == old_review
    assert get_sources_index_path(tmp_path).read_bytes() == old_registry

    handle_compile_md(tmp_path, str(source), review_id="changed")
    registry = load_source_registry(tmp_path)
    assert list(registry.sources) == [artifact_id]
    assert registry.sources[artifact_id].sha256 != old_hash


def test_materialized_importer_proposals_stay_noncanonical_and_keep_source_immutable(tmp_path: Path):
    import pytest

    from codememory.build import build_context_pack
    from codememory.compiler.review import load_review_set
    from codememory.handlers import handle_compile_md, handle_materialize_review
    from codememory.index import load_index
    from codememory.search import search

    source = tmp_path / "source.md"
    source.write_text("# Decision\n\nKeep the source immutable.", encoding="utf-8")
    before = source.read_bytes()
    handle_compile_md(tmp_path, str(source), review_id="materialize-v2")
    review = load_review_set(tmp_path, "materialize-v2")
    review.proposals[0].status = "active"
    from codememory.compiler.review import save_review_set
    save_review_set(tmp_path, review)

    output = handle_materialize_review(tmp_path, "materialize-v2", accept_all=True)
    review = load_review_set(tmp_path, "materialize-v2")
    index = load_index(tmp_path)

    assert "written: 2" in output
    assert source.read_bytes() == before
    assert all(index.memories[p.memory_id].status == "proposed" for p in review.proposals)
    assert all(index.memories[p.memory_id].source_refs for p in review.proposals)
    assert search(tmp_path, query="immutable") == []
    assert search(tmp_path, query="immutable", status="proposed")
    with pytest.raises(ValueError, match="not assemblable"):
        build_context_pack(tmp_path, review.proposals[0].memory_id)


def test_importer_v2_materialize_rejects_missing_source_refs(tmp_path: Path):
    from codememory.compiler.review import load_review_set, save_review_set
    from codememory.handlers import handle_compile_md, handle_materialize_review

    source = tmp_path / "source.md"
    source.write_text("# Source\n\nProvenance is required.", encoding="utf-8")
    handle_compile_md(tmp_path, str(source), review_id="missing-ref")
    review = load_review_set(tmp_path, "missing-ref")
    review.proposals[0].source_refs = []
    review.proposals[0].decision = "accepted"
    save_review_set(tmp_path, review)

    output = handle_materialize_review(tmp_path, "missing-ref")

    assert "written: 0" in output
    assert "missing source_refs" in output
    assert not (tmp_path / "user" / "imports" / "source" / "anchor.md").exists()
