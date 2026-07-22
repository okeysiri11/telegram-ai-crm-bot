# MarketplaceApplication — AI Marketplace & Plugin Store (Sprint 12.1).

from __future__ import annotations

from typing import Any

from applications.marketplace.ai_store import AIMarketplace, ai_marketplace
from applications.marketplace.config import DEFAULT_CONFIG, MarketplaceConfig
from applications.marketplace.connectors import ConnectorMarketplace, connector_marketplace
from applications.marketplace.core import MarketplaceManager, marketplace_manager
from applications.marketplace.enterprise import EnterpriseMarketplace, enterprise_marketplace
from applications.marketplace.portal import DeveloperPortal, developer_portal
from applications.marketplace.security import MarketplaceSecurity, marketplace_security
from applications.marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.marketplace.workflows import WorkflowMarketplace, workflow_marketplace


class MarketplaceApplication:
    def __init__(
        self,
        *,
        config: MarketplaceConfig | None = None,
        store: MarketplaceStore | None = None,
        core: MarketplaceManager | None = None,
        ai: AIMarketplace | None = None,
        workflows: WorkflowMarketplace | None = None,
        connectors: ConnectorMarketplace | None = None,
        security: MarketplaceSecurity | None = None,
        portal: DeveloperPortal | None = None,
        enterprise: EnterpriseMarketplace | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or marketplace_store
        self.core = core or marketplace_manager
        self.ai = ai or ai_marketplace
        self.workflows = workflows or workflow_marketplace
        self.connectors = connectors or connector_marketplace
        self.security = security or marketplace_security
        self.portal = portal or developer_portal
        self.enterprise = enterprise or enterprise_marketplace

    def reset(self) -> None:
        self.store.reset()

    def health(self) -> dict[str, Any]:
        # Ensure connector catalog available without rewriting other apps
        self.connectors._seed()
        return {
            "status": "ok",
            "application": self.config.application,
            "application_name": self.config.application_name,
            "application_version": self.config.application_version,
            "release_status": self.config.release_status,
            "api_prefix": self.config.api_prefix,
            "platform_dependency": self.config.platform_dependency,
            "ai_marketplace_ready": True,
            "plugin_store_ready": True,
            "developer_portal_ready": True,
            "enterprise_marketplace_ready": True,
            "engines": {
                "marketplace_core": self.config.marketplace_core,
                "plugin_store": self.config.plugin_store,
                "ai_marketplace": self.config.ai_marketplace,
                "workflow_marketplace": self.config.workflow_marketplace,
                "connector_marketplace": self.config.connector_marketplace,
                "security": self.config.security,
                "developer_portal": self.config.developer_portal,
                "enterprise_marketplace": self.config.enterprise_marketplace,
            },
            "core": self.core.status(),
            "ai": self.ai.status(),
            "workflows": self.workflows.status(),
            "connectors": self.connectors.status(),
            "security": self.security.status(),
            "portal": self.portal.status(),
            "enterprise": self.enterprise.status(),
        }


marketplace = MarketplaceApplication()
