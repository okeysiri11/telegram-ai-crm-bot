"""AI Marketplace — install/update/share/publish agents with ratings and permissions (Sprint 12.1)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.marketplace.core import MarketplaceManager, marketplace_manager
from applications.marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.marketplace.shared.store import MarketplaceStore, marketplace_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AIMarketplace:
    def __init__(self, store: MarketplaceStore | None = None, core: MarketplaceManager | None = None) -> None:
        self.store = store or marketplace_store
        self.core = core or marketplace_manager

    def publish_agent(
        self,
        *,
        name: str,
        category: str = "custom_enterprise",
        version: str = "1.0.0",
        publisher: str = "",
        permissions: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        meta = dict(metadata or {})
        meta["permissions"] = list(permissions or ["read_context", "assist"])
        return self.core.publish_package(
            name=name,
            kind="agent",
            category=category,
            version=version,
            publisher=publisher,
            metadata=meta,
        )

    def install_agent(self, package_id: str, *, org_id: str = "", user_id: str = "") -> dict[str, Any]:
        pkg = self.core.get_package(package_id)
        if pkg.get("kind") != "agent":
            raise ValidationError("package is not an agent")
        return self.core.install(package_id, org_id=org_id, user_id=user_id)

    def update_agent(self, installation_id: str, *, to_version: str) -> dict[str, Any]:
        return self.core.update(installation_id, to_version=to_version)

    def share_agent(self, package_id: str, *, with_org_id: str) -> dict[str, Any]:
        pkg = self.core.get_package(package_id)
        if pkg.get("kind") != "agent":
            raise ValidationError("package is not an agent")
        shared = pkg.setdefault("shared_with", [])
        if with_org_id and with_org_id not in shared:
            shared.append(with_org_id)
        pkg["updated_at"] = _now()
        self.store.packages.save(package_id, pkg)
        self.store.agents.save(package_id, pkg)
        return {"package_id": package_id, "shared_with": shared}

    def agent_permissions(self, package_id: str, *, permissions: list[str] | None = None) -> dict[str, Any]:
        pkg = self.core.get_package(package_id)
        if pkg.get("kind") != "agent":
            raise ValidationError("package is not an agent")
        if permissions is not None:
            meta = pkg.setdefault("metadata", {})
            meta["permissions"] = list(permissions)
            self.store.packages.save(package_id, pkg)
            self.store.agents.save(package_id, pkg)
        return {"package_id": package_id, "permissions": (pkg.get("metadata") or {}).get("permissions", [])}

    def list_agents(self) -> list[dict[str, Any]]:
        return self.core.list_packages(kind="agent")

    def rate_agent(self, package_id: str, *, score: float, reviewer: str = "", comment: str = "") -> dict[str, Any]:
        return self.core.rate(package_id, score=score, reviewer=reviewer, comment=comment)

    def status(self) -> dict[str, Any]:
        return {"ai_marketplace": "1.0", "agents": len(self.list_agents()), "ready": True}


ai_marketplace = AIMarketplace()
