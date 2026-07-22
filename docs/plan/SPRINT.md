# CodeMemory Current Sprint

> **Status:** SPRINT COMPLETE — accepted by owner.
> **Sprint:** Importer v2A — Deterministic Source-Aware Markdown Compiler.
> **Branch:** `codex/importer-v2`.
> **Upstream contracts:** `docs/prd.md`, `docs/architecture.md`, `docs/plan/FUTURE.md`.

---

## Start Gate — Completed

The owner instructed CodeMemory to continue in roadmap order. The next roadmap item is Importer v2; this sprint implements only its minimal deterministic, zero-LLM subitem.

The optional LLM proposer, semantic refinement, Web, MCP/toolkit expansion, Operator UI work, and Personal Memory Phase 2 remain closed.

---

## Objective

Upgrade `compile-md` from heading-only atom splitting into a source-aware migration plan: register every Markdown document as a Source Artifact, generate one lightweight anchor proposal per document, generate paragraph-level derived proposals with exact provenance, and keep every materialized result proposed until the owner merges it.

---

## Contracts

1. `compile-md` may write only Source Artifact registry metadata and its review-set JSON. It never changes source documents or directly creates canonical atom files.
2. A source document has one stable artifact ID derived from its resolved URI, independent of content changes. Recompiling the same URI updates that registry entry instead of adding another one.
3. Each document produces exactly one anchor proposal. The anchor carries a `source_refs` entry for the registered artifact and contains only a compact source description, not a copy of the document body.
4. Each non-empty Markdown paragraph produces one deterministic derived proposal. It carries the same artifact reference plus a paragraph locator and exact line range.
5. Review decisions select which candidates may be materialized. Materialized compiler atoms remain `status: proposed`; review acceptance is not canonical owner merge.
6. `source_refs` express provenance only. Deterministic Importer v2A does not invent `imports` edges; imports suggestions belong to the deferred semantic proposer.
7. Re-running the same source with the same review ID is idempotent: it preserves existing review decisions and does not rewrite unchanged registry/review files. Reusing a review ID for different compiler input fails before replacing the existing review.

---

## Deliverables

### 1. Source-aware compiler contracts

- [x] Extend compiler models with registered artifact IDs, paragraph records, proposal role, and structured `source_refs`.
- [x] Use stable URI-derived Source Artifact IDs and idempotent registry upsert.
- [x] Preserve exact source path, SHA-256, paragraph identity, heading context, and line range in the review set.

### 2. Anchor and derived proposals

- [x] Generate exactly one compact anchor proposal per Markdown document.
- [x] Split section bodies into non-empty paragraphs and generate deterministic derived proposals.
- [x] Keep all proposals pending in review and all materialized atoms `status: proposed`.
- [x] Never create automatic imports edges in the deterministic path.

### 3. Review and materialization safety

- [x] Persist `source_refs` into materialized atom frontmatter.
- [x] Preserve prior decisions on an identical compile retry.
- [x] Reject a conflicting reuse of `review_id` without changing the prior review.
- [x] Keep path traversal protection, no-overwrite behavior, and reindex behavior intact.

### 4. Adapters, docs, and tests

- [x] Keep CLI behavior behind the shared `handle_compile_md` / `handle_materialize_review` facade.
- [x] Report registered sources, anchors, derived candidates, and total proposals in compile output.
- [x] Update PRD/architecture, USER_GUIDE, INTEGRATION, and project structure to the delivered contract.
- [x] Add unit and CLI regression coverage for source registration, provenance, proposal status, idempotency, and source immutability.

---

## Executable Acceptance Criteria

1. Compile a two-file Markdown corpus: the registry contains exactly two stable artifacts; the review contains two anchors and one derived proposal per non-empty paragraph.
2. Every anchor and derived proposal references the correct artifact; each derived locator resolves to the recorded source lines.
3. Source files are byte-identical before and after compile and materialization.
4. Compile identical input twice with the same review ID: registry bytes and review bytes are unchanged, decisions are preserved, and no duplicate artifacts/proposals appear.
5. Change source content and reuse the same review ID: compilation fails without replacing the prior review; using a new review ID updates the existing artifact hash without changing its ID.
6. Accept and materialize selected anchor/derived candidates: only selected files are written, each has `status: proposed` and valid `source_refs`, and default search/build cannot treat it as active canonical truth.
7. The deterministic compiler emits no imports suggestions and introduces no LLM/provider dependency into `src/codememory`.
8. Unsafe review IDs and memory IDs remain rejected; existing files are never overwritten.
9. All unit/API and existing integration suites pass; `git diff --check` passes; checked-in examples have no test residue.

---

## Acceptance Commands

```powershell
python -m pytest tests/unit/test_memory_compiler.py tests/unit/test_sources.py -q
python -m pytest tests/unit tests/test_api.py -q
python tests/integration_test.py
python tests/integration_personal.py
rg -n "llm_gateway|openai|anthropic|gemini|embedding" src/codememory/compiler
git diff --check
git status --short --branch -uall
```

Expected dependency grep result: no matches (exit code 1 is success).

---

## Explicit Deferrals

- LLM-based semantic extraction, classification, deduplication, or imports suggestions.
- MCP/toolkit importer tools and Operator UI review surfaces.
- Web ingestion, URL fetching, PDF parsing, and non-Markdown corpus support.
- Personal Memory semantic discovery.

---

## Completion Gate

Owner independently reproduced the contract and failure-window checks, accepted Importer v2A with no remaining blockers, and authorized commit/push of `codex/importer-v2`.

`SPRINT COMPLETE`
