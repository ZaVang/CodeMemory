"""Golden-question test contract (architecture.md §3.4).

Core only exports the question set with assembled context and records
reported results. The optional three-arm runner lives in ``evaluation/``;
this module stays provider-free by design — pytest is independent of the
compiler and test contract.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from .build import build_context_pack, render_context_pack
from .index import load_index


class GoldenQuestion(BaseModel):
    """One verifiable question attached to an entry atom."""

    q: str
    expect: str | None = None


class TestBundle(BaseModel):
    """What `codememory test <entry>` hands to the runner."""

    format_version: str = "memory-test/v1"
    entry: str
    context: str
    questions: list[GoldenQuestion] = Field(default_factory=list)
    notices: list[str] = Field(default_factory=list)


def export_test_bundle(
    root_dir: Path,
    entry_id: str,
    *,
    depth: str = "recommended",
    budget: int | None = None,
) -> TestBundle:
    """Assemble the entry's context and export its golden questions."""
    pack = build_context_pack(
        root_dir, entry_id, depth=depth, budget=budget, track_access=False,
    )
    context = render_context_pack(pack, "xml-markdown")

    raw = load_index(root_dir).memories[entry_id].golden_questions
    questions = [
        GoldenQuestion(q=item["q"], expect=item.get("expect"))
        for item in raw
        if isinstance(item, dict) and isinstance(item.get("q"), str)
    ]

    notices: list[str] = []
    if not questions:
        notices.append(
            f"No golden_questions declared on '{entry_id}'; nothing to verify."
        )
    return TestBundle(entry=entry_id, context=context, questions=questions, notices=notices)


def record_test_report(root_dir: Path, entry_id: str, results: list[dict]) -> str:
    """Validate runner results ({q, answer, pass}) and write them to the log."""
    if not isinstance(results, list) or not results:
        raise ValueError("results must be a non-empty list of {q, answer, pass} objects")
    for i, item in enumerate(results):
        if not isinstance(item, dict) or not all(k in item for k in ("q", "answer", "pass")):
            raise ValueError(f"results[{i}] must contain q, answer and pass")
        if not isinstance(item["pass"], bool):
            raise ValueError(f"results[{i}].pass must be a boolean")

    passed = sum(1 for r in results if r["pass"])
    summary = f"{entry_id}: {passed}/{len(results)} golden questions passed"

    from .log import append_log
    append_log(root_dir, "test_report", summary)
    return summary
