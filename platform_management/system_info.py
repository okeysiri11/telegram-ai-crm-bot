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
    from services.platform_infrastructure_service import platform_infrastructure_service

    return await platform_infrastructure_service.component_statuses()


async def _redis_status() -> dict[str, Any]:
    from services.platform_infrastructure_service import platform_infrastructure_service

    return await platform_infrastructure_service.redis_status()
