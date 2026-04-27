"""CodememoryToolkit — one-line integration facade for Agent harnesses.

Provides a single entry-point for registering all codememory tools with
harnesslib Sandbox or exporting them in OpenAI function-calling format.

Usage::

    from codememory.integrations import CodememoryToolkit

    # Option A: export for any OpenAI-compatible platform
    toolkit = CodememoryToolkit(root="examples/investment")
    tools = toolkit.get_tools_for_openai()
    # -> [{"type": "function", "function": {...}}, ...]

    # Option B: register with harnesslib Sandbox
    import asyncio
    from harnesslib.sandbox import Sandbox

    async def main():
        sandbox = Sandbox()
        await toolkit.register_to_sandbox(sandbox)
        # sandbox.list_tools() now includes 9 codememory tools

    asyncio.run(main())
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class CodememoryToolkit:
    """One-line integration facade for codememory.

    Encapsulates the codememory root directory and provides convenience
    methods for registering tools with Agent harnesses or exporting
    tool definitions for OpenAI-compatible platforms.

    Parameters
    ----------
    root :
        Path to the memory data root directory.  If ``None``, the
        ``CODEMEMORY_ROOT`` environment variable or current working
        directory is used.

    Examples
    --------
    >>> toolkit = CodememoryToolkit(root="examples/investment")
    >>> tools = toolkit.get_tools_for_openai()
    >>> len(tools)
    9
    """

    def __init__(self, root: str | None = None) -> None:
        self._root = root

    # ------------------------------------------------------------------
    # OpenAI format
    # ------------------------------------------------------------------

    def get_tools_for_openai(self) -> list[dict[str, Any]]:
        """Return all codememory tools in OpenAI function-calling format.

        Each tool is represented as::

            {
                "type": "function",
                "function": {
                    "name": "resolve_context",
                    "description": "...",
                    "parameters": {...}
                }
            }

        This format can be consumed directly by the OpenAI API, Anthropic
        API (via tool_use), or any platform that accepts the OpenAI tool
        schema.

        Returns
        -------
        list[dict]
            List of tool definitions, one per codememory operation.
        """
        from .tools import TOOL_DEFINITIONS

        tools: list[dict[str, Any]] = []
        for td in TOOL_DEFINITIONS:
            tools.append({
                "type": "function",
                "function": {
                    "name": td["name"],
                    "description": td["description"],
                    "parameters": td.get("input_schema", {}),
                },
            })
        return tools

    # ------------------------------------------------------------------
    # Sandbox integration
    # ------------------------------------------------------------------

    async def register_to_sandbox(self, sandbox) -> None:
        """Register all 9 codememory tools with a harnesslib Sandbox.

        Parameters
        ----------
        sandbox :
            A ``harnesslib.sandbox.Sandbox`` instance.

        Examples
        --------
        >>> import asyncio
        >>> from harnesslib.sandbox import Sandbox
        >>> from codememory.integrations import CodememoryToolkit
        >>>
        >>> async def main():
        ...     sandbox = Sandbox()
        ...     toolkit = CodememoryToolkit(root="examples/investment")
        ...     await toolkit.register_to_sandbox(sandbox)
        ...     names = [t.name for t in sandbox.list_tools()]
        ...     print(names)
        >>>
        >>> asyncio.run(main())
        """
        from .tools import register_all

        await register_all(sandbox)
