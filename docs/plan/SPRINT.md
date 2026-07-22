# CodeMemory Current Sprint

> **Status:** SPRINT COMPLETE — accepted by owner.
> **Sprint:** Adapter Alignment — Shared MCP / Toolkit Agent Surface.
> **Branch:** `codex/mcp-toolkit-alignment`.
> **Depends on:** accepted Importer v2B commit `b1744b3`.
> **Upstream contracts:** `docs/prd.md`, `docs/architecture.md`, `docs/plan/FUTURE.md`.

---

## Start Gate — Open

The owner accepted Importer v2B, authorized its completion commit/push, and instructed CodeMemory to continue with the next roadmap item. Roadmap priority 2 is MCP / toolkit alignment.

This sprint only aligns agent adapters with existing shared handlers. It does not expose importer/owner operations, add Web/UI work, change canonical build semantics, or start Personal Memory semantic discovery.

---

## Objective

Give MCP and `CodememoryToolkit` one shared, root-bound agent-tool contract. A standard instance exposes the five canonical agent operations `build / search / expand_source / create / propose`; a Personal Profile adds only the already-accepted capture/read/maintenance/review extension. All calls delegate to shared handlers and preserve canonical proposal gates.

---

## Contracts

1. Tool definitions and dispatch live in one provider-neutral module consumed by both Sandbox/Toolkit and MCP; neither adapter may reimplement operation logic.
2. A standard root exposes exactly: `build_memory`, `search_memories`, `expand_source`, `create_memory`, and `propose_memory`.
3. A Personal Profile adds exactly: `capture_memory`, `read_memory`, `maintenance_status`, `maintain_memory`, `resume_memory_maintenance`, and `review_personal_memory`.
4. Toolkit instances and MCP processes bind one explicit resolved root. Exported schemas never contain `root`; caller-supplied root values are ignored/rejected and cannot redirect a write.
5. `build_memory`, `search_memories`, and `expand_source` delegate to `handle_build`, `handle_search`, and `handle_source_expand` with equivalent arguments and machine-readable results.
6. `create_memory` creates a complete new Atom in one Core write. Standard roots may create active low-risk Atoms or explicitly proposed Atoms; Personal Profile agent creation is always forced to proposed unless an owner uses the trusted CLI confirmation path.
7. `propose_memory` means a modification proposal against an existing Atom and delegates to `handle_propose`; it must never update target bytes before owner merge.
8. Legacy agent aliases (`resolve_context`, `update_memory`, `validate_memories`, `snapshot`, `find_orphans`, `changelog`, `log`, `import_memories`, MCP `resolve_memory`, `propose_update`) are removed from exported agent surfaces. Their owner CLI/Core capabilities remain unchanged.
9. Personal maintenance/review tools retain Phase 1B single-run, provenance, scan-blocked, and root-binding contracts; this sprint only shares their adapter definitions/dispatch.
10. MCP JSON-RPC errors remain bounded and tool calls never expose Python tracebacks, filesystem rerouting, or hidden owner operations.

---

## Deliverables

### 1. Shared agent-tool contract

- [x] Add one typed/shared tool-definition catalog with standard and Personal extension profiles.
- [x] Add one root-bound dispatcher that delegates every tool to the existing handler facade.
- [x] Include read-only annotations and provider-neutral JSON Schema once, then adapt it mechanically for MCP/OpenAI/Anthropic/Gemini.

### 2. Safe create / propose semantics

- [x] Extend Core creation to accept complete summary/body content atomically while preserving existing CLI defaults.
- [x] Force Personal Profile agent-created Atoms to proposed; keep trusted CLI owner-confirmation paths unchanged.
- [x] Route modification proposals through `handle_propose` and prove target bytes remain unchanged until merge.

### 3. Toolkit and MCP convergence

- [x] Make `CodememoryToolkit` export/register only the root-appropriate shared definitions.
- [x] Make MCP `tools/list` and `tools/call` use the same root-appropriate catalog and dispatcher.
- [x] Remove duplicated/unsafe legacy adapter implementations and add `expand_source` to both surfaces.

### 4. Documentation and tests

- [x] Update architecture/PRD, INTEGRATION, README, project structure, and roadmap wording for exact standard/Personal surfaces.
- [x] Add parity, root-binding, complete-create, proposal-no-mutation, source expansion, and MCP JSON-RPC tests.
- [x] Update integration tests to the aligned names without weakening existing Core behavior coverage.
- [x] Run all Core/API/Personal/integration suites and restore checked-in example side effects.

---

## Executable Acceptance Criteria

1. Standard Toolkit exports and MCP `tools/list` contain the same exact five names and equivalent schemas/read-only annotations.
2. A Personal root exports the same five plus the same exact six Personal extension names in Toolkit and MCP.
3. OpenAI, Anthropic, Gemini, Sandbox, and MCP schemas contain no `root`; forged `root` values and escaped IDs (`..`, backslash, drive, or absolute forms) cannot redirect create/capture/propose writes.
4. `expand_source` returns the same structured payload through shared dispatch, Toolkit Sandbox, and MCP for fresh/stale/missing sources.
5. Standard `create_memory` writes supplied summary/body/imports in one creation, reindexes once, and honors explicit active/proposed status.
6. Personal `create_memory` cannot create an active Atom through any agent adapter; the created Atom is proposed and excluded from default search/build.
7. `propose_memory` creates a patch-queue record for an existing Atom; target bytes/index semantics are unchanged until owner `merge`.
8. No exported adapter contains legacy direct-update/import/validation/snapshot/log tools, while the corresponding CLI commands still work.
9. MCP without `CODEMEMORY_ROOT` fails before serving; invalid roots and unknown tools return bounded errors.
10. Existing Personal capture/read/maintenance/review integration behavior remains green through the shared dispatcher.
11. All unit/API/Personal/integration suites pass, `git diff --check` passes, and example fixtures have no residue.

---

## Acceptance Commands

```powershell
python -m pytest tests/unit/test_agent_tool_alignment.py tests/unit/test_source_expand.py tests/unit/test_create_update.py -q
python -m pytest tests/unit tests/test_api.py -q
python -m pytest tests/personal -q
python tests/integration_test.py
python tests/integration_personal.py
git diff --check
git status --short --branch -uall
```

---

## Explicit Deferrals

- Importer/compiler tools in MCP or Toolkit.
- Owner-only validate/test/merge/reject/source-registry administration tools.
- Operator UI, instance allowlist registry, Web/PDF ingestion, or semantic discovery.
- Backward-compatible aliases for the removed legacy agent-tool names.

---

## Completion Gate

Owner review completed on 2026-07-22 with no remaining blocking or actionable findings. The owner independently reproduced the adapter surface, root binding, proposal gates, and all reported path-escape forms, confirmed valid nested Chinese IDs remain contained, and authorized `SPRINT COMPLETE`, accepted HISTORY, commit, and push.
