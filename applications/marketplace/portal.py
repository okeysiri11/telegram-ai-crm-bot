"""Developer Portal — publish, validate, analytics, downloads, ratings, docs (Sprint 12.1)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.marketplace.core import MarketplaceManager, marketplace_manager
from applications.marketplace.security import MarketplaceSecurity, marketplace_security
from applications.marketplace.shared.store import MarketplaceStore, marketplace_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DeveloperPortal:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        core: MarketplaceManager | None = None,
        security: MarketplaceSecurity | None = None,
    ) -> None:
        self.store = store or marketplace_store
        self.core = core or marketplace_manager
        self.security = security or marketplace_security

    def publish(
        self,
        *,
        name: str,
        kind: str,
        category: str = "custom_enterprise",
        version: str = "1.0.0",
        publisher: str = "",
        documentation: str = "",
        api_reference: str = "",
        dependencies: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        meta = dict(metadata or {})
        meta["documentation"] = documentation
        meta["api_reference"] = api_reference
        pkg = self.core.publish_package(
            name=name,
            kind=kind,
            category=category,
            version=version,
            publisher=publisher,
            dependencies=dependencies,
            metadata=meta,
        )
        validation = self.validate_package(pkg["package_id"])
        pub_id = f"pub_{uuid.uuid4().hex[:10]}"
        record = {
            "publication_id": pub_id,
            "package_id": pkg["package_id"],
            "publisher": publisher,
            "validation": validation,
            "at": _now(),
        }
        self.store.publications.save(pub_id, record)
        return {"package": pkg, "publication": record, "validation": validation}

    def validate_package(self, package_id: str) -> dict[str, Any]:
        scan = self.security.full_scan(package_id)
        compat = self.core.check_compatibility(package_id)
        return {
            "package_id": package_id,
            "security_passed": scan["passed"],
            "compatible": compat["compatible"],
            "valid": scan["passed"] and compat["compatible"],
            "scan": scan,
            "compatibility": compat,
        }

    def analytics(self, package_id: str) -> dict[str, Any]:
        pkg = self.core.get_package(package_id)
        downloads = [d for d in self.store.downloads.list_all() if d.get("package_id") == package_id]
        ratings = [r for r in self.store.ratings.list_all() if r.get("package_id") == package_id]
        return {
            "package_id": package_id,
            "downloads": len(downloads),
            "rating_avg": pkg.get("rating_avg", 0),
            "rating_count": pkg.get("rating_count", 0),
            "installations": len([i for i in self.store.installations.list_all() if i.get("package_id") == package_id]),
            "documentation": (pkg.get("metadata") or {}).get("documentation", ""),
            "api_reference": (pkg.get("metadata") or {}).get("api_reference", ""),
        }

    def documentation(self, package_id: str) -> dict[str, Any]:
        pkg = self.core.get_package(package_id)
        meta = pkg.get("metadata") or {}
        return {
            "package_id": package_id,
            "name": pkg["name"],
            "documentation": meta.get("documentation", ""),
            "api_reference": meta.get("api_reference", ""),
            "version": pkg["version"],
        }

    def status(self) -> dict[str, Any]:
        return {
            "developer_portal": "1.0",
            "publications": len(self.store.publications.list_all()),
            "ready": True,
        }


developer_portal = DeveloperPortal()
