#!/usr/bin/env python3
"""End-to-end integration test for the aligned standard agent surface.

Covers exact Toolkit registration, complete create/search, canonical build,
non-mutating modification proposals, owner merge, and proposed visibility.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_ROOT_PATH = Path("examples/investment").resolve()
_created_files: list[Path] = []
passed = 0
failed = 0


def _check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


async def main() -> None:
    global passed, failed

    from harnesslib.sandbox import Sandbox
    from codememory.core import parse_frontmatter
    from codememory.handlers import handle_merge
    from codememory.index import load_index, reindex
    from codememory.integrations import CodememoryToolkit
    from codememory.proposals import list_proposals

    print("=" * 62)
    print("  CodeMemory Integration Test -- Aligned Agent Surface")
    print("=" * 62)

    sandbox = Sandbox()
    await CodememoryToolkit(root=str(_ROOT_PATH)).register_to_sandbox(sandbox)
    definitions = sandbox.list_tools()
    names = {tool.name for tool in definitions}
    expected = {
        "build_memory",
        "search_memories",
        "expand_source",
        "create_memory",
        "propose_memory",
    }
    _check("INIT1: exact five standard tools", names == expected, f"got {sorted(names)}")
    _check(
        "INIT2: schemas omit root",
        all("root" not in (tool.input_schema or {}).get("properties", {}) for tool in definitions),
    )
    _check(
        "INIT3: legacy direct-update tools absent",
        not ({"resolve_context", "update_memory", "snapshot", "import_memories"} & names),
    )

    print("\n-- A. Complete create + search --")
    created_id = "user/test/adapter-create"
    created_path = _ROOT_PATH / f"{created_id}.md"
    _created_files.append(created_path)
    created = await sandbox.execute(
        "create_memory",
        {
            "id": created_id,
            "summary": "Adapter complete creation",
            "body": "# Adapter Create\n\nComplete body written atomically.",
            "tags": ["adapter-alignment", "integration"],
        },
    )
    _check("A1: create returns path", ".md" in created["result"])
    _check("A2: complete file exists", created_path.exists())
    meta, body = parse_frontmatter(created_path)
    _check(
        "A3: summary/body written in initial version",
        meta["version"] == 1
        and meta["summary"] == "Adapter complete creation"
        and "Complete body written atomically" in body,
    )
    searched = await sandbox.execute("search_memories", {"tags": ["adapter-alignment"]})
    _check("A4: active creation is searchable", created_id in searched["result"])

    print("\n-- B. Canonical build --")
    built = await sandbox.execute(
        "build_memory",
        {"id": "user/investment/context", "depth": "required", "format": "plain-markdown"},
    )
    text = built["result"]
    expected_ids = [
        "user/investment/risk-tolerance",
        "user/investment/semiconductor-thesis",
        "user/investment/current-holdings",
        "user/investment/february-buy",
        "user/preferences/no-leverage",
        "user/investment/context",
    ]
    positions = [text.find(f"] {memory_id}") for memory_id in expected_ids]
    _check("B1: build returns context", len(text) > 100)
    _check("B2: all required nodes present", all(position >= 0 for position in positions))
    _check("B3: dependencies precede target", all(position < positions[-1] for position in positions[:-1]))

    print("\n-- C. Proposal queue does not mutate target --")
    target_id = "user/test/adapter-proposal"
    target_path = _ROOT_PATH / f"{target_id}.md"
    _created_files.append(target_path)
    await sandbox.execute(
        "create_memory",
        {
            "id": target_id,
            "summary": "Before proposal",
            "body": "# Before\n\nOriginal canonical bytes.",
            "tags": ["adapter-alignment"],
        },
    )
    _check("C1: proposal target exists", target_path.exists())
    before = target_path.read_bytes()
    proposed = await sandbox.execute(
        "propose_memory",
        {
            "id": target_id,
            "reason": "Integration proposal",
            "summary": "After proposal",
            "body": "# After\n\nOwner-approved replacement.",
        },
    )
    proposal_id = proposed["result"].split(":", 1)[-1].strip()
    _check("C2: proposal queued", proposal_id.startswith("0"))
    _check("C3: target bytes unchanged before merge", target_path.read_bytes() == before)
    _check("C4: patch queue contains proposal", any(item.proposal_id == proposal_id for item in list_proposals(_ROOT_PATH)))
    handle_merge(_ROOT_PATH, proposal_id)
    merged_meta, merged_body = parse_frontmatter(target_path)
    _check(
        "C5: owner merge applies patch",
        merged_meta["version"] == 2
        and merged_meta["summary"] == "After proposal"
        and "Owner-approved replacement" in merged_body,
    )
    _check("C6: merged proposal leaves queue", all(item.proposal_id != proposal_id for item in list_proposals(_ROOT_PATH)))

    print("\n-- D. Proposed creation visibility --")
    pending_id = "user/test/adapter-pending"
    pending_path = _ROOT_PATH / f"{pending_id}.md"
    _created_files.append(pending_path)
    pending = await sandbox.execute(
        "create_memory",
        {
            "id": pending_id,
            "summary": "Pending owner review",
            "body": "# Pending\n\nNot canonical yet.",
            "tags": ["adapter-pending"],
            "propose": True,
        },
    )
    _check("D1: proposed creation succeeds", pending_path.exists() and "Status: proposed" in pending["result"])
    pending_meta, _ = parse_frontmatter(pending_path)
    _check("D2: proposed status persisted", pending_meta["status"] == "proposed")
    pending_search = await sandbox.execute("search_memories", {"query": "Pending owner review"})
    _check("D3: default search excludes proposed", pending_id not in pending_search["result"])
    try:
        await sandbox.execute("build_memory", {"id": pending_id})
    except ValueError as exc:
        _check("D4: build rejects proposed", "not assemblable" in str(exc))
    else:
        _check("D4: build rejects proposed", False, "build unexpectedly succeeded")

    print("\n-- Cleanup --")
    for path in _created_files:
        if path.exists():
            path.unlink()
            print(f"  deleted {path}")
    test_dir = _ROOT_PATH / "user/test"
    if test_dir.exists() and not any(test_dir.iterdir()):
        test_dir.rmdir()
    reindex(_ROOT_PATH)
    _check("CLEANUP: reindex back to 10 memories", len(load_index(_ROOT_PATH).memories) == 10)

    print("\n" + "=" * 62)
    total = passed + failed
    print(f"  Results: {passed}/{total} passed")
    if failed:
        raise SystemExit(1)
    print("  All tests PASSED")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(main())
