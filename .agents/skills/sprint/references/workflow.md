# Sprint Workflow

Run the repository's standard sprint loop.

## Invocation Contract

Read `docs/plans/SPRINT.md`, implement every unfinished checklist item, run the acceptance commands until they pass, update task status after each iteration, append a record to `docs/plans/HISTORY.md`, and add new pitfalls to `docs/plans/pitfalls.md`.

Default completion signal: `SPRINT COMPLETE`

## Required Context

- Project instructions: `AGENTS.md`
- Long-term sprint source: `docs/plans/FUTURE.md`
- Sprint contract: `docs/plans/SPRINT.md`
- Pitfall knowledge base: `docs/plans/pitfalls.md`

## Materializing A Sprint

If `docs/plans/SPRINT.md` is empty, missing, already complete, or the user asks to start a specific sprint, generate the active sprint contract from `docs/plans/FUTURE.md`.

Use:

```powershell
python .agents/skills/sprint/scripts/materialize_sprint.py --sprint <number>
```

If the user does not specify a sprint:

1. Continue the existing `SPRINT.md` if it has unfinished checklist items.
2. If `SPRINT.md` is empty, materialize Sprint 0.
3. If `SPRINT.md` appears complete, ask which sprint to start next instead of guessing.

The generated `SPRINT.md` is the working contract for the session. Keep it updated as items complete.

## Operating Rules

1. Read `AGENTS.md`, `FUTURE.md`, `SPRINT.md`, and `pitfalls.md` before coding.
2. Work only on unfinished checklist items.
3. After each completed item, update its checkbox in `docs/plans/SPRINT.md`.
4. Run the acceptance commands named by the sprint contract.
5. If the sprint changes file layout or ownership, update `docs/project_structure.md`.
6. At the end, append a concise sprint record to `docs/plans/HISTORY.md`.
7. If new recurring pitfalls were found, append them to `docs/plans/pitfalls.md`.
8. End with `SPRINT COMPLETE` only after acceptance commands pass or unresolved blockers are explicitly recorded.
