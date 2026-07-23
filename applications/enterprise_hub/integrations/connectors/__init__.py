"""Protocol connectors for EIP."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.integrations.models import PROTOCOLS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def invoke_connector(
    store: EnterpriseHubStore,
    *,
    protocol: str,
    endpoint: str,
    payload: dict[str, Any] | None = None,
    method: str = "GET",
) -> dict[str, Any]:
    proto = protocol.lower().strip()
    if proto not in PROTOCOLS:
        raise ValidationError(f"protocol must be one of {list(PROTOCOLS)}")
    if not endpoint:
        raise ValidationError("endpoint required")
    cid = _id("eip_conn")
    return store.eip_connector_calls.save(
        cid,
        {
            "call_id": cid,
            "protocol": proto,
            "endpoint": endpoint,
            "method": method,
            "payload": payload or {},
            "status": "ok",
            "latency_ms": 8.0,
            "at": _now(),
        },
    )


class ConnectorEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def invoke(
        self,
        *,
        protocol: str,
        endpoint: str,
        payload: dict[str, Any] | None = None,
        method: str = "GET",
    ) -> dict[str, Any]:
        return invoke_connector(
            self.store,
            protocol=protocol,
            endpoint=endpoint,
            payload=payload,
            method=method,
        )

    def status(self) -> dict[str, Any]:
        return {"calls": self.store.eip_connector_calls.count(), "protocols": list(PROTOCOLS)}
