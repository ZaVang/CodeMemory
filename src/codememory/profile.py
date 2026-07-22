"""Personal Profile initialization and validation.

Git delivery is deliberately represented as an optional capability.  Profile
initialization and capture remain valid in ordinary, non-Git directories.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PROFILE_RELATIVE_PATH = Path(".codememory/profile.yaml")
RUNTIME_IGNORE_RULES = (
    ".codememory/capture.lock",
    ".codememory/maintenance/state.json",
    ".codememory/maintenance/pending/",
)


class ProfilePaths(BaseModel):
    journal: str = "journal"
    incubator: str = "incubator"
    canonical: str = "memory"
    reviews: str = "reviews"
    private_local: str = "private-local"

    @model_validator(mode="after")
    def paths_stay_inside_instance(self) -> "ProfilePaths":
        values = [self.journal, self.incubator, self.canonical, self.reviews, self.private_local]
        for value in values:
            path = Path(value)
            if not value or path.is_absolute() or ".." in path.parts:
                raise ValueError(f"profile path must stay inside the instance: {value!r}")
        if len(set(values)) != len(values):
            raise ValueError("profile paths must be distinct")
        return self


class CaptureConfig(BaseModel):
    append_only_for_agents: bool = True
    hash: Literal["sha256"] = "sha256"


class MaintenanceConfig(BaseModel):
    auto_commit: bool = False
    auto_push: bool = False
    remote: str = "origin"
    branch: str = "main"
    sensitive_scan: Literal["required"] = "required"

    @model_validator(mode="after")
    def push_requires_commit(self) -> "MaintenanceConfig":
        if self.auto_push and not self.auto_commit:
            raise ValueError("maintenance.auto_push=true requires auto_commit=true")
        return self


class SemanticConfig(BaseModel):
    enabled: bool = False
    external_embeddings: bool = False


class DiscoveryConfig(BaseModel):
    lexical: bool = True
    temporal: bool = True
    tags: bool = True
    semantic: SemanticConfig = Field(default_factory=SemanticConfig)


class PersonalProfile(BaseModel):
    format_version: Literal[1] = 1
    profile: Literal["personal"] = "personal"
    owner: str = "owner"
    timezone: str = "Asia/Hong_Kong"
    paths: ProfilePaths = Field(default_factory=ProfilePaths)
    capture: CaptureConfig = Field(default_factory=CaptureConfig)
    maintenance: MaintenanceConfig = Field(default_factory=MaintenanceConfig)
    discovery: DiscoveryConfig = Field(default_factory=DiscoveryConfig)


class GitDeliveryStatus(BaseModel):
    status: Literal["available", "unavailable"]
    reason: Literal["not_git_repo", "remote_missing"] | None = None
    enabled: bool = False


class ProfileValidationResult(BaseModel):
    profile_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    git_delivery: GitDeliveryStatus
    profile: PersonalProfile | None = None


def required_ignore_rules(profile: PersonalProfile) -> tuple[str, ...]:
    private_path = Path(profile.paths.private_local).as_posix().rstrip("/") + "/"
    return (private_path, *RUNTIME_IGNORE_RULES)


def _run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    command = ["git", "-C", str(root), *args]
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(command, 127, "", str(exc))


def _git_delivery_status(root: Path, profile: PersonalProfile) -> GitDeliveryStatus:
    enabled = profile.maintenance.auto_commit or profile.maintenance.auto_push
    inside = _run_git(root, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return GitDeliveryStatus(status="unavailable", reason="not_git_repo", enabled=enabled)
    remote = _run_git(root, "remote", "get-url", profile.maintenance.remote)
    if remote.returncode != 0:
        return GitDeliveryStatus(status="unavailable", reason="remote_missing", enabled=enabled)
    return GitDeliveryStatus(status="available", enabled=enabled)


def load_personal_profile(root: Path) -> PersonalProfile:
    profile_path = root / PROFILE_RELATIVE_PATH
    if not profile_path.exists():
        raise FileNotFoundError(f"Personal Profile not found: {profile_path}")
    raw = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    return PersonalProfile.model_validate(raw)


def validate_personal_profile(root: Path) -> ProfileValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    profile: PersonalProfile | None = None
    try:
        profile = load_personal_profile(root)
    except (FileNotFoundError, OSError, yaml.YAMLError, ValidationError) as exc:
        errors.append(str(exc))

    if profile is None:
        fallback = PersonalProfile()
        return ProfileValidationResult(
            profile_valid=False,
            errors=errors,
            git_delivery=_git_delivery_status(root, fallback),
        )

    try:
        ZoneInfo(profile.timezone)
    except ZoneInfoNotFoundError:
        errors.append(f"unknown timezone: {profile.timezone}")

    for rel in (
        profile.paths.journal,
        profile.paths.incubator,
        profile.paths.canonical,
        profile.paths.reviews,
        profile.paths.private_local,
        ".codememory",
    ):
        if not (root / rel).is_dir():
            errors.append(f"required directory missing: {rel}")

    ignore_path = root / ".gitignore"
    ignore_lines = set(ignore_path.read_text(encoding="utf-8").splitlines()) if ignore_path.exists() else set()
    for rule in required_ignore_rules(profile):
        if rule not in ignore_lines:
            errors.append(f".gitignore missing required rule: {rule}")

    git_status = _git_delivery_status(root, profile)
    if git_status.reason != "not_git_repo":
        tracked = _run_git(root, "ls-files", "--", profile.paths.private_local)
        if tracked.returncode == 0 and tracked.stdout.strip():
            errors.append(
                f"private-local path '{profile.paths.private_local}' is already tracked by Git: "
                f"{tracked.stdout.strip()}"
            )
    if git_status.enabled and git_status.status == "unavailable":
        warnings.append(f"Git delivery enabled but unavailable: {git_status.reason}")

    return ProfileValidationResult(
        profile_valid=not errors,
        errors=errors,
        warnings=warnings,
        git_delivery=git_status,
        profile=profile,
    )


def _merge_gitignore(root: Path, profile: PersonalProfile) -> None:
    path = root / ".gitignore"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = existing.splitlines()
    missing = [rule for rule in required_ignore_rules(profile) if rule not in lines]
    if not missing:
        return
    separator = "\n" if existing and not existing.endswith("\n") else ""
    block = "\n".join(missing) + "\n"
    path.write_text(existing + separator + block, encoding="utf-8")


def _write_readme_if_missing(root: Path, profile: PersonalProfile) -> None:
    path = root / "README.md"
    if path.exists():
        return
    path.write_text(
        "# Personal Memory\n\n"
        "This directory is a CodeMemory Personal Profile.\n\n"
        "> Security: a private GitHub repository is not encrypted storage. "
        "Once raw records enter Git history, deleting them from the working tree "
        "does not guarantee removal from history. Keep local-only material in "
        f"`{profile.paths.private_local.rstrip('/')}/`.\n",
        encoding="utf-8",
    )


def init_personal_profile(
    root: Path,
    *,
    owner: str = "owner",
    timezone: str = "Asia/Hong_Kong",
    auto_commit: bool = False,
    auto_push: bool = False,
    remote: str = "origin",
    branch: str = "main",
) -> ProfileValidationResult:
    """Create or validate a Personal Profile without initializing Git."""
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    profile_path = root / PROFILE_RELATIVE_PATH
    if profile_path.exists():
        try:
            existing_profile = load_personal_profile(root)
        except (OSError, yaml.YAMLError, ValidationError):
            return validate_personal_profile(root)
        _merge_gitignore(root, existing_profile)
        _write_readme_if_missing(root, existing_profile)
        return validate_personal_profile(root)

    if auto_push:
        auto_commit = True
    profile = PersonalProfile(
        owner=owner,
        timezone=timezone,
        maintenance=MaintenanceConfig(
            auto_commit=auto_commit,
            auto_push=auto_push,
            remote=remote,
            branch=branch,
        ),
    )
    for rel in (
        profile.paths.journal,
        profile.paths.incubator,
        profile.paths.canonical,
        profile.paths.reviews,
        profile.paths.private_local,
        ".codememory",
    ):
        (root / rel).mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        yaml.safe_dump(profile.model_dump(mode="json"), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    _merge_gitignore(root, profile)
    _write_readme_if_missing(root, profile)
    return validate_personal_profile(root)
