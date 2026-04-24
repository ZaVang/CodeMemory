"""
src/llm_gateway/circuit_breaker.py — 两态熔断器。

设计：完全封装在 llm_gateway/ 内部，与 Agent / Pipeline 层解耦。

状态机：
  CLOSED（正常）──失败次数达阈值──> OPEN（屏蔽）
  OPEN ──recovery_timeout 到期──> CLOSED（自动恢复）

与降级链（fallback_chain）的配合：
  熔断后 bridge._call_model() 抛 RuntimeError，fallback_chain 捕获后
  尝试备选模型，实现"先熔断，再降级"的双重保护。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreaker:
    """两态熔断器（CLOSED ↔ OPEN）。

    Parameters
    ----------
    failure_threshold:
        连续失败多少次后触发熔断，默认 5。
    recovery_timeout:
        熔断后自动恢复的等待秒数，默认 120 秒。

    Usage
    -----
    breaker = CircuitBreaker()

    if breaker.is_open("openai/gpt-4o"):
        raise RuntimeError("Circuit open")
    try:
        result = await call_model(...)
        breaker.record_success("openai/gpt-4o")
    except Exception:
        breaker.record_failure("openai/gpt-4o")
        raise
    """

    failure_threshold: int = 5
    recovery_timeout: float = 120.0

    # 内部状态：不暴露为公共属性
    _failures: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    _open_until: dict[str, float] = field(default_factory=dict, init=False, repr=False)

    def is_open(self, key: str) -> bool:
        """检查指定 key 的熔断器是否处于 OPEN 状态。

        若恢复超时已到期，自动恢复为 CLOSED 并返回 False。
        """
        deadline = self._open_until.get(key)
        if deadline is None:
            return False
        if time.monotonic() >= deadline:
            # 自动恢复
            self._open_until.pop(key, None)
            self._failures.pop(key, None)
            logger.info("熔断器 [%s] 已自动恢复（CLOSED）", key)
            return False
        return True

    def record_success(self, key: str) -> None:
        """记录一次成功调用，清除该 key 的失败计数与熔断状态。"""
        was_open = key in self._open_until
        self._failures.pop(key, None)
        self._open_until.pop(key, None)
        if was_open:
            logger.info("熔断器 [%s] 在成功调用后恢复（CLOSED）", key)

    def record_failure(self, key: str) -> None:
        """记录一次失败调用。达到阈值时触发熔断（OPEN）。"""
        count = self._failures.get(key, 0) + 1
        self._failures[key] = count
        if count >= self.failure_threshold:
            deadline = time.monotonic() + self.recovery_timeout
            self._open_until[key] = deadline
            logger.warning(
                "熔断器 [%s] OPEN（连续失败 %d 次），%.0f 秒后自动恢复",
                key, count, self.recovery_timeout,
            )

    def failure_count(self, key: str) -> int:
        """返回指定 key 的当前连续失败次数（用于测试和监控）。"""
        return self._failures.get(key, 0)

    def reset(self, key: str) -> None:
        """手动重置指定 key 的熔断状态（运维/测试用）。"""
        self._failures.pop(key, None)
        self._open_until.pop(key, None)
