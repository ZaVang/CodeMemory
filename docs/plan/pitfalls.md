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

---

## Validation tests and unrelated decay warnings

`validate` can emit decay/staleness warnings for low-intensity memories. When a test is asserting source-ref warning counts, make the fixture memory intentionally non-decaying, for example by using `intensity: 8` or `status: protected`.

Otherwise a source-ref test can fail for an unrelated validation warning.

---

## Progressive disclosure boundary

Do not make ContextPack automatically expand Source Artifact bodies while implementing source-related features.

Default ContextPack output should carry `source_refs`; source body retrieval belongs behind explicit `expand_source` calls. This keeps long documents out of agent handoff prompts unless the caller intentionally asks for them.
