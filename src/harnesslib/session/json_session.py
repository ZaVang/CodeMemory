"""JSON文件Session实现。

每个session一个JSON文件（data/sessions/{session_id}.json），
追加写入事件。初期实现，后续可迁移到SQLite/PostgreSQL。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..event import Event, SessionBase, SessionInfo


class JsonSession(SessionBase):
    """基于JSON文件的Session实现。"""

    def __init__(self, data_dir: str | Path) -> None:
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self._data_dir / f"{session_id}.json"

    async def create_session(self, session_id: str | None = None) -> str:
        import uuid

        if session_id is None:
            now = datetime.now(timezone.utc)
            short_uuid = uuid.uuid4().hex[:8]
            session_id = f"{now.strftime('%Y%m%d_%H%M%S')}_{short_uuid}"

        path = self._session_path(session_id)
        if not path.exists():
            path.write_text(json.dumps([], ensure_ascii=False, indent=2))
        return session_id

    async def emit(self, event: Event) -> None:
        path = self._session_path(event.session_id)

        # 读取已有事件
        events: list[dict] = []
        if path.exists():
            events = json.loads(path.read_text())

        # 幂等：重复event_id不重复写入
        existing_ids = {e["event_id"] for e in events}
        if event.event_id in existing_ids:
            return

        events.append(event.model_dump(mode="json"))
        path.write_text(json.dumps(events, ensure_ascii=False, indent=2))

    async def get_events(
        self, session_id: str, since: str | None = None
    ) -> list[Event]:
        path = self._session_path(session_id)
        if not path.exists():
            return []

        events_raw = json.loads(path.read_text())
        events = [Event.model_validate(e) for e in events_raw]

        if since is not None:
            # 找到since event_id的位置，返回之后的事件
            for i, e in enumerate(events):
                if e.event_id == since:
                    return events[i + 1 :]
            return []  # since event_id not found

        return events

    async def get_session(self, session_id: str) -> SessionInfo:
        events = await self.get_events(session_id)
        if not events:
            return SessionInfo(
                session_id=session_id,
                created_at=datetime.now(timezone.utc),
            )
        return SessionInfo(
            session_id=session_id,
            created_at=events[0].timestamp,
            last_event_id=events[-1].event_id,
            last_event_at=events[-1].timestamp,
            event_count=len(events),
        )