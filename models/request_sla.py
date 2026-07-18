# Request SLA domain types.

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RequestSlaSnapshot:
    request_id: str
    manager_id: int | None
    first_response_deadline: datetime
    completion_deadline: datetime
    escalation_level: int
    first_response_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "manager_id": self.manager_id,
            "first_response_deadline": self.first_response_deadline.isoformat(),
            "completion_deadline": self.completion_deadline.isoformat(),
            "escalation_level": self.escalation_level,
            "first_response_at": self.first_response_at.isoformat() if self.first_response_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class RequestEscalationContext:
    request_id: str
    request_number: str
    vertical: str
    request_type: str
    manager_uuid: str | None
    manager_telegram_id: int | None
    client_telegram_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "request_number": self.request_number,
            "vertical": self.vertical,
            "request_type": self.request_type,
            "manager_uuid": self.manager_uuid,
            "manager_telegram_id": self.manager_telegram_id,
            "client_telegram_id": self.client_telegram_id,
        }
