# Enterprise health — deep dependency and readiness probes.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.config import DEFAULT_CONFIG, AutoMarketplaceConfig
from applications.auto_marketplace.integrations.cross_platform import (
    CrossPlatformIntegrationEngine,
    cross_platform_integration_engine,
)


class HealthEngine:
    def __init__(
        self,
        config: AutoMarketplaceConfig | None = None,
        cross_platform: CrossPlatformIntegrationEngine | None = None,
    ) -> None:
        self._config = config or DEFAULT_CONFIG
        self._cross = cross_platform or cross_platform_integration_engine

    def live(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "application": "auto_marketplace",
            "application_version": self._config.application_version,
            "production_ready": self._config.production_ready,
        }

    def ready(self) -> dict[str, Any]:
        from applications.auto_marketplace.application import auto_marketplace

        domains = ("marketplace", "auto_ai", "transactions", "service", "logistics", "fleet_ops", "enterprise")
        present = {d: hasattr(auto_marketplace, d) for d in domains}
        return {
            "status": "ready" if all(present.values()) else "degraded",
            "domains": present,
            "enterprise_engine": self._config.enterprise_engine,
            "global_network": self._config.global_network,
        }

    def dependencies(self) -> dict[str, Any]:
        return {
            "platform": self._config.platform_dependency,
            "ecosystem": self._config.ecosystem_dependency,
            "cross_platform": self._cross.status(),
            "untouched": {
                "platform_core": True,
                "ecosystem": True,
                "agro_marketplace": True,
                "port_erp": True,
            },
        }

    def deep(self) -> dict[str, Any]:
        return {**self.live(), **self.ready(), "dependencies": self.dependencies()}

    def metrics(self) -> dict[str, Any]:
        return {"health": self.deep()}


health_engine = HealthEngine()
