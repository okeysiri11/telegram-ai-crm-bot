# Dashboard aggregator — parallel widget fetch with widget-level cache.

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, Awaitable, Callable

from platform_operations.activity_service import (
    build_configuration_changes,
    build_notifications_queue,
    build_recent_audit,
    build_recent_events,
)
from platform_operations.jobs_widgets import (
    build_failed_jobs,
    build_job_execution_rate,
    build_job_queue_size,
    build_job_retry_rate,
    build_running_jobs,
    build_worker_health,
)
from platform_operations.observability_widgets import (
    database_health_widget as build_observability_database_health,
    integration_health_widget as build_observability_integration_health,
    performance_widget as build_observability_performance,
    platform_health_widget as build_platform_health,
    queue_health_widget as build_observability_queue_health,
    realtime_health_widget as build_observability_realtime_health,
    slowest_apis_widget as build_slowest_apis,
    worker_health_widget as build_observability_worker_health,
)
from platform_operations.metrics_service import build_top_kpis
from platform_operations.models import (
    DashboardPayload,
    SharedDashboardContext,
    WidgetMeta,
    WidgetPayload,
    utc_now_iso,
)
from platform_operations.status_service import (
    build_platform_version,
    build_system_status,
    build_workflow_status,
)
from platform_operations.summary_service import (
    build_active_requests,
    build_manager_load,
    build_requests_by_vertical,
    build_sla_status,
)
from platform_operations.widgets import ALL_WIDGET_IDS, get_widget_spec

logger = logging.getLogger(__name__)

WidgetBuilder = Callable[[SharedDashboardContext], Awaitable[dict[str, Any]]]

WIDGET_BUILDERS: dict[str, WidgetBuilder] = {
    "system_status": build_system_status,
    "active_requests": build_active_requests,
    "requests_by_vertical": build_requests_by_vertical,
    "manager_load": build_manager_load,
    "sla_status": build_sla_status,
    "workflow_status": build_workflow_status,
    "recent_events": build_recent_events,
    "recent_audit": build_recent_audit,
    "configuration_changes": build_configuration_changes,
    "top_kpis": build_top_kpis,
    "notifications_queue": build_notifications_queue,
    "platform_version": build_platform_version,
    "running_jobs": build_running_jobs,
    "failed_jobs": build_failed_jobs,
    "job_queue_size": build_job_queue_size,
    "worker_health": build_worker_health,
    "job_execution_rate": build_job_execution_rate,
    "job_retry_rate": build_job_retry_rate,
    "platform_health": build_platform_health,
    "observability_performance": build_observability_performance,
    "slowest_apis": build_slowest_apis,
    "observability_queue_health": build_observability_queue_health,
    "observability_worker_health": build_observability_worker_health,
    "observability_integration_health": build_observability_integration_health,
    "observability_realtime_health": build_observability_realtime_health,
    "observability_database_health": build_observability_database_health,
}

_DASHBOARD_CACHE_KEY = "full_dashboard"
_DASHBOARD_TTL = int(os.getenv("OPS_DASHBOARD_TTL_SECONDS", "15"))


# ---- widget cache (Redis + memory) ----

class OperationsWidgetCache:
    def __init__(self) -> None:
        self._memory: dict[str, tuple[float, Any]] = {}
        self._redis = None
        self._redis_checked = False

    async def _get_redis(self):
        if self._redis_checked:
            return self._redis
        self._redis_checked = True
        redis_url = os.getenv("REDIS_URL", "").strip()
        if not redis_url:
            return None
        try:
            from redis.asyncio import Redis

            client = Redis.from_url(redis_url, decode_responses=True)
            await client.ping()
            self._redis = client
        except Exception:
            self._redis = None
        return self._redis

    def _key(self, widget_id: str) -> str:
        return f"platform:ops:widget:{widget_id}"

    async def get(self, widget_id: str) -> dict[str, Any] | None:
        ck = self._key(widget_id)
        redis = await self._get_redis()
        if redis is not None:
            try:
                raw = await redis.get(ck)
                if raw is not None:
                    return json.loads(raw)
            except Exception:
                pass
        entry = self._memory.get(ck)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            self._memory.pop(ck, None)
            return None
        return value

    async def set(self, widget_id: str, payload: dict[str, Any], *, ttl_seconds: int) -> None:
        ck = self._key(widget_id)
        ttl = max(int(ttl_seconds), 1)
        self._memory[ck] = (time.monotonic() + ttl, payload)
        redis = await self._get_redis()
        if redis is not None:
            try:
                await redis.setex(ck, ttl, json.dumps(payload, default=str))
            except Exception:
                pass

    async def clear(self) -> None:
        self._memory.clear()
        redis = await self._get_redis()
        if redis is not None:
            try:
                async for key in redis.scan_iter(match="platform:ops:widget:*"):
                    await redis.delete(key)
            except Exception:
                pass


widget_cache = OperationsWidgetCache()


class OperationsDashboardService:
    @staticmethod
    async def fetch_widget(
        widget_id: str,
        *,
        shared: SharedDashboardContext | None = None,
        use_cache: bool = True,
    ) -> WidgetPayload:
        spec = get_widget_spec(widget_id)
        builder = WIDGET_BUILDERS.get(widget_id)
        if builder is None:
            from platform_operations.exceptions import WidgetNotFoundError

            raise WidgetNotFoundError(widget_id)

        if use_cache:
            cached = await widget_cache.get(widget_id)
            if cached is not None:
                meta = WidgetMeta(
                    widget_id=widget_id,
                    updated_at=cached.get("meta", {}).get("updated_at", utc_now_iso()),
                    refresh_interval=spec.refresh_interval,
                    status="cached",
                    cache_hit=True,
                    duration_ms=0.0,
                )
                return WidgetPayload(meta=meta, data=cached.get("data", {}))

        started = time.perf_counter()
        ctx = shared or SharedDashboardContext()
        status: str = "ok"
        try:
            data = await builder(ctx)
        except Exception as exc:
            logger.warning("widget_fetch_failed widget=%s error=%s", widget_id, exc, exc_info=True)
            data = {"error": str(exc)}
            status = "error"

        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        meta = WidgetMeta(
            widget_id=widget_id,
            updated_at=utc_now_iso(),
            refresh_interval=spec.refresh_interval,
            status=status,  # type: ignore[arg-type]
            cache_hit=False,
            duration_ms=duration_ms,
        )
        payload = WidgetPayload(meta=meta, data=data)
        await widget_cache.set(widget_id, payload.to_dict(), ttl_seconds=spec.ttl_seconds)
        return payload

    @staticmethod
    async def aggregate_dashboard(*, use_cache: bool = True) -> DashboardPayload:
        started = time.perf_counter()

        if use_cache:
            cached = await widget_cache.get(_DASHBOARD_CACHE_KEY)
            if cached is not None:
                widgets = {
                    wid: WidgetPayload(
                        meta=WidgetMeta(
                            widget_id=wid,
                            updated_at=cached["widgets"][wid]["meta"]["updated_at"],
                            refresh_interval=cached["widgets"][wid]["meta"]["refresh_interval"],
                            status="cached",
                            cache_hit=True,
                        ),
                        data=cached["widgets"][wid]["data"],
                    )
                    for wid in cached.get("widgets", {})
                }
                return DashboardPayload(
                    generated_at=cached.get("generated_at", utc_now_iso()),
                    widgets=widgets,
                    duration_ms=round((time.perf_counter() - started) * 1000, 2),
                    cache_hit=True,
                )

        shared = SharedDashboardContext()
        results = await asyncio.gather(
            *[
                OperationsDashboardService.fetch_widget(wid, shared=shared, use_cache=use_cache)
                for wid in ALL_WIDGET_IDS
            ],
            return_exceptions=True,
        )

        widgets: dict[str, WidgetPayload] = {}
        for wid, result in zip(ALL_WIDGET_IDS, results, strict=True):
            if isinstance(result, Exception):
                spec = get_widget_spec(wid)
                widgets[wid] = WidgetPayload(
                    meta=WidgetMeta(
                        widget_id=wid,
                        updated_at=utc_now_iso(),
                        refresh_interval=spec.refresh_interval,
                        status="error",
                    ),
                    data={"error": str(result)},
                )
            else:
                widgets[wid] = result

        dashboard = DashboardPayload(
            generated_at=utc_now_iso(),
            widgets=widgets,
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
            cache_hit=False,
        )
        await widget_cache.set(
            _DASHBOARD_CACHE_KEY,
            dashboard.to_dict(),
            ttl_seconds=_DASHBOARD_TTL,
        )
        return dashboard

    @staticmethod
    async def invalidate_cache() -> None:
        await widget_cache.clear()


operations_dashboard_service = OperationsDashboardService()
