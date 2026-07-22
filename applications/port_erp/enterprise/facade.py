# Enterprise domain facade — network, integration, registry, production.

from __future__ import annotations

from typing import Any

from applications.port_erp.analytics_global.engine import GlobalAnalyticsEngine, global_analytics_engine
from applications.port_erp.deployment.engine import DeploymentEngine, deployment_engine
from applications.port_erp.digital_exchange.engine import DigitalExchangeEngine, digital_exchange_engine
from applications.port_erp.enterprise.engine import (
    EnterpriseIntegrationEngine,
    enterprise_integration_engine,
)
from applications.port_erp.global_registry.engine import GlobalRegistryEngine, global_registry_engine
from applications.port_erp.health.engine import HealthEngine, health_engine
from applications.port_erp.integration.engine import IntegrationEngine, integration_engine
from applications.port_erp.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.port_erp.network.engine import NetworkEngine, network_engine
from applications.port_erp.partners.engine import PartnerEngine, partner_engine
from applications.port_erp.production.engine import ProductionEngine, production_engine


class EnterpriseDomainEngine:
    """Sprint 9.8 facade — enterprise, network, registry, production release."""

    def __init__(
        self,
        enterprise: EnterpriseIntegrationEngine | None = None,
        integration: IntegrationEngine | None = None,
        network: NetworkEngine | None = None,
        partners: PartnerEngine | None = None,
        registry: GlobalRegistryEngine | None = None,
        exchange: DigitalExchangeEngine | None = None,
        analytics: GlobalAnalyticsEngine | None = None,
        production: ProductionEngine | None = None,
        deployment: DeploymentEngine | None = None,
        health: HealthEngine | None = None,
        platform: PlatformBridge | None = None,
    ) -> None:
        self.enterprise = enterprise or enterprise_integration_engine
        self.integration = integration or integration_engine
        self.network = network or network_engine
        self.partners = partners or partner_engine
        self.registry = registry or global_registry_engine
        self.exchange = exchange or digital_exchange_engine
        self.analytics = analytics or global_analytics_engine
        self.production = production or production_engine
        self.deployment = deployment or deployment_engine
        self.health = health or health_engine
        self._platform = platform or platform_bridge

    def metrics(self) -> dict[str, Any]:
        return {
            **self.network.metrics(),
            "registry": self.registry.summary(),
            "integrations": len(self.integration.list_links()),
            "exchange_offers": len(self.exchange.list_offers()),
            "deployment_profiles": len(self.deployment.list_profiles()),
            "release_reports": len(self.production.list_reports()),
        }

    async def remember_snapshot(self) -> None:
        await self._platform.remember_context("enterprise:snapshot", self.metrics())


enterprise_domain_engine = EnterpriseDomainEngine()
