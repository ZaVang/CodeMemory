"""Drift guards for primary documentation and checked-in examples."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import unquote

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_ROOTS = (
    REPO_ROOT / "examples" / "investment",
    REPO_ROOT / "examples" / "companion",
    REPO_ROOT / "examples" / "software-architecture",
)
PRIMARY_GUIDES = (
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "USER_GUIDE.md",
    REPO_ROOT / "docs" / "INTEGRATION.md",
    REPO_ROOT / "docs" / "agent-memory-guide.md",
    REPO_ROOT / "docs" / "project_structure.md",
    REPO_ROOT / "frontend" / "README.md",
    REPO_ROOT / ".claude" / "CLAUDE.md",
    REPO_ROOT / ".claude" / "commands" / "sprint.md",
)
REMOVED_HEAT_FIELDS = {
    "intensity",
    "stability",
    "stability_source",
    "days_since_last_access",
}
REMOVED_AGENT_TOOLS = {
    "resolve_context",
    "resolve_memory",
    "update_memory",
    "propose_update",
    "overview",
    "wander",
    "validate_memories",
    "import_memories",
}


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    _, raw, _ = text.split("---", 2)
    return yaml.safe_load(raw) or {}


def _walk_json_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        keys = {str(key) for key in value}
        for child in value.values():
            keys.update(_walk_json_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(_walk_json_keys(child))
        return keys
    return set()


def test_example_frontmatter_uses_current_model_fields() -> None:
    offenders: list[str] = []
    for root in EXAMPLE_ROOTS:
        for path in root.rglob("*.md"):
            removed = REMOVED_HEAT_FIELDS.intersection(_frontmatter(path))
            if removed:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {sorted(removed)}")
    assert not offenders, "removed example metadata:\n" + "\n".join(offenders)


def test_example_indexes_do_not_publish_removed_heat_fields() -> None:
    offenders: list[str] = []
    for root in EXAMPLE_ROOTS:
        index_path = root / ".codememory" / "index.json"
        data = json.loads(index_path.read_text(encoding="utf-8"))
        removed = REMOVED_HEAT_FIELDS.intersection(_walk_json_keys(data))
        if removed:
            offenders.append(f"{index_path.relative_to(REPO_ROOT)}: {sorted(removed)}")
    assert not offenders, "removed index fields:\n" + "\n".join(offenders)


def test_runnable_agent_example_uses_exact_current_surface() -> None:
    path = REPO_ROOT / "examples" / "example_agent.py"
    source = path.read_text(encoding="utf-8")

    spec = importlib.util.spec_from_file_location("codememory_example_agent", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.EXPECTED_TOOLS == [
        "build_memory",
        "search_memories",
        "expand_source",
        "create_memory",
        "propose_memory",
    ]
    assert not (REMOVED_AGENT_TOOLS & set(re.findall(r'"name":\s*"([^"]+)"', source)))
    assert '"root"' not in source
    assert "TemporaryDirectory" in source


def test_primary_guides_do_not_teach_removed_interfaces() -> None:
    command_pattern = re.compile(r"\bcodememory\s+(focus|overview|wander)\b")
    offenders: list[str] = []
    for path in PRIMARY_GUIDES:
        text = path.read_text(encoding="utf-8")
        if command_pattern.search(text):
            offenders.append(f"{path.relative_to(REPO_ROOT)}: removed CLI command")
        if "--intensity" in text:
            offenders.append(f"{path.relative_to(REPO_ROOT)}: removed CLI field")
        if path.name == "INTEGRATION.md":
            for tool in sorted(REMOVED_AGENT_TOOLS):
                if re.search(rf"`{re.escape(tool)}`", text):
                    offenders.append(f"{path.relative_to(REPO_ROOT)}: removed tool {tool}")
    assert not offenders, "stale primary guidance:\n" + "\n".join(offenders)


def test_primary_markdown_links_resolve() -> None:
    link_pattern = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
    missing: list[str] = []

    for path in PRIMARY_GUIDES:
        for raw_target in link_pattern.findall(path.read_text(encoding="utf-8")):
            target = unquote(raw_target.strip().strip("<>").split("#", 1)[0])
            if not target or re.match(r"^[a-z]+://", target) or target.startswith("mailto:"):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                missing.append(f"{path.relative_to(REPO_ROOT)} -> {target}")

    assert not missing, "missing local Markdown links:\n" + "\n".join(missing)


def test_project_structure_maps_unified_build_module() -> None:
    text = (REPO_ROOT / "docs" / "project_structure.md").read_text(encoding="utf-8")
    assert "src/codememory/build.py" in text
    assert "src/codememory/context_pack.py" not in text
    assert "src/codememory/agent_tools.py" in text
    assert "backend/routers/reviews.py" in text


def test_agent_contribution_guide_enforces_current_write_gates() -> None:
    text = (REPO_ROOT / "docs" / "agent-memory-guide.md").read_text(encoding="utf-8")
    scenario_d = text.split("### 场景 D：", 1)[1].split("---", 1)[0]

    assert "codememory update" not in text
    assert "codememory create --propose" not in text
    assert "create 后立即 update" not in text
    assert text.count('"tool": "create_memory"') >= 3
    assert "一次提交完整" in text
    assert "codememory propose user/decisions/2026-06-pin-python-313" in scenario_d
    assert "status` 不属于当前 modification patch 支持字段" in scenario_d
    assert "codememory update" not in scenario_d
