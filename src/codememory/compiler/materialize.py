"""Materialize accepted memory proposals into canonical atom files."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

import yaml

from codememory.core import compute_body_hash
from codememory.index import load_index, reindex
from codememory.sources import get_source_artifact

from .models import MaterializeResult, MemoryProposal, ReviewSet


def _safe_memory_path(root: Path, memory_id: str) -> Path:
    """Resolve a memory id under root, rejecting absolute/traversal paths."""
    if not memory_id or "\\" in memory_id or ":" in memory_id:
        raise ValueError(f"unsafe memory_id: {memory_id}")

    pure = PurePosixPath(memory_id)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError(f"unsafe memory_id: {memory_id}")

    root_resolved = root.resolve()
    target = (root_resolved / f"{memory_id}.md").resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"unsafe memory_id: {memory_id}") from exc
    return target


def _frontmatter_for_proposal(
    proposal: MemoryProposal,
    *,
    force_proposed: bool = False,
) -> dict:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    frontmatter = {
        "type": proposal.type,
        "id": proposal.memory_id,
        "summary": proposal.summary,
        "status": "proposed" if force_proposed else proposal.status,
        "created": today,
        "updated": today,
        "version": 1,
        "tags": proposal.tags,
        "maturity": proposal.maturity,
        "source": proposal.source,
        "evidence": {
            "contributors": ["memory-compiler"],
            "sessions": [],
        },
        "summary_hash": compute_body_hash(proposal.body.strip()),
    }
    if proposal.source_refs:
        frontmatter["source_refs"] = [
            ref.model_dump(mode="json", exclude_none=True) for ref in proposal.source_refs
        ]
    if proposal.imports:
        frontmatter["imports"] = proposal.imports
    return frontmatter


def _proposal_import_ids(proposal: MemoryProposal) -> list[str] | None:
    """Return import IDs, or ``None`` when a semantic review was tampered."""

    values: list[str] = []
    if not isinstance(proposal.imports, dict):
        return None
    for strength, refs in proposal.imports.items():
        if strength not in {"required", "recommended", "related"} or not isinstance(refs, list):
            return None
        for ref in refs:
            if isinstance(ref, str):
                target = ref
            elif isinstance(ref, dict) and isinstance(ref.get("id"), str):
                target = ref["id"]
            else:
                return None
            if not target:
                return None
            values.append(target)
    return values


def _has_same_batch_cycle(graph: dict[str, list[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(target) for target in graph.get(node, [])):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)


def _preflight_semantic_review(
    root: Path,
    review: ReviewSet,
    proposals: list[MemoryProposal],
) -> list[str]:
    """Validate the complete accepted semantic batch before the first write."""

    errors: list[str] = []
    review_sources = {source.source_id: source for source in review.sources}
    review_paragraphs = {
        (paragraph.source_id, paragraph.paragraph_id): paragraph
        for paragraph in review.paragraphs
    }
    accepted_ids = [proposal.memory_id for proposal in proposals]
    accepted_id_set = set(accepted_ids)
    if len(accepted_ids) != len(accepted_id_set):
        errors.append("duplicate memory_id in accepted semantic batch")

    existing_ids = set(load_index(root).memories)
    graph: dict[str, list[str]] = {}
    for proposal in proposals:
        try:
            file_path = _safe_memory_path(root, proposal.memory_id)
        except ValueError:
            errors.append(f"unsafe memory_id: {proposal.proposal_id}")
            continue
        if file_path.exists():
            errors.append(f"exists: {proposal.memory_id}")
        if not proposal.source_refs:
            errors.append(f"missing source_refs: {proposal.proposal_id}")
        else:
            invalid_source_ref = False
            for ref in proposal.source_refs:
                source = review_sources.get(ref.artifact_id)
                artifact = get_source_artifact(root, ref.artifact_id)
                if source is None or artifact is None or artifact.sha256 != source.sha256:
                    invalid_source_ref = True
                    break
                if proposal.role == "derived":
                    paragraph = review_paragraphs.get((ref.artifact_id, ref.section_id))
                    expected_range = (
                        f"L{paragraph.start_line}-L{paragraph.end_line}"
                        if paragraph is not None
                        else None
                    )
                    if paragraph is None or ref.range != expected_range:
                        invalid_source_ref = True
                        break
                elif ref.section_id is not None or ref.range is not None:
                    invalid_source_ref = True
                    break
            if invalid_source_ref:
                errors.append(f"invalid source_refs: {proposal.proposal_id}")

        import_ids = _proposal_import_ids(proposal)
        if import_ids is None:
            errors.append(f"invalid imports: {proposal.proposal_id}")
            continue
        if proposal.memory_id in import_ids:
            errors.append(f"self import: {proposal.proposal_id}")
        if any(target not in accepted_id_set and target not in existing_ids for target in import_ids):
            errors.append(f"unresolved imports: {proposal.proposal_id}")
        graph[proposal.memory_id] = [target for target in import_ids if target in accepted_id_set]

    if _has_same_batch_cycle(graph):
        errors.append("same-batch import cycle")
    return errors


def materialize_review_set(
    root: Path,
    review: ReviewSet,
    accept_all: bool = False,
) -> MaterializeResult:
    """Write accepted proposals to disk and refresh the index."""
    result = MaterializeResult()

    semantic_review = (
        review.compiler_version >= 3
        or review.proposer is not None
        or any(
            proposal.source.get("platform") == "memory-compiler-llm"
            for proposal in review.proposals
        )
    )

    if semantic_review:
        accepted_proposals = [
            proposal
            for proposal in review.proposals
            if proposal.decision == "accepted" or accept_all
        ]
        result.skipped.extend(
            proposal.proposal_id
            for proposal in review.proposals
            if proposal.decision != "accepted" and not accept_all
        )
        result.errors.extend(_preflight_semantic_review(root, review, accepted_proposals))
        if result.errors:
            return result

    for proposal in review.proposals:
        accepted = proposal.decision == "accepted" or accept_all
        if not accepted:
            if not semantic_review:
                result.skipped.append(proposal.proposal_id)
            continue

        try:
            file_path = _safe_memory_path(root, proposal.memory_id)
        except ValueError as exc:
            result.errors.append(str(exc))
            continue

        if review.compiler_version >= 2:
            if not proposal.source_refs:
                result.errors.append(f"missing source_refs: {proposal.proposal_id}")
                continue
            missing_artifacts = [
                ref.artifact_id
                for ref in proposal.source_refs
                if get_source_artifact(root, ref.artifact_id) is None
            ]
            if missing_artifacts:
                result.errors.append(
                    f"unregistered source_refs: {proposal.proposal_id}: "
                    + ", ".join(sorted(set(missing_artifacts)))
                )
                continue

        if file_path.exists():
            result.errors.append(f"exists: {proposal.memory_id}")
            continue

        file_path.parent.mkdir(parents=True, exist_ok=True)
        yaml_str = yaml.dump(
            _frontmatter_for_proposal(
                proposal,
                force_proposed=review.compiler_version >= 2 or semantic_review,
            ),
            allow_unicode=True,
            sort_keys=False,
        )
        file_path.write_text(f"---\n{yaml_str}---\n{proposal.body.strip()}\n", encoding="utf-8")
        result.written.append(str(file_path))

    if result.written:
        reindex(root)
    return result
