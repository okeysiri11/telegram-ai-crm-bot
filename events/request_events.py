# Request lifecycle events for the internal platform event bus.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class RequestCreatedEvent(BaseEvent):
    request_id: str
    request_number: str
    vertical: str
    request_type: str
    status: str = "NEW"
    client_telegram_id: int | None = None
    client_name: str = ""
    description: str = ""
    manager_id: str | None = None
    manager_telegram_id: int | None = None


@dataclass(kw_only=True)
class RequestAssignedEvent(BaseEvent):
    request_id: str
    request_number: str
    vertical: str
    request_type: str
    manager_id: str
    manager_telegram_id: int | None = None
    client_telegram_id: int | None = None
    status: str = "ASSIGNED"


@dataclass(kw_only=True)
class ManagerFirstResponseEvent(BaseEvent):
    request_id: str
    request_number: str
    vertical: str
    request_type: str
    manager_id: str
    manager_telegram_id: int | None = None
    client_telegram_id: int | None = None
    response_time_seconds: int = 0
    sla_compliant: bool = True


@dataclass(kw_only=True)
class RequestCompletedEvent(BaseEvent):
    request_id: str
    request_number: str
    vertical: str
    request_type: str
    status: str = "COMPLETED"
    manager_id: str | None = None
    client_telegram_id: int | None = None
    converted_to_deal: bool = False


@dataclass(kw_only=True)
class RequestOverdueEvent(BaseEvent):
    request_id: str
    request_number: str
    vertical: str
    request_type: str
    manager_id: str | None = None
    manager_telegram_id: int | None = None
    overdue_seconds: int = 0
    reason: str = "sla_first_response"
    escalation_level: int = 1


@dataclass(kw_only=True)
class ManagerEscalationEvent(BaseEvent):
    request_id: str
    request_number: str
    vertical: str
    request_type: str
    manager_id: str | None = None
    manager_telegram_id: int | None = None
    client_telegram_id: int | None = None
    escalation_level: int = 2
    overdue_seconds: int = 0
    reason: str = "sla_manager_escalation"


@dataclass(kw_only=True)
class ManagerReassignedEvent(BaseEvent):
    request_id: str
    request_number: str
    vertical: str
    request_type: str
    previous_manager_id: str | None = None
    manager_id: str
    manager_telegram_id: int | None = None
    client_telegram_id: int | None = None
