"""Connector Marketplace — Telegram, WhatsApp, Email, Google, Microsoft, GitHub, Stripe, etc. (Sprint 12.1)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from applications.marketplace.core import MarketplaceManager, marketplace_manager
from applications.marketplace.shared.store import MarketplaceStore, marketplace_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


CONNECTOR_CATALOG = (
    ("telegram", "messaging"),
    ("whatsapp", "messaging"),
    ("email", "messaging"),
    ("google", "productivity"),
    ("microsoft", "productivity"),
    ("github", "devtools"),
    ("stripe", "payments"),
    ("binance", "crypto"),
    ("openai", "ai"),
    ("anthropic", "ai"),
    ("local_apis", "enterprise"),
    ("enterprise_apis", "enterprise"),
)


class ConnectorMarketplace:
    def __init__(self, store: MarketplaceStore | None = None, core: MarketplaceManager | None = None) -> None:
        self.store = store or marketplace_store
        self.core = core or marketplace_manager
        self._seed()

    def _seed(self) -> None:
        if self.store.connectors.list_all():
            return
        for name, family in CONNECTOR_CATALOG:
            self.core.publish_package(
                name=f"{name}_connector",
                kind="connector",
                category="custom_enterprise",
                version="1.0.0",
                publisher="marketplace",
                metadata={"connector": name, "family": family, "seeded": True},
            )

    def list_connectors(self) -> list[dict[str, Any]]:
        self._seed()
        return self.core.list_packages(kind="connector")

    def install_connector(self, package_id: str, *, org_id: str = "") -> dict[str, Any]:
        self._seed()
        return self.core.install(package_id, org_id=org_id)

    def catalog(self) -> dict[str, Any]:
        return {
            "connectors": [c[0] for c in CONNECTOR_CATALOG],
            "families": sorted({c[1] for c in CONNECTOR_CATALOG}),
            "at": _now(),
        }

    def status(self) -> dict[str, Any]:
        self._seed()
        return {"connector_marketplace": "1.0", "connectors": len(self.list_connectors()), "ready": True}


connector_marketplace = ConnectorMarketplace()
