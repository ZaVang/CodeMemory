"""Sensitive-scanned, idempotent Git delivery for maintenance runs."""

from __future__ import annotations

import math
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from .capture import _instance_lock
from .maintenance import (
    MaintenanceEvent,
    MaintenanceState,
    append_maintenance_event,
    load_maintenance_events,
    load_maintenance_state,
    save_maintenance_state,
)
from .profile import load_personal_profile


class ScanFinding(BaseModel):
    rule: str
    path: str
    locator: str


class DeliveryResult(BaseModel):
    run_id: str
    stage: Literal[
        "disabled", "unavailable", "blocked", "scan_blocked", "committed", "pushed"
    ]
    commit: str | None = None
    findings: list[ScanFinding] = Field(default_factory=list)
    detail: str | None = None


_SECRET_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("github_token", re.compile(r"(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("generic_secret", re.compile(r"(?i)(?:password|secret|token|api[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}")),
)
_ENTROPY_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9+/=_-])[A-Za-z0-9+/=_-]{32,}(?![A-Za-z0-9+/=_-])")
_HEX_DIGEST_RE = re.compile(r"[0-9a-fA-F]{32,}")
_HIGH_ENTROPY_THRESHOLD = 4.5


def _git(root: Path, *args: str, timeout: int = 20) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True,
            encoding="utf-8", errors="replace", check=False, timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(["git", *args], 127, "", str(exc))


def _instance_is_repo_root(root: Path) -> bool:
    result = _git(root, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        return False
    try:
        return Path(result.stdout.strip()).resolve() == root.resolve()
    except OSError:
        return False


def _allowed_prefixes(root: Path) -> tuple[set[str], tuple[str, ...], tuple[str, ...]]:
    profile = load_personal_profile(root)
    exact = {
        ".gitignore", "README.md", ".codememory/profile.yaml",
        ".codememory/maintenance/runs.jsonl", ".codememory/log.md",
    }
    directories = tuple(
        Path(value).as_posix().rstrip("/") + "/"
        for value in (
            profile.paths.journal, profile.paths.incubator,
            profile.paths.canonical, profile.paths.reviews,
        )
    )
    excluded = (
        Path(profile.paths.private_local).as_posix().rstrip("/") + "/",
        ".codememory/maintenance/state.json",
        ".codememory/maintenance/pending/",
        ".codememory/maintenance/maintenance.lock",
        ".codememory/capture.lock",
        ".codememory/index.json",
    )
    return exact, directories, excluded


def _is_allowed(path: str, exact: set[str], directories: tuple[str, ...]) -> bool:
    normalized = Path(path).as_posix()
    return normalized in exact or any(normalized.startswith(prefix) for prefix in directories)


def _is_runtime(path: str, excluded: tuple[str, ...]) -> bool:
    normalized = Path(path).as_posix()
    return any(normalized == prefix or normalized.startswith(prefix) for prefix in excluded)


def _changed_paths(root: Path) -> list[str]:
    result = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if result.returncode != 0:
        raise RuntimeError("unable to inspect Git working tree")
    paths: list[str] = []
    entries = result.stdout.split("\0")
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if len(entry) < 4:
            continue
        status = entry[:2]
        paths.append(entry[3:])
        if "R" in status or "C" in status:
            if index < len(entries) and entries[index]:
                paths.append(entries[index])
            index += 1
    return paths


def _staged_paths(root: Path) -> list[str]:
    result = _git(root, "diff", "--cached", "--name-only", "-z", "--no-ext-diff")
    return [path for path in result.stdout.split("\0") if path]


def _shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    return -sum(
        (count / len(value)) * math.log2(count / len(value))
        for count in {character: value.count(character) for character in set(value)}.values()
    )


def _contains_high_entropy_token(value: str) -> bool:
    for match in _ENTROPY_TOKEN_RE.finditer(value):
        candidate = match.group(0)
        if _HEX_DIGEST_RE.fullmatch(candidate):
            continue
        if _shannon_entropy(candidate) >= _HIGH_ENTROPY_THRESHOLD:
            return True
    return False


def _scan_staged_diff(root: Path) -> list[ScanFinding]:
    result = _git(
        root, "-c", "core.quotePath=false", "diff", "--cached",
        "--unified=0", "--no-ext-diff", "--no-color",
    )
    if result.returncode != 0:
        raise RuntimeError("unable to scan staged Git diff")
    findings: list[ScanFinding] = []
    path = "(unknown)"
    new_line = 0
    for line in result.stdout.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
            continue
        if line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            new_line = int(match.group(1)) if match else 0
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        value = line[1:]
        for name, pattern in _SECRET_RULES:
            if pattern.search(value):
                findings.append(ScanFinding(rule=name, path=path, locator=f"{path}:{new_line}"))
        if _contains_high_entropy_token(value):
            findings.append(ScanFinding(rule="high_entropy", path=path, locator=f"{path}:{new_line}"))
        new_line += 1
    return findings


def _run_event(root: Path, run_id: str) -> MaintenanceEvent:
    event = next((item for item in reversed(load_maintenance_events(root)) if item.run_id == run_id), None)
    if event is None:
        raise KeyError(f"maintenance run not found: {run_id}")
    return event


def _find_commit(root: Path, run_id: str) -> str | None:
    result = _git(root, "log", "--all", "--format=%H", "--grep", f"^CodeMemory-Run: {run_id}$", "-n", "1")
    value = result.stdout.strip()
    return value or None


def _unstage(root: Path, paths: list[str]) -> None:
    if paths:
        _git(root, "reset", "-q", "HEAD", "--", *paths)


def _deliver_maintenance_locked(root: Path, run_id: str | None = None) -> DeliveryResult:
    profile = load_personal_profile(root)
    state = load_maintenance_state(root)
    selected = run_id or state.active_run_id
    if not selected:
        raise RuntimeError("no maintenance run is awaiting delivery")
    if state.active_run_id and selected != state.active_run_id:
        return DeliveryResult(
            run_id=selected,
            stage="blocked",
            detail=f"active maintenance run {state.active_run_id} must finish first",
        )
    if not profile.maintenance.auto_commit:
        return DeliveryResult(run_id=selected, stage="disabled", detail="auto_commit is false")
    if not _instance_is_repo_root(root):
        return DeliveryResult(run_id=selected, stage="unavailable", detail="instance is not a Git repository root")
    if _git(root, "remote", "get-url", profile.maintenance.remote).returncode != 0:
        return DeliveryResult(run_id=selected, stage="unavailable", detail="configured remote is missing")

    event = _run_event(root, selected)
    existing_commit = state.delivery_commit or _find_commit(root, selected)
    if existing_commit:
        state.active_run_id = selected
        state.active_stage = "scan_passed"
        state.delivery_commit = existing_commit
        if not profile.maintenance.auto_push:
            state.delivery_pushed = False
            save_maintenance_state(root, MaintenanceState())
            return DeliveryResult(run_id=selected, stage="committed", commit=existing_commit)
        pushed = _git(
            root, "push", profile.maintenance.remote,
            f"{existing_commit}:refs/heads/{profile.maintenance.branch}", timeout=60,
        )
        if pushed.returncode != 0:
            save_maintenance_state(root, state)
            return DeliveryResult(run_id=selected, stage="committed", commit=existing_commit, detail="push failed; retry will reuse this commit")
        state.delivery_pushed = True
        save_maintenance_state(root, MaintenanceState())
        return DeliveryResult(run_id=selected, stage="pushed", commit=existing_commit)

    exact, directories, excluded = _allowed_prefixes(root)
    existing_staged = _staged_paths(root)
    if existing_staged:
        return DeliveryResult(run_id=selected, stage="blocked", detail="working tree already has staged changes")
    changed = _changed_paths(root)
    unknown = [path for path in changed if not _is_allowed(path, exact, directories) and not _is_runtime(path, excluded)]
    if unknown:
        return DeliveryResult(run_id=selected, stage="blocked", detail="unknown changes outside Personal Profile delivery paths: " + ", ".join(sorted(unknown)))
    stage_paths = [path for path in changed if _is_allowed(path, exact, directories)]
    if not stage_paths:
        return DeliveryResult(run_id=selected, stage="blocked", detail="no deliverable Personal Profile changes")
    staged = _git(root, "add", "--", *stage_paths)
    if staged.returncode != 0:
        return DeliveryResult(run_id=selected, stage="blocked", detail="unable to stage Personal Profile changes")
    findings = _scan_staged_diff(root)
    if findings:
        _unstage(root, stage_paths)
        instant = datetime.now().astimezone().isoformat(timespec="seconds")
        append_maintenance_event(root, MaintenanceEvent(
            run_id=selected, stage="scan_blocked", input_digest=event.input_digest,
            capture_ids=event.capture_ids, capture_hashes=event.capture_hashes,
            occurred_at=instant,
            detail={"findings": [finding.model_dump(mode="json") for finding in findings]},
        ))
        save_maintenance_state(root, MaintenanceState(active_run_id=selected, active_stage="scan_blocked"))
        return DeliveryResult(run_id=selected, stage="scan_blocked", findings=findings)

    instant = datetime.now().astimezone().isoformat(timespec="seconds")
    append_maintenance_event(root, MaintenanceEvent(
        run_id=selected, stage="scan_passed", input_digest=event.input_digest,
        capture_ids=event.capture_ids, capture_hashes=event.capture_hashes,
        occurred_at=instant,
    ))
    # The scan_passed ledger event must be included in this single delivery commit.
    _git(root, "add", "--", ".codememory/maintenance/runs.jsonl")
    commit = _git(
        root, "commit", "-m", "chore(memory): maintain personal profile",
        "-m", f"CodeMemory-Run: {selected}",
    )
    if commit.returncode != 0:
        _unstage(root, _staged_paths(root))
        return DeliveryResult(run_id=selected, stage="blocked", detail="Git commit failed")
    commit_hash = _git(root, "rev-parse", "HEAD").stdout.strip()
    state = MaintenanceState(
        active_run_id=selected,
        active_stage="scan_passed",
        delivery_commit=commit_hash,
        delivery_pushed=False,
    )
    save_maintenance_state(root, state)
    if not profile.maintenance.auto_push:
        save_maintenance_state(root, MaintenanceState())
        return DeliveryResult(run_id=selected, stage="committed", commit=commit_hash)
    pushed = _git(
        root, "push", profile.maintenance.remote,
        f"{commit_hash}:refs/heads/{profile.maintenance.branch}", timeout=60,
    )
    if pushed.returncode != 0:
        return DeliveryResult(run_id=selected, stage="committed", commit=commit_hash, detail="push failed; retry will reuse this commit")
    save_maintenance_state(root, MaintenanceState())
    return DeliveryResult(run_id=selected, stage="pushed", commit=commit_hash)


def deliver_maintenance(root: Path, run_id: str | None = None) -> DeliveryResult:
    with _instance_lock(root / ".codememory" / "maintenance" / "maintenance.lock"):
        return _deliver_maintenance_locked(root, run_id)
