# CodeMemory Current Sprint

> **Status:** SPRINT COMPLETE — accepted by owner.
> **Sprint:** Personal Periodic Review — Deterministic Evidence Bundle.
> **Branch:** `codex/personal-periodic-review`.
> **Depends on:** owner-accepted Personal Memory Web on `main` at `4c5b1cc`.

## Objective

Add a bounded monthly/yearly review workflow for Personal Profiles. Core freezes a deterministic, provenance-rich evidence bundle for an explicit calendar period; the Personal Memory Skill performs semantic synthesis and may update Incubator Topics. Reviews remain temporary by default and are persisted only on explicit owner request.

## Contracts

1. Period selection is explicit: `monthly + YYYY-MM` or `yearly + YYYY`, interpreted in the Personal Profile timezone as a closed calendar window. Core never guesses “last month” from wall-clock time.
2. Bundle generation is read-only. It does not consume Captures, mutate maintenance state, write Topics/reviews, rebuild indexes, invoke Git, load an embedding model, or call an LLM.
3. Inputs reuse authoritative parsers: complete/hash-valid Captures, valid Topic revisions and inline Claims, and currently assemblable canonical Atom/Schema metadata. Invalid objects are excluded with bounded diagnostics.
4. In-period Captures are included with stable IDs/hashes/content. Captures outside the window are included only when explicitly cited by an included Topic revision and are marked `in_period: false`.
5. Included Topics are revisions authored/updated in the period. For each such logical topic, Core may add the latest valid pre-window revision as a baseline so explicit evolution can be compared without semantic guessing.
6. Claim snapshots are read per Topic revision. Stable `claim_id` histories may yield deterministic status transitions only when authored statuses differ across ordered revisions; Core does not decide whether a claim is true.
7. Relationships come only from authored `derived_from`, `relations`, `merged_from`, and canonical promotion provenance. Lexical or semantic similarity never becomes a persisted edge.
8. Bundle ordering and digest are deterministic. Equivalent instance bytes plus period/options produce byte-equivalent JSON and the same digest; generation time is not part of the digest.
9. Default output is JSON to stdout or an explicit no-clobber output file. No report Markdown is created merely by preparing a bundle.
10. Explicit persistence writes at most one file per period under the configured `paths.reviews`: `monthly/YYYY-MM.md` or `yearly/YYYY.md`. The caller cannot choose an arbitrary path.
11. Persistence requires a valid unchanged bundle plus non-empty authored Markdown. Same digest/content is idempotent; changed content conflicts unless owner explicitly supplies overwrite.
12. Persisted review metadata records period/window, bundle digest, origin, creator and stable source IDs; it is non-canonical, never enters imports/build, and contains no absolute root/private-local/model/Git data.
13. The Personal Memory Skill first resolves any active maintenance run and catches up unconsumed Capture before preparing a review. Core does not silently run maintenance from `periodic-review`.
14. The Skill distinguishes facts, synthesis, inference and uncertainty; it may prepare provenance-valid Topic changesets, but canonical promotion remains owner-gated.
15. No REST, Web, MCP, generic Agent-tool, semantic-index, external provider, scheduler, auto-commit, or auto-push surface is added in this Sprint.

## Deliverables

- [x] Add typed periodic-review bundle/window/topic/claim/transition models.
- [x] Add deterministic bundle preparation using existing Personal parsers and canonical metadata.
- [x] Add safe no-clobber JSON output and explicit owner-only review persistence.
- [x] Add thin handlers and owner CLI `periodic-review prepare|save`.
- [x] Extend the Personal Memory Skill with monthly/yearly review sequencing and output discipline.
- [x] Add window, invalid-object, baseline, transition, digest/idempotency, path/privacy and no-mutation tests.
- [x] Update PRD, architecture, profile contract, integration/user/project docs, roadmap and pitfalls.
- [x] Run Core/API, Personal, integration and diff acceptance; restore generated example side effects.

## Executable Acceptance Criteria

1. Monthly `2026-07` resolves to `2026-07-01T00:00:00` through `2026-07-31T23:59:59.999999` in the Profile timezone; yearly `2026` resolves analogously.
2. Equivalent input bytes generate the same serialized bundle and digest across repeated runs; no runtime timestamp, absolute root or output path changes the result.
3. Hash-invalid/incomplete Captures and malformed Topic/Claim blocks are excluded; diagnostics reveal only safe relative locators/IDs.
4. In-period Topic revisions include their explicit Capture evidence plus at most one latest pre-window baseline revision per logical topic. Unrelated historical objects are excluded.
5. Repeated stable `claim_id` snapshots produce a transition only for an authored status change, with source/target revision IDs and statuses preserved.
6. Canonical promotion events are included only when explicit provenance references an included Topic revision; proposed/archived content is not treated as current canonical truth.
7. `prepare` changes no instance bytes. `--output` refuses to overwrite and writes atomically.
8. `save` derives its destination under resolved `paths.reviews`; traversal, symlink/junction escape, tampered bundle digest, empty content and mismatched period all fail before writes.
9. Re-saving identical digest/content returns reused with unchanged bytes. Changed content requires explicit `--overwrite`; a different bundle for the same period conflicts without it.
10. Persisted review frontmatter is non-canonical, contains stable source IDs/digest and no private configuration; reindex/search/build do not treat it as an Atom.
11. CLI remains owner-only; Agent catalog/MCP/Toolkit/REST/OpenAPI contain no periodic-review operation.
12. Skill contract runs maintenance status/resume/catch-up first, defaults to a temporary synthesis, persists only on explicit owner request, and never auto-promotes canonical content.
13. Existing Core/API/Personal/integration suites remain green and `git diff --check` passes with no example/runtime residue.

## Acceptance Commands

```powershell
python -m pytest tests/personal/test_periodic_review.py -q
python -m pytest tests/unit tests/test_api.py -q
python -m pytest tests/personal -q
python tests/integration_test.py
python tests/integration_personal.py
git diff --check
git status --short --branch -uall
```

## Explicit Deferrals

- Automatic scheduling, notification delivery, automatic Git commit/push, and background generation.
- REST/Web/MCP/Toolkit/Agent-tool exposure.
- Fixed report taxonomies, dashboards, semantic clustering, model invocation inside Core, and automatic canonical promotion.
- Cross-owner review sharing, authentication, remote storage, and arbitrary review filenames.

## Completion Gate

Owner acceptance was recorded on 2026-07-23 after independent contract review and the complete acceptance matrix passed. This sprint is closed; no deferred capability is implied by this status.
