# Sprint 8.7 — Portal / mobile / partner events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class PortalUserRegisteredEvent(BaseEvent):
    user_id: str = ""
    email: str = ""
    role: str = ""


@dataclass(kw_only=True)
class NotificationSentEvent(BaseEvent):
    notification_id: str = ""
    recipient_id: str = ""
    channel: str = ""
    title: str = ""


@dataclass(kw_only=True)
class PartnerConnectedEvent(BaseEvent):
    connection_id: str = ""
    partner_type: str = ""
    partner_name: str = ""


@dataclass(kw_only=True)
class WebhookTriggeredEvent(BaseEvent):
    subscription_id: str = ""
    event_type: str = ""
    target_url: str = ""


@dataclass(kw_only=True)
class MobileSessionStartedEvent(BaseEvent):
    session_id: str = ""
    user_id: str = ""
    platform: str = ""


@dataclass(kw_only=True)
class DocumentSharedEvent(BaseEvent):
    share_id: str = ""
    document_id: str = ""
    owner_id: str = ""
    recipient_id: str = ""
