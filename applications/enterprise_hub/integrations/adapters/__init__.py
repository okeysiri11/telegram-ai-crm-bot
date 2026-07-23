"""Adapter layer for EIP."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.integrations.models import ADAPTERS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def invoke_adapter(
    store: EnterpriseHubStore,
    *,
    adapter: str,
    operation: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ad = adapter.lower().strip()
    if ad not in ADAPTERS:
        raise ValidationError(f"adapter must be one of {list(ADAPTERS)}")
    if not operation:
        raise ValidationError("operation required")
    aid = _id("eip_adp")
    return store.eip_adapter_calls.save(
        aid,
        {
            "call_id": aid,
            "adapter": ad,
            "operation": operation,
            "payload": payload or {},
            "status": "ok",
            "at": _now(),
        },
    )


class AdapterFramework:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def invoke(
        self,
        *,
        adapter: str,
        operation: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return invoke_adapter(
            self.store, adapter=adapter, operation=operation, payload=payload
        )

    def status(self) -> dict[str, Any]:
        return {"calls": self.store.eip_adapter_calls.count(), "adapters": list(ADAPTERS)}
