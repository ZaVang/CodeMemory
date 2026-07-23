"""Deterministic evidence bundles for Personal Profile periodic reviews."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo

import yaml
from pydantic import BaseModel, Field

from .capture import CaptureRecord, scan_all_captures
from .core import parse_frontmatter
from .index import load_index
from .personal_index import TopicRecord, scan_all_topics, scan_claims_in_topic
from .profile import PersonalProfile, validate_personal_profile


ReviewPeriod = Literal["monthly", "yearly"]
FORMAT_VERSION = "personal-periodic-review/v1"


class PeriodicReviewWindow(BaseModel):
    period: ReviewPeriod
    anchor: str
    timezone: str
    date_from: str
    date_to: str


class PeriodicCaptureEvidence(BaseModel):
    id: str
    captured_at: str
    actor: str
    content_hash: str
    content: str
    locator: str
    in_period: bool


class PeriodicClaimSnapshot(BaseModel):
    claim_id: str
    topic_id: str
    revision_id: str
    title: str
    content: str
    origin: str
    claim_status: str
    timestamp: str
    derived_from: list[dict[str, str]] = Field(default_factory=list)
    locator: str


class PeriodicClaimTransition(BaseModel):
    claim_id: str
    from_revision_id: str
    to_revision_id: str
    from_status: str
    to_status: str
    changed_at: str


class PeriodicTopicEvidence(BaseModel):
    topic_id: str
    revision_id: str
    title: str
    content: str
    origin: str
    created_at: str | None = None
    updated_at: str | None = None
    content_hash: str | None = None
    tags: list[str] = Field(default_factory=list)
    derived_from: list[dict[str, str]] = Field(default_factory=list)
    relations: list[dict[str, str]] = Field(default_factory=list)
    merged_from: list[dict[str, str]] = Field(default_factory=list)
    claims: list[PeriodicClaimSnapshot] = Field(default_factory=list)
    locator: str
    is_baseline: bool = False


class PeriodicCanonicalEvidence(BaseModel):
    id: str
    summary: str
    status: str
    origin: str | None = None
    topic: str | None = None
    created: str | None = None
    updated: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    locator: str


class PeriodicReviewBundle(BaseModel):
    format_version: Literal["personal-periodic-review/v1"] = FORMAT_VERSION
    window: PeriodicReviewWindow
    captures: list[PeriodicCaptureEvidence] = Field(default_factory=list)
    topics: list[PeriodicTopicEvidence] = Field(default_factory=list)
    claim_transitions: list[PeriodicClaimTransition] = Field(default_factory=list)
    canonical: list[PeriodicCanonicalEvidence] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    bundle_digest: str


class PeriodicReviewSaveResult(BaseModel):
    path: str
    bundle_digest: str
    reused: bool = False
    overwritten: bool = False


def _require_profile(root: Path) -> PersonalProfile:
    validation = validate_personal_profile(root)
    if not validation.profile_valid or validation.profile is None:
        raise ValueError("Periodic review requires a valid Personal Profile")
    return validation.profile


def _require_contained_profile_directory(
    root: Path,
    relative: str,
    *,
    label: str,
) -> Path:
    resolved_root = root.resolve()
    resolved_path = (resolved_root / relative).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"paths.{label} resolves outside bound root") from exc
    if not resolved_path.is_dir():
        raise ValueError(f"paths.{label} directory is missing")
    return resolved_path


def resolve_periodic_window(
    root: Path,
    *,
    period: ReviewPeriod,
    anchor: str,
) -> PeriodicReviewWindow:
    profile = _require_profile(root)
    zone = ZoneInfo(profile.timezone)
    if period == "monthly":
        try:
            start_date = date.fromisoformat(f"{anchor}-01")
        except ValueError as exc:
            raise ValueError("monthly periodic review anchor must be YYYY-MM") from exc
        if start_date.strftime("%Y-%m") != anchor:
            raise ValueError("monthly periodic review anchor must be YYYY-MM")
        if start_date.month == 12:
            next_date = date(start_date.year + 1, 1, 1)
        else:
            next_date = date(start_date.year, start_date.month + 1, 1)
    else:
        if len(anchor) != 4 or not anchor.isdigit():
            raise ValueError("yearly periodic review anchor must be YYYY")
        start_date = date(int(anchor), 1, 1)
        next_date = date(start_date.year + 1, 1, 1)
    start = datetime.combine(start_date, time.min, tzinfo=zone)
    end = datetime.combine(next_date, time.min, tzinfo=zone) - timedelta(microseconds=1)
    return PeriodicReviewWindow(
        period=period,
        anchor=anchor,
        timezone=profile.timezone,
        date_from=start.isoformat(timespec="microseconds"),
        date_to=end.isoformat(timespec="microseconds"),
    )


def _parse_timestamp(value: object, zone: ZoneInfo) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=zone)
    return parsed.astimezone(zone)


def _bounds(window: PeriodicReviewWindow) -> tuple[datetime, datetime]:
    return datetime.fromisoformat(window.date_from), datetime.fromisoformat(window.date_to)


def _in_window(value: object, window: PeriodicReviewWindow, zone: ZoneInfo) -> bool:
    parsed = _parse_timestamp(value, zone)
    if parsed is None:
        return False
    start, end = _bounds(window)
    return start <= parsed <= end


def _safe_refs(value: object, allowed: set[str]) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        safe: dict[str, str] = {}
        for key in sorted(allowed):
            candidate = item.get(key)
            if isinstance(candidate, (str, bool, int, float)):
                safe[key] = str(candidate)
        if safe:
            result.append(safe)
    return result


def _safe_tags(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted(str(item) for item in value if item is not None)


def _topic_timestamp(topic: TopicRecord, zone: ZoneInfo) -> datetime | None:
    return _parse_timestamp(
        topic.metadata.get("updated_at") or topic.metadata.get("created_at"),
        zone,
    )


def _topic_evidence(
    root: Path,
    topic: TopicRecord,
    *,
    is_baseline: bool,
    zone: ZoneInfo,
) -> tuple[PeriodicTopicEvidence, list[str]]:
    claims_scan = scan_claims_in_topic(root, topic)
    parsed_timestamp = _topic_timestamp(topic, zone)
    timestamp = (
        parsed_timestamp.isoformat(timespec="microseconds")
        if parsed_timestamp is not None
        else ""
    )
    claims = [
        PeriodicClaimSnapshot(
            claim_id=claim.claim_id,
            topic_id=claim.topic_id,
            revision_id=claim.revision_id,
            title=claim.title,
            content=claim.content,
            origin=str(claim.metadata.get("origin") or "agent_inference"),
            claim_status=str(claim.metadata["claim_status"]),
            timestamp=timestamp,
            derived_from=_safe_refs(
                claim.metadata.get("derived_from"),
                {"kind", "id", "capture_id", "content_hash"},
            ),
            locator=claim.display_locator,
        )
        for claim in claims_scan.claims
        if parsed_timestamp is not None
    ]
    evidence = PeriodicTopicEvidence(
        topic_id=topic.topic_id,
        revision_id=topic.revision_id,
        title=topic.title,
        content=topic.content,
        origin=str(topic.metadata.get("origin") or "mixed"),
        created_at=str(topic.metadata["created_at"]) if topic.metadata.get("created_at") else None,
        updated_at=str(topic.metadata["updated_at"]) if topic.metadata.get("updated_at") else None,
        content_hash=str(topic.metadata["content_hash"]) if topic.metadata.get("content_hash") else None,
        tags=_safe_tags(topic.metadata.get("tags")),
        derived_from=_safe_refs(
            topic.metadata.get("derived_from"),
            {"kind", "id", "capture_id", "topic_id", "revision_id", "content_hash"},
        ),
        relations=_safe_refs(
            topic.metadata.get("relations"),
            {"relation", "type", "id", "target_id", "topic_id", "revision_id", "content_hash"},
        ),
        merged_from=_safe_refs(
            topic.metadata.get("merged_from"),
            {"kind", "id", "topic_id", "revision_id", "content_hash"},
        ),
        claims=sorted(claims, key=lambda item: item.claim_id),
        locator=topic.display_locator,
        is_baseline=is_baseline,
    )
    return evidence, claims_scan.warnings


def _capture_ref_id(ref: dict[str, str]) -> str | None:
    kind = ref.get("kind")
    value = ref.get("id") or ref.get("capture_id")
    if value and (kind in {None, "", "capture"} or value.startswith("cap_")):
        return value
    return None


def _capture_evidence(
    record: CaptureRecord,
    *,
    in_period: bool,
) -> PeriodicCaptureEvidence:
    return PeriodicCaptureEvidence(
        id=record.id,
        captured_at=record.captured_at,
        actor=record.actor,
        content_hash=record.content_hash,
        content=record.payload,
        locator=record.display_locator,
        in_period=in_period,
    )


def _claim_transitions(topics: list[PeriodicTopicEvidence]) -> list[PeriodicClaimTransition]:
    grouped: dict[str, list[PeriodicClaimSnapshot]] = {}
    for topic in topics:
        for claim in topic.claims:
            grouped.setdefault(claim.claim_id, []).append(claim)
    result: list[PeriodicClaimTransition] = []
    for claim_id, snapshots in grouped.items():
        snapshots.sort(key=lambda item: (item.timestamp, item.revision_id))
        previous = snapshots[0]
        for current in snapshots[1:]:
            if current.claim_status != previous.claim_status:
                result.append(PeriodicClaimTransition(
                    claim_id=claim_id,
                    from_revision_id=previous.revision_id,
                    to_revision_id=current.revision_id,
                    from_status=previous.claim_status,
                    to_status=current.claim_status,
                    changed_at=current.timestamp,
                ))
            previous = current
    return sorted(result, key=lambda item: (item.changed_at, item.claim_id, item.to_revision_id))


def _safe_provenance(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, Any] = {}
    for key in ("topic_id", "topic_revision_id", "topic_revision_hash", "owner_confirmed"):
        if key in value and isinstance(value[key], (str, bool, int, float)):
            result[key] = value[key]
    captures = _safe_refs(
        value.get("captures"),
        {"kind", "id", "capture_id", "content_hash"},
    )
    if captures:
        result["captures"] = captures
    return result


def _canonical_evidence(
    root: Path,
    included_revisions: set[str],
) -> list[PeriodicCanonicalEvidence]:
    index = load_index(root)
    result: list[PeriodicCanonicalEvidence] = []
    resolved_root = root.resolve()
    for memory_id, entry in sorted(index.memories.items()):
        if entry.status != "active" or entry.type not in {"atom", "schema"}:
            continue
        path = (resolved_root / entry.path).resolve()
        try:
            path.relative_to(resolved_root)
        except ValueError:
            continue
        if not path.is_file():
            continue
        metadata, _ = parse_frontmatter(path)
        provenance = _safe_provenance(metadata.get("provenance"))
        revision_id = provenance.get("topic_revision_id")
        if not isinstance(revision_id, str) or revision_id not in included_revisions:
            continue
        result.append(PeriodicCanonicalEvidence(
            id=memory_id,
            summary=entry.summary,
            status=entry.status,
            origin=entry.origin,
            topic=entry.topic,
            created=entry.created or None,
            updated=entry.updated or None,
            provenance=provenance,
            locator=entry.path,
        ))
    return result


def _safe_diagnostics(root: Path, warnings: list[str]) -> list[str]:
    root_text = str(root.resolve())
    variants = {root_text, root_text.replace("\\", "/")}
    result: list[str] = []
    for warning in warnings:
        safe = str(warning)
        for variant in variants:
            safe = safe.replace(variant, ".")
        result.append(safe[:300])
    return sorted(set(result))


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def periodic_review_digest(bundle: PeriodicReviewBundle) -> str:
    return _digest_payload(bundle.model_dump(mode="json", exclude={"bundle_digest"}))


def prepare_periodic_review(
    root: Path,
    *,
    period: ReviewPeriod,
    anchor: str,
) -> PeriodicReviewBundle:
    profile = _require_profile(root)
    _require_contained_profile_directory(root, profile.paths.journal, label="journal")
    _require_contained_profile_directory(root, profile.paths.incubator, label="incubator")
    zone = ZoneInfo(profile.timezone)
    window = resolve_periodic_window(root, period=period, anchor=anchor)
    captures_scan = scan_all_captures(root)
    topics_scan = scan_all_topics(root)
    start, _ = _bounds(window)

    grouped: dict[str, list[TopicRecord]] = {}
    for topic in topics_scan.topics:
        if _topic_timestamp(topic, zone) is not None:
            grouped.setdefault(topic.topic_id, []).append(topic)

    selected: list[tuple[TopicRecord, bool]] = []
    for topic_id in sorted(grouped):
        revisions = sorted(
            grouped[topic_id],
            key=lambda item: (_topic_timestamp(item, zone), item.revision_id),
        )
        in_period = [item for item in revisions if _in_window(
            item.metadata.get("updated_at") or item.metadata.get("created_at"),
            window,
            zone,
        )]
        if not in_period:
            continue
        baseline = [
            item
            for item in revisions
            if (_topic_timestamp(item, zone) or start) < start
        ]
        if baseline:
            selected.append((baseline[-1], True))
        selected.extend((item, False) for item in in_period)

    topic_evidence: list[PeriodicTopicEvidence] = []
    warnings = [*captures_scan.warnings, *topics_scan.warnings]
    for topic, is_baseline in selected:
        evidence, claim_warnings = _topic_evidence(
            root,
            topic,
            is_baseline=is_baseline,
            zone=zone,
        )
        topic_evidence.append(evidence)
        warnings.extend(claim_warnings)
    topic_evidence.sort(
        key=lambda item: (
            _parse_timestamp(item.updated_at or item.created_at, zone)
            or datetime.min.replace(tzinfo=zone),
            item.topic_id,
            item.revision_id,
            item.is_baseline,
        )
    )

    cited_capture_ids = {
        capture_id
        for topic in topic_evidence
        for ref in [
            *topic.derived_from,
            *(ref for claim in topic.claims for ref in claim.derived_from),
        ]
        if (capture_id := _capture_ref_id(ref))
    }
    capture_evidence = [
        _capture_evidence(
            record,
            in_period=_in_window(record.captured_at, window, zone),
        )
        for record in captures_scan.captures
        if _in_window(record.captured_at, window, zone) or record.id in cited_capture_ids
    ]
    capture_evidence.sort(key=lambda item: (
        _parse_timestamp(item.captured_at, zone) or datetime.min.replace(tzinfo=zone),
        item.id,
    ))

    included_revisions = {topic.revision_id for topic in topic_evidence}
    transitions = _claim_transitions(topic_evidence)
    canonical = _canonical_evidence(root, included_revisions)
    source_ids = sorted({
        *(capture.id for capture in capture_evidence),
        *(topic.revision_id for topic in topic_evidence),
        *(claim.claim_id for topic in topic_evidence for claim in topic.claims),
        *(item.id for item in canonical),
    })
    payload = {
        "format_version": FORMAT_VERSION,
        "window": window.model_dump(mode="json"),
        "captures": [item.model_dump(mode="json") for item in capture_evidence],
        "topics": [item.model_dump(mode="json") for item in topic_evidence],
        "claim_transitions": [item.model_dump(mode="json") for item in transitions],
        "canonical": [item.model_dump(mode="json") for item in canonical],
        "diagnostics": _safe_diagnostics(root, warnings),
        "source_ids": source_ids,
    }
    return PeriodicReviewBundle(
        **payload,
        bundle_digest=_digest_payload(payload),
    )


def serialize_periodic_review(bundle: PeriodicReviewBundle) -> str:
    if periodic_review_digest(bundle) != bundle.bundle_digest:
        raise ValueError("Periodic review bundle digest mismatch")
    return json.dumps(bundle.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def write_periodic_review_bundle(path: Path, bundle: PeriodicReviewBundle) -> Path:
    if path.exists():
        raise FileExistsError(f"Periodic review output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = serialize_periodic_review(bundle)
    temp = path.with_name(path.name + ".tmp")
    try:
        with open(temp, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()
    return path


def _replace_with_secure_temp(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="x",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        temp_path = None
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def load_periodic_review_bundle(path: Path) -> PeriodicReviewBundle:
    bundle = PeriodicReviewBundle.model_validate_json(path.read_text(encoding="utf-8"))
    if periodic_review_digest(bundle) != bundle.bundle_digest:
        raise ValueError("Periodic review bundle digest mismatch")
    return bundle


def _review_path(root: Path, profile: PersonalProfile, bundle: PeriodicReviewBundle) -> Path:
    resolved_root = root.resolve()
    reviews_root = _require_contained_profile_directory(
        root,
        profile.paths.reviews,
        label="reviews",
    )
    path = (reviews_root / bundle.window.period / f"{bundle.window.anchor}.md").resolve()
    try:
        path.relative_to(reviews_root)
    except ValueError as exc:
        raise ValueError("Periodic review path resolves outside paths.reviews") from exc
    return path


def save_periodic_review(
    root: Path,
    bundle: PeriodicReviewBundle,
    body: str,
    *,
    created_by: str = "agent:codex",
    overwrite: bool = False,
) -> PeriodicReviewSaveResult:
    profile = _require_profile(root)
    expected_window = resolve_periodic_window(
        root,
        period=bundle.window.period,
        anchor=bundle.window.anchor,
    )
    if bundle.window != expected_window:
        raise ValueError("Periodic review bundle window does not match the bound Profile")
    if periodic_review_digest(bundle) != bundle.bundle_digest:
        raise ValueError("Periodic review bundle digest mismatch")
    content = body.strip()
    if not content:
        raise ValueError("Periodic review content must not be empty")
    path = _review_path(root, profile, bundle)
    rel_path = path.relative_to(root.resolve()).as_posix()
    title = "Monthly" if bundle.window.period == "monthly" else "Yearly"
    metadata = {
        "format_version": FORMAT_VERSION,
        "review_period": bundle.window.period,
        "review_anchor": bundle.window.anchor,
        "date_from": bundle.window.date_from,
        "date_to": bundle.window.date_to,
        "timezone": bundle.window.timezone,
        "bundle_digest": bundle.bundle_digest,
        "origin": "agent_synthesis",
        "created_by": created_by,
        "source_ids": bundle.source_ids,
    }
    rendered = (
        "---\n"
        + yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).rstrip()
        + f"\n---\n\n# {title} Review — {bundle.window.anchor}\n\n{content}\n"
    )
    existed = path.exists()
    if existed:
        current = path.read_text(encoding="utf-8")
        if current == rendered:
            return PeriodicReviewSaveResult(
                path=rel_path,
                bundle_digest=bundle.bundle_digest,
                reused=True,
            )
        if not overwrite:
            raise FileExistsError(
                f"Periodic review already exists for {bundle.window.period} {bundle.window.anchor}"
            )
    _replace_with_secure_temp(path, rendered)
    return PeriodicReviewSaveResult(
        path=rel_path,
        bundle_digest=bundle.bundle_digest,
        overwritten=existed and overwrite,
    )
