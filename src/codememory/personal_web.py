"""Provider-neutral read models for the Personal owner workspace."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from .capture import scan_all_captures
from .core import parse_frontmatter
from .personal_index import ClaimRecord, TopicRecord, scan_all_claims, scan_all_topics
from .profile import PersonalProfile, validate_personal_profile


class PersonalOverview(BaseModel):
    capture_count: int
    topic_count: int
    claim_count: int
    canonical_count: int
    diagnostics_count: int


class PersonalCaptureView(BaseModel):
    id: str
    captured_at: str
    actor: str
    content_hash: str
    content: str
    locator: str


class PersonalCapturePage(BaseModel):
    items: list[PersonalCaptureView] = Field(default_factory=list)
    total: int
    offset: int
    limit: int


class PersonalClaimView(BaseModel):
    claim_id: str
    topic_id: str
    revision_id: str
    title: str
    content: str
    origin: str
    claim_status: str
    confidence: float | None = None
    derived_from: list[dict[str, Any]] = Field(default_factory=list)
    locator: str


class PersonalTopicView(BaseModel):
    topic_id: str
    revision_id: str
    title: str
    content: str
    origin: str
    created_at: str | None = None
    updated_at: str | None = None
    content_hash: str | None = None
    tags: list[str] = Field(default_factory=list)
    derived_from: list[dict[str, Any]] = Field(default_factory=list)
    relations: list[dict[str, Any]] = Field(default_factory=list)
    merged_from: list[dict[str, Any]] = Field(default_factory=list)
    claims: list[PersonalClaimView] = Field(default_factory=list)
    locator: str


class PersonalTimelineEdge(BaseModel):
    relation: str
    source_id: str
    target_id: str


class PersonalTimelineEvent(BaseModel):
    id: str
    kind: Literal["capture", "topic_revision", "canonical_promotion"]
    timestamp: str
    title: str
    origin: str | None = None
    locator: str | None = None


class PersonalTimeline(BaseModel):
    events: list[PersonalTimelineEvent] = Field(default_factory=list)
    edges: list[PersonalTimelineEdge] = Field(default_factory=list)


def _require_profile(root: Path) -> PersonalProfile:
    validation = validate_personal_profile(root)
    if not validation.profile_valid or validation.profile is None:
        raise ValueError("Personal workspace requires a valid Personal Profile")
    resolved_root = root.resolve()
    profile = validation.profile
    for rel in (profile.paths.journal, profile.paths.incubator, profile.paths.canonical):
        try:
            (resolved_root / rel).resolve().relative_to(resolved_root)
        except ValueError as exc:
            raise ValueError("Personal workspace path resolves outside bound root") from exc
    return profile


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]


def _mapping_list(value: object, allowed: set[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [
        {
            key: item[key]
            for key in allowed
            if key in item and isinstance(item[key], (str, int, float, bool))
        }
        for item in value
        if isinstance(item, dict)
    ]


def _claim_view(claim: ClaimRecord) -> PersonalClaimView:
    confidence = claim.metadata.get("confidence")
    return PersonalClaimView(
        claim_id=claim.claim_id,
        topic_id=claim.topic_id,
        revision_id=claim.revision_id,
        title=claim.title,
        content=claim.content,
        origin=str(claim.metadata.get("origin") or "agent_inference"),
        claim_status=str(claim.metadata["claim_status"]),
        confidence=float(confidence) if isinstance(confidence, (float, int)) else None,
        derived_from=_mapping_list(
            claim.metadata.get("derived_from"),
            {"kind", "id", "capture_id", "content_hash"},
        ),
        locator=claim.display_locator,
    )


def _topic_views(root: Path) -> tuple[list[PersonalTopicView], list[str]]:
    topics_scan = scan_all_topics(root)
    claims_scan = scan_all_claims(root, topics_scan.topics)
    claims_by_revision: dict[str, list[PersonalClaimView]] = {}
    for claim in claims_scan.claims:
        claims_by_revision.setdefault(claim.revision_id, []).append(_claim_view(claim))

    views: list[PersonalTopicView] = []
    for topic in topics_scan.topics:
        metadata = topic.metadata
        views.append(PersonalTopicView(
            topic_id=topic.topic_id,
            revision_id=topic.revision_id,
            title=topic.title,
            content=topic.content,
            origin=str(metadata.get("origin") or "mixed"),
            created_at=str(metadata["created_at"]) if metadata.get("created_at") else None,
            updated_at=str(metadata["updated_at"]) if metadata.get("updated_at") else None,
            content_hash=str(metadata["content_hash"]) if metadata.get("content_hash") else None,
            tags=_string_list(metadata.get("tags")),
            derived_from=_mapping_list(
                metadata.get("derived_from"),
                {"kind", "id", "capture_id", "topic_id", "revision_id", "content_hash"},
            ),
            relations=_mapping_list(
                metadata.get("relations"),
                {"relation", "type", "id", "target_id", "topic_id", "revision_id", "content_hash"},
            ),
            merged_from=_mapping_list(
                metadata.get("merged_from"),
                {"kind", "id", "topic_id", "revision_id", "content_hash"},
            ),
            claims=sorted(
                claims_by_revision.get(topic.revision_id, []),
                key=lambda item: item.claim_id,
            ),
            locator=topic.display_locator,
        ))
    views.sort(key=lambda item: (item.updated_at or item.created_at or "", item.revision_id), reverse=True)
    return views, [*topics_scan.warnings, *claims_scan.warnings]


def get_personal_overview(root: Path) -> PersonalOverview:
    profile = _require_profile(root)
    captures = scan_all_captures(root)
    topics, topic_warnings = _topic_views(root)
    canonical_root = (root.resolve() / profile.paths.canonical).resolve()
    canonical_count = len(list(canonical_root.rglob("*.md"))) if canonical_root.is_dir() else 0
    return PersonalOverview(
        capture_count=len(captures.captures),
        topic_count=len(topics),
        claim_count=sum(len(topic.claims) for topic in topics),
        canonical_count=canonical_count,
        diagnostics_count=len(captures.warnings) + len(topic_warnings),
    )


def get_personal_captures(root: Path, *, offset: int = 0, limit: int = 50) -> PersonalCapturePage:
    _require_profile(root)
    if offset < 0 or limit < 1 or limit > 200:
        raise ValueError("Capture pagination must use offset >= 0 and 1 <= limit <= 200")
    records = sorted(
        scan_all_captures(root).captures,
        key=lambda item: (item.captured_at, item.id),
        reverse=True,
    )
    return PersonalCapturePage(
        items=[
            PersonalCaptureView(
                id=item.id,
                captured_at=item.captured_at,
                actor=item.actor,
                content_hash=item.content_hash,
                content=item.payload,
                locator=item.display_locator,
            )
            for item in records[offset:offset + limit]
        ],
        total=len(records),
        offset=offset,
        limit=limit,
    )


def get_personal_topics(root: Path) -> list[PersonalTopicView]:
    _require_profile(root)
    topics, _ = _topic_views(root)
    return topics


def _event_timestamp(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return text


def _ref_id(ref: dict[str, Any]) -> str | None:
    return str(ref.get("id") or ref.get("capture_id") or "") or None


def _relation_target(relation: dict[str, Any]) -> tuple[str, str] | None:
    target = relation.get("target_id") or relation.get("id") or relation.get("revision_id")
    kind = relation.get("relation") or relation.get("type") or "related"
    if not target:
        return None
    return str(kind), str(target)


def get_personal_timeline(root: Path, *, topic_id: str | None = None) -> PersonalTimeline:
    profile = _require_profile(root)
    captures = scan_all_captures(root).captures
    topics = get_personal_topics(root)
    if topic_id:
        topics = [item for item in topics if item.topic_id == topic_id]
        if not topics:
            raise KeyError(f"Topic not found: {topic_id}")

    referenced_capture_ids = {
        ref_id
        for topic in topics
        for ref in topic.derived_from
        if (ref_id := _ref_id(ref))
    }
    events: dict[str, PersonalTimelineEvent] = {}
    edges: set[tuple[str, str, str]] = set()
    for capture in captures:
        if topic_id and capture.id not in referenced_capture_ids:
            continue
        events[capture.id] = PersonalTimelineEvent(
            id=capture.id,
            kind="capture",
            timestamp=capture.captured_at,
            title=capture.payload.replace("\n", " ")[:120],
            origin="human_explicit",
            locator=capture.display_locator,
        )
    for topic in topics:
        timestamp = _event_timestamp(topic.updated_at or topic.created_at)
        if timestamp:
            events[topic.revision_id] = PersonalTimelineEvent(
                id=topic.revision_id,
                kind="topic_revision",
                timestamp=timestamp,
                title=topic.title,
                origin=topic.origin,
                locator=topic.locator,
            )
        for ref in topic.derived_from:
            source = _ref_id(ref)
            if source:
                edges.add(("derived_from", source, topic.revision_id))
        for ref in topic.merged_from:
            source = _ref_id(ref) or (
                str(ref.get("revision_id")) if ref.get("revision_id") else None
            )
            if source:
                edges.add(("merged_from", source, topic.revision_id))
        for relation in topic.relations:
            parsed = _relation_target(relation)
            if parsed:
                relation_kind, target = parsed
                edges.add((relation_kind, topic.revision_id, target))

    canonical_root = (root.resolve() / profile.paths.canonical).resolve()
    if canonical_root.is_dir():
        for path in sorted(canonical_root.rglob("*.md")):
            metadata, _ = parse_frontmatter(path)
            provenance = metadata.get("provenance")
            if not isinstance(provenance, dict):
                continue
            revision_id = provenance.get("topic_revision_id")
            if not revision_id or (topic_id and revision_id not in {item.revision_id for item in topics}):
                continue
            timestamp = _event_timestamp(metadata.get("updated") or metadata.get("created"))
            atom_id = str(metadata.get("id") or path.relative_to(root).with_suffix("").as_posix())
            event_id = f"promotion:{atom_id}"
            if timestamp:
                events[event_id] = PersonalTimelineEvent(
                    id=event_id,
                    kind="canonical_promotion",
                    timestamp=timestamp,
                    title=str(metadata.get("summary") or atom_id),
                    origin=str(metadata.get("origin")) if metadata.get("origin") else None,
                    locator=path.relative_to(root).as_posix(),
                )
            edges.add(("promoted_to", str(revision_id), event_id))

    return PersonalTimeline(
        events=sorted(events.values(), key=lambda item: (item.timestamp, item.id)),
        edges=[
            PersonalTimelineEdge(relation=relation, source_id=source, target_id=target)
            for relation, source, target in sorted(edges)
        ],
    )
