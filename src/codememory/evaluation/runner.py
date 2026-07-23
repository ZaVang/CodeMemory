"""Provider-neutral three-arm golden-question evaluation runner."""

from __future__ import annotations

import hashlib
import html
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from ..build import build_context_pack, render_context_pack
from ..core import estimate_tokens, parse_frontmatter
from ..index import load_index
from ..models import NON_ASSEMBLABLE_STATUSES
from ..test_contract import GoldenQuestion
from .models import (
    EvalAnswerResult,
    EvalArmMetrics,
    EvalArmName,
    EvalArmResult,
    EvalCallMetadata,
    EvalComparison,
    EvalPairwiseOutcome,
    EvalReport,
    EvalSample,
    EvalSettings,
    EvalSkippedQuestion,
    EvalUsage,
    EvalJudgeResult,
)


ARM_ORDER: tuple[EvalArmName, ...] = (
    "context_pack",
    "full_memory",
    "no_memory",
)
_FROZEN_GENERATED_AT = "1970-01-01T00:00:00+00:00"


class EvaluationClient(Protocol):
    """Minimal client boundary; implementations may not receive arm identity."""

    async def answer(self, *, question: str, context: str) -> EvalAnswerResult:
        """Answer one question from one optional memory context."""

    async def judge(
        self,
        *,
        question: str,
        expect: str,
        answer: str,
    ) -> EvalJudgeResult:
        """Blindly judge one answer against expected points."""


@dataclass(frozen=True)
class FrozenArm:
    """In-memory context snapshot; context is never copied into the report."""

    arm: EvalArmName
    context: str
    sha256: str
    chars: int
    estimated_tokens: int


@dataclass(frozen=True)
class ScoredQuestion:
    question_index: int
    question: str
    expect: str


@dataclass(frozen=True)
class FrozenEvaluationInput:
    """All experiment inputs frozen before the first provider call."""

    entry: str
    dataset_sha256: str
    arms: tuple[FrozenArm, ...]
    scored_questions: tuple[ScoredQuestion, ...]
    skipped_questions: tuple[EvalSkippedQuestion, ...]
    notices: tuple[str, ...]


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_indexed_path(root: Path, relative_path: str, memory_id: str) -> Path:
    resolved_root = root.resolve()
    path = (resolved_root / relative_path).resolve()
    try:
        path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(
            f"Indexed path for '{memory_id}' escapes the bound memory root"
        ) from exc
    if not path.is_file():
        raise FileNotFoundError(f"Indexed memory file for '{memory_id}' was not found")
    return path


def build_full_memory_context(root: Path) -> str:
    """Render all assemblable canonical bodies without evaluation frontmatter.

    The representation is deliberately not the raw Markdown file: raw
    frontmatter can contain ``golden_questions.expect`` and would leak the
    answer key to the answer model.
    """

    index = load_index(root)
    records: list[str] = []
    for memory_id in sorted(index.memories):
        entry = index.memories[memory_id]
        if entry.status in NON_ASSEMBLABLE_STATUSES:
            continue
        if entry.type not in ("atom", "schema"):
            continue
        path = _safe_indexed_path(root, entry.path, memory_id)
        _meta, body = parse_frontmatter(path)
        safe_id = html.escape(memory_id, quote=True)
        safe_type = html.escape(entry.type, quote=True)
        safe_summary = html.escape(entry.summary, quote=False)
        records.extend(
            [
                f'<memory id="{safe_id}" type="{safe_type}">',
                f"<summary>{safe_summary}</summary>",
                "<authored_body>",
                body.strip(),
                "</authored_body>",
                "</memory>",
            ]
        )

    return (
        '<codememory_full_memory format_version="full-memory/v1">\n'
        + "\n".join(records)
        + "\n</codememory_full_memory>\n"
    )


def _questions_for_entry(root: Path, entry_id: str) -> list[GoldenQuestion]:
    index = load_index(root)
    if entry_id not in index.memories:
        raise ValueError(f"Target memory '{entry_id}' not found. Did you reindex?")
    raw = index.memories[entry_id].golden_questions
    return [
        GoldenQuestion(q=item["q"], expect=item.get("expect"))
        for item in raw
        if isinstance(item, dict) and isinstance(item.get("q"), str)
    ]


def freeze_evaluation_input(
    root: Path,
    entry_id: str,
    *,
    depth: str = "recommended",
    budget: int | None = None,
) -> FrozenEvaluationInput:
    """Freeze all contexts and scored questions before client construction."""

    questions = _questions_for_entry(root, entry_id)
    scored: list[ScoredQuestion] = []
    skipped: list[EvalSkippedQuestion] = []
    for index, question in enumerate(questions):
        expect = question.expect.strip() if isinstance(question.expect, str) else ""
        if expect:
            scored.append(
                ScoredQuestion(
                    question_index=index,
                    question=question.q,
                    expect=expect,
                )
            )
        else:
            skipped.append(
                EvalSkippedQuestion(question_index=index, question=question.q)
            )
    if not scored:
        raise ValueError(
            f"No scorable golden questions on '{entry_id}'; add a non-empty expect"
        )

    pack = build_context_pack(
        root,
        entry_id,
        depth=depth,
        budget=budget,
        track_access=False,
    ).model_copy(update={"generated_at": _FROZEN_GENERATED_AT})
    context_pack = render_context_pack(pack, "xml-markdown")
    full_memory = build_full_memory_context(root)

    arm_contexts: tuple[tuple[EvalArmName, str], ...] = (
        ("context_pack", context_pack),
        ("full_memory", full_memory),
        ("no_memory", ""),
    )
    arms = tuple(
        FrozenArm(
            arm=arm,
            context=context,
            sha256=_sha256(context),
            chars=len(context),
            estimated_tokens=estimate_tokens(context),
        )
        for arm, context in arm_contexts
    )
    notices = tuple(
        [
            f"Skipped {len(skipped)} golden question(s) without a non-empty expect."
        ]
        if skipped
        else []
    )
    return FrozenEvaluationInput(
        entry=entry_id,
        dataset_sha256=_sha256(full_memory),
        arms=arms,
        scored_questions=tuple(scored),
        skipped_questions=tuple(skipped),
        notices=notices,
    )


def _usage_sum(calls: list[EvalCallMetadata]) -> EvalUsage:
    return EvalUsage(
        input_tokens=sum(call.usage.input_tokens for call in calls),
        output_tokens=sum(call.usage.output_tokens for call in calls),
        total_tokens=sum(call.usage.total_tokens for call in calls),
    )


def _metrics(samples: list[EvalSample], eligible: int) -> EvalArmMetrics:
    answer_calls = [sample.answer_call for sample in samples if sample.answer_call]
    judge_calls = [sample.judge_call for sample in samples if sample.judge_call]
    judged = sum(sample.status in ("passed", "failed") for sample in samples)
    passed = sum(sample.passed for sample in samples)
    errors = sum(sample.status in ("answer_error", "judge_error") for sample in samples)
    return EvalArmMetrics(
        eligible=eligible,
        judged=judged,
        passed=passed,
        errors=errors,
        pass_rate=passed / eligible,
        answer_usage=_usage_sum(answer_calls),
        judge_usage=_usage_sum(judge_calls),
        latency_ms=sum(call.latency_ms for call in answer_calls + judge_calls),
    )


async def _run_arm(
    frozen_arm: FrozenArm,
    questions: tuple[ScoredQuestion, ...],
    client: EvaluationClient,
) -> EvalArmResult:
    samples: list[EvalSample] = []
    for item in questions:
        try:
            answer_result = await client.answer(
                question=item.question,
                context=frozen_arm.context,
            )
        except Exception as exc:
            samples.append(
                EvalSample(
                    question_index=item.question_index,
                    question=item.question,
                    expect=item.expect,
                    status="answer_error",
                    error_phase="answer",
                    error_type=type(exc).__name__,
                )
            )
            continue

        try:
            judge_result = await client.judge(
                question=item.question,
                expect=item.expect,
                answer=answer_result.answer,
            )
        except Exception as exc:
            samples.append(
                EvalSample(
                    question_index=item.question_index,
                    question=item.question,
                    expect=item.expect,
                    status="judge_error",
                    answer=answer_result.answer,
                    answer_call=answer_result.call,
                    error_phase="judge",
                    error_type=type(exc).__name__,
                )
            )
            continue

        samples.append(
            EvalSample(
                question_index=item.question_index,
                question=item.question,
                expect=item.expect,
                status="passed" if judge_result.passed else "failed",
                answer=answer_result.answer,
                passed=judge_result.passed,
                judge_reason=judge_result.reason,
                answer_call=answer_result.call,
                judge_call=judge_result.call,
            )
        )

    return EvalArmResult(
        arm=frozen_arm.arm,
        context_sha256=frozen_arm.sha256,
        context_chars=frozen_arm.chars,
        context_estimated_tokens=frozen_arm.estimated_tokens,
        samples=samples,
        metrics=_metrics(samples, len(questions)),
    )


def _pairwise(
    left: EvalArmResult,
    right: EvalArmResult,
) -> EvalPairwiseOutcome:
    left_by_question = {
        sample.question_index: sample
        for sample in left.samples
        if sample.status in ("passed", "failed")
    }
    right_by_question = {
        sample.question_index: sample
        for sample in right.samples
        if sample.status in ("passed", "failed")
    }
    common = sorted(set(left_by_question) & set(right_by_question))
    left_only = right_only = both_passed = both_failed = 0
    for question_index in common:
        left_passed = left_by_question[question_index].passed
        right_passed = right_by_question[question_index].passed
        if left_passed and right_passed:
            both_passed += 1
        elif left_passed:
            left_only += 1
        elif right_passed:
            right_only += 1
        else:
            both_failed += 1
    return EvalPairwiseOutcome(
        left_arm=left.arm,
        right_arm=right.arm,
        comparable=len(common),
        left_only_passed=left_only,
        right_only_passed=right_only,
        both_passed=both_passed,
        both_failed=both_failed,
        pass_rate_delta=left.metrics.pass_rate - right.metrics.pass_rate,
    )


def _ratio_reduction(smaller: int, larger: int) -> float | None:
    if larger <= 0:
        return None
    return (larger - smaller) / larger


def _comparison(arms: list[EvalArmResult]) -> EvalComparison:
    by_name = {arm.arm: arm for arm in arms}
    context = by_name["context_pack"]
    full = by_name["full_memory"]
    none = by_name["no_memory"]
    full_rate = full.metrics.pass_rate
    return EvalComparison(
        context_vs_full=_pairwise(context, full),
        context_vs_no_memory=_pairwise(context, none),
        full_vs_no_memory=_pairwise(full, none),
        context_vs_full_retention=(
            context.metrics.pass_rate / full_rate if full_rate > 0 else None
        ),
        context_chars_saved_vs_full=full.context_chars - context.context_chars,
        context_char_reduction_vs_full=_ratio_reduction(
            context.context_chars,
            full.context_chars,
        ),
        answer_input_tokens_saved_vs_full=(
            full.metrics.answer_usage.input_tokens
            - context.metrics.answer_usage.input_tokens
        ),
        answer_input_token_reduction_vs_full=_ratio_reduction(
            context.metrics.answer_usage.input_tokens,
            full.metrics.answer_usage.input_tokens,
        ),
    )


async def run_evaluation(
    frozen: FrozenEvaluationInput,
    client: EvaluationClient,
    *,
    settings: EvalSettings,
) -> EvalReport:
    """Run all arms and return a privacy-bounded report."""

    arm_results: list[EvalArmResult] = []
    for arm in frozen.arms:
        arm_results.append(
            await _run_arm(arm, frozen.scored_questions, client)
        )

    return EvalReport(
        run_id=f"eval-{uuid4().hex}",
        created_at=datetime.now(timezone.utc).isoformat(),
        entry=frozen.entry,
        dataset_sha256=frozen.dataset_sha256,
        settings=settings,
        skipped_questions=list(frozen.skipped_questions),
        arms=arm_results,
        comparison=_comparison(arm_results),
        notices=list(frozen.notices),
    )
