# Audit trail domain types and event mapping.

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from events.base_event import BaseEvent
from events.request_events import (
    ManagerEscalationEvent,
    ManagerReassignedEvent,
    RequestAssignedEvent,
    RequestCompletedEvent,
    RequestCreatedEvent,
    RequestOverdueEvent,
)
from events.owner_events import OwnerEscalationEvent
from events.configuration_events import ConfigurationChangedEvent


class AuditEventType(str, enum.Enum):
    REQUEST_CREATED = "REQUEST_CREATED"
    REQUEST_ASSIGNED = "REQUEST_ASSIGNED"
    REQUEST_COMPLETED = "REQUEST_COMPLETED"
    MANAGER_REASSIGNED = "MANAGER_REASSIGNED"
    REQUEST_OVERDUE = "REQUEST_OVERDUE"
    MANAGER_ESCALATION = "MANAGER_ESCALATION"
    OWNER_ESCALATED = "OWNER_ESCALATED"
    CONFIGURATION_CHANGED = "CONFIGURATION_CHANGED"


ENTITY_TYPE_REQUEST = "client_request"
ENTITY_TYPE_CONFIGURATION = "platform_configuration"


@dataclass(frozen=True)
class AuditRecord:
    event_type: str
    entity_type: str
    entity_id: str
    actor_id: str | None
    old_value: dict[str, Any] | None
    new_value: dict[str, Any] | None
    metadata_json: dict[str, Any]
    created_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "actor_id": self.actor_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def audit_record_from_event(event: BaseEvent) -> AuditRecord | None:
    if isinstance(event, RequestCreatedEvent):
        return AuditRecord(
            event_type=AuditEventType.REQUEST_CREATED.value,
            entity_type=ENTITY_TYPE_REQUEST,
            entity_id=event.request_id,
            actor_id=str(event.client_telegram_id) if event.client_telegram_id is not None else None,
            old_value=None,
            new_value={
                "status": event.status,
                "request_number": event.request_number,
                "vertical": event.vertical,
                "request_type": event.request_type,
            },
            metadata_json={
                "request_id": event.request_id,
                "request_number": event.request_number,
                "vertical": event.vertical,
                "request_type": event.request_type,
                "client_telegram_id": event.client_telegram_id,
                "client_name": event.client_name,
                "description": event.description,
                "manager_id": event.manager_id,
                "manager_telegram_id": event.manager_telegram_id,
                "platform_event_id": event.event_id,
                "platform_event_type": event.event_type,
            },
        )

    if isinstance(event, RequestAssignedEvent):
        return AuditRecord(
            event_type=AuditEventType.REQUEST_ASSIGNED.value,
            entity_type=ENTITY_TYPE_REQUEST,
            entity_id=event.request_id,
            actor_id=str(event.manager_telegram_id) if event.manager_telegram_id is not None else event.manager_id,
            old_value={"status": "NEW"},
            new_value={
                "status": event.status,
                "manager_id": event.manager_id,
                "request_number": event.request_number,
            },
            metadata_json={
                "request_id": event.request_id,
                "request_number": event.request_number,
                "vertical": event.vertical,
                "request_type": event.request_type,
                "manager_id": event.manager_id,
                "manager_telegram_id": event.manager_telegram_id,
                "client_telegram_id": event.client_telegram_id,
                "platform_event_id": event.event_id,
                "platform_event_type": event.event_type,
            },
        )

    if isinstance(event, RequestCompletedEvent):
        return AuditRecord(
            event_type=AuditEventType.REQUEST_COMPLETED.value,
            entity_type=ENTITY_TYPE_REQUEST,
            entity_id=event.request_id,
            actor_id=str(event.client_telegram_id) if event.client_telegram_id is not None else event.manager_id,
            old_value={"status": "IN_PROGRESS"},
            new_value={
                "status": event.status,
                "converted_to_deal": event.converted_to_deal,
                "request_number": event.request_number,
            },
            metadata_json={
                "request_id": event.request_id,
                "request_number": event.request_number,
                "vertical": event.vertical,
                "request_type": event.request_type,
                "manager_id": event.manager_id,
                "client_telegram_id": event.client_telegram_id,
                "converted_to_deal": event.converted_to_deal,
                "platform_event_id": event.event_id,
                "platform_event_type": event.event_type,
            },
        )

    if isinstance(event, ManagerReassignedEvent):
        return AuditRecord(
            event_type=AuditEventType.MANAGER_REASSIGNED.value,
            entity_type=ENTITY_TYPE_REQUEST,
            entity_id=event.request_id,
            actor_id=str(event.manager_telegram_id) if event.manager_telegram_id is not None else event.manager_id,
            old_value={"manager_id": event.previous_manager_id},
            new_value={
                "manager_id": event.manager_id,
                "request_number": event.request_number,
            },
            metadata_json={
                "request_id": event.request_id,
                "request_number": event.request_number,
                "vertical": event.vertical,
                "request_type": event.request_type,
                "previous_manager_id": event.previous_manager_id,
                "manager_id": event.manager_id,
                "manager_telegram_id": event.manager_telegram_id,
                "client_telegram_id": event.client_telegram_id,
                "platform_event_id": event.event_id,
                "platform_event_type": event.event_type,
            },
        )

    if isinstance(event, RequestOverdueEvent):
        return AuditRecord(
            event_type=AuditEventType.REQUEST_OVERDUE.value,
            entity_type=ENTITY_TYPE_REQUEST,
            entity_id=event.request_id,
            actor_id=str(event.manager_telegram_id) if event.manager_telegram_id is not None else event.manager_id,
            old_value={"sla_status": "ok"},
            new_value={
                "sla_status": "overdue",
                "overdue_seconds": event.overdue_seconds,
                "reason": event.reason,
                "escalation_level": event.escalation_level,
            },
            metadata_json={
                "request_id": event.request_id,
                "request_number": event.request_number,
                "vertical": event.vertical,
                "request_type": event.request_type,
                "manager_id": event.manager_id,
                "manager_telegram_id": event.manager_telegram_id,
                "overdue_seconds": event.overdue_seconds,
                "reason": event.reason,
                "escalation_level": event.escalation_level,
                "platform_event_id": event.event_id,
                "platform_event_type": event.event_type,
            },
        )

    if isinstance(event, ManagerEscalationEvent):
        return AuditRecord(
            event_type=AuditEventType.MANAGER_ESCALATION.value,
            entity_type=ENTITY_TYPE_REQUEST,
            entity_id=event.request_id,
            actor_id=str(event.manager_telegram_id) if event.manager_telegram_id is not None else event.manager_id,
            old_value={"escalation_level": 1},
            new_value={
                "escalation_level": event.escalation_level,
                "overdue_seconds": event.overdue_seconds,
                "reason": event.reason,
            },
            metadata_json={
                "request_id": event.request_id,
                "request_number": event.request_number,
                "vertical": event.vertical,
                "request_type": event.request_type,
                "manager_id": event.manager_id,
                "manager_telegram_id": event.manager_telegram_id,
                "client_telegram_id": event.client_telegram_id,
                "escalation_level": event.escalation_level,
                "overdue_seconds": event.overdue_seconds,
                "reason": event.reason,
                "platform_event_id": event.event_id,
                "platform_event_type": event.event_type,
            },
        )

    if isinstance(event, OwnerEscalationEvent):
        return AuditRecord(
            event_type=AuditEventType.OWNER_ESCALATED.value,
            entity_type=ENTITY_TYPE_REQUEST,
            entity_id=event.request_id,
            actor_id=event.owner_id,
            old_value={
                "escalation_level": 3,
                "manager_id": event.manager_id,
            },
            new_value={
                "escalation_level": event.escalation_level,
                "owner_id": event.owner_id,
                "minutes_overdue": event.minutes_overdue,
                "reason": event.reason,
            },
            metadata_json={
                "request_id": event.request_id,
                "request_number": event.request_number,
                "vertical": event.vertical,
                "request_type": event.request_type,
                "manager_before": event.manager_id,
                "manager_name": event.manager_name,
                "owner": event.owner_id,
                "owner_name": event.owner_name,
                "minutes_overdue": event.minutes_overdue,
                "deadline": event.completion_deadline,
                "escalation_level": event.escalation_level,
                "trigger": event.trigger,
                "reason": event.reason,
                "platform_event_id": event.event_id,
                "platform_event_type": event.event_type,
            },
        )

    if isinstance(event, ConfigurationChangedEvent):
        return AuditRecord(
            event_type=AuditEventType.CONFIGURATION_CHANGED.value,
            entity_type=ENTITY_TYPE_CONFIGURATION,
            entity_id=event.config_key,
            actor_id=event.changed_by,
            old_value={"value": event.old_value},
            new_value={"value": event.new_value},
            metadata_json={
                "config_key": event.config_key,
                "section": event.section,
                "action": event.action,
                "version": event.version,
                "reason": event.reason,
                "platform_event_id": event.event_id,
                "platform_event_type": event.event_type,
            },
        )

    return None
