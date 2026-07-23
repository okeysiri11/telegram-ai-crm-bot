"""prometheus exporter."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.observability.exporters import export_telemetry
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class PrometheusExporter:
    name = "prometheus"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def export(self, *, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return export_telemetry(self.store, exporter=self.name, payload=payload)
