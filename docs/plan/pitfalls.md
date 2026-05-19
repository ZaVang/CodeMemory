# CodeMemory Sprint Pitfalls

Recurring implementation notes for future sprints.

---

## Path convention

The local `sprint` skill still references the older `docs/plans/` path. This repository now uses singular `docs/plan/`.

Use:

- `docs/plan/FUTURE.md`
- `docs/plan/SPRINT.md`
- `docs/plan/HISTORY.md`
- `docs/plan/pitfalls.md`

Do not recreate `docs/plans/`.

---

## Test side effects

Some API tests can rewrite example dataset generated files, especially:

- `examples/companion/.codememory/index.json`
- `examples/companion/.codememory/log.md`

If those files change only because tests reindexed or logged operations, restore them before finalizing unless the sprint intentionally changes example data.
