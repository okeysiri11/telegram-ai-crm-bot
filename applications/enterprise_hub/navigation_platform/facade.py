"""Navigation Platform Suite — Sprint 26.5 / v9.0.4."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platform_enterprise_navigation.facade import NavigationLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store

ROOT = Path(__file__).resolve().parents[3]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class NavigationPlatformSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = NavigationLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations()

    def bootstrap(self) -> dict[str, Any]:
        self.library = NavigationLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        nav_root = ROOT / "src" / "web" / "navigation"
        result["navigation_path_exists"] = nav_root.exists()
        result["command_palette_exists"] = (nav_root / "components" / "CommandPalette.tsx").exists()
        result["search_provider_exists"] = (nav_root / "managers" / "searchProvider.ts").exists()
        result["dashboard_page_exists"] = (nav_root / "pages" / "NavigationDashboardPage.tsx").exists()
        bid = _id("enp_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "hub_version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.enp_bootstraps.save(bid, record)
        for key, attr, prefix in (
            ("inventory", "enp_inventory", "enp_inv"),
            ("dashboard", "enp_dashboards", "enp_dash"),
            ("links", "enp_integrations", "enp_int"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        self.store.enp_bootstraps.save(bid, record)
        return record

    def inventory(self) -> dict[str, Any]:
        inv = self.library.inventory()
        rid = _id("enp_inv")
        record = {"inventory_id": rid, **inv, "created_at": _now()}
        self.store.enp_inventory.save(rid, record)
        return record

    def dashboard(self) -> dict[str, Any]:
        dash = self.library.dashboard()
        rid = _id("enp_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.enp_dashboards.save(rid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.enp_bootstraps.list_all()),
            "path": "src/web/navigation",
        }


navigation_platform = NavigationPlatformSuite()
