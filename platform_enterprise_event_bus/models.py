"""Enterprise Event Bus domain models — Sprint 36.1.

Control-plane types for topics, delivery, DLQ, and replay.
Transport SoR remains events.event_bus.PlatformEventBus.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class EventPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    SYSTEM = "system"


PRIORITY_RANK = {
    EventPriority.LOW: 0,
    EventPriority.NORMAL: 1,
    EventPriority.HIGH: 2,
    EventPriority.CRITICAL: 3,
    EventPriority.SYSTEM: 4,
}


DEFAULT_TOPICS: tuple[str, ...] = (
    "system",
    "security",
    "workflow",
    "crm",
    "erp",
    "knowledge",
    "notifications",
    "ai",
    "agents",
    "voice",
    "marketplace",
    "billing",
    "analytics",
    "creative",
    "platform",
)


class DeliveryMode(str, Enum):
    FIRE_AND_FORGET = "fire_and_forget"
    BROADCAST = "broadcast"
    MULTICAST = "multicast"
    REQUEST_RESPONSE = "request_response"
    SCHEDULED = "scheduled"
    DELAYED = "delayed"


@dataclass
class SecurityContext:
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    authenticated: bool = True
    principal_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> SecurityContext:
        data = data or {}
        return cls(
            roles=list(data.get("roles") or []),
            permissions=list(data.get("permissions") or []),
            authenticated=bool(data.get("authenticated", True)),
            principal_id=data.get("principal_id"),
        )


@dataclass
class EnterpriseEvent:
    event_type: str
    category: str
    source_service: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex}")
    target_service: str | None = None
    timestamp: float = field(default_factory=time.time)
    correlation_id: str | None = None
    causation_id: str | None = None
    priority: EventPriority | str = EventPriority.NORMAL
    metadata: dict[str, Any] = field(default_factory=dict)
    security_context: SecurityContext = field(default_factory=SecurityContext)
    tenant_id: str | None = None
    user_id: str | None = None
    trace_id: str | None = None
    signature: str | None = None
    version: str = "1.0"
    topic: str = "platform"
    delivery_mode: DeliveryMode | str = DeliveryMode.FIRE_AND_FORGET
    deliver_at: float | None = None
    reply_to: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.priority, str):
            self.priority = EventPriority(self.priority)
        if isinstance(self.delivery_mode, str):
            self.delivery_mode = DeliveryMode(self.delivery_mode)
        if isinstance(self.security_context, dict):
            self.security_context = SecurityContext.from_dict(self.security_context)
        if not self.trace_id:
            self.trace_id = f"tr_{uuid.uuid4().hex[:16]}"
        if not self.correlation_id:
            self.correlation_id = self.event_id

    @property
    def priority_value(self) -> EventPriority:
        return self.priority if isinstance(self.priority, EventPriority) else EventPriority(self.priority)

    def payload_hash(self) -> str:
        raw = json.dumps(self.payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "category": self.category,
            "source_service": self.source_service,
            "target_service": self.target_service,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "priority": self.priority_value.value,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
            "security_context": self.security_context.to_dict(),
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "trace_id": self.trace_id,
            "signature": self.signature,
            "version": self.version,
            "topic": self.topic,
            "delivery_mode": (
                self.delivery_mode.value
                if isinstance(self.delivery_mode, DeliveryMode)
                else str(self.delivery_mode)
            ),
            "deliver_at": self.deliver_at,
            "reply_to": self.reply_to,
            "payload_hash": self.payload_hash(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnterpriseEvent:
        return cls(
            event_id=str(data.get("event_id") or f"evt_{uuid.uuid4().hex}"),
            event_type=str(data.get("event_type") or "generic"),
            category=str(data.get("category") or data.get("topic") or "platform"),
            source_service=str(data.get("source_service") or "unknown"),
            target_service=data.get("target_service"),
            timestamp=float(data.get("timestamp") or time.time()),
            correlation_id=data.get("correlation_id"),
            causation_id=data.get("causation_id"),
            priority=data.get("priority") or EventPriority.NORMAL,
            payload=dict(data.get("payload") or {}),
            metadata=dict(data.get("metadata") or {}),
            security_context=SecurityContext.from_dict(data.get("security_context")),
            tenant_id=data.get("tenant_id"),
            user_id=data.get("user_id"),
            trace_id=data.get("trace_id"),
            signature=data.get("signature"),
            version=str(data.get("version") or "1.0"),
            topic=str(data.get("topic") or data.get("category") or "platform"),
            delivery_mode=data.get("delivery_mode") or DeliveryMode.FIRE_AND_FORGET,
            deliver_at=data.get("deliver_at"),
            reply_to=data.get("reply_to"),
        )


@dataclass
class Subscription:
    subscription_id: str
    subscriber_id: str
    topic: str | None = None
    event_type: str | None = None
    event_filter: str | None = None  # glob / regex
    priority_min: EventPriority | str | None = None
    tenant_id: str | None = None
    user_id: str | None = None
    regex: str | None = None
    wildcard: str | None = None
    active: bool = True
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subscription_id": self.subscription_id,
            "subscriber_id": self.subscriber_id,
            "topic": self.topic,
            "event_type": self.event_type,
            "event_filter": self.event_filter,
            "priority_min": (
                self.priority_min.value
                if isinstance(self.priority_min, EventPriority)
                else self.priority_min
            ),
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "regex": self.regex,
            "wildcard": self.wildcard,
            "active": self.active,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


@dataclass
class DeliveryRecord:
    delivery_id: str
    event_id: str
    subscriber_id: str
    status: str  # pending | delivered | failed | retrying | dead
    attempts: int = 0
    last_error: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    duration_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeadLetterRecord:
    dlq_id: str
    event: dict[str, Any]
    reason: str
    subscriber_id: str | None = None
    attempts: int = 0
    created_at: float = field(default_factory=time.time)
    retried: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TopicInfo:
    name: str
    description: str = ""
    event_count: int = 0
    subscriber_count: int = 0
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def match_wildcard(pattern: str, value: str) -> bool:
    if pattern == "*":
        return True
    if pattern.endswith(".*"):
        return value.startswith(pattern[:-1]) or value.startswith(pattern[:-2])
    if "*" in pattern or "?" in pattern:
        rx = re.escape(pattern).replace(r"\*", ".*").replace(r"\?", ".")
        return re.fullmatch(rx, value) is not None
    return pattern == value


def sign_payload(payload: dict[str, Any], *, secret: str) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode()
    return hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
