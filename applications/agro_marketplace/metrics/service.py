# Metrics service — time-series style metric points for BI.

from __future__ import annotations

from applications.agro_marketplace.analytics.models import MetricPoint
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class MetricsService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def record(self, point: MetricPoint) -> MetricPoint:
        return self._store.bi_metrics.save(point.metric_id, point)

    def list_metrics(self, *, domain: str | None = None, name: str | None = None) -> list[MetricPoint]:
        items = self._store.bi_metrics.list_all()
        if domain:
            items = [m for m in items if m.domain == domain]
        if name:
            items = [m for m in items if m.name == name]
        return sorted(items, key=lambda m: m.recorded_at)

    def latest(self, name: str) -> MetricPoint | None:
        items = self.list_metrics(name=name)
        return items[-1] if items else None


metrics_service = MetricsService()
