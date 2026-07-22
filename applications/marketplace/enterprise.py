"""Enterprise Marketplace — private/org markets, internal packages, roles, company repo (Sprint 12.1)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.marketplace.core import MarketplaceManager, marketplace_manager
from applications.marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.marketplace.shared.store import MarketplaceStore, marketplace_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


ENTERPRISE_ROLES = ("admin", "publisher", "installer", "viewer")


class EnterpriseMarketplace:
    def __init__(self, store: MarketplaceStore | None = None, core: MarketplaceManager | None = None) -> None:
        self.store = store or marketplace_store
        self.core = core or marketplace_manager

    def create_org_marketplace(self, *, org_id: str, name: str) -> dict[str, Any]:
        if not org_id or not name:
            raise ValidationError("org_id and name required")
        mid = f"omkt_{uuid.uuid4().hex[:10]}"
        market = {
            "market_id": mid,
            "org_id": org_id,
            "name": name,
            "private": True,
            "roles": {},
            "created_at": _now(),
        }
        self.store.org_markets.save(mid, market)
        return market

    def get_org_marketplace(self, market_id: str) -> dict[str, Any]:
        item = self.store.org_markets.get(market_id)
        if item is None:
            raise NotFoundError("org_marketplace", market_id)
        return item

    def publish_internal(
        self,
        *,
        org_id: str,
        name: str,
        kind: str = "plugin",
        category: str = "custom_enterprise",
        version: str = "1.0.0",
    ) -> dict[str, Any]:
        pkg = self.core.publish_package(
            name=name,
            kind=kind,
            category=category,
            version=version,
            publisher=org_id,
            private=True,
            org_id=org_id,
            metadata={"internal": True},
        )
        self.store.private_packages.save(pkg["package_id"], pkg)
        return pkg

    def company_repository(self, org_id: str) -> dict[str, Any]:
        packages = [p for p in self.store.packages.list_all() if p.get("org_id") == org_id]
        return {"org_id": org_id, "packages": packages, "count": len(packages), "at": _now()}

    def grant_role(self, market_id: str, *, principal: str, role: str) -> dict[str, Any]:
        if role not in ENTERPRISE_ROLES:
            raise ValidationError(f"role must be one of {ENTERPRISE_ROLES}")
        market = self.get_org_marketplace(market_id)
        market.setdefault("roles", {})[principal] = role
        self.store.org_markets.save(market_id, market)
        return {"market_id": market_id, "principal": principal, "role": role}

    def private_marketplace_catalog(self, org_id: str) -> dict[str, Any]:
        packages = [p for p in self.store.packages.list_all() if p.get("private") and p.get("org_id") == org_id]
        markets = [m for m in self.store.org_markets.list_all() if m.get("org_id") == org_id]
        return {"org_id": org_id, "markets": markets, "packages": packages, "count": len(packages)}

    def status(self) -> dict[str, Any]:
        return {
            "enterprise_marketplace": "1.0",
            "org_markets": len(self.store.org_markets.list_all()),
            "private_packages": len(self.store.private_packages.list_all()),
            "ready": True,
        }


enterprise_marketplace = EnterpriseMarketplace()
