#!/usr/bin/env python3
"""Runnable root-bound Agent example with no provider or API key.

The demo copies ``examples/investment`` to a temporary directory, registers
the exact standard five-tool surface, and performs:

    search_memories -> create_memory -> build_memory

Tool payloads never contain a filesystem root. The Toolkit binds the root once
when it is constructed, and the temporary directory is removed automatically.

Run from the repository root:

    PYTHONPATH=src python examples/example_agent.py
"""

from __future__ import annotations

import asyncio
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


EXPECTED_TOOLS = [
    "build_memory",
    "search_memories",
    "expand_source",
    "create_memory",
    "propose_memory",
]


class MockAgent:
    """Return a fixed sequence of current CodeMemory tool calls."""

    def __init__(self) -> None:
        self._steps: list[dict[str, Any]] = [
            {
                "name": "search_memories",
                "input": {
                    "query": "risk tolerance",
                    "tags": ["investment"],
                },
            },
            {
                "name": "create_memory",
                "input": {
                    "id": "user/demo/moderate-risk-note",
                    "summary": "Demo risk preference with a 20% position limit",
                    "body": (
                        "# Demo risk preference\n\n"
                        "The user prefers a moderate-aggressive strategy, limits "
                        "a single position to 20%, and avoids crypto.\n"
                    ),
                    "tags": ["investment", "risk", "demo"],
                    "import_required": ["user/investment/context"],
                    "propose": False,
                },
            },
            {
                "name": "build_memory",
                "input": {
                    "id": "user/demo/moderate-risk-note",
                    "depth": "required",
                    "budget": 1200,
                    "format": "plain-markdown",
                },
            },
        ]

    def next_tool_call(self) -> dict[str, Any] | None:
        if not self._steps:
            return None
        return self._steps.pop(0)


async def run_agent() -> None:
    """Execute the mock Agent against a disposable copy of the example root."""

    from codememory.integrations import CodememoryToolkit
    from harnesslib.sandbox import Sandbox

    source_root = REPO_ROOT / "examples" / "investment"

    with TemporaryDirectory(prefix="codememory-agent-demo-") as temp_dir:
        demo_root = Path(temp_dir) / "investment"
        shutil.copytree(source_root, demo_root)

        toolkit = CodememoryToolkit(root=str(demo_root))
        sandbox = Sandbox()
        await toolkit.register_to_sandbox(sandbox)

        registered = [tool.name for tool in sandbox.list_tools()]
        if registered != EXPECTED_TOOLS:
            raise RuntimeError(f"unexpected standard tool surface: {registered}")

        print("CodeMemory Agent demo")
        print(f"registered tools ({len(registered)}): {', '.join(registered)}")

        agent = MockAgent()
        while call := agent.next_tool_call():
            name = call["name"]
            payload = call["input"]
            print(f"\n-> {name}: {_compact_payload(payload)}")
            response = await sandbox.execute(name, payload)
            result = str(response.get("result", response))
            preview = result if len(result) <= 360 else result[:360] + "..."
            print(f"<- {preview}")

        print("\nDemo complete; temporary memory root removed.")


def _compact_payload(payload: dict[str, Any]) -> str:
    """Render payload keys without dumping long body text."""

    rendered: list[str] = []
    for key, value in payload.items():
        text = repr(value)
        if len(text) > 80:
            text = text[:77] + "..."
        rendered.append(f"{key}={text}")
    return ", ".join(rendered)


if __name__ == "__main__":
    asyncio.run(run_agent())
