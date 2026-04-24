"""Harness — 系统中枢，Effect循环。

Harness不直接调用任何组件，而是yield Effect声明意图，
由基础设施执行后喂回结果。每个yield点自动记录事件到Session。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Generic, TypeVar

from .event import Event, SessionBase
from .sandbox import SandboxBase

T = TypeVar("T")

logger = logging.getLogger(__name__)


# ── Effect 类型定义 ──


@dataclass
class Effect(Generic[T]):
    """所有Effect的基类。Harness通过yield Effect声明意图。"""


@dataclass
class ExecuteToolEffect(Effect[dict]):
    """请求Sandbox执行一个工具。"""

    tool_name: str
    payload: dict[str, Any]


@dataclass
class EmitEventEffect(Effect[None]):
    """请求向Session写入一条事件。"""

    event: Event


@dataclass
class GetEventsEffect(Effect[list[Event]]):
    """请求从Session读取事件流。"""

    session_id: str
    since: str | None = None


# ── Harness 本体 ──


class Harness:
    """系统中枢。不含业务逻辑，不知道"预测"是什么。

    职责：
    1. 被Orchestration指派处理一个session（wake）
    2. 运行Pipeline的Effect循环，自动记录事件到Session
    3. 通过Sandbox执行工具调用
    4. 处理错误恢复和重试
    """

    def __init__(self, session: SessionBase, sandbox: SandboxBase) -> None:
        self.session = session
        self.sandbox = sandbox
        self._session_context: dict = {}  # 12-E1: session级别上下文（prediction_context等）

    def set_session_context(self, context: dict) -> None:
        """设置 session 级别的上下文，将附加到每个 tool_response 事件的 metadata 中。"""
        self._session_context = dict(context)

    async def wake(self, session_id: str) -> None:
        """被Orchestration指派处理一个session。

        语义：确保这个session正在被一个Harness处理。

        正常流程：Orchestration创建新session_id，wake启动新执行循环。
        恢复流程：Harness崩溃后，Orchestration起新实例，
                 用同一个session_id调wake → 从Session中恢复到断点。
        """
        # 检查 session 是否已存在（恢复场景）
        existing_events = await self.session.get_events(session_id)
        if existing_events:
            logger.info(
                "Harness.wake: 恢复 session %s, 已有 %d 个事件",
                session_id,
                len(existing_events),
            )
            # 检查是否已完成（pipeline_end 事件存在）
            event_types = {e.event_type for e in existing_events}
            if "pipeline_end" in event_types:
                logger.info(
                    "Harness.wake: session %s 已完成，跳过",
                    session_id,
                )
                return
            # TODO Sprint 1+: 实现断点恢复 —— 找到最后一个 tool_response，
            # 从该点之后继续执行 pipeline
            logger.info(
                "Harness.wake: session %s 尚未完成，需要恢复（当前仅记录日志）",
                session_id,
            )
        else:
            logger.info("Harness.wake: 新 session %s", session_id)

    async def run_effect_loop(
        self,
        session_id: str,
        effects: AsyncGenerator[Effect, Any],
    ) -> None:
        """运行一个Effect循环。

        遍历Pipeline yield出来的Effect，逐个执行并喂回结果。
        每个Effect执行前后自动emit事件到Session。
        """
        result = None
        try:
            effect = await effects.asend(None)  # 启动generator
            while True:
                result = await self._handle_effect(session_id, effect)
                effect = await effects.asend(result)
        except StopAsyncIteration:
            pass

    async def _handle_effect(self, session_id: str, effect: Effect) -> Any:
        """处理单个Effect。根据类型分发到对应的基础设施。"""
        if isinstance(effect, ExecuteToolEffect):
            return await self._handle_execute_tool(session_id, effect)
        elif isinstance(effect, EmitEventEffect):
            # Ensure the event carries the current session_id
            event = effect.event
            if event.session_id != session_id:
                event = event.model_copy(update={"session_id": session_id})
            await self.session.emit(event)
            return None
        elif isinstance(effect, GetEventsEffect):
            return await self.session.get_events(
                effect.session_id, since=effect.since
            )
        else:
            raise TypeError(f"Unknown effect type: {type(effect)}")

    async def _handle_execute_tool(
        self, session_id: str, effect: ExecuteToolEffect
    ) -> dict:
        """执行工具调用，自动记录事件。"""
        # 记录请求事件
        await self.session.emit(
            Event(
                session_id=session_id,
                event_type="tool_request",
                component=effect.tool_name,
                payload_in=effect.payload,
            )
        )

        try:
            result = await self.sandbox.execute(effect.tool_name, effect.payload)

            # 提取 thinking 字段到 metadata（Schema 只增不改原则：不放入 payload_out）
            metadata: dict = dict(self._session_context)  # 12-E1: 注入 session 级别上下文
            if isinstance(result, dict) and "thinking" in result:
                metadata["thinking"] = result.get("thinking")

            # 记录响应事件
            await self.session.emit(
                Event(
                    session_id=session_id,
                    event_type="tool_response",
                    component=effect.tool_name,
                    payload_out=result,
                    metadata=metadata if metadata else None,
                )
            )
            return result

        except Exception as e:
            # 记录错误事件
            await self.session.emit(
                Event(
                    session_id=session_id,
                    event_type="tool_error",
                    component=effect.tool_name,
                    payload_in=effect.payload,
                    error=str(e),
                )
            )
            raise