"""Source Artifact registry primitives.

Source Artifacts preserve original documents and external materials without
turning them into memory atoms.  Atoms can later point at these records via
``source_refs`` while imports remain atom-to-atom dependency edges.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Literal
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from pydantic import BaseModel, Field, field_validator


SourceKind = Literal["markdown", "code", "text", "pdf", "url", "external"]
SourceStatus = Literal["active", "archived", "missing", "stale"]
SourceCheckState = Literal["fresh", "missing", "stale", "external"]
SourceExpansionStatus = Literal["fresh", "stale", "missing", "unsupported"]


class SourceArtifact(BaseModel):
    """Metadata for an original source document or external material."""

    id: str
    kind: SourceKind
    uri: str
    sha256: str = ""
    summary: str = ""
    status: SourceStatus = "active"

    @field_validator("id", "uri")
    @classmethod
    def _require_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class SourceRegistry(BaseModel):
    """The ``.codememory/sources/index.json`` registry."""

    version: int = 1
    updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    sources: dict[str, SourceArtifact] = Field(default_factory=dict)


class SourceArtifactCheck(BaseModel):
    """Health check result for a Source Artifact."""

    artifact_id: str
    state: SourceCheckState
    uri: str
    expected_sha256: str = ""
    current_sha256: str | None = None
    message: str = ""


class SourceExpansion(BaseModel):
    """Explicit source expansion result for progressive disclosure workflows."""

    artifact_id: str
    status: SourceExpansionStatus
    kind: SourceKind | None = None
    uri: str = ""
    path: str | None = None
    sha256: str = ""
    current_sha256: str | None = None
    content: str = ""
    range_start: int | None = None
    range_end: int | None = None
    truncated: bool = False
    message: str = ""


def get_sources_index_path(root_dir: Path) -> Path:
    """Return the canonical source registry path."""

    return root_dir / ".codememory" / "sources" / "index.json"


def load_source_registry(root_dir: Path) -> SourceRegistry:
    """Load source registry, returning an empty registry when missing/invalid."""

    path = get_sources_index_path(root_dir)
    if not path.exists():
        return SourceRegistry()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return SourceRegistry.model_validate(raw)
    except Exception:
        return SourceRegistry()


def save_source_registry(root_dir: Path, registry: SourceRegistry) -> None:
    """Persist source registry to ``.codememory/sources/index.json``."""

    path = get_sources_index_path(root_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    registry.updated = datetime.now().isoformat()
    path.write_text(
        json.dumps(registry.model_dump(mode="json"), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def compute_file_sha256(path: Path) -> str:
    """Compute full SHA-256 hex digest for a local source file."""

    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_source_uri(root_dir: Path, uri: str) -> Path | None:
    """Resolve a local source URI relative to a memory root.

    URL-like or external URIs return ``None`` because they cannot be checked by
    local file hashing.
    """

    direct_path = Path(uri)
    if direct_path.is_absolute():
        return direct_path

    parsed = urlparse(uri)
    scheme = parsed.scheme.lower()
    if scheme and scheme != "file":
        return None
    if scheme == "file":
        raw_path = unquote(parsed.path)
        if parsed.netloc:
            raw_path = f"//{parsed.netloc}{raw_path}"
        path = Path(url2pathname(raw_path))
        if path.is_absolute():
            return path
        return root_dir / path
    path = Path(uri)
    if path.is_absolute():
        return path
    return root_dir / path


def _resolve_source_uri_for_expansion(root_dir: Path, uri: str) -> Path | None:
    """Resolve a local source URI for expansion without allowing root escape.

    Absolute paths are allowed because a registry may intentionally preserve
    sources outside the memory dataset. Relative paths are resolved under the
    memory root and must remain inside it.
    """

    path = resolve_source_uri(root_dir, uri)
    if path is None:
        return None
    parsed = urlparse(uri)
    original = Path(url2pathname(unquote(parsed.path))) if parsed.scheme.lower() == "file" else Path(uri)
    if not original.is_absolute():
        try:
            path.resolve().relative_to(root_dir.resolve())
        except ValueError:
            return None
    return path


def infer_source_kind(uri: str) -> SourceKind:
    """Infer a conservative SourceKind from URI suffix."""

    lowered = uri.lower()
    if lowered.startswith(("http://", "https://")):
        return "url"
    suffix = Path(uri).suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix in {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".cpp", ".c", ".h"}:
        return "code"
    if suffix == ".pdf":
        return "pdf"
    if suffix in {".txt", ".rst"}:
        return "text"
    return "external"


def _default_source_id(uri: str) -> str:
    digest = hashlib.sha1(uri.encode("utf-8")).hexdigest()[:12]
    stem = Path(uri).stem.lower() or "source"
    safe_stem = "".join(ch if ch.isalnum() else "-" for ch in stem).strip("-")
    safe_stem = safe_stem or "source"
    return f"src/{safe_stem}-{digest}"


def add_source_artifact(
    root_dir: Path,
    uri: str,
    source_id: str | None = None,
    kind: SourceKind | None = None,
    summary: str = "",
    status: SourceStatus = "active",
) -> SourceArtifact:
    """Create or replace a Source Artifact in the registry."""

    local_path = resolve_source_uri(root_dir, uri)
    sha256 = compute_file_sha256(local_path) if local_path is not None and local_path.exists() else ""
    artifact = SourceArtifact(
        id=source_id or _default_source_id(uri),
        kind=kind or infer_source_kind(uri),
        uri=uri,
        sha256=sha256,
        summary=summary,
        status=status,
    )
    registry = load_source_registry(root_dir)
    registry.sources[artifact.id] = artifact
    save_source_registry(root_dir, registry)
    return artifact


def list_source_artifacts(root_dir: Path) -> list[SourceArtifact]:
    """Return all Source Artifacts sorted by id."""

    registry = load_source_registry(root_dir)
    return [registry.sources[key] for key in sorted(registry.sources)]


def get_source_artifact(root_dir: Path, source_id: str) -> SourceArtifact | None:
    """Return a Source Artifact by id, or ``None`` when absent."""

    return load_source_registry(root_dir).sources.get(source_id)


def check_source_artifact(root_dir: Path, artifact: SourceArtifact) -> SourceArtifactCheck:
    """Detect whether a Source Artifact is fresh, missing, stale, or external."""

    local_path = resolve_source_uri(root_dir, artifact.uri)
    if local_path is None:
        return SourceArtifactCheck(
            artifact_id=artifact.id,
            state="external",
            uri=artifact.uri,
            expected_sha256=artifact.sha256,
            message="external source cannot be checked by local file hashing",
        )
    if not local_path.exists():
        return SourceArtifactCheck(
            artifact_id=artifact.id,
            state="missing",
            uri=artifact.uri,
            expected_sha256=artifact.sha256,
            message=f"source file not found: {artifact.uri}",
        )
    current = compute_file_sha256(local_path)
    if artifact.sha256 and current != artifact.sha256:
        return SourceArtifactCheck(
            artifact_id=artifact.id,
            state="stale",
            uri=artifact.uri,
            expected_sha256=artifact.sha256,
            current_sha256=current,
            message="source file hash differs from registry",
        )
    return SourceArtifactCheck(
        artifact_id=artifact.id,
        state="fresh",
        uri=artifact.uri,
        expected_sha256=artifact.sha256,
        current_sha256=current,
    )


def check_source_registry(root_dir: Path) -> list[SourceArtifactCheck]:
    """Check every Source Artifact in the registry."""

    return [check_source_artifact(root_dir, artifact) for artifact in list_source_artifacts(root_dir)]


def _display_source_path(root_dir: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root_dir.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def _apply_text_window(
    text: str,
    start: int | None = None,
    end: int | None = None,
    max_chars: int | None = None,
) -> tuple[str, int, int, bool]:
    full_len = len(text)
    range_start = max(start or 0, 0)
    range_start = min(range_start, full_len)
    range_end = full_len if end is None else max(end, range_start)
    range_end = min(range_end, full_len)
    if max_chars is not None:
        max_chars = max(max_chars, 0)
        range_end = min(range_end, range_start + max_chars)
    content = text[range_start:range_end]
    truncated = range_start != 0 or range_end != full_len
    return content, range_start, range_end, truncated


def expand_source_artifact(
    root_dir: Path,
    source_id: str,
    start: int | None = None,
    end: int | None = None,
    max_chars: int | None = None,
) -> SourceExpansion:
    """Return source text or a structured notice for a Source Artifact.

    This is the explicit expansion step for progressive disclosure. ContextPack
    can expose ``source_refs`` without source bodies; callers use this function
    when they intentionally need the backing source text.
    """

    artifact = get_source_artifact(root_dir, source_id)
    if artifact is None:
        return SourceExpansion(
            artifact_id=source_id,
            status="missing",
            message=f"Source Artifact '{source_id}' not found.",
        )

    base = {
        "artifact_id": artifact.id,
        "kind": artifact.kind,
        "uri": artifact.uri,
        "sha256": artifact.sha256,
    }

    if artifact.kind not in {"markdown", "code", "text"}:
        return SourceExpansion(
            **base,
            status="unsupported",
            message=f"Source Artifact kind '{artifact.kind}' cannot be expanded as local text.",
        )

    local_path = _resolve_source_uri_for_expansion(root_dir, artifact.uri)
    if local_path is None:
        return SourceExpansion(
            **base,
            status="unsupported",
            message="Source Artifact URI is not a safe local file path.",
        )

    path_display = _display_source_path(root_dir, local_path)
    if not local_path.exists():
        return SourceExpansion(
            **base,
            path=path_display,
            status="missing",
            message=f"source file not found: {artifact.uri}",
        )

    current_sha256 = compute_file_sha256(local_path)
    status: SourceExpansionStatus = (
        "stale" if artifact.sha256 and current_sha256 != artifact.sha256 else "fresh"
    )
    message = "source file hash differs from registry" if status == "stale" else ""

    try:
        text = local_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return SourceExpansion(
            **base,
            path=path_display,
            status="unsupported",
            current_sha256=current_sha256,
            message="source file is not valid UTF-8 text",
        )
    except OSError as exc:
        return SourceExpansion(
            **base,
            path=path_display,
            status="missing",
            current_sha256=current_sha256,
            message=f"source file could not be read: {exc}",
        )

    content, range_start, range_end, truncated = _apply_text_window(text, start=start, end=end, max_chars=max_chars)

    return SourceExpansion(
        **base,
        path=path_display,
        status=status,
        current_sha256=current_sha256,
        content=content,
        range_start=range_start,
        range_end=range_end,
        truncated=truncated,
        message=message,
    )
