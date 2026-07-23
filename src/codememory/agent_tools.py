"""Shared root-bound agent tool catalog and dispatcher.

Toolkit/Sandbox and MCP adapt these provider-neutral definitions mechanically.
All operation behavior remains in :mod:`codememory.handlers`.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .handlers import (
    handle_build,
    handle_capture,
    handle_create,
    handle_maintenance_resume,
    handle_maintenance_run,
    handle_maintenance_status,
    handle_propose,
    handle_read,
    handle_review_batch,
    handle_search,
    handle_source_expand,
)
from .profile import PROFILE_RELATIVE_PATH, load_personal_profile


@dataclass(frozen=True)
class AgentToolSpec:
    """One provider-neutral tool definition."""

    name: str
    description: str
    input_schema: dict[str, Any]
    read_only: bool

    def as_legacy_dict(self) -> dict[str, Any]:
        """Return the historical Toolkit definition shape."""

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": deepcopy(self.input_schema),
            "read_only": self.read_only,
        }


def _object_schema(
    properties: dict[str, Any],
    *,
    required: list[str] | None = None,
) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema


_IMPORT_PROPERTIES = {
    "import_required": {"type": "array", "items": {"type": "string"}},
    "import_recommended": {"type": "array", "items": {"type": "string"}},
    "import_related": {"type": "array", "items": {"type": "string"}},
}


def _create_spec(*, personal: bool) -> AgentToolSpec:
    propose_schema: dict[str, Any] = {
        "type": "boolean",
        "default": True if personal else False,
        "description": (
            "Personal agent creation is always proposed."
            if personal
            else "Create as status=proposed instead of active."
        ),
    }
    if personal:
        propose_schema["enum"] = [True]
    return AgentToolSpec(
        name="create_memory",
        description=(
            "Create a complete new Atom in one write. Personal Profile agent creation "
            "is always status=proposed and requires owner merge."
            if personal
            else "Create a complete new Atom in one write; set propose=true when owner review is required."
        ),
        input_schema=_object_schema(
            {
                "id": {"type": "string", "description": "New Atom ID"},
                "summary": {"type": "string", "description": "One-line summary"},
                "body": {"type": "string", "description": "Complete Markdown body"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "propose": propose_schema,
                **deepcopy(_IMPORT_PROPERTIES),
            },
            required=["id", "summary", "body"],
        ),
        read_only=False,
    )


_BUILD_SPEC = AgentToolSpec(
    name="build_memory",
    description="Build canonical context from an Atom through the explicit imports DAG.",
    input_schema=_object_schema(
        {
            "id": {"type": "string"},
            "depth": {
                "type": "string",
                "enum": ["required", "recommended", "full"],
                "default": "recommended",
            },
            "budget": {"type": "integer", "minimum": 1},
            "focus": {"type": "string"},
            "task_goal": {"type": "string"},
            "format": {
                "type": "string",
                "enum": ["xml-markdown", "markdown", "plain-markdown", "json"],
                "default": "xml-markdown",
            },
        },
        required=["id"],
    ),
    read_only=True,
)


def _search_spec(*, semantic: bool) -> AgentToolSpec:
    properties: dict[str, Any] = {
        "query": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "type": {"type": "string", "enum": ["atom", "schema"]},
        "status": {
            "type": "string",
            "enum": ["active", "proposed", "archived", "superseded", "draft"],
        },
        "maturity": {
            "type": "string",
            "enum": ["draft", "verified", "proven", "superseded"],
        },
        "semantic_type": {"type": "string"},
        "has_imports": {"type": "boolean"},
        "has_schema": {"type": "boolean"},
        "kinds": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["capture", "incubator_topic", "incubator_claim", "atom"],
            },
        },
        "date_from": {"type": "string"},
        "date_to": {"type": "string"},
        "topic": {"type": "string"},
        "project": {"type": "string"},
        "person": {"type": "string"},
        "origin": {"type": "string"},
        "claim_status": {"type": "string"},
    }
    if semantic:
        properties.update({
            "semantic": {
                "type": "boolean",
                "default": False,
                "description": "Use the configured local Personal semantic index.",
            },
            "semantic_limit": {"type": "integer", "minimum": 1, "default": 10},
        })
    return AgentToolSpec(
        name="search_memories",
        description=(
            "Discover typed Personal memory candidates lexically or through the "
            "explicitly enabled local semantic index."
            if semantic
            else "Lexically discover canonical Atoms and, for Personal Profiles, Capture/Topic objects."
        ),
        input_schema=_object_schema(properties),
        read_only=True,
    )


_EXPAND_SPEC = AgentToolSpec(
    name="expand_source",
    description="Explicitly read a registered Source Artifact with freshness and truncation metadata.",
    input_schema=_object_schema(
        {
            "artifact_id": {"type": "string"},
            "start": {"type": "integer", "minimum": 0},
            "end": {"type": "integer", "minimum": 0},
            "max_chars": {"type": "integer", "minimum": 1},
        },
        required=["artifact_id"],
    ),
    read_only=True,
)


_CORE_PREFIX: tuple[AgentToolSpec, ...] = (
    _BUILD_SPEC,
    _search_spec(semantic=False),
    _EXPAND_SPEC,
)


_PROPOSE_SPEC = AgentToolSpec(
    name="propose_memory",
    description="Queue a modification proposal against an existing Atom without changing target bytes.",
    input_schema=_object_schema(
        {
            "id": {"type": "string", "description": "Existing target Atom ID"},
            "reason": {"type": "string"},
            "summary": {"type": "string"},
            "body": {"type": "string"},
            **deepcopy(_IMPORT_PROPERTIES),
            "source_ref": {"type": "string"},
        },
        required=["id", "reason"],
    ),
    read_only=False,
)


_PERSONAL_EXTENSION: tuple[AgentToolSpec, ...] = (
    AgentToolSpec(
        name="capture_memory",
        description="Append an immutable Capture to the bound Personal Profile.",
        input_schema=_object_schema(
            {"text": {"type": "string"}, "actor": {"type": "string"}},
            required=["text"],
        ),
        read_only=False,
    ),
    AgentToolSpec(
        name="read_memory",
        description="Read a Capture, Topic revision, or inline Claim by stable ID.",
        input_schema=_object_schema({"id": {"type": "string"}}, required=["id"]),
        read_only=True,
    ),
    AgentToolSpec(
        name="maintenance_status",
        description="Inspect the active Personal maintenance run and unconsumed valid Captures.",
        input_schema=_object_schema({}),
        read_only=True,
    ),
    AgentToolSpec(
        name="maintain_memory",
        description="Apply one provenance-rich Topic changeset to the bound Personal Profile.",
        input_schema=_object_schema(
            {"changeset": {"type": "object"}},
            required=["changeset"],
        ),
        read_only=False,
    ),
    AgentToolSpec(
        name="resume_memory_maintenance",
        description="Resume the same pending or scan-blocked Personal maintenance run.",
        input_schema=_object_schema({}),
        read_only=False,
    ),
    AgentToolSpec(
        name="review_personal_memory",
        description="Apply an owner-provided batch of promote, merge, and delete decisions.",
        input_schema=_object_schema(
            {"decisions": {"type": "array", "items": {"type": "object"}}},
            required=["decisions"],
        ),
        read_only=False,
    ),
)


def is_personal_root(root: Path) -> bool:
    """Return whether the bound root declares a Personal Profile."""

    return (root / PROFILE_RELATIVE_PATH).is_file()


def standard_tool_specs() -> list[AgentToolSpec]:
    """Return the exact root-independent standard agent surface."""

    return [*_CORE_PREFIX, _create_spec(personal=False), _PROPOSE_SPEC]


def _semantic_search_is_configured(root: Path) -> bool:
    if not is_personal_root(root):
        return False
    try:
        semantic = load_personal_profile(root).discovery.semantic
    except Exception:
        return False
    return bool(semantic.enabled and semantic.model_path and semantic.model_id)


def tool_specs_for_root(root: Path) -> list[AgentToolSpec]:
    """Return the exact shared agent surface for a bound root."""

    personal = is_personal_root(root)
    specs = [
        _BUILD_SPEC,
        _search_spec(semantic=_semantic_search_is_configured(root)),
        _EXPAND_SPEC,
        _create_spec(personal=personal),
        _PROPOSE_SPEC,
    ]
    if personal:
        specs.extend(_PERSONAL_EXTENSION)
    return specs


def _required(arguments: dict[str, Any], name: str) -> Any:
    value = arguments.get(name)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"'{name}' parameter is required")
    return value


def _dispatch(root: Path, name: str, arguments: dict[str, Any]) -> str:
    if name == "build_memory":
        return handle_build(
            root,
            _required(arguments, "id"),
            depth=arguments.get("depth", "recommended"),
            budget=arguments.get("budget"),
            focus=arguments.get("focus"),
            task_goal=arguments.get("task_goal"),
            output_format=arguments.get("format", "xml-markdown"),
        )
    if name == "search_memories":
        return handle_search(
            root,
            query=arguments.get("query"),
            tags=arguments.get("tags"),
            type_=arguments.get("type"),
            status=arguments.get("status"),
            maturity=arguments.get("maturity"),
            semantic_type=arguments.get("semantic_type"),
            has_imports=arguments.get("has_imports", False),
            has_schema=arguments.get("has_schema", False),
            kinds=arguments.get("kinds"),
            date_from=arguments.get("date_from"),
            date_to=arguments.get("date_to"),
            topic=arguments.get("topic"),
            project=arguments.get("project"),
            person=arguments.get("person"),
            origin=arguments.get("origin"),
            claim_status=arguments.get("claim_status"),
            semantic=bool(arguments.get("semantic", False)),
            semantic_limit=int(arguments.get("semantic_limit", 10)),
        )
    if name == "expand_source":
        return handle_source_expand(
            root,
            _required(arguments, "artifact_id"),
            start=arguments.get("start"),
            end=arguments.get("end"),
            max_chars=arguments.get("max_chars"),
        )
    if name == "create_memory":
        personal = is_personal_root(root)
        propose = True if personal else bool(arguments.get("propose", False))
        path = handle_create(
            root,
            memory_type="atom",
            memory_id=_required(arguments, "id"),
            summary=_required(arguments, "summary"),
            body=_required(arguments, "body"),
            tags=arguments.get("tags"),
            propose=propose,
            import_required=arguments.get("import_required"),
            import_recommended=arguments.get("import_recommended"),
            import_related=arguments.get("import_related"),
            created_by="agent",
        )
        return f"Created memory: {path}\nStatus: {'proposed' if propose else 'active'}"
    if name == "propose_memory":
        proposal_id = handle_propose(
            root,
            _required(arguments, "id"),
            reason=_required(arguments, "reason"),
            summary=arguments.get("summary"),
            body=arguments.get("body"),
            import_required=arguments.get("import_required"),
            import_recommended=arguments.get("import_recommended"),
            import_related=arguments.get("import_related"),
            source_ref=arguments.get("source_ref"),
        )
        return f"Queued proposal: {proposal_id}"
    if name == "capture_memory":
        return handle_capture(root, _required(arguments, "text"), actor=arguments.get("actor"))
    if name == "read_memory":
        return handle_read(root, _required(arguments, "id"))
    if name == "maintenance_status":
        return handle_maintenance_status(root)
    if name == "maintain_memory":
        return handle_maintenance_run(root, _required(arguments, "changeset"))
    if name == "resume_memory_maintenance":
        return handle_maintenance_resume(root)
    if name == "review_personal_memory":
        return handle_review_batch(root, _required(arguments, "decisions"))
    raise ValueError(f"unknown agent tool: {name}")


def dispatch_agent_tool(root: Path, name: str, arguments: dict[str, Any] | None = None) -> str:
    """Dispatch one allowed tool against the bound root via shared handlers."""

    resolved_root = root.resolve()
    allowed = {spec.name for spec in tool_specs_for_root(resolved_root)}
    if name not in allowed:
        raise ValueError(f"unknown or unavailable agent tool: {name}")
    clean_arguments = {
        key: value
        for key, value in dict(arguments or {}).items()
        if key != "root"
    }
    try:
        return _dispatch(resolved_root, name, clean_arguments)
    except SystemExit as exc:
        raise ValueError("operation rejected by CodeMemory") from exc
