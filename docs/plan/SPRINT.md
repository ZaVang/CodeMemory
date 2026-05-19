# CodeMemory Current Sprint

> **Active sprint:** P1.3 `expand_source`
> **Goal:** Provide explicit source expansion for agent and human workflows without changing ContextPack's progressive-disclosure default.

---

## Sprint Rules

1. This file tracks only the current sprint.
2. Completed and accepted work is removed from this file.
3. Follow-up ideas move to `docs/plan/FUTURE.md`.
4. Product or architecture changes must update `docs/prd.md` or `docs/architecture.md`.
5. Runtime implementation should be TDD-first.

---

## Scope

Build the minimal `expand_source` contract:

- core can retrieve a Source Artifact by stable artifact id;
- expansion can return full content for local file artifacts;
- expansion can return a bounded excerpt when a text range is requested;
- expansion output includes provenance metadata: artifact id, kind, uri/path, sha256, status, and stale/missing notices;
- CLI/API shape is minimal and backed by shared core behavior;
- docs explain that ContextPack still carries source refs by default and source bodies are retrieved only by explicit expansion.

Not in scope:

- semantic section lookup;
- binary/PDF parsing beyond safe unsupported notices;
- frontend source expansion UI;
- MCP/harness tool exposure;
- migration compiler source-aware proposals.

---

## Tasks

### Task 1 — Define Source Expansion contract

- [x] Add a core result model for source expansion.
- [x] Define supported inputs: artifact id, optional character range, and optional maximum characters.
- [x] Define structured statuses for fresh, stale, missing, and unsupported artifacts.
- [x] Add tests for model shape and error/status behavior.

**Acceptance:** Callers receive a stable, serializable object rather than raw text or thrown filesystem errors.

### Task 2 — Implement local-file expansion

- [x] Load Source Artifact metadata from `.codememory/sources/index.json`.
- [x] Resolve local `file://` and path-like artifact URIs safely relative to the memory root.
- [x] Return full text content for supported text artifacts.
- [x] Return bounded excerpts for requested character ranges or max-character limits.
- [x] Detect missing and stale local files.
- [x] Add tests for full content, excerpt content, missing file, and stale hash detection.

**Acceptance:** Core can return source content or a structured notice for the common local Markdown/text migration path.

### Task 3 — Expose minimal CLI/API surface

- [x] Add a CLI command for explicit source expansion.
- [x] Reuse the same core function from any API/tool handler path.
- [x] Preserve machine-readable JSON output.
- [x] Add tests for public command/handler behavior where existing test structure supports it.

**Acceptance:** Agent harnesses can call one stable command or handler without depending on frontend code.

### Task 4 — Update docs and sprint records

- [x] Update architecture/user/project docs with implemented `expand_source` behavior.
- [x] Update sprint checklist as tasks complete.
- [ ] Append history and pitfalls at closeout after acceptance.

**Acceptance:** Docs describe implemented behavior and clearly separate default ContextPack disclosure from explicit source expansion.

---

## Sprint Acceptance Criteria

- Core can return a source excerpt or full source by artifact id.
- Expansion output includes artifact id, uri/path, hash/status, and content or structured notice.
- Missing or stale source expansion returns a structured error/notice.
- CLI/API path uses shared core behavior.
- Tests cover full expansion, bounded excerpt, missing artifact/file, stale detection, and public surface.
