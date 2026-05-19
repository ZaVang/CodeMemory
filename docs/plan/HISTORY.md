# CodeMemory Sprint History

This file records accepted sprint outcomes. Current work belongs in `docs/plan/SPRINT.md`; long-term backlog belongs in `docs/plan/FUTURE.md`.

---

## 2026-05-19 — Source Artifact Registry foundation

**Status:** Accepted and archived.

**Commit:** `b93add5 Add source artifact registry docs and checks`

**Delivered:**

- Added `SourceArtifact`, `SourceRegistry`, and source check models.
- Added `.codememory/sources/index.json` load/save registry primitives.
- Added add/list/get/check source operations.
- Added CLI commands: `codememory source add|list|get|check`.
- Added validation warnings for missing and stale local Source Artifacts.
- Updated architecture, user guide, project structure, and sprint docs.
- Added unit coverage for source serialization, persistence, handler exposure, fresh/stale/missing checks, and validate integration.

**Acceptance evidence:**

- `python -m pytest -q tests/unit tests/test_api.py` → `148 passed`
- `git diff --check` → passed
- Markdown local link check → `checked 11 markdown files; no missing local doc links`
- old plan path check → `no stale old plan paths`
- manual CLI source flow verified add/check/validate behavior

**Deferred:**

- `source_refs`
- `expand_source`
- ContextPack / resolve v2 source disclosure
- Migration Compiler v2 Source Artifact integration
- frontend source-ref UI
