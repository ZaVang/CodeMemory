"""
LLM Bridge — Configuration loader.

Loads a YAML configuration file and resolves environment variable
placeholders (e.g. ``${OPENAI_API_KEY}``) so that secrets never need
to be hard-coded.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Union

import yaml
from dotenv import load_dotenv

from .models import BridgeConfig

# Ensure .env is loaded as early as possible.
load_dotenv()

# Pattern to match ${VAR_NAME} or ${VAR_NAME:-default}
ENV_VAR_PATTERN = re.compile(r"\$\{([^}:\s]+)(?::-(.*?))?\}")


def _resolve_env_vars(value: str) -> str:
    """Replace ``${VAR}`` / ``${VAR:-default}`` tokens in *value*."""

    def _replacer(match: re.Match) -> str:  # type: ignore[type-arg]
        var_name = match.group(1)
        default = match.group(2)
        env_value = os.environ.get(var_name)
        if env_value is not None:
            return env_value
        if default is not None:
            return default
        raise ValueError(
            f"Environment variable '{var_name}' is not set and no default provided."
        )

    return ENV_VAR_PATTERN.sub(_replacer, value)


def _walk_and_resolve(obj: object) -> object:
    """Recursively walk a parsed YAML tree and resolve env vars in strings."""
    if isinstance(obj, str):
        return _resolve_env_vars(obj)
    if isinstance(obj, dict):
        return {k: _walk_and_resolve(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk_and_resolve(item) for item in obj]
    return obj


def load_config(path: Union[str, Path]) -> BridgeConfig:
    """Load and validate a ``BridgeConfig`` from a YAML file.

    Environment variable placeholders such as ``${OPENAI_API_KEY}`` are
    resolved **before** Pydantic validation, so the YAML file can safely
    reference secrets stored in the environment or a ``.env`` file.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    resolved = _walk_and_resolve(raw)
    return BridgeConfig.model_validate(resolved)
