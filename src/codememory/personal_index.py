"""Typed indexing, lexical discovery, and stable-ID reads for Personal Profile."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import yaml
from pydantic import BaseModel, Field

from .capture import scan_all_captures, scan_capture_file
from .core import parse_frontmatter
from .models import IndexData, PersonalIndexEntry
from .profile import load_personal_profile


_TOPIC_HEADING_RE = re.compile(r"^## (?P<title>.+?)\s*$", re.MULTILINE)
_TOPIC_META_RE = re.compile(
    r"<!--\s*codememory:topic\s*\n(?P<meta>.*?)\n-->\n?",
    re.DOTALL,
)
_CLAIM_HEADING_RE = re.compile(r"^### Claim:\s*(?P<title>.+?)\s*$", re.MULTILINE)
_CLAIM_META_RE = re.compile(
    r"<!--\s*codememory:claim\s*\n(?P<meta>.*?)\n-->\n?",
    re.DOTALL,
)
_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


class TopicRecord(BaseModel):
    topic_id: str
    revision_id: str
    title: str
    content: str
    path: str
    display_locator: str
    line: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class TopicScan(BaseModel):
    topics: list[TopicRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ClaimRecord(BaseModel):
    claim_id: str
    topic_id: str
    revision_id: str
    title: str
    content: str
    path: str
    display_locator: str
    line: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClaimScan(BaseModel):
    claims: list[ClaimRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ObjectReadResult(BaseModel):
    kind: str
    id: str
    path: str
    display_locator: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    read_action: str = "read"


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def scan_topic_file(root: Path, path: Path) -> TopicScan:
    """Parse Topic sections while preserving nested claim blocks as content."""
    text = path.read_text(encoding="utf-8")
    headings = list(_TOPIC_HEADING_RE.finditer(text))
    result = TopicScan()
    rel_path = path.relative_to(root).as_posix()
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        segment = text[heading.end():end]
        meta_match = _TOPIC_META_RE.search(segment)
        if meta_match is None:
            continue
        line = text.count("\n", 0, heading.start()) + 1
        try:
            metadata = yaml.safe_load(meta_match.group("meta")) or {}
            topic_id = str(metadata["topic_id"])
            revision_id = str(metadata["revision_id"])
            if "claim_status" in metadata:
                result.warnings.append(
                    f"Topic-level claim_status ignored: {revision_id} ({rel_path}:{line})"
                )
                metadata.pop("claim_status", None)
            content = segment[meta_match.end():]
            if content.startswith("\n"):
                content = content[1:]
            content = content.rstrip("\n")
            result.topics.append(TopicRecord(
                topic_id=topic_id,
                revision_id=revision_id,
                title=heading.group("title").strip(),
                content=content,
                path=rel_path,
                display_locator=f"{rel_path}:{line}",
                line=line,
                metadata=metadata,
            ))
        except (KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
            result.warnings.append(f"invalid Topic ignored: {rel_path}:{line}: {exc}")
    return result


def scan_all_topics(root: Path) -> TopicScan:
    profile = load_personal_profile(root)
    result = TopicScan()
    incubator = root / profile.paths.incubator
    if not incubator.exists():
        return result
    seen: set[tuple[str, str]] = set()
    for path in sorted(incubator.rglob("*.md")):
        scanned = scan_topic_file(root, path)
        for topic in scanned.topics:
            month = Path(topic.path).stem
            key = (month, topic.topic_id)
            if key in seen:
                scanned.warnings.append(
                    f"duplicate topic_id in {month}: {topic.topic_id}"
                )
                continue
            seen.add(key)
            result.topics.append(topic)
        result.warnings.extend(scanned.warnings)
    return result


def scan_claims_in_topic(root: Path, topic: TopicRecord) -> ClaimScan:
    result = ClaimScan()
    headings = list(_CLAIM_HEADING_RE.finditer(topic.content))
    all_level_three = list(re.finditer(r"^### .+?$", topic.content, re.MULTILINE))
    for heading in headings:
        end = next(
            (candidate.start() for candidate in all_level_three if candidate.start() > heading.start()),
            len(topic.content),
        )
        segment = topic.content[heading.end():end]
        meta_match = _CLAIM_META_RE.search(segment)
        line = topic.line + topic.content.count("\n", 0, heading.start()) + 1
        if meta_match is None:
            result.warnings.append(f"incomplete Claim ignored: {topic.path}:{line}")
            continue
        try:
            metadata = yaml.safe_load(meta_match.group("meta")) or {}
            claim_id = str(metadata["claim_id"])
            claim_status = str(metadata["claim_status"])
            if claim_status not in {"unassessed", "supported", "contested", "refuted"}:
                result.warnings.append(f"invalid claim_status ignored: {claim_id}")
                continue
            content = segment[meta_match.end():].strip()
            result.claims.append(ClaimRecord(
                claim_id=claim_id,
                topic_id=topic.topic_id,
                revision_id=topic.revision_id,
                title=heading.group("title").strip(),
                content=content,
                path=topic.path,
                display_locator=f"{topic.path}:{line}",
                line=line,
                metadata={
                    **metadata,
                    "topic_id": topic.topic_id,
                    "revision_id": topic.revision_id,
                    "updated_at": topic.metadata.get("updated_at"),
                },
            ))
        except (KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
            result.warnings.append(f"invalid Claim ignored: {topic.path}:{line}: {exc}")
    return result


def scan_all_claims(root: Path, topics: list[TopicRecord] | None = None) -> ClaimScan:
    result = ClaimScan()
    seen: set[str] = set()
    for topic in topics if topics is not None else scan_all_topics(root).topics:
        scanned = scan_claims_in_topic(root, topic)
        for claim in scanned.claims:
            if claim.claim_id in seen:
                result.warnings.append(f"duplicate claim_id: {claim.claim_id}")
                continue
            seen.add(claim.claim_id)
            result.claims.append(claim)
        result.warnings.extend(scanned.warnings)
    return result


def build_personal_index(root: Path) -> tuple[dict[str, PersonalIndexEntry], list[str]]:
    profile_path = root / ".codememory" / "profile.yaml"
    if not profile_path.exists():
        return {}, []
    objects: dict[str, PersonalIndexEntry] = {}
    warnings: list[str] = []
    captures = scan_all_captures(root)
    warnings.extend(captures.warnings)
    for capture in captures.captures:
        objects[capture.id] = PersonalIndexEntry(
            kind="capture",
            id=capture.id,
            path=capture.path,
            display_locator=capture.display_locator,
            summary=capture.payload.replace("\n", " ")[:160],
            content=capture.payload,
            timestamp=capture.captured_at,
            origin="human_explicit",
            metadata={
                "captured_at": capture.captured_at,
                "actor": capture.actor,
                "content_hash": capture.content_hash,
            },
        )
    topics = scan_all_topics(root)
    warnings.extend(topics.warnings)
    for topic in topics.topics:
        meta = topic.metadata
        objects[topic.revision_id] = PersonalIndexEntry(
            kind="incubator_topic",
            id=topic.revision_id,
            path=topic.path,
            display_locator=topic.display_locator,
            summary=topic.title,
            content=topic.content,
            timestamp=str(meta.get("updated_at") or meta.get("created_at") or ""),
            tags=_string_list(meta.get("tags")),
            origin=str(meta.get("origin")) if meta.get("origin") is not None else None,
            topic=topic.topic_id,
            project=str(meta.get("project")) if meta.get("project") is not None else None,
            people=_string_list(meta.get("people") or meta.get("person")),
            metadata=meta,
        )
    claims = scan_all_claims(root, topics.topics)
    warnings.extend(claims.warnings)
    for claim in claims.claims:
        meta = claim.metadata
        objects[claim.claim_id] = PersonalIndexEntry(
            kind="incubator_claim",
            id=claim.claim_id,
            path=claim.path,
            display_locator=claim.display_locator,
            summary=claim.title,
            content=claim.content,
            timestamp=str(meta.get("updated_at") or ""),
            origin=str(meta.get("origin") or "agent_inference"),
            topic=claim.topic_id,
            metadata=meta,
        )
    return objects, warnings


def _tokens(query: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(query)]


def _lexical_score(query: str, *, id_: str, summary: str, tags: Iterable[str], body: str) -> float:
    tokens = _tokens(query)
    if not tokens:
        return 1.0 if query.lower() in " ".join((id_, summary, *tags, body)).lower() else 0.0
    total = len(tokens)
    id_hits = sum(token in id_.lower() for token in tokens)
    summary_hits = sum(token in summary.lower() for token in tokens)
    tag_values = [tag.lower() for tag in tags]
    tag_hits = sum(any(token in tag for tag in tag_values) for token in tokens)
    body_lower = body.lower()
    body_hits = sum(token in body_lower for token in tokens)
    return (4 * id_hits + 3 * summary_hits + 2 * tag_hits + body_hits) / total


def _date_value(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None


def _within(value: str, date_from: str | None, date_to: str | None) -> bool:
    parsed = _date_value(value)
    if date_from and (parsed is None or parsed < date.fromisoformat(date_from)):
        return False
    if date_to and (parsed is None or parsed > date.fromisoformat(date_to)):
        return False
    return True


def typed_search(
    root: Path,
    *,
    query: str | None = None,
    tags: list[str] | None = None,
    kinds: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    topic: str | None = None,
    project: str | None = None,
    person: str | None = None,
    origin: str | None = None,
    claim_status: str | None = None,
    type_: str | None = None,
    status: str | None = None,
    maturity: str | None = None,
    semantic_type: str | None = None,
    has_imports: bool = False,
    has_schema: bool = False,
) -> list[dict[str, Any]]:
    """Search captures, Topic revisions, and canonical atoms lexically."""
    from .index import load_index
    from .search import search

    requested = set(kinds or ("capture", "incubator_topic", "incubator_claim", "atom"))
    index = load_index(root)
    results: list[dict[str, Any]] = []
    for entry in index.personal_objects.values():
        if entry.kind not in requested:
            continue
        if claim_status:
            if entry.kind != "incubator_claim" or entry.metadata.get("claim_status") != claim_status:
                continue
        if tags and not all(tag in entry.tags for tag in tags):
            continue
        if topic and entry.topic != topic:
            continue
        if project and entry.project != project:
            continue
        if person and person not in entry.people:
            continue
        if origin and entry.origin != origin:
            continue
        if not _within(entry.timestamp, date_from, date_to):
            continue
        score = _lexical_score(
            query,
            id_=entry.id,
            summary=entry.summary,
            tags=entry.tags,
            body=entry.content,
        ) if query else 0.0
        if query and score == 0:
            continue
        dump = entry.model_dump(mode="json")
        dump["score"] = round(score, 3)
        dump["snippet"] = entry.content.replace("\n", " ")[:200]
        results.append(dump)

    if "atom" in requested:
        atoms = search(
            root,
            query=query,
            tags=tags,
            type_=type_,
            status=status,
            maturity=maturity,
            semantic_type=semantic_type,
            has_imports=has_imports,
            has_schema=has_schema,
        )
        for atom in atoms:
            if claim_status and atom.get("claim_status") != claim_status:
                continue
            if topic and atom.get("topic") != topic:
                continue
            if project and atom.get("project") != project:
                continue
            if person and person not in atom.get("people", []):
                continue
            if origin and atom.get("origin") != origin:
                continue
            timestamp = atom.get("updated") or atom.get("created") or ""
            if not _within(timestamp, date_from, date_to):
                continue
            atom["kind"] = "atom"
            atom["display_locator"] = atom.get("path", "")
            atom["read_action"] = "build"
            atom["timestamp"] = timestamp
            atom["metadata"] = {
                key: atom.get(key)
                for key in (
                    "type", "status", "maturity", "origin", "claim_status",
                    "topic", "project", "people", "created", "updated",
                )
            }
            results.append(atom)

    results.sort(key=lambda item: (-float(item.get("score", 0)), item.get("timestamp", ""), item["id"]), reverse=False)
    return results


def read_personal_object(root: Path, object_id: str) -> ObjectReadResult:
    """Read a Capture or Topic by stable ID; line numbers remain display-only."""
    from .index import load_index

    index: IndexData = load_index(root)
    entry = index.personal_objects.get(object_id)
    if entry is None:
        if object_id in index.memories:
            raise ValueError(f"'{object_id}' is a canonical atom; use build")
        raise KeyError(f"Personal object not found: {object_id}")
    path = root / entry.path
    if entry.kind == "capture":
        record = next((item for item in scan_capture_file(root, path).captures if item.id == object_id), None)
        if record is None:
            raise KeyError(f"Capture no longer resolves by stable ID: {object_id}")
        return ObjectReadResult(
            kind="capture",
            id=record.id,
            path=record.path,
            display_locator=record.display_locator,
            content=record.payload,
            metadata={
                "captured_at": record.captured_at,
                "actor": record.actor,
                "content_hash": record.content_hash,
            },
        )
    if entry.kind == "incubator_claim":
        topics = scan_topic_file(root, path).topics
        claim = next(
            (
                item
                for topic_item in topics
                for item in scan_claims_in_topic(root, topic_item).claims
                if item.claim_id == object_id
            ),
            None,
        )
        if claim is None:
            raise KeyError(f"Claim no longer resolves by stable ID: {object_id}")
        return ObjectReadResult(
            kind="incubator_claim",
            id=claim.claim_id,
            path=claim.path,
            display_locator=claim.display_locator,
            content=claim.content,
            metadata=claim.metadata,
        )
    topic = next((item for item in scan_topic_file(root, path).topics if item.revision_id == object_id), None)
    if topic is None:
        raise KeyError(f"Topic revision no longer resolves by stable ID: {object_id}")
    return ObjectReadResult(
        kind="incubator_topic",
        id=topic.revision_id,
        path=topic.path,
        display_locator=topic.display_locator,
        content=topic.content,
        metadata=topic.metadata,
    )
