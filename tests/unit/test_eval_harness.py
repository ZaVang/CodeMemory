"""Eval harness: three frozen arms, blind judging, and safe reports."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from codememory.evaluation.models import (
    EvalAnswerPayload,
    EvalAnswerResult,
    EvalCallMetadata,
    EvalJudgePayload,
    EvalJudgeResult,
    EvalSettings,
    EvalUsage,
)
from codememory.evaluation.runner import (
    build_full_memory_context,
    freeze_evaluation_input,
    run_evaluation,
)
from codememory.handlers import handle_eval
from codememory.index import get_index_path, reindex


def _write_memory(
    root: Path,
    memory_id: str,
    *,
    body: str,
    summary: str | None = None,
    type_: str = "atom",
    status: str = "active",
    imports: str = "",
    golden: str = "",
) -> Path:
    path = root / f"{memory_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        f"type: {type_}\n"
        f"id: {memory_id}\n"
        f"summary: {summary or memory_id + ' summary'}\n"
        f"status: {status}\n"
        "version: 1\n"
        "tags: [eval-fixture]\n"
        f"{imports}"
        f"{golden}"
        "---\n\n"
        f"{body}\n",
        encoding="utf-8",
    )
    return path


def _fixture_root(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "memory"
    entry = "user/entry"
    golden = (
        "golden_questions:\n"
        '  - q: "What is the durable answer?"\n'
        '    expect: "EXPECTED-POINT-ONLY"\n'
        '  - q: "This question has no rubric"\n'
    )
    imports = (
        "imports:\n"
        "  required:\n"
        "    - id: user/dep\n"
    )
    _write_memory(
        root,
        entry,
        body="TARGET-BODY durable answer",
        imports=imports,
        golden=golden,
    )
    _write_memory(root, "user/dep", body="DEPENDENCY-BODY")
    _write_memory(root, "user/unrelated", body="UNRELATED-ACTIVE-BODY")
    _write_memory(root, "schemas/decision", type_="schema", body="SCHEMA-BODY")
    _write_memory(
        root,
        "user/proposed",
        status="proposed",
        body="PROPOSED-SECRET-BODY",
    )
    _write_memory(
        root,
        "user/archived",
        status="archived",
        body="ARCHIVED-SECRET-BODY",
    )
    (root / "data").mkdir(parents=True)
    (root / "data" / "source.txt").write_text(
        "SOURCE-ARTIFACT-BODY",
        encoding="utf-8",
    )
    (root / "journal").mkdir(parents=True)
    (root / "journal" / "2026-07-23.md").write_text(
        "CAPTURE-PRIVATE-BODY",
        encoding="utf-8",
    )
    (root / "incubator").mkdir(parents=True)
    (root / "incubator" / "2026-07.md").write_text(
        "TOPIC-PRIVATE-BODY",
        encoding="utf-8",
    )
    reindex(root)
    return root, entry


def _call_metadata(
    requested_model: str,
    *,
    input_tokens: int,
    latency_ms: int = 5,
) -> EvalCallMetadata:
    return EvalCallMetadata(
        requested_model=requested_model,
        provider="fake",
        response_model="fake-response-model",
        usage=EvalUsage(
            input_tokens=input_tokens,
            output_tokens=3,
            total_tokens=input_tokens + 3,
        ),
        latency_ms=latency_ms,
    )


class FakeEvaluationClient:
    def __init__(
        self,
        *,
        fail_answer_marker: str | None = None,
        fail_judge_answer: str | None = None,
    ) -> None:
        self.answer_calls: list[dict[str, str]] = []
        self.judge_calls: list[dict[str, str]] = []
        self.fail_answer_marker = fail_answer_marker
        self.fail_judge_answer = fail_judge_answer

    async def answer(self, *, question: str, context: str) -> EvalAnswerResult:
        self.answer_calls.append({"question": question, "context": context})
        if self.fail_answer_marker and self.fail_answer_marker in context:
            raise RuntimeError("DO-NOT-LEAK-PROVIDER-ERROR")
        if "<codememory_full_memory" in context:
            answer = "full-answer"
        elif "<codememory_context_pack" in context:
            answer = "context-answer"
        else:
            answer = "no-memory-answer"
        return EvalAnswerResult(
            answer=answer,
            call=_call_metadata("fake-answer", input_tokens=len(context) + 10),
        )

    async def judge(
        self,
        *,
        question: str,
        expect: str,
        answer: str,
    ) -> EvalJudgeResult:
        self.judge_calls.append(
            {"question": question, "expect": expect, "answer": answer}
        )
        if self.fail_judge_answer == answer:
            raise LookupError("DO-NOT-LEAK-JUDGE-ERROR")
        passed = answer in ("context-answer", "full-answer")
        return EvalJudgeResult(
            passed=passed,
            reason="meets expected points" if passed else "missing expected points",
            call=_call_metadata("fake-judge", input_tokens=20),
        )


def _settings() -> EvalSettings:
    return EvalSettings(
        depth="recommended",
        budget=5000,
        answer_model="fake-answer",
        judge_model="fake-judge",
        answer_max_tokens=128,
        judge_max_tokens=64,
    )


def test_freezes_three_isolated_arms_without_expected_answer_leak(tmp_path: Path):
    root, entry = _fixture_root(tmp_path)

    frozen = freeze_evaluation_input(root, entry, budget=5000)
    by_arm = {arm.arm: arm for arm in frozen.arms}
    context = by_arm["context_pack"].context
    full = by_arm["full_memory"].context

    assert tuple(by_arm) == ("context_pack", "full_memory", "no_memory")
    assert "TARGET-BODY" in context
    assert "DEPENDENCY-BODY" in context
    assert "UNRELATED-ACTIVE-BODY" not in context
    assert "UNRELATED-ACTIVE-BODY" in full
    assert "SCHEMA-BODY" in full
    for forbidden in (
        "EXPECTED-POINT-ONLY",
        "PROPOSED-SECRET-BODY",
        "ARCHIVED-SECRET-BODY",
        "SOURCE-ARTIFACT-BODY",
        "CAPTURE-PRIVATE-BODY",
        "TOPIC-PRIVATE-BODY",
        "golden_questions",
    ):
        assert forbidden not in context
        assert forbidden not in full
    assert by_arm["no_memory"].context == ""
    assert len(frozen.scored_questions) == 1
    assert len(frozen.skipped_questions) == 1

    id_positions = [
        full.index('id="schemas/decision"'),
        full.index('id="user/dep"'),
        full.index('id="user/entry"'),
        full.index('id="user/unrelated"'),
    ]
    assert id_positions == sorted(id_positions)


def test_hashes_are_stable_and_track_full_memory_changes(tmp_path: Path):
    root, entry = _fixture_root(tmp_path)
    before = freeze_evaluation_input(root, entry, budget=5000)
    repeated = freeze_evaluation_input(root, entry, budget=5000)

    assert before.dataset_sha256 == repeated.dataset_sha256
    assert [arm.sha256 for arm in before.arms] == [
        arm.sha256 for arm in repeated.arms
    ]

    unrelated = root / "user" / "unrelated.md"
    unrelated.write_text(
        unrelated.read_text(encoding="utf-8").replace(
            "UNRELATED-ACTIVE-BODY",
            "UNRELATED-CHANGED-BODY",
        ),
        encoding="utf-8",
    )
    reindex(root)
    changed = freeze_evaluation_input(root, entry, budget=5000)
    before_by_arm = {arm.arm: arm.sha256 for arm in before.arms}
    changed_by_arm = {arm.arm: arm.sha256 for arm in changed.arms}

    assert changed.dataset_sha256 != before.dataset_sha256
    assert changed_by_arm["full_memory"] != before_by_arm["full_memory"]
    assert changed_by_arm["context_pack"] == before_by_arm["context_pack"]
    assert changed_by_arm["no_memory"] == before_by_arm["no_memory"]


def test_full_memory_rejects_forged_index_path_escape(tmp_path: Path):
    root, _entry = _fixture_root(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    index_path = get_index_path(root)
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["memories"]["user/unrelated"]["path"] = "../outside.md"
    index_path.write_text(json.dumps(index), encoding="utf-8")

    with pytest.raises(ValueError, match="escapes the bound memory root"):
        build_full_memory_context(root)


def test_runner_calls_three_answers_and_blind_judges_and_computes_metrics(tmp_path: Path):
    root, entry = _fixture_root(tmp_path)
    frozen = freeze_evaluation_input(root, entry, budget=5000)
    client = FakeEvaluationClient()

    report = asyncio.run(run_evaluation(frozen, client, settings=_settings()))

    assert len(client.answer_calls) == 3
    assert len(client.judge_calls) == 3
    assert all("EXPECTED-POINT-ONLY" not in call["context"] for call in client.answer_calls)
    assert all(set(call) == {"question", "expect", "answer"} for call in client.judge_calls)
    assert all("context" not in call and "arm" not in call for call in client.judge_calls)

    arms = {arm.arm: arm for arm in report.arms}
    assert arms["context_pack"].metrics.pass_rate == 1.0
    assert arms["full_memory"].metrics.pass_rate == 1.0
    assert arms["no_memory"].metrics.pass_rate == 0.0
    assert report.comparison.context_vs_full.pass_rate_delta == 0.0
    assert report.comparison.context_vs_full_retention == 1.0
    assert report.comparison.context_vs_no_memory.left_only_passed == 1
    assert report.comparison.context_chars_saved_vs_full == (
        arms["full_memory"].context_chars - arms["context_pack"].context_chars
    )
    assert report.comparison.answer_input_tokens_saved_vs_full == (
        arms["full_memory"].metrics.answer_usage.input_tokens
        - arms["context_pack"].metrics.answer_usage.input_tokens
    )
    assert report.skipped_questions[0].reason == "missing_expect"


@pytest.mark.parametrize(
    ("client", "expected_status", "expected_type"),
    [
        (
            FakeEvaluationClient(fail_answer_marker="<codememory_full_memory"),
            "answer_error",
            "RuntimeError",
        ),
        (
            FakeEvaluationClient(fail_judge_answer="context-answer"),
            "judge_error",
            "LookupError",
        ),
    ],
)
def test_partial_failures_continue_and_do_not_leak_exception_text(
    tmp_path: Path,
    client: FakeEvaluationClient,
    expected_status: str,
    expected_type: str,
):
    root, entry = _fixture_root(tmp_path)
    frozen = freeze_evaluation_input(root, entry, budget=5000)

    report = asyncio.run(run_evaluation(frozen, client, settings=_settings()))
    serialized = report.model_dump_json()
    failed_samples = [
        sample
        for arm in report.arms
        for sample in arm.samples
        if sample.status == expected_status
    ]

    assert len(failed_samples) == 1
    assert failed_samples[0].error_type == expected_type
    assert "DO-NOT-LEAK" not in serialized
    assert sum(arm.metrics.eligible for arm in report.arms) == 3
    assert sum(arm.metrics.errors for arm in report.arms) == 1
    assert len(client.answer_calls) == 3


def test_no_scorable_question_fails_before_any_call(tmp_path: Path):
    root = tmp_path / "memory"
    _write_memory(
        root,
        "user/entry",
        body="BODY",
        golden='golden_questions:\n  - q: "No rubric"\n',
    )
    reindex(root)
    client = FakeEvaluationClient()

    with pytest.raises(ValueError, match="No scorable golden questions"):
        asyncio.run(
            handle_eval(
                root,
                "user/entry",
                config_path="unused.yaml",
                answer_model="fake-answer",
                judge_model="fake-judge",
                client=client,
            )
        )
    assert client.answer_calls == []
    assert client.judge_calls == []


def test_report_privacy_and_output_no_clobber_are_pre_call(tmp_path: Path):
    root, entry = _fixture_root(tmp_path)
    output = tmp_path / "report.json"
    client = FakeEvaluationClient()

    summary = asyncio.run(
        handle_eval(
            root,
            entry,
            config_path="SECRET-CONFIG-PATH.yaml",
            answer_model="fake-answer",
            judge_model="fake-judge",
            budget=5000,
            output=str(output),
            client=client,
        )
    )
    report_text = output.read_text(encoding="utf-8")
    report = json.loads(report_text)

    assert "Evaluation report written:" in summary
    assert report["format_version"] == "memory-eval/v1"
    for forbidden in (
        str(root),
        "SECRET-CONFIG-PATH",
        "TARGET-BODY",
        "DEPENDENCY-BODY",
        "UNRELATED-ACTIVE-BODY",
        "memory_context",
        "system_prompt",
        "thinking",
    ):
        assert forbidden not in report_text
    assert "context-answer" in report_text
    assert "EXPECTED-POINT-ONLY" in report_text

    second_client = FakeEvaluationClient()
    with pytest.raises(FileExistsError, match="--overwrite"):
        asyncio.run(
            handle_eval(
                root,
                entry,
                config_path="unused.yaml",
                answer_model="fake-answer",
                judge_model="fake-judge",
                budget=5000,
                output=str(output),
                client=second_client,
            )
        )
    assert second_client.answer_calls == []

    overwrite_client = FakeEvaluationClient()
    asyncio.run(
        handle_eval(
            root,
            entry,
            config_path="unused.yaml",
            answer_model="fake-answer",
            judge_model="fake-judge",
            budget=5000,
            output=str(output),
            overwrite=True,
            client=overwrite_client,
        )
    )
    assert len(overwrite_client.answer_calls) == 3
    assert not list(tmp_path.glob(".report.json.*.tmp"))


def test_gateway_adapter_uses_structured_tool_free_prompts_and_blind_judge():
    from codememory.evaluation.gateway_adapter import LLMGatewayEvaluationClient

    class FakeBridge:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        async def chat(self, **kwargs):
            self.calls.append(kwargs)
            response_model = kwargs["response_model"]
            parsed = (
                EvalAnswerPayload(answer="candidate")
                if response_model is EvalAnswerPayload
                else EvalJudgePayload(passed=True, reason="matches")
            )
            return SimpleNamespace(
                parsed=parsed,
                provider="fake",
                model="fake-model",
                model_id="provider-response-id",
                usage=SimpleNamespace(
                    input_tokens=11,
                    output_tokens=4,
                    total_tokens=15,
                ),
            )

    bridge = FakeBridge()
    client = LLMGatewayEvaluationClient(
        bridge,
        answer_model="answer",
        judge_model="judge",
        answer_max_tokens=100,
        judge_max_tokens=50,
        params_factory=lambda **kwargs: kwargs,
    )
    asyncio.run(client.answer(question="Q", context="PRIVATE-CONTEXT"))
    asyncio.run(client.judge(question="Q", expect="EXPECTED", answer="candidate"))

    answer_call, judge_call = bridge.calls
    answer_payload = json.loads(answer_call["messages"][0]["content"])
    judge_payload = json.loads(judge_call["messages"][0]["content"])
    assert answer_payload == {
        "question": "Q",
        "memory_context": "PRIVATE-CONTEXT",
    }
    assert "EXPECTED" not in answer_call["messages"][0]["content"]
    assert judge_payload == {
        "question": "Q",
        "expected_points": "EXPECTED",
        "candidate_answer": "candidate",
    }
    assert "PRIVATE-CONTEXT" not in judge_call["messages"][0]["content"]
    assert "arm" not in judge_call["messages"][0]["content"]
    assert "tools" not in answer_call and "tools" not in judge_call
    assert answer_call["params"] == {
        "system_prompt": answer_call["params"]["system_prompt"],
        "temperature": 0.0,
        "seed": 0,
        "max_tokens": 100,
    }
    assert judge_call["params"]["max_tokens"] == 50


def test_cli_requires_all_explicit_eval_flags_before_dispatch(monkeypatch, tmp_path: Path):
    import codememory.cli as cli

    with pytest.raises(SystemExit):
        cli.main(["--root", str(tmp_path), "eval", "user/entry"])
    with pytest.raises(SystemExit):
        cli.main(
            [
                "--root",
                str(tmp_path),
                "eval",
                "user/entry",
                "--llm-config",
                "gateway.yaml",
                "--answer-model",
                "answer",
            ]
        )

    seen: dict = {}

    async def fake_handler(*args, **kwargs):
        seen.update(kwargs)
        return '{"format_version":"memory-eval/v1"}'

    monkeypatch.setattr(cli, "handle_eval", fake_handler)
    cli.main(
        [
            "--root",
            str(tmp_path),
            "eval",
            "user/entry",
            "--llm-config",
            "gateway.yaml",
            "--answer-model",
            "answer",
            "--judge-model",
            "judge",
        ]
    )
    assert seen["config_path"] == "gateway.yaml"
    assert seen["answer_model"] == "answer"
    assert seen["judge_model"] == "judge"


def test_missing_optional_provider_dependency_writes_no_report(
    tmp_path: Path,
    monkeypatch,
):
    root, entry = _fixture_root(tmp_path)
    config = tmp_path / "gateway.yaml"
    output = tmp_path / "should-not-exist.json"
    config.write_text("models: {}\n", encoding="utf-8")
    monkeypatch.setitem(sys.modules, "llm_gateway", None)

    with pytest.raises(RuntimeError, match=r"codememory\[llm\]"):
        asyncio.run(
            handle_eval(
                root,
                entry,
                config_path=str(config),
                answer_model="answer",
                judge_model="judge",
                budget=5000,
                output=str(output),
            )
        )
    assert not output.exists()
    assert not list(tmp_path.glob(".should-not-exist.json.*.tmp"))


def test_core_import_and_agent_catalog_do_not_load_or_expose_eval_provider():
    script = (
        "import sys, codememory; "
        "from codememory.agent_tools import standard_tool_specs; "
        "assert 'llm_gateway' not in sys.modules; "
        "assert all(tool.name != 'eval_memory' for tool in standard_tool_specs()); "
        "print('eval boundary ok')"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "eval boundary ok" in result.stdout
