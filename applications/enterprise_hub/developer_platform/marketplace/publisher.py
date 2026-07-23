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
from applications.enterprise_hub.developer_platform.marketplace.signatures import MarketplaceSignatures


class MarketplacePublisher:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.repo = MarketplaceRepository(self.store)
        self.signatures = MarketplaceSignatures(self.store)

    def publish(
        self,
        *,
        package_id: str,
        name: str,
        version: str = "1.0.0",
        author: str = "bidex",
        description: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        listing = self.repo.publish_listing(
            package_id=package_id,
            name=name,
            version=version,
            author=author,
            description=description,
            tags=tags,
        )
        sig = self.signatures.sign(package_id=package_id, version=version, signer=author)
        pid = _id("sdp_pub")
        record = {
            "publish_id": pid,
            "listing_id": listing["listing_id"],
            "signature_id": sig["signature_id"],
            "package_id": package_id,
            "version": version,
            "at": _now(),
        }
        return self.store.sdp_publishes.save(pid, record)

    def status(self) -> dict[str, Any]:
        return {"publishes": len(self.store.sdp_publishes.list_all())}
