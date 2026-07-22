# CodeMemory Current Sprint

> **Status:** SPRINT COMPLETE — accepted by owner.
> **Sprint:** Importer v2B — Optional LLM Semantic Proposer.
> **Branch:** `codex/importer-v2-llm-proposer`.
> **Depends on:** accepted Importer v2A commit `9193c7f`.
> **Upstream contracts:** `docs/prd.md`, `docs/architecture.md`, `docs/plan/FUTURE.md`.

---

## Start Gate — Open

The owner accepted Importer v2A, authorized its merge/cleanup, and instructed CodeMemory to continue with the next roadmap subitem.

This sprint adds only an explicitly enabled LLM proposer inside the Importer layer. Deterministic `compile-md` remains the default. Core, canonical build, Web, MCP/toolkit expansion, Operator UI, and Personal Memory semantic discovery remain unchanged.

---

## Objective

Allow an owner to explicitly send a registered Markdown corpus to a configured `llm_gateway` model for semantic extraction. The model may propose fewer, reusable Derived Atoms and imports suggestions, but every output remains provenance-bound, reviewable, `status: proposed`, and unable to enter canonical search/build until normal owner merge.

---

## Contracts

1. LLM mode is opt-in only: `compile-md --proposer llm` also requires explicit gateway config and model arguments. No flag, config discovery, environment heuristic, or fallback may enable it.
2. Provider SDKs and `llm_gateway` are imported lazily only on the LLM path. A normal `import codememory` and deterministic compile work without optional provider packages.
3. Source text is sent only to the explicitly configured model. Prompts treat source documents as untrusted data, expose no secrets/config contents, enable no tools/Web, and request typed structured output.
4. The LLM proposes semantic drafts; CodeMemory owns stable paths, proposal IDs, status, provenance, and validation. Model-supplied absolute paths, statuses, source refs, or arbitrary frontmatter are never trusted.
5. Every semantic draft must cite at least one paragraph ID from the current document. Unknown/cross-document provenance drops the draft with a non-sensitive diagnostic.
6. Imports suggestions may target only an explicitly supplied same-document draft key or an indexed existing Atom ID included in the prompt inventory. Unknown targets are dropped and diagnosed; deterministic v2A still emits no imports.
7. Same `review_id` + same source/options returns the existing review without another model call and preserves decisions. Changed source/options conflict before any model call or registry/review replacement.
8. Semantic materialization preflights all accepted proposals before writing: registered source refs, safe/non-existing paths, resolvable imports, and same-batch cycle freedom. Any preflight error writes nothing.
9. Review/materialize acceptance remains separate from canonical acceptance. LLM proposals always materialize as `status: proposed`; owner `merge` remains the only activation path.
10. Review metadata records proposer mode, prompt contract version, requested model, provider/model response identity, and aggregate token usage, but never credentials, gateway config contents/path, raw thinking, or source text beyond the existing review proposal bodies/provenance.

---

## Deliverables

### 1. Provider-neutral semantic proposer

- [x] Add typed semantic draft/import models, prompt construction, stable ID/path mapping, provenance validation, and diagnostics under `src/codememory/compiler/`.
- [x] Generate deterministic anchors plus LLM-derived semantic proposals; do not emit the v2A paragraph-copy derived set in LLM mode.
- [x] Resolve validated same-document and existing-Atom imports suggestions into reviewable proposal imports.
- [x] Record safe proposer/call/usage metadata and a stable source/options digest.

### 2. Optional gateway adapter and CLI

- [x] Add a lazy `llm_gateway` adapter that requests structured output with low-temperature bounded generation and no tools.
- [x] Extend `compile-md` with explicit `--proposer llm --llm-config PATH --llm-model MODEL`; reject incomplete/mixed flag combinations.
- [x] Keep deterministic CLI/API output and imports unchanged when LLM mode is absent.
- [x] Return a clear install/config error when optional provider dependencies are unavailable.

### 3. Idempotency and materialization safety

- [x] Return an existing semantic review without calling the model when source/options match.
- [x] Reject changed source/options under an existing review ID before model invocation or registry/review mutation.
- [x] Preflight all accepted semantic proposals and make validation failure zero-write.
- [x] Reject unknown import targets and same-batch cycles; preserve no-overwrite and `status: proposed` guarantees.

### 4. Documentation and tests

- [x] Update PRD/architecture, USER_GUIDE, INTEGRATION, project structure, and roadmap wording for the delivered opt-in boundary.
- [x] Add fake-bridge tests for prompt safety, semantic quality contract, provenance, imports, usage metadata, retries, and zero-write failure.
- [x] Add CLI tests proving deterministic default, explicit opt-in, missing optional dependency errors, and no live provider/network calls.
- [x] Run all existing Core/API/Personal/integration suites and restore checked-in example side effects.

---

## Executable Acceptance Criteria

1. Deterministic `compile-md` without proposer flags produces byte-equivalent v2A review semantics and makes zero `llm_gateway` imports/calls.
2. LLM mode with a fake bridge receives untrusted-source/system instructions, paragraph IDs/bodies, and a bounded existing-Atom inventory; it receives no credential/config contents and no tools.
3. A five-paragraph document can yield two semantic Derived proposals rather than five paragraph copies; both cite valid source paragraph IDs/ranges and remain pending/proposed.
4. Valid suggestions resolve one same-document dependency and one existing Atom dependency at the declared strength; unknown targets are absent and diagnosed.
5. A draft with missing/foreign paragraph IDs is excluded and cannot reach review materialization.
6. Repeating the same semantic review ID makes no second bridge call and leaves registry/review bytes and decisions unchanged.
7. Source/options changes under the same review ID fail before bridge call and leave registry/review unchanged; a new review ID may call the model and refresh the stable artifact hash.
8. Tampered source refs, unsafe/existing paths, unresolved imports, or same-batch cycles cause semantic materialization to write zero files.
9. Even if review JSON is tampered to `status: active`, accepted semantic proposals materialize as proposed; default search/build excludes them.
10. LLM review metadata contains mode/prompt/model/provider/usage but no API key, config path/body, raw thinking, or unredacted secrets.
11. Missing `--llm-config`/`--llm-model`, missing provider packages, invalid structured output, and gateway failures create no review file and never fall back to deterministic semantic claims.
12. All unit/API/Personal/integration suites pass, optional-dependency boundary grep/import tests pass, `git diff --check` passes, and examples have no residue.

---

## Acceptance Commands

```powershell
python -m pytest tests/unit/test_memory_compiler.py tests/unit/test_importer_llm.py tests/unit/test_sources.py -q
python -m pytest tests/unit tests/test_api.py -q
python -m pytest tests/personal -q
python tests/integration_test.py
python tests/integration_personal.py
python -c "import codememory; print('core import ok')"
git diff --check
git status --short --branch -uall
```

No acceptance command may require a real API key or network provider call.

---

## Explicit Deferrals

- Automatic proposer enablement, config discovery, background/network ingestion, or provider selection.
- Cross-document semantic deduplication and modification proposals for existing Atoms.
- MCP/toolkit importer tools and Operator UI review surfaces.
- Web/PDF/non-Markdown ingestion and Personal Memory semantic discovery.

---

## Completion Gate

Owner review completed on 2026-07-22 with no blocking or actionable findings. The owner independently reproduced the high-risk opt-in, idempotency, provenance/import validation, zero-write materialization, forced-proposed, and Core dependency boundaries and authorized `SPRINT COMPLETE`, acceptance history, commit, and push.
