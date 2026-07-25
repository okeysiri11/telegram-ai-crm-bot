"""Enterprise Navigation Suite — Sprint 26.7 / v9.0.6."""

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


class EnterpriseNavigationSuite:
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
        result["quick_switcher_exists"] = (nav_root / "components" / "QuickSwitcher.tsx").exists()
        result["federation_exists"] = (nav_root / "managers" / "workspaceFederation.ts").exists()
        result["registry_exists"] = (nav_root / "managers" / "applicationRegistry.ts").exists()
        result["dashboard_page_exists"] = (nav_root / "pages" / "NavigationDashboardPage.tsx").exists()
        result["platform_package_exists"] = (ROOT / "platform_enterprise_navigation" / "facade.py").exists()
        bid = _id("env_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "hub_version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.env_bootstraps.save(bid, record)
        for key, attr, prefix in (
            ("inventory", "env_inventory", "env_inv"),
            ("dashboard", "env_dashboards", "env_dash"),
            ("links", "env_integrations", "env_int"),
            ("global_nav", "env_global_nav", "env_gnav"),
            ("workspaces", "env_workspaces", "env_ws"),
            ("registry", "env_registry", "env_reg"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        return record

    def inventory(self) -> dict[str, Any]:
        inv = self.library.inventory()
        rid = _id("env_inv")
        record = {"inventory_id": rid, **inv, "created_at": _now()}
        self.store.env_inventory.save(rid, record)
        return record

    def dashboard(self) -> dict[str, Any]:
        dash = self.library.dashboard()
        rid = _id("env_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.env_dashboards.save(rid, record)
        return record

    def global_navigation(self, **kwargs: Any) -> dict[str, Any]:
        return self.library.global_navigation(**kwargs)

    def workspaces(self) -> dict[str, Any]:
        return self.library.workspaces()

    def switch_workspace(self, kind_or_id: str, **kwargs: Any) -> dict[str, Any]:
        result = self.library.switch_workspace(kind_or_id, **kwargs)
        rid = _id("env_switch")
        self.store.env_switches.save(rid, {"switch_id": rid, **result, "created_at": _now()})
        return result

    def application_registry(self) -> dict[str, Any]:
        return self.library.application_registry()

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        result = self.library.search(query, **kwargs)
        rid = _id("env_search")
        self.store.env_searches.save(rid, {"search_id": rid, **result, "created_at": _now()})
        return result

    def favorites(self) -> dict[str, Any]:
        return self.library.favorites()

    def add_favorite(self, entry: dict[str, Any]) -> dict[str, Any]:
        return self.library.add_favorite(entry)

    def history(self, kind: str | None = None) -> dict[str, Any]:
        return self.library.history(kind)

    def breadcrumbs(self, pathname: str) -> dict[str, Any]:
        return self.library.breadcrumbs(pathname)

    def quick_switcher(self, **kwargs: Any) -> dict[str, Any]:
        return self.library.quick_switcher(**kwargs)

    def analytics(self) -> dict[str, Any]:
        data = self.library.analytics()
        rid = _id("env_an")
        record = {"analytics_id": rid, **data, "created_at": _now()}
        self.store.env_analytics.save(rid, record)
        return record

    def validate_permissions(self, resource: str, permissions: list[str]) -> dict[str, Any]:
        return self.library.validate_permissions(resource, permissions)

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.env_bootstraps.list_all()),
            "path": "src/web/navigation",
            "api_prefix": "/api/enterprise-navigation/v1",
        }


enterprise_navigation = EnterpriseNavigationSuite()
