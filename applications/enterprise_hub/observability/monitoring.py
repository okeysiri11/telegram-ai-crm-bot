"""Monitoring engine — orchestrates collectors and target oversight."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.observability.collectors import collect
from applications.enterprise_hub.observability.exporters import export_telemetry
from applications.enterprise_hub.observability.health import HealthMonitor
from applications.enterprise_hub.observability.metrics import MetricsPlatform
from applications.enterprise_hub.observability.service_registry import ServiceRegistry
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class MonitoringEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.metrics = MetricsPlatform(self.store)
        self.health = HealthMonitor(self.store)
        self.services = ServiceRegistry(self.store)

    def collect(self, *, collector: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return collect(self.store, collector=collector, payload=payload)

    def export(self, *, exporter: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return export_telemetry(self.store, exporter=exporter, payload=payload)

    def status(self) -> dict[str, Any]:
        return {
            "collections": self.store.obs_collections.count(),
            "exports": self.store.obs_exports.count(),
            "metrics": self.metrics.status(),
            "health": self.health.status(),
            "services": self.services.status(),
        }
