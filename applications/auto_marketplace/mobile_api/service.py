# Mobile API — rate limiting, offline sync, versioning.

from __future__ import annotations

import time
from typing import Any

from applications.auto_marketplace.config import DEFAULT_CONFIG


class MobileAPIService:
    API_VERSION = "v1"
    RATE_LIMIT = 100
    WINDOW_SEC = 60

    def __init__(self) -> None:
        self._buckets: dict[str, list[float]] = {}

    def api_info(self) -> dict[str, Any]:
        return {
            "api_version": self.API_VERSION,
            "application_version": DEFAULT_CONFIG.application_version,
            "mobile_prefix": DEFAULT_CONFIG.mobile_api_prefix,
            "endpoints": ["feed", "vehicles", "favorites", "notifications", "sync"],
            "documentation": "/api/auto/mobile/v1/docs",
        }

    def check_rate_limit(self, client_id: str) -> tuple[bool, int]:
        now = time.time()
        window_start = now - self.WINDOW_SEC
        hits = [t for t in self._buckets.get(client_id, []) if t > window_start]
        if len(hits) >= self.RATE_LIMIT:
            return False, 0
        hits.append(now)
        self._buckets[client_id] = hits
        return True, self.RATE_LIMIT - len(hits)

    def offline_sync_manifest(self, user_id: str, *, last_sync: float = 0) -> dict[str, Any]:
        from applications.auto_marketplace.shared.store import marketplace_store

        store = marketplace_store
        return {
            "user_id": user_id,
            "last_sync": last_sync,
            "sync_at": time.time(),
            "entities": {
                "favorites": len([f for f in store.favorites.list_all() if f.user_id == user_id]),
                "notifications": len([n for n in store.portal_notifications.list_all() if n.user_id == user_id and n.created_at > last_sync]),
                "garage": len([g for g in store.garage_vehicles.list_all() if g.user_id == user_id]),
            },
            "delta_available": True,
        }

    def mobile_feed(self, user_id: str = "") -> dict[str, Any]:
        from applications.auto_marketplace.shared.store import marketplace_store

        vehicles = marketplace_store.catalog_vehicles.list_all()[:10]
        return {
            "featured": [v.to_dict() for v in vehicles],
            "user_id": user_id,
        }


mobile_api_service = MobileAPIService()
