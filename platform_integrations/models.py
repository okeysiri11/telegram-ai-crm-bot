# Integration Hub domain models.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class ConnectorType(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"
    WEBHOOK = "webhook"
    STREAMING = "streaming"
    POLLING = "polling"


class ProviderType(str, enum.Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    SMS = "sms"
    HTTP_REST = "http_rest"
    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"
    WHATSAPP = "whatsapp"
    BITRIX24 = "bitrix24"
    AMOCRM = "amocrm"
    GOOGLE = "google"
    OPENAI = "openai"
    STRIPE = "stripe"


class ConnectorStatus(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass
class ConnectorMetadata:
    connector_id: str
    provider: str
    connector_type: str
    version: str
    enabled: bool = True
    description: str = ""
    tags: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "provider": self.provider,
            "connector_type": self.connector_type,
            "version": self.version,
            "enabled": self.enabled,
            "description": self.description,
            "tags": self.tags,
            "config": self.config,
        }


@dataclass
class ConnectorHealth:
    connector_id: str
    provider: str
    status: str
    latency_ms: float = 0.0
    error_count: int = 0
    last_success: datetime | None = None
    last_failure: datetime | None = None
    last_error: str | None = None
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "provider": self.provider,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "error_count": self.error_count,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "last_error": self.last_error,
            "checked_at": self.checked_at.isoformat(),
        }


@dataclass
class WebhookRegistration:
    webhook_id: str
    name: str
    provider: str
    path: str
    secret: str
    enabled: bool = True
    connector_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self, *, include_secret: bool = False) -> dict[str, Any]:
        data = {
            "webhook_id": self.webhook_id,
            "name": self.name,
            "provider": self.provider,
            "path": self.path,
            "enabled": self.enabled,
            "connector_id": self.connector_id,
            "created_at": self.created_at.isoformat(),
        }
        if include_secret:
            data["secret"] = self.secret
        return data


@dataclass
class RetryRecord:
    retry_id: str
    connector_id: str
    operation: str
    payload: dict[str, Any]
    attempt: int
    max_attempts: int
    next_retry_at: float
    status: str = "scheduled"
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "retry_id": self.retry_id,
            "connector_id": self.connector_id,
            "operation": self.operation,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "next_retry_at": self.next_retry_at,
            "status": self.status,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class IntegrationStatistics:
    total_invocations: int = 0
    successful_invocations: int = 0
    failed_invocations: int = 0
    retries_scheduled: int = 0
    dead_letter_count: int = 0
    webhooks_received: int = 0
    webhooks_processed: int = 0
    rate_limited: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_invocations": self.total_invocations,
            "successful_invocations": self.successful_invocations,
            "failed_invocations": self.failed_invocations,
            "retries_scheduled": self.retries_scheduled,
            "dead_letter_count": self.dead_letter_count,
            "webhooks_received": self.webhooks_received,
            "webhooks_processed": self.webhooks_processed,
            "rate_limited": self.rate_limited,
        }


@dataclass
class QueuedOperation:
    operation_id: str
    connector_id: str
    operation: str
    payload: dict[str, Any]
    enqueued_at: float = field(default_factory=time.monotonic)

    @staticmethod
    def new(connector_id: str, operation: str, payload: dict[str, Any]) -> QueuedOperation:
        return QueuedOperation(
            operation_id=str(uuid.uuid4()),
            connector_id=connector_id,
            operation=operation,
            payload=payload,
        )
