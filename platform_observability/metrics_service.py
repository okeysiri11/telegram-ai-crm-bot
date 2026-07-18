# Metrics service — collection, batch export, catalog.

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections import defaultdict
from typing import Any

from platform_observability.models import MetricPoint

logger = logging.getLogger(__name__)

METRIC_CATALOG: dict[str, str] = {
    "system.cpu.percent": "CPU utilization percent",
    "system.memory.percent": "Memory utilization percent",
    "system.memory.rss_mb": "Process RSS memory MB",
    "redis.connected": "Redis connectivity (1=up)",
    "redis.latency_ms": "Redis ping latency",
    "postgresql.connected": "PostgreSQL connectivity (1=up)",
    "postgresql.pool.size": "DB connection pool size",
    "jobs.queue.size": "Job queue depth",
    "jobs.running.count": "Running jobs",
    "jobs.dead_letter.count": "Dead letter queue size",
    "workflow.executions.active": "Active workflow executions",
    "eventbus.events_per_second": "EventBus throughput",
    "realtime.connections.count": "WebSocket connections",
    "realtime.messages_per_second": "Realtime message rate",
    "integrations.latency_ms": "Integration hub latency",
    "api.request.duration_ms": "API request latency",
    "api.requests_per_second": "API request rate",
}


class MetricsService:
    def __init__(self, *, batch_size: int = 100) -> None:
        self._points: list[MetricPoint] = []
        self._aggregates: dict[str, list[float]] = defaultdict(list)
        self._batch_size = batch_size
        self._export_buffer: list[dict[str, Any]] = []
        self._lock = asyncio.Lock()

    def reset(self) -> None:
        self._points.clear()
        self._aggregates.clear()
        self._export_buffer.clear()

    def catalog(self) -> dict[str, str]:
        return dict(METRIC_CATALOG)

    def record(
        self,
        name: str,
        value: float,
        *,
        unit: str = "count",
        tags: dict[str, str] | None = None,
    ) -> None:
        point = MetricPoint(name=name, value=value, unit=unit, tags=tags or {})
        self._points.append(point)
        self._aggregates[name].append(value)
        if len(self._export_buffer) < 10_000:
            self._export_buffer.append(point.to_dict())

    def record_batch(self, points: list[MetricPoint]) -> None:
        for point in points:
            self.record(point.name, point.value, unit=point.unit, tags=point.tags)

    async def collect_platform_metrics(self) -> list[MetricPoint]:
        """Collect metrics from all platform subsystems."""
        collected: list[MetricPoint] = []

        collected.extend(self._collect_system())
        collected.extend(await self._collect_redis())
        collected.extend(await self._collect_postgresql())
        collected.extend(await self._collect_jobs())
        collected.extend(await self._collect_workflows())
        collected.extend(await self._collect_eventbus())
        collected.extend(await self._collect_realtime())
        collected.extend(await self._collect_integrations())

        self.record_batch(collected)
        return collected

    def _collect_system(self) -> list[MetricPoint]:
        points: list[MetricPoint] = []
        try:
            import psutil

            points.append(MetricPoint("system.cpu.percent", psutil.cpu_percent(interval=0)))
            mem = psutil.virtual_memory()
            points.append(MetricPoint("system.memory.percent", mem.percent, unit="percent"))
            points.append(
                MetricPoint("system.memory.rss_mb", psutil.Process().memory_info().rss / 1_048_576, unit="mb")
            )
        except Exception:
            points.append(MetricPoint("system.cpu.percent", 0.0, unit="percent"))
            points.append(MetricPoint("system.memory.percent", 0.0, unit="percent"))
        return points

    async def _collect_redis(self) -> list[MetricPoint]:
        points: list[MetricPoint] = []
        redis_url = os.getenv("REDIS_URL", "").strip()
        if not redis_url:
            points.append(MetricPoint("redis.connected", 0, tags={"status": "not_configured"}))
            return points
        try:
            from redis.asyncio import Redis

            started = time.perf_counter()
            client = Redis.from_url(redis_url, decode_responses=True)
            await client.ping()
            latency = round((time.perf_counter() - started) * 1000, 2)
            await client.aclose()
            points.append(MetricPoint("redis.connected", 1))
            points.append(MetricPoint("redis.latency_ms", latency, unit="ms"))
        except Exception:
            points.append(MetricPoint("redis.connected", 0, tags={"status": "down"}))
        return points

    async def _collect_postgresql(self) -> list[MetricPoint]:
        points: list[MetricPoint] = []
        try:
            from database.session import check_db_health

            started = time.perf_counter()
            result = await check_db_health()
            latency = round((time.perf_counter() - started) * 1000, 2)
            points.append(MetricPoint("postgresql.connected", 1 if result.get("ok") else 0))
            points.append(MetricPoint("api.request.duration_ms", latency, unit="ms", tags={"probe": "db_health"}))
        except Exception:
            points.append(MetricPoint("postgresql.connected", 0))
        return points

    async def _collect_jobs(self) -> list[MetricPoint]:
        try:
            from platform_jobs.job_metrics import job_metrics

            snap = await job_metrics.snapshot()
            return [
                MetricPoint("jobs.queue.size", snap.queued + snap.retrying),
                MetricPoint("jobs.running.count", snap.running),
                MetricPoint("jobs.dead_letter.count", snap.dead_letter),
            ]
        except Exception:
            return []

    async def _collect_workflows(self) -> list[MetricPoint]:
        try:
            from platform_management.management_service import management_service

            stats = await management_service.workflows_statistics()
            active = stats.get("active_executions", 0) if isinstance(stats, dict) else 0
            return [MetricPoint("workflow.executions.active", float(active))]
        except Exception:
            return [MetricPoint("workflow.executions.active", 0)]

    async def _collect_eventbus(self) -> list[MetricPoint]:
        try:
            from events.event_bus import PlatformEventBus

            subs = PlatformEventBus.list_subscribers()
            total_handlers = sum(len(v) for v in subs.values())
            return [
                MetricPoint("eventbus.handlers.count", float(total_handlers)),
                MetricPoint("eventbus.event_types.count", float(len(subs))),
            ]
        except Exception:
            return []

    async def _collect_realtime(self) -> list[MetricPoint]:
        try:
            from platform_realtime.realtime_hub import realtime_hub

            stats = realtime_hub.metrics.to_dict()
            return [
                MetricPoint("realtime.connections.count", float(stats.get("connected_clients", 0))),
                MetricPoint("realtime.messages_per_second", float(stats.get("messages_per_second", 0))),
            ]
        except Exception:
            return []

    async def _collect_integrations(self) -> list[MetricPoint]:
        try:
            from platform_integrations.integration_service import integration_service

            stats = integration_service.stats
            return [
                MetricPoint("integrations.invocations.total", float(stats.total_invocations)),
                MetricPoint("integrations.failures.total", float(stats.failed_invocations)),
            ]
        except Exception:
            return []

    def query(
        self,
        *,
        name: str | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        points = self._points
        if name:
            points = [p for p in points if p.name == name]
        return [p.to_dict() for p in points[-limit:]]

    def summary(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name, values in self._aggregates.items():
            if not values:
                continue
            result[name] = {
                "count": len(values),
                "min": round(min(values), 4),
                "max": round(max(values), 4),
                "avg": round(sum(values) / len(values), 4),
                "last": round(values[-1], 4),
            }
        return result

    async def flush_export_buffer(self) -> list[dict[str, Any]]:
        async with self._lock:
            batch = self._export_buffer[: self._batch_size]
            self._export_buffer = self._export_buffer[self._batch_size :]
            return batch


metrics_service = MetricsService()
