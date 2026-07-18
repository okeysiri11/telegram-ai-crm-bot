# Platform system information — version, uptime, subsystem status.

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from platform_configuration.configuration_center import configuration_center

logger = logging.getLogger(__name__)

_START_TIME = time.monotonic()


def uptime_seconds() -> float:
    return round(time.monotonic() - _START_TIME, 2)


async def get_system_info() -> dict[str, Any]:
    s = configuration_center.settings

    components = await get_component_statuses()

    return {
        "platform_version": s.management.platform_version,
        "build_version": s.management.build_version,
        "git_revision": s.management.git_revision,
        "environment": s.security.environment,
        "timezone": str(datetime.now(timezone.utc).astimezone().tzinfo or "UTC"),
        "uptime_seconds": uptime_seconds(),
        "database_status": components.get("database", {}),
        "redis_status": components.get("redis", {}),
        "workflow_status": components.get("workflow", {}),
        "sdk_status": components.get("sdk", {}),
        "configuration_status": components.get("configuration", {}),
        "redis_configured": bool(s.redis.url),
    }


async def get_component_statuses() -> dict[str, Any]:
    from services.platform_infrastructure_service import platform_infrastructure_service

    return await platform_infrastructure_service.component_statuses()


async def _redis_status() -> dict[str, Any]:
    from services.platform_infrastructure_service import platform_infrastructure_service

    return await platform_infrastructure_service.redis_status()
