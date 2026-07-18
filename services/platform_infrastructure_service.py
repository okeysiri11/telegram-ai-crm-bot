# Platform infrastructure probes — database/redis health for upper layers.

from __future__ import annotations

from typing import Any


class PlatformInfrastructureService:
    """Infrastructure health checks — only layer allowed to touch database.session probes."""

    @staticmethod
    async def database_health() -> dict[str, Any]:
        from database.session import check_db_health

        return await check_db_health()

    @staticmethod
    async def redis_status() -> dict[str, Any]:
        from config import REDIS_URL

        if not REDIS_URL:
            return {"status": "skipped", "configured": False}
        try:
            from redis.asyncio import Redis

            client = Redis.from_url(REDIS_URL, decode_responses=True)
            await client.ping()
            await client.aclose()
            return {"status": "healthy", "configured": True}
        except Exception as exc:
            return {"status": "unhealthy", "configured": True, "error": str(exc)}

    @staticmethod
    async def component_statuses() -> dict[str, Any]:
        from platform_configuration.config_provider import config_provider
        from platform_sdk.vertical_registry import vertical_registry
        from platform_sdk.workflow_loader import sdk_workflow_loader

        db = await PlatformInfrastructureService.database_health()
        redis_status = await PlatformInfrastructureService.redis_status()

        try:
            sdk_workflow_loader.ensure_loaded()
            workflow_count = len(sdk_workflow_loader._registry.list_ids())  # noqa: SLF001
            workflow_status = "healthy"
            workflow_error = None
        except Exception as exc:
            workflow_count = 0
            workflow_status = "degraded"
            workflow_error = str(exc)

        return {
            "database": {
                "status": "healthy" if db.get("ok") else "unhealthy",
                "details": db,
            },
            "redis": redis_status,
            "workflow": {
                "status": workflow_status,
                "definitions_loaded": workflow_count,
                "error": workflow_error,
            },
            "sdk": {
                "status": "healthy",
                "verticals_registered": len(vertical_registry.list_codes()),
                "verticals_enabled": len(vertical_registry.list_enabled_codes()),
            },
            "configuration": {
                "status": "healthy",
                "keys_loaded": len(config_provider.snapshot()),
            },
            "notifications": {
                "status": "healthy" if config_provider.is_notification_enabled() else "disabled",
            },
        }


platform_infrastructure_service = PlatformInfrastructureService()
