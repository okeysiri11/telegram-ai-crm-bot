"""Workspace Platform Suite — Sprint 26.4 / v9.0.3."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platform_enterprise_workspace.facade import WorkspaceLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store

ROOT = Path(__file__).resolve().parents[3]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class WorkspacePlatformSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = WorkspaceLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations()

    def bootstrap(self) -> dict[str, Any]:
        self.library = WorkspaceLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        ws_root = ROOT / "src" / "web" / "workspace"
        result["workspace_path_exists"] = ws_root.exists()
        result["home_page_exists"] = (ws_root / "pages" / "WorkspaceHomePage.tsx").exists()
        result["widget_manager_exists"] = (ws_root / "managers" / "widgetManager.ts").exists()
        result["realtime_exists"] = (ws_root / "realtime" / "liveUpdates.ts").exists()
        bid = _id("ews_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "hub_version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.ews_bootstraps.save(bid, record)
        for key, attr, prefix in (
            ("inventory", "ews_inventory", "ews_inv"),
            ("dashboard", "ews_dashboards", "ews_dash"),
            ("links", "ews_integrations", "ews_int"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        self.store.ews_bootstraps.save(bid, record)
        return record

    def inventory(self) -> dict[str, Any]:
        inv = self.library.inventory()
        rid = _id("ews_inv")
        record = {"inventory_id": rid, **inv, "created_at": _now()}
        self.store.ews_inventory.save(rid, record)
        return record

    def dashboard(self) -> dict[str, Any]:
        dash = self.library.dashboard()
        rid = _id("ews_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.ews_dashboards.save(rid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.ews_bootstraps.list_all()),
            "path": "src/web/workspace",
        }


workspace_platform = WorkspacePlatformSuite()
