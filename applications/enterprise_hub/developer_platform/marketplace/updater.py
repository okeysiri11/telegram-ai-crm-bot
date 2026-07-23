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



from applications.enterprise_hub.developer_platform.package_manager import PackageManager


class MarketplaceUpdater:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.packages = PackageManager(self.store)

    def check_updates(self) -> list[dict[str, Any]]:
        updates = []
        for listing in self.store.sdp_listings.list_all():
            pkg = self.store.sdp_packages.get(listing["package_id"])
            if pkg and pkg.get("version") != listing.get("version"):
                updates.append(
                    {
                        "package_id": listing["package_id"],
                        "installed": pkg.get("version"),
                        "available": listing.get("version"),
                        "listing_id": listing["listing_id"],
                    }
                )
        return updates

    def auto_update(self, *, package_id: str, version: str) -> dict[str, Any]:
        action = self.packages.update(package_id=package_id, version=version)
        uid = _id("sdp_upd")
        return self.store.sdp_updates.save(
            uid,
            {
                "update_id": uid,
                "package_id": package_id,
                "version": version,
                "action_id": action["action_id"],
                "automatic": True,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "updates": len(self.store.sdp_updates.list_all()),
            "available": len(self.check_updates()),
        }
