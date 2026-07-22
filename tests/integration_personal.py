#!/usr/bin/env python3
"""Phase 1A end-to-end acceptance against disposable external instances."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import tempfile
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from codememory.capture import append_capture  # noqa: E402
from codememory.index import reindex  # noqa: E402
from codememory.integrations import CodememoryToolkit  # noqa: E402
from codememory.profile import init_personal_profile  # noqa: E402
from harnesslib.sandbox import Sandbox  # noqa: E402


passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"PASS {name}")
    else:
        failed += 1
        print(f"FAIL {name}: {detail}")


async def main() -> int:
    with tempfile.TemporaryDirectory(prefix="codememory-personal-") as temp:
        root = Path(temp) / "instance"
        other = Path(temp) / "untrusted-root"
        root.mkdir()
        other.mkdir()
        subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(root), "remote", "add", "origin", "git@github.com:owner/private-memory.git"],
            check=True,
            capture_output=True,
        )
        initialized = init_personal_profile(root)
        check("profile valid in external Git repo", initialized.profile_valid)
        check("Git delivery capability detected", initialized.git_delivery.status == "available")
        check("delivery remains disabled by default", initialized.git_delivery.enabled is False)

        capture = append_capture(root, "Owner chose an explicit canonical boundary")
        check("capture persisted", (root / capture.path).exists())

        topic_path = root / "incubator" / "2026-07.md"
        topic_path.write_text(
            """# 2026-07 Incubator

## Canonical boundary
<!-- codememory:topic
topic_id: topic/canonical-boundary
revision_id: topic/canonical-boundary@2026-07
created_at: 2026-07-22T12:00:00+08:00
updated_at: 2026-07-22T12:00:00+08:00
origin: mixed
content_hash: sha256:test
derived_from: []
relations: []
-->

Capture and Topic are discovery objects, not DAG nodes.

### Claim: only atoms build
<!-- codememory:claim
claim_id: claim/canonical-boundary/only-atoms-build
origin: agent_inference
claim_status: unassessed
derived_from: []
-->

The parser preserves this block without indexing it independently.
""",
            encoding="utf-8",
        )
        reindex(root)

        toolkit = CodememoryToolkit(root=str(root))
        sandbox = Sandbox()
        await toolkit.register_to_sandbox(sandbox)
        schemas = {tool.name: tool.input_schema for tool in sandbox.list_tools()}
        check("toolkit exposes capture/search/read/build", {
            "capture_memory", "search_memories", "read_memory", "build_memory"
        }.issubset(schemas))
        check("bound tool schemas omit root", all("root" not in (schema or {}).get("properties", {}) for schema in schemas.values()))

        tool_capture = await sandbox.execute(
            "capture_memory",
            {"text": "bound root must win", "root": str(other)},
        )
        captured = json.loads(tool_capture["result"])
        check("caller root override ignored", (root / captured["path"]).exists() and not (other / captured["path"]).exists())

        reindex(root)
        searched = await sandbox.execute("search_memories", {"query": "boundary"})
        check("typed search finds capture and Topic", "capture" in searched["result"] and "incubator_topic" in searched["result"])
        read = await sandbox.execute("read_memory", {"id": "topic/canonical-boundary@2026-07"})
        check("stable Topic read preserves claim block", "claim/canonical-boundary/only-atoms-build" in read["result"])

        try:
            await sandbox.execute("build_memory", {"id": capture.id})
        except ValueError as exc:
            check("build rejects Capture with read route", "use read" in str(exc))
        else:
            check("build rejects Capture with read route", False, "build unexpectedly succeeded")

    print(f"\nPhase 1A integration: {passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
