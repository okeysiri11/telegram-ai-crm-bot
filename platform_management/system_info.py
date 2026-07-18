# Platform system information — version, uptime, subsystem status.

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any

_START_TIME = time.monotonic()
_BUILD_VERSION = os.getenv("PLATFORM_BUILD_VERSION", "1.0.0")
_PLATFORM_VERSION = os.getenv("PLATFORM_VERSION", "2.0.0")
_GIT_REVISION = os.getenv("GIT_REVISION", os.getenv("GIT_COMMIT", "unknown"))


def uptime_seconds() -> float:
    return round(time.monotonic() - _START_TIME, 2)


async def get_system_info() -> dict[str, Any]:
    from config import ENVIRONMENT, REDIS_URL

    components = await get_component_statuses()

    return {
        "platform_version": _PLATFORM_VERSION,
        "build_version": _BUILD_VERSION,
        "git_revision": _GIT_REVISION,
        "environment": ENVIRONMENT,
        "timezone": str(datetime.now(timezone.utc).astimezone().tzinfo or "UTC"),
        "uptime_seconds": uptime_seconds(),
        "database_status": components.get("database", {}),
        "redis_status": components.get("redis", {}),
        "workflow_status": components.get("workflow", {}),
        "sdk_status": components.get("sdk", {}),
        "configuration_status": components.get("configuration", {}),
        "redis_configured": bool(REDIS_URL),
    }


async def get_component_statuses() -> dict[str, Any]:
    from database.session import check_db_health
    from platform_configuration.config_provider import config_provider
    from platform_sdk.vertical_registry import vertical_registry
    from platform_sdk.workflow_loader import sdk_workflow_loader

    db = await check_db_health()
    redis_status = await _redis_status()

    try:
        sdk_workflow_loader.ensure_loaded()
        workflow_count = len(sdk_workflow_loader._registry.list_ids())  # noqa: SLF001
        workflow_status = "healthy"
    except Exception as exc:
        workflow_count = 0
        workflow_status = "degraded"
        workflow_error = str(exc)
    else:
        workflow_error = None

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


async def _redis_status() -> dict[str, Any]:
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
