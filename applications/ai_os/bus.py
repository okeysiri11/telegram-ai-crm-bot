"""System Bus — event/message/knowledge/workflow/memory/plugin/connector buses (Sprint 12.4)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.ai_os.config import DEFAULT_CONFIG
from applications.ai_os.shared.exceptions import ValidationError
from applications.ai_os.shared.store import AIOSStore, ai_os_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SystemBus:
    def __init__(self, store: AIOSStore | None = None) -> None:
        self.store = store or ai_os_store
        self.buses = list(DEFAULT_CONFIG.buses)

    def publish(self, *, bus: str, topic: str, payload: dict[str, Any] | None = None, source: str = "ai_os") -> dict[str, Any]:
        if bus not in self.buses:
            raise ValidationError(f"bus must be one of {self.buses}")
        if not topic:
            raise ValidationError("topic required")
        mid = f"bus_{uuid.uuid4().hex[:12]}"
        msg = {
            "message_id": mid,
            "bus": bus,
            "topic": topic,
            "source": source,
            "payload": dict(payload or {}),
            "at": _now(),
        }
        self.store.bus_messages.save(mid, msg)
        return msg

    def subscribe_poll(self, *, bus: str, topic: str | None = None) -> list[dict[str, Any]]:
        if bus not in self.buses:
            raise ValidationError(f"bus must be one of {self.buses}")
        msgs = [m for m in self.store.bus_messages.list_all() if m.get("bus") == bus]
        if topic:
            msgs = [m for m in msgs if m.get("topic") == topic]
        return msgs

    def catalog(self) -> dict[str, Any]:
        return {"buses": self.buses, "message_count": len(self.store.bus_messages.list_all())}

    def status(self) -> dict[str, Any]:
        return {"system_bus": "1.0", "buses": self.buses, "ready": True}


system_bus = SystemBus()
