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

## build 不自动展开 asset 原文

实现 asset 相关功能时，不要让 build 产物（resolve / context-pack 输出）自动内联 asset 的原文正文。

build 产物默认只携带 asset 引用（source_refs）；原文获取必须走显式的 `source expand`。这保证长文档不会未经请求就进入 agent 的 handoff 上下文。（概念边界见 `docs/architecture.md` §3.5。）
