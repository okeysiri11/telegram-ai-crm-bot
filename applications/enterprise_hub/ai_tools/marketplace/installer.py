"""Marketplace installer — install/update/disable packages."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_tools.marketplace.packages import PackageCatalog
from applications.enterprise_hub.ai_tools.marketplace.signatures import PackageSignatures
from applications.enterprise_hub.ai_tools.skill_registry import SkillRegistry
from applications.enterprise_hub.ai_tools.tool_registry import ToolRegistry
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class MarketplaceInstaller:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.packages = PackageCatalog(self.store)
        self.signatures = PackageSignatures(self.store)
        self.tools = ToolRegistry(self.store)
        self.skills = SkillRegistry(self.store)

    def install(self, *, package_id: str, signature_id: str | None = None) -> dict[str, Any]:
        pkg = self.packages.get(package_id)
        if signature_id:
            verified = self.signatures.verify(signature_id=signature_id)
            if not verified.get("valid"):
                raise ValidationError("invalid package signature")
        installed: dict[str, Any] = {}
        payload = pkg.get("payload") or {}
        if pkg.get("kind") == "tool":
            installed = self.tools.register(
                name=payload.get("name") or pkg["name"],
                domain=payload.get("domain", "custom"),
                description=payload.get("description", ""),
                owner=payload.get("owner", "marketplace"),
                version=pkg.get("version", "1.0"),
                permissions=payload.get("permissions"),
                cost_per_call=float(payload.get("cost_per_call", 0.01) or 0.01),
            )
        else:
            steps = payload.get("steps")
            if not steps:
                raise ValidationError("skill package requires steps")
            installed = self.skills.register(
                name=payload.get("name") or pkg["name"],
                description=payload.get("description", ""),
                steps=steps,
                category=payload.get("category", "marketplace"),
            )
        iid = _id("ats_inst")
        return self.store.ats_installs.save(
            iid,
            {
                "install_id": iid,
                "package_id": package_id,
                "kind": pkg["kind"],
                "installed_id": installed.get("tool_id") or installed.get("skill_id"),
                "at": _now(),
            },
        )

    def disable(self, *, package_id: str) -> dict[str, Any]:
        pkg = self.packages.get(package_id)
        pkg["status"] = "disabled"
        self.store.ats_packages.save(package_id, pkg)
        return pkg
