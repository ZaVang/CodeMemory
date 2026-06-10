"""Memory validation: broken links, schema compliance, cycle detection, decay suggestions."""

import logging
from datetime import datetime, timedelta
from pathlib import Path

from .core import compute_retrieval_probability
from .core import parse_frontmatter
from .index import load_index
from .models import NON_ASSEMBLABLE_STATUSES, IndexData, MemoryEntry
from .resolve import _get_imports, build_dag, find_cycle_participants
from .sources import check_source_registry, load_source_registry

_logger = logging.getLogger("codememory")


def check_schema_compliance(metadata: dict, schemas: dict) -> list[str]:
    """Check if an instance's metadata conforms to its declared schema."""
    schema_id = metadata.get("schema")
    if not schema_id:
        return []
    schema = schemas.get(schema_id)
    if not schema:
        return [f"Schema '{schema_id}' not found"]
    return [
        f"Missing required field: {f['name']}"
        for f in schema.get("fields", [])
        if f.get("required") and f["name"] not in metadata
    ]


def _compute_in_degree(memory_id: str, index: IndexData) -> int:
    """Count how many other memories reference this one via imports."""
    for mid, entry in index.memories.items():
        if mid == memory_id:
            continue
        imports_dict = entry.imports
        if not isinstance(imports_dict, dict):
            continue
        all_refs = (
            imports_dict.get("required", [])
            + imports_dict.get("recommended", [])
            + imports_dict.get("related", [])
        )
        for ref in all_refs:
            ref_id = ref if isinstance(ref, str) else ref.get("id", "")
            if ref_id == memory_id:
                return 1
    return 0


def _check_maturity_stale(memory_id: str, entry: MemoryEntry) -> list[str]:
    """Check if proven memories have gone too long without access."""
    warnings: list[str] = []
    if entry.maturity != "proven":
        return warnings

    if not entry.last_access:
        warnings.append(
            f"{memory_id} is proven but has never been accessed. "
            f"Consider review to confirm status."
        )
        return warnings

    try:
        last_access = datetime.fromisoformat(entry.last_access)
        if last_access < datetime.now() - timedelta(days=365):
            warnings.append(
                f"{memory_id} is proven but last accessed {entry.last_access} "
                f"(>12 months ago). Consider review to confirm proven status."
            )
    except (ValueError, TypeError):
        pass
    return warnings


def _check_decay(memory_id: str, entry: MemoryEntry, index: IndexData) -> list[str]:
    """Check whether a memory is at risk of decay (R13-M1: unified formula).

    Uses the same continuous decay formula as overview/wander:
        R = 0.5^(days_since / stability)
    Triggers a warning when retrieval probability drops below 0.1
    (roughly 3.3 half-lives — equivalent to ~46 days at default stability=14.0).
    """
    warnings: list[str] = []

    if entry.intensity >= 8:
        return warnings

    # Use precomputed days_since field, or compute from last_access
    days_since = getattr(entry, 'days_since_last_access', None)
    if days_since is None and entry.access_count > 0 and entry.last_access:
        try:
            last_access = datetime.fromisoformat(entry.last_access)
            days_since = max(0, (datetime.now() - last_access).days)
        except (ValueError, TypeError):
            pass

    stability = getattr(entry, 'stability', 14.0)

    if days_since is not None and days_since >= 0:
        retrieval_prob = compute_retrieval_probability(days_since, stability)
        if retrieval_prob > 0.1:
            return warnings

    if _compute_in_degree(memory_id, index) > 0:
        return warnings

    warnings.append(
        f"{memory_id} has low access (access_count={entry.access_count}), "
        f"no recent access, and is not referenced by any other memory. "
        f"Consider re-linking or archiving this memory."
    )
    return warnings


def _check_source_refs(memory_id: str, entry: MemoryEntry, source_ids: set[str]) -> list[str]:
    """Check that atom source_refs point to registered Source Artifacts."""

    warnings: list[str] = []
    for ref in entry.source_refs:
        if ref.artifact_id not in source_ids:
            warnings.append(
                f"{memory_id} source_ref points to non-existent Source Artifact: {ref.artifact_id}"
            )
    return warnings


def validate(root_dir: Path) -> tuple[int, int]:
    """Run integrity checks on all indexed memories.

    Returns (error_count, warning_count).
    """
    index = load_index(root_dir)
    memories = index.memories

    errors = 0
    warnings = 0

    # Build full schema dict for lookup
    schemas: dict[str, dict] = {}
    for mid, entry in memories.items():
        if entry.type == "schema":
            file_path = root_dir / entry.path
            meta, _ = parse_frontmatter(file_path)
            schemas[mid] = meta
    source_registry = load_source_registry(root_dir)
    source_ids = set(source_registry.sources.keys())

    print("Running CodeMemory Validation...\n")

    for mid, entry in memories.items():
        # 1. Broken link check
        deps = _get_imports(entry, "full")
        for dep in deps:
            if dep not in memories:
                print(f"[ERROR] {mid} imports non-existent memory: {dep}")
                errors += 1

        # 2. Schema compliance (only when schema field is present)
        if entry.schema:
            file_path = root_dir / entry.path
            meta, _ = parse_frontmatter(file_path)
            for err in check_schema_compliance(meta, schemas):
                print(f"[ERROR] {mid} schema compliance: {err}")
                errors += 1

        # 3. Cycle check
        graph = build_dag(mid, "required", index)
        cycle_ids = find_cycle_participants(graph)
        if cycle_ids and mid in cycle_ids:
            print(f"[WARNING] {mid} is part of a circular dependency involving: {cycle_ids}")
            print("          Fix: Consider merging atoms or placing in a composite as siblings.")
            warnings += 1

        # 4. Maturity staleness check
        for msg in _check_maturity_stale(mid, entry):
            print(f"[MATURITY-WARN] {msg}")
            warnings += 1

        # 5. Source ref check
        for msg in _check_source_refs(mid, entry, source_ids):
            print(f"[SOURCE-REF-WARN] {msg}")
            warnings += 1

        # 6. Decay check
        if entry.type != "schema":
            for msg in _check_decay(mid, entry, index):
                print(f"[DECAY-WARN] {msg}")
                warnings += 1

        # 7. Proposed backlog check (Phase A: unreviewed proposals pile up)
        if entry.status == "proposed":
            try:
                updated_dt = datetime.fromisoformat(entry.updated)
                age_days = (datetime.now() - updated_dt).days
            except (ValueError, TypeError):
                age_days = None
            if age_days is not None and age_days > 14:
                print(
                    f"[PROPOSED-WARN] {mid} has been proposed for {age_days} days. "
                    f"Review it: codememory merge {mid} (or reject)."
                )
                warnings += 1

        # 8. Status edge check (Phase A: active atoms importing non-assemblable nodes)
        if entry.status == "active":
            for dep in deps:
                dep_entry = memories.get(dep)
                if dep_entry is not None and dep_entry.status in NON_ASSEMBLABLE_STATUSES:
                    print(
                        f"[STATUS-WARN] {mid} (active) imports {dep} "
                        f"({dep_entry.status}); it will be skipped at build time."
                    )
                    warnings += 1

        # 9. golden_questions shape check (Phase C, architecture §3.4)
        if entry.type != "schema":
            meta_raw, _raw_body = parse_frontmatter(root_dir / entry.path)
            gq = meta_raw.get("golden_questions")
            if gq is not None:
                if not isinstance(gq, list):
                    print(f"[GOLDEN-WARN] {mid} golden_questions must be a list.")
                    warnings += 1
                else:
                    for i, item in enumerate(gq):
                        if not isinstance(item, dict) or not isinstance(item.get("q"), str):
                            print(
                                f"[GOLDEN-WARN] {mid} golden_questions[{i}] must be "
                                f"a mapping with a string 'q' field."
                            )
                            warnings += 1

    # 7. Source Artifact registry checks
    for result in check_source_registry(root_dir):
        if result.state in {"missing", "stale"}:
            print(f"[SOURCE-WARN] {result.artifact_id} is {result.state}: {result.message}")
            warnings += 1

    # 8. Modification-proposal queue checks (Phase C, architecture §3.3)
    from .proposals import list_proposals
    for prop in list_proposals(root_dir):
        if prop.target_id not in memories:
            print(
                f"[PROPOSAL-WARN] {prop.proposal_id} targets non-existent memory "
                f"{prop.target_id}; reject it or restore the target."
            )
            warnings += 1
        try:
            age_days = (datetime.now() - datetime.fromisoformat(prop.created_at)).days
        except (ValueError, TypeError):
            age_days = None
        if age_days is not None and age_days > 14:
            print(
                f"[PROPOSAL-WARN] {prop.proposal_id} has been pending for {age_days} days. "
                f"Review it: codememory merge {prop.proposal_id} (or reject)."
            )
            warnings += 1

    print(f"\nValidation complete. {len(memories)} memories checked.")
    print(f"Errors: {errors}, Warnings: {warnings}")
    return errors, warnings
