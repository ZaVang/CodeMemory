"""
LLM Bridge — Retry, fallback, and load-balancing router.

Provides resilience primitives that the ``LLMBridge`` class uses
internally so that callers never need to deal with rate limits,
transient errors, or key rotation.
"""

from __future__ import annotations

import asyncio
import itertools
import logging
import random
from typing import Any, Callable, Coroutine, Optional, Sequence

from .models import RetryConfig

logger = logging.getLogger(__name__)


class KeyRotator:
    """Thread-safe round-robin API-key rotator.

    Parameters
    ----------
    keys : list[str]
        One or more API keys to cycle through.
    """

    def __init__(self, keys: list[str]) -> None:
        if not keys:
            raise ValueError("At least one API key is required.")
        self._cycle = itertools.cycle(keys)

    def next(self) -> str:
        """Return the next API key."""
        return next(self._cycle)


async def retry_with_backoff(
    fn: Callable[..., Coroutine[Any, Any, Any]],
    *args: Any,
    retry_config: RetryConfig | None = None,
    retryable_exceptions: tuple[type[BaseException], ...] = (Exception,),
    **kwargs: Any,
) -> Any:
    """Execute *fn* with exponential-backoff retry.

    Parameters
    ----------
    fn :
        Async callable to execute.
    retry_config :
        Controls max retries, delays, and backoff multiplier.
        Falls back to ``RetryConfig()`` defaults when ``None``.
    retryable_exceptions :
        Tuple of exception types that should trigger a retry.
    """
    cfg = retry_config or RetryConfig()
    last_error: BaseException | None = None

    for attempt in range(1, cfg.max_retries + 1):
        try:
            return await fn(*args, **kwargs)
        except retryable_exceptions as exc:
            last_error = exc
            if attempt == cfg.max_retries:
                break
            delay = min(
                cfg.base_delay * (cfg.exponential_base ** (attempt - 1)),
                cfg.max_delay,
            )
            # Add jitter (±25 %) to prevent thundering-herd effects.
            jitter = delay * 0.25 * (2 * random.random() - 1)
            sleep_time = max(0, delay + jitter)
            logger.warning(
                "Attempt %d/%d failed (%s). Retrying in %.2fs …",
                attempt,
                cfg.max_retries,
                exc,
                sleep_time,
            )
            await asyncio.sleep(sleep_time)

    raise RuntimeError(
        f"All {cfg.max_retries} attempts failed. Last error: {last_error}"
    ) from last_error


async def fallback_chain(
    primary_fn: Callable[..., Coroutine[Any, Any, Any]],
    fallback_fns: Sequence[Callable[..., Coroutine[Any, Any, Any]]],
) -> Any:
    """Try *primary_fn*; on failure walk through *fallback_fns* in order.

    Each callable is expected to be a zero-argument async function
    (use ``functools.partial`` to bind arguments beforehand).
    """
    try:
        return await primary_fn()
    except Exception as primary_exc:
        logger.warning("Primary call failed (%s). Trying fallbacks …", primary_exc)
        for idx, fb_fn in enumerate(fallback_fns, start=1):
            try:
                return await fb_fn()
            except Exception as fb_exc:
                logger.warning(
                    "Fallback %d failed (%s).", idx, fb_exc
                )
        raise RuntimeError(
            "All fallback models exhausted."
        ) from primary_exc
