---
name: personal-memory
description: Maintain a CodeMemory Personal Profile. Use for low-friction capture, missed-run catch-up, incubator Topic synthesis, provenance-rich claims, owner review, or canonical promotion. Do not use it for Web research or semantic discovery.
---

# Personal Memory

Operate only on the Personal Profile explicitly bound to the current CodeMemory root.

## Choose the interaction mode

- For a record-only request, append the owner's text as a Capture and stop. Do not ask follow-up questions.
- Enter interview mode only when the owner explicitly asks you to continue asking questions.
- If a critical ambiguity makes the requested result impossible or unsafe, ask the minimum blocking question. Do not interrupt for optional enrichment.
- Treat an explicit request to create a "formal idea" or canonical idea as owner confirmation for that promotion only.

## Capture

Preserve the owner's wording. Use the capture command/tool so the append, stable Capture ID, content hash, lock, flush, and fsync contracts remain enforced. Never rewrite or delete an existing Capture unless the owner explicitly requests manual cleanup.

## Maintain

1. Read all complete, hash-valid, unconsumed Captures returned by the maintenance status/run API. Include missed days; never infer consumption from dates or line numbers.
2. Read related existing Topics before choosing whether to create or revise one.
3. Submit a deterministic changeset. Reuse a Topic ID for the same subject. Let Core derive and verify the revision ID from content and provenance.
4. Give every synthesized paragraph paragraph-level provenance using Capture IDs and content hashes.
5. A Topic may use `origin: mixed`. Put each independent Agent inference in an inline claim block with a stable `claim_id` and claim-level `claim_status`; never create a separate claim Markdown file.
6. Resume a pending or blocked run through Core. Never generate a second changeset for the same active run.

## Review and promotion

- Routine Capture organization and Topic revisions do not require per-item approval.
- Agent-created canonical Atoms remain `proposed` and outside default build until the owner confirms them.
- Present concentrated review as a batch and support promote, merge, and delete decisions together.
- Preserve Capture hashes, Topic revision hashes, and owner confirmation in canonical provenance.

## Safety boundaries

- Capture remains available during maintenance or delivery failures.
- A sensitive-scan block is a safety notification, not an ordinary review reminder. Report only the rule, path, and object locator; never echo the matching value.
- Do not bypass the staged-diff scan, stage private/runtime files, or create another commit while retrying a failed push.
- Do not use Web or semantic discovery in Phase 1B.
