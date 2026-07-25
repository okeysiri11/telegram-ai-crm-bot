"""Identity Center Suite — Sprint 26.3 / v9.0.2."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platform_enterprise_identity_center.facade import IdentityCenterLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store

ROOT = Path(__file__).resolve().parents[3]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class IdentityCenterSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = IdentityCenterLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations()

    def bootstrap(self) -> dict[str, Any]:
        self.library = IdentityCenterLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        auth_root = ROOT / "src" / "web" / "auth"
        result["auth_path_exists"] = auth_root.exists()
        result["login_page_exists"] = (auth_root / "pages" / "LoginPage.tsx").exists()
        result["identity_dashboard_exists"] = (auth_root / "pages" / "IdentityCenterPage.tsx").exists()
        result["mfa_center_exists"] = (auth_root / "managers" / "mfaCenter.ts").exists()
        bid = _id("eic_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "hub_version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.eic_bootstraps.save(bid, record)
        for key, attr, prefix in (
            ("inventory", "eic_inventory", "eic_inv"),
            ("dashboard", "eic_dashboards", "eic_dash"),
            ("links", "eic_integrations", "eic_int"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        self.store.eic_bootstraps.save(bid, record)
        return record

    def inventory(self) -> dict[str, Any]:
        inv = self.library.inventory()
        rid = _id("eic_inv")
        record = {"inventory_id": rid, **inv, "created_at": _now()}
        self.store.eic_inventory.save(rid, record)
        return record

    def dashboard(self) -> dict[str, Any]:
        dash = self.library.dashboard()
        rid = _id("eic_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.eic_dashboards.save(rid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.eic_bootstraps.list_all()),
            "path": "src/web/auth",
        }


identity_center = IdentityCenterSuite()
