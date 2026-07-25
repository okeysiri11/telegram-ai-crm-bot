"""Command Center Platform Suite — Sprint 26.6 / v9.0.5."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platform_enterprise_command_center.facade import CommandCenterLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store

ROOT = Path(__file__).resolve().parents[3]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CommandCenterPlatformSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = CommandCenterLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations()

    def bootstrap(self) -> dict[str, Any]:
        self.library = CommandCenterLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        cc_root = ROOT / "src" / "web" / "command-center"
        result["command_center_path_exists"] = cc_root.exists()
        result["palette_exists"] = (cc_root / "components" / "UniversalCommandPalette.tsx").exists()
        result["omnibox_exists"] = (cc_root / "components" / "Omnibox.tsx").exists()
        result["productivity_page_exists"] = (cc_root / "pages" / "CommandCenterPage.tsx").exists()
        result["platform_package_exists"] = (ROOT / "platform_enterprise_command_center" / "facade.py").exists()
        # legacy ecc module still present
        result["legacy_ecc_exists"] = (
            ROOT / "applications" / "enterprise_hub" / "command_center" / "facade.py"
        ).exists()
        bid = _id("ecc2_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "hub_version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.ecc2_bootstraps.save(bid, record)
        for key, attr, prefix in (
            ("inventory", "ecc2_inventory", "ecc2_inv"),
            ("dashboard", "ecc2_dashboards", "ecc2_dash"),
            ("links", "ecc2_integrations", "ecc2_int"),
            ("nav_index", "ecc2_nav_index", "ecc2_nav"),
            ("productivity", "ecc2_productivity", "ecc2_prod"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        self.store.ecc2_bootstraps.save(bid, record)
        return record

    def inventory(self) -> dict[str, Any]:
        inv = self.library.inventory()
        rid = _id("ecc2_inv")
        record = {"inventory_id": rid, **inv, "created_at": _now()}
        self.store.ecc2_inventory.save(rid, record)
        return record

    def dashboard(self) -> dict[str, Any]:
        dash = self.library.dashboard()
        rid = _id("ecc2_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.ecc2_dashboards.save(rid, record)
        return record

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        result = self.library.search(query, **kwargs)
        rid = _id("ecc2_search")
        self.store.ecc2_searches.save(rid, {"search_id": rid, **result, "created_at": _now()})
        return result

    def execute(self, action: str, **kwargs: Any) -> dict[str, Any]:
        result = self.library.execute(action, **kwargs)
        rid = _id("ecc2_exec")
        self.store.ecc2_executions.save(rid, {"execution_id": rid, **result, "created_at": _now()})
        return result

    def ai_command(self, utterance: str, **kwargs: Any) -> dict[str, Any]:
        result = self.library.ai_command(utterance, **kwargs)
        rid = _id("ecc2_ai")
        self.store.ecc2_ai_commands.save(rid, {"ai_id": rid, **result, "created_at": _now()})
        return result

    def suggestions(self, **kwargs: Any) -> dict[str, Any]:
        items = self.library.suggestions(**kwargs)
        return {"suggestions": items, "count": len(items)}

    def context(self, patch: dict[str, Any] | None = None) -> dict[str, Any]:
        if patch:
            return self.library.update_context(patch)
        return self.library.context_snapshot()

    def productivity(self) -> dict[str, Any]:
        hub = self.library.productivity_hub()
        rid = _id("ecc2_prod")
        record = {"productivity_id": rid, **hub, "created_at": _now()}
        self.store.ecc2_productivity.save(rid, record)
        return record

    def analytics(self) -> dict[str, Any]:
        data = self.library.analytics()
        rid = _id("ecc2_an")
        record = {"analytics_id": rid, **data, "created_at": _now()}
        self.store.ecc2_analytics.save(rid, record)
        return record

    def navigation_index(self) -> dict[str, Any]:
        data = self.library.navigation_index()
        rid = _id("ecc2_nav")
        record = {"index_id": rid, **data, "created_at": _now()}
        self.store.ecc2_nav_index.save(rid, record)
        return record

    def validate_permissions(self, action: str, permissions: list[str]) -> dict[str, Any]:
        return self.library.validate_permissions(action, permissions)

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.ecc2_bootstraps.list_all()),
            "path": "src/web/command-center",
            "api_prefix": "/api/enterprise-command/v1",
        }


command_center_platform = CommandCenterPlatformSuite()
