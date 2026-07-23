# CodeMemory Current Sprint

> **Status:** SPRINT COMPLETE — accepted by owner.
> **Sprint:** Operator UI Alignment — Build, Review Queue, and Golden Questions.
> **Branch:** `codex/operator-ui-alignment`.
> **Depends on:** accepted MCP / Toolkit alignment commit `e6577e4`.
> **Upstream contracts:** `docs/prd.md`, `docs/architecture.md`, `docs/plan/FUTURE.md`.

---

## Start Gate — Open

The owner accepted MCP / Toolkit alignment, authorized its completion commit/push, and instructed CodeMemory to start the next roadmap item. Roadmap priority 3 is Operator UI alignment.

This sprint aligns the existing FastAPI adapter and React operator UI with already-accepted Core contracts. It does not add Personal Memory Web, arbitrary instance browsing, importer review UI, semantic discovery, Web/PDF ingestion, or a new design system.

---

## Objective

Make the local operator UI accurately expose the current memory-as-code workflow: canonical `build` output, an owner review queue for proposed Atoms and modification patches, and read-only golden questions. Remove UI behavior tied to deleted intensity / stability / decay / wander semantics while preserving graph, list, dashboard, edit, validate, reindex, dataset switching, and source-safe Core boundaries.

---

## Contracts

1. `backend/` remains a REST adapter. Build, merge/reject, test export, create/update, search, validate, and reindex must delegate to existing Core/handler behavior rather than reimplement canonical semantics in React or routers.
2. `POST /api/build` is the primary UI assembly endpoint and returns both the structured ContextPack and the requested rendered output. The UI must stop calling `/api/resolve`; compatibility REST aliases may remain but cannot have separate assembly logic.
3. `GET /api/reviews` returns two explicit queues: proposed Atoms and modification patch proposals. Queue items must expose kind, stable ID/target, summary/reason, created metadata, and patch fields without modifying targets.
4. Owner review actions are explicit, kind-specific merge/reject calls. Atom merge activates proposed → active; Atom reject archives it; patch merge applies through Core update/version/change log; patch reject deletes only the patch record.
5. `GET /api/tests/{memory_id}` exports the existing golden-question TestBundle. The UI displays questions, optional expectations, notices, and context availability read-only; it does not run an LLM, judge answers, or fabricate pass/fail results.
6. Operator create writes complete summary/body/imports through one Core create call and may explicitly choose active or proposed. Owner edit uses canonical update semantics and cannot revive removed intensity/stability fields.
7. Frontend/API types, forms, graph sizing, search/list/detail/dashboard/help copy contain no active intensity, stability, decay, wander, or touch behavior. Maturity remains because it is still canonical metadata.
8. Proposed/archived/superseded status remains visible in operator inventory and graph, but only assemblable targets can build. Errors from non-buildable targets and invalid review actions are bounded and leave bytes unchanged.
9. Every request stays scoped by the existing dataset alias header. This sprint does not accept absolute roots or add a production instance registry; examples discovery remains the development/demo boundary.
10. No new frontend or Python runtime dependency is introduced. Existing responsive layout, themes, keyboard behavior, dataset switching, graph/list/dashboard flows, and API compatibility tests remain green.

---

## Deliverables

### 1. REST operator contract

- [x] Add primary structured `/api/build` backed by the unified build pipeline.
- [x] Add typed review-queue list and kind-specific merge/reject endpoints.
- [x] Add golden-question TestBundle export endpoint.
- [x] Route complete create/update through Core and remove stale touch/decay adapter behavior.

### 2. Operator review and build UI

- [x] Add a Review view showing proposed Atoms and modification patch proposals with explicit merge/reject confirmation and refresh behavior.
- [x] Rename the UI assembly workflow from Resolve to Build and consume structured ContextPack plus rendered output.
- [x] Display status/provenance-relevant proposal details without exposing hidden filesystem paths.
- [x] Show golden questions and optional expectations in Memory Detail without executing or judging them.

### 3. Legacy UI cleanup

- [x] Remove intensity/stability/decay/wander/touch fields, controls, calculations, API calls, and help text.
- [x] Replace intensity-based graph sizing with canonical graph metadata such as dependent count and fixed bounded sizes.
- [x] Keep maturity/status/tags/imports/source metadata and existing owner edit/archive behavior intact.

### 4. Documentation and verification

- [x] Add API regression tests for build parity, review queue/actions, golden questions, complete create, and bounded failure paths.
- [x] Add frontend build/Playwright coverage for Build, Review, and legacy-control absence.
- [x] Update PRD/architecture only where adapter status needs clarification; update USER_GUIDE, project structure, roadmap, and UI help text.
- [x] Run all Core/API/Personal/integration/frontend acceptance commands and restore checked-in example side effects.

---

## Executable Acceptance Criteria

1. `POST /api/build` returns a structured pack and rendered output from the same pipeline; for the same request its rendered content matches Core `render_context_pack` and contains no proposed target.
2. `GET /api/reviews` distinguishes proposed Atoms from patch proposals and reports stable IDs, targets, patch fields, and a correct total without changing files or index state.
3. Merging/rejecting each review kind produces the accepted Core state transition; invalid kind/ID/status returns a bounded 4xx and leaves target/proposal bytes unchanged.
4. `GET /api/tests/{id}` returns the declared golden questions, optional expectations, assembled context, and empty-question notice exactly from the Core TestBundle.
5. Operator create sends complete summary/body/imports once, supports explicit proposed status, and does not perform a post-create direct file rewrite.
6. The UI has a visible Review view with separate proposed-Atom and patch sections, empty/loading/error states, confirmation before action, and refresh after successful merge/reject.
7. Memory Detail uses Build terminology/output and exposes golden questions; Graph/List navigation still opens the same memory and non-buildable status errors are understandable.
8. Frontend production code has no `fetchWander`, `WanderResponse`, `touchMemory`, intensity/stability/decay UI calculations, or `/api/resolve` call. Graph size remains bounded and deterministic.
9. Dashboard validate/reindex/stats, dataset switching, create/edit/archive, search, graph, list, themes, and keyboard shortcuts remain functional.
10. `npm run build`, `npm run lint`, Playwright smoke, all Python unit/API/Personal/integration suites, and `git diff --check` pass; example fixtures have no residue.

---

## Acceptance Commands

```powershell
python -m pytest tests/unit tests/test_api.py -q
python -m pytest tests/personal -q
python tests/integration_test.py
python tests/integration_personal.py
Set-Location frontend
npm run build
npm run lint
npm run test:e2e:ci
Set-Location ..
rg -n "fetchWander|WanderResponse|touchMemory|intensity|stability|decay|/api/resolve" frontend/src
git diff --check
git status --short --branch -uall
```

The legacy-term grep must return no production frontend matches (exit code 1).

---

## Explicit Deferrals

- Personal Memory Web instance registry, Capture/Incubator browsing, provenance timeline, and batch Topic review.
- Importer/compiler review-set UI and LLM proposer configuration.
- Golden-question execution, answer judging, report submission, eval harness, or provider calls.
- Web/PDF/non-Markdown ingestion, semantic discovery, external embeddings, and arbitrary filesystem roots.
- Visual redesign, framework migration, dependency upgrades, and production authentication/authorization.

---

## Completion Gate

Owner review completed on 2026-07-23 with no remaining blocking findings. The owner independently rechecked dataset-root containment and Core search delegation, reproduced the former absolute-path header escape as a bounded 400 with no outside writes, ran the complete Python/frontend/integration acceptance set, restored generated example side effects, and authorized `SPRINT COMPLETE`, accepted HISTORY, commit, push, merge, and branch cleanup.
