"""Explicit, provider-backed evaluation adapter for golden questions.

The package keeps experiment construction and report models provider-neutral.
``gateway_adapter`` is imported only by an explicitly invoked eval handler.
"""

from .models import (
    EvalArmMetrics,
    EvalArmResult,
    EvalCallMetadata,
    EvalComparison,
    EvalReport,
    EvalSample,
    EvalSettings,
    EvalUsage,
)
from .runner import (
    EvaluationClient,
    FrozenEvaluationInput,
    freeze_evaluation_input,
    run_evaluation,
)

__all__ = [
    "EvalArmMetrics",
    "EvalArmResult",
    "EvalCallMetadata",
    "EvalComparison",
    "EvalReport",
    "EvalSample",
    "EvalSettings",
    "EvalUsage",
    "EvaluationClient",
    "FrozenEvaluationInput",
    "freeze_evaluation_input",
    "run_evaluation",
]
