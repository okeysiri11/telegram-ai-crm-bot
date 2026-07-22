# Cross-platform shared services — identity, AI, docs, analytics, notifications, billing.

from __future__ import annotations

from applications.auto_marketplace.enterprise.models import CrossPlatformLink
from applications.auto_marketplace.integrations.agro_bridge import AgroMarketplaceBridge, agro_marketplace_bridge
from applications.auto_marketplace.integrations.port_bridge import PortERPBridge, port_erp_bridge
from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


SHARED_CAPABILITIES = (
    "identity",
    "ai_agents",
    "documents",
    "analytics",
    "notifications",
    "billing",
)


class CrossPlatformIntegrationEngine:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        agro: AgroMarketplaceBridge | None = None,
        port: PortERPBridge | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self.agro = agro or agro_marketplace_bridge
        self.port = port or port_erp_bridge

    def link(self, *, target: str, shared: list[str] | None = None) -> CrossPlatformLink:
        if target not in {"agro_marketplace", "port_erp", "ecosystem", "platform"}:
            raise ValidationError(f"unsupported target: {target}")
        caps = shared or list(SHARED_CAPABILITIES)
        item = CrossPlatformLink(target=target, shared=caps)
        return self._store.cross_platform_links.save(item.link_id, item)

    def list_links(self) -> list[CrossPlatformLink]:
        return self._store.cross_platform_links.list_all()

    def status(self) -> dict:
        return {
            "agro": self.agro.health(),
            "port_erp": self.port.health(),
            "links": len(self.list_links()),
            "shared_capabilities": list(SHARED_CAPABILITIES),
        }

    def metrics(self) -> dict:
        return {"cross_platform_links": self._store.cross_platform_links.count(), **self.status()}


cross_platform_integration_engine = CrossPlatformIntegrationEngine()
