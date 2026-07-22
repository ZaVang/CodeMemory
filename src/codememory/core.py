"""Core utilities for CodeMemory: frontmatter parsing, hashing, path resolution."""

import hashlib
import logging
import math
import os
import sys
from pathlib import Path, PurePosixPath

import yaml

_logger = logging.getLogger("codememory")


def configure_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure the codememory logger.

    Default level is WARNING.  ``--verbose`` promotes to INFO; ``--quiet``
    suppresses everything below ERROR.
    """
    level = logging.WARNING
    if verbose:
        level = logging.INFO
    if quiet:
        level = logging.ERROR
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s", stream=sys.stderr)


def get_root_dir(custom_root: str | None = None) -> Path:
    """Determine the memory root directory.

    Priority:
    1. Explicit --root / custom_root argument
    2. CODEMEMORY_ROOT environment variable
    3. Current working directory
    """
    if custom_root:
        return Path(custom_root).resolve()
    env_root = os.environ.get("CODEMEMORY_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path.cwd()


def compute_body_hash(body: str) -> str:
    """sha256(body)[:7]"""
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:7]


def estimate_tokens(text: str) -> int:
    """Prototype phase: length of string as token proxy."""
    return len(text)


def parse_frontmatter(filepath: Path) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from a markdown file.

    Returns (metadata_dict, body_string).
    """
    try:
        content = filepath.read_text(encoding="utf-8-sig")
    except Exception as e:
        _logger.error("Error reading %s: %s", filepath, e)
        return {}, ""

    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_str = parts[1]
    body = parts[2].strip()

    try:
        metadata = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError as e:
        _logger.error("Error parsing YAML in %s: %s", filepath, e)
        metadata = {}

    return metadata, body


def resolve_safe_relative_path(
    root_dir: Path,
    identifier: str,
    *,
    suffix: str,
    label: str,
    allow_nested: bool = True,
) -> Path:
    """Resolve a strict slash-delimited identifier under ``root_dir``.

    Validation happens before joining so Windows drive/root semantics and
    backslashes cannot reinterpret a caller-controlled identifier.  The final
    resolved containment check also rejects escapes through an existing
    symlink or junction inside the root.
    """

    if not isinstance(identifier, str) or not identifier:
        raise ValueError(f"unsafe {label}: value is empty")
    if identifier != identifier.strip():
        raise ValueError(f"unsafe {label}: surrounding whitespace is not allowed")
    if "\\" in identifier or ":" in identifier:
        raise ValueError(f"unsafe {label}: backslashes and colons are not allowed")

    parts = identifier.split("/")
    if (
        PurePosixPath(identifier).is_absolute()
        or any(not part or part in {".", ".."} or part != part.strip() for part in parts)
        or (not allow_nested and len(parts) != 1)
    ):
        raise ValueError(f"unsafe {label}: expected non-empty relative path segments")

    root_resolved = root_dir.resolve()
    target = (root_resolved / f"{identifier}{suffix}").resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"unsafe {label}: path escapes the bound root") from exc
    return target


def get_memory_path(root_dir: Path, memory_id: str) -> Path:
    """Resolve a validated memory ID to a contained ``.md`` path."""

    return resolve_safe_relative_path(
        root_dir,
        memory_id,
        suffix=".md",
        label="memory_id",
    )
