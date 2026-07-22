# CodeMemory Current Sprint

> **Status:** Complete — Phase 1A accepted by owner on 2026-07-22.
> **Sprint:** Personal Memory Phase 1A — Instance, Capture, Typed Discovery.
> **Upstream contracts:** `docs/prd.md`, `docs/architecture.md`, `docs/personal-memory-profile.md`

---

## Start Gate — Open

The owner accepted the Phase 0 contracts after clarifying optional Git delivery, single-run `scan_blocked`, and claim-level status. Phase 1A implementation is authorized.

Phase 1B is a separate subsequent sprint defined in `docs/plan/FUTURE.md`. It must not be pulled into 1A.

---

## Objective

Deliver the deterministic substrate that lets a dedicated Codex task initialize and safely append to an external Personal Profile, then discover and read Capture / Incubator Topic / Canonical Atom objects without allowing non-canonical content into build.

No LLM, clustering, maintenance, Git automation, semantic index, Web UI, or production MyMemory data migration belongs in Phase 1A.

---

## Deliverables

### 1. Profile and external instance

- [x] Add Personal Profile manifest models and validation.
- [x] Add `codememory init <path> --profile personal` without overwriting existing content.
- [x] Create/validate `journal/`, `incubator/`, `memory/`, `reviews/`, `private-local/`, and `.codememory/` layout.
- [x] Ensure root `.gitignore` contains `private-local/`, maintenance `state.json`, and `pending/`; fail validation if `private-local/` is already tracked.
- [x] Keep CodeMemory repo and instance root independent; no hard-coded `D:\work\MyMemory` in runtime code.
- [x] Keep non-Git directories valid; default `auto_commit=false` / `auto_push=false`, and report Git delivery as optional availability rather than a Capture prerequisite.

### 2. Capture

- [x] Add `codememory capture` with text argument and stdin input.
- [x] Generate globally unique, time-sortable `cap_<ULID>` IDs.
- [x] Compute per-Capture SHA-256 using the normalization contract in `docs/personal-memory-profile.md`.
- [x] Append a complete block under an instance-level lock, flush + fsync before success, and return the ID/hash/path.
- [x] Parse complete Capture blocks and report incomplete trailing blocks without consuming them.
- [x] Provide no Agent-facing update/delete operation for Capture; owner cleanup remains an explicit manual/owner surface.

### 3. Typed index and discovery

- [x] Extend indexing to discriminate `capture`, `incubator_topic`, and `atom`.
- [x] Parse stable Topic metadata from monthly incubator sections without treating the whole monthly file as an Atom.
- [x] Preserve nested claim blocks while parsing Topic boundaries; claim-level indexing remains explicitly deferred to Phase 1B.
- [x] Return typed search results with `kind`, stable ID, path, display locator, summary/snippet, metadata, and `read_action`.
- [x] Support lexical query, time range, tags, kind, topic/project/person, origin, and claim_status filters where metadata exists.
- [x] Add `read` by stable Capture ID or Topic revision ID; line numbers are display-only.
- [x] Route Atom candidates to build and Capture/Topic candidates to read; reject build on non-Atom IDs with a clear error.
- [x] Preserve existing Atom search/build behavior for non-personal datasets.

### 4. Adapters and documentation

- [x] Route init/capture/typed search/read through shared handlers.
- [x] Expose the minimum dedicated-task surface in CLI and toolkit/MCP: capture, search, read, build.
- [x] Bind each MCP process/toolkit instance to one explicit root; no arbitrary root supplied per untrusted tool call.
- [x] Update USER_GUIDE / INTEGRATION / project_structure and provide a generated MyMemory README security notice.
- [x] Keep Web external-instance work deferred; document its server-side allowlist contract only.

### 5. Tests

- [x] Unit tests cover profile validation, Capture format/hash/parser/locking, typed index, filters, read routing, and build rejection.
- [x] Integration test uses a temporary external Git repo, never `D:\work\MyMemory` or checked-in examples.
- [x] Regression tests prove existing Atom CLI/API/build/search contracts remain green.
- [x] Tests verify `private-local/` ignore and tracked-path failure.

---

## Executable Acceptance Criteria

1. Initialize a non-repo temporary directory and an already-initialized temporary Git repo; both produce the same valid Personal Profile layout without overwriting a pre-existing README.
2. Capture three inputs on one date: exactly one journal Markdown exists, it has three complete unique blocks, and each reported hash matches only its payload.
3. Reopen and reindex the instance: all three Capture IDs are unchanged and readable; no line number is stored as identity.
4. Append an intentionally incomplete trailing block: validation reports it, search/read exclude it, and the previous complete Capture remains intact.
5. Add two Topic sections to one monthly incubator file and one Canonical Atom: typed search returns all three kinds with correct `read_action`.
6. Time/kind/tag/origin filters and Atom-level claim_status filters return deterministic results; Topic claim blocks are preserved but not independently indexed in 1A. Lexical query does not require embeddings or network.
7. `build <capture-id>` and `build <topic-revision-id>` fail clearly; `build <atom-id>` succeeds through the existing imports pipeline.
8. Run init a second time and capture/index repeatedly: no duplicate directories, metadata blocks, IDs, or index entries appear.
9. `private-local/` and maintenance runtime state are ignored by default; a fixture with `private-local/` pre-tracked fails profile validation.
10. A non-Git profile initializes and captures successfully with `git_delivery=unavailable`; a Git repo without remote also captures successfully. Defaults remain auto_commit/auto_push false.
11. Search the implementation for `D:\work\MyMemory` and external embedding calls: both are absent.
12. Existing unit/API suite and the new personal integration suite pass; `git diff --check` is clean and checked-in example data is unchanged.

---

## Acceptance Commands

These commands are the required target; implementation may add narrower commands but may not remove them:

```powershell
python -m pytest tests/unit tests/test_api.py -q
python -m pytest tests/personal/test_profile.py tests/personal/test_capture.py tests/personal/test_discovery.py -q
python tests/integration_personal.py
rg -n -F "D:\work\MyMemory" src backend frontend -g "*.py" -g "*.ts" -g "*.tsx"
rg -n -i "openai.*embedding|external_embeddings.*true" src/codememory
git diff --check
git status --short --branch -uall
```

Expected grep result for the two forbidden-pattern commands: no matches (exit code 1 is success for those checks).

---

## Explicit Deferrals to Phase 1B+

- Codex semantic classification, grill-style follow-up, clustering and synthesis.
- Daily maintenance ledger, changeset apply/recovery and missed-run catch-up.
- Incubator Topic automatic upsert/merge and canonical promotion review.
- Sensitive diff scan, Git commit/push, retry and notifications.
- Local semantic discovery and every external embedding integration.
- Web UI external-instance browsing or review workflows.

---

## Completion Signal

`SPRINT COMPLETE` — implementation, automated acceptance, and owner review are complete. Phase 1B remains closed.
