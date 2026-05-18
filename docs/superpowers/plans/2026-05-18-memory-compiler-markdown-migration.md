# Memory Compiler Markdown Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Core/CLI-level Markdown Memory Compiler that scans an existing Markdown corpus, preserves source provenance, generates a reviewable draft memory graph, and materializes approved proposals into canonical CodeMemory atoms.

**Architecture:** Add a focused `codememory.compiler` package that owns migration models, Markdown corpus ingestion, deterministic proposal generation, review-set persistence, and materialization. The first MVP is deterministic and testable without live LLM calls; later LLM proposal backends can plug into the same proposal model.

**Tech Stack:** Python 3.13, Pydantic v2, PyYAML, existing CodeMemory `core/index/skeletonize` helpers, argparse CLI, pytest.

---

## Scope Check

This plan implements the first working compiler loop:

```text
Markdown corpus → preserved source manifest → draft proposal graph → review JSON → materialized atom files
```

It does **not** implement a Web UI review surface or live LLM extraction. Those are separate plans after this CLI/Core foundation lands. This keeps the first implementation small enough to test and trust.

---

## File Structure

Create:

- `src/codememory/compiler/__init__.py` — public compiler API exports.
- `src/codememory/compiler/models.py` — Pydantic models for source docs, source segments, proposals, review sets, and materialization results.
- `src/codememory/compiler/ingest.py` — Markdown corpus scanning and source hashing.
- `src/codememory/compiler/segment.py` — Markdown section segmentation with provenance.
- `src/codememory/compiler/propose.py` — deterministic draft proposal generation from segments.
- `src/codememory/compiler/review.py` — review-set save/load paths and proposal decision helpers.
- `src/codememory/compiler/materialize.py` — approved proposal → atom `.md` files + reindex.
- `tests/unit/test_memory_compiler.py` — unit tests for the end-to-end compiler loop.

Modify:

- `src/codememory/handlers.py` — add `handle_compile_md()` and `handle_materialize_review()`.
- `src/codememory/cli.py` — add `compile-md` and `materialize-review` subcommands.
- `src/codememory/__init__.py` — export the new compiler entry points.
- `pyproject.toml` — switch packaging to include `codememory.*` subpackages.
- `docs/INTEGRATION.md` — document the CLI migration loop.

---

## Task 1: Add Compiler Models and Review-Set Serialization

**Files:**
- Create: `src/codememory/compiler/__init__.py`
- Create: `src/codememory/compiler/models.py`
- Test: `tests/unit/test_memory_compiler.py`

- [ ] **Step 1: Write failing tests for model defaults and JSON round-trip**

Append this to a new file `tests/unit/test_memory_compiler.py`:

```python
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
```

- [ ] **Step 2: Run the test and confirm it fails**

Run:

```powershell
python -m pytest -q tests/unit/test_memory_compiler.py::test_review_set_round_trip
```

Expected:

```text
ModuleNotFoundError: No module named 'codememory.compiler'
```

- [ ] **Step 3: Create the compiler package exports**

Create `src/codememory/compiler/__init__.py`:

```python
"""Memory Compiler: source corpus → reviewable draft memory graph."""

from .models import (
    MaterializeResult,
    MemoryProposal,
    ReviewSet,
    SourceDoc,
    SourceSegment,
)
from .review import load_review_set, save_review_set

__all__ = [
    "MaterializeResult",
    "MemoryProposal",
    "ReviewSet",
    "SourceDoc",
    "SourceSegment",
    "load_review_set",
    "save_review_set",
]
```

- [ ] **Step 4: Create the Pydantic models**

Create `src/codememory/compiler/models.py`:

```python
"""Data models for Memory Compiler review sets."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


Decision = Literal["pending", "accepted", "rejected"]


class SourceDoc(BaseModel):
    """A source Markdown file discovered during corpus ingestion."""

    source_id: str
    path: str
    rel_path: str
    sha256: str
    chars: int

    @field_validator("sha256")
    @classmethod
    def _sha256_is_hex(cls, value: str) -> str:
        if len(value) != 64:
            raise ValueError("sha256 must be 64 hex characters")
        int(value, 16)
        return value


class SourceSegment(BaseModel):
    """A segment extracted from a source Markdown file."""

    segment_id: str
    source_id: str
    rel_path: str
    heading: str
    level: int = Field(ge=0, le=6)
    ordinal: int = Field(ge=0)
    body: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)


class MemoryProposal(BaseModel):
    """A proposed canonical memory generated from a source segment."""

    proposal_id: str
    memory_id: str
    type: Literal["atom", "schema"] = "atom"
    summary: str
    body: str
    tags: list[str] = Field(default_factory=list)
    maturity: Literal["draft", "verified", "proven", "superseded"] = "draft"
    status: str = "active"
    intensity: int = Field(default=5, ge=1, le=10)
    imports: dict[str, list[str]] = Field(default_factory=dict)
    source: dict[str, Any] = Field(default_factory=dict)
    decision: Decision = "pending"


class ReviewSet(BaseModel):
    """A PR-style migration review artifact."""

    review_id: str
    created: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_root: str
    sources: list[SourceDoc] = Field(default_factory=list)
    segments: list[SourceSegment] = Field(default_factory=list)
    proposals: list[MemoryProposal] = Field(default_factory=list)


class MaterializeResult(BaseModel):
    """Summary of applying accepted proposals to the memory root."""

    written: list[str] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
```

- [ ] **Step 5: Add review-set save/load**

Create `src/codememory/compiler/review.py`:

```python
"""Review-set persistence and decision helpers."""

from __future__ import annotations

import json
from pathlib import Path

from .models import Decision, ReviewSet


def get_reviews_dir(root: Path) -> Path:
    """Return the directory used for compiler review sets."""
    return root / ".codememory" / "reviews"


def get_review_path(root: Path, review_id: str) -> Path:
    """Return the JSON path for a review id."""
    return get_reviews_dir(root) / f"{review_id}.json"


def save_review_set(root: Path, review: ReviewSet) -> Path:
    """Persist a review set as pretty JSON."""
    path = get_review_path(root, review.review_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(review.model_dump(mode="json"), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def load_review_set(root: Path, review_id: str) -> ReviewSet:
    """Load a review set from disk."""
    path = get_review_path(root, review_id)
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ReviewSet.model_validate(raw)


def set_all_decisions(review: ReviewSet, decision: Decision) -> ReviewSet:
    """Return a copy of a review set with every proposal decision changed."""
    updated = []
    for proposal in review.proposals:
        updated.append(proposal.model_copy(update={"decision": decision}))
    return review.model_copy(update={"proposals": updated})
```

- [ ] **Step 6: Run the test and confirm it passes**

Run:

```powershell
python -m pytest -q tests/unit/test_memory_compiler.py::test_review_set_round_trip
```

Expected:

```text
1 passed
```

- [ ] **Step 7: Commit**

```powershell
git add src/codememory/compiler/__init__.py src/codememory/compiler/models.py src/codememory/compiler/review.py tests/unit/test_memory_compiler.py
git commit -m "feat: add memory compiler review models"
```

---

## Task 2: Implement Markdown Corpus Ingestion and Segmentation

**Files:**
- Create: `src/codememory/compiler/ingest.py`
- Create: `src/codememory/compiler/segment.py`
- Modify: `tests/unit/test_memory_compiler.py`

- [ ] **Step 1: Add failing ingestion and segmentation tests**

Append to `tests/unit/test_memory_compiler.py`:

```python
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
```

- [ ] **Step 2: Run tests and confirm they fail**

Run:

```powershell
python -m pytest -q tests/unit/test_memory_compiler.py::test_scan_markdown_corpus_preserves_sources_and_ignores_codememory tests/unit/test_memory_compiler.py::test_segment_markdown_doc_tracks_headings_and_lines
```

Expected:

```text
ModuleNotFoundError: No module named 'codememory.compiler.ingest'
```

- [ ] **Step 3: Implement corpus scanning**

Create `src/codememory/compiler/ingest.py`:

```python
"""Source corpus ingestion for Markdown migration."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .models import SourceDoc


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def scan_markdown_corpus(source_root: Path) -> list[SourceDoc]:
    """Scan a file or directory for Markdown source docs without modifying them."""
    root = source_root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"source root not found: {source_root}")

    if root.is_file():
        files = [root] if root.suffix.lower() == ".md" else []
        rel_base = root.parent
    else:
        rel_base = root
        files = [
            path
            for path in sorted(root.rglob("*.md"))
            if ".codememory" not in path.parts
        ]

    docs: list[SourceDoc] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        rel_path = path.relative_to(rel_base).as_posix()
        sha = _sha256_text(text)
        docs.append(
            SourceDoc(
                source_id=f"src-{sha[:12]}",
                path=str(path),
                rel_path=rel_path,
                sha256=sha,
                chars=len(text),
            )
        )
    return docs
```

- [ ] **Step 4: Implement segment extraction**

Create `src/codememory/compiler/segment.py`:

```python
"""Markdown source segmentation with provenance."""

from __future__ import annotations

from pathlib import Path

from codememory.skeletonize.markdown import split_sections

from .models import SourceDoc, SourceSegment


def _line_number_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, max(0, offset)) + 1


def segment_markdown_doc(doc: SourceDoc) -> list[SourceSegment]:
    """Split one Markdown source doc into heading-based segments."""
    text = Path(doc.path).read_text(encoding="utf-8")
    sections = split_sections(text)
    segments: list[SourceSegment] = []
    search_from = 0

    for ordinal, section in enumerate(sections):
        raw = section.raw or section.body
        start = text.find(raw, search_from)
        if start < 0:
            start = search_from
        end = start + len(raw)
        search_from = max(end, search_from)

        heading = section.heading or Path(doc.rel_path).stem
        segment_id = f"{doc.source_id}-seg-{ordinal}"
        segments.append(
            SourceSegment(
                segment_id=segment_id,
                source_id=doc.source_id,
                rel_path=doc.rel_path,
                heading=heading,
                level=section.level,
                ordinal=ordinal,
                body=section.body.strip(),
                start_line=_line_number_for_offset(text, start),
                end_line=_line_number_for_offset(text, end),
            )
        )
    return segments
```

- [ ] **Step 5: Run tests and confirm they pass**

Run:

```powershell
python -m pytest -q tests/unit/test_memory_compiler.py::test_scan_markdown_corpus_preserves_sources_and_ignores_codememory tests/unit/test_memory_compiler.py::test_segment_markdown_doc_tracks_headings_and_lines
```

Expected:

```text
2 passed
```

- [ ] **Step 6: Commit**

```powershell
git add src/codememory/compiler/ingest.py src/codememory/compiler/segment.py tests/unit/test_memory_compiler.py
git commit -m "feat: scan and segment markdown corpus"
```

---

## Task 3: Generate Deterministic Draft Memory Proposals

**Files:**
- Create: `src/codememory/compiler/propose.py`
- Modify: `src/codememory/compiler/__init__.py`
- Modify: `tests/unit/test_memory_compiler.py`

- [ ] **Step 1: Add failing proposal-generation tests**

Append to `tests/unit/test_memory_compiler.py`:

```python
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
```

- [ ] **Step 2: Run tests and confirm they fail**

Run:

```powershell
python -m pytest -q tests/unit/test_memory_compiler.py::test_compile_markdown_corpus_generates_draft_proposals_with_provenance tests/unit/test_memory_compiler.py::test_compile_markdown_corpus_disambiguates_duplicate_memory_ids
```

Expected:

```text
ModuleNotFoundError: No module named 'codememory.compiler.propose'
```

- [ ] **Step 3: Implement proposal generation**

Create `src/codememory/compiler/propose.py`:

```python
"""Draft memory proposal generation for Markdown corpus migration."""

from __future__ import annotations

import re
from pathlib import Path

from codememory.skeletonize.common import extract_first_sentence, slugify

from .ingest import scan_markdown_corpus
from .models import MemoryProposal, ReviewSet, SourceSegment
from .segment import segment_markdown_doc


def _clean_slug(value: str) -> str:
    slug = slugify(value, max_len=60).strip("-")
    return slug or "untitled"


def _path_prefix(rel_path: str) -> str:
    path = Path(rel_path)
    parts = [*_clean_parts(path.parts[:-1]), _clean_slug(path.stem)]
    return "/".join(part for part in parts if part)


def _clean_parts(parts: tuple[str, ...]) -> list[str]:
    return [_clean_slug(re.sub(r"\.md$", "", part, flags=re.I)) for part in parts]


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


def proposal_from_segment(
    segment: SourceSegment,
    source_sha256: str,
    tags: list[str] | None = None,
    namespace: str = "user/imports",
    used_ids: set[str] | None = None,
) -> MemoryProposal:
    """Create one deterministic draft proposal from a Markdown segment."""
    used_ids = used_ids if used_ids is not None else set()
    prefix = _path_prefix(segment.rel_path)
    heading_slug = _clean_slug(segment.heading)
    memory_id = _unique_memory_id(f"{namespace}/{prefix}/{heading_slug}", used_ids)
    title = segment.heading or Path(segment.rel_path).stem
    body = f"# {title}\n\n{segment.body}".strip()
    summary = extract_first_sentence(segment.body, max_chars=120) or title
    proposal_tags = list(dict.fromkeys([*(tags or []), "compiled", "markdown"]))

    return MemoryProposal(
        proposal_id=f"prop-{segment.segment_id}",
        memory_id=memory_id,
        summary=summary,
        body=body,
        tags=proposal_tags,
        maturity="draft",
        source={
            "platform": "memory-compiler",
            "created_by": "codememory compile-md",
            "original_file": segment.rel_path,
            "original_sha256": source_sha256,
            "segment_id": segment.segment_id,
            "heading": segment.heading,
            "line_start": segment.start_line,
            "line_end": segment.end_line,
        },
    )


def compile_markdown_corpus(
    source_root: Path,
    review_id: str,
    tags: list[str] | None = None,
    namespace: str = "user/imports",
) -> ReviewSet:
    """Compile a Markdown corpus into a draft review set."""
    docs = scan_markdown_corpus(source_root)
    segments = []
    proposals = []
    used_ids: set[str] = set()
    source_sha_by_id = {doc.source_id: doc.sha256 for doc in docs}

    for doc in docs:
        doc_segments = segment_markdown_doc(doc)
        segments.extend(doc_segments)
        for segment in doc_segments:
            proposals.append(
                proposal_from_segment(
                    segment,
                    source_sha256=source_sha_by_id[segment.source_id],
                    tags=tags,
                    namespace=namespace,
                    used_ids=used_ids,
                )
            )

    return ReviewSet(
        review_id=review_id,
        source_root=str(source_root.resolve()),
        sources=docs,
        segments=segments,
        proposals=proposals,
    )
```

- [ ] **Step 4: Export proposal APIs**

Modify `src/codememory/compiler/__init__.py` to include:

```python
from .propose import compile_markdown_corpus, proposal_from_segment
```

and add these names to `__all__`:

```python
"compile_markdown_corpus",
"proposal_from_segment",
```

- [ ] **Step 5: Run tests and confirm they pass**

Run:

```powershell
python -m pytest -q tests/unit/test_memory_compiler.py::test_compile_markdown_corpus_generates_draft_proposals_with_provenance tests/unit/test_memory_compiler.py::test_compile_markdown_corpus_disambiguates_duplicate_memory_ids
```

Expected:

```text
2 passed
```

- [ ] **Step 6: Commit**

```powershell
git add src/codememory/compiler/__init__.py src/codememory/compiler/propose.py tests/unit/test_memory_compiler.py
git commit -m "feat: generate markdown memory proposals"
```

---

## Task 4: Materialize Accepted Proposals into Canonical Atom Files

**Files:**
- Create: `src/codememory/compiler/materialize.py`
- Modify: `src/codememory/compiler/__init__.py`
- Modify: `tests/unit/test_memory_compiler.py`

- [ ] **Step 1: Add failing materialization tests**

Append to `tests/unit/test_memory_compiler.py`:

```python
def test_materialize_review_set_writes_only_accepted_proposals_and_reindexes(tmp_path: Path):
    from codememory.compiler.materialize import materialize_review_set
    from codememory.compiler.models import MemoryProposal, ReviewSet
    from codememory.index import load_index
    from codememory.core import parse_frontmatter

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
```

- [ ] **Step 2: Run the test and confirm it fails**

Run:

```powershell
python -m pytest -q tests/unit/test_memory_compiler.py::test_materialize_review_set_writes_only_accepted_proposals_and_reindexes
```

Expected:

```text
ModuleNotFoundError: No module named 'codememory.compiler.materialize'
```

- [ ] **Step 3: Implement materialization**

Create `src/codememory/compiler/materialize.py`:

```python
"""Materialize accepted memory proposals into canonical atom files."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from codememory.core import compute_body_hash, get_memory_path
from codememory.index import reindex

from .models import MaterializeResult, ReviewSet


def _frontmatter_for_proposal(proposal) -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    frontmatter = {
        "type": proposal.type,
        "id": proposal.memory_id,
        "summary": proposal.summary,
        "status": proposal.status,
        "created": now,
        "updated": now,
        "version": 1,
        "tags": proposal.tags,
        "intensity": proposal.intensity,
        "maturity": proposal.maturity,
        "source": proposal.source,
        "evidence": {
            "contributors": ["memory-compiler"],
            "sessions": [],
        },
        "summary_hash": compute_body_hash(proposal.body.strip()),
    }
    if proposal.imports:
        frontmatter["imports"] = proposal.imports
    return frontmatter


def materialize_review_set(
    root: Path,
    review: ReviewSet,
    accept_all: bool = False,
) -> MaterializeResult:
    """Write accepted proposals to disk and refresh the index."""
    result = MaterializeResult()

    for proposal in review.proposals:
        accepted = proposal.decision == "accepted" or accept_all
        if not accepted:
            result.skipped.append(proposal.proposal_id)
            continue

        file_path = get_memory_path(root, proposal.memory_id)
        if file_path.exists():
            result.errors.append(f"exists: {proposal.memory_id}")
            continue

        file_path.parent.mkdir(parents=True, exist_ok=True)
        yaml_str = yaml.dump(
            _frontmatter_for_proposal(proposal),
            allow_unicode=True,
            sort_keys=False,
        )
        content = f"---\n{yaml_str}---\n{proposal.body.strip()}\n"
        file_path.write_text(content, encoding="utf-8")
        result.written.append(str(file_path))

    if result.written:
        reindex(root)

    return result
```

- [ ] **Step 4: Export materialization API**

Modify `src/codememory/compiler/__init__.py` to include:

```python
from .materialize import materialize_review_set
```

and add this name to `__all__`:

```python
"materialize_review_set",
```

- [ ] **Step 5: Run the test and confirm it passes**

Run:

```powershell
python -m pytest -q tests/unit/test_memory_compiler.py::test_materialize_review_set_writes_only_accepted_proposals_and_reindexes
```

Expected:

```text
1 passed
```

- [ ] **Step 6: Commit**

```powershell
git add src/codememory/compiler/__init__.py src/codememory/compiler/materialize.py tests/unit/test_memory_compiler.py
git commit -m "feat: materialize accepted memory proposals"
```

---

## Task 5: Add CLI Handlers for Compile and Materialize

**Files:**
- Modify: `src/codememory/handlers.py`
- Modify: `tests/unit/test_memory_compiler.py`

- [ ] **Step 1: Add failing handler tests**

Append to `tests/unit/test_memory_compiler.py`:

```python
def test_handle_compile_md_saves_review_set(tmp_path: Path):
    from codememory.handlers import handle_compile_md
    from codememory.compiler.review import load_review_set

    source = tmp_path / "docs"
    source.mkdir()
    (source / "guide.md").write_text("# Guide\n\nUse the compiler.", encoding="utf-8")

    output = handle_compile_md(
        root=tmp_path,
        source=str(source),
        review_id="compile-test",
        tags=["guide"],
    )

    assert ".codememory" in output
    review = load_review_set(tmp_path, "compile-test")
    assert len(review.proposals) == 1
    assert review.proposals[0].decision == "pending"


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
```

- [ ] **Step 2: Run tests and confirm they fail**

Run:

```powershell
python -m pytest -q tests/unit/test_memory_compiler.py::test_handle_compile_md_saves_review_set tests/unit/test_memory_compiler.py::test_handle_materialize_review_accept_all
```

Expected:

```text
ImportError: cannot import name 'handle_compile_md'
```

- [ ] **Step 3: Add handler imports**

Modify the import block in `src/codememory/handlers.py`:

```python
from .compiler.materialize import materialize_review_set
from .compiler.propose import compile_markdown_corpus
from .compiler.review import load_review_set, save_review_set, set_all_decisions
```

- [ ] **Step 4: Add handler functions**

Add these functions near `handle_skeletonize()` in `src/codememory/handlers.py`:

```python
def handle_compile_md(
    root: Path,
    source: str,
    review_id: str | None = None,
    tags: list[str] | None = None,
    namespace: str = "user/imports",
) -> str:
    """Compile Markdown corpus into a reviewable draft proposal graph."""
    source_path = Path(source)
    if review_id is None:
        review_id = datetime.now(timezone.utc).strftime("compile-%Y%m%d-%H%M%S")

    review = compile_markdown_corpus(
        source_root=source_path,
        review_id=review_id,
        tags=tags,
        namespace=namespace,
    )
    path = save_review_set(root, review)
    return (
        f"Review set saved: {path}\n"
        f"sources: {len(review.sources)}\n"
        f"segments: {len(review.segments)}\n"
        f"proposals: {len(review.proposals)}"
    )


def handle_materialize_review(
    root: Path,
    review_id: str,
    accept_all: bool = False,
) -> str:
    """Materialize accepted proposals from a compiler review set."""
    review = load_review_set(root, review_id)
    if accept_all:
        review = set_all_decisions(review, "accepted")
        save_review_set(root, review)

    result = materialize_review_set(root, review, accept_all=False)
    lines = [
        f"written: {len(result.written)}",
        f"skipped: {len(result.skipped)}",
        f"errors: {len(result.errors)}",
    ]
    if result.errors:
        lines.append("error details:")
        lines.extend(f"- {err}" for err in result.errors)
    return "\n".join(lines)
```

- [ ] **Step 5: Run tests and confirm they pass**

Run:

```powershell
python -m pytest -q tests/unit/test_memory_compiler.py::test_handle_compile_md_saves_review_set tests/unit/test_memory_compiler.py::test_handle_materialize_review_accept_all
```

Expected:

```text
2 passed
```

- [ ] **Step 6: Commit**

```powershell
git add src/codememory/handlers.py tests/unit/test_memory_compiler.py
git commit -m "feat: add memory compiler handlers"
```

---

## Task 6: Add CLI Commands

**Files:**
- Modify: `src/codememory/cli.py`
- Modify: `tests/unit/test_memory_compiler.py`

- [ ] **Step 1: Add failing CLI parser tests**

Append to `tests/unit/test_memory_compiler.py`:

```python
def test_cli_compile_md_and_materialize_review(tmp_path: Path, capsys):
    import os
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
```

- [ ] **Step 2: Run the test and confirm it fails**

Run:

```powershell
python -m pytest -q tests/unit/test_memory_compiler.py::test_cli_compile_md_and_materialize_review
```

Expected:

```text
SystemExit: 2
```

because argparse does not know `compile-md`.

- [ ] **Step 3: Import the new handlers**

Modify the handler import list in `src/codememory/cli.py`:

```python
    handle_compile_md,
    handle_materialize_review,
```

- [ ] **Step 4: Add CLI subcommands**

Add this after the existing `skeletonize` subcommand block in `src/codememory/cli.py`:

```python
    # compile-md
    p = subparsers.add_parser("compile-md", help="Compile Markdown corpus into a review set")
    _add_logging_flags(p)
    p.add_argument("source", help="Markdown file or directory to compile")
    p.add_argument("--review-id", help="Stable review ID; defaults to timestamp")
    p.add_argument("--tags", help="Comma-separated tags for generated proposals")
    p.add_argument("--namespace", default="user/imports", help="Memory ID namespace for proposals")

    # materialize-review
    p = subparsers.add_parser("materialize-review", help="Materialize accepted compiler proposals")
    _add_logging_flags(p)
    p.add_argument("review_id", help="Review ID from compile-md")
    p.add_argument("--accept-all", action="store_true", help="Accept all pending proposals before materializing")
```

- [ ] **Step 5: Add command dispatch branches**

Add this near the bottom command dispatch in `src/codememory/cli.py`:

```python
    elif cmd == "compile-md":
        tags_list = None
        if args.tags:
            tags_list = [t.strip() for t in args.tags.split(",") if t.strip()]
        print(handle_compile_md(
            root,
            args.source,
            review_id=args.review_id,
            tags=tags_list,
            namespace=args.namespace,
        ))
    elif cmd == "materialize-review":
        print(handle_materialize_review(
            root,
            args.review_id,
            accept_all=args.accept_all,
        ))
```

- [ ] **Step 6: Run the CLI test and confirm it passes**

Run:

```powershell
python -m pytest -q tests/unit/test_memory_compiler.py::test_cli_compile_md_and_materialize_review
```

Expected:

```text
1 passed
```

- [ ] **Step 7: Commit**

```powershell
git add src/codememory/cli.py tests/unit/test_memory_compiler.py
git commit -m "feat: add memory compiler cli commands"
```

---

## Task 7: Export Public APIs and Fix Package Discovery

**Files:**
- Modify: `src/codememory/__init__.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Add compiler exports to package root**

Modify `src/codememory/__init__.py`:

```python
from .compiler import (
    MaterializeResult,
    MemoryProposal,
    ReviewSet,
    SourceDoc,
    SourceSegment,
    compile_markdown_corpus,
    load_review_set,
    materialize_review_set,
    save_review_set,
)
```

Add these names to `__all__`:

```python
"MaterializeResult",
"MemoryProposal",
"ReviewSet",
"SourceDoc",
"SourceSegment",
"compile_markdown_corpus",
"load_review_set",
"materialize_review_set",
"save_review_set",
```

- [ ] **Step 2: Update package discovery so subpackages ship**

Replace this block in `pyproject.toml`:

```toml
[tool.setuptools]
package-dir = { "" = "src" }
packages = ["codememory", "harnesslib", "llm_gateway"]
```

with:

```toml
[tool.setuptools]
package-dir = { "" = "src" }

[tool.setuptools.packages.find]
where = ["src"]
include = ["codememory*", "harnesslib*", "llm_gateway*"]
```

- [ ] **Step 3: Run import verification**

Run:

```powershell
@'
from codememory import compile_markdown_corpus, materialize_review_set
from codememory.compiler import ReviewSet
print(compile_markdown_corpus.__name__)
print(materialize_review_set.__name__)
print(ReviewSet.__name__)
'@ | python -
```

Expected:

```text
compile_markdown_corpus
materialize_review_set
ReviewSet
```

- [ ] **Step 4: Commit**

```powershell
git add src/codememory/__init__.py pyproject.toml
git commit -m "chore: export compiler APIs and package submodules"
```

---

## Task 8: Document the Markdown Migration Loop

**Files:**
- Modify: `docs/INTEGRATION.md`

- [ ] **Step 1: Add migration documentation**

Add this section after the Quick Start in `docs/INTEGRATION.md`:

````markdown
## Markdown Migration: Memory Compiler

CodeMemory can migrate an existing Markdown corpus without rewriting the source files. The compiler creates a PR-style review set first; only accepted proposals are materialized as canonical memory atoms.

```powershell
# 1. Compile existing Markdown into a review set
codememory --root examples/work compile-md ./docs --review-id docs-import --tags "work,migration"

# 2. Inspect the review JSON
cat examples/work/.codememory/reviews/docs-import.json

# 3. Materialize every proposal for a first-pass migration
codememory --root examples/work materialize-review docs-import --accept-all

# 4. Validate the resulting memory graph
codememory --root examples/work validate
```

Compiler guarantees:

- Original Markdown files are not modified.
- Generated memories start as `maturity: draft`.
- Each generated memory stores `source.original_file`, `source.original_sha256`, and `source.segment_id`.
- The review JSON can be edited before materialization.
- Existing memory files are not overwritten.
````

- [ ] **Step 2: Verify Markdown formatting does not break fenced blocks**

Run:

```powershell
@'
from pathlib import Path
text = Path("docs/INTEGRATION.md").read_text(encoding="utf-8")
assert "## Markdown Migration: Memory Compiler" in text
assert text.count("```") % 2 == 0
print("docs ok")
'@ | python -
```

Expected:

```text
docs ok
```

- [ ] **Step 3: Commit**

```powershell
git add docs/INTEGRATION.md
git commit -m "docs: document markdown memory compiler migration"
```

---

## Task 9: Run Full Verification

**Files:**
- No code changes unless verification reveals a failure caused by this plan.

- [ ] **Step 1: Run focused compiler tests**

Run:

```powershell
python -m pytest -q tests/unit/test_memory_compiler.py
```

Expected:

```text
all tests in tests/unit/test_memory_compiler.py pass
```

- [ ] **Step 2: Run core unit tests**

Run:

```powershell
python -m pytest -q tests/unit tests/test_api.py
```

Expected:

```text
all tests pass
```

- [ ] **Step 3: Run the standalone integration script**

Run:

```powershell
python tests/integration_test.py
```

Expected:

```text
24/24 tests passed
```

- [ ] **Step 4: Run a manual migration smoke test**

Run:

```powershell
$tmp = Join-Path $env:TEMP "codememory-compiler-smoke"
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force "$tmp\docs" | Out-Null
Set-Content -Path "$tmp\docs\architecture.md" -Value "# Architecture`n`nCore plus Work Layer.`n`n## Migration`n`nMarkdown compiler creates proposals." -Encoding UTF8
python -m codememory.cli --root "$tmp\memory" compile-md "$tmp\docs" --review-id smoke --tags "smoke"
python -m codememory.cli --root "$tmp\memory" materialize-review smoke --accept-all
python -m codememory.cli --root "$tmp\memory" validate
```

Expected:

```text
Review set saved:
written: 2
Validation complete
Errors: 0
```

- [ ] **Step 5: Inspect git diff**

Run:

```powershell
git diff --stat HEAD
git status --short
```

Expected:

```text
Only intentional source, tests, packaging, and docs files are modified.
```

If the smoke test created files outside the temp directory, remove them before the final commit.

- [ ] **Step 6: Final commit if any verification fixes were needed**

If verification required fixes, commit them:

```powershell
git add src/codememory tests/unit/test_memory_compiler.py pyproject.toml docs/INTEGRATION.md
git commit -m "fix: stabilize memory compiler migration"
```

If no fixes were needed, do not create an empty commit.

---

## Self-Review

**Spec coverage:**

- Memory Compiler as formal construction path: Tasks 1-6.
- Markdown corpus as first migration source: Tasks 2-3 and Task 8.
- Preserve originals: Task 2 tests source text before/after and Task 8 documents the guarantee.
- Draft graph / proposal before canonical memory: Tasks 1, 3, 5, and 6.
- Review before materialize: Tasks 1, 4, 5, and 6.
- Provenance back to source: Tasks 3 and 4.
- Core/CLI first, UI next: Scope Check.

**Placeholder scan:** This plan intentionally contains no placeholder markers or open-ended implementation steps.

**Type consistency:** The plan consistently uses `SourceDoc`, `SourceSegment`, `MemoryProposal`, `ReviewSet`, `MaterializeResult`, `compile_markdown_corpus`, `save_review_set`, `load_review_set`, and `materialize_review_set`.
