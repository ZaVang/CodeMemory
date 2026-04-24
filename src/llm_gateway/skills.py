"""
LLM Bridge — Local skill loader.

Loads SKILL.md files from a user-defined skills directory, strips YAML
frontmatter, and renders them with Jinja2 so they can be injected into
LLMBridge.chat() calls as system prompts.

Two layout formats are supported:

Flat (legacy)::

    skills_dir/
    └── <skill-name>/
        └── SKILL.md

Plugin (Claude Code plugin format)::

    skills_dir/
    └── <skill-name>/
        ├── .claude-plugin/
        │   └── plugin.json   # {"skills": ["./skills/"]}
        └── skills/
            └── <skill-name>/
                └── SKILL.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import frontmatter
from jinja2 import Environment, StrictUndefined, TemplateError


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class LLMBridgeError(Exception):
    """Base exception for all LLM Bridge errors."""


class SkillNotFoundError(LLMBridgeError):
    """Raised when a requested skill's SKILL.md file does not exist."""

    def __init__(self, skill_name: str, skills_dir: Path) -> None:
        super().__init__(
            f"Skill '{skill_name}' not found in '{skills_dir}'. "
            f"Tried flat layout ({skills_dir / skill_name / 'SKILL.md'}) "
            f"and plugin layout ({skills_dir / skill_name / '.claude-plugin' / 'plugin.json'})."
        )
        self.skill_name = skill_name
        self.skills_dir = skills_dir


class SkillRenderError(LLMBridgeError):
    """Raised when Jinja2 rendering of a skill template fails."""

    def __init__(self, skill_name: str, cause: Exception) -> None:
        super().__init__(f"Failed to render skill '{skill_name}': {cause}")
        self.skill_name = skill_name
        self.cause = cause


# ---------------------------------------------------------------------------
# SkillLoader
# ---------------------------------------------------------------------------

class SkillLoader:
    """Loads and renders skill templates from a local skills directory.

    Supports two directory layouts:

    * **Flat** — ``skills_dir/<skill-name>/SKILL.md``
    * **Plugin** (Claude Code plugin format) — skill root contains
      ``.claude-plugin/plugin.json`` whose ``"skills"`` array lists
      sub-directories; each sub-directory is scanned for ``<name>/SKILL.md``.

    Both layouts may coexist in the same ``skills_dir``.

    Parameters
    ----------
    skills_dir :
        Path to the directory containing skill subdirectories.

    Raises
    ------
    FileNotFoundError
        If ``skills_dir`` does not exist.
    """

    def __init__(self, skills_dir: Path) -> None:
        if not skills_dir.exists():
            raise FileNotFoundError(
                f"Skills directory does not exist: {skills_dir}"
            )
        if not skills_dir.is_dir():
            raise NotADirectoryError(
                f"Skills directory is not a directory: {skills_dir}"
            )
        self._skills_dir = skills_dir
        self._jinja_env = Environment(
            undefined=StrictUndefined,
            keep_trailing_newline=True,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_skill_path(self, skill_name: str) -> Path | None:
        """Return the SKILL.md path for *skill_name*, or ``None`` if not found.

        Resolution order:

        1. Plugin format — ``.claude-plugin/plugin.json`` present; each path
           listed in ``"skills"`` is searched for ``<skill_name>/SKILL.md``.
        2. Flat format — ``<skill_name>/SKILL.md`` directly under the root.
        """
        root = self._skills_dir / skill_name
        if not root.is_dir():
            return None

        plugin_json = root / ".claude-plugin" / "plugin.json"
        if plugin_json.exists():
            try:
                data = json.loads(plugin_json.read_text(encoding="utf-8"))
                for skills_rel in data.get("skills", []):
                    candidate = (root / skills_rel / skill_name / "SKILL.md").resolve()
                    if candidate.exists():
                        return candidate
            except (json.JSONDecodeError, OSError):
                pass  # fall through to flat format

        flat = root / "SKILL.md"
        return flat if flat.exists() else None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, skill_name: str, variables: dict[str, Any] | None = None) -> str:
        """Load and Jinja2-render a single skill.

        Reads the resolved ``SKILL.md`` (UTF-8), strips YAML frontmatter via
        ``python-frontmatter``, and renders the body template with the
        provided variables.

        Parameters
        ----------
        skill_name :
            Name of the skill subdirectory.
        variables :
            Template variables.  ``None`` is treated as ``{}``.
            Variables referenced without ``| default()`` raise
            ``SkillRenderError`` (via Jinja2 ``StrictUndefined``).

        Returns
        -------
        str
            Rendered skill body (frontmatter stripped).

        Raises
        ------
        SkillNotFoundError
            If no ``SKILL.md`` can be resolved for *skill_name*.
        SkillRenderError
            If Jinja2 rendering fails (e.g. undefined variable).
        """
        skill_path = self._resolve_skill_path(skill_name)
        if skill_path is None:
            raise SkillNotFoundError(skill_name, self._skills_dir)

        raw_text = skill_path.read_text(encoding="utf-8")
        post = frontmatter.loads(raw_text)
        body = post.content

        vars_: dict[str, Any] = dict(variables or {})

        # Auto-inject references from sibling references.md if not overridden by caller.
        # Skill templates can use:
        #   {{ references | default('') }}          — full reference doc
        #   {{ references_chunk | default(references | default('')) }}
        #                                           — prefer Agent-filtered chunk, fall back to full
        if "references" not in vars_:
            refs_path = skill_path.parent / "references.md"
            if refs_path.exists():
                vars_["references"] = refs_path.read_text(encoding="utf-8")

        try:
            template = self._jinja_env.from_string(body)
            return template.render(**vars_)
        except TemplateError as exc:
            raise SkillRenderError(skill_name, exc) from exc

    def load_many(
        self,
        skill_names: list[str],
        variables: dict[str, Any] | None = None,
    ) -> str:
        """Load and concatenate multiple skills.

        Skills are rendered in the given order and joined with
        ``'\\n\\n---\\n\\n'``.

        Parameters
        ----------
        skill_names :
            Ordered list of skill names to load.
        variables :
            Jinja2 template variables shared across all skills.

        Returns
        -------
        str
            Single concatenated string of all rendered skill bodies.
        If ``skill_names`` is empty, returns an empty string ``""``.
        """
        rendered = [self.load(name, variables) for name in skill_names]
        return "\n\n---\n\n".join(rendered)

    def list_skills(self) -> list[str]:
        """Return a sorted list of available skill names.

        Includes both flat-format and plugin-format skills.
        Returns ``[]`` if no valid skills are found or if the directory
        was removed after ``__init__`` was called.

        Returns
        -------
        list[str]
            Sorted skill names.
        """
        if not self._skills_dir.exists():
            return []
        return sorted(
            d.name
            for d in self._skills_dir.iterdir()
            if d.is_dir() and self._resolve_skill_path(d.name) is not None
        )