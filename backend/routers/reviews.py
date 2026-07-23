"""Owner review queue and golden-question REST adapter."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from shared import ReviewActionRequest, get_root, load_cm_index, serialize
from codememory.handlers import handle_merge, handle_reject, handle_test
from codememory.proposals import list_proposals, load_proposal

router = APIRouter(prefix="/api", tags=["reviews"])


def _proposed_atoms() -> list[dict]:
    atoms: list[dict] = []
    for memory_id, entry in sorted(load_cm_index().memories.items()):
        if entry.status != "proposed":
            continue
        atoms.append({
            "kind": "proposed_atom",
            "id": memory_id,
            "target_id": memory_id,
            "summary": entry.summary,
            "created_at": entry.created,
            "created_by": (entry.source or {}).get("created_by", "unknown"),
            "tags": entry.tags,
            "version": entry.version,
        })
    return atoms


@router.get("/reviews")
def get_reviews():
    atoms = _proposed_atoms()
    patches = [
        {
            "kind": "patch_proposal",
            "id": proposal.proposal_id,
            "target_id": proposal.target_id,
            "reason": proposal.reason,
            "created_at": proposal.created_at,
            "created_by": proposal.created_by,
            "patch": proposal.patch.model_dump(mode="json", exclude_none=True),
            "patch_fields": [
                name
                for name, value in proposal.patch.model_dump(mode="json").items()
                if value is not None
            ],
        }
        for proposal in list_proposals(get_root())
    ]
    return serialize({
        "proposed_atoms": atoms,
        "patch_proposals": patches,
        "total": len(atoms) + len(patches),
    })


def _apply_atom(action: str, memory_id: str) -> dict:
    entry = load_cm_index().memories.get(memory_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")
    if entry.status != "proposed":
        raise HTTPException(
            status_code=409,
            detail=f"Memory '{memory_id}' is '{entry.status}', expected 'proposed'",
        )
    try:
        result = handle_merge(get_root(), memory_id) if action == "merged" else handle_reject(get_root(), memory_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except SystemExit as exc:
        raise HTTPException(status_code=409, detail="Review action rejected by CodeMemory") from exc
    return serialize({"status": action, "kind": "proposed_atom", "id": memory_id, "result": result})


def _apply_patch(action: str, proposal_id: str) -> dict:
    try:
        proposal = load_proposal(get_root(), proposal_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if proposal is None:
        raise HTTPException(status_code=404, detail=f"Patch proposal '{proposal_id}' not found")
    try:
        result = handle_merge(get_root(), proposal_id) if action == "merged" else handle_reject(get_root(), proposal_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except SystemExit as exc:
        raise HTTPException(status_code=409, detail="Review action rejected by CodeMemory") from exc
    return serialize({
        "status": action,
        "kind": "patch_proposal",
        "id": proposal_id,
        "target_id": proposal.target_id,
        "result": result,
    })


@router.post("/reviews/atoms/merge")
def merge_atom(req: ReviewActionRequest):
    return _apply_atom("merged", req.id)


@router.post("/reviews/atoms/reject")
def reject_atom(req: ReviewActionRequest):
    return _apply_atom("rejected", req.id)


@router.post("/reviews/patches/merge")
def merge_patch(req: ReviewActionRequest):
    return _apply_patch("merged", req.id)


@router.post("/reviews/patches/reject")
def reject_patch(req: ReviewActionRequest):
    return _apply_patch("rejected", req.id)


@router.get("/tests/{memory_id:path}")
def get_test_bundle(memory_id: str, depth: str = "recommended", budget: int | None = None):
    try:
        return json.loads(handle_test(get_root(), memory_id, depth=depth, budget=budget))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found") from exc
    except (ValueError, FileNotFoundError) as exc:
        message = str(exc)
        status = 404 if "not found" in message.lower() else 400
        raise HTTPException(status_code=status, detail=message)
