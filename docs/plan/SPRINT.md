# CodeMemory Current Sprint

> **Status:** SPRINT COMPLETE — accepted by owner.
> **Sprint:** Personal Memory Web — Allowlisted Owner Workspace.
> **Branch:** `codex/personal-memory-web`.
> **Depends on:** owner-accepted Personal Memory Phase 2 commit `501e74a`.

## Objective

Extend the existing local Operator UI with a safe Personal workspace for allowlisted external Personal Profiles: browse Capture and Incubator content, prepare one explicit owner batch review, and inspect provenance-rich idea evolution without turning the product into a general filesystem browser or full Markdown editor.

## Contracts

1. External instances enter Web only through a server-owned YAML registry path configured by `CODEMEMORY_INSTANCE_REGISTRY`; request payloads and headers never contain roots.
2. Registry aliases are exact safe identifiers. Invalid/duplicate aliases, relative roots, missing roots, non-Personal roots, and profile-invalid roots fail closed. Existing contained `examples/` discovery remains developer/demo compatibility only.
3. The resolver maps an exact known alias to its prevalidated resolved root. Absolute paths, traversal, separators, whitespace variants, unknown aliases, and alias collisions are rejected before request ContextVar mutation.
4. Dataset responses expose only safe metadata (`name`, `memory_count`, `profile`, `source`), never absolute root, registry path, profile contents, Git remote, model path, or private-local data.
5. External registry roots are not automatically reindexed or mutated during server startup. Reindex remains an explicit owner action.
6. Personal REST operations exist only for valid Personal roots and delegate to provider-neutral Core models/handlers. Routers perform validation/status mapping only; they do not parse Markdown, reconstruct provenance, or implement review semantics.
7. Capture browsing returns only complete hash-valid Capture records in stable reverse chronological order with bounded pagination. It cannot edit/delete Capture.
8. Incubator browsing returns Topic revisions and inline Claims with stable IDs, origin, claim status, provenance and safe locators. It does not expose absolute paths or private-local/runtime files.
9. Timeline uses authored timestamps plus explicit `derived_from`, `relations`, `merged_from`, and promotion provenance. It does not invent semantic links or treat line numbers as identity.
10. Concentrated review submits one owner-confirmed batch of existing `promote | merge | delete` actions through `handle_review_batch`. The UI previews the complete batch and requires explicit confirmation; no action runs on selection alone.
11. The Personal page is advertised only for Personal datasets. Standard demo roots retain existing Graph/List/Dashboard/Review behavior and exact Agent/MCP surfaces.
12. The UI is a browsing/review workspace, not a full editor, Obsidian replacement, raw file browser, semantic-vector viewer, maintenance runner, Git control panel, or authentication system.
13. No endpoint exposes semantic index vectors/query logs, Git credentials/remotes, maintenance pending changesets, raw registry configuration, or arbitrary file content.
14. REST/API and UI remain local-owner surfaces. Production authentication, multi-user authorization, remote hosting and arbitrary cross-machine access are deferred.

## Deliverables

- [x] Add typed server-owned instance registry loading, exact alias resolution and safe dataset metadata.
- [x] Add provider-neutral Personal Web overview/capture/topic/timeline models and handlers.
- [x] Add a thin Personal REST router with bounded reads and owner batch review.
- [x] Add a Personal Operator UI view for Capture browsing, Topic/Claim inspection, batch decisions and timeline.
- [x] Add registry/root/privacy, valid-object filtering, timeline and review-delegation regression coverage.
- [x] Add frontend mocked E2E coverage for Personal-only navigation, browsing and confirmed batch review.
- [x] Update PRD, architecture, guides, project structure, frontend help and roadmap/pitfalls.
- [x] Run backend/Core/Personal/integration/frontend acceptance and restore test side effects.

## Executable Acceptance Criteria

1. A temporary registry maps `mymemory` to an external valid Personal Profile; `/api/datasets` lists it without an absolute path and exact header requests resolve to that root.
2. Absolute/traversal/separator/whitespace/unknown aliases and duplicate registry/demo aliases return bounded errors and never create or modify files outside an allowlisted root.
3. Relative/missing/non-Personal/profile-invalid registry roots are excluded or fail startup/config loading with no fallback to path interpretation.
4. Server startup does not reindex or change bytes in external registry roots.
5. Personal overview/capture/topic/timeline endpoints reject standard roots and return typed, stable, path-safe objects for Personal roots.
6. Malformed/hash-invalid Capture and invalid Topic/Claim blocks are absent from Web results while diagnostics remain bounded.
7. Timeline order and edges derive only from explicit timestamps/provenance/relations; stable IDs survive path/line changes.
8. One REST review batch calls the shared Core handler once; promote/merge/delete outcomes match CLI behavior. Invalid/self-referential actions fail without router-side writes.
9. Frontend shows Personal navigation only for Personal datasets, supports empty/loading/error states, and does not regress Graph/List/Dashboard/Review for standard roots.
10. Owner can select multiple Topic decisions, review the full batch, cancel with zero calls, then explicitly confirm one batch call and refresh results.
11. UI/API payloads contain no absolute root, registry path, private-local path, semantic vectors, credentials, Git remote or maintenance pending state.
12. Core/API/Personal/integration/frontend build/lint/E2E and `git diff --check` pass with no example/runtime residue.

## Acceptance Commands

```powershell
python -m pytest tests/unit/test_personal_web.py tests/test_api.py -q
python -m pytest tests/unit tests/test_api.py -q
python -m pytest tests/personal -q
python tests/integration_test.py
python tests/integration_personal.py
Push-Location frontend; npm run build; npm run lint; npm run test:e2e:ci; Pop-Location
git diff --check
git status --short --branch -uall
```

## Explicit Deferrals

- Authentication, multiple owners/roles, remote hosting, registry editing through Web and arbitrary root entry.
- Capture editing/deletion, full Markdown editing, maintenance execution, Git delivery controls and semantic index management.
- Automatic relationship inference, semantic timeline clustering and background Web refresh.

## Completion Gate

Owner acceptance was recorded on 2026-07-23 after independent boundary review and the complete acceptance matrix passed. This sprint is closed; no follow-up implementation is implied by this status.
