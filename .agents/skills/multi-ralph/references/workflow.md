# Multi-Ralph Workflow

Run a bounded planner -> generator -> evaluator loop for the current sprint.

## Shared Files

| File | Purpose |
| --- | --- |
| `docs/plans/SPRINT.md` | Sprint contract and acceptance commands |
| `docs/plans/pitfalls.md` | Shared pitfall knowledge |
| `docs/orch/plan.md` | Planner output |
| `docs/orch/gen_status.md` | Generator handoff |
| `docs/orch/eval.md` | Evaluator report and next-iteration feedback |

## Loop

1. Ensure `docs/orch/` exists.
2. Read `docs/plans/SPRINT.md`.
3. Stop early if there are no unfinished checklist items.
4. For each iteration, run these roles strictly in order:
   - Planner: identify unfinished work, read relevant pitfalls, and write `docs/orch/plan.md`.
   - Generator: implement the plan, update checklist items, run acceptance commands, and write `docs/orch/gen_status.md`.
   - Evaluator: independently rerun acceptance commands, compare against the generator report, and write `docs/orch/eval.md`.
5. Continue, complete, or stop as blocked based on the evaluator decision.
6. Append newly discovered pitfalls to `docs/plans/pitfalls.md` before ending.

## Codex Adaptation

- Prefer Codex subagents when the user explicitly asks for delegated or parallel agent work.
- If subagents are not being used, preserve the same planner -> generator -> evaluator separation within one thread and keep the shared-file protocol intact.
- Do not rely on Claude-specific `Task` invocation syntax or `$ARGUMENTS`; translate requested options into ordinary instructions.
