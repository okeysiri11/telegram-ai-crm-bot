# Connector base class — all providers extend this.

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from platform_integrations.models import ConnectorHealth, ConnectorStatus, ConnectorType

logger = logging.getLogger(__name__)


class ConnectorBase(ABC):
    """Abstract connector — platform modules must not call third parties directly."""

    provider: str = "unknown"
    connector_type: ConnectorType = ConnectorType.OUTBOUND
    version: str = "1.0.0"

    def __init__(self, connector_id: str, *, config: dict[str, Any] | None = None) -> None:
        self.connector_id = connector_id
        self.config = config or {}
        self._connected = False
        self._last_success: float | None = None
        self._last_failure: float | None = None
        self._last_error: str | None = None
        self._error_count = 0

    async def connect(self) -> None:
        self._connected = True
        logger.info("connector_connected id=%s provider=%s", self.connector_id, self.provider)

    async def disconnect(self) -> None:
        self._connected = False
        logger.info("connector_disconnected id=%s provider=%s", self.connector_id, self.provider)

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def invoke(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            if operation == "receive":
                result = await self.receive(payload)
            else:
                result = await self.send(operation, payload)
            self._last_success = time.monotonic()
            result["_latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
            return result
        except Exception as exc:
            self._last_failure = time.monotonic()
            self._last_error = str(exc)
            self._error_count += 1
            raise

    @abstractmethod
    async def send(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Outbound operation."""

    async def receive(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Inbound operation — override for inbound/webhook connectors."""
        raise NotImplementedError(f"{self.provider} does not support inbound receive")

    async def health_check(self) -> ConnectorHealth:
        from datetime import datetime, timezone

        started = time.perf_counter()
        status = ConnectorStatus.CONNECTED if self._connected else ConnectorStatus.DISCONNECTED
        try:
            await self.ping()
            latency = round((time.perf_counter() - started) * 1000, 2)
            status = ConnectorStatus.CONNECTED
        except Exception as exc:
            latency = round((time.perf_counter() - started) * 1000, 2)
            status = ConnectorStatus.FAILED
            self._last_error = str(exc)

        return ConnectorHealth(
            connector_id=self.connector_id,
            provider=self.provider,
            status=status.value,
            latency_ms=latency,
            error_count=self._error_count,
            last_success=datetime.fromtimestamp(self._last_success, tz=timezone.utc)
            if self._last_success
            else None,
            last_failure=datetime.fromtimestamp(self._last_failure, tz=timezone.utc)
            if self._last_failure
            else None,
            last_error=self._last_error,
        )

    async def ping(self) -> None:
        """Lightweight health probe — override if needed."""
        if not self._connected:
            await self.connect()
