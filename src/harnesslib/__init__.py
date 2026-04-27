"""harnesslib — General-purpose Agent orchestration framework.

Inspired by the Anthropic Managed Agents Harness architecture.
Cross-project reusable, no business assumptions built in.

Core classes
------------
**Harness** — Agent main loop
    Manages the conversation lifecycle: receives user input, calls the LLM
    via ``llm_gateway.LLMBridge``, executes tool calls via ``Sandbox``,
    and loops until the model produces a final answer.

**Sandbox** — Tool execution environment
    In-memory tool registry.  All tools are registered with a name +
    ``ToolDefinition`` + async handler.  Tools are invoked through a
    unified ``execute(name, payload)`` interface.  There is no preset
    list of tools — the sandbox is a blank slate.

**ToolDefinition** — Tool descriptor
    Pydantic model with ``name``, ``description``, and optional
    ``input_schema`` (JSON Schema dict).

**SandboxBase** — Abstract sandbox interface
    ABC that defines the contract: ``register()``, ``execute()``,
    ``list_tools()``.  Implement this to create custom backends
    (e.g., remote sandbox, Docker sandbox).

Minimal example
---------------
>>> import asyncio
>>> from harnesslib.sandbox import Sandbox, ToolDefinition
>>>
>>> async def main():
...     sandbox = Sandbox()
...
...     # Register a tool
...     await sandbox.register(
...         ToolDefinition(
...             name="greet",
...             description="Greet a user by name",
...             input_schema={
...                 "type": "object",
...                 "properties": {"name": {"type": "string"}},
...                 "required": ["name"],
...             },
...         ),
...         handler=lambda p: {"result": f"Hello, {p['name']}!"},
...     )
...
...     # Execute it
...     result = await sandbox.execute("greet", {"name": "World"})
...     print(result["result"])  # "Hello, World!"
...
...     # List tools
...     print([t.name for t in sandbox.list_tools()])  # ['greet']
>>>
>>> asyncio.run(main())

Integration with codememory
---------------------------
>>> from codememory.integrations import CodememoryToolkit
>>> toolkit = CodememoryToolkit(root="examples/investment")
>>> await toolkit.register_to_sandbox(sandbox)
>>> # sandbox now has 9 memory tools (resolve_context, create_memory, ...)
"""

from .harness import Harness
from .sandbox import Sandbox, SandboxBase, ToolDefinition

__all__ = ["Harness", "Sandbox", "SandboxBase", "ToolDefinition"]