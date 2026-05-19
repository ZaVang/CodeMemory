# UX Audit Workflow

Perform a first-time-user UX audit from the perspective of a domain expert who has no prior product knowledge.

## Core Method

1. Read user-facing documentation first.
2. Experience the product through its public interface rather than source code.
3. For frontend products, use the bundled page-state script before and after meaningful actions.
4. Record only what was actually observed.
5. Classify findings into:
   - A. Logic is sound but awkward to use
   - B. Logic itself is flawed
   - C. Purpose or operation is unclear
   - D. UI execution is weak
6. Produce `docs/ux-audit-report.md` with product understanding, startup experience, feature walkthroughs, classified issues, scores, continued-use verdict, and top three recommendations.

## Required Evidence

- Use `README.md` or `README_CN.md` plus user-facing guide docs as the starting context.
- For frontend products, use `scripts/get_page_state.js` and rely on returned `content_snapshot` plus `interactive_elements` rather than guessing.
- If the script or product fails to run, record the failure instead of inventing observations.
