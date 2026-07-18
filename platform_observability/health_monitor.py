# Health monitor — aggregate platform component health.

from __future__ import annotations

import logging
from typing import Any

from platform_observability.observability_events import HealthChangedEvent

logger = logging.getLogger(__name__)


class HealthMonitor:
    def __init__(self) -> None:
        self._status: dict[str, str] = {}

    def reset(self) -> None:
        self._status.clear()

    async def check_all(self) -> dict[str, Any]:
        components: dict[str, dict[str, Any]] = {}

        components["database"] = await self._check_database()
        components["redis"] = await self._check_redis()
        components["jobs"] = await self._check_jobs()
        components["integrations"] = await self._check_integrations()
        components["realtime"] = await self._check_realtime()
        components["event_bus"] = await self._check_eventbus()

        overall = self._overall(components)
        await self._emit_changes(components)

        return {
            "overall_status": overall,
            "components": components,
            "checked_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
        }

    async def _check_database(self) -> dict[str, Any]:
        try:
            from database.session import check_db_health

            result = await check_db_health()
            status = "healthy" if result.get("ok") else "unhealthy"
            return {"status": status, "details": result}
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}

    async def _check_redis(self) -> dict[str, Any]:
        import os

        if not os.getenv("REDIS_URL", "").strip():
            return {"status": "not_configured"}
        try:
            from redis.asyncio import Redis

            client = Redis.from_url(os.getenv("REDIS_URL", ""), decode_responses=True)
            await client.ping()
            await client.aclose()
            return {"status": "healthy"}
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}

    async def _check_jobs(self) -> dict[str, Any]:
        try:
            from platform_jobs.worker_manager import worker_manager

            summary = worker_manager.health_summary()
            status = "healthy" if summary.get("healthy", 0) > 0 or summary.get("total", 0) == 0 else "degraded"
            return {"status": status, "workers": summary}
        except Exception as exc:
            return {"status": "unknown", "error": str(exc)}

    async def _check_integrations(self) -> dict[str, Any]:
        try:
            from platform_integrations.integration_service import integration_service

            health = await integration_service.health()
            return {"status": health.get("overall_status", "unknown"), "details": health}
        except Exception as exc:
            return {"status": "unknown", "error": str(exc)}

    async def _check_realtime(self) -> dict[str, Any]:
        try:
            from platform_realtime.realtime_hub import realtime_hub

            stats = realtime_hub.metrics.to_dict()
            return {
                "status": "healthy",
                "connections": stats.get("connected_clients", 0),
                "messages_per_second": stats.get("messages_per_second", 0),
            }
        except Exception as exc:
            return {"status": "unknown", "error": str(exc)}

    async def _check_eventbus(self) -> dict[str, Any]:
        try:
            from events.event_bus import PlatformEventBus

            subs = PlatformEventBus.list_subscribers()
            return {"status": "healthy", "event_types": len(subs)}
        except Exception as exc:
            return {"status": "unknown", "error": str(exc)}

    @staticmethod
    def _overall(components: dict[str, dict]) -> str:
        statuses = [c.get("status", "unknown") for c in components.values()]
        if any(s == "unhealthy" for s in statuses):
            return "unhealthy"
        if any(s in ("degraded", "partial") for s in statuses):
            return "degraded"
        if all(s in ("healthy", "not_configured", "unknown") for s in statuses):
            return "healthy"
        return "degraded"

    async def _emit_changes(self, components: dict[str, dict]) -> None:
        from events.event_bus import publish

        for name, data in components.items():
            current = data.get("status", "unknown")
            previous = self._status.get(name)
            if previous is not None and previous != current:
                await publish(
                    HealthChangedEvent(
                        component=name,
                        previous_status=previous,
                        current_status=current,
                    )
                )
            self._status[name] = current


health_monitor = HealthMonitor()
