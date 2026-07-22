"""Append-only Capture storage for Personal Profile journals."""

from __future__ import annotations

import hashlib
import os
import re
import secrets
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml
from pydantic import BaseModel, Field

from .profile import load_personal_profile, validate_personal_profile


_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_CAPTURE_HEADING_RE = re.compile(
    r"^## (?P<time>\d{2}:\d{2}) — (?P<id>cap_[0-9A-HJKMNP-TV-Z]{26})\s*$",
    re.MULTILINE,
)
_CAPTURE_META_RE = re.compile(
    r"<!--\s*codememory:capture\s*\n(?P<meta>.*?)\n-->\n?",
    re.DOTALL,
)


class CaptureRecord(BaseModel):
    id: str
    captured_at: str
    actor: str
    content_hash: str
    payload: str
    path: str
    display_locator: str
    line: int


class CaptureScan(BaseModel):
    captures: list[CaptureRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def normalize_capture_payload(payload: str) -> str:
    return payload.replace("\r\n", "\n").replace("\r", "\n")


def capture_content_hash(payload: str) -> str:
    normalized = normalize_capture_payload(payload)
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def new_capture_id(now: datetime | None = None) -> str:
    """Return a time-sortable ULID with the Capture namespace prefix."""
    timestamp_ms = int((now or datetime.now().astimezone()).timestamp() * 1000)
    raw = timestamp_ms.to_bytes(6, "big") + secrets.token_bytes(10)
    value = int.from_bytes(raw, "big")
    chars = ["0"] * 26
    for index in range(25, -1, -1):
        chars[index] = _CROCKFORD[value & 31]
        value >>= 5
    return "cap_" + "".join(chars)


@contextmanager
def _instance_lock(lock_path: Path) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(lock_path, "a+b")
    try:
        if handle.tell() == 0 and lock_path.stat().st_size == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown Personal Profile timezone: {name}") from exc


def append_capture(
    root: Path,
    payload: str,
    *,
    actor: str | None = None,
    now: datetime | None = None,
) -> CaptureRecord:
    """Append one complete Capture block and fsync before returning."""
    validation = validate_personal_profile(root)
    if not validation.profile_valid or validation.profile is None:
        raise ValueError("Invalid Personal Profile: " + "; ".join(validation.errors))
    profile = validation.profile
    normalized = normalize_capture_payload(payload)
    instant = now.astimezone(_timezone(profile.timezone)) if now else datetime.now(_timezone(profile.timezone))
    capture_id = new_capture_id(instant)
    digest = capture_content_hash(normalized)
    journal_path = (
        root
        / profile.paths.journal
        / instant.strftime("%Y")
        / instant.strftime("%m")
        / f"{instant:%Y-%m-%d}.md"
    )
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "id": capture_id,
        "captured_at": instant.isoformat(timespec="seconds"),
        "actor": actor or profile.owner,
        "content_hash": digest,
    }
    comment = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).rstrip()
    block = (
        f"## {instant:%H:%M} — {capture_id}\n"
        f"<!-- codememory:capture\n{comment}\n-->\n"
        f"{normalized}\n\n"
    )

    with _instance_lock(root / ".codememory" / "capture.lock"):
        existing = journal_path.read_text(encoding="utf-8") if journal_path.exists() else ""
        if not existing:
            prefix = f"# {instant:%Y-%m-%d}\n\n"
        elif existing.endswith("\n\n"):
            prefix = ""
        elif existing.endswith("\n"):
            prefix = "\n"
        else:
            prefix = "\n\n"
        line = (existing + prefix).count("\n") + 1
        with open(journal_path, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(prefix + block)
            handle.flush()
            os.fsync(handle.fileno())

    rel_path = journal_path.relative_to(root).as_posix()
    return CaptureRecord(
        id=capture_id,
        captured_at=metadata["captured_at"],
        actor=metadata["actor"],
        content_hash=digest,
        payload=normalized,
        path=rel_path,
        display_locator=f"{rel_path}:{line}",
        line=line,
    )


def _recover_payload(raw: str, expected_hash: str) -> str:
    candidates = [raw]
    if raw.endswith("\n\n"):
        candidates.insert(0, raw[:-2])
    if raw.endswith("\n"):
        candidates.append(raw[:-1])
    for candidate in candidates:
        if capture_content_hash(candidate) == expected_hash:
            return candidate
    return raw[:-2] if raw.endswith("\n\n") else raw


def scan_capture_file(root: Path, path: Path) -> CaptureScan:
    text = path.read_text(encoding="utf-8")
    matches = list(_CAPTURE_HEADING_RE.finditer(text))
    result = CaptureScan()
    rel_path = path.relative_to(root).as_posix()
    for index, heading in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        segment = text[heading.end():end]
        meta_match = _CAPTURE_META_RE.search(segment)
        line = text.count("\n", 0, heading.start()) + 1
        if meta_match is None:
            result.warnings.append(f"incomplete Capture ignored: {rel_path}:{line}")
            continue
        try:
            metadata = yaml.safe_load(meta_match.group("meta")) or {}
            if metadata.get("id") != heading.group("id"):
                raise ValueError("heading id does not match metadata id")
            expected_hash = str(metadata["content_hash"])
            payload = _recover_payload(segment[meta_match.end():], expected_hash)
            if capture_content_hash(payload) != expected_hash:
                result.warnings.append(f"Capture hash mismatch: {heading.group('id')}")
                continue
            result.captures.append(CaptureRecord(
                id=heading.group("id"),
                captured_at=str(metadata["captured_at"]),
                actor=str(metadata.get("actor", "owner")),
                content_hash=expected_hash,
                payload=payload,
                path=rel_path,
                display_locator=f"{rel_path}:{line}",
                line=line,
            ))
        except (KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
            result.warnings.append(f"invalid Capture ignored: {rel_path}:{line}: {exc}")
    marker_count = text.count("codememory:capture")
    if marker_count > len(matches):
        result.warnings.append(f"incomplete trailing Capture metadata ignored: {rel_path}")
    return result


def scan_all_captures(root: Path) -> CaptureScan:
    profile = load_personal_profile(root)
    result = CaptureScan()
    journal = root / profile.paths.journal
    if not journal.exists():
        return result
    for path in sorted(journal.rglob("*.md")):
        scanned = scan_capture_file(root, path)
        result.captures.extend(scanned.captures)
        result.warnings.extend(scanned.warnings)
    return result
