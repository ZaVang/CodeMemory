---
name: multi-ralph
description: Run this repository's planner -> generator -> evaluator sprint loop. Use when the user asks for multi-ralph, a bounded multi-agent sprint loop, planner/generator/evaluator orchestration, or iterative sprint execution with independent verification.
---

# Multi Ralph

## Workflow

1. Read `references/workflow.md`.
2. Read `AGENTS.md`, `docs/plans/SPRINT.md`, and `docs/plans/pitfalls.md`.
3. Preserve the planner -> generator -> evaluator separation and the shared-file protocol.
4. Use Codex subagents only when the user has explicitly asked for delegation or parallel agent work; otherwise keep the same staged workflow within one thread.
5. Stop on `COMPLETE`, continue on `CONTINUE`, and report blockers on `BLOCKED`.
6. When the detailed role prompts or report templates matter, read `references/claude-command.md` and adapt them to Codex rather than reproducing Claude-specific syntax verbatim.

## Legacy Script

- `scripts/multi-agent-ralph.sh` is preserved from the Claude workflow for reference only.
- Treat it as historical guidance, not as the default execution path inside Codex.
