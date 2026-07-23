# CodeMemory Current Sprint

> **Status:** SPRINT COMPLETE — accepted by owner.
> **Sprint:** Documentation and Examples Alignment.
> **Branch:** `codex/docs-examples-alignment`.
> **Depends on:** accepted Operator UI alignment commit `a0f89b5`.
> **Upstream contracts:** `docs/prd.md`, `docs/architecture.md`, `docs/personal-memory-profile.md`.

---

## Start Gate — Open

The owner accepted and merged Operator UI alignment, cleaned all previous branches, and instructed CodeMemory to continue with the next roadmap item. Roadmap priority 4 is documentation and examples alignment.

This sprint reconciles user-facing documentation, integration guidance, repository maps, and checked-in example roots with already-accepted behavior. It does not change canonical Core semantics or begin the eval harness, Personal Memory Web, semantic discovery, Web/PDF ingestion, or provider work.

---

## Objective

Make every primary onboarding and integration path runnable from a clean checkout with current memory-as-code terminology: `build` as the primary read path, the exact root-bound agent tool catalog, proposal/review gates, source-aware importer flow, current REST operator surface, and examples free of removed heat metadata.

---

## Contracts

1. Product and architecture truth remain in PRD/architecture/profile contracts; this sprint documents accepted behavior and does not invent new semantics.
2. `docs/INTEGRATION.md` must be a current integration guide, not a legacy guide with a stale-warning banner. Removed focus/overview/wander, intensity/stability/decay, and removed agent aliases cannot appear as active instructions.
3. `build` is the primary canonical assembly verb. `resolve` and `context-pack` may be documented only as compatibility CLI/API aliases that share the build pipeline.
4. Agent examples expose the exact standard five-tool root-bound surface. Tool payloads contain no `root`; creation is complete in one write; modification uses `propose_memory`; no removed aliases are invoked.
5. Example execution must not mutate checked-in datasets. Writable demonstrations use an isolated temporary copy or disposable root and clean up automatically.
6. Example Atom/Schema frontmatter uses only current model fields. Removed `intensity`, `stability`, `stability_source`, and `days_since_last_access` keys are forbidden; prose must not teach heat/decay semantics.
7. Checked-in example indexes are regenerated from source Markdown after metadata cleanup, and each registered example dataset must validate without errors.
8. `docs/project_structure.md`, README, USER_GUIDE, agent-facing quick references, and example descriptions must identify current module/file ownership and current command/tool names.
9. Historical `docs/reference/`, accepted HISTORY, superseded roadmap notes, and architecture migration records may retain legacy vocabulary when clearly historical; regression checks target active guidance and examples.
10. No runtime dependency, public API, Core behavior, frontend behavior, or example dataset alias is added or renamed in this sprint.

---

## Deliverables

### 1. Primary documentation

- [x] Rewrite `docs/INTEGRATION.md` around current CLI, Python, MCP/Toolkit, REST, importer, and Personal Profile contracts.
- [x] Align README and USER_GUIDE quick paths on `build`, exact proposal gates, and current feature status.
- [x] Correct `docs/project_structure.md` and agent quick references where removed modules/commands are still presented as current.

### 2. Runnable examples

- [x] Rewrite `examples/example_agent.py` to use the root-bound five-tool surface with complete create and canonical build in a disposable root.
- [x] Remove obsolete heat/decay frontmatter and prose from every example dataset without changing stable IDs/import graphs.
- [x] Regenerate checked-in indexes and validate investment, companion, and software-architecture datasets.

### 3. Drift prevention

- [x] Add focused tests for current example metadata, current agent example tool names/payloads, and primary-guide legacy-instruction absence.
- [x] Add or reuse a local Markdown link check for primary documentation.
- [x] Run the complete docs/examples acceptance set and restore any generated example side effects not intentionally part of this sprint.

---

## Executable Acceptance Criteria

1. A new user can follow README and INTEGRATION quick starts using `reindex → validate → search → build` against `examples/investment` without an obsolete command or field.
2. Primary integration docs accurately list the five standard agent tools and six Personal extensions, state explicit root binding, and contain no agent payload `root` parameter.
3. `PYTHONPATH=src python examples/example_agent.py` exits 0, registers exactly the standard five tools, calls only current names, performs complete create/build in a temporary root, and leaves `examples/` byte-clean.
4. No Markdown under active example datasets has frontmatter keys `intensity`, `stability`, `stability_source`, or `days_since_last_access`; the no-leverage prose uses canonical protected/constraint language instead of a numeric heat score.
5. `reindex` followed by `validate` succeeds for investment, companion, and software-architecture; regenerated indexes contain no removed heat fields.
6. `docs/project_structure.md` does not claim deleted `context_pack.py` exists and maps build, REST review, importer, agent tools, and Personal modules to their actual files.
7. Primary guides contain no active instructions for focus/overview/wander, `create --intensity`, decay warnings, or removed agent aliases. Clearly labeled compatibility/history tables are allowed.
8. Focused drift tests, all Python unit/API/Personal/integration suites, Markdown link checks, and `git diff --check` pass; generated logs or unrelated example state are absent.

---

## Acceptance Commands

```powershell
python -m pytest tests/unit/test_docs_examples.py -q
python -m pytest tests/unit tests/test_api.py -q
python -m pytest tests/personal -q
python tests/integration_test.py
python tests/integration_personal.py
$env:PYTHONPATH = "src"
python examples/example_agent.py
Remove-Item Env:PYTHONPATH
python -m codememory.cli --root examples/investment reindex
python -m codememory.cli --root examples/investment validate
python -m codememory.cli --root examples/companion reindex
python -m codememory.cli --root examples/companion validate
python -m codememory.cli --root examples/software-architecture reindex
python -m codememory.cli --root examples/software-architecture validate
rg -n "^(intensity|stability|stability_source|days_since_last_access):" examples
git diff --check
git status --short --branch -uall
```

The removed-field grep must return no matches (exit code 1). Reindex changes are intentional only where they reflect the cleaned example Markdown; log/test side effects must be restored.

---

## Explicit Deferrals

- Eval harness and provider-backed golden-question execution/judging.
- Personal Memory Phase 2 semantic discovery or external embeddings.
- Personal Memory Web, production instance registry, authentication, or provenance timeline UI.
- Importer review UI, Web/PDF/non-Markdown ingestion, dependency upgrades, or visual redesign.
- Renaming compatibility CLI/API aliases or example dataset directory aliases.

---

## Completion Gate

Implementation completed on 2026-07-23 with focused drift checks `7 passed`, Core/API `278 passed` (one existing Pydantic warning), Personal `42 passed`, existing integration `21/21`, and Personal integration `15/15`. Owner-review follow-up removed the remaining active Agent-guide bypass: new Agent Atoms now use complete one-write `create_memory`, every existing-Atom change (including source binding) uses a modification proposal, Scenario D uses `codememory propose`, and status-only lifecycle is explicitly owner-only because it is outside the patch schema. The runnable Agent example registered exactly five tools and completed in a disposable root. Investment and companion validate with zero warnings; software-architecture has zero errors and four existing maturity-review warnings. Generated test log/index side effects were restored, the three intentional indexes were regenerated from the pre-test runtime baseline, removed-field grep has no matches, and `git diff --check` passes.

Owner accepted the Documentation and Examples Alignment sprint on 2026-07-23 after independently re-running the focused documentation/example checks, Core/API and Personal suites, Personal integration, the five-tool Agent example, removed-field grep, and `git diff --check`. The accepted outcome is recorded in `docs/plan/HISTORY.md`.

Commit, push, merge, and branch cleanup remain separate explicit Git operations.
