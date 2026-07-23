"""Soap connector."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.integrations.connectors import invoke_connector
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class SoapConnector:
    protocol = "soap"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def invoke(
        self,
        *,
        endpoint: str,
        payload: dict[str, Any] | None = None,
        method: str = "GET",
    ) -> dict[str, Any]:
        return invoke_connector(
            self.store,
            protocol=self.protocol,
            endpoint=endpoint,
            payload=payload,
            method=method,
        )
