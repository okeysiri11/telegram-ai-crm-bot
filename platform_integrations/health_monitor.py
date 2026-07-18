# Health monitor — connector status aggregation.

from __future__ import annotations

import asyncio
import logging

from platform_integrations.connector_registry import connector_registry
from platform_integrations.models import ConnectorHealth, ConnectorStatus

logger = logging.getLogger(__name__)


class HealthMonitor:
    def __init__(self) -> None:
        self._cache: dict[str, ConnectorHealth] = {}

    def reset(self) -> None:
        self._cache.clear()

    async def check_connector(self, connector_id: str) -> ConnectorHealth:
        meta = connector_registry.get_metadata(connector_id)
        if not meta.enabled:
            health = ConnectorHealth(
                connector_id=connector_id,
                provider=meta.provider,
                status=ConnectorStatus.DISABLED.value,
            )
            self._cache[connector_id] = health
            return health

        connector = connector_registry.get(connector_id)
        health = await connector.health_check()
        self._cache[connector_id] = health
        return health

    async def check_all(self) -> list[ConnectorHealth]:
        results = await asyncio.gather(
            *[self.check_connector(m.connector_id) for m in connector_registry.list_metadata()],
            return_exceptions=True,
        )
        health_list: list[ConnectorHealth] = []
        for result in results:
            if isinstance(result, ConnectorHealth):
                health_list.append(result)
        return health_list

    def cached(self) -> list[ConnectorHealth]:
        return list(self._cache.values())

    async def overall_status(self) -> str:
        checks = await self.check_all()
        if not checks:
            return "unknown"
        if any(c.status == ConnectorStatus.FAILED.value for c in checks):
            return "degraded"
        if any(c.status == ConnectorStatus.DISABLED.value for c in checks):
            return "partial"
        return "healthy"


health_monitor = HealthMonitor()
