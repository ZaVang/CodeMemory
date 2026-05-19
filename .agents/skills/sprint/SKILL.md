---
name: sprint
description: Execute this repository's standard sprint workflow from `docs/plans/SPRINT.md`, or materialize the current sprint from `docs/plans/FUTURE.md` before execution. Use when the user asks to run, start, prepare, materialize, continue, or complete a sprint, or perform the repository's usual sprint loop.
---

# Sprint

## Workflow

1. Read `references/workflow.md`.
2. Read `AGENTS.md`, `docs/plans/FUTURE.md`, `docs/plans/SPRINT.md`, and `docs/plans/pitfalls.md` before making changes.
3. If `docs/plans/SPRINT.md` is empty, missing, complete, or the user asks to start a specific sprint, materialize a sprint from `docs/plans/FUTURE.md` using `scripts/materialize_sprint.py`.
4. Work only on unfinished sprint items.
5. Keep `docs/plans/SPRINT.md` current as items are completed.
6. Run the acceptance commands defined by the sprint contract.
7. Close out with the required `docs/plans/HISTORY.md` and `docs/plans/pitfalls.md` updates.
8. If you need the original wording of the Claude command, read `references/claude-command.md` and preserve the intent while using Codex-native instructions.
