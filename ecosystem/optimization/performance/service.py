# Performance engine — application/agent/workflow/KPI monitoring.

from __future__ import annotations

from typing import Any

from events.publisher import publish

from ecosystem.optimization.events import PerformanceUpdatedEvent
from ecosystem.optimization.models import MetricDomain, PerformanceSnapshot
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class PerformanceEngine:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    async def record(
        self,
        name: str,
        value: float,
        *,
        domain: MetricDomain = MetricDomain.APPLICATION,
        unit: str = "",
        target: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> PerformanceSnapshot:
        snapshot = PerformanceSnapshot(
            domain=domain,
            name=name,
            value=value,
            unit=unit,
            target=target,
            metadata=metadata or {},
        )
        self._store.performance_snapshots.save(snapshot.snapshot_id, snapshot)
        await publish(
            PerformanceUpdatedEvent(
                snapshot_id=snapshot.snapshot_id,
                domain=domain.value,
                name=name,
                value=value,
            )
        )
        return snapshot

    async def collect_ecosystem_metrics(self) -> list[PerformanceSnapshot]:
        from ecosystem.shared.store import ecosystem_store as store

        snapshots = []
        snapshots.append(
            await self.record(
                "registered_applications",
                float(len(__import__("ecosystem.config", fromlist=["DEFAULT_CONFIG"]).DEFAULT_CONFIG.registered_applications)),
                domain=MetricDomain.APPLICATION,
                unit="count",
                target=1,
            )
        )
        snapshots.append(
            await self.record(
                "workforce_tasks",
                float(store.workforce_tasks.count()),
                domain=MetricDomain.WORKFLOW,
                unit="count",
                target=0,
            )
        )
        snapshots.append(
            await self.record(
                "assistant_conversations",
                float(store.conversations.count()),
                domain=MetricDomain.APPLICATION,
                unit="count",
                target=0,
            )
        )
        records = store.execution_records.list_all()
        avg_latency = sum(r.duration_ms for r in records) / len(records) if records else 50.0
        snapshots.append(
            await self.record(
                "avg_response_latency",
                round(avg_latency, 2),
                domain=MetricDomain.LATENCY,
                unit="ms",
                target=300.0,
            )
        )
        util = min(100.0, store.workforce_tasks.count() * 5.0)
        snapshots.append(
            await self.record(
                "resource_utilization",
                util,
                domain=MetricDomain.RESOURCE,
                unit="percent_util",
                target=80.0,
            )
        )
        completed = len([t for t in store.workforce_tasks.list_all() if t.status.value == "completed"])
        snapshots.append(
            await self.record(
                "business_task_completion",
                float(completed),
                domain=MetricDomain.BUSINESS,
                unit="count",
                target=1,
            )
        )
        agent_load = store.specialists.count()
        snapshots.append(
            await self.record(
                "agent_pool_size",
                float(agent_load),
                domain=MetricDomain.AGENT,
                unit="count",
                target=8,
            )
        )
        return snapshots

    def dashboard(self) -> dict[str, Any]:
        snapshots = sorted(self._store.performance_snapshots.list_all(), key=lambda s: s.created_at, reverse=True)
        by_domain: dict[str, list[dict[str, Any]]] = {}
        for snap in snapshots[:50]:
            by_domain.setdefault(snap.domain.value, []).append(snap.to_dict())
        return {"by_domain": by_domain, "total_snapshots": len(snapshots)}

    def list_snapshots(self, *, domain: MetricDomain | None = None) -> list[PerformanceSnapshot]:
        snaps = self._store.performance_snapshots.list_all()
        if domain:
            snaps = [s for s in snaps if s.domain == domain]
        return sorted(snaps, key=lambda s: s.created_at, reverse=True)


performance_engine = PerformanceEngine()
