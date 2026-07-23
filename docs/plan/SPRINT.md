# CodeMemory Current Sprint

> **Status:** SPRINT COMPLETE — accepted by owner.
> **Sprint:** Eval Harness — ContextPack vs Full Memory vs No Memory.
> **Branch:** `codex/eval-harness`.
> **Depends on:** owner-accepted Documentation and Examples Alignment commit `4efe087`.
> **Upstream contracts:** `docs/prd.md`, `docs/architecture.md`, `docs/plan/FUTURE.md`.

---

## Start Gate — Open

The owner accepted Documentation and Examples Alignment and instructed CodeMemory to continue with the next roadmap item. Roadmap priority 5 is the eval harness.

This sprint turns the existing golden-question export contract into an explicit, provider-backed experiment runner. It does not change canonical build semantics, place provider dependencies in Core, expose evaluation through MCP/Agent tools or Web, add semantic discovery, or start Personal Memory Web.

---

## Objective

Measure whether canonical ContextPack assembly preserves useful answer quality while using less context than a naive full-memory baseline, and whether either memory condition improves over no memory. Produce a reproducible, auditable report without persisting prompts, memory context, provider configuration, credentials, or raw model thinking.

---

## Contracts

1. Core remains provider-free. Golden-question export/build and deterministic baseline construction are provider-neutral; `llm_gateway` is imported only after the owner explicitly invokes `codememory eval` with a complete config/model set.
2. One frozen run evaluates exactly three arms with the same entry, scored questions, answer model, answer prompt, decoding parameters, and independent calls:
   - `context_pack`: the canonical build output for the requested depth/budget;
   - `full_memory`: every assemblable indexed Atom/Schema rendered as stable `id + summary + authored body`, sorted by ID;
   - `no_memory`: an empty memory context.
3. `full_memory` excludes proposed/archived/superseded objects, Capture/Incubator content, Source Artifact bodies, `.codememory/` runtime data, and all frontmatter-only evaluation fields. In particular, `golden_questions.expect` must never enter an answer prompt.
4. Only questions with a non-empty `expect` are scored. Questions without `expect` are reported as skipped; if none are scorable, preflight fails before any provider call.
5. The answer model never receives `expect`. The structured judge receives only question, expected points, and candidate answer; it does not receive arm identity, context, config path, or previous judgments.
6. Answer and judge calls use no tools/Web, temperature 0, bounded output tokens, and the same requested model per role across all arms. Provider/model aliases may differ between answer and judge roles only when explicitly configured.
7. A single answer/judge failure is recorded as a bounded per-sample error and the remaining experiment continues. Error records expose only phase and exception type, not provider payloads or potentially sensitive exception text.
8. The report uses a versioned typed schema and includes dataset/context hashes, safe model metadata, token usage, latency, per-question verdicts, arm pass rates, paired pass deltas, and context-size/token comparisons.
9. Reports do not include memory contexts, prompts, provider config paths, credentials, raw provider responses, or raw thinking. Answers, expected points, and short judge reasons are retained because they are necessary for audit.
10. Runs write no repository state by default. JSON prints to stdout; `--output` performs one atomic final write, rejects an existing path unless `--overwrite` is explicit, and never writes into the memory root implicitly.
11. Preflight freezes all three contexts and their hashes before the first model call. The full-memory dataset digest covers every included ID, summary, and authored body so a report can identify its exact input state without copying the corpus.
12. This sprint exposes only a trusted owner/CI CLI and Python handler. REST, Operator UI, MCP, Toolkit, automation, result history dashboards, repeated-trial statistics, and provider selection UI are deferred.

---

## Deliverables

### 1. Product and architecture contract

- [x] Define the three-arm experiment, anti-leakage boundary, scoring semantics, report privacy, and explicit provider activation in PRD/architecture.
- [x] Define measurable product signals: pass rate, ContextPack-vs-full retention/delta, memory-vs-no-memory uplift, and answer-input token savings.

### 2. Provider-neutral evaluation engine

- [x] Add typed report, arm, sample, call metadata, metrics, and comparison models.
- [x] Add deterministic ContextPack/full-memory/no-memory snapshot construction with hashes and safe containment.
- [x] Add the provider-neutral runner with blind judging, bounded failure continuation, conservative metrics, and no implicit writes.

### 3. Explicit LLM adapter and CLI

- [x] Add a lazy `llm_gateway` evaluation adapter using structured answer/judge output, no tools, temperature 0, and bounded tokens.
- [x] Add `codememory eval <entry>` with required config, answer model, judge model, optional build depth/budget, output path, and explicit overwrite.
- [x] Keep `codememory test` export/report compatibility unchanged and keep eval absent from Agent/MCP/REST surfaces.

### 4. Verification and documentation

- [x] Add regression tests for arm isolation, no expected-answer leakage, status filtering, stable ordering/hashes, blind judge input, partial failures, metrics, output safety, CLI flag gates, and lazy provider imports.
- [x] Update README, USER_GUIDE, INTEGRATION, project structure, and roadmap status without presenting live provider execution as a default/offline path.
- [x] Run focused, Core/API, Personal, existing integration, Personal integration, import-boundary, and diff hygiene acceptance.

---

## Executable Acceptance Criteria

1. A deterministic fixture with one target, imported dependencies, unrelated active Atom, proposed/archived Atoms, a Source Artifact, Capture/Topic data, and golden expectations produces:
   - ContextPack containing only the canonical DAG result;
   - full-memory containing every and only assemblable Atom/Schema body in sorted-ID order;
   - no-memory with empty context;
   - no answer prompt containing any `expect` value.
2. With a fake answer/judge client, each scorable question produces exactly three independent answer calls and three blind judge calls; arm labels/context never enter judge input.
3. Missing `expect` questions are skipped without calls. An entry with no scored question fails before client construction/calls and writes no report.
4. Answer or judge failure in one arm records only phase/error type, continues other samples, and counts conservatively against that arm's eligible denominator.
5. Metrics exactly report eligible, judged, passed, errors, pass rate, safe usage totals, latency, context size, ContextPack-vs-full pass delta/retention, uplift over no-memory, and answer-input token savings.
6. Identical frozen input produces identical dataset/context hashes and ordering. Changing any included body/summary changes the full-memory dataset digest.
7. Report JSON contains no root/config absolute path, prompt, context body, credential marker, raw response, or thinking field; it retains answers/expected points/judge reasons.
8. `codememory eval` without any one of `--llm-config`, `--answer-model`, or `--judge-model` exits before provider import/call. Ordinary Core import and all non-eval CLI paths do not load `llm_gateway`.
9. `--output` refuses pre-existing files before calls; successful output is atomic. `--overwrite` must be explicit and only replaces the exact resolved target.
10. Existing `codememory test`, read/build/search, Agent tool catalog, REST golden-question endpoint, importer, and Personal Profile behavior remain unchanged.
11. Focused eval tests, all unit/API/Personal/integration suites, provider import-boundary checks, and `git diff --check` pass with no example/runtime residue.

---

## Acceptance Commands

```powershell
python -m pytest tests/unit/test_eval_harness.py tests/unit/test_golden_questions.py -q
python -m pytest tests/unit tests/test_api.py -q
python -m pytest tests/personal -q
python tests/integration_test.py
python tests/integration_personal.py
python -c "import sys, codememory; assert 'llm_gateway' not in sys.modules; print('core import ok')"
python -c "from codememory.agent_tools import standard_tool_specs; assert all(t.name != 'eval_memory' for t in standard_tool_specs()); print('agent boundary ok')"
git diff --check
git status --short --branch -uall
```

No live provider/network call is required for acceptance.

---

## Explicit Deferrals

- Repeated trials, confidence intervals, statistical significance, benchmark scheduling, or CI provider secrets.
- Operator UI / REST evaluation execution, report dashboards, dataset comparison UI, or remote result storage.
- MCP/Toolkit/Agent evaluation tools.
- Semantic discovery, embeddings, Personal Memory Web, Web/PDF ingestion, or importer review UI.
- Source Artifact full-text baseline or automatic source expansion.

---

## Completion Gate

Implementation completed on 2026-07-23. The provider-neutral engine freezes three isolated contexts before the first call, strips evaluation frontmatter from full-memory, fixes ContextPack generation metadata for stable hashes, uses blind structured judging, continues bounded per-sample failures, and emits privacy-bounded `memory-eval/v1` metrics. The explicit CLI lazily loads `llm_gateway`; no Agent/MCP/REST surface was added.

Acceptance evidence:

- focused eval + golden-question suite: `17 passed`;
- Core/API: `290 passed` with one existing Pydantic deprecation warning;
- Personal Profile: `42 passed`;
- existing integration: `21/21 passed`;
- Personal integration: `15/15 passed`;
- Core import did not load `llm_gateway`; standard Agent catalog contains no eval tool;
- `git diff --check` passed;
- generated companion/investment index and investment log side effects were restored.

Owner accepted the Eval Harness sprint on 2026-07-23 after independently rechecking full-memory answer-key isolation, blind answer/judge inputs, lazy provider loading, adapter-surface exclusion, report privacy, no-clobber atomic output, fake-client privacy probes, all regression suites, and diff hygiene. The accepted outcome is recorded in `docs/plan/HISTORY.md`.

Push, merge, and branch cleanup remain separate explicit Git operations.
