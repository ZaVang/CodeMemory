"""Core utilities for CodeMemory: frontmatter parsing, hashing, path resolution."""

import hashlib
import logging
import math
import os
import sys
from pathlib import Path

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


def get_memory_path(root_dir: Path, memory_id: str) -> Path:
    """Resolve a memory ID to a file path.

    E.g. 'user/ideas/x' -> root/user/ideas/x.md
    """
    # prevent directory traversal
    safe_id = memory_id.replace("..", "")
    return root_dir / f"{safe_id}.md"


def compute_retrieval_probability(
    days_since: int | float,
    stability: float,
    min_retention: float = 0.05,
) -> float:
    """Hybrid decay formula with a long-term retention floor (R15-C2).

    Pure exponential R_pure = 0.5^(days / stability) works well for short-term
    ranking but asymptotically approaches zero — well-learned semantic knowledge
    doesn't silently vanish.  The hybrid formula uses a power-law tail that
    preserves a minimum retrieval probability for all memories regardless of age.

    R_hybrid = max(0.5^(days/stability), min_retention / (1 + days / (10 * stability)))

    Short-term behavior (< 60 days at default stability=14.0) is unchanged.
    Long-term floor matches Bahrick's "permastore" finding: ~3-6% baseline.
    """
    if days_since < 0:
        days_since = 0
    if stability <= 0:
        stability = 14.0

    exponential = math.pow(0.5, days_since / stability)
    floor = min_retention / (1.0 + days_since / (10.0 * stability))
    return max(exponential, floor)
