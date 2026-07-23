"""Integration monitoring — health, latency, errors, limits, sync success."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class IntegrationMonitor:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def snapshot(
        self,
        *,
        integration_id: str,
        latency_ms: float = 0.0,
        errors: int = 0,
        requests: int = 0,
        rate_limit_remaining: int = 1000,
        sync_success_rate: float = 1.0,
    ) -> dict[str, Any]:
        item = self.store.eip_registry.get(integration_id)
        if item is None:
            raise NotFoundError(f"integration not found: {integration_id}")
        mid = _id("eip_mon")
        return self.store.eip_monitors.save(
            mid,
            {
                "monitor_id": mid,
                "integration_id": integration_id,
                "state": item.get("status", "unknown"),
                "latency_ms": float(latency_ms),
                "errors": int(errors),
                "requests": int(requests),
                "rate_limit_remaining": int(rate_limit_remaining),
                "sync_success_rate": float(sync_success_rate),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"snapshots": self.store.eip_monitors.count()}
