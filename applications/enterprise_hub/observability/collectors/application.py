"""application collector."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.observability.collectors import collect
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class ApplicationCollector:
    name = "application"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def run(self, *, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return collect(self.store, collector=self.name, payload=payload)
