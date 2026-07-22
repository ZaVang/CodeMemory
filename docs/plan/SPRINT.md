# CodeMemory Current Sprint

> **Status:** SPRINT COMPLETE — accepted by owner.
> **Sprint:** Personal Memory Phase 1B — Codex Maintenance + Git Delivery.
> **Depends on:** accepted Phase 1A commit `136c78c`.
> **Upstream contracts:** `docs/prd.md`, `docs/architecture.md`, `docs/personal-memory-profile.md`.

---

## Start Gate — Open

The owner accepted Phase 1A and explicitly authorized Phase 1B after the accepted branch was committed and pushed. Phase 1B begins on its own branch.

Web UI and semantic discovery remain out of scope. External embeddings remain disabled.

---

## Objective

Add an idempotent Codex-driven maintenance workflow on top of the deterministic Phase 1A substrate: consume every valid unprocessed Capture, upsert provenance-rich Incubator Topics, gate canonical promotion through owner confirmation, and safely deliver accepted local changes through Git without ever blocking Capture.

---

## Deliverables

### 1. Maintenance run ledger and recovery

- [x] Add maintenance run models, append-only `runs.jsonl`, local state, pending changeset, stage transitions, and stable input digest.
- [x] Discover all complete hash-valid Captures not consumed by an `applied` run, including missed-run catch-up across dates.
- [x] Ensure the same input digest returns the existing applied run and never duplicates Topic changes, consumption, or commits.
- [x] Persist before/after hashes and resume an interrupted apply from the same pending changeset without regenerating it.
- [x] Enforce one active run; `scan_blocked` blocks new maintenance and Git delivery while Capture remains available.
- [x] Resume the same blocked run after owner repair, then catch up Captures added during the block in a later run.
- [x] Keep all maintenance state out of journal Markdown.

### 2. Personal Memory Codex Skill and Topic upsert

- [x] Add a repository Personal Memory Codex Skill covering capture judgment, optional follow-up, active reading, synthesis, provenance, claim blocks, and owner-facing review behavior.
- [x] Keep “record only” low-friction; only enter interview mode when the owner explicitly requests continued questioning or a critical ambiguity blocks the requested result.
- [x] Generate one monthly incubator Markdown and deterministically upsert one section per `topic_id + revision_id`.
- [x] Preserve stable Topic/revision IDs, paragraph-level `derived_from`, `origin: mixed`, and stable inline `claim_id` blocks without creating claim Markdown files.
- [x] Repeated maintenance over equivalent input must update the existing Topic section rather than duplicate it.

### 3. Canonical promotion and batch review

- [x] Default Agent-created canonical Atoms to proposed and exclude them from default search/build.
- [x] Treat an explicit owner instruction to create a formal idea as confirmation.
- [x] Support batch promote, merge, and delete decisions for Incubator review.
- [x] Preserve Capture/Topic revision hashes and owner confirmation in Atom provenance.
- [x] Activate promoted Atoms only after owner confirmation; existing imports DAG remains the only canonical build path.

### 4. Sensitive scan and Git delivery

- [x] Scan the staged delivery diff for sensitive values before commit without echoing secret contents.
- [x] On a hit, enter `scan_blocked`, notify the owner with rule/path/object locator only, and create no commit or push.
- [x] Stage only Profile-declared tracked paths; reject unknown changes outside those paths and never stage `paths.private_local` or ignored runtime state.
- [x] Auto-commit only when explicitly enabled, with one unique `CodeMemory-Run: <run_id>` trailer.
- [x] Auto-push only when explicitly enabled; failed push preserves the same commit and retries without creating another commit.
- [x] Avoid a second dirty commit caused only by updating committed/pushed runtime state.
- [x] Document that private GitHub is not encrypted storage and deleted raw records may remain in Git history.

### 5. Automation, adapters, documentation, and tests

- [x] Add shared handlers and CLI/toolkit entry points for maintenance status/run/resume and review decisions without exposing arbitrary roots.
- [x] Define the Automation invocation contract and concise success/failure/blocked owner notifications.
- [x] Update USER_GUIDE, INTEGRATION, architecture, profile contract, and project structure.
- [x] Add unit coverage for maintenance, promotion, Git delivery, Skill behavior, and every idempotency/recovery boundary.
- [x] Extend disposable integration coverage; never touch production MyMemory and restore all checked-in example side effects.

---

## Executable Acceptance Criteria

1. Construct three days of Captures, skip two scheduled runs, then maintain: every unconsumed valid Capture is consumed exactly once in deterministic order.
2. Run the same input twice: the second call returns the existing applied run; incubator diff, Topic count, and Git commit count remain unchanged.
3. Simulate process exit during apply; restart uses the same pending changeset and reaches identical after hashes without regenerating the changeset.
4. Equivalent input maps to the same `topic_id + revision_id` and updates one section; a month still has one incubator Markdown.
5. Agent promotion creates a proposed Atom invisible to default build; explicit owner confirmation activates it with complete provenance.
6. One review batch can promote, merge, and delete multiple Topics; routine Topic updates do not create per-item proposals.
7. Inject a test token: sensitive scan enters `scan_blocked`, does not reveal the token, and performs no commit/push. Capture continues; the same run resumes after repair; later maintenance catches up blocked-period Captures.
8. A temporary bare remote proves auto commit/push; an intentionally failed first push retries the same commit without increasing commit count.
9. Every delivery commit has exactly one `CodeMemory-Run: <run_id>` trailer; repeated runner calls do not duplicate commits.
10. The configured `paths.private_local` is ignored; a pre-tracked configured private path fails validation.
11. Skill tests prove record-only does not question, explicit “continue asking” enters interview mode, and no critical gap means no interruption.
12. Updating committed/pushed state does not create a second dirty commit; delivery status is reconstructible from trailers and the remote ref.
13. Unknown changes outside Profile-declared paths block auto commit; private/runtime paths are never staged.
14. Topic may be `origin: mixed`; inference uses a stable inline claim block and does not create another Markdown file.
15. All unit/API/integration acceptance passes with no example or temporary repository residue.

---

## Acceptance Commands

```powershell
python -m pytest tests/unit tests/test_api.py -q
python -m pytest tests/personal/test_maintenance.py tests/personal/test_promotion.py tests/personal/test_git_delivery.py -q
python tests/integration_personal.py
rg -n -i "openai.*embedding|external_embeddings.*true" src/codememory
git diff --check
git status --short --branch -uall
```

Expected embedding grep result: no matches (exit code 1 is success).

---

## Explicit Deferrals

- Local semantic index and all external embedding integrations.
- Personal Memory Web UI and arbitrary external-instance browsing.
- Full Markdown editor or Obsidian replacement behavior.

---

## Completion Signal

`SPRINT COMPLETE`
