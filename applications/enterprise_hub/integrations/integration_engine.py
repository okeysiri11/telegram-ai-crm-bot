"""Integration Engine — connectors, adapters, sync, retry."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.integrations.adapters import AdapterFramework
from applications.enterprise_hub.integrations.connectors import ConnectorEngine
from applications.enterprise_hub.integrations.models import SYNC_MODES
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class IntegrationEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.connectors = ConnectorEngine(self.store)
        self.adapters = AdapterFramework(self.store)

    def connect(
        self,
        *,
        protocol: str,
        endpoint: str,
        payload: dict[str, Any] | None = None,
        method: str = "GET",
    ) -> dict[str, Any]:
        return self.connectors.invoke(
            protocol=protocol, endpoint=endpoint, payload=payload, method=method
        )

    def adapt(
        self,
        *,
        adapter: str,
        operation: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.adapters.invoke(adapter=adapter, operation=operation, payload=payload)

    def sync(
        self,
        *,
        integration_id: str,
        mode: str = "incremental",
        records: int = 0,
    ) -> dict[str, Any]:
        if self.store.eip_registry.get(integration_id) is None:
            raise NotFoundError(f"integration not found: {integration_id}")
        m = mode.lower().strip()
        if m not in SYNC_MODES:
            raise ValidationError(f"mode must be one of {list(SYNC_MODES)}")
        sid = _id("eip_sync")
        return self.store.eip_syncs.save(
            sid,
            {
                "sync_id": sid,
                "integration_id": integration_id,
                "mode": m,
                "records": int(records),
                "status": "completed",
                "at": _now(),
            },
        )

    def retry(
        self,
        *,
        integration_id: str,
        attempt: int = 1,
        error: str = "",
        fallback_route: str = "",
        notify_admin: bool = True,
    ) -> dict[str, Any]:
        if self.store.eip_registry.get(integration_id) is None:
            raise NotFoundError(f"integration not found: {integration_id}")
        delay_ms = min(1000 * (2 ** max(0, int(attempt) - 1)), 30000)
        rid = _id("eip_retry")
        return self.store.eip_retries.save(
            rid,
            {
                "retry_id": rid,
                "integration_id": integration_id,
                "attempt": int(attempt),
                "delay_ms": delay_ms,
                "error": error,
                "fallback_route": fallback_route,
                "notify_admin": notify_admin,
                "status": "retried",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "connectors": self.connectors.status(),
            "adapters": self.adapters.status(),
            "syncs": self.store.eip_syncs.count(),
            "retries": self.store.eip_retries.count(),
            "sync_modes": list(SYNC_MODES),
        }
