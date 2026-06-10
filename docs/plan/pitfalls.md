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

**有效期：收敛阶段 C 移除 intensity / decay 机制后本条失效（见 `docs/architecture.md` §6）。**

`validate` can emit decay/staleness warnings for low-intensity memories. When a test is asserting source-ref warning counts, make the fixture memory intentionally non-decaying, for example by using `intensity: 8`.

Otherwise a source-ref test can fail for an unrelated validation warning.

注意：阶段 A 起 `intensity: 8` 不再自动产生 `protected: true`（已解耦），它只影响 decay 行为。

---

## build 不自动展开 asset 原文

实现 asset 相关功能时，不要让 build 产物（resolve / context-pack 输出）自动内联 asset 的原文正文。

build 产物默认只携带 asset 引用（source_refs）；原文获取必须走显式的 `source expand`。这保证长文档不会未经请求就进入 agent 的 handoff 上下文。（概念边界见 `docs/architecture.md` §3.5。）
