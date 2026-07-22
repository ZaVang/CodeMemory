"""Owner-gated promotion and batch review for Personal Profile Topics."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator

from .core import compute_body_hash
from .index import reindex
from .personal_index import TopicRecord, scan_all_topics
from .profile import load_personal_profile


class ReviewAction(BaseModel):
    action: Literal["promote", "merge", "delete"]
    revision_id: str
    atom_id: str | None = None
    target_revision_id: str | None = None
    owner_confirmed: bool = False

    @model_validator(mode="after")
    def required_targets(self) -> "ReviewAction":
        if self.action == "promote" and not self.atom_id:
            raise ValueError("promote requires atom_id")
        if self.action == "merge" and not self.target_revision_id:
            raise ValueError("merge requires target_revision_id")
        return self


class ReviewBatchResult(BaseModel):
    promoted: list[str] = Field(default_factory=list)
    merged: list[str] = Field(default_factory=list)
    deleted: list[str] = Field(default_factory=list)


def _topic(root: Path, revision_id: str) -> TopicRecord:
    topic = next((item for item in scan_all_topics(root).topics if item.revision_id == revision_id), None)
    if topic is None:
        raise KeyError(f"Topic revision not found: {revision_id}")
    return topic


def _safe_atom_id(root: Path, atom_id: str) -> Path:
    profile = load_personal_profile(root)
    prefix = Path(profile.paths.canonical).as_posix().rstrip("/") + "/"
    normalized = Path(atom_id).as_posix().lstrip("/")
    if not normalized.startswith(prefix) or ".." in Path(normalized).parts:
        raise ValueError(f"canonical atom id must start with {prefix}")
    return root / f"{normalized}.md"


def promote_topic(
    root: Path,
    revision_id: str,
    atom_id: str,
    *,
    owner_confirmed: bool = False,
    now: datetime | None = None,
) -> Path:
    topic = _topic(root, revision_id)
    path = _safe_atom_id(root, atom_id)
    if path.exists():
        raise FileExistsError(f"canonical atom already exists: {atom_id}")
    derived = topic.metadata.get("derived_from", [])
    provenance = {
        "topic_id": topic.topic_id,
        "topic_revision_id": topic.revision_id,
        "topic_revision_hash": topic.metadata.get("content_hash") or topic.metadata.get("revision_hash"),
        "captures": derived if isinstance(derived, list) else [],
        "owner_confirmed": owner_confirmed,
    }
    instant = (now or datetime.now().astimezone()).date().isoformat()
    body = f"# {topic.title}\n\n{topic.content.strip()}\n"
    meta = {
        "type": "atom",
        "id": atom_id,
        "summary": topic.title,
        "status": "active" if owner_confirmed else "proposed",
        "created": instant,
        "updated": instant,
        "version": 1,
        "tags": topic.metadata.get("tags", []),
        "maturity": "draft",
        "origin": topic.metadata.get("origin", "mixed"),
        "topic": topic.topic_id,
        "provenance": provenance,
        "source": {"platform": "codememory-personal", "created_by": "agent"},
        "summary_hash": compute_body_hash(body.strip()),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n" + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True) + "---\n" + body,
        encoding="utf-8",
    )
    reindex(root)
    return path


def _remove_topic_section(root: Path, topic: TopicRecord) -> None:
    path = root / topic.path
    text = path.read_text(encoding="utf-8")
    headings = list(re.finditer(r"^## .+?$", text, re.MULTILINE))
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        segment = text[heading.start():end]
        if f"revision_id: {topic.revision_id}" in segment:
            updated = (text[:heading.start()] + text[end:]).rstrip() + "\n"
            path.write_text(updated, encoding="utf-8")
            return
    raise KeyError(f"Topic section no longer resolves: {topic.revision_id}")


def _replace_topic_section(root: Path, topic: TopicRecord, replacement: str) -> None:
    path = root / topic.path
    text = path.read_text(encoding="utf-8")
    headings = list(re.finditer(r"^## .+?$", text, re.MULTILINE))
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        segment = text[heading.start():end]
        if f"revision_id: {topic.revision_id}" in segment:
            path.write_text(text[:heading.start()] + replacement + text[end:].lstrip("\n"), encoding="utf-8")
            return
    raise KeyError(f"Topic section no longer resolves: {topic.revision_id}")


def merge_topics(root: Path, revision_id: str, target_revision_id: str) -> str:
    if revision_id == target_revision_id:
        raise ValueError("cannot merge a Topic revision into itself")
    source = _topic(root, revision_id)
    target = _topic(root, target_revision_id)
    if source.path != target.path:
        raise ValueError("Phase 1B merge requires Topics in the same monthly incubator file")
    merged_body = target.content.rstrip() + "\n\n" + source.content.rstrip()
    merged_hash = "sha256:" + hashlib.sha256(merged_body.encode("utf-8")).hexdigest()
    merged_revision = "rev_" + hashlib.sha256(
        f"{target.topic_id}\0{target.revision_id}\0{source.revision_id}\0{merged_hash}".encode("utf-8")
    ).hexdigest()[:20]
    meta = dict(target.metadata)
    meta["revision_id"] = merged_revision
    meta["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    meta["content_hash"] = merged_hash
    merged_from = list(meta.get("merged_from", [])) if isinstance(meta.get("merged_from"), list) else []
    merged_from.append({
        "topic_id": source.topic_id,
        "revision_id": source.revision_id,
        "content_hash": source.metadata.get("content_hash") or source.metadata.get("revision_hash"),
    })
    meta["merged_from"] = merged_from
    replacement = (
        f"## {target.title}\n<!-- codememory:topic\n"
        + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).rstrip()
        + f"\n-->\n{merged_body}\n\n"
    )
    _replace_topic_section(root, target, replacement)
    refreshed_source = next(item for item in scan_all_topics(root).topics if item.revision_id == source.revision_id)
    _remove_topic_section(root, refreshed_source)
    reindex(root)
    return merged_revision


def apply_review_batch(root: Path, actions: list[ReviewAction]) -> ReviewBatchResult:
    result = ReviewBatchResult()
    for action in actions:
        if action.action == "promote":
            promote_topic(
                root, action.revision_id, action.atom_id or "",
                owner_confirmed=action.owner_confirmed,
            )
            result.promoted.append(action.atom_id or "")
        elif action.action == "merge":
            result.merged.append(merge_topics(root, action.revision_id, action.target_revision_id or ""))
        else:
            topic = _topic(root, action.revision_id)
            _remove_topic_section(root, topic)
            result.deleted.append(action.revision_id)
    reindex(root)
    return result
