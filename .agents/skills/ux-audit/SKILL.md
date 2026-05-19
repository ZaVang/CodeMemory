---
name: ux-audit
description: Perform a first-time-user product UX audit and write a structured report. Use when the user asks for a UX audit, product experience review, first-time-user evaluation, or a user-perspective quality review of this repository.
---

# UX Audit

## Workflow

1. Read `references/workflow.md`.
2. Start from `README.md` or `README_CN.md` plus user-facing guide docs.
3. For frontend work, use `scripts/get_page_state.js` to inspect actual rendered state before and after key interactions.
4. Base the report only on observed behavior, not source-level assumptions.
5. Write the final report to `docs/ux-audit-report.md`.
6. If the full legacy report template is needed, read `references/claude-command.md` and reuse the structure while adapting any Claude-only wording.
