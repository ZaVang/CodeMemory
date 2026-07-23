"""Optional local semantic discovery index for Personal Profiles.

The index is derived, private-local state. It only ranks typed discovery
candidates and is never read by canonical build.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, Field

from .core import parse_frontmatter
from .index import load_index
from .models import NON_ASSEMBLABLE_STATUSES
from .profile import PersonalProfile, load_personal_profile, resolve_private_local_root


class SemanticEmbedder(Protocol):
    model_id: str
    fingerprint: str

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text."""


class SemanticRecord(BaseModel):
    key: str
    kind: str
    id: str
    summary: str
    snippet: str
    path: str
    display_locator: str
    read_action: str
    content_sha256: str
    vector: list[float]


class SemanticIndex(BaseModel):
    format_version: str = "personal-semantic/v1"
    model_id: str
    model_fingerprint: str
    dimensions: int
    input_sha256: str
    records: list[SemanticRecord] = Field(default_factory=list)


class SemanticBuildResult(BaseModel):
    status: str
    records: int
    input_sha256: str
    model_id: str


class SemanticStatus(BaseModel):
    enabled: bool
    configured: bool
    index_status: str
    records: int = 0
    model_id: str | None = None


class SemanticSearchResult(BaseModel):
    kind: str
    id: str
    summary: str
    score: float
    snippet: str
    path: str
    display_locator: str
    read_action: str


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def semantic_index_path(root: Path, profile: PersonalProfile | None = None) -> Path:
    profile = profile or load_personal_profile(root)
    private_root = resolve_private_local_root(root, profile)
    path = (private_root / "semantic" / "index.json").resolve()
    path.relative_to(private_root)
    return path


def _safe_path(root: Path, relative: str, object_id: str) -> Path:
    resolved_root = root.resolve()
    path = (resolved_root / relative).resolve()
    try:
        path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"indexed path escapes root: {object_id}") from exc
    if not path.is_file():
        raise FileNotFoundError(f"indexed object missing: {object_id}")
    return path


def _source_documents(root: Path) -> list[dict[str, str]]:
    index = load_index(root)
    documents: list[dict[str, str]] = []
    for entry in index.personal_objects.values():
        documents.append({
            "key": f"{entry.kind}:{entry.id}",
            "kind": entry.kind,
            "id": entry.id,
            "summary": entry.summary,
            "content": entry.content,
            "path": entry.path,
            "display_locator": entry.display_locator,
            "read_action": "read",
        })
    for memory_id, entry in index.memories.items():
        if entry.status in NON_ASSEMBLABLE_STATUSES or entry.type not in ("atom", "schema"):
            continue
        path = _safe_path(root, entry.path, memory_id)
        _meta, body = parse_frontmatter(path)
        documents.append({
            "key": f"atom:{memory_id}",
            "kind": "atom",
            "id": memory_id,
            "summary": entry.summary,
            "content": body.strip(),
            "path": entry.path,
            "display_locator": entry.path,
            "read_action": "build",
        })
    documents.sort(key=lambda item: item["key"])
    return documents


def _document_text(item: dict[str, str]) -> str:
    return f"{item['id']}\n{item['summary']}\n{item['content']}".strip()


def _input_digest(documents: list[dict[str, str]]) -> str:
    payload = [
        {"key": item["key"], "summary": item["summary"], "content": item["content"]}
        for item in documents
    ]
    return _sha(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        raise ValueError("embedding vector has zero norm")
    return [value / norm for value in vector]


def _load(path: Path) -> SemanticIndex:
    index = SemanticIndex.model_validate_json(path.read_text(encoding="utf-8"))
    if index.records and index.dimensions < 1:
        raise ValueError("semantic index has invalid dimensions")
    if any(len(record.vector) != index.dimensions for record in index.records):
        raise ValueError("semantic index record dimension mismatch")
    if any(
        not math.isfinite(value)
        for record in index.records
        for value in record.vector
    ):
        raise ValueError("semantic index contains non-finite vectors")
    return index


def _write_atomic(path: Path, index: SemanticIndex) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temp.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(index.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _require_enabled(root: Path) -> PersonalProfile:
    profile = load_personal_profile(root)
    semantic = profile.discovery.semantic
    if not semantic.enabled:
        raise ValueError("semantic discovery is disabled in Personal Profile")
    if semantic.external_embeddings:
        raise ValueError("external embeddings are not supported")
    if not semantic.model_path or not semantic.model_id:
        raise ValueError("semantic discovery model is not configured")
    return profile


def build_semantic_index(root: Path, embedder: SemanticEmbedder) -> SemanticBuildResult:
    profile = _require_enabled(root)
    if embedder.model_id != profile.discovery.semantic.model_id:
        raise ValueError("embedder model_id does not match Personal Profile")
    documents = _source_documents(root)
    digest = _input_digest(documents)
    path = semantic_index_path(root, profile)
    if path.exists():
        existing = _load(path)
        if existing.input_sha256 == digest and existing.model_fingerprint == embedder.fingerprint:
            return SemanticBuildResult(
                status="reused", records=len(existing.records),
                input_sha256=digest, model_id=embedder.model_id,
            )
    vectors = embedder.embed([_document_text(item) for item in documents])
    if len(vectors) != len(documents):
        raise ValueError("embedder returned the wrong number of vectors")
    normalized = [_normalize([float(value) for value in vector]) for vector in vectors]
    dimensions = len(normalized[0]) if normalized else 0
    if any(len(vector) != dimensions for vector in normalized):
        raise ValueError("embedding dimensions are inconsistent")
    records = [
        SemanticRecord(
            key=item["key"], kind=item["kind"], id=item["id"],
            summary=item["summary"], snippet=item["content"].replace("\n", " ")[:200],
            path=item["path"], display_locator=item["display_locator"],
            read_action=item["read_action"],
            content_sha256=_sha(_document_text(item)), vector=vector,
        )
        for item, vector in zip(documents, normalized)
    ]
    semantic_index = SemanticIndex(
        model_id=embedder.model_id,
        model_fingerprint=embedder.fingerprint,
        dimensions=dimensions,
        input_sha256=digest,
        records=records,
    )
    _write_atomic(path, semantic_index)
    return SemanticBuildResult(
        status="built", records=len(records), input_sha256=digest, model_id=embedder.model_id,
    )


def semantic_status(root: Path) -> SemanticStatus:
    profile = load_personal_profile(root)
    semantic = profile.discovery.semantic
    path = semantic_index_path(root, profile)
    if not semantic.enabled:
        return SemanticStatus(enabled=False, configured=False, index_status="disabled")
    configured = bool(semantic.model_path and semantic.model_id)
    if not path.exists():
        return SemanticStatus(enabled=True, configured=configured, index_status="missing", model_id=semantic.model_id)
    try:
        index = _load(path)
        current = _input_digest(_source_documents(root))
    except Exception:
        return SemanticStatus(enabled=True, configured=configured, index_status="invalid", model_id=semantic.model_id)
    return SemanticStatus(
        enabled=True, configured=configured,
        index_status="ready" if current == index.input_sha256 else "stale",
        records=len(index.records), model_id=index.model_id,
    )


def semantic_search(
    root: Path,
    query: str,
    embedder: SemanticEmbedder,
    *,
    limit: int = 10,
    kinds: list[str] | None = None,
) -> list[SemanticSearchResult]:
    profile = _require_enabled(root)
    path = semantic_index_path(root, profile)
    if not path.is_file():
        raise ValueError("semantic index is missing; build it first")
    index = _load(path)
    if index.model_id != embedder.model_id or index.model_fingerprint != embedder.fingerprint:
        raise ValueError("semantic index model is stale; rebuild it")
    if index.input_sha256 != _input_digest(_source_documents(root)):
        raise ValueError("semantic index content is stale; rebuild it")
    query_vectors = embedder.embed([query])
    if len(query_vectors) != 1:
        raise ValueError("embedder returned an invalid query vector")
    query_vector = _normalize([float(value) for value in query_vectors[0]])
    if len(query_vector) != index.dimensions:
        raise ValueError("query embedding dimension does not match semantic index")
    requested = set(kinds or ())
    results: list[SemanticSearchResult] = []
    for record in index.records:
        if requested and record.kind not in requested:
            continue
        score = sum(left * right for left, right in zip(query_vector, record.vector))
        results.append(SemanticSearchResult(
            kind=record.kind, id=record.id, summary=record.summary,
            score=round(score, 6), snippet=record.snippet,
            path=record.path, display_locator=record.display_locator,
            read_action=record.read_action,
        ))
    results.sort(key=lambda item: (-item.score, item.kind, item.id))
    return results[:max(1, limit)]
