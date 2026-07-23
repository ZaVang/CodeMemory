"""Typed ``memory-eval/v1`` report models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


EvalArmName = Literal["context_pack", "full_memory", "no_memory"]
EvalSampleStatus = Literal["passed", "failed", "answer_error", "judge_error"]


class EvalUsage(BaseModel):
    """Safe, normalized token counters for one or more calls."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class EvalCallMetadata(BaseModel):
    """Provider metadata that is safe to retain in a report."""

    requested_model: str
    provider: str = ""
    response_model: str = ""
    usage: EvalUsage = Field(default_factory=EvalUsage)
    latency_ms: int = 0


class EvalSample(BaseModel):
    """One arm's answer and blind-judge outcome for a scored question."""

    question_index: int
    question: str
    expect: str
    status: EvalSampleStatus
    answer: str | None = None
    passed: bool = False
    judge_reason: str | None = None
    answer_call: EvalCallMetadata | None = None
    judge_call: EvalCallMetadata | None = None
    error_phase: Literal["answer", "judge"] | None = None
    error_type: str | None = None


class EvalArmMetrics(BaseModel):
    """Conservative metrics: provider errors stay in the eligible denominator."""

    eligible: int
    judged: int
    passed: int
    errors: int
    pass_rate: float
    answer_usage: EvalUsage = Field(default_factory=EvalUsage)
    judge_usage: EvalUsage = Field(default_factory=EvalUsage)
    latency_ms: int = 0


class EvalArmResult(BaseModel):
    """All results and safe context metadata for one experiment arm."""

    arm: EvalArmName
    context_sha256: str
    context_chars: int
    context_estimated_tokens: int
    samples: list[EvalSample] = Field(default_factory=list)
    metrics: EvalArmMetrics


class EvalPairwiseOutcome(BaseModel):
    """Blind-judge paired outcomes where both arms produced a verdict."""

    left_arm: EvalArmName
    right_arm: EvalArmName
    comparable: int
    left_only_passed: int
    right_only_passed: int
    both_passed: int
    both_failed: int
    pass_rate_delta: float


class EvalComparison(BaseModel):
    """Primary product signals derived from the three arms."""

    context_vs_full: EvalPairwiseOutcome
    context_vs_no_memory: EvalPairwiseOutcome
    full_vs_no_memory: EvalPairwiseOutcome
    context_vs_full_retention: float | None = None
    context_chars_saved_vs_full: int
    context_char_reduction_vs_full: float | None = None
    answer_input_tokens_saved_vs_full: int
    answer_input_token_reduction_vs_full: float | None = None


class EvalSettings(BaseModel):
    """Frozen experiment settings; paths and credentials are deliberately absent."""

    depth: Literal["required", "recommended", "full"]
    budget: int | None = Field(default=None, gt=0)
    answer_model: str
    judge_model: str
    answer_max_tokens: int = Field(gt=0)
    judge_max_tokens: int = Field(gt=0)
    temperature: float = 0.0
    seed: int = 0
    prompt_version: str = "memory-eval-prompt/v1"
    arm_order: list[EvalArmName] = Field(
        default_factory=lambda: ["context_pack", "full_memory", "no_memory"]
    )


class EvalSkippedQuestion(BaseModel):
    """A declared golden question that has no scoreable expectation."""

    question_index: int
    question: str
    reason: str = "missing_expect"


class EvalReport(BaseModel):
    """Versioned, auditable report with no copied memory context or prompts."""

    format_version: str = "memory-eval/v1"
    run_id: str
    created_at: str
    entry: str
    dataset_sha256: str
    settings: EvalSettings
    skipped_questions: list[EvalSkippedQuestion] = Field(default_factory=list)
    arms: list[EvalArmResult]
    comparison: EvalComparison
    notices: list[str] = Field(default_factory=list)


class EvalAnswerPayload(BaseModel):
    """Structured answer requested from the answer model."""

    answer: str = Field(min_length=1)


class EvalJudgePayload(BaseModel):
    """Structured, arm-blind verdict requested from the judge model."""

    passed: bool
    reason: str = Field(min_length=1, max_length=500)


class EvalAnswerResult(BaseModel):
    """Provider-neutral answer client result."""

    answer: str
    call: EvalCallMetadata


class EvalJudgeResult(BaseModel):
    """Provider-neutral judge client result."""

    passed: bool
    reason: str
    call: EvalCallMetadata
