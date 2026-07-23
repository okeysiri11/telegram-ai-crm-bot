from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"



from applications.enterprise_hub.developer_platform.marketplace.repository import MarketplaceRepository
from applications.enterprise_hub.developer_platform.package_manager import PackageManager


class MarketplaceInstaller:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.repo = MarketplaceRepository(self.store)
        self.packages = PackageManager(self.store)

    def install_listing(self, *, listing_id: str) -> dict[str, Any]:
        listing = self.store.sdp_listings.get(listing_id)
        if not listing:
            raise NotFoundError(f"listing not found: {listing_id}")
        action = self.packages.install(
            package_id=listing["package_id"],
            name=listing["name"],
            version=listing.get("version", "1.0.0"),
            plugin_id=listing["package_id"],
        )
        listing["downloads"] = int(listing.get("downloads", 0)) + 1
        self.store.sdp_listings.save(listing_id, listing)
        iid = _id("sdp_inst")
        return self.store.sdp_installs.save(
            iid,
            {
                "install_id": iid,
                "listing_id": listing_id,
                "package_id": listing["package_id"],
                "action_id": action["action_id"],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"installs": len(self.store.sdp_installs.list_all())}
