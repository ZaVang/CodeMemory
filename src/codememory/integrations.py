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

from copy import deepcopy
from typing import Any


class CodememoryToolkit:
    """One-line integration facade for codememory.

    Encapsulates the codememory root directory and provides convenience
    methods for registering tools with Agent harnesses or exporting
    tool definitions for OpenAI, Anthropic, and Google Gemini formats.

    Parameters
    ----------
    root :
        Path to the memory data root directory.  If ``None``, the
        ``CODEMEMORY_ROOT`` environment variable or current working
        directory is used.

    Examples
    --------
    >>> toolkit = CodememoryToolkit(root="examples/investment")
    >>>
    >>> # OpenAI format
    >>> openai_tools = toolkit.get_tools_for_openai()
    >>> len(openai_tools)
        13
    >>>
    >>> # Anthropic format
    >>> anthropic_tools = toolkit.get_tools_for_anthropic()
    >>> len(anthropic_tools)
        13
    >>>
    >>> # Gemini format
    >>> gemini_tools = toolkit.get_tools_for_gemini()
    >>> len(gemini_tools)
        13
    """

    def __init__(self, root: str | None = None) -> None:
        self._root = root

    def _bound_definitions(self) -> list[dict[str, Any]]:
        """Export schemas without a caller-controlled root parameter."""
        from .tools import TOOL_DEFINITIONS

        definitions = deepcopy(TOOL_DEFINITIONS)
        for definition in definitions:
            properties = definition.get("input_schema", {}).get("properties", {})
            properties.pop("root", None)
        return definitions

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
        tools: list[dict[str, Any]] = []
        for td in self._bound_definitions():
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
    # Anthropic format
    # ------------------------------------------------------------------

    def get_tools_for_anthropic(self) -> list[dict[str, Any]]:
        """Return all codememory tools in Anthropic tool_use format.

        Each tool is represented as::

            {
                "name": "resolve_context",
                "description": "...",
                "input_schema": {...}
            }

        This is the format expected by the Anthropic Messages API when
        passing tools directly (without the OpenAI-style ``"type": "function"``
        wrapper).

        Returns
        -------
        list[dict]
            List of tool definitions, one per codememory operation.
        """
        tools: list[dict[str, Any]] = []
        for td in self._bound_definitions():
            tools.append({
                "name": td["name"],
                "description": td["description"],
                "input_schema": td.get("input_schema", {}),
            })
        return tools

    # ------------------------------------------------------------------
    # Gemini format
    # ------------------------------------------------------------------

    def get_tools_for_gemini(self) -> list[dict[str, Any]]:
        """Return all codememory tools in Google Gemini function_declarations format.

        Each tool is represented as::

            {
                "name": "resolve_context",
                "description": "...",
                "parameters": {...}
            }

        This format matches the ``function_declarations`` array expected by
        the Google Gemini API.  Note that Google uses ``parameters`` as the
        schema key (vs. OpenAI/Anthropic ``input_schema`` / ``parameters``
        nesting).

        Returns
        -------
        list[dict]
            List of tool definitions, one per codememory operation.
        """
        tools: list[dict[str, Any]] = []
        for td in self._bound_definitions():
            tools.append({
                "name": td["name"],
                "description": td["description"],
                "parameters": td.get("input_schema", {}),
            })
        return tools

    # ------------------------------------------------------------------
    # Sandbox integration
    # ------------------------------------------------------------------

    async def register_to_sandbox(self, sandbox) -> None:
        """Register all codememory tools with a harnesslib Sandbox.

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
        from .core import get_root_dir
        from .tools import register_all

        await register_all(sandbox, str(get_root_dir(self._root)))
