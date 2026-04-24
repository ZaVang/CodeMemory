"""
LLM Bridge — Main entry point.

``LLMBridge`` is the **only** class external code needs to interact with.
It dispatches calls to the correct provider, handles key rotation,
retry with exponential backoff, and dynamic fallback.
"""

from __future__ import annotations

import asyncio
import functools
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Type, TypeVar, Union

from pydantic import BaseModel

# ── Optional tracing integration ──
# If a tracing module is available, LLM calls and tool executions
# are recorded automatically. Otherwise, tracing is silently skipped.
try:
    from harnesslib._tracing import (
        get_current_trace as _get_trace,
        AgentSessionEntry as _AgentSessionEntry,
        LLMCallEntry as _LLMCallEntry,
        ToolCallEntry as _ToolCallEntry,
    )
except ImportError:
    _get_trace = None  # type: ignore[assignment]
    _AgentSessionEntry = None  # type: ignore[assignment,misc]
    _LLMCallEntry = None  # type: ignore[assignment,misc]
    _ToolCallEntry = None  # type: ignore[assignment,misc]

from .circuit_breaker import CircuitBreaker
from .config import load_config
from .models import BridgeConfig, ChatParameters, ModelConfig, UnifiedResponse
from .providers import PROVIDER_REGISTRY, BaseProvider
from .router import KeyRotator, fallback_chain, retry_with_backoff
from .skills import LLMBridgeError, SkillLoader
from .tools import BridgeTool

logger = logging.getLogger(__name__)


class LLMBridge:
    """Unified, multi-provider LLM gateway.

    ``LLMBridge`` is the single entry-point for all LLM interactions.
    It routes requests to OpenAI, Anthropic, or Google based on the
    model string, handles API-key rotation, exponential-backoff retry,
    and dynamic fallback across models.

    Examples
    --------
    **Basic text completion:**

    .. code-block:: python

        import asyncio
        from llm_bridge import LLMBridge

        async def main():
            bridge = LLMBridge.from_config("llm_bridge_config.yaml")

            # Simple text response
            response = await bridge.chat(
                model="openai/gpt-4o",
                messages=[{"role": "user", "content": "Hello!"}],
            )
            print(response.content)        # "Hello! How can I help you?"
            print(response.usage)          # UsageInfo(input_tokens=10, ...)
            print(response.stop_reason)    # "stop"
            print(response.model_id)       # "chatcmpl-abc123..."

        asyncio.run(main())

    **Structured output with Pydantic:**

    .. code-block:: python

        from pydantic import BaseModel
        from llm_bridge import LLMBridge, ChatParameters

        class MovieReview(BaseModel):
            title: str
            rating: float
            pros: list[str]
            cons: list[str]

        async def main():
            bridge = LLMBridge.from_config("llm_bridge_config.yaml")

            response = await bridge.chat(
                model="google/gemini-2.0-flash",
                messages=[{"role": "user", "content": "Review the movie Inception"}],
                response_model=MovieReview,
                params=ChatParameters(
                    temperature=0.3,
                    max_tokens=32000,
                    system_prompt="You are a professional film critic.",
                ),
            )
            review = response.parsed  # MovieReview instance
            print(f"{review.title}: {review.rating}/10")
            print(f"Pros: {review.pros}")

    **Using a config alias with fallback:**

    .. code-block:: python

        # In llm_bridge_config.yaml:
        #   models:
        #     fast:
        #       provider: openai
        #       model: gpt-4o
        #       fallback_models: [gemini_flash]

        response = await bridge.chat(
            model="fast",  # uses config alias
            messages=[{"role": "user", "content": "Summarize this text..."}],
            params=ChatParameters(max_tokens=500, top_p=0.9),
        )
    """

    def __init__(self, config: BridgeConfig, *, config_path: Optional[Path] = None) -> None:
        self._config = config
        self._providers: dict[str, BaseProvider] = {}
        self._key_rotators: dict[str, KeyRotator] = {}
        self._circuit_breaker = CircuitBreaker()

        # Pre-instantiate providers and key rotators from config.
        for alias, model_cfg in config.models.items():
            provider_name = model_cfg.provider.lower()
            if provider_name not in PROVIDER_REGISTRY:
                raise ValueError(
                    f"Unknown provider '{provider_name}' for model '{alias}'. "
                    f"Available: {list(PROVIDER_REGISTRY.keys())}"
                )
            self._providers[alias] = PROVIDER_REGISTRY[provider_name]()
            # Filter out empty strings — YAML ${VAR:-} expands to "" when unset.
            valid_keys = [k for k in model_cfg.api_keys if k]
            if valid_keys:
                self._key_rotators[alias] = KeyRotator(valid_keys)

        # ------------------------------------------------------------------
        # Skill loader — resolve skills_dir and create SkillLoader if present
        # ------------------------------------------------------------------
        if config.skills_dir:
            raw = Path(config.skills_dir)
            resolved_skills_dir: Optional[Path] = (
                raw if raw.is_absolute()
                else (config_path.parent.parent / raw if config_path else raw)
            )
        elif config_path is not None:
            # Default: look for 'skills/' next to the config file
            resolved_skills_dir = config_path.parent.parent / "skills"
        else:
            resolved_skills_dir = None

        self._skill_loader: Optional[SkillLoader] = (
            SkillLoader(resolved_skills_dir)
            if resolved_skills_dir is not None and resolved_skills_dir.exists()
            else None
        )

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_config(cls, path: Union[str, Path]) -> "LLMBridge":
        """Create an ``LLMBridge`` from a YAML configuration file.

        Parameters
        ----------
        path :
            Path to a ``llm_bridge_config.yaml`` file.  Environment
            variables like ``${OPENAI_API_KEY}`` are resolved automatically.
        """
        config_path = Path(path).resolve()
        return cls(load_config(config_path), config_path=config_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def chat(
        self,
        model: str,
        messages: list[dict],
        *,
        response_model: Optional[Type[BaseModel]] = None,
        params: Optional[ChatParameters] = None,
        skills: Optional[list[str]] = None,
        skill_vars: Optional[dict] = None,
        tools: Optional[list[BridgeTool]] = None,
        max_tool_rounds: int = 10,
        **kwargs,
    ) -> UnifiedResponse:
        """Send a chat request through the bridge.

        This is the **primary method** for all LLM interactions.

        Parameters
        ----------
        model :
            Either a config alias (e.g. ``"gpt4o"``, ``"fast"``) defined
            in your YAML config, or an inline ``"provider/model"`` string
            (e.g. ``"openai/gpt-4o"``, ``"anthropic/claude-sonnet-4"``).

        messages :
            OpenAI-style message list::

                [
                    {"role": "system", "content": "You are helpful."},
                    {"role": "user", "content": "Hello!"},
                ]

            Note: for Anthropic, system messages should be passed via
            ``params.system_prompt`` instead of inline messages.

        response_model :
            Optional Pydantic model class.  When provided, the bridge
            requests structured (JSON) output from the provider and
            returns the parsed model in ``response.parsed``.

        params :
            Optional ``ChatParameters`` controlling generation behaviour.
            All fields are optional and provider-agnostic — the bridge
            maps them to the correct SDK-specific names automatically::

                params = ChatParameters(
                    max_tokens=32000,          # → OpenAI: max_completion_tokens
                                              # → Anthropic: max_tokens
                                              # → Google: max_output_tokens
                    temperature=0.5,
                    top_p=0.9,
                    top_k=40,                 # Anthropic & Google only
                    frequency_penalty=0.3,    # OpenAI & Google only
                    presence_penalty=0.3,     # OpenAI & Google only
                    stop_sequences=["END"],
                    seed=42,                  # OpenAI & Google only
                    system_prompt="Be concise.",
                )

        **kwargs :
            Additional provider-specific arguments forwarded directly
            to the SDK call.

        tools :
            Optional list of :class:`BridgeTool` instances.  When provided,
            the bridge enters an **agentic loop**: it passes the tool
            definitions to the model, executes any requested tool calls
            locally, appends the results, and calls the model again —
            repeating until the model stops requesting tools or
            ``max_tool_rounds`` is reached.

        max_tool_rounds :
            Maximum number of model ↔ tool-execution cycles (default 10).
            Prevents infinite loops when the model keeps requesting tools.

        Returns
        -------
        UnifiedResponse
            Contains ``content``, ``parsed``, ``usage``, ``stop_reason``,
            and ``model_id`` regardless of which provider was used.

        Raises
        ------
        RuntimeError
            If all retry attempts and fallback models are exhausted.
        ValueError
            If the model string cannot be resolved.

        Example
        -------
        >>> response = await bridge.chat(
        ...     model="openai/gpt-4o",
        ...     messages=[{"role": "user", "content": "Hello!"}],
        ...     params=ChatParameters(temperature=0.2, max_tokens=32000),
        ... )
        >>> print(response.content)
        >>> print(response.usage.total_tokens)
        """

        # ------------------------------------------------------------------
        # Skill injection — load and merge into system prompt
        # ------------------------------------------------------------------
        if skills:
            if self._skill_loader is None:
                raise LLMBridgeError(
                    "Cannot load skills: no skills directory is configured or the "
                    "directory does not exist. Set 'skills_dir' in your config YAML."
                )
            skill_content = self._skill_loader.load_many(skills, skill_vars)
            existing_system = params.system_prompt if params else None
            merged_system = (
                skill_content
                if not existing_system
                else f"{skill_content}\n\n---\n\n{existing_system}"
            )
            # Create a NEW ChatParameters — never mutate the caller's object.
            params = (params or ChatParameters()).model_copy(
                update={"system_prompt": merged_system}
            )

        logger.info(
            "LLM 调用开始 [model=%s, structured=%s]",
            model,
            response_model.__name__ if response_model else "—",
        )
        model_cfg = self._resolve_model(model)
        alias = model  # keep for logging

        # ── Tool use: enter agentic loop ──────────────────────────────────────
        if tools:
            return await self._chat_with_tools(
                model_cfg=model_cfg,
                alias=alias,
                messages=messages,
                tools=tools,
                response_model=response_model,
                params=params,
                max_tool_rounds=max_tool_rounds,
                **kwargs,
            )

        # Build the primary call
        primary = functools.partial(
            self._call_model, model_cfg, messages, response_model, params,
            _config_alias=alias, **kwargs
        )

        # Build fallback callables
        fallback_fns = []
        for fb_model_str in model_cfg.fallback_models:
            fb_cfg = self._resolve_model(fb_model_str)
            fallback_fns.append(
                functools.partial(
                    self._call_model, fb_cfg, messages, response_model, params,
                    _config_alias=fb_model_str, **kwargs
                )
            )

        if fallback_fns:
            response = await fallback_chain(primary, fallback_fns)
        else:
            response = await primary()

        # Optional token-usage logging
        if self._config.log_usage:
            logger.info(
                "[%s] %s/%s — in: %d  out: %d  total: %d  reason: %s",
                alias,
                response.provider,
                response.model,
                response.usage.input_tokens,
                response.usage.output_tokens,
                response.usage.total_tokens,
                response.stop_reason,
            )

        return response

    _T = TypeVar("_T")

    async def chat_with_feedback(
        self,
        model: str,
        messages: list[dict],
        parse: "Callable[[str], _T]",
        *,
        max_attempts: int = 3,
        params: Optional[ChatParameters] = None,
        **kwargs,
    ) -> "_T":
        """带错误反馈的 LLM 重试。

        首次调用正常。若 ``parse(raw)`` 抛出异常，将 LLM 上一次的错误输出
        和错误信息追加为新的 user turn，让 LLM 看到自己的错误并自我纠正，
        然后重试，最多 ``max_attempts`` 次。最后一次仍失败时透传异常。

        Parameters
        ----------
        model:
            模型别名，同 ``chat()``。
        messages:
            初始消息列表，同 ``chat()``。
        parse:
            调用方提供的解析函数 ``raw: str → T``。
            parse 抛出任何异常时视为"输出不合规"，触发重试。
        max_attempts:
            最大尝试次数（含首次），默认 3。
        params:
            ChatParameters，同 ``chat()``。
        """
        current_messages = list(messages)
        last_exc: BaseException | None = None
        for attempt in range(max_attempts):
            response = await self.chat(
                model=model, messages=current_messages, params=params, **kwargs
            )
            raw = response.content or ""
            try:
                return parse(raw)
            except Exception as exc:
                last_exc = exc
                if attempt < max_attempts - 1:
                    logger.warning(
                        "chat_with_feedback attempt %d/%d 输出不合规 (%s)，携带错误反馈重试",
                        attempt + 1,
                        max_attempts,
                        exc,
                    )
                    current_messages = [
                        *current_messages,
                        {"role": "assistant", "content": raw},
                        {
                            "role": "user",
                            "content": (
                                f"你的输出不符合格式要求，错误：{exc}\n"
                                "请严格按要求重新输出，不要输出任何说明或额外内容。"
                            ),
                        },
                    ]
        raise last_exc  # type: ignore[misc]

    async def get_available_models(
        self, *, timeout: float = 10.0
    ) -> dict[str, list[str]]:
        """Query all configured providers for their available remote models.

        Only queries providers that have a valid (non-empty) API key configured.
        All qualifying providers are queried concurrently with a per-provider
        timeout so a slow or unresponsive provider never blocks the call.

        Parameters
        ----------
        timeout :
            Per-provider timeout in seconds (default 10 s).

        Returns
        -------
        dict[str, list[str]]
            A mapping of provider name (e.g., 'openai', 'anthropic', 'google')
            to a list of their supported model IDs.  Providers that time out or
            raise an exception are returned with an empty list.
        """
        # Collect one entry per provider — first alias that has a valid key wins.
        # Structure: {provider_name: (alias, api_key, extra)}
        provider_to_query: dict[str, tuple[str, str, dict]] = {}
        for alias, model_cfg in self._config.models.items():
            provider_name = model_cfg.provider.lower()
            if provider_name in provider_to_query:
                continue

            rotator = self._key_rotators.get(alias)
            if rotator is None:
                # No rotator means no valid key was configured for this alias.
                logger.debug("Skipping list_models for '%s': no valid API key.", alias)
                continue
            api_key = rotator.next()
            provider_to_query[provider_name] = (alias, api_key, model_cfg.extra)

        if not provider_to_query:
            return {}

        logger.debug("Querying model lists for providers: %s", list(provider_to_query))

        # Query all providers concurrently, each with an individual timeout.
        async def _query(provider_name: str, alias: str, api_key: str, extra: dict) -> tuple[str, list[str]]:
            provider = self._providers[alias]
            try:
                models = await asyncio.wait_for(
                    provider.list_models(api_key=api_key, **extra),
                    timeout=timeout,
                )
                logger.debug("list_models '%s': %d models returned.", provider_name, len(models))
                return provider_name, models
            except asyncio.TimeoutError:
                logger.warning("list_models '%s': timed out after %.1fs.", provider_name, timeout)
                return provider_name, []
            except Exception as e:
                logger.warning("list_models '%s': failed — %s", provider_name, e)
                return provider_name, []

        results = await asyncio.gather(
            *[
                _query(pname, alias, api_key, extra)
                for pname, (alias, api_key, extra) in provider_to_query.items()
            ]
        )
        return dict(results)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _chat_with_tools(
        self,
        *,
        model_cfg: ModelConfig,
        alias: str,
        messages: list[dict],
        tools: list[BridgeTool],
        response_model,
        params,
        max_tool_rounds: int,
        **kwargs,
    ) -> UnifiedResponse:
        """Agentic tool loop: call → execute tools (parallel) → call again until done."""
        import uuid
        from .models import ToolParam

        tool_map = {t.definition.name: t for t in tools}
        tool_defs: list[ToolParam] = [t.definition for t in tools]

        current_messages = list(messages)
        last_response = None

        # Session-level tracking
        session_id = str(uuid.uuid4())
        session_start = time.perf_counter()
        total_input_tokens = 0
        total_output_tokens = 0
        tool_sequence: list[str] = []

        for round_num in range(max_tool_rounds):
            response = await self._call_model(
                model_cfg,
                current_messages,
                response_model,
                params,
                _config_alias=alias,
                _tools=tool_defs,
                **kwargs,
            )
            last_response = response

            # Accumulate token usage
            total_input_tokens += response.usage.input_tokens
            total_output_tokens += response.usage.output_tokens

            if not response.tool_calls:
                # Model is done — record session and return final answer
                trace = _get_trace() if _get_trace else None
                if trace:
                    trace.record_agent_session(_AgentSessionEntry(
                        session_id=session_id,
                        turns=round_num + 1,
                        tool_sequence=tool_sequence,
                        total_input_tokens=total_input_tokens,
                        total_output_tokens=total_output_tokens,
                        stop_reason="end_turn",
                        duration_ms=(time.perf_counter() - session_start) * 1000,
                    ))
                return response

            logger.info(
                "[%s] tool round %d/%d — %d tool call(s): %s",
                alias,
                round_num + 1,
                max_tool_rounds,
                len(response.tool_calls),
                [tc.name for tc in response.tool_calls],
            )

            # Track tool sequence
            tool_sequence.extend(tc.name for tc in response.tool_calls)

            # Append the assistant turn (with tool_calls) in OpenAI format
            current_messages.append({
                "role": "assistant",
                "content": response.content or "",
                "tool_calls": [
                    {
                        "id": tc.tool_use_id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.input),
                        },
                    }
                    for tc in response.tool_calls
                ],
            })

            # Execute all tools in parallel
            async def _run_one(tc):
                t0 = time.perf_counter()
                tool = tool_map.get(tc.name)
                if tool is None:
                    logger.warning("Unknown tool requested: %s", tc.name)
                    result = f"Error: unknown tool '{tc.name}'"
                    error = f"unknown tool '{tc.name}'"
                else:
                    try:
                        result = await tool.run(**tc.input)
                        error = None
                    except Exception as exc:
                        result = f"Error executing {tc.name}: {exc}"
                        error = str(exc)
                        logger.warning("Tool %s raised: %s", tc.name, exc)
                duration_ms = (time.perf_counter() - t0) * 1000
                return tc, result, error, duration_ms

            outcomes = await asyncio.gather(*[_run_one(tc) for tc in response.tool_calls])

            # Record tool calls to trace and append results to messages
            trace = _get_trace() if _get_trace else None
            for tc, result, error, duration_ms in outcomes:
                if trace and _ToolCallEntry:
                    trace.record_tool_call(_ToolCallEntry(
                        tool_use_id=tc.tool_use_id,
                        name=tc.name,
                        arguments=tc.input,
                        result=result if not error else None,
                        error=error,
                        duration_ms=duration_ms,
                    ))
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tc.tool_use_id,
                    "content": result,
                })

        logger.warning(
            "[%s] max_tool_rounds=%d reached — returning last response.",
            alias,
            max_tool_rounds,
        )
        # Record session at max_rounds exit
        trace = _get_trace() if _get_trace else None
        if trace and _AgentSessionEntry:
            trace.record_agent_session(_AgentSessionEntry(
                session_id=session_id,
                turns=max_tool_rounds,
                tool_sequence=tool_sequence,
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
                stop_reason="max_tool_rounds",
                duration_ms=(time.perf_counter() - session_start) * 1000,
            ))
        return last_response  # type: ignore[return-value]

    def _resolve_model(self, model: str) -> ModelConfig:
        """Resolve a model alias or ``provider/model`` string."""
        # 1. Check config aliases
        if model in self._config.models:
            return self._config.models[model]

        # 2. Parse inline "provider/model"
        if "/" in model:
            provider, model_name = model.split("/", 1)
            return ModelConfig(provider=provider, model=model_name)

        # 3. Try default
        if (
            self._config.default_model
            and self._config.default_model in self._config.models
        ):
            return self._config.models[self._config.default_model]

        raise ValueError(
            f"Cannot resolve model '{model}'. "
            f"Known aliases: {list(self._config.models.keys())}"
        )

    async def _call_model(
        self,
        model_cfg: ModelConfig,
        messages: list[dict],
        response_model: Optional[Type[BaseModel]],
        params: Optional[ChatParameters],
        *,
        _config_alias: Optional[str] = None,
        _tools=None,
        **kwargs,
    ) -> UnifiedResponse:
        """Execute a single model call with retry + key rotation."""
        provider_name = model_cfg.provider.lower()
        provider_cls = PROVIDER_REGISTRY.get(provider_name)
        if provider_cls is None:
            raise ValueError(f"No provider registered for '{provider_name}'.")

        adapter = provider_cls()

        # Determine API key: prefer rotator keyed by config alias (round-robin),
        # then fall back to first key in model_cfg, then empty string.
        rotator = self._key_rotators.get(_config_alias) if _config_alias else None
        if rotator:
            api_key = rotator.next()
        elif model_cfg.api_keys:
            api_key = model_cfg.api_keys[0]
        else:
            api_key = ""

        # Build default ChatParameters from config if caller didn't provide
        effective_params = params or ChatParameters()
        if effective_params.max_tokens is None and model_cfg.max_tokens:
            effective_params = effective_params.model_copy(
                update={"max_tokens": model_cfg.max_tokens}
            )
        if effective_params.temperature is None and model_cfg.temperature is not None:
            effective_params = effective_params.model_copy(
                update={"temperature": model_cfg.temperature}
            )

        # Merge extra kwargs from config
        merged_kwargs = {**model_cfg.extra, **kwargs}

        async def _do_call() -> UnifiedResponse:
            t0 = time.perf_counter()
            unified, raw = await adapter.chat(
                model=model_cfg.model,
                messages=messages,
                api_key=api_key,
                response_model=response_model,
                params=effective_params,
                tools=_tools,
                **merged_kwargs,
            )
            latency_ms = (time.perf_counter() - t0) * 1000

            trace = _get_trace() if _get_trace else None
            if trace is not None and _LLMCallEntry:
                trace.record_llm_call(_LLMCallEntry(
                    called_at=datetime.now(timezone.utc).isoformat(),
                    model=unified.model,
                    provider=unified.provider,
                    messages=messages,
                    raw_response=raw,
                    content=unified.content,
                    parsed=unified.parsed.model_dump(mode="json") if unified.parsed else None,
                    usage=unified.usage.model_dump(),
                    stop_reason=unified.stop_reason,
                    latency_ms=latency_ms,
                ))

            return unified

        model_key = f"{model_cfg.provider}/{model_cfg.model}"

        async def _guarded_call() -> UnifiedResponse:
            if self._circuit_breaker.is_open(model_key):
                raise RuntimeError(
                    f"Circuit breaker OPEN for '{model_key}' — skipping call"
                )
            try:
                result = await _do_call()
                self._circuit_breaker.record_success(model_key)
                return result
            except Exception:
                self._circuit_breaker.record_failure(model_key)
                raise

        return await retry_with_backoff(
            _guarded_call,
            retry_config=self._config.retry,
        )
