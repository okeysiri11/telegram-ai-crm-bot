# Integration Hub events — published to Platform EventBus.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class ConnectorConnectedEvent(BaseEvent):
    connector_id: str
    provider: str
    version: str = "1.0.0"


@dataclass(kw_only=True)
class ConnectorFailedEvent(BaseEvent):
    connector_id: str
    provider: str
    error: str
    operation: str = ""


@dataclass(kw_only=True)
class WebhookReceivedEvent(BaseEvent):
    webhook_id: str
    provider: str
    path: str
    payload_size: int = 0


@dataclass(kw_only=True)
class WebhookProcessedEvent(BaseEvent):
    webhook_id: str
    provider: str
    success: bool
    duration_ms: float = 0.0


@dataclass(kw_only=True)
class RetryScheduledEvent(BaseEvent):
    retry_id: str
    connector_id: str
    operation: str
    attempt: int
    next_retry_at: float
