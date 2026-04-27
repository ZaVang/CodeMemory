#!/usr/bin/env python3
"""example_agent.py — Minimal Agent demonstrating codememory integration.

Shows the complete loop: memory search → create new memory → resolve context
→ produce an answer.  Uses a mock LLM handler — no API key required.

Usage::

    PYTHONPATH=src python examples/example_agent.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: ensure src/ is on the path so local packages are importable.
# ---------------------------------------------------------------------------
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


# ===================================================================
# Mock LLM — simulates agent reasoning without real API calls
# ===================================================================

class MockLLM:
    """Simulates LLM responses for demonstration purposes.

    Instead of calling a real model, this mock returns pre-scripted
    tool-use responses that drive the agent through the full workflow.
    """

    def __init__(self) -> None:
        self._turn = 0
        _root = "examples/investment"
        # Pre-scripted agent "thoughts" — each turn the mock returns
        # a tool_call intent (search -> create -> resolve -> answer).
        self._script = [
            # Turn 0: Search existing memories
            {
                "tool_calls": [
                    {
                        "name": "search_memories",
                        "input": {
                            "query": "risk tolerance",
                            "tags": ["investment"],
                            "root": _root,
                        },
                    },
                ],
                "content": "Let me check if we have any risk-related memories.",
            },
            # Turn 1: Create a new memory (found nothing relevant)
            {
                "tool_calls": [
                    {
                        "name": "create_memory",
                        "input": {
                            "type": "atom",
                            "id": "user/demo/demo-risk-note",
                            "tags": ["investment", "risk", "demo"],
                            "intensity": 6,
                            "root": _root,
                        },
                    },
                ],
                "content": "No existing risk note found. Let me create one.",
            },
            # Turn 2: Update the new memory with actual content
            {
                "tool_calls": [
                    {
                        "name": "update_memory",
                        "input": {
                            "id": "user/demo/demo-risk-note",
                            "change_note": "Fill in risk preference content from user input",
                            "body": (
                                "## Risk Preference\n\n"
                                "The user prefers a **moderate-aggressive** strategy:\n"
                                "- Max single position: 20%\n"
                                "- Preferred sectors: tech, healthcare\n"
                                "- No crypto or penny stocks\n"
                                "- Rebalance quarterly\n"
                            ),
                            "summary": (
                                "Risk preference: moderate-aggressive, max position 20%, "
                                "tech/healthcare focus, quarterly rebalance"
                            ),
                            "root": _root,
                        },
                    },
                ],
                "content": "Now let me fill in the actual risk preference content.",
            },
            # Turn 3: Resolve the context to verify the new memory is linked
            {
                "tool_calls": [
                    {
                        "name": "resolve_context",
                        "input": {
                            "id": "user/investment/context",
                            "depth": "recommended",
                            "root": _root,
                        },
                    },
                ],
                "content": "Let me verify the investment context resolves correctly.",
            },
            # Turn 4: Overview to see the final state
            {
                "tool_calls": [
                    {
                        "name": "overview",
                        "input": {"limit": 5, "format": "inject", "root": _root},
                    },
                ],
                "content": "Let me see the current memory overview.",
            },
            # Turn 5: Final answer (no tool calls)
            {
                "content": (
                    "Based on your memory graph:\n\n"
                    "Your risk profile is moderate-aggressive with a 20% max position "
                    "limit, focused on tech and healthcare. The investment context "
                    "shows you prefer quarterly rebalancing and avoid crypto. "
                    "Your recent decisions align with these constraints.\n\n"
                    "I have created a new risk note (user/demo/demo-risk-note) "
                    "that will be available for future sessions."
                ),
            },
        ]

    def next_response(self) -> dict:
        """Return the next pre-scripted response."""
        if self._turn >= len(self._script):
            return {"content": "I've completed the memory workflow."}
        resp = self._script[self._turn]
        self._turn += 1
        return resp


# ===================================================================
# Agent loop
# ===================================================================

async def run_agent():
    """Run the full agent workflow with mock LLM."""
    from harnesslib.sandbox import Sandbox
    from codememory.integrations import CodememoryToolkit

    # ── 1. Initialize components ──────────────────────────────────────
    print("=" * 62)
    print("  CodeMemory Agent Demo (mock LLM)")
    print("=" * 62)

    toolkit = CodememoryToolkit(root="examples/investment")
    sandbox = Sandbox()
    await toolkit.register_to_sandbox(sandbox)

    registered = [t.name for t in sandbox.list_tools()]
    print(f"\n[init] Registered {len(registered)} tools:")
    for name in registered:
        print(f"       - {name}")

    mock_llm = MockLLM()

    # ── 2. Conversation loop ──────────────────────────────────────────
    user_message = (
        "I prefer moderate-aggressive risk with max 20% single position. "
        "Please record this and check if it's consistent with my existing "
        "investment context."
    )
    print(f"\n[user] {user_message}")

    messages = [{"role": "user", "content": user_message}]
    turn = 0

    while True:
        response = mock_llm.next_response()
        if response is None:
            break

        # Check if the model wants to call tools
        tool_calls = response.get("tool_calls", [])
        assistant_text = response.get("content", "")

        print(f"\n[agent-turn {turn}] {assistant_text}")

        if not tool_calls:
            # Final answer — no more tool calls
            print(f"\n[final-answer]\n{assistant_text}")
            break

        # Execute all tool calls in parallel (simulated)
        for tc in tool_calls:
            name = tc["name"]
            payload = tc["input"]
            print(f"  -> calling {name}({_format_payload(payload)})")

            try:
                result = await sandbox.execute(name, payload)
                result_text = result.get("result", str(result))
                # Truncate long results for display
                if len(result_text) > 200:
                    result_text = result_text[:200] + "..."
                print(f"  <- {name}: {result_text}")
            except Exception as exc:
                print(f"  <- {name} ERROR: {exc}")

        turn += 1
        if turn > 10:
            print("\n[warning] Max turns reached — stopping.")
            break

    # ── 3. Cleanup — remove demo memory ───────────────────────────────
    print("\n" + "-" * 62)
    print("[cleanup] Removing demo memory...")
    demo_file = (
        Path("examples/investment/user/demo/demo-risk-note.md")
    )
    if demo_file.exists():
        demo_file.unlink()
        # Remove empty demo directory
        demo_dir = demo_file.parent
        try:
            next(demo_dir.iterdir())
        except StopIteration:
            demo_dir.rmdir()
    print("[cleanup] Done.")
    print("=" * 62)


def _format_payload(payload: dict) -> str:
    """Format a tool payload for display, truncating long values."""
    parts = []
    for k, v in payload.items():
        s = str(v)
        if len(s) > 60:
            s = s[:57] + "..."
        parts.append(f"{k}={s}")
    return ", ".join(parts)


# ===================================================================
# Entry point
# ===================================================================

if __name__ == "__main__":
    asyncio.run(run_agent())
