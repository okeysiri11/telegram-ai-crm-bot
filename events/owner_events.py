# Owner escalation domain events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class OwnerEscalationEvent(BaseEvent):
    request_id: str
    request_number: str
    vertical: str
    request_type: str = ""
    manager_id: str | None = None
    manager_telegram_id: int | None = None
    manager_name: str = ""
    owner_id: str | None = None
    owner_name: str = ""
    minutes_overdue: int = 0
    reason: str = "Exceeded maximum escalation threshold"
    escalation_level: int = 4
    completion_deadline: str = ""
    trigger: str = "owner_escalation_level_4"
