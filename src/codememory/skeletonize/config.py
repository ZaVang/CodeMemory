"""External configuration for skeletonize — glob-matched default weight.

Supports a ``.codememory/skeletonize.yaml`` file at the project root::

    defaults:
      "**/test_*.py": 3
      "**/migrations/**": 2
      "src/core/**": 8
      "src/api/**": 7

``@weight`` annotations in source code always take precedence over
glob-matched defaults. The config file is optional — when absent, all
files default to weight 5.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path

import yaml

_CONFIG_CACHE: dict[Path, dict[str, int]] = {}


def load_config(project_root: Path) -> dict[str, int]:
    """Load skeletonize weight defaults from a YAML config file.

    Returns a ``{glob: weight}`` dict. Result is cached per project_root.
    Returns the full defaults map (each call to :func:`resolve_weight`
    iterates over it).
    """
    if project_root in _CONFIG_CACHE:
        return _CONFIG_CACHE[project_root]

    config_file = project_root / '.codememory' / 'skeletonize.yaml'
    defaults: dict[str, int] = {}

    if config_file.is_file():
        try:
            data = yaml.safe_load(config_file.read_text(encoding='utf-8'))
            if isinstance(data, dict) and 'defaults' in data:
                raw = data['defaults']
                if isinstance(raw, dict):
                    for pattern, weight in raw.items():
                        try:
                            ival = int(weight)
                            defaults[str(pattern)] = max(1, min(10, ival))
                        except (ValueError, TypeError):
                            pass
        except Exception:
            pass  # malformed config is silently ignored

    _CONFIG_CACHE[project_root] = defaults
    return defaults


def resolve_weight(file_path: str | Path, project_root: Path) -> int | None:
    """Find the default weight for *file_path* from config globs.

    Returns the weight value if a glob matches, or None if no match.
    """
    defaults = load_config(project_root)
    if not defaults:
        return None

    fp = str(file_path).replace('\\', '/')

    for pattern, weight in defaults.items():
        if fnmatch.fnmatch(fp, pattern):
            return weight

    return None
