# Communication models — Sprint 7.2.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


class MessageType(str, enum.Enum):
    EVENT = "event"
    COMMAND = "command"
    QUERY = "query"
    REQUEST = "request"
    RESPONSE = "response"
    DIRECT = "direct"
    BROADCAST = "broadcast"


class EventCategory(str, enum.Enum):
    DOMAIN = "domain"
    APPLICATION = "application"
    SYSTEM = "system"
    AI = "ai"
    WORKFLOW = "workflow"


class MessagePriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    ROUTED = "routed"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class SyncScope(str, enum.Enum):
    CONTEXT = "context"
    USER = "user"
    PERMISSION = "permission"
    ORGANIZATION = "organization"
    NOTIFICATION = "notification"
    FULL = "full"


@dataclass
class Envelope:
    message_id: str = field(default_factory=_id)
    message_type: MessageType = MessageType.EVENT
    source_application: str = ""
    target_application: str = ""
    correlation_id: str = ""
    reply_to: str = ""
    topic: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    status: DeliveryStatus = DeliveryStatus.PENDING
    headers: dict[str, str] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=_ts)
    delivered_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "source_application": self.source_application,
            "target_application": self.target_application,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "topic": self.topic,
            "payload": dict(self.payload),
            "priority": self.priority.value,
            "status": self.status.value,
            "headers": dict(self.headers),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at,
            "delivered_at": self.delivered_at,
        }


@dataclass
class BusEvent:
    event_id: str = field(default_factory=_id)
    category: EventCategory = EventCategory.APPLICATION
    event_name: str = ""
    source_application: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "category": self.category.value,
            "event_name": self.event_name,
            "source_application": self.source_application,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class Subscription:
    subscription_id: str = field(default_factory=_id)
    application_id: str = ""
    topic: str = ""
    event_filter: str = ""
    is_active: bool = True
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subscription_id": self.subscription_id,
            "application_id": self.application_id,
            "topic": self.topic,
            "event_filter": self.event_filter,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class ApplicationRegistration:
    application_id: str = ""
    name: str = ""
    version: str = "1.0.0"
    capabilities: list[str] = field(default_factory=list)
    endpoints: dict[str, str] = field(default_factory=dict)
    health_status: str = "unknown"
    dependencies: list[str] = field(default_factory=list)
    min_ecosystem_version: str = "1.0.0-alpha"
    is_connected: bool = False
    last_heartbeat: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    registered_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "application_id": self.application_id,
            "name": self.name,
            "version": self.version,
            "capabilities": list(self.capabilities),
            "endpoints": dict(self.endpoints),
            "health_status": self.health_status,
            "dependencies": list(self.dependencies),
            "min_ecosystem_version": self.min_ecosystem_version,
            "is_connected": self.is_connected,
            "last_heartbeat": self.last_heartbeat,
            "metadata": dict(self.metadata),
            "registered_at": self.registered_at,
        }


@dataclass
class SyncRecord:
    sync_id: str = field(default_factory=_id)
    scope: SyncScope = SyncScope.CONTEXT
    source_application: str = ""
    target_applications: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    completed_at: float = 0.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sync_id": self.sync_id,
            "scope": self.scope.value,
            "source_application": self.source_application,
            "target_applications": list(self.target_applications),
            "data": dict(self.data),
            "status": self.status,
            "completed_at": self.completed_at,
            "created_at": self.created_at,
        }


@dataclass
class DeliveryConfirmation:
    confirmation_id: str = field(default_factory=_id)
    message_id: str = ""
    application_id: str = ""
    status: DeliveryStatus = DeliveryStatus.DELIVERED
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "confirmation_id": self.confirmation_id,
            "message_id": self.message_id,
            "application_id": self.application_id,
            "status": self.status.value,
            "created_at": self.created_at,
        }


@dataclass
class SharedContext:
    context_id: str = field(default_factory=_id)
    user_id: str = ""
    application_id: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    shared_with: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "user_id": self.user_id,
            "application_id": self.application_id,
            "data": dict(self.data),
            "shared_with": list(self.shared_with),
            "created_at": self.created_at,
        }
