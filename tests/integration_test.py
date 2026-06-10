#!/usr/bin/env python3
"""integration_test.py — 5-scenario end-to-end test for codememory.

Covers: create+search, resolve context, update+stale, wander cold memory,
snapshot persistence.  Uses the Python API and Sandbox interface.

Usage::

    PYTHONPATH=src python tests/integration_test.py
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Ensure src/ is on the path
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_ROOT = "examples/investment"
_ROOT_PATH = Path(_ROOT).resolve()

# ---------- test state ----------
passed = 0
failed = 0
_created_files: list[Path] = []


def _check(name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


# ===================================================================
# Scenario A — Create + Search
# ===================================================================

async def test_a_create_and_search(sandbox):
    """Create an atom, then search for it by tags and verify it appears."""
    print("\n-- A. Create + Search --")

    # Create
    res = await sandbox.execute("create_memory", {
        "type": "atom",
        "id": "user/test/sprint5-a-test",
        "tags": ["test", "sprint5", "scenario-a"],
        "intensity": 5,
        "root": _ROOT,
    })
    create_result = res.get("result", str(res))
    _check("A1: create returns path", ".md" in str(create_result))

    test_file = _ROOT_PATH / "user" / "test" / "sprint5-a-test.md"
    _created_files.append(test_file)
    _check("A2: file exists on disk", test_file.exists())

    # Search by tags — search handler now returns {"result": <formatted string>}
    res = await sandbox.execute("search_memories", {
        "tags": ["sprint5", "scenario-a"],
        "root": _ROOT,
    })
    result_text = res.get("result", str(res))
    _check("A3: search by tags finds created memory", "sprint5-a-test" in result_text)
    _check("A4: search result matches created id", "sprint5-a-test" in result_text)


# ===================================================================
# Scenario B — Resolve Context
# ===================================================================

async def test_b_resolve_context(sandbox):
    """Resolve user/investment/context and verify topological order."""
    print("\n-- B. Resolve Context --")

    res = await sandbox.execute("resolve_context", {
        "id": "user/investment/context",
        "depth": "required",
        "root": _ROOT,
    })
    text = res.get("result", str(res))
    _check("B1: resolve returns text", len(text) > 100)

    # Actual memory IDs as they exist in examples/investment (6 required nodes)
    expected_ids = [
        "user/investment/risk-tolerance",
        "user/investment/semiconductor-thesis",
        "user/investment/current-holdings",
        "user/investment/february-buy",
        "user/preferences/no-leverage",
        "user/investment/context",
    ]
    # Find node positions by the heading pattern "### [N/6] <id>"
    positions: dict[str, int] = {}
    all_found = True
    for eid in expected_ids:
        # Unified pipeline heading format: "### [N/6] <id>"
        marker = f"] {eid}"
        idx = text.find(marker)
        if idx >= 0:
            prefix_start = max(0, idx - 10)
            if "### [" in text[prefix_start:idx]:
                positions[eid] = idx
            else:
                positions[eid] = -1
                all_found = False
        else:
            positions[eid] = -1
            all_found = False
    _check("B2: all 6 expected nodes found in resolve output", all_found)

    # Topological order: composite should be last (all deps before it)
    composite_pos = positions.get("user/investment/context", -1)
    deps_before = True
    for eid in expected_ids[:-1]:
        dep_pos = positions.get(eid, -1)
        if dep_pos < 0 or dep_pos >= composite_pos:
            deps_before = False
            break
    _check("B3: all deps appear before context (topo order)", deps_before)


# ===================================================================
# Scenario C — Update + Stale Detection
# ===================================================================

async def test_c_update_and_stale(sandbox):
    """Update body without summary -> stale detected. Fix summary -> stale gone."""
    print("\n-- C. Update + Stale Detection --")

    # Create a test memory
    res = await sandbox.execute("create_memory", {
        "type": "atom",
        "id": "user/test/sprint5-c-stale",
        "tags": ["test", "sprint5", "scenario-c"],
        "intensity": 5,
        "root": _ROOT,
    })
    test_file = _ROOT_PATH / "user" / "test" / "sprint5-c-stale.md"
    _created_files.append(test_file)
    _check("C1: create returns path", test_file.exists())

    # Step 1: Set body + summary together (summary_hash will match body)
    test_body = "## Test Body\n\nInitial content for stale test."
    test_summary = "Stale test initial summary."

    res = await sandbox.execute("update_memory", {
        "id": "user/test/sprint5-c-stale",
        "change_note": "Set initial body and summary",
        "body": test_body,
        "summary": test_summary,
        "root": _ROOT,
    })
    _check("C2: initial update succeeds", ".md" in res.get("result", ""))

    # Step 2: Overview fresh memory — should NOT be stale
    # Use default format to avoid inject-format line truncation hiding [stale]
    res = await sandbox.execute("overview", {
        "tags": ["test", "sprint5", "scenario-c"],
        "limit": 10,
        "format": "default",
        "root": _ROOT,
    })
    overview_text = res.get("result", str(res))
    no_stale = "[stale]" not in overview_text
    _check("C3: freshly updated memory is NOT stale", no_stale)

    # Step 3: Update body alone (NOT summary) — triggers stale
    new_body = test_body + "\n\nExtra line added to make body differ."
    res = await sandbox.execute("update_memory", {
        "id": "user/test/sprint5-c-stale",
        "change_note": "Change body without updating summary",
        "body": new_body,
        "root": _ROOT,
    })
    _check("C4: body-only update succeeds", ".md" in res.get("result", ""))

    # Step 4: Overview should now show stale
    res = await sandbox.execute("overview", {
        "tags": ["test", "sprint5", "scenario-c"],
        "limit": 10,
        "format": "default",
        "root": _ROOT,
    })
    overview_text = res.get("result", str(res))
    is_stale = "[stale]" in overview_text
    _check("C5: stale detected after body-only update", is_stale)

    # Step 5: Update summary to fix stale
    res = await sandbox.execute("update_memory", {
        "id": "user/test/sprint5-c-stale",
        "change_note": "Fix summary to match new body",
        "summary": "Fixed summary matching updated body.",
        "root": _ROOT,
    })
    _check("C6: summary update succeeds", ".md" in res.get("result", ""))

    # Step 6: Verify stale is gone
    res = await sandbox.execute("overview", {
        "tags": ["test", "sprint5", "scenario-c"],
        "limit": 10,
        "format": "default",
        "root": _ROOT,
    })
    overview_text = res.get("result", str(res))
    stale_gone = "[stale]" not in overview_text
    _check("C7: stale disappears after summary update", stale_gone)


# ===================================================================
# Scenario D — Wander Cold Memory
# ===================================================================

async def test_d_wander_cold_memory(sandbox):
    """Wander/recall returns a low-access-count memory with relevant metadata."""
    print("\n-- D. Wander Cold Memory --")

    # Use overview --with-recall to get a recall line
    res = await sandbox.execute("overview", {
        "limit": 20,
        "with_recall": True,
        "format": "inject",
        "root": _ROOT,
    })
    text = res.get("result", str(res))
    recall_found = "[recall]" in text
    _check("D1: wander/recall returns a [recall] line", recall_found)

    # The recall line should contain a memory id and summary
    if recall_found:
        for line in text.split("\n"):
            if "[recall]" in line:
                # Format: [recall] <id> -- <summary>（tags: ...）
                _check("D2: recall line has memory id", " — " in line or "--" in line)
                _check("D3: recall line has tags", "tags:" in line.lower() or "（" in line)
                break


# ===================================================================
# Scenario E — Snapshot Persistence
# ===================================================================

async def test_e_snapshot_persistence(sandbox):
    """Create a TransientDAG, snapshot it, verify the .md can be resolved."""
    print("\n-- E. Snapshot Persistence --")

    from codememory.transient import TransientDAG

    # Build a transient DAG with two transient nodes
    dag = TransientDAG()
    dag.add(
        "s/step-data",
        type="atom",
        summary="Raw data collected during session",
        body="## Session Data\n\nCollected Q1 earnings data: revenue +15%, profit +8%.\n",
        intensity=6,
    )
    dag.add(
        "s/step-analysis",
        type="atom",
        summary="Analysis derived from session data",
        body="## Session Analysis\n\nBased on Q1 data: growth is accelerating, "
             "sector rotation toward tech continues.\n",
        imports={"required": ["s/step-data"]},
        intensity=7,
    )

    dag_dict = dag.to_dict()
    snapshot_id = f"sprint5-e-{datetime.now().strftime('%H%M%S')}"

    res = await sandbox.execute("snapshot", {
        "id": snapshot_id,
        "dag_data": dag_dict,
        "root": _ROOT,
    })
    snap_result = res.get("result", str(res))
    _check("E1: snapshot returns path", ".md" in snap_result)

    # Find the snapshot file
    snap_dir = _ROOT_PATH / "user" / "snapshots"
    candidates = sorted(snap_dir.glob(f"*-{snapshot_id}.md"))
    _check("E2: snapshot file created on disk", len(candidates) > 0)
    if candidates:
        snap_file = candidates[0]
        _created_files.append(snap_file)

        # Verify the file has expected frontmatter and body content
        raw = snap_file.read_text(encoding="utf-8")
        _check("E3: snapshot has frontmatter", raw.startswith("---"))
        _check("E4: snapshot contains session data", "Q1 earnings" in raw)
        _check("E5: snapshot contains analysis", "growth is accelerating" in raw)


# ===================================================================
# Main
# ===================================================================

async def main():
    global passed, failed

    from harnesslib.sandbox import Sandbox
    from codememory.integrations import CodememoryToolkit

    print("=" * 62)
    print("  CodeMemory Integration Test -- Sprint 5")
    print("=" * 62)

    # Initialize sandbox with codememory tools
    toolkit = CodememoryToolkit(root=_ROOT)
    sandbox = Sandbox()
    await toolkit.register_to_sandbox(sandbox)

    names = [t.name for t in sandbox.list_tools()]
    _check("INIT: 12 tools registered", len(names) == 12, f"got {len(names)}")

    # Run all scenarios
    await test_a_create_and_search(sandbox)
    await test_b_resolve_context(sandbox)
    await test_c_update_and_stale(sandbox)
    await test_d_wander_cold_memory(sandbox)
    await test_e_snapshot_persistence(sandbox)

    # ── Cleanup ──────────────────────────────────────────────────────
    print("\n-- Cleanup --")
    for f in _created_files:
        if f.exists():
            f.unlink()
            print(f"  deleted {f}")

    # Remove empty directories
    for subdir in ["test", "snapshots"]:
        d = _ROOT_PATH / "user" / subdir
        if d.exists():
            for leftover in d.glob("*.md"):
                leftover.unlink()
                print(f"  deleted leftover {leftover}")
            try:
                next(d.iterdir())
            except StopIteration:
                d.rmdir()
                print(f"  removed empty dir {d}")

    # Reindex to clean state
    from codememory.index import reindex, load_index
    reindex(_ROOT_PATH)
    idx = load_index(_ROOT_PATH)
    count = len(idx.memories)
    _check("CLEANUP: reindex back to 10 memories", count == 10, f"got {count}")

    # ── Summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    total = passed + failed
    print(f"  Results: {passed}/{total} passed")
    if failed > 0:
        print(f"  {failed} FAILURES")
        sys.exit(1)
    else:
        print("  All tests PASSED")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(main())
