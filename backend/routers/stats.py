"""Stats, validation, reindex, and dataset routes."""

from __future__ import annotations

import io
from contextlib import redirect_stdout

from fastapi import APIRouter, HTTPException

from shared import (
    DEFAULT_DATASET,
    DatasetSwitchRequest,
    get_available_datasets,
    get_root,
    load_cm_index,
    reindex,
    serialize,
    stale_check,
)
from codememory.validate import validate

router = APIRouter(prefix="/api", tags=["stats"])


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@router.get("/stats")
def get_stats():
    index = load_cm_index()
    memories = index.memories

    total = 0
    maturity_counts: dict[str, int] = {}
    stale_count = 0
    stale_ids: list[str] = []
    tag_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}

    for mem_id, entry in memories.items():
        total += 1

        if hasattr(entry, "model_dump"):
            d = entry.model_dump(mode="json")
        elif isinstance(entry, dict):
            d = entry
        else:
            continue

        maturity = d.get("maturity", "draft")
        maturity_counts[maturity] = maturity_counts.get(maturity, 0) + 1

        mtype = d.get("type", "atom")
        type_counts[mtype] = type_counts.get(mtype, 0) + 1

        mstatus = d.get("status", "active")
        status_counts[mstatus] = status_counts.get(mstatus, 0) + 1

        if stale_check(mem_id, entry):
            stale_count += 1
            stale_ids.append(mem_id)

        for tag in d.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    sorted_tags = [
        {"tag": tag, "count": count}
        for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])
    ]

    return serialize({
        "total": total,
        "maturity": maturity_counts,
        "type": type_counts,
        "status": status_counts,
        "stale_count": stale_count,
        "stale_ids": stale_ids,
        "tags": sorted_tags,
    })


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

@router.post("/validate")
def post_validate():
    try:
        index = load_cm_index()
        output = io.StringIO()
        with redirect_stdout(output):
            error_count, warning_count = validate(get_root())
        errors, warnings = _parse_validate_output(output.getvalue())
        return serialize({
            "validated_count": len(index.memories),
            "error_count": error_count,
            "warning_count": warning_count,
            "errors": errors,
            "warnings": warnings,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _parse_validate_output(text: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("[ERROR]"):
            message = line.removeprefix("[ERROR]").strip()
            issue_type = "schema_compliance" if "schema compliance" in message else "broken_link"
            errors.append({"type": issue_type, "message": message})
        elif line.startswith("[WARNING]"):
            warnings.append({
                "type": "circular_dependency",
                "message": line.removeprefix("[WARNING]").strip(),
            })
        else:
            warning_prefixes = {
                "MATURITY-WARN": "maturity",
                "SOURCE-REF-WARN": "source_ref",
                "PROPOSED-WARN": "proposed",
                "STATUS-WARN": "status",
                "GOLDEN-WARN": "golden_questions",
                "SOURCE-WARN": "source",
                "PROPOSAL-WARN": "proposal",
                "CAPTURE-WARN": "capture",
                "TOPIC-WARN": "topic",
            }
            for prefix, issue_type in warning_prefixes.items():
                marker = f"[{prefix}]"
                if line.startswith(marker):
                    warnings.append({
                        "type": issue_type,
                        "message": line.removeprefix(marker).strip(),
                    })
                    break

    return errors, warnings


# ---------------------------------------------------------------------------
# Reindex
# ---------------------------------------------------------------------------

@router.post("/reindex")
def post_reindex():
    try:
        reindex(get_root())
        return serialize({"status": "ok", "message": "Reindex completed"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------

@router.get("/datasets")
def get_datasets():
    datasets = get_available_datasets()
    # R17-CR1: Always return the server's real default (DEFAULT_DATASET),
    # not whatever the client may have sent in the X-Codememory-Dataset header.
    # The middleware no longer writes ContextVar on exempt paths, but using
    # the constant here is a belt-and-suspenders defence against self-reinforcement.
    current = DEFAULT_DATASET
    current_name = current
    return {
        "datasets": serialize(datasets),
        "current": current,
        "current_name": current_name,
    }


@router.post("/datasets/switch")
def post_dataset_switch(req: DatasetSwitchRequest):
    datasets = get_available_datasets()
    names = [d["name"] for d in datasets]
    if req.name not in names:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{req.name}' not found. Available: {', '.join(names)}",
        )
    return serialize({"current": req.name})
