# CodeMemory Current Sprint

> **Status:** SPRINT COMPLETE — accepted by owner.
> **Sprint:** Personal Memory Phase 2 — Local Semantic Discovery.
> **Branch:** `codex/personal-semantic-discovery`.
> **Depends on:** owner-accepted Eval Harness commit `f002856`.

## Objective

Add an optional local semantic candidate index for Personal Profiles while preserving the hard boundary: semantic search discovers typed entry candidates; canonical imports DAG remains the only build mechanism.

## Contracts

1. Default search remains deterministic lexical/time/tag search and loads no embedding dependency.
2. Semantic discovery requires `profile.discovery.semantic.enabled=true`, a relative local model path under `private_local`, and an explicitly built derived index.
3. The local adapter uses `sentence-transformers` with `local_files_only=True`; no model download or network fallback is allowed.
4. External embeddings remain default false and unsupported in this sprint; setting `external_embeddings=true` is rejected, never silently routed externally.
5. The derived index lives under the ignored `private_local` path, contains typed IDs, hashes, normalized vectors and safe discovery metadata, and never enters Git delivery.
6. Index input includes only valid indexed Capture/Topic/Claim objects and assemblable canonical Atom/Schema content. Corrupt captures and non-assemblable Atoms are excluded.
7. Rebuilding identical input/model is idempotent and performs no embedding call/write. Changed content/model makes the index stale until an explicit rebuild.
8. Semantic results preserve `kind`, stable `id`, `display_locator`, `read_action` (`read` or `build`), score and snippet.
9. `search --semantic` and `search_memories {semantic:true}` only rank candidates. They cannot create imports, inject body into ContextPack, auto-read results, or mutate maintenance/canonical state.
10. Query fails safely when disabled, unconfigured, missing/stale, dimension-mismatched, or unavailable; lexical search remains usable.
11. Embedding vectors/query text are not logged. Index paths are resolved and contained under bound root/private-local.
12. No Web semantic UI, external provider, hybrid reranker, automatic background indexing, or semantic canonical build.

## Deliverables

- [x] Extend the Personal Profile semantic config and validation boundary.
- [x] Add provider-neutral typed semantic index/build/query models with atomic local persistence.
- [x] Add lazy local sentence-transformer adapter and explicit owner CLI index/status operations.
- [x] Add opt-in semantic mode to shared search handler/catalog without changing default results.
- [x] Add stale/idempotency/containment/filter/build-isolation/provider-boundary regression coverage.
- [x] Update PRD, architecture, profile contract, guides, project structure, roadmap and pitfalls.
- [x] Run focused, Core/API, Personal and integration acceptance; restore test side effects.

## Executable Acceptance Criteria

1. Default init/profile has semantic disabled and no model path; lexical search does not import sentence-transformers or create semantic files.
2. Enabled config accepts only a relative model directory inside configured `private_local`; absolute/traversal/outside paths fail validation.
3. Fake local embedder builds typed vectors for valid Capture/Topic/Claim and assemblable Atoms; proposed/archived/corrupt objects are absent.
4. Identical rebuild returns reused with zero embed/write; changed content or model fingerprint is detected stale before query.
5. Semantic query returns stable typed candidates and cosine ordering; kind filters work and missing/dimension-invalid indexes fail boundedly.
6. `search_memories semantic=true` is available only for configured Personal roots; default/standard behavior remains lexical.
7. Tampering semantic index cannot affect `build_context_pack`; no imports or context nodes derive from semantic neighbors.
8. Local adapter is lazy, uses `local_files_only=True`, and makes no network call; external embedding flag is rejected.
9. Index/report contents contain no absolute root/model path or raw query log and stay under ignored private-local.
10. All focused/Core/API/Personal/integration tests and `git diff --check` pass.

## Acceptance Commands

```powershell
python -m pytest tests/personal/test_semantic_discovery.py -q
python -m pytest tests/unit tests/test_api.py -q
python -m pytest tests/personal -q
python tests/integration_test.py
python tests/integration_personal.py
python -c "import sys, codememory; assert 'sentence_transformers' not in sys.modules; print('semantic import boundary ok')"
git diff --check
git status --short --branch -uall
```

## Explicit Deferrals

- External embedding services, model downloads, Web UI, background scheduling and hybrid lexical-semantic fusion.
- Semantic generation of imports, automatic reads, ContextPack injection or maintenance clustering.

## Implementation Evidence

- `python -m pytest tests/personal/test_semantic_discovery.py -q` → 13 passed, including Windows junction escape rejection before embed/write.
- `python -m pytest tests/unit tests/test_api.py -q` → 290 passed, 1 existing Pydantic warning.
- `python -m pytest tests/personal -q` → 55 passed.
- `python tests/integration_test.py` → 21/21 passed.
- `python tests/integration_personal.py` → 15/15 passed.
- Core import probe → `semantic import boundary ok`; `sentence_transformers` remains unloaded.
- `git diff --check` → passed.
- Generated example index/log differences restored; worktree contains only intended Phase 2 changes.
- Owner-review root containment finding fixed: resolved `paths.private_local` must remain inside the bound root before validation, model loading, status, index build, or search.

## Completion Gate

Owner accepted Personal Memory Phase 2 on 2026-07-23 after independently reproducing the junction escape regression, all semantic boundaries, full test suites, import isolation, and diff hygiene. The accepted outcome is recorded in `docs/plan/HISTORY.md`.

Push, merge, and branch cleanup remain separate explicit Git operations.
