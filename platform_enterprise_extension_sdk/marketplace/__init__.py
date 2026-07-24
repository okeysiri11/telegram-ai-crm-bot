"""Marketplace Foundation — Sprint 25.0."""

from __future__ import annotations

from typing import Any

from platform_enterprise_extension_sdk.models import MARKETPLACE_CATEGORIES


class MarketplaceFoundation:
    def catalog(self) -> dict[str, Any]:
        return {
            "categories": list(MARKETPLACE_CATEGORIES),
            "foundation": True,
            "publish_ready": True,
            "listings": [],
        }

    def list_extension(self, *, extension: dict[str, Any], category: str) -> dict[str, Any]:
        category = (category or "").lower()
        if category not in MARKETPLACE_CATEGORIES:
            raise ValueError(f"unsupported category: {category}")
        if extension.get("status") not in ("verified", "published"):
            raise ValueError("only verified extensions may be listed")
        if not extension.get("signature"):
            raise ValueError("marketplace listing requires digital signature")
        return {
            "listing_id": f"mkt_{extension['extension_id']}",
            "extension_id": extension["extension_id"],
            "category": category,
            "name": extension.get("name"),
            "version": extension.get("version"),
            "status": "published",
        }
