"""Event模型 + SessionBase接口。

Session = 一次会话 = 一条追加写入的事件流。
独立于Harness和Sandbox，是整个系统唯一持久的状态锚。
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class Event(BaseModel):
    """一条事件记录。所有系统行为的原子单位。

    event_type 是 str 而非 Enum —— 通用层不预设事件类型集合，
    具体的事件类型由项目层（Pipeline/Tools）定义。
    """

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str
    component: str
    payload_in: dict[str, Any] | None = None
    payload_out: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    error: str | None = None


class SessionInfo(BaseModel):
    """Session元信息。"""

    session_id: str
    created_at: datetime
    last_event_id: str | None = None
    last_event_at: datetime | None = None
    event_count: int = 0


class SessionBase(ABC):
    """一次会话 = 一条追加写入的事件流。

    实现方式：任何支持按顺序消费、接受幂等追加的存储。
    初期: JSON文件  后续: SQLite / PostgreSQL
    """

    @abstractmethod
    async def emit(self, event: Event) -> None:
        """追加一条事件（幂等：重复event_id不重复写入）。"""

    @abstractmethod
    async def get_events(
        self, session_id: str, since: str | None = None
    ) -> list[Event]:
        """获取事件流。since=event_id 时返回该事件之后的未处理事件。"""

    @abstractmethod
    async def get_session(self, session_id: str) -> SessionInfo:
        """获取session元信息。"""

    @abstractmethod
    async def create_session(self, session_id: str | None = None) -> str:
        """创建一个新session，返回session_id。"""