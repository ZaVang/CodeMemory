"""Idempotent Personal Profile maintenance and Incubator Topic upsert."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo

import yaml
from pydantic import BaseModel, Field, model_validator

from .capture import CaptureRecord, _instance_lock, scan_all_captures
from .index import reindex
from .profile import load_personal_profile, validate_personal_profile


RUNS_RELATIVE_PATH = Path(".codememory/maintenance/runs.jsonl")
STATE_RELATIVE_PATH = Path(".codememory/maintenance/state.json")
PENDING_RELATIVE_DIR = Path(".codememory/maintenance/pending")
_TOPIC_RE = re.compile(
    r"^## (?P<title>.+?)\n<!--\s*codememory:topic\s*\n(?P<meta>.*?)\n-->\n(?P<body>.*?)(?=^## |\Z)",
    re.MULTILINE | re.DOTALL,
)


class ProvenanceRef(BaseModel):
    capture_id: str
    content_hash: str


class ClaimDraft(BaseModel):
    text: str
    title: str = "Inference"
    origin: Literal["agent_inference"] = "agent_inference"
    claim_status: Literal["unassessed", "supported", "contested", "refuted"] = "unassessed"
    derived_from: list[ProvenanceRef]
    claim_id: str | None = None


class TopicParagraph(BaseModel):
    text: str
    heading: str | None = None
    origin: Literal["human_explicit", "agent_synthesis", "mixed"] = "agent_synthesis"
    derived_from: list[ProvenanceRef]


class TopicDraft(BaseModel):
    title: str
    paragraphs: list[TopicParagraph]
    claims: list[ClaimDraft] = Field(default_factory=list)
    origin: Literal["human_explicit", "agent_synthesis", "mixed"] = "mixed"
    tags: list[str] = Field(default_factory=list)
    topic_id: str | None = None
    month: str | None = None

    @model_validator(mode="after")
    def has_content(self) -> "TopicDraft":
        if not self.paragraphs and not self.claims:
            raise ValueError("Topic draft must contain a paragraph or claim")
        return self


class FileMutation(BaseModel):
    path: str
    before_hash: str
    after_hash: str
    before_content: str
    after_content: str


class PendingChangeset(BaseModel):
    run_id: str
    input_digest: str
    capture_ids: list[str]
    capture_hashes: dict[str, str]
    generated_at: str
    mutations: list[FileMutation]


RunStage = Literal[
    "prepared", "applying", "applied", "scan_blocked", "scan_passed", "conflict"
]


class MaintenanceEvent(BaseModel):
    run_id: str
    stage: RunStage
    input_digest: str
    capture_ids: list[str] = Field(default_factory=list)
    capture_hashes: dict[str, str] = Field(default_factory=dict)
    changeset_hash: str | None = None
    occurred_at: str
    detail: dict[str, Any] = Field(default_factory=dict)


class MaintenanceState(BaseModel):
    active_run_id: str | None = None
    active_stage: RunStage | None = None
    delivery_commit: str | None = None
    delivery_pushed: bool = False


class MaintenanceResult(BaseModel):
    run_id: str | None = None
    stage: str
    input_digest: str | None = None
    capture_ids: list[str] = Field(default_factory=list)
    reused: bool = False
    warnings: list[str] = Field(default_factory=list)


def _digest_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _stable_id(prefix: str, payload: object, size: int = 20) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"{prefix}_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:size]}"


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def _now(root: Path, value: datetime | None = None) -> datetime:
    profile = load_personal_profile(root)
    zone = ZoneInfo(profile.timezone)
    return value.astimezone(zone) if value else datetime.now(zone)


def load_maintenance_state(root: Path) -> MaintenanceState:
    path = root / STATE_RELATIVE_PATH
    if not path.exists():
        return MaintenanceState()
    return MaintenanceState.model_validate_json(path.read_text(encoding="utf-8"))


def save_maintenance_state(root: Path, state: MaintenanceState) -> None:
    _atomic_write(root / STATE_RELATIVE_PATH, state.model_dump_json(indent=2) + "\n")


def load_maintenance_events(root: Path) -> list[MaintenanceEvent]:
    path = root / RUNS_RELATIVE_PATH
    if not path.exists():
        return []
    events: list[MaintenanceEvent] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(MaintenanceEvent.model_validate_json(line))
    return events


def append_maintenance_event(root: Path, event: MaintenanceEvent) -> None:
    path = root / RUNS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(event.model_dump_json() + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _latest_events(root: Path) -> dict[str, MaintenanceEvent]:
    latest: dict[str, MaintenanceEvent] = {}
    for event in load_maintenance_events(root):
        latest[event.run_id] = event
    return latest


def _consumed_capture_ids(root: Path) -> set[str]:
    consumed: set[str] = set()
    for event in load_maintenance_events(root):
        if event.stage in {"applied", "scan_blocked", "scan_passed"}:
            consumed.update(event.capture_ids)
    return consumed


def discover_unconsumed_captures(root: Path) -> tuple[list[CaptureRecord], list[str]]:
    scan = scan_all_captures(root)
    consumed = _consumed_capture_ids(root)
    records = [record for record in scan.captures if record.id not in consumed]
    records.sort(key=lambda record: (record.captured_at, record.id))
    return records, scan.warnings


def capture_input_digest(captures: list[CaptureRecord]) -> str:
    return _digest_text("\n".join(f"{item.id}\0{item.content_hash}" for item in captures))


def _provenance_dict(refs: list[ProvenanceRef]) -> list[dict[str, str]]:
    return [ref.model_dump(mode="json") for ref in refs]


def _render_topic(draft: TopicDraft, captures: dict[str, CaptureRecord], when: datetime) -> tuple[str, str, str]:
    all_refs = [ref for paragraph in draft.paragraphs for ref in paragraph.derived_from]
    all_refs.extend(ref for claim in draft.claims for ref in claim.derived_from)
    for ref in all_refs:
        record = captures.get(ref.capture_id)
        if record is None or record.content_hash != ref.content_hash:
            raise ValueError(f"invalid provenance reference: {ref.capture_id}")
    topic_id = draft.topic_id or _stable_id("top", {"title": draft.title.casefold()})
    body_blocks: list[str] = []
    for paragraph in draft.paragraphs:
        if paragraph.heading:
            body_blocks.append(f"### {paragraph.heading}")
        provenance = {"origin": paragraph.origin, "derived_from": _provenance_dict(paragraph.derived_from)}
        body_blocks.extend([
            "<!-- codememory:provenance",
            yaml.safe_dump(provenance, sort_keys=False, allow_unicode=True).rstrip(),
            "-->",
            paragraph.text,
        ])
    for claim in draft.claims:
        claim_payload = {
            "topic_id": topic_id,
            "title": claim.title,
            "text": claim.text,
            "claim_status": claim.claim_status,
            "derived_from": _provenance_dict(claim.derived_from),
        }
        claim_id = claim.claim_id or _stable_id("claim", claim_payload)
        claim_meta = {
            "claim_id": claim_id,
            "origin": claim.origin,
            "claim_status": claim.claim_status,
            "derived_from": claim_payload["derived_from"],
        }
        body_blocks.extend([
            f"### Claim: {claim.title}",
            "<!-- codememory:claim",
            yaml.safe_dump(claim_meta, sort_keys=False, allow_unicode=True).rstrip(),
            "-->",
            claim.text,
        ])
    body = "\n".join(body_blocks).rstrip()
    revision_payload = {
        "topic_id": topic_id,
        "title": draft.title,
        "origin": draft.origin,
        "tags": draft.tags,
        "body": body,
    }
    revision_id = _stable_id("rev", revision_payload)
    meta = {
        "topic_id": topic_id,
        "revision_id": revision_id,
        "created_at": when.isoformat(timespec="seconds"),
        "updated_at": when.isoformat(timespec="seconds"),
        "origin": draft.origin,
        "tags": draft.tags,
        "derived_from": _provenance_dict(all_refs),
        "content_hash": _digest_text(body),
    }
    blocks = [
        f"## {draft.title}",
        "<!-- codememory:topic",
        yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).rstrip(),
        "-->",
        body,
    ]
    return topic_id, revision_id, "\n".join(blocks).rstrip() + "\n\n"


def _upsert_topic(document: str, topic_id: str, rendered: str, month: str) -> str:
    prefix = document if document else f"# Incubator — {month}\n\n"
    for match in _TOPIC_RE.finditer(prefix):
        try:
            meta = yaml.safe_load(match.group("meta")) or {}
        except yaml.YAMLError:
            continue
        if str(meta.get("topic_id")) == topic_id:
            created_at = meta.get("created_at")
            if created_at is not None:
                rendered = re.sub(
                    r"(?m)^created_at:.*$",
                    "created_at: " + str(created_at),
                    rendered,
                    count=1,
                )
            return prefix[:match.start()] + rendered + prefix[match.end():].lstrip("\n")
    if not prefix.endswith("\n\n"):
        prefix = prefix.rstrip("\n") + "\n\n"
    return prefix + rendered


def _prepare_maintenance_locked(
    root: Path,
    *,
    drafts: list[TopicDraft] | None = None,
    now: datetime | None = None,
) -> MaintenanceResult:
    validation = validate_personal_profile(root)
    if not validation.profile_valid or validation.profile is None:
        raise ValueError("Invalid Personal Profile: " + "; ".join(validation.errors))
    state = load_maintenance_state(root)
    if state.active_run_id:
        if state.active_stage == "scan_blocked":
            raise RuntimeError(f"maintenance blocked by sensitive scan in run {state.active_run_id}")
        return _resume_maintenance_locked(root)

    captures, warnings = discover_unconsumed_captures(root)
    if not captures:
        for event in reversed(load_maintenance_events(root)):
            if event.stage in {"applied", "scan_passed"}:
                return MaintenanceResult(
                    run_id=event.run_id,
                    stage=event.stage,
                    input_digest=event.input_digest,
                    capture_ids=event.capture_ids,
                    reused=True,
                    warnings=warnings,
                )
        return MaintenanceResult(stage="idle", warnings=warnings)
    digest = capture_input_digest(captures)
    for event in reversed(load_maintenance_events(root)):
        if event.input_digest == digest and event.stage in {"applied", "scan_passed"}:
            return MaintenanceResult(run_id=event.run_id, stage=event.stage, input_digest=digest, capture_ids=event.capture_ids, reused=True, warnings=warnings)

    instant = _now(root, now)
    run_id = _stable_id("run", {"input_digest": digest})
    # A revision may retain provenance from older, already-consumed Captures.
    # The run input remains only the unconsumed set, while provenance validation
    # resolves against every currently complete and hash-valid Capture.
    all_valid = scan_all_captures(root).captures
    records = {record.id: record for record in all_valid}
    if drafts is None:
        raise ValueError(
            "maintenance requires a Topic changeset from the Personal Memory Skill; "
            "inspect maintenance status first"
        )
    topic_drafts = drafts
    profile = validation.profile
    contents: dict[str, str] = {}
    originals: dict[str, str] = {}
    for draft in topic_drafts:
        month = draft.month or captures[0].captured_at[:7]
        if not re.fullmatch(r"\d{4}-\d{2}", month):
            raise ValueError(f"invalid Topic month: {month}")
        rel = (Path(profile.paths.incubator) / f"{month}.md").as_posix()
        if rel not in contents:
            path = root / rel
            originals[rel] = path.read_text(encoding="utf-8") if path.exists() else ""
            contents[rel] = originals[rel]
        topic_id, _revision_id, rendered = _render_topic(draft, records, instant)
        contents[rel] = _upsert_topic(contents[rel], topic_id, rendered, month)
    mutations = [
        FileMutation(
            path=rel,
            before_hash=_digest_text(originals[rel]),
            after_hash=_digest_text(contents[rel]),
            before_content=originals[rel],
            after_content=contents[rel],
        )
        for rel in sorted(contents)
        if originals[rel] != contents[rel]
    ]
    pending = PendingChangeset(
        run_id=run_id,
        input_digest=digest,
        capture_ids=[record.id for record in captures],
        capture_hashes={record.id: record.content_hash for record in captures},
        generated_at=instant.isoformat(timespec="seconds"),
        mutations=mutations,
    )
    pending_path = root / PENDING_RELATIVE_DIR / f"{run_id}.json"
    _atomic_write(pending_path, pending.model_dump_json(indent=2) + "\n")
    changeset_hash = _digest_text(pending.model_dump_json(exclude={"generated_at"}))
    append_maintenance_event(root, MaintenanceEvent(
        run_id=run_id, stage="prepared", input_digest=digest,
        capture_ids=pending.capture_ids, capture_hashes=pending.capture_hashes,
        changeset_hash=changeset_hash, occurred_at=instant.isoformat(timespec="seconds"),
    ))
    save_maintenance_state(root, MaintenanceState(active_run_id=run_id, active_stage="prepared"))
    return _resume_maintenance_locked(root, warnings=warnings)


def prepare_maintenance(
    root: Path,
    *,
    drafts: list[TopicDraft] | None = None,
    now: datetime | None = None,
) -> MaintenanceResult:
    with _instance_lock(root / ".codememory" / "maintenance" / "maintenance.lock"):
        return _prepare_maintenance_locked(root, drafts=drafts, now=now)


def _resume_maintenance_locked(root: Path, *, warnings: list[str] | None = None) -> MaintenanceResult:
    state = load_maintenance_state(root)
    if not state.active_run_id:
        return MaintenanceResult(stage="idle", warnings=warnings or [])
    if state.active_stage == "scan_blocked":
        return MaintenanceResult(run_id=state.active_run_id, stage="scan_blocked", warnings=warnings or [])
    pending_path = root / PENDING_RELATIVE_DIR / f"{state.active_run_id}.json"
    if not pending_path.exists():
        raise FileNotFoundError(f"pending changeset missing for {state.active_run_id}")
    pending = PendingChangeset.model_validate_json(pending_path.read_text(encoding="utf-8"))
    latest = _latest_events(root).get(pending.run_id)
    if latest and latest.stage in {"applied", "scan_passed"}:
        profile = load_personal_profile(root)
        delivery_finished = latest.stage == "scan_passed" and (
            not profile.maintenance.auto_push or state.delivery_pushed
        )
        if delivery_finished or not profile.maintenance.auto_commit:
            save_maintenance_state(root, MaintenanceState())
        return MaintenanceResult(run_id=pending.run_id, stage=latest.stage, input_digest=pending.input_digest, capture_ids=pending.capture_ids, reused=True, warnings=warnings or [])
    instant = _now(root)
    if not latest or latest.stage != "applying":
        append_maintenance_event(root, MaintenanceEvent(
            run_id=pending.run_id, stage="applying", input_digest=pending.input_digest,
            capture_ids=pending.capture_ids, capture_hashes=pending.capture_hashes,
            occurred_at=instant.isoformat(timespec="seconds"),
        ))
        state.active_stage = "applying"
        save_maintenance_state(root, state)
    for mutation in pending.mutations:
        path = root / mutation.path
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        current_hash = _digest_text(current)
        if current_hash == mutation.after_hash:
            continue
        if current_hash != mutation.before_hash:
            append_maintenance_event(root, MaintenanceEvent(
                run_id=pending.run_id, stage="conflict", input_digest=pending.input_digest,
                capture_ids=pending.capture_ids, capture_hashes=pending.capture_hashes,
                occurred_at=instant.isoformat(timespec="seconds"), detail={"path": mutation.path},
            ))
            state.active_stage = "conflict"
            save_maintenance_state(root, state)
            return MaintenanceResult(run_id=pending.run_id, stage="conflict", input_digest=pending.input_digest, capture_ids=pending.capture_ids, warnings=warnings or [])
        _atomic_write(path, mutation.after_content)
    append_maintenance_event(root, MaintenanceEvent(
        run_id=pending.run_id, stage="applied", input_digest=pending.input_digest,
        capture_ids=pending.capture_ids, capture_hashes=pending.capture_hashes,
        occurred_at=_now(root).isoformat(timespec="seconds"),
        detail={"after_hashes": {item.path: item.after_hash for item in pending.mutations}},
    ))
    profile = load_personal_profile(root)
    if profile.maintenance.auto_commit:
        state.active_stage = "applied"
        save_maintenance_state(root, state)
    else:
        save_maintenance_state(root, MaintenanceState())
    reindex(root)
    return MaintenanceResult(run_id=pending.run_id, stage="applied", input_digest=pending.input_digest, capture_ids=pending.capture_ids, warnings=warnings or [])


def resume_maintenance(root: Path, *, warnings: list[str] | None = None) -> MaintenanceResult:
    with _instance_lock(root / ".codememory" / "maintenance" / "maintenance.lock"):
        return _resume_maintenance_locked(root, warnings=warnings)


def maintenance_status(root: Path) -> dict[str, Any]:
    state = load_maintenance_state(root)
    captures, warnings = discover_unconsumed_captures(root)
    return {
        "active_run_id": state.active_run_id,
        "active_stage": state.active_stage,
        "unconsumed_capture_ids": [record.id for record in captures],
        "unconsumed_captures": [
            {
                "id": record.id,
                "captured_at": record.captured_at,
                "content_hash": record.content_hash,
                "display_locator": record.display_locator,
            }
            for record in captures
        ],
        "warnings": warnings,
    }
