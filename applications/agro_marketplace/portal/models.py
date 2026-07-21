# Sprint 8.7 — Portal, mobile, users and partner domain models.

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


class PortalKind(str, enum.Enum):
    FARMER = "farmer"
    BUYER = "buyer"
    SUPPLIER = "supplier"
    EXPORTER = "exporter"
    ADMINISTRATOR = "administrator"
    EXECUTIVE = "executive"


class PartnerType(str, enum.Enum):
    BANK = "bank"
    INSURANCE = "insurance"
    LOGISTICS = "logistics"
    GOVERNMENT = "government"
    LABORATORY = "laboratory"
    ERP = "erp"
    MARKETPLACE = "marketplace"


class NotificationChannel(str, enum.Enum):
    IN_APP = "in_app"
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    WORKFLOW = "workflow"
    AI_ALERT = "ai_alert"


@dataclass
class PortalUser:
    user_id: str = field(default_factory=_id)
    email: str = ""
    display_name: str = ""
    role: str = "farmer"
    organization_id: str = ""
    phone: str = ""
    locale: str = "en"
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "display_name": self.display_name,
            "role": self.role,
            "organization_id": self.organization_id,
            "phone": self.phone,
            "locale": self.locale,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class MobileSession:
    session_id: str = field(default_factory=_id)
    user_id: str = ""
    device_id: str = ""
    access_token: str = ""
    platform: str = "ios"
    started_at: float = field(default_factory=_ts)
    expires_at: float = 0.0
    is_active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "device_id": self.device_id,
            "access_token": self.access_token,
            "platform": self.platform,
            "started_at": self.started_at,
            "expires_at": self.expires_at,
            "is_active": self.is_active,
        }


@dataclass
class PortalView:
    view_id: str = field(default_factory=_id)
    kind: PortalKind = PortalKind.FARMER
    title: str = ""
    widgets: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    user_id: str = ""
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "view_id": self.view_id,
            "kind": self.kind.value,
            "title": self.title,
            "widgets": list(self.widgets),
            "recommendations": list(self.recommendations),
            "user_id": self.user_id,
            "updated_at": self.updated_at,
        }


@dataclass
class PartnerConnection:
    connection_id: str = field(default_factory=_id)
    partner_type: PartnerType = PartnerType.BANK
    partner_name: str = ""
    status: str = "connected"
    credentials_ref: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    connected_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            "partner_type": self.partner_type.value,
            "partner_name": self.partner_name,
            "status": self.status,
            "credentials_ref": self.credentials_ref,
            "config": dict(self.config),
            "connected_at": self.connected_at,
        }


@dataclass
class WebhookSubscription:
    subscription_id: str = field(default_factory=_id)
    target_url: str = ""
    event_types: list[str] = field(default_factory=list)
    secret: str = ""
    is_active: bool = True
    partner_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subscription_id": self.subscription_id,
            "target_url": self.target_url,
            "event_types": list(self.event_types),
            "is_active": self.is_active,
            "partner_id": self.partner_id,
            "created_at": self.created_at,
        }


@dataclass
class MessageThread:
    thread_id: str = field(default_factory=_id)
    participants: list[str] = field(default_factory=list)
    subject: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "thread_id": self.thread_id,
            "participants": list(self.participants),
            "subject": self.subject,
            "created_at": self.created_at,
        }


@dataclass
class Message:
    message_id: str = field(default_factory=_id)
    thread_id: str = ""
    sender_id: str = ""
    body: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "sender_id": self.sender_id,
            "body": self.body,
            "created_at": self.created_at,
        }


@dataclass
class CalendarEvent:
    event_id: str = field(default_factory=_id)
    user_id: str = ""
    title: str = ""
    starts_at: float = 0.0
    ends_at: float = 0.0
    event_type: str = "general"
    related_id: str = ""
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "user_id": self.user_id,
            "title": self.title,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "event_type": self.event_type,
            "related_id": self.related_id,
            "created_at": self.created_at,
        }


@dataclass
class SharedDocument:
    share_id: str = field(default_factory=_id)
    document_id: str = ""
    owner_id: str = ""
    recipient_id: str = ""
    title: str = ""
    shared_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "share_id": self.share_id,
            "document_id": self.document_id,
            "owner_id": self.owner_id,
            "recipient_id": self.recipient_id,
            "title": self.title,
            "shared_at": self.shared_at,
        }
