"""Workflow Marketplace — import/export, templates, automation & business packs (Sprint 12.1)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.marketplace.core import MarketplaceManager, marketplace_manager
from applications.marketplace.shared.exceptions import ValidationError
from applications.marketplace.shared.store import MarketplaceStore, marketplace_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkflowMarketplace:
    def __init__(self, store: MarketplaceStore | None = None, core: MarketplaceManager | None = None) -> None:
        self.store = store or marketplace_store
        self.core = core or marketplace_manager

    def publish_workflow(
        self,
        *,
        name: str,
        steps: list[dict[str, Any]] | None = None,
        category: str = "custom_enterprise",
        pack_type: str = "template",
        version: str = "1.0.0",
        publisher: str = "",
    ) -> dict[str, Any]:
        if pack_type not in {"template", "automation", "business"}:
            raise ValidationError("pack_type must be template|automation|business")
        return self.core.publish_package(
            name=name,
            kind="workflow",
            category=category,
            version=version,
            publisher=publisher,
            metadata={"steps": list(steps or []), "pack_type": pack_type},
        )

    def export_workflow(self, package_id: str) -> dict[str, Any]:
        pkg = self.core.get_package(package_id)
        if pkg.get("kind") != "workflow":
            raise ValidationError("package is not a workflow")
        payload = {
            "name": pkg["name"],
            "version": pkg["version"],
            "category": pkg["category"],
            "metadata": pkg.get("metadata") or {},
            "exported_at": _now(),
        }
        return {"package_id": package_id, "format": "json", "blob": json.dumps(payload), "payload": payload}

    def import_workflow(self, *, payload: dict[str, Any], publisher: str = "") -> dict[str, Any]:
        if not payload.get("name"):
            raise ValidationError("payload.name required")
        return self.publish_workflow(
            name=payload["name"],
            steps=(payload.get("metadata") or {}).get("steps"),
            category=payload.get("category", "custom_enterprise"),
            pack_type=(payload.get("metadata") or {}).get("pack_type", "template"),
            version=payload.get("version", "1.0.0"),
            publisher=publisher,
        )

    def list_templates(self) -> list[dict[str, Any]]:
        return [w for w in self.core.list_packages(kind="workflow") if (w.get("metadata") or {}).get("pack_type") == "template"]

    def list_automation_packs(self) -> list[dict[str, Any]]:
        return [w for w in self.core.list_packages(kind="workflow") if (w.get("metadata") or {}).get("pack_type") == "automation"]

    def list_business_packs(self) -> list[dict[str, Any]]:
        return [w for w in self.core.list_packages(kind="workflow") if (w.get("metadata") or {}).get("pack_type") == "business"]

    def status(self) -> dict[str, Any]:
        return {
            "workflow_marketplace": "1.0",
            "workflows": len(self.core.list_packages(kind="workflow")),
            "ready": True,
        }


workflow_marketplace = WorkflowMarketplace()
